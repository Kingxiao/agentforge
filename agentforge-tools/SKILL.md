---
name: agentforge-tools
description: Agent tool system design guide. Tool interface design + concurrency strategy + MCP integration + lazy loading + tool count paradox. Triggered when user says "Agent tool system", "tool system", "tool interface", "MCP integration", or "agent tools design".
triggers:
  - Agent tool system
  - tool system
  - tool interface
  - MCP integration
  - agent tools design
metadata:
  version: "2.0.0"
  last_updated: "2026-04-06"
  category: "agent-engineering"
---

# AgentForge Phase 2: Tool System Design

> Previous: `/agentforge-architecture` | Next: `/agentforge-context` | Series entry: `/agentforge`
> Building MCP servers: `/mcp-builder`

## Core Principle

> **More tools ≠ more capability. Vercel improved after deleting 80% of their tools.** [CC]

Reasons:
1. Every tool definition consumes prompt tokens
2. Choice paralysis: the more tools, the easier the LLM picks the wrong one
3. Overlapping functionality causes unpredictable behavior

**Optimal number**: 10-15 core tools, extensions loaded via MCP on demand.

## Decision 1: Tool Interface Design

### Minimum Viable Interface (Prototype Stage)

```
Tool = name + description + inputSchema + call(input) → output
```

Suitable for: prototype validation, < 10 tools, single-person projects

### Production-Grade Interface (Scale Stage)

30+ method tool interface extracted from Claude Code [CC], each method addressing a real product need:

| Method | Addresses What | Required? |
|--------|---------------|----------|
| `call(input, context)` | Execution | Yes |
| `inputSchema` / `outputSchema` | Type safety + API schema generation | Yes |
| `description()` | Static description for LLM | Yes |
| `prompt()` | Dynamic description for LLM (can vary with context) | No |
| `isConcurrencySafe()` | Whether safe to run in parallel | Yes |
| `isReadOnly()` | Affects permission decisions (read-only can be lenient) | Yes |
| `isDestructive()` | High-risk operation marker | No |
| `shouldDefer` | Lazy loading (doesn't occupy prompt space) | No |
| `checkPermissions()` | Tool-level permission check | No |
| `validateInput()` | Pre-execution validation (prevents invalid calls) | Yes |
| `renderToolUseMessage()` | User-facing input rendering | No |
| `renderToolResultMessage()` | User-facing result rendering | No |
| `mapToolResultToToolResultBlockParam()` | API result serialization | Yes |

**Implementation strategy**: Use builder pattern + reasonable defaults to reduce burden.
```
buildTool({ name, schema, call })  // Other methods have safe defaults
```

### Tool Interface Comparison Across Agents

| Agent | Interface Complexity | Method Count |
|-------|---------------------|--------------|
| Claude Code [CC] | Full | 30+ |
| Codex CLI [CX] | Medium (trait + handler) | ~15 |
| OpenCode [OC] | Minimal | 2 (`Info()` + `Run()`) |
| Aider [AD] | No formal interface (prompt-driven) | 0 |
| Cline [CL] | Medium (enum + handler) | 27 tools (ClineDefaultTool enum) |

## Decision 2: Concurrency Strategy

### Partition Strategy [CC] (Recommended)

```
All tool calls
    ↓
[Partition]
    ├─ Concurrency-safe (isConcurrencySafe() = true)
    │   FileRead, Glob, Grep, WebFetch, WebSearch
    │   → Promise.all() / goroutine / rayon
    │
    └─ State-changing (isConcurrencySafe() = false)
        FileWrite, FileEdit, Bash, Git
        → Serial execution
```

**Principle**: Default to serial (safe), explicitly mark concurrency-safe tools for parallelism.

### Concurrency Strategy Comparison Across Agents

| Agent | Strategy |
|-------|----------|
| Claude Code [CC] | Partitioned parallelism (optimal) |
| Cline [CL] | Supports parallel tool calls (model capability dependent) |
| OpenCode [OC] | Serial |
| Codex CLI [CX] | Serial (safety first) |
| Aider [AD] | Serial |

### Semantic Concurrency vs Implementation-Layer Concurrency (Critical Distinction)

**Common misconception**: Bash tool marks `isConcurrencySafe() = false`, so "all Bash calls must be serial."

**Correct understanding**: Concurrency safety is a **semantic property**, not an implementation-layer property. The judgment standard is "would concurrent execution potentially cause race conditions or state corruption?" — not "which executor is used underneath."

```
Judging whether a tool is semantically concurrency-safe:

Would Tool A and Tool B, executed concurrently, affect each other?
├─ Yes (shared file, shared DB, shared process state) → Not concurrency-safe, serial
└─ No (independent resources, read-only, idempotent) → Concurrency-safe, can parallel

Examples:
├─ FileRead("a.py") + FileRead("b.py")      → Concurrency-safe ✓ (read-only, independent)
├─ Bash("eslint src/a.js") + Bash("eslint src/b.js") → Concurrency-safe ✓ (stateless, independent files)
├─ FileEdit("a.py") + FileEdit("b.py")      → Concurrency-safe ✓ (different files, no cross)
├─ FileEdit("a.py") + FileEdit("a.py")      → Not safe ✗ (same file, write-write conflict)
└─ Bash("npm test") + Bash("npm test")      → Not safe ✗ (shared test DB/port)
```

**Practical guidance**: `isConcurrencySafe()` is the tool's default safety declaration. Wrappers around stateless Bash commands (lint, format, read-only analysis) can override to `true`, but must document the rationale in comments. Global serial is the safe fallback, not the optimal solution.

### IterationBudget with Refund Pattern [HR]

Beyond parallelization, tool execution cost can be managed at the **iteration budget** level. Hermes Agent uses a thread-safe counter passed top-down through agent and subagents:

```python
class IterationBudget:
    def consume() -> bool   # Returns False if exhausted (caller should wrap up)
    def refund()            # Undo a consumption — used after programmatic execution
    @property remaining: int
    @property used: int
```

The key insight: `execute_code` calls `refund()` after programmatic execution completes. Code that runs via tool (single call, batch output) doesn't burn budget the same way as 20 individual tool calls would.

**Effect**: the model is subtly incentivized to use code for loops rather than calling the same tool 20 times — because loop-via-code costs 1 budget unit, while 20 separate tool calls cost 20.

**Budget pressure injection**: warnings are injected as a `_budget_warning` key inside the last tool result JSON (not as a separate message), which preserves prompt cache structure while still alerting the model:

```
0-70%  → no warning
70-90% → "consider wrapping up" nudge
90%+   → "urgent: final N iterations"
```

**When to use**: any long-running agent where users might issue open-ended tasks that could expand indefinitely. Parent cap (e.g. 90), subagent cap (e.g. 50) — parent + children can exceed parent cap combined, which is intentional: subagent work shouldn't block parent.

## Decision 3: Tool Registration Method

### Static Registration [OC]

```go
func CoderAgentTools() []tools.BaseTool {
    return []tools.BaseTool{
        tools.NewBashTool(),
        tools.NewEditTool(),
        tools.NewGlobTool(),
        tools.NewGrepTool(),
        tools.NewViewTool(),
        tools.NewWriteTool(),
    }
}
```

**Suitable for**: Fixed tool set, no runtime changes needed

### Dynamic Registration [CC]

```
assembleToolPool(context)
    ├─ filter(featureFlags)        // Feature gates
    ├─ filter(userPermissions)     // User rejection rules
    ├─ filter(agentContext)        // Sub-agent restrictions
    ├─ filter(pluginSettings)      // Plugin toggles
    └─ + loadMCPTools()            // MCP dynamic discovery
```

**Suitable for**: Tools need runtime changes (permissions, plugins, sub-agent scenarios)

### Lazy Loading [CC]

```
Initial prompt only exposes tool name + one-line description
    ↓
LLM retrieves full schema via ToolSearch tool when needed
    ↓
Reduces token footprint in system prompt
```

**Suitable for**: Must consider when tool count > 20

### CLI Tool First Principle

**If a CLI tool is already in the LLM's training data, prefer invoking it via Bash rather than wrapping it as an MCP tool.** The LLM already "knows" how to use `git`, `grep`, `curl` and other tools. Additional MCP wrapping only adds complexity without adding capability. Vercel improved after deleting 80% of their custom tools — that's why.

## Decision 4: MCP Integration

MCP (Model Context Protocol) is the standard protocol for tool extension. All mainstream Agents support it.

### Integration Pattern [OC]

```go
// 1. Configure MCP servers
config.MCPServers = map[string]MCPServer{
    "database": {Type: "stdio", Command: "mcp-server-postgres"},
}

// 2. Dynamic tool discovery at startup
for _, server := range mcpServers {
    tools := server.ListTools()
    for _, tool := range tools {
        register(fmt.Sprintf("%s_%s", server.Name, tool.Name), tool)
    }
}

// 3. Route to corresponding server at execution time
func (t *mcpTool) Run(ctx, call) (ToolResponse, error) {
    return t.server.CallTool(ctx, t.originalName, call.Input)
}
```

**Transport protocols**: stdio (local, recommended) or SSE (remote)

### MCP Integration Checklist

- [ ] Supports both stdio and SSE transports
- [ ] Tool names prefixed with server name (`{server}_{tool}`) to prevent conflicts
- [ ] Reconnection mechanism when server crashes
- [ ] Server tool list supports dynamic refresh

## Decision 5: Core Tool Set

**Recommended minimum tool set** (suitable for coding agents):

| Tool | Functionality | Concurrency Safe? |
|------|--------------|------------------|
| `Bash` | Shell command execution | No |
| `FileRead` | Read file contents | Yes |
| `FileWrite` | Create new file | No |
| `FileEdit` | Precise replacement edit | No |
| `Glob` | File pattern search | Yes |
| `Grep` | Content regex search | Yes |
| `WebFetch` | HTTP requests | Yes |
| `WebSearch` | Web search | Yes |
| `Agent` | Spawn sub-agent | No |

**Extended tools** (add on demand):
- `LSP` — Language Server Protocol (code intelligence)
- `Notebook` — Jupyter notebook editing
- `Todo` — Task management
- `Plan` — Plan mode switching

## External API Call Tool Design

When an Agent calls external APIs (REST/gRPC/database writes) through tools, three production-grade challenges must be handled: idempotency, retry, rate limiting. These three issues must be declared at the tool interface design stage — otherwise Agent retries will produce duplicate side effects.

**Three production-grade problems and handling principles**:

**Idempotency**: Write operations (POST/PUT/DELETE) must declare idempotency. Prefer `Idempotency-Key` header (supported by Stripe/OpenAI), fallback to "check-then-act." Expose idempotency key to the Agent rather than silently handling internally.

**Retry**: Only retry idempotent operations + recoverable errors (5xx/timeout/rate limit); do not retry 4xx. Exponential backoff + jitter, prefer `retry-after` header.

**Rate limiting**: Client-side proactive rate limiting (token bucket / sliding window). Feed `x-ratelimit-remaining` back to the Agent so it can perceive quota status. **When multiple tools share the same API, use a shared rate limiter** — see "Multi-tool shared rate limiting" below.

**Tool interface extensions** (must declare for production-grade API tools):
| Method | Purpose |
|--------|---------|
| `isIdempotent()` | Declare idempotency (affects Agent retry decisions) |
| `getRateLimitKey()` | Return shared rate limiter key (same key = shared limiting) |
| `getMaxRetries()` | Declare max retry count |
| `requiresIdempotencyKey()` | Force Agent to pass idempotency key |

Full code implementation → [`references/external-api-tools.md`](references/external-api-tools.md)

## External API Pagination Handling

List-type interfaces all have pagination. Improper handling causes the Agent to **see only the first page and assume data is complete**, leading to wrong decisions.

**Three pagination modes**: cursor (`next_cursor`/`has_more`), page_token (Google style), offset/limit (older REST, `items.length < limit` signals end).

**Implementation Key Points**:
1. **Hard cap**: `MAX_PAGES=10` (prevents infinite pagination from bugs)
2. **Token budget truncation**: When exceeded, return `truncated=true` + `next_cursor` (enables Agent to resume pagination)
3. **Tool description must explain pagination**: `"When results are truncated, response contains next_cursor field. Use cursor=<value> to resume"`

| Interface Method | Purpose |
|-----------------|---------|
| `supportsPagination()` | Declare pagination support (LLM-aware) |
| `getMaxPages()` | Return hard cap |
| `resumeFromCursor(cursor)` | Resume from cursor (cross-turn continuation) |

**Full PaginatedAPITool implementation** → [`references/external-api-tools.md`](references/external-api-tools.md)

## Multi-Tool Shared Rate Limiting (Concurrency-Safe Rate Limit Coordination)

**Problem**: Multiple tools concurrently call the same rate-limited API (e.g., Confluence = 5 RPM). Each tool rate-limits independently, but concurrent calls collectively still exceed limit and trigger 429.

**Solution**: Process-level shared rate limiter registry — `get_shared_limiter(endpoint_key, rpm)` caches singleton by endpoint. All tools with the same endpoint get the same RateLimiter instance. Concurrent calls automatically queue.

**Tool interface declaration**:
```python
def getRateLimitKey(self) -> str:
    return "confluence.company.com"  # Tools with same key share one rate limiter
```

Full implementation → [`references/external-api-tools.md`](references/external-api-tools.md)

## Tool Error Handling

**Key principle**: Agent reads error messages to self-correct. Error message quality directly determines correction efficiency.

**Anti-pattern**: `Error: operation failed`
**Correct approach**:
```
Error: File 'src/auth.ts' not found.
Did you mean 'src/auth/index.ts'?
Use the Glob tool to search for files matching 'auth'.
```

**Schema validation failure** gives field-level errors:
```
Validation error: 'file_path' must be an absolute path.
Received: 'src/main.rs'
Expected: '/absolute/path/to/src/main.rs'
```

### Policy-as-Schema Pattern [HR]

Behavioral policy for tool use is typically placed in the system prompt. Hermes embeds it directly into the tool's schema `description` field — the model receives it as part of the tool definition, not buried in a long system prompt:

```python
skill_manage_schema = {
    "name": "skill_manage",
    "description": """Create, update, or delete skills.

    CREATE when:
    - A complex task succeeded (5+ tool calls) and you want the approach reusable
    - You overcame an error not covered by any existing skill
    - A user-corrected approach worked — capture the correction immediately

    UPDATE when:
    - Existing skill instructions are stale or wrong
    - You encountered an OS-specific failure the skill didn't anticipate
    - You found a missing step during actual use — patch immediately

    DELETE when:
    - Skill is superseded by a better automated tool
    - Instructions are platform-specific and no longer apply

    If you used a skill and hit issues not covered by it, patch it in the same session.
    """,
    "parameters": { ... }
}
```

**Why this works**: Tool descriptions are loaded at every turn as part of the tool list — the model cannot "forget" them the way it can lose track of a system prompt rule buried on page 3. Policy placed in the schema is always in context when the tool is relevant.

**When to use**: For tools where the "when to use this" judgment is complex and situation-dependent (skill management, memory writes, delegation decisions). Not for simple tools where the name is self-explanatory.

**Trade-off**: Inflates tool description token cost. Only use for tools with non-obvious invocation heuristics.

## Decision 6: Prompt Variants Tool Adaptation [CL]

Different LLMs support tool calling differently. Cline's approach: provide different tool definition variants by model family.

### Dual-Track Strategy

```
ClineToolSet
    ├─ Native tool use (models supporting function calling)
    │   Claude, GPT-4, Gemini, etc.
    │   → Directly use API native tool_use format
    │
    └─ XML fallback (models not supporting function calling)
        Ollama local models, older APIs, etc.
        → Serialize tool definitions as XML into system prompt
        → Parse XML tags in LLM output to extract tool calls
```

### Fallback Chain

```
Detect model capability
    ↓
Supports native tool use?
    ├─ Yes → Use native tool_use parameter
    └─ No → Convert tool schema to XML template injected into prompt
              ↓
           Parse <tool_name>...</tool_name> tags in response
              ↓
           Map back to standard ToolCall structure
```

**Design implications**:
- Tool system cannot assume all models support function calling
- Tool definitions (schema) must be decoupled from calling protocol (native vs XML)
- One tool set, two serialization formats, switch at runtime by model capability
- This is the Provider abstraction layer's responsibility, should not infiltrate tool implementation

## Decision 7: Next-Generation Capability Types

> The following capabilities generalized during 2024-2025. Before making any tool system architecture decisions, must declare which capability planes the Agent uses — different planes have cascading effects on Phase 1-5.

### Three-Plane Capability Framework

```
Input Plane           Processing Plane                Output Plane
──────────           ──────────────────              ──────────────────
Text                  Tool Use (function calling)      Text (structured/unstructured)
Image          →      Extended Thinking   →          JSON Schema
Audio                  Code Interpreter                Image generation
Video                  Web Search/Grounding            Audio/speech
File                   Computer-use execution          Actions (click/keyboard)
Real-time stream        Batch Processing
```

**Three-plane selection's downstream cascading effects:**
- Input includes image/video → Phase 3 must account for visual token cost (~1500 tokens/image)
- Processing includes Computer-use → Phase 5 security assessment changes dramatically (GUI operation surface far larger than Bash)
- Processing includes Code Interpreter → Tools have persistent state, breaks "tools are stateless" assumption
- Output includes Structured JSON → Replaces max_tokens as output control — doesn't truncate, constrains format

### Computer-use (GUI Automation)

Action space = mouse + keyboard, observation = screenshots, not function calling.

```
Screenshot → LLM understands UI → click/type action → screenshot → loop
```

- Anthropic: `computer_20251124` tool (screenshot, click, key, type)
- Goose: `computercontroller` MCP server (cross-platform, `goose-mcp/computercontroller/`)
- OpenHands: Playwright runtime (`extensions/browser/pw-session.ts`)

**Key constraint**: Each step screenshot ~1500 tokens. 50-step task = 75,000 tokens just for images. Must implement screenshot compression/deduplication.

### Structured Output

Forces model output conforming to JSON Schema. Replaces max_tokens as output control — doesn't truncate, constrains format.

```python
# OpenAI mode
response_format = {"type": "json_schema", "json_schema": {...}}

# Anthropic mode: tool-as-output
# Define a tool that only returns values and has no side effects, forcing model to fill schema
```

Letta implementation: `ResponseFormatType` enum (text / json_schema / json_object)

### Code Interpreter (Sandboxed Execution)

Persistent sandbox: variables and imports persist across calls, unlike ordinary tools (each call independent).

- **E2B** (production-grade cloud sandbox): `AsyncSandbox.run_code()` — Python/TypeScript
- **Modal** (distributed computing): High-concurrency batch execution
- **Local sandbox**: `LocalPythonSandbox` / `LocalNodeSandbox` (Letta implementation)

**Architecture note**: Sandbox is stateful middleware, requires explicit session lifecycle management (create→use→destroy).

### File / Document Upload

Injects file content into context via API rather than local file reading.

```
User file → Files API storage → file_id → reference in message → LLM reads
```

**Security warning**: PDF/Office documents can contain prompt injection attacks. Must scan content before uploading. → See `/agentforge-security`

### Realtime / Voice (Real-time Streaming)

**Fundamental difference**: WebSocket bidirectional stream, not HTTP request-response. <500ms latency constraint.
All current 5 loop paradigms (see `/agentforge-architecture`) are request-response based. Realtime requires a separate architecture.

- OpenAI Realtime API: WebSocket + audio stream
- Google Gemini Live API: Low-latency bidirectional interaction
- OpenClaw: `realtime-voice/provider-registry.ts` (multi-provider registry)

## Capability Freshness Check (Must Execute Before Any Selection)

> AI capabilities have major updates every quarter. The capabilities documented here have a cutoff date and **must not be used as final decision basis**.
> Before confirming any capability selection, use **WebFetch** to get the following real-time data:

**Must check (every Agent selection)**:

| Purpose | Real-time Data Source |
|---------|----------------------|
| Anthropic latest capabilities & changelog | https://platform.claude.com/docs/changes |
| OpenAI latest capabilities & changelog | https://platform.openai.com/docs/changelog |
| Google Gemini latest capabilities | https://ai.google.dev/gemini-api/docs/changelog |
| Model comprehensive rankings (quality + cost + speed) | https://artificialanalysis.ai/ |
| Coding-specific rankings | https://aider.chat/docs/leaderboards/ |
| API real-time pricing (200+ models) | https://openrouter.ai/models |

**Check as needed (for specific decisions)**:

| Purpose | Real-time Data Source |
|---------|----------------------|
| Embedding model rankings | https://huggingface.co/spaces/mteb/leaderboard |
| Arena ELO (general dialogue quality) | https://lmarena.ai/ |
| Long context support comparison | https://www.morphllm.com/llm-context-window-comparison |
| LLM inference cost trends | https://epoch.ai/data-insights/llm-inference-price-trends/ |

**Execution protocol**:
1. WebFetch corresponding platform changelog → Confirm needed capabilities are GA (not Beta)
2. WebFetch artificialanalysis.ai → Confirm current best cost-performance model
3. When this skill's content diverges from real-time data, **real-time data takes precedence**

## Current State (April 2026)

1. **MCP becoming de facto standard** — Anthropic's Model Context Protocol adopted by OpenAI, Google, Microsoft and other major vendors. Tool interoperability problem essentially solved. Custom tool protocols are no longer necessary.
2. **Streamable HTTP replacing SSE** — MCP transport migrating from SSE to Streamable HTTP. Supports stateless deployment and horizontal scaling. Production environment deployment complexity greatly reduced.
3. **Tool simplification trend accelerating** — Industry consensus shifting from "provide more tools" to "provide more precise tools." Vercel, Cursor and other teams publicly shared cases of performance improvement after tool reduction. 10-15 core tools + MCP on-demand loading becoming mainstream.
4. **Agent-to-Agent tool sharing emerging** — Google's A2A protocol enables cross-Agent tool calls. Tools no longer bound to single Agents. Tool registry rising from Agent-internal to platform layer.
5. **Tool call security auditing becoming essential** — As Agents enter production environments, security features for tool calls — audit logs, fine-grained permission control, call frequency limits — shifting from optional to mandatory. → For permission design see `/agentforge-security`; for observability see `/agent-observability`.

## Streaming Data Source Tool Pattern

> **Applicable scenarios**: Real-time transcription, log tailing, WebSocket pushes, Server-Sent Events — not "call once, return result," but "call once, continuously produce data chunks."

Request-response tools with `call()` are unsuitable for streaming data sources. Fundamental difference:

| | Request-Response Tool | Streaming Data Source Tool |
|---|---|---|
| Call pattern | `result = tool.call(input)` | `async for chunk in tool.stream(input)` |
| Data arrival | Returns when all ready | Arrives chunk by chunk, latency <500ms |
| State | Stateless | Stateful (maintains connection/cursor) |
| Cancellation | Not needed | Must implement `close()` |

### Streaming Tool Interface

```python
class StreamingTool(BaseTool):
    """Base class for streaming data source tools. call() fetches latest N historical items;
    stream() continuously receives incremental data chunks."""

    async def call(self, input: dict) -> ToolResult:
        """Fetch recent N completed items (snapshot, non-streaming, for initial context fill)"""
        raise NotImplementedError

    async def stream(self, input: dict) -> AsyncGenerator[ToolResult, None]:
        """Continuously produce incremental data chunks"""
        raise NotImplementedError

    async def close(self) -> None:
        """Close underlying connection (must implement)"""
        raise NotImplementedError
```

### Meeting Transcription Tool Example

```python
class TranscriptionStreamTool(StreamingTool):
    """
    Wraps real-time transcription WebSocket stream into Agent Loop-consumable tool.
    Core design: don't let WebSocket callbacks directly call LLM — write to queue,
    Agent Loop consumes in batches at its own pace (prevents LLM from being
    swamped by partial transcripts every 300ms).
    """

    def __init__(self, deepgram_api_key: str):
        self.api_key = deepgram_api_key
        self.buffer: asyncio.Queue[str] = asyncio.Queue()
        self._ws: Optional[WebSocket] = None

    async def call(self, message: dict) -> ToolResult:
        """Get most recent N completed sentences (snapshot)"""
        recent = list(self.buffer._queue)[-input.get("n", 5):]
        return ToolResult(output="\n".join(recent))

    async def stream(self, input: dict) -> AsyncGenerator[ToolResult, None]:
        """
        Push a batch of transcription results to Agent Loop every batch_seconds.
        Partial transcripts accumulate internally to avoid LLM token waste.
        """
        batch_seconds = input.get("batch_seconds", 30)
        batch: list[str] = []
        async for event in self._connect():
            if event.is_final:
                batch.append(event.text)
            # Flush batch when batch_seconds or sentence count threshold reached
            if self._should_flush(batch, batch_seconds):
                yield ToolResult(output="\n".join(batch), metadata={"is_final": True})
                batch.clear()

    async def close(self) -> None:
        if self._ws:
            await self._ws.close()
```

### Agent Loop Adaptation

Streaming tools change the Agent Loop's control mechanism — not user message triggering, but data stream triggering:

```python
async def streaming_agent_loop(
    stream_tool: StreamingTool,
    batch_seconds: int = 30,
):
    """
    Data stream-driven Agent Loop:
    Triggers one LLM processing whenever enough new data accumulates (batch_seconds).
    """
    async for chunk in stream_tool.stream({"batch_seconds": batch_seconds}):
        # Append new content to context (not full refresh)
        context.append_transcript_chunk(chunk.output)

        # Trigger LLM analysis per batch
        response = await llm.call([
            {"role": "system", "content": ANALYSIS_PROMPT},
            {"role": "user",   "content": context.get_recent(token_budget=4000)},
        ])

        # Process LLM output (push summary, trigger notifications, etc.)
        await handle_response(response)
```

**Key constraints**:
- `batch_seconds` is a trade-off between latency and cost: shorter latency means lower cost but more frequent LLM calls
- Context append strategy: append incremental data rather than resend full context (prevents token linear explosion)
- Long-running processes must implement `close()` and call it when Agent stops

> Full implementation → `references/streaming-tools.md`

---

## LLM-as-Tool Pattern (P25)

**Definition**: Encapsulate one LLM API call as the implementation body of a tool — not just using LLM to call tools, but reversing the roles. Typical scenario: classification, entity extraction, sentiment judgment, format conversion — logically a "tool" (has clear input/output), but using LLM is more reliable than rules.

```python
from dataclasses import dataclass
from anthropic import Anthropic

# Model selection dimensions (specific IDs and pricing must be verified via WebFetch artificialanalysis.ai before use):
# Ultra-low cost → current cheapest nano-level model (Gemini / GPT / Haiku, all vendors have nano tier)
# Medium cost → mini-level model, balances cost and quality
# High quality → frontier-level model (Claude Sonnet / GPT-5 standard tier, etc.)
# Selection principle: simple classification uses nano, complex intent/compliance judgment uses frontier; cost difference can be 10-50x

@dataclass
class ClassificationResult:
    category: str
    confidence: float
    reasoning: str

class ClassifyMessageTool:
    """LLM-as-Tool: classification tool, implementation is LLM call"""

    CATEGORIES = ["bug_report", "feature_request", "question", "noise"]

    def __init__(self, client: Anthropic, model: str = os.getenv("CLASSIFY_MODEL", "claude-haiku-4-5-20251001")):  # verified: 2026-04-08
        self.client = client
        self.model = model  # Replace based on selection decision above

    def call(self, message: str) -> ClassificationResult:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=200,
            system=(
                "You are a message classifier. Classify the given message into exactly one of: "
                "bug_report, feature_request, question, noise. "
                "Respond in JSON: {\"category\": \"...\", \"confidence\": 0.0-1.0, \"reasoning\": \"...\"}"
            ),
            messages=[{"role": "user", "content": message}],
        )
        import json
        data = json.loads(response.content[0].text)
        return ClassificationResult(**data)
```

**Key difference from ordinary tools**:

| Dimension | Ordinary Tool | LLM-as-Tool |
|-----------|-------------|-------------|
| Implementation | API call / rules / DB query | LLM API call |
| Output determinism | Deterministic | Probabilistic (needs confidence threshold) |
| Cost | Fixed | Floats with token count |
| Applicable scenarios | Structured operations | Semantic judgment, classification, extraction |

**Low-confidence handling**:
```python
result = classify_tool.call(message)
if result.confidence < 0.7:
    # Degrade: send to human review queue, rather than blindly proceeding
    await send_to_human_review(message, result)
```

## Known Pitfalls

1. **Tool explosion syndrome** — Creating separate tools for each API endpoint, causing tool count to balloon to 50+. LLM tool selection accuracy drops off a cliff. Solution: Merge similar tools into parameterized tools (e.g., `database_query` instead of `get_users` / `get_orders` / `get_products`). Keep core tools to 15 or fewer.
2. **MCP cold-start latency** — stdio-transport MCP servers have 2-5 second latency on first call due to process startup, causing poor user experience. Solution: Implement MCP server connection pool + pre-warm mechanism, or use Streamable HTTP transport + resident service.
3. **Tool description and schema drift** — Tool's description and inputSchema inconsistent. LLM understands function from description but constructs parameters from schema, causing call failures. Solution: Auto-generate descriptions from schema, or add schema-description consistency check in CI.
4. **Concurrency safety marking missing** — Default to all tools serial execution causing poor performance, but blindly marking concurrency-safe causes race conditions. Solution: Strictly enforce "default serial + explicit concurrency-safe marking" strategy. Document concurrency safety rationale for each tool.
5. **Tool result truncation silently failing** — Tool returns huge results (e.g., reading entire log file), silently truncated. LLM makes decisions based on incomplete information. Solution: Tool layer implements result size check. When exceeded, return summary + pagination hint instead of silent truncation.

## Further Reading

| Topic | Resource |
|-------|----------|
| Tool interface complete reference (30+ methods) | [`references/tool-interface-full.md`](references/tool-interface-full.md) |
| External API tool full implementation (idempotency/retry/pagination/shared rate limiting) | [`references/external-api-tools.md`](references/external-api-tools.md) |
| Concurrency strategy detailed comparison | [`references/concurrency-strategies.md`](references/concurrency-strategies.md) |
| Edit format comparison (Patch/precise replacement/unified diff) | [`references/edit-format-comparison.md`](references/edit-format-comparison.md) |
| Tool call permissions & sandbox | `/agentforge-security` |
| Tool call observability | `/agent-observability` |
| Building MCP servers | `/mcp-builder` |

## Tool System Checklist

- [ ] Tool interface defined (at minimum: name, schema, call, validateInput)
- [ ] Each tool annotated with concurrency safety
- [ ] Tool partitioned concurrency implemented (read-only parallel / write serial)
- [ ] Error messages include fix suggestions
- [ ] Total tool count ≤ 15 (core) + MCP on-demand
- [ ] Supports MCP stdio transport

## Reverse Audit (Diagnose Mode)

> Invoked by `/agentforge-diagnose` — D2 tool dimension static audit of existing code.

| # | Check Item | How to Check | Pass Criteria |
|---|-----------|-------------|--------------|
| T1 | Tool count reasonable | `grep -rn "@tool\|def.*tool\|register_tool\|add_tool" src/ \| wc -l` | ≤ 10 core tools (≤ 15 including MCP) |
| T2 | Tool descriptions clear | Read tool registration code, check docstring/description fields | Each tool has clear usage documentation |
| T3 | Supports concurrent execution | `grep -rn "Promise.all\|asyncio.gather\|go func\|concurrent.futures" src/` | Has concurrency patterns OR explicit "serial by design" comment |
| T4 | Large data not passed directly | Check tool return value handling, look for large file/image operations | Binary/large files use path references, not embedded in messages |
| T5 | Tool results have limits | `grep -rn "max_length\|truncat\|limit" src/ \| grep -i tool` | Tool return results have max_tokens or length control |

**High-probability problems**: Tool count > 15 (success rate drops P1), all tools serial with no concurrency (latency P2), no tool descriptions (LLM picks wrong tool P1)

## Next Step

Tool system design complete → **`/agentforge-context`** (Phase 3: Context Engineering)
