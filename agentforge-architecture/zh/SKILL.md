---
name: agentforge-architecture
description: Agent architecture selection guide. 7 loop paradigms (Async Generator / Submission-Handler / PubSub Event / Reflection Chain / Plugin Gateway / Event-Driven Webhook / Realtime-Voice) + language selection + Provider abstraction. Triggers when user asks about "Agent architecture selection", "how to design Agent loop", "which language to use for Agent".
triggers:
  - Agent 架构选型
  - Agent loop
  - 选什么语言写 Agent
  - agent loop design
  - agent architecture
metadata:
  version: "2.0.0"
  last_updated: "2026-04-06"
  category: "agent-engineering"
---

# AgentForge Phase 1: Architecture Selection

> Series entry: `/agentforge` | Deep cognitive theory: `/cognitive-architecture`
> Knowledge source: Reverse engineering 11 production-grade Agent codebases (2026-04-06 v2)

## Decision 1: Choose an Agent Loop Paradigm

Every Agent's core is a loop: `User Input → LLM Inference → Tool Execution → Observe Results → Continue or Stop`.
But the **implementation paradigm** of this loop constrains all subsequent architecture decisions.

### Paradigm Decision Tree

> **Revision note**: The original decision tree used "UI form" as the primary axis, routing imprecisely for Agents without interactive UIs (Slack Bots, Daemons, API services). The revised tree uses **deployment form** as the primary axis, covering all Agent types more accurately.

```
What is your Agent's deployment form?
│
├─ Interactive CLI / IDE tool (real-time user dialogue)
│  │
│  ├─ Needs streaming UI + rich tool ecosystem + fast iteration
│  │  → Async Generator (TypeScript)
│  │  → Representatives: Claude Code, Cline
│  │
│  └─ Needs OS-level security isolation + peak performance + enterprise-grade approvals
│     → Submission-Handler (Rust)
│     → Representatives: Codex CLI, Goose
│
├─ Multi-channel Bot / Platform service (Slack / Discord / Telegram / Web)
│  │
│  ├─ Needs unified multi-channel + plugin extensibility + Agent OS positioning
│  │  → Plugin Gateway (TypeScript)
│  │  → Representative: OpenClaw
│  │  → Note: OpenClaw users can directly use built-in Slack/Discord/Telegram Channel plugins
│  │
│  └─ Needs single-channel rapid implementation (Slack only or Web only)
│     → PubSub Event Loop (Go) or Async Generator (TypeScript) both work
│     → Tradeoff: Go naturally fits Slack event concurrency; TypeScript has richer tool ecosystem
│
├─ Background Daemon / Scheduled task / Workflow Pipeline (no interactive UI)
│  │
│  ├─ Fixed DAG, steps deterministic, LLM does single-step inference only
│  │  → No full Agent Loop needed; use LLM API calls + orchestration framework (Airflow / Temporal)
│  │
│  ├─ Dynamic steps (Agent autonomously decides next step) + needs database persistence
│  │  → PubSub Event Loop (Go)
│  │  → Representative: OpenCode
│  │
│  └─ Fast prototype + Python ecosystem (rich SDKs: Whisper/Pandas/LangChain)
│     → Reflection Chain (Python)
│     → Representative: Aider
│
├─ HTTP API service (other systems call it)
│  → PubSub Event Loop (Go) — high concurrency
│  → Async Generator (TypeScript) — rich tools
│
└─ Real-time Voice / Low latency (<500ms)
   → Realtime/Voice, the sixth paradigm (WebSocket) — see below
```

**Common misrouting corrections**:
- "I'm building a Slack Bot" → First check if multi-channel is needed: yes → Plugin Gateway; no → PubSub or Async Generator both work; don't force Async Generator (Slack doesn't need streaming UI)
- "I'm building a scheduled task" → First determine if steps are fixed: fixed → use orchestration framework, no Agent Loop needed; dynamic → PubSub Event Loop

### Paradigm 1: Async Generator Loop

**Representative**: Claude Code (`src/query.ts` 1729 lines + `src/QueryEngine.ts` 1295 lines) [CC]

```
async function* queryLoop(params) {
  while (true) {
    yield* streamAPIResponse()       // Stream to UI
    const toolUses = collectToolUses()
    if (!toolUses.length) break      // No tool call = done
    yield* executeAndYieldResults()  // Tool execution also streamed
  }
}
```

**Core characteristics**:
- Entire loop is a generator; each step yields to UI renderer
- Tool concurrency partitioning: read-only tools parallel / write tools serial [CC]
- Streaming tool execution: starts executing parsed tools before API response is complete [CC]
- Auto-compact: forks subprocess to summarize when token threshold exceeded [CC]

**Advantages**: Excellent streaming experience; caller can inject info or interrupt at any yield point
**Cost**: High complexity in generator error handling and debugging
**Use when**: All interactive Agents. Not suitable for pure batch processing

### Paradigm 2: Submission-Handler Dispatch

**Representative**: Codex CLI (`codex-rs/core/src/codex.rs`, 294KB) [CX]

```rust
async fn submission_loop() {
    while let Some(sub) = rx.recv().await {
        match sub.op {
            Op::UserInput{..}  => handle_user_input(),
            Op::ExecApproval{..} => handle_approval(),
            Op::Compact        => handle_compact(),
            Op::InterAgentCommunication{..} => handle_ipc(),
            Op::Shutdown       => break,
            // ...40+ operation types
        }
    }
}
```

**Core characteristics**:
- Single event loop; all operations routed through Op enum, no global state [CX]
- OS-level sandbox: macOS Seatbelt / Linux Landlock / Windows Sandbox [CX]
- Starlark policy engine: Python-like DSL for defining command approval rules [CX]
- Guardian AI: risk assessment via another LLM [CX] (⚠️ Feature exists but name is disputed; official docs call it "Codex Security"; "Guardian AI" is community terminology — see `/agentforge-security`)

**Advantages**: Type safety, peak performance, OS-level security isolation
**Cost**: High Rust development and maintenance cost
**Use when**: Enterprise-grade security and approval scenarios

### Paradigm 3: PubSub Event Loop

**Representative**: OpenCode (`internal/llm/agent/agent.go`, 600 lines) [OC]

```go
func (a *agent) Run(ctx, sessionID, content) (<-chan AgentEvent, error) {
    go func() {
        for {
            events := provider.StreamResponse(ctx, messages, tools)
            for event := range events {
                processEvent(event)  // Tool calls, text streaming
            }
            if finishReason != "tool_use" { break }
            executeTools(ctx, toolCalls)
        }
    }()
    return eventChan, nil
}
```

**Core characteristics**:
- PubSub decoupling: Agent/Session/Message/Permission each have independent Broker [OC]
- SQLite + WAL persistence, Goose migration manages schema [OC]
- Deep LSP integration: real Language Server (not just syntax highlighting) [OC]
- 75+ Provider support (dynamically loaded via models.dev, including Anthropic, OpenAI, Gemini, Bedrock, Groq, Ollama, etc.) [OC]

**Advantages**: Go concurrency model naturally fits Agents; PubSub completely decouples UI from logic
**Cost**: Go's LLM SDK ecosystem is relatively weak
**Use when**: Systems requiring database persistence and real-time event driving

### Paradigm 4: Reflection Chain

**Representative**: Aider (`aider/coders/base_coder.py`, 859 lines) [AD]

```python
def run_one(self, user_message):
    self.init_before_message()
    for i in range(max_reflections):     # Default 3 rounds
        response = self.send_message(msg)
        edits = self.parse_edits(response)
        self.apply_edits(edits)
        if self.is_satisfactory():
            break
        msg = f"Review and improve: {response}"
    self.auto_commit()
```

**Core characteristics**:
- No formal tool system: edit formats agreed via prompt conventions, not function calling [AD]
- Polymorphic edit formats: 6 formats (diff/udiff/patch/whole-file/architect/ask), switched at runtime. In ask mode, Agent only asks questions without editing [AD]
- Repo Map: AST-level codebase index (intelligent summary within token budget) [AD]
- Reflection loop: Agent self-examines output, up to 3 rounds of improvement [AD]

**Advantages**: Minimal architecture; prompt drives everything; fastest onboarding
**Cost**: No tool schema means LLM more prone to output format errors
**Use when**: Fast prototyping, pair programming scenarios

### Paradigm 5: Plugin Gateway Loop

**Representative**: OpenClaw (`src/agents/agent-command.ts`) [OW]

```
Gateway layer (multi-channel entry)
    ↓ Telegram / Discord / Slack / Web / CLI / ...
Channel layer (protocol adapter)
    ↓ Unified message format
LLM layer (Agent loop)
    ├─ Dynamic Prompt Variant selection by Provider
    ├─ Skill system (lazy loading + environment-aware filtering)
    ├─ 4 loop detectors + global circuit breaker (30 times)
    └─ Plugin SDK (5 types: Provider/Channel/Tool/Skill/Memory)
```

**Core characteristics**:
- Multi-channel gateway: 10+ channels unified, single Agent core serves all channels [OW]
- Plugin SDK: 5 plugin types, jiti dynamic import, hot loading [OW]
- Prompt Cache stability: deterministic file sorting ensures cache hit rate [OW]
- 4 loop detectors: signature comparison + echo detection + ping-pong + global circuit breaker [OW]

**Plugin SDK Code Examples (TypeScript)**:

> ⚠️ **Note**: The examples below illustrate OpenClaw Plugin SDK architecture patterns (inferred from Gateway/Channel/LLM three-layer principles). `@openclaw/sdk` and `@openclaw/core` are pattern-level package names; actual API follows OpenClaw official documentation.

```typescript
// 1. Implement custom Channel (protocol adapter layer)
// Channel: receives platform messages → normalizes to AgentMessage → returns response
import { ChannelPlugin, AgentMessage, ChannelContext } from "@openclaw/sdk";

export class WebhookChannel implements ChannelPlugin {
  readonly name = "webhook";

  // Convert platform raw message to unified format
  normalize(raw: Record<string, unknown>): AgentMessage {
    return {
      role: "user",
      content: String(raw.text ?? raw.message ?? ""),
      metadata: { platform: "webhook", rawPayload: raw },
    };
  }

  // Pass Agent response back to platform
  async send(ctx: ChannelContext, response: string): Promise<void> {
    await ctx.http.post(ctx.config.webhookUrl, { text: response });
  }
}

// 2. Register custom LLM Provider
import { ProviderPlugin, LLMRequest, LLMResponse } from "@openclaw/sdk";

export class MyLLMProvider implements ProviderPlugin {
  readonly name = "my-llm";

  async send(req: LLMRequest): Promise<LLMResponse> {
    const resp = await myLLMClient.chat(req.messages, {
      model: req.model,
      tools: req.tools,
    });
    return {
      content: resp.choices[0].message.content,
      toolCalls: resp.choices[0].message.tool_calls ?? [],
      usage: resp.usage,
    };
  }

  async *stream(req: LLMRequest): AsyncGenerator<LLMStreamEvent> {
    for await (const chunk of myLLMClient.stream(req.messages)) {
      yield { type: "content_delta", delta: chunk.text };
    }
    yield { type: "complete" };
  }
}

// 3. Register Skill (tool-type plugin)
import { SkillPlugin, ToolCall, ToolResult } from "@openclaw/sdk";

export class ConfluenceSearchSkill implements SkillPlugin {
  readonly name = "confluence-search";
  readonly description = "Search Confluence knowledge base";
  readonly inputSchema = {
    type: "object",
    properties: {
      query: { type: "string", description: "Search query" },
      space: { type: "string", description: "Confluence space key" },
    },
    required: ["query"],
  };

  async execute(call: ToolCall): Promise<ToolResult> {
    const { query, space } = call.input as { query: string; space?: string };
    const results = await confluenceClient.search(query, { space });
    return {
      content: results.map((r) => `[${r.title}](${r.url})\n${r.excerpt}`).join("\n\n"),
    };
  }
}

// 4. Register plugins with OpenClaw Gateway
import { OpenClaw } from "@openclaw/core";

const agent = new OpenClaw({
  plugins: [
    new WebhookChannel(),           // Channel plugin
    new MyLLMProvider(),            // Provider plugin
    new ConfluenceSearchSkill(),    // Skill plugin
  ],
  defaultProvider: "my-llm",
  defaultModel: "my-model-v1",
});

await agent.start();
```

**Advantages**: Agent OS positioning, beyond single IDE/CLI binding
**Cost**: High architectural complexity; requires maintaining multi-channel adapter layer
**Use when**: Agent products needing multi-platform distribution

## Decision 2: Language Selection

| Language | TUI Framework | LLM SDK Ecosystem | Concurrency Model | Streaming/Audio | Representatives |
|----------|---------------|-------------------|-------------------|-----------------|-----------------|
| **TypeScript** | Ink (React) | Richest | async/await + Worker | ✅ Native AsyncGenerator, mature WebSocket | Claude Code, Cline, OpenClaw |
| **Rust** | ratatui | Weak but self-built | Tokio async | ✅ Tokio Stream, low latency, high frame-rate audio | Codex CLI, Goose |
| **Go** | Bubble Tea | Moderate | goroutine + channel | ✅ goroutine naturally fits frame-by-frame concurrency, channel for backpressure | OpenCode |
| **Python** | Rich / textual | Rich | asyncio | ⚠️ asyncio available but ecosystem fragmented (websockets/aiohttp mixed) | Aider, OpenHands, Letta |
| **Zig** | custom/none | Early stage (need to build HTTP layer) | manual threading/async (no runtime) | Self-evolving Platform (experimental) |

> Zig ecosystem details, known pitfalls, hot-loading patterns → [`references/lang-zig.md`](references/lang-zig.md)

**Selection guidance**:
- **Delivery speed priority** → TypeScript (largest ecosystem, fastest iteration)
- **Performance + security priority** → Rust (OS-level sandbox, zero-cost abstraction)
- **Concurrency + simplicity priority** → Go (goroutine naturally fits Agent concurrency)
- **Prototype + research priority** → Python (fastest onboarding, most LLM libraries)
- **Peak performance + self-evolving Platform** → Zig (comptime invariants, dlopen hot-loading, zero runtime; cost: extremely weak ecosystem, suitable only for system-level scenarios)

### Provider Aggregation Layer (Multi-Model Unified Interface)

When building your own Provider abstraction, you can optionally reuse aggregation layer libraries — saving the work of manually writing SDK adapters for each vendor:

| Library | Language | Characteristics | Use When |
|---------|----------|-----------------|---------|
| **LiteLLM** | Python | Unified interface to 100+ models (OpenAI-compatible format), includes routing/retry/fallback | Python Agent rapid multi-Provider integration |
| **OpenRouter** | HTTP API | Cloud proxy, single API key access to all major models, no local dependencies | Prototype stage /，不想管 SDK 版本 |
| **AI SDK (Vercel)** | TypeScript | Unified streaming interface, includes Provider switching + structured output | TypeScript/JS Agent |
| **llm.rs / llm crate** | Rust | Local GGUF model inference, no API needed | Offline Rust Agent |

**When to build custom Provider interface vs. reuse aggregation layer**:

```
Build custom:
├─ Need peak performance (Rust/Go, reduce middle layer)
├─ Need precise control over streaming event format
└─ Production-grade; cannot accept aggregation layer version dependency risk

Reuse aggregation layer:
├─ Prototype stage; need rapid integration of 5+ Providers
├─ Python Agent; LiteLLM is already the de facto standard
└─ No need to customize streaming / token billing details
```

**Security warning** (supply chain): LiteLLM suffered a PyPI poisoning incident in March 2026 (credential theft + K8s lateral movement backdoor). Production environments must lock versions + hash verification. → See `/agentforge-security` supply chain security chapter.

## Decision 3: Provider Abstraction

All production-grade Agents implement a Provider interface to support multiple models. The leanest design [OC]:

```go
type Provider interface {
    SendMessages(ctx, messages, tools) (*ProviderResponse, error)  // Synchronous
    StreamResponse(ctx, messages, tools) <-chan ProviderEvent       // Streaming
    Model() models.Model
}
```

**Multi-modal content blocks** (extension constraints for Provider interface):

When an Agent uses image/audio/file input, the messages type shifts from `[]string` to `[]ContentBlock`:

```go
// Plain-text Agent (simple)
messages = [{"role": "user", "content": "fix this bug"}]

// Multi-modal Agent (required)
messages = [{"role": "user", "content": [
    {"type": "text", "text": "fix this bug"},
    {"type": "image", "source": {"type": "base64", "data": "..."}},  // ~1500 tokens
    {"type": "document", "source": {"type": "url", "url": "..."}}
]}]
```

**Architectural impact**: If the Provider interface only accepts `string` messages, extending to multi-modal requires a breaking interface change. Define messages with a `ContentBlock` union type from day one.

**Event stream standardization** (converging design across all Agents):

| Event | Meaning |
|-------|---------|
| ContentStart/Delta/Stop | Text streaming |
| ThinkingDelta | Thinking process (extended thinking) |
| ToolUseStart/Delta/Stop | Tool call |
| Complete | Turn complete |
| Error | Error |

**Token billing must be tracked**:
```
inputTokens + cacheCreationTokens + cacheReadTokens + outputTokens → totalCost
```

### Event-Driven HTTP Webhook: The Sixth Paradigm

The current 5 paradigms are all **active loop type** — Agent drives the loop proactively, waiting for user input or tool results. But the most common production scenario is **passive trigger type**: platform sends HTTP POST, Agent processes once and exits, no persistent state.

```
Trigger source (Slack/GitHub/Stripe, etc.)
    ↓ HTTP POST Webhook
Agent service (FastAPI/Express)
    ├── Signature verification (Layer 2-0, see security Phase)
    ├── Idempotency check (event_id deduplication, prevent double execution)
    ├── One-shot LLM inference + tool calls
    └── Return 200 OK (timeout varies by platform, see note below)
```

**Core characteristics**:
- **No persistent loop**: each HTTP request is an independent execution unit
- **No conversation history**: each call builds context from scratch, no state across requests
- **Idempotency mandatory**: Webhook platforms have retry mechanisms; the same event_id may arrive 2+ times

```python
import asyncio
from fastapi import FastAPI, Request
import redis.asyncio as redis

app = FastAPI()
redis_client = redis.Redis()

@app.post("/webhook/slack/events")
async def handle_event(request: Request):
    # 1. Signature verification (done in middleware layer)
    payload = await request.json()

    # 2. Idempotency: Slack may retry
    event_id = payload.get("event_id", "")
    if event_id and await redis_client.set(f"evt:{event_id}", "1", nx=True, ex=3600) is None:
        return {"ok": True}  # Already processed; ACK directly

    # 3. Return 200 quickly (timeouts vary by platform: Slack 3s, GitHub 15s, Stripe 30s)
    # Reprocessing pushed to background
    asyncio.create_task(process_event(payload))
    return {"ok": True}

async def process_event(payload: dict):
    """Real Agent logic: one-shot inference, no cross-request state maintained"""
    message = payload["event"]["text"]
    result = await classify_and_create_issue(message)
    await post_slack_reply(payload, result)
```

**Key differences from other paradigms**:

| Dimension | Active Loop Paradigms (1-5) | Event-Driven Webhook (Sixth) |
|----------|---------------------------|------------------------------|
| Trigger method | Agent proactively waits | Platform pushes HTTP request |
| State | Persistent across rounds | Stateless, each request independent |
| Context | Conversation history accumulates | Built fresh each time |
| Idempotency | Usually not needed | **Must implement** |
| Timeout constraint | Relaxed (user waiting) | Strict (varies by platform: Slack 3s, GitHub 15s, Stripe 30s) |

**Use when**:
```
Is your Agent triggered by external events (Webhook / Cron / Message Queue)?
    Yes → Does it need conversation state across events?
        No → Sixth paradigm (Event-Driven HTTP Webhook)
        Yes → Needs state storage (Redis/DB) + sixth paradigm + explicit history loading
    No → User interaction driven → Paradigms 1-5
```

**GitHub PR Review Agent shortcut (verified 2026-04-08)**:
If the target is GitHub PR Review, **no need to build your own Webhook Server** — use the official Action directly:
```yaml
# .github/workflows/claude-review.yml
- uses: anthropics/claude-code-action@v1
  # Production security best practice: pin to commit hash, prevent supply chain attacks
  # Example: uses: anthropics/claude-code-action@abc1234 (replace with latest commit hash in actual use)
  with:
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
    # Least privilege: read-only code + write PR comments
permissions:
  contents: read
  pull-requests: write
```
Cost: ~$0.05 for 400-line diff (Claude Sonnet 4.6), team of 50 PRs/month <$5. Saves 1-2 days of work vs. self-built FastAPI Webhook.

**One-click pin all Actions to commit hash** (prevent supply chain attacks):
```bash
# Copy script to project
cp /path/to/agentforge-architecture/scripts/pin-action.sh ./scripts/
chmod +x ./scripts/pin-action.sh

# Automatically replace all tag references in .github/workflows/ with immutable hashes
./scripts/pin-action.sh .github/workflows/
# Output:
#   Pinning anthropics/claude-code-action@v1
#   → abc1234def5678...
#   Updated: uses: anthropics/claude-code-action@abc1234  # v1

# Review and commit
git diff .github/workflows/
git add .github/workflows/ && git commit -m "ci: pin GitHub Actions to commit hashes"
```
> Script: `agentforge-architecture/scripts/pin-action.sh`
> Depends on `gh` CLI (`pacman -S github-cli`); automatically skips references already at hash.

---

### Realtime / Voice: The Seventh Paradigm

All previous six paradigms are based on the **request-response** model. Voice/Realtime Agents diverge here, choosing two different implementation paths:

#### Path A: Degraded Solution (recommended first attempt)

```
Audio → ASR (Whisper/Deepgram) → Text chunks → Async Generator Loop (Paradigm 1)
Pros: Reuse existing loop architecture; tool-calling logic unchanged
Cons: Additional 200-500ms ASR latency; cannot achieve <500ms response
Use when: Meeting assistants/transcription (no need for real-time interruption response)
```

**ASR tool interface** (differs from ordinary tools — streaming data source, not request-response):

```typescript
// Streaming data source tool: continuously yields data chunks, not one-shot return
class TranscriptionStreamTool {
  async *stream(audioSource: MediaStream): AsyncGenerator<TranscriptChunk> {
    const recognizer = new SpeechRecognizer({ model: "whisper-large" });
    for await (const audioChunk of audioSource) {
      const text = await recognizer.transcribe(audioChunk);
      if (text.trim()) {
        yield { text, timestamp: Date.now(), isFinal: text.endsWith(".") };
      }
    }
  }
}

// Agent Loop consumption: accumulate text chunks every 30 seconds → trigger one inference
async function meetingAgentLoop(stream: TranscriptionStreamTool) {
  let buffer: string[] = [];
  for await (const chunk of stream.stream(audioSource)) {
    buffer.push(chunk.text);
    if (buffer.length >= 15 || chunk.isFinal) {  // ~30 seconds per batch
      await agentLoop.process(buffer.join(" "));
      buffer = [];
    }
  }
}
```

#### Path B: True Realtime Path (<500ms scenarios)

```
WebSocket persistent connection (bidirectional streaming)
├─ Audio frames continuously streamed (no waiting for complete sentence)
├─ LLM listens and generates speech simultaneously (streaming VAD + streaming TTS)
├─ User interruption → send cancel event → stop current generation
└─ Tool calls via WebSocket transmission (not separate HTTP)
Currently supported: OpenAI Realtime API, Gemini Live API
```

**Additional architectural requirements for Path B** (completely different from Path A):
- Independent WebSocket state machine (connect/disconnect/reconnect)
- Concurrent conversation isolation (each user has independent WebSocket session)
- Interruption handling (cancelEvent + buffer flush)
- Context window management strategy completely different (no "single request" concept)

**Decision**: Unless there is a clear <500ms latency requirement, prioritize Path A — implementation complexity is 10x lower.

## Current State (April 2026)

- **5-paradigm landscape stable**: All new Agents launched since 2025 fall into one of these 5 paradigms; no sixth has emerged
- **Rust Agents rising**: Codex CLI + Goose prove Rust can build full-featured Agents; no longer just "performance scenarios"
- **Plugin Gateway solidified**: OpenClaw evolved from Cline fork to Agent OS; Gateway/Channel/LLM three-layer已成为独立范式
- **Provider interface converging**: All Agents' Provider abstractions look increasingly similar; Send + Stream + Model three-method pattern is now the de facto standard
- **Bitter Lesson note**: Reflection Chain (Paradigm 4) may weaken as model capabilities grow — stronger models need fewer explicit reflection loops

## Known Pitfalls

1. **Paradigm and language binding** — The decision tree treats paradigm and language as separate choices, but they're tightly coupled: Submission-Handler almost always means Rust, PubSub almost always means Go. Fix: Choose paradigm first, then confirm language constraints; never do the reverse
2. **Premature Provider abstraction generalization** — Supporting 10 Providers from the start causes interface bloat. Fix: Hardcode 1 Provider to start, abstract after confirming the interface; reference OpenCode's 2-method interface
3. **Streaming and batch processing mixed** — Async Generator paradigm assumes all output is streamed, but tool execution results often arrive in one batch. Fix: Distinguish between "streaming generation" and "completion event" yield types
4. **Ignoring loop detection** — Dive straight into coding after choosing a paradigm, forget to add infinite-loop protection. All production Agents have loop detection. Fix: Plan loop detection during architecture phase, not as an afterthought; see `/agentforge-harness`
5. **Delayed token billing tracking** — Provider abstraction only handles Send/Stream, forgets to track token consumption. Cost overruns discovered only after going live. Fix: Provider interface must return usage information; track from day one

## Architecture Checklist

- [ ] Loop paradigm selected and its constraints understood (consider sixth paradigm for Voice/Realtime scenarios)
- [ ] Implementation language selected and TUI/SDK ecosystem confirmed to meet needs
- [ ] Provider abstraction interface designed (supports at least 2 Providers)
- [ ] messages type uses ContentBlock union (supports multi-modal extension; don't use plain string)
- [ ] Event stream format determined (streaming or synchronous)
- [ ] Token billing tracking plan determined (includes image/video token costs)
- [ ] Capability plane determined (input/processing/output) → See `/agentforge-spec` capability plane declaration

## Reverse Audit (Diagnose Mode)

> Called by `/agentforge-diagnose` — performs D1 architecture-dimension static audit on existing code.

| # | Check Item | How to Check | Pass Criteria |
|---|-----------|-------------|---------------|
| A1 | Loop paradigm identifiable | Read entry file, find main loop structure | Can clearly determine which loop paradigm (Blocking/Event/Async/Workflow/Webhook) |
| A2 | Paradigm matches scenario | Confirm Agent type (Webhook/CLI/Service), cross-reference with architecture selection table | Paradigm doesn't conflict with type (e.g., Webhook Agent should not have blocking while loop) |
| A3 | No God File | `find src -name "*.py" -o -name "*.ts" \| xargs wc -l \| sort -n \| tail -5` | All files < 500 lines |
| A4 | Single module responsibility | Check directory structure; confirm loop/tools/prompt/memory are independent | No "does everything" central file |
| A5 | No hardcoded config | `grep -rn "api_key\s*=\s*['\"]" src/` | No bare keys, model IDs, or endpoints in source code |

**High-probability issues**: Hardcoded API key (security P0), single file >800 lines (maintenance P1), Webhook Agent using blocking while True loop (performance P0)

## Next Steps

After architecture selection → **`/agentforge-tools`** (Phase 2: Tool System Design)
