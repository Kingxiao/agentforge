---
name: agentforge-architecture
disable-model-invocation: true
description: Internal AgentForge Phase 1 architecture guide. Load only when explicitly named or selected by the agentforge router; do not auto-trigger from generic architecture, language, or Agent questions.
triggers:
  - Agent architecture selection
  - Agent loop
  - which language to use for Agent
  - agent loop design
  - agent architecture
metadata:
  version: "3.0.0"
  last_updated: "2026-08-08"
  category: "agent-engineering"
---

# AgentForge Phase 1: Architecture Selection

> **Phase isolation:** This file is self-contained for its decision. References to other `/agentforge-*` skills are navigation only; do not load another phase in the same response unless the user explicitly requests a multi-phase comparison.

> Series entry: `/agentforge` | Deep cognitive theory: `/cognitive-architecture`
> Knowledge source: reverse engineering 11 production-grade Agent codebases (2026-04-06 v2)

## Decision 1: Choose an Agent Loop Paradigm

Every Agent's core is a loop: `User Input → LLM Inference → Tool Execution → Observe Results → Continue or Stop`. But the **implementation paradigm** of this loop constrains all subsequent architecture decisions.

### Paradigm Decision Tree

Use **deployment form** as the primary axis, not UI form (a Slack Bot has no interactive UI but still needs a paradigm decision).

- **Interactive CLI / IDE tool (real-time user dialogue)**
  - Streaming UI + rich tool ecosystem + fast iteration → **Async Generator (TypeScript)**. Representatives: Claude Code, Cline.
  - OS-level security isolation + peak performance + enterprise-grade approvals → **Submission-Handler (Rust)**. Representatives: Codex CLI, Goose.
- **Multi-channel Bot / Platform service (Slack / Discord / Telegram / Web)**
  - Unified multi-channel + plugin extensibility + Agent OS positioning → **Plugin Gateway (TypeScript)**. Representative: OpenClaw. OpenClaw users can reuse built-in Slack/Discord/Telegram Channel plugins.
  - Single channel, rapid implementation → **PubSub Event Loop (Go)** or **Async Generator (TypeScript)** both work. Trade-off: Go fits Slack event concurrency naturally; TypeScript has richer tool ecosystem.
- **Background Daemon / Scheduled task / Workflow Pipeline (no interactive UI)**
  - Fixed DAG, steps deterministic, LLM does single-step inference only → no full Agent Loop needed; LLM API calls + orchestration framework (Airflow / Temporal).
  - Dynamic steps (Agent decides next step) + database persistence → **PubSub Event Loop (Go)**. Representative: OpenCode.
  - Fast prototype + Python ecosystem (Whisper / Pandas / LangChain) → **Reflection Chain (Python)**. Representative: Aider.
- **Batch processing / data pipeline / research task** (non-interactive, Python execution) — state must persist across steps + Python ecosystem + code as action language → **Code Generation Loop (Python)**. Representative: smolagents. 6-tier executor isolation; `LocalPythonExecutor` NOT for untrusted code.
- **HTTP API service (called by other systems)** → PubSub Event Loop (Go, high concurrency) **or** Async Generator (TypeScript, rich tools).
- **Real-time Voice / low latency (< 500 ms)** → **Realtime/Voice** (eighth documented paradigm, WebSocket — see below).

**Common misrouting corrections**:
- "I'm building a Slack Bot" → first check if multi-channel is needed: yes → Plugin Gateway; no → PubSub or Async Generator. Don't force Async Generator (Slack doesn't need streaming UI).
- "I'm building a scheduled task" → first determine if steps are fixed: fixed → orchestration framework, no Agent Loop needed; dynamic → PubSub Event Loop.

### Paradigm 1: Async Generator Loop

**Representative**: Claude Code (`src/query.ts` 1729 lines + `src/QueryEngine.ts` 1295 lines) [CC]

Structure: `async function* queryLoop(params)` — a generator that `yield*`s a `streamAPIResponse()` stream to the UI, collects tool uses, breaks when there are none, otherwise `yield*`s `executeAndYieldResults()`.

**Core characteristics**:
- Entire loop is a generator; each step yields to UI renderer.
- Tool concurrency partitioning: read-only tools parallel / write tools serial [CC].
- Streaming tool execution: starts executing parsed tools before API response is complete [CC].
- Auto-compact: forks subprocess to summarize when token threshold exceeded [CC].

**Advantages**: excellent streaming experience; caller can inject info or interrupt at any yield point.
**Cost**: high complexity in generator error handling and debugging.
**Use when**: all interactive Agents. Not suitable for pure batch processing.

### Paradigm 2: Submission-Handler Dispatch

**Representative**: Codex CLI (`codex-rs/core/src/codex.rs`, 294 KB) [CX]

Structure: `async fn submission_loop()` with `while let Some(sub) = rx.recv().await` — dispatches `sub.op` to handlers via a large `match` (Op::UserInput, Op::ExecApproval, Op::Compact, Op::InterAgentCommunication, Op::Shutdown, …40+ operation types).

**Core characteristics**:
- Single event loop; all operations routed through `Op` enum, no global state [CX].
- OS-level sandbox: macOS Seatbelt / Linux Landlock / Windows Sandbox [CX].
- Starlark policy engine: Python-like DSL for command approval rules [CX].
- Guardian AI: risk assessment via another LLM [CX] (the official name is "Codex Security"; "Guardian AI" is community terminology).

**Advantages**: type safety, peak performance, OS-level security isolation.
**Cost**: high Rust development and maintenance cost.
**Use when**: enterprise-grade security and approval scenarios.

### Paradigm 3: PubSub Event Loop

**Representative**: OpenCode (`internal/llm/agent/agent.go`, 600 lines) [OC]

Structure: `func (a *agent) Run(ctx, sessionID, content) (<-chan AgentEvent, error)` launches a goroutine. Inside, `provider.StreamResponse(...)` yields events; for each event, `processEvent(event)` handles tool calls / text streaming. Break when `finishReason != "tool_use"`, otherwise `executeTools(ctx, toolCalls)` and loop. Returns the event channel.

**Core characteristics**:
- PubSub decoupling: Agent / Session / Message / Permission each have independent Broker [OC].
- SQLite + WAL persistence; Goose migration manages schema [OC].
- Deep LSP integration: real Language Server (not just syntax highlighting) [OC].
- 75+ Provider support (dynamically loaded via `models.dev`: Anthropic, OpenAI, Gemini, Bedrock, Groq, Ollama, etc.) [OC].

**Advantages**: Go concurrency model naturally fits Agents; PubSub fully decouples UI from logic.
**Cost**: Go's LLM SDK ecosystem is relatively weak.
**Use when**: systems requiring database persistence and real-time event driving.

### Paradigm 4: Reflection Chain

**Representative**: Aider (`aider/coders/base_coder.py`, 859 lines) [AD]

Structure: `run_one(user_message)` initializes, loops `for i in range(max_reflections)` (default 3): send message → parse edits → apply edits → check `is_satisfactory()` to break or refine (`msg = f"Review and improve: {response}"`). Auto-commits at the end.

**Core characteristics**:
- No formal tool system: edit formats agreed via prompt conventions, not function calling [AD].
- Polymorphic edit formats: 6 formats (diff / udiff / patch / whole-file / architect / ask), switched at runtime. In ask mode, Agent only asks questions without editing [AD].
- Repo Map: AST-level codebase index (intelligent summary within token budget) [AD].
- Reflection loop: Agent self-examines output, up to 3 rounds of improvement [AD].

**Advantages**: minimal architecture; prompt drives everything; fastest onboarding.
**Cost**: no tool schema means LLM more prone to output-format errors.
**Use when**: fast prototyping, pair-programming scenarios.

### Paradigm 5: Plugin Gateway Loop

**Representative**: OpenClaw (`src/agents/agent-command.ts`) [OW]

Three-layer architecture:
- **Gateway layer** — multi-channel entry (Telegram / Discord / Slack / Web / CLI / …).
- **Channel layer** — protocol adapter → unified message format.
- **LLM layer** — Agent loop with dynamic Prompt Variant selection by Provider, Skill system (lazy loading + environment-aware filtering), 4 loop detectors + global circuit breaker (30 times), Plugin SDK (5 types: Provider / Channel / Tool / Skill / Memory).

**Core characteristics**:
- Multi-channel gateway: 10+ channels unified, single Agent core serves all channels [OW].
- Plugin SDK: 5 plugin types, `jiti` dynamic import, hot loading [OW].
- Prompt Cache stability: deterministic file sorting ensures cache hit rate [OW].
- 4 loop detectors: signature comparison + echo detection + ping-pong + global circuit breaker [OW].

**Plugin SDK pattern (principle)**: Channel plugin implements `normalize(raw)` (platform raw → `AgentMessage`) and `send(ctx, response)` (response → platform). Provider plugin implements `send(req)` (sync LLM call) and `stream(req)` (async generator). Skill plugin implements `execute(call)` to run a tool call. All registered with `new OpenClaw({ plugins: [...], defaultProvider, defaultModel })`. (Package names `@openclaw/sdk` / `@openclaw/core` are pattern-level; follow OpenClaw official docs for actual API.)

**Advantages**: Agent OS positioning — beyond single IDE/CLI binding.
**Cost**: high architectural complexity; must maintain multi-channel adapter layer.
**Use when**: Agent products needing multi-platform distribution.

### Paradigm 6: Code Generation Loop

**Representative**: smolagents (`src/smolagents/agents.py`, `CodeAgent` class) [SM]

Structure: `CodeAgent.run(task)` maintains `memory: list[Message]`; loop `for step in range(max_steps)`: LLM generates Python `code` given task + memory + tool signatures → `self.executor.run(code)` runs it → append `{"role": "tool", "content": result}` to memory → return when `"final_answer"` appears in `executor.state`.

**Core characteristics**:
- **Python code as action language**: LLM generates `tool_name(arg1, arg2)` Python calls, not `{"name":..., "input":...}` JSON [SM].
- **Persistent state dict**: variables survive across steps — `df = pd.read_csv(...)` in step 1, `df.groupby(...)` in step 2 [SM].
- **Tool → Python signature conversion**: tools auto-converted to `def tool_name(arg: type) -> type: ...` injected into prompt [SM].
- **6-tier executor isolation** — same code, different security boundary:

| Tier | Sandbox | Use Case |
|------|---------|----------|
| Local | ❌ None | Dev only — never production |
| Docker | Process isolation | Staging, trusted code |
| E2B | Firecracker microVM | Production, untrusted code |
| Modal / Blaxel | Cloud serverless | Auto-scaling production |
| Wasm (Deno) | Browser-compatible | Client-side / edge |

**Contrast with Reflection Chain (Paradigm 4)**:

| Dimension | Reflection Chain (Aider) | Code Generation Loop (smolagents) |
|-----------|--------------------------|-----------------------------------|
| Tool invocation | Prompt convention (no function calling) | Python function calls in generated code |
| State persistence | None (each round is stateless) | State dict survives across steps |
| Executor | None (LLM output applied by host) | PythonExecutor AST walker |
| Best fit | Interactive code editing | Batch data pipelines / research tasks |

**Advantages**: natural expression for chained computations (load → transform → visualize → format report); state dict eliminates redundant re-loading between steps.
**Cost**: `LocalPythonExecutor` is NOT sandboxed — arbitrary code execution risk with untrusted input; harder to audit than JSON tool calls.
**Use when**: data analysis / research pipelines / multi-step transformations leveraging the Python ecosystem. **Not** for interactive CLI tools, multi-channel Agents, or untrusted user input without a proper sandbox tier.

## Decision 2: Language Selection

| Language | TUI Framework | LLM SDK Ecosystem | Concurrency Model | Streaming/Audio | Representatives |
|----------|---------------|-------------------|-------------------|-----------------|-----------------|
| **TypeScript** | Ink (React) | Richest | async/await + Worker | Native AsyncGenerator, mature WebSocket | Claude Code, Cline, OpenClaw |
| **Rust** | ratatui | Weak but self-built | Tokio async | Tokio Stream, low latency, high frame-rate audio | Codex CLI, Goose |
| **Go** | Bubble Tea | Moderate | goroutine + channel | goroutine naturally fits frame-by-frame concurrency; channel for backpressure | OpenCode |
| **Python** | Rich / textual | Rich | asyncio | asyncio available but ecosystem fragmented (websockets / aiohttp mixed) | Aider, OpenHands, Letta |
| **Zig** | custom/none | Early stage (need to build HTTP layer) | manual threading/async (no runtime) | Self-evolving Platform (experimental) |

> Zig ecosystem details, known pitfalls, hot-loading patterns → [`references/lang-zig.md`](references/lang-zig.md)

**Selection guidance**:
- **Delivery speed priority** → TypeScript (largest ecosystem, fastest iteration).
- **Performance + security priority** → Rust (OS-level sandbox, zero-cost abstraction).
- **Concurrency + simplicity priority** → Go (goroutine naturally fits Agent concurrency).
- **Prototype + research priority** → Python (fastest onboarding, most LLM libraries).
- **Peak performance + self-evolving Platform** → Zig (comptime invariants, dlopen hot-loading, zero runtime; cost: extremely weak ecosystem, system-level only).

### Provider Aggregation Layer (Multi-Model Unified Interface)

When building your own Provider abstraction, you can optionally reuse aggregation-layer libraries — saving the work of manually writing SDK adapters for each vendor:

| Library | Language | Characteristics | Use When |
|---------|----------|-----------------|---------|
| **LiteLLM** | Python | Unified interface to 100+ models (OpenAI-compatible format), routing/retry/fallback | Python Agent rapid multi-Provider integration |
| **OpenRouter** | HTTP API | Cloud proxy, single API key, no local dependencies | Prototype stage, no need to manage SDK versions |
| **AI SDK (Vercel)** | TypeScript | Unified streaming interface, Provider switching + structured output | TypeScript/JS Agent |
| **llm.rs / llm crate** | Rust | Local GGUF model inference, no API | Offline Rust Agent |

**Build custom** when: peak performance (Rust/Go, reduce middle layer); precise control over streaming event format; production-grade, cannot accept aggregation-layer version dependency risk.

**Reuse aggregation layer** when: prototype stage, need rapid integration of 5+ Providers; Python Agent (LiteLLM is the de facto standard); no need to customize streaming / token billing details.

**Security warning (supply chain)**: model aggregation packages sit on a credential path. Pin reviewed versions, verify provenance/integrity where the ecosystem supports it, minimize runtime privileges, and monitor upstream advisories. → `/agentforge-security`.

## Decision 3: Provider Abstraction

Introduce a provider boundary when the system needs vendor substitution, testing seams, or multiple backends. A single-provider prototype can keep one small adapter without implementing speculative multi-provider features. Example interface [OC]:

```
Provider {
    SendMessages(ctx, messages, tools) → ProviderResponse       // synchronous
    StreamResponse(ctx, messages, tools) → chan ProviderEvent   // streaming
    Model() → models.Model
}
```

### Multi-modal Content Blocks

When an Agent uses image/audio/file input, the `messages` type shifts from `string[]` to `ContentBlock[]`:

- Plain-text Agent: `[{"role": "user", "content": "fix this bug"}]`.
- Multi-modal Agent: `[{"role": "user", "content": [{"type": "text", "text": "..."}, {"type": "image", "source": {...}}, {"type": "document", "source": {...}}]}]`.

**Architectural impact**: if the Provider interface only accepts `string` messages, extending to multi-modal requires a breaking interface change. **Define messages with a `ContentBlock` union type from day one.**

### Event Stream Standardization

Converging design across all Agents:

| Event | Meaning |
|-------|---------|
| ContentStart/Delta/Stop | Text streaming |
| ThinkingDelta | Thinking process (extended thinking) |
| ToolUseStart/Delta/Stop | Tool call |
| Complete | Turn complete |
| Error | Error |

**Token billing must be tracked**: `inputTokens + cacheCreationTokens + cacheReadTokens + outputTokens → totalCost`.

## Paradigm 7: Event-Driven HTTP Webhook

This paradigm is a **passive HTTP trigger**: a platform sends an HTTP request, the service processes the event, acknowledges it, and may enqueue bounded work. A webhook describes ingress and delivery semantics; it does not by itself imply an autonomous Agent loop.

Flow: trigger source (Slack/GitHub/Stripe) → HTTP POST webhook → Agent service (FastAPI/Express) → signature verification (Layer 2-0, see security Phase) → idempotency check (dedupe by `event_id`) → one-shot LLM inference + tool calls → return 200 OK (timeout varies by platform).

**Core characteristics**:
- **No persistent loop**: each HTTP request is an independent execution unit.
- **No conversation history**: each call builds context from scratch; no state across requests.
- **Idempotency mandatory**: webhook platforms retry; the same `event_id` may arrive 2+ times.

**Implementation pattern (principle)**: FastAPI endpoint `POST /webhook/slack/events` — (1) verify signature in middleware; (2) parse payload; (3) idempotency — `redis.set(f"evt:{event_id}", "1", nx=True, ex=3600)`; if the key already exists, ACK immediately; (4) return 200 quickly (Slack 3 s, GitHub 15 s, Stripe 30 s timeouts) and push real work to `asyncio.create_task(process_event(payload))`. The background task runs one-shot inference + tool calls, no cross-request state.

**Key differences from active-loop paradigms**:

| Dimension | Active Loop (1–6) | Event-Driven Webhook (7) |
|----------|---------------------------|------------------------------|
| Trigger | Agent proactively waits | Platform pushes HTTP request |
| State | Persistent across rounds | Stateless, each request independent |
| Context | Conversation history accumulates | Built fresh each time |
| Idempotency | Usually not needed | **Must implement** |
| Timeout constraint | Relaxed (user waiting) | Strict (Slack 3s, GitHub 15s, Stripe 30s) |

**Use when**:
- Trigger is an inbound HTTP webhook? Yes → use this paradigm, then decide whether state is needed across events.
- Trigger is cron or a scheduler? Use a scheduled workflow/job; do not call it a webhook.
- Trigger is a message queue? Use an event consumer/worker and apply the queue's acknowledgement and idempotency semantics.
- Otherwise (user interaction driven) → paradigms 1–6.

**GitHub PR Review shortcut (verified 2026-04-08)**: if the target is GitHub PR Review, **don't build your own webhook server** — use the official Action: `uses: anthropics/claude-code-action@v1` (production: pin to commit hash). Least privilege: `contents: read` + `pull-requests: write`. Cost: ~$0.05 for a 400-line diff (Claude Sonnet 4.6); team of 50 PRs/month < $5. Saves 1–2 days vs self-built FastAPI webhook.

**Pin all Actions to commit hash** (prevent supply chain attacks): `./scripts/pin-action.sh .github/workflows/` (script in `agentforge-architecture/scripts/`, depends on `gh` CLI, skips references already at hash).

## Paradigm 8: Realtime / Voice

All previous paradigms are based on the **request-response** model. Voice/Realtime Agents diverge here, with two implementation paths:

### Path A: Degraded Solution (recommended first attempt)

`Audio → ASR (Whisper / Deepgram) → Text chunks → Async Generator Loop (Paradigm 1)`.

**Pros**: reuse existing loop architecture; tool-calling logic unchanged.
**Cons**: extra 200–500 ms ASR latency; cannot achieve < 500 ms response.
**Use when**: meeting assistants / transcription (no real-time interruption required).

**ASR tool interface (principle)** — streaming data source, not request-response. `TranscriptionStreamTool.stream(audioSource)` is an async generator yielding `{text, timestamp, isFinal}` chunks. Agent loop consumption pattern: accumulate text chunks into a buffer, flush every ~30 seconds (15 chunks or `isFinal`) → trigger one LLM inference on the buffered text → reset buffer.

### Path B: True Realtime Path (< 500 ms scenarios)

`WebSocket persistent connection (bidirectional streaming)` → audio frames continuously streamed (no waiting for complete sentence) → LLM listens and generates speech simultaneously (streaming VAD + streaming TTS) → user interruption sends cancel event and stops current generation → tool calls via WebSocket (not separate HTTP).

Currently supported: OpenAI Realtime API (`gpt-realtime`), Gemini Live API.

**Realtime cost model**: provider prices and audio accounting are changeable facts. Before a cost decision, retrieve current primary pricing and compute `input_audio_units × input_rate + output_audio_units × output_rate + text/tool/cache charges`. Record assumptions, expected speaking/listening ratio, concurrency, and a measured pilot. Compare against the ASR→text→TTS path on both cost and latency; do not reuse historical per-minute examples.

**Additional architectural requirements for Path B**: independent WebSocket state machine (connect/disconnect/reconnect); concurrent conversation isolation (independent WebSocket session per user); interruption handling (cancelEvent + buffer flush); context window management completely different (no "single request" concept).

**Decision**: unless there is a clear < 500 ms latency requirement, prioritize Path A — 10× lower implementation complexity.

## Historical Snapshot (April 2026; re-verify before use)

- **Eight documented paradigms plus “no Agent loop”**: the list is a design catalog, not an exhaustive taxonomy. Fixed DAGs should remain workflows rather than being forced into one of the loop paradigms.
- **Rust Agents rising**: Codex CLI + Goose prove Rust can build full-featured Agents; no longer just "performance scenarios."
- **Plugin Gateway solidified**: OpenClaw evolved from Cline fork to Agent OS; the Gateway/Channel/LLM three-layer has become its own distinct paradigm.
- **Provider interface converging**: all Agents' Provider abstractions look increasingly similar; Send + Stream + Model three-method pattern is now the de facto standard.
- **Bitter Lesson note**: Reflection Chain (Paradigm 4) may weaken as model capabilities grow — stronger models need fewer explicit reflection loops.

## Common Pitfalls

1. **Paradigm and language binding** — The decision tree treats paradigm and language as separate choices, but they're tightly coupled: Submission-Handler almost always means Rust, PubSub almost always means Go. Fix: choose paradigm first, then confirm language constraints; never reverse.
2. **Premature Provider abstraction generalization** — supporting many providers from the start causes interface bloat. Fix: isolate the current provider behind the smallest boundary required by tests and expected substitution; add capabilities only for a concrete second consumer.
3. **Streaming and batch processing mixed** — Async Generator paradigm assumes all output is streamed, but tool execution results often arrive in one batch. Fix: distinguish between "streaming generation" and "completion event" yield types.
4. **Ignoring loop detection** — Dive straight into coding after choosing a paradigm, forget to add infinite-loop protection. All production Agents have loop detection. Fix: plan loop detection during architecture phase, not as an afterthought; see `/agentforge-harness`.
5. **Delayed token billing tracking** — Provider abstraction only handles Send/Stream, forgets to track token consumption. Cost overruns discovered only after going live. Fix: Provider interface must return usage information; track from day one.

## Architecture Checklist

- [ ] Delivery shape selected: fixed workflow, or one of paradigms 1–8; constraints understood
- [ ] Implementation language selected; TUI/SDK ecosystem meets needs
- [ ] Provider boundary matches actual needs: one isolated adapter, or tested support for each required provider
- [ ] `messages` type uses ContentBlock union (supports multi-modal extension; don't use plain string)
- [ ] Event stream format determined (streaming or synchronous)
- [ ] Token billing tracking plan determined (includes image/video token costs)
- [ ] Capability plane determined (input/processing/output) → see `/agentforge-spec`

## Reverse Audit (Diagnose Mode)

> Called by `/agentforge-diagnose` — D1 architecture-dimension static audit.

| # | Check | How | Pass Criteria |
|---|-----------|-------------|---------------|
| A1 | Loop paradigm identifiable | Read entry file, find main loop structure | Can clearly determine paradigm (Blocking / Event / Async / Workflow / Webhook) |
| A2 | Paradigm matches scenario | Confirm Agent type (Webhook/CLI/Service), cross-reference selection table | Paradigm doesn't conflict with type (e.g. Webhook Agent should not have blocking `while` loop) |
| A3 | Cohesive boundaries | Inspect largest/high-churn modules, dependency direction, and tests | Size and coupling do not make independent change or review unsafe; line count is only a navigation signal |
| A4 | Single module responsibility | Check directory structure; loop/tools/prompt/memory independent | No "does everything" central file |
| A5 | No hardcoded config | `grep -rn "api_key\s*=\s*['\"]" src/` | No bare keys, model IDs, or endpoints in source |

**High-risk issues to verify**: hardcoded credentials; unbounded loops; webhook handlers that cannot acknowledge within platform requirements; modules whose coupling repeatedly causes unsafe changes. File length alone does not establish severity.

## Next Steps

After architecture selection → **`/agentforge-tools`** (Phase 2: Tool System Design)
