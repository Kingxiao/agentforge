---
name: agentforge-tools
disable-model-invocation: true
description: Internal AgentForge Phase 2 tool-system guide. Load only when explicitly named or selected by the agentforge router; do not auto-trigger for generic tools, interfaces, MCP, or integration questions.
triggers:
  - Agent tool system
  - tool system
  - tool interface
  - MCP integration
  - agent tools design
metadata:
  version: "2.0.0"
  last_updated: "2026-04-11"
  category: "agent-engineering"
---

# AgentForge Phase 2: Tool System Design

> Previous: `/agentforge-architecture` | Next: `/agentforge-context` | Series entry: `/agentforge`
> Building MCP servers: `/mcp-builder`

## Core Principle

> **More tools ≠ more capability. Vercel improved after deleting 80% of their tools.** [CC]

Reasons: (1) every tool definition consumes prompt tokens, (2) choice paralysis — the more tools, the easier the LLM picks the wrong one, (3) overlapping functionality causes unpredictable behavior.

**Optimal number**: 10–15 core tools, extensions loaded via MCP on demand.

## Decision 1: Tool Interface Design

### Minimum Viable Interface (Prototype)

`Tool = name + description + inputSchema + call(input) → output`. Good for prototype validation, < 10 tools, single-person projects.

### Production-Grade Interface (Scale)

Extracted from Claude Code [CC] — 30+ methods, each addressing a real product need:

| Method | Addresses | Required? |
|--------|---------|----------|
| `call(input, context)` | Execution | Yes |
| `inputSchema` / `outputSchema` | Type safety + API schema | Yes |
| `description()` | Static description for LLM | Yes |
| `prompt()` | Dynamic description (varies with context) | No |
| `isConcurrencySafe()` | Whether safe to run in parallel | Yes |
| `isReadOnly()` | Permission decisions (read-only can be lenient) | Yes |
| `isDestructive()` | High-risk marker | No |
| `shouldDefer` | Lazy loading (doesn't occupy prompt space) | No |
| `checkPermissions()` | Tool-level permission check | No |
| `validateInput()` | Pre-execution validation | Yes |
| `renderToolUseMessage()` / `renderToolResultMessage()` | User-facing rendering | No |
| `mapToolResultToToolResultBlockParam()` | API result serialization | Yes |

**Implementation strategy**: Builder pattern + reasonable defaults. `buildTool({ name, schema, call })` — other methods inherit safe defaults.

### Tool Interface Comparison Across Agents

| Agent | Interface Complexity | Method Count |
|-------|---------|--------------|
| Claude Code [CC] | Full | 30+ |
| Codex CLI [CX] | Medium (trait + handler) | ~15 |
| OpenCode [OC] | Minimal | 2 (`Info()` + `Run()`) |
| Aider [AD] | No formal interface (prompt-driven) | 0 |
| Cline [CL] | Medium (enum + handler) | 27 tools (ClineDefaultTool enum) |

### Purpose-Built Tools Over Generic Tools [SWE]

SWE-agent (Princeton/Stanford, NeurIPS 2024): domain-specific tools outperform generic bash+file tools for coding. The underlying mechanism: better-structured inputs → better LLM decisions. **Key question for each tool**: "what is the minimum information the agent needs to make the right next decision?" — not "what can the agent do?"

**Constrained output > comprehensive output**: `search_dir <term>` should return filenames + match counts **only** — not context snippets or line previews. Empirically, models performed worse when search showed snippet context. Succinct output forces deliberate navigation.

**View windowing as a feature**: `str_replace_editor view <file>` shows 100 lines + line numbers, truncated at 16K chars. LLMs reason better in small windows; forces navigation (scroll/search) rather than processing the whole file.

**Linter feedback as immediate error signal**: After every `str_replace` edit, flake8 runs automatically. If syntax invalid, the edit is still applied but the model gets immediate feedback: `<NOTE>Your edits have been applied, but the linter has found syntax errors.</NOTE><ERRORS>line 42: unexpected indent</ERRORS>`. This collapses the edit→verify→fix loop from 3 steps to 1.

**Exact-match editing (`str_replace`) > line-based editing**: Require `--old_str` and `--new_str`. Forces agent to VIEW the file before editing (must see exact text to specify it), prevents off-by-one errors, self-documenting (old_str shows what's being changed), atomic.

**Blocklists are ACI decisions, not just security**: SWE-agent blocks `vim`, `nano`, `emacs`, `gdb`, `less`, `tail -f`, bare `python`. Forces the intended workflow (view → search → str_replace) rather than ad-hoc interactive patterns that the framework can't supervise. **Rule**: Every blocked tool is an implicit statement that there is a better, supervisable alternative.

**Empty output should be explicit**: `"Your command ran successfully and did not produce any output."` — without this, agents infer from silence that the command failed, or loop trying again.

**ACI Design Checklist** (apply to every new tool):
- [ ] What is the minimum output format the agent needs? (remove everything else)
- [ ] Does full output contain noise that hurts reasoning? → Add truncation/filtering
- [ ] Is there a feedback loop? (linter, validation, success confirmation)
- [ ] Does the tool encourage bad workflows if used naively? → Add blocklist/constraint
- [ ] Can the agent make irreversible mistakes? → Add undo or dry-run mode

## Decision 2: Concurrency Strategy

### Partition Strategy [CC] (Recommended)

Partition tool calls by `isConcurrencySafe()` → concurrency-safe (FileRead, Glob, Grep, WebFetch, WebSearch) run via `Promise.all()` / goroutine / rayon; state-changing (FileWrite, FileEdit, Bash, Git) run serial.

**Principle**: Default to serial (safe); explicitly mark concurrency-safe tools for parallelism.

### Concurrency Strategy Comparison

| Agent | Strategy |
|-------|----------|
| Claude Code [CC] | Partitioned parallelism (optimal) |
| Cline [CL] | Supports parallel tool calls (model-capability dependent) |
| OpenCode [OC] | Serial |
| Codex CLI [CX] | Serial (safety first) |
| Aider [AD] | Serial |

### Semantic Concurrency vs Implementation-Layer Concurrency

Concurrency safety is a **semantic property**, not an implementation property. Judgment standard: "would concurrent execution potentially cause race conditions or state corruption?" — not "which executor is used underneath."

Examples:
- `FileRead("a.py") + FileRead("b.py")` → safe (read-only, independent)
- `Bash("eslint src/a.js") + Bash("eslint src/b.js")` → safe (stateless, independent files)
- `FileEdit("a.py") + FileEdit("b.py")` → safe (different files)
- `FileEdit("a.py") + FileEdit("a.py")` → **not safe** (write-write conflict)
- `Bash("npm test") + Bash("npm test")` → **not safe** (shared test DB/port)

**Practical guidance**: `isConcurrencySafe()` is the tool's default safety declaration. Wrappers around stateless Bash commands (lint, format, read-only analysis) can override to `true`, but must document the rationale. Global serial is the safe fallback, not the optimal solution.

### IterationBudget with Refund Pattern [HR]

Beyond parallelization, tool execution cost can be managed at the **iteration budget** level. Hermes uses a thread-safe counter passed top-down through agent and subagents:

- `consume()` → returns False if exhausted (caller wraps up).
- `refund()` → undoes a consumption. Key insight: `execute_code` calls `refund()` after programmatic execution completes. Code that runs via tool (single call, batch output) doesn't burn budget the same way as 20 individual tool calls would.

**Effect**: model is subtly incentivized to use code for loops rather than calling the same tool 20 times — loop-via-code costs 1 budget unit, 20 separate tool calls cost 20.

**Budget pressure injection**: inject warnings as a `_budget_warning` key inside the last tool result JSON (not as a separate message) — preserves prompt-cache structure. Thresholds: 0–70% no warning; 70–90% "consider wrapping up" nudge; 90%+ "urgent: final N iterations."

**When to use**: long-running agents where users might issue open-ended tasks. Parent cap (e.g. 90), subagent cap (e.g. 50) — parent + children can exceed parent cap combined (subagent work shouldn't block parent).

## Decision 3: Tool Registration Method

**Static registration [OC]**: fixed list at startup, no runtime changes. Good for fixed tool sets.

**Dynamic registration [CC]**: `assembleToolPool(context)` filters by feature flags → user permissions → agent context (sub-agent restrictions) → plugin settings → adds MCP tool discovery. Good when tools must change at runtime (permissions, plugins, sub-agents).

**Lazy loading [CC]**: initial prompt only exposes tool name + one-line description; LLM retrieves full schema via `ToolSearch` tool when needed. Reduces system-prompt token footprint. Consider when tool count > 20.

### CLI Tool First Principle

**If a CLI tool is already in the LLM's training data, prefer invoking it via Bash rather than wrapping it as an MCP tool.** The LLM already "knows" `git`, `grep`, `curl`, etc. Additional MCP wrapping adds complexity without adding capability. Vercel improved after deleting 80% of their custom tools — that's why.

## Decision 4: MCP Integration

MCP (Model Context Protocol) is the standard protocol for tool extension. All mainstream Agents support it.

### Integration Pattern [OC]

1. **Configure MCP servers** (stdio local or SSE/Streamable HTTP remote).
2. **Dynamic tool discovery at startup** — list server tools, register each as `{server}_{tool}` (prefixed to prevent conflicts).
3. **Route to server at execution time** — tool's `Run(ctx, call)` delegates to `server.CallTool(...)`.

### MCP Integration Checklist

- [ ] Supports stdio AND Streamable HTTP transports
- [ ] Tool names prefixed with server name to prevent conflicts
- [ ] Reconnection mechanism when server crashes
- [ ] Server tool list supports dynamic refresh

## Decision 5: Core Tool Set

**Recommended minimum (coding agents)**:

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

**Extensions (on demand)**: `LSP`, `Notebook`, `Todo`, `Plan`.

### Tool Design by ACI Class

| ACI Pattern | Tool Design Implication |
|-------------|------------------------|
| View windows | 100 lines max; always include line numbers; truncate at 16K chars |
| Succinct search | Filenames/counts only; separate snippet-access tool |
| Exact-match edit | Require old_str + new_str; validate match before applying |
| Linter feedback | Run formatter/linter after every write; report errors in-band |
| Atomic endpoints | Single `submit`/`done`/`finish` tool capturing final state |
| Blocklist | Block interactive/infinite tools; provide supervisable alternatives |

## External API Call Tool Design

When the Agent calls external APIs (REST/gRPC/database writes) through tools, three production-grade challenges must be handled: **idempotency, retry, rate limiting**. Declare at interface design stage — otherwise Agent retries will produce duplicate side effects.

- **Idempotency**: Write ops (POST/PUT/DELETE) must declare idempotency. Prefer `Idempotency-Key` header (Stripe/OpenAI style); fallback to "check-then-act". Expose the key to the Agent rather than silently handling it.
- **Retry**: Only retry idempotent ops + recoverable errors (5xx / timeout / rate-limit). Do not retry 4xx. Exponential backoff + jitter. Prefer server's `retry-after` header.
- **Rate limiting**: Client-side proactive limiting (token bucket / sliding window). Feed `x-ratelimit-remaining` back to the Agent. **When multiple tools share the same API, use a shared rate limiter**.

**Tool interface extensions for production API tools**:

| Method | Purpose |
|--------|---------|
| `isIdempotent()` | Declares idempotency (affects retry decisions) |
| `getRateLimitKey()` | Shared rate limiter key (same key = shared limiting) |
| `getMaxRetries()` | Max retry count |
| `requiresIdempotencyKey()` | Force Agent to pass idempotency key |

> Full code → [`references/external-api-tools.md`](references/external-api-tools.md)

## External API Pagination Handling

List-type interfaces all have pagination. Improper handling causes the Agent to see only the first page and assume data is complete, leading to wrong decisions.

**Three pagination modes**: cursor (`next_cursor` / `has_more`), page_token (Google style), offset/limit (older REST — `items.length < limit` signals end).

**Implementation key points**:
1. **Hard cap**: `MAX_PAGES=10` (prevents infinite pagination from bugs).
2. **Token budget truncation**: when exceeded, return `truncated=true` + `next_cursor` so Agent can resume.
3. **Tool description must explain pagination**: "When results are truncated, response contains `next_cursor`. Use `cursor=<value>` to resume."

Interface extensions: `supportsPagination()`, `getMaxPages()`, `resumeFromCursor(cursor)`.

## Multi-Tool Shared Rate Limiting

**Problem**: Multiple tools concurrently call the same rate-limited API (e.g. Confluence = 5 RPM). Each tool rate-limits independently, but concurrent calls collectively still exceed limit.

**Solution**: Process-level shared rate limiter registry — `get_shared_limiter(endpoint_key, rpm)` caches a singleton by endpoint. All tools with the same `getRateLimitKey()` (e.g. `"confluence.company.com"`) share one RateLimiter; concurrent calls automatically queue.

## Tool Error Handling

**Key principle**: Agent reads error messages to self-correct. Error message quality directly determines correction efficiency.

**Anti-pattern**: `Error: operation failed`

**Correct**:
```
Error: File 'src/auth.ts' not found.
Did you mean 'src/auth/index.ts'?
Use the Glob tool to search for files matching 'auth'.
```

**Schema validation failure** gives field-level errors (`'file_path' must be an absolute path. Received: 'src/main.rs'. Expected: '/absolute/path/...'`).

### Policy-as-Schema Pattern [HR]

Behavioral policy for tool use is typically placed in the system prompt. Hermes embeds it directly into the tool's schema `description` field — the model receives it as part of the tool definition, not buried in a long system prompt.

Example: a `skill_manage` tool's description spells out CREATE/UPDATE/DELETE criteria inline ("CREATE when: a complex task succeeded with 5+ tool calls and you want the approach reusable", "UPDATE when: existing skill instructions are stale…").

**Why it works**: tool descriptions are loaded every turn as part of the tool list — the model cannot "forget" them the way it loses track of a system-prompt rule buried on page 3. Policy placed in the schema is always in context when the tool is relevant.

**When to use**: tools where the "when to use this" judgment is complex and situation-dependent (skill management, memory writes, delegation decisions). Not for simple tools where the name is self-explanatory. **Trade-off**: inflates tool-description token cost.

### CodeAgent: Code as Action Language [SM]

smolagents (HuggingFace) demonstrates an alternative to JSON tool calls: the LLM generates Python code that calls tools directly. Tools become Python-callable functions.

Instead of `{"name": "search", "arguments": {"query": "python async patterns"}}`, the agent generates:

```python
results = search("python async patterns")
filtered = [r for r in results if "asyncio" in r["title"]]
summary = summarize(filtered[:3])
final_answer(summary)
```

**Why more efficient**: Python syntax is more compact than JSON for chained operations; variables persist across steps without re-serialization; multiple tool calls can occur within one LLM output; partial state (print outputs, assigned variables) survives exceptions.

**Persistent state executor**: `PythonExecutor` holds a `state: dict` that persists across all steps. AST-walks execution — each assignment updates `self.state`; tools registered in `state["search"] = search_tool`; variables survive between steps. Tools are NOT actually converted to Python functions — they remain callable objects; the signature the LLM sees is documentation only.

**Executor isolation tier** (required decision):

| Tier | Executor | Isolation | Use For |
|------|----------|-----------|---------|
| Dev | LocalPythonExecutor | NONE (AST sandbox only) | Trusted LLM output, local dev |
| Staging | DockerExecutor | Container | CI/testing |
| Production | E2BExecutor (Firecracker VM) | OS-level | Untrusted input, user-facing |
| Browser | WasmExecutor (Deno) | Deno permissions | Web/serverless |

**Anti-pattern**: LocalPythonExecutor is NOT a security tool (explicitly documented by HuggingFace). Never use for code influenced by untrusted users.

**When to use CodeAgent vs. JSON ToolCalling**:
- Use **CodeAgent** when: multi-step workflows with state sharing, complex data transformations, loops/conditionals needed.
- Use **JSON** when: simple single-tool calls, model doesn't reliably generate syntactically valid Python, structured output is required.

## Decision 6: Prompt Variants Tool Adaptation [CL]

Different LLMs support tool calling differently. Cline's approach: dual-track strategy.

- **Native tool use** (Claude, GPT-4, Gemini, etc.) → directly use API's native `tool_use` format.
- **XML fallback** (Ollama local models, older APIs) → serialize tool definitions as XML in the system prompt; parse `<tool_name>…</tool_name>` tags in LLM output to extract tool calls.

**Design implications**: tool system cannot assume all models support function calling; tool definitions (schema) must be decoupled from calling protocol (native vs XML); one tool set, two serialization formats, switch at runtime by model capability. This is the Provider abstraction layer's responsibility — should not infiltrate tool implementation.

## Decision 7: Next-Generation Capability Types

> AI capabilities generalized during 2024–2025. Before any tool-system architecture decision, declare which capability planes the Agent uses — each plane has cascading effects on Phases 1–5.

### Three-Plane Capability Framework

```
Input Plane           Processing Plane                Output Plane
──────────           ──────────────────              ──────────────────
Text                  Tool Use (function calling)      Text (structured/unstructured)
Image          →      Extended Thinking   →            JSON Schema
Audio                 Code Interpreter                  Image generation
Video                 Web Search / Grounding            Audio / speech
File                  Computer-use execution            Actions (click/keyboard)
Real-time stream      Batch Processing
```

**Downstream cascade**:
- Input includes image/video → Phase 3 must account for visual token cost (~1500 tokens/image).
- Processing includes Computer-use → Phase 5 security assessment changes dramatically (GUI operation surface far larger than Bash).
- Processing includes Code Interpreter → tools have persistent state, breaks the "tools are stateless" assumption.
- Output includes Structured JSON → replaces `max_tokens` as output control — doesn't truncate, constrains format.

### Computer-use (GUI Automation)

Action space = mouse + keyboard, observation = screenshots, not function calling. Loop: screenshot → LLM understands UI → click/type action → screenshot → loop.

- Anthropic: `computer_20251124` tool (screenshot, click, key, type)
- Goose: `computercontroller` MCP server (cross-platform)
- OpenHands: Playwright runtime

**Key constraint**: each step screenshot ~1500 tokens. 50-step task = 75,000 tokens just for images. Must implement screenshot compression/deduplication.

### Structured Output

Forces model output conforming to JSON Schema. Replaces `max_tokens` as output control. OpenAI mode: `response_format = {"type": "json_schema", "json_schema": {…}}`. Anthropic mode: "tool-as-output" — define a tool that only returns values and has no side effects, forcing the model to fill the schema.

### Code Interpreter (Sandboxed Execution)

Persistent sandbox: variables and imports persist across calls, unlike ordinary tools (each call independent). Options: **E2B** (production cloud sandbox, Firecracker), **Modal** (distributed high-concurrency), local sandbox (LocalPythonSandbox / LocalNodeSandbox). Architecture note: sandbox is stateful middleware — requires explicit session lifecycle management (create → use → destroy).

### File / Document Upload

Injects file content into context via API rather than local file reading: `User file → Files API storage → file_id → reference in message → LLM reads`.

**Security warning**: PDF/Office documents can contain prompt injection attacks. Must scan content before uploading. → `/agentforge-security`

### Realtime / Voice (Real-time Streaming)

**Fundamental difference**: WebSocket bidirectional stream, not HTTP request-response. <500 ms latency constraint. All 5 standard loop paradigms (see `/agentforge-architecture`) are request-response based — Realtime requires a separate architecture. Options: OpenAI Realtime API, Google Gemini Live API, OpenClaw `realtime-voice/provider-registry.ts`.

## Capability Freshness Check (Must Execute Before Any Selection)

> AI capabilities have major updates every quarter. Anything documented here has a cutoff date and **must not be used as final decision basis**. Before confirming any selection, **WebFetch** the following real-time data:

**Must check, every Agent selection**:

| Purpose | Real-time Source |
|---------|----------------------|
| Anthropic latest capabilities & changelog | https://platform.claude.com/docs/changes |
| OpenAI latest capabilities & changelog | https://platform.openai.com/docs/changelog |
| Google Gemini latest capabilities | https://ai.google.dev/gemini-api/docs/changelog |
| Model comprehensive rankings (quality + cost + speed) | https://artificialanalysis.ai/ |
| Coding-specific rankings | https://aider.chat/docs/leaderboards/ |
| API real-time pricing (200+ models) | https://openrouter.ai/models |

**Check as needed**:

| Purpose | Real-time Source |
|---------|----------------------|
| Embedding model rankings | https://huggingface.co/spaces/mteb/leaderboard |
| Arena ELO (general dialogue quality) | https://lmarena.ai/ |
| Long context support comparison | https://www.morphllm.com/llm-context-window-comparison |
| LLM inference cost trends | https://epoch.ai/data-insights/llm-inference-price-trends/ |

**Execution protocol**: (1) WebFetch platform changelog → confirm needed capabilities are GA, not Beta. (2) WebFetch artificialanalysis.ai → confirm current best cost-performance model. (3) When this skill's content diverges from real-time data, **real-time data takes precedence**.

## Agent Tools vs Domain Tools: Two Tool Categories

Agent systems depend on two categories of tools that require different selection criteria:

| Dimension | Agent Tools | Domain Tools |
|-----------|------------|--------------|
| **What** | Tools the Agent calls via function calling / MCP | Libraries and frameworks the Agent's code depends on but doesn't "call" through the Agent protocol |
| **Examples** | WebSearch, FileRead, DatabaseQuery, API calls | Backtesting engines (VectorBT), ML frameworks (PyTorch), rendering engines (Three.js), data analysis (pandas) |
| **Selection guided by** | This Phase — interface design, concurrency, lazy loading | **User's domain expertise** — agentforge cannot evaluate domain tool quality |
| **Who evaluates** | Agent can search and evaluate (MCP registry, tool count paradox, etc.) | User must evaluate or search independently |

**Why this matters**: agentforge-tools covers Agent tool design comprehensively (Decisions 1–12). But many Agent systems also depend on domain tools the Agent doesn't "call" — it uses them in its generated code. These are invisible to the Agent tool interface but critical to system functionality.

**Guidance**: when your Agent operates in a specialized domain, identify domain tools early (Phase 0 Spec) and evaluate them independently. Search for current framework comparisons and benchmarks in your domain — this Phase cannot provide domain-specific recommendations because they change faster than the skill can track.

## Current State (April 2026)

1. **MCP becoming de facto standard** — Anthropic's Model Context Protocol adopted by OpenAI, Google, Microsoft. Tool interoperability essentially solved. Custom tool protocols no longer necessary.
2. **Streamable HTTP replacing SSE** — MCP transport migrating from SSE to Streamable HTTP. Supports stateless deployment and horizontal scaling.
3. **Tool simplification trend accelerating** — Industry consensus shifting from "provide more tools" to "provide more precise tools." Vercel, Cursor publicly shared performance improvements after tool reduction.
4. **Agent-to-Agent tool sharing emerging** — Google's A2A protocol enables cross-Agent tool calls. Tools no longer bound to single Agents.
5. **Tool-call security auditing becoming essential** — As Agents enter production, audit logs, fine-grained permission control, call-frequency limits shifting from optional to mandatory. → `/agentforge-security`, `/agent-observability`.

## Streaming Data Source Tool Pattern

> **Applicable**: real-time transcription, log tailing, WebSocket pushes, SSE — "call once, continuously produce data chunks", not "call once, return result."

Request-response tools with `call()` are unsuitable for streaming. Fundamental difference:

| | Request-Response | Streaming Data Source |
|---|---|---|
| Call pattern | `result = tool.call(input)` | `async for chunk in tool.stream(input)` |
| Data arrival | Returns when all ready | Arrives chunk by chunk, latency <500 ms |
| State | Stateless | Stateful (maintains connection/cursor) |
| Cancellation | Not needed | Must implement `close()` |

### Streaming Tool Interface

A `StreamingTool` base class provides three methods: `call(input)` fetches recent N completed items as a snapshot (non-streaming, for initial context fill); `stream(input)` is an async generator that continuously yields incremental data chunks; `close()` closes the underlying connection (must implement).

### Design Principles for Streaming Tools

**Example — meeting transcription**: wrap a real-time Deepgram WebSocket stream into an Agent-Loop-consumable tool. Core design: **don't let WebSocket callbacks directly call the LLM**. Instead, write to an internal queue and let the Agent Loop consume in batches at its own pace — otherwise the LLM gets swamped by partial transcripts every 300 ms. `stream()` accumulates partial transcripts internally, only flushing a batch when `batch_seconds` elapses or a sentence-count threshold is reached.

**Agent Loop adaptation**: streaming tools change the Loop's control mechanism — not user-message triggering, but data-stream triggering. The loop awaits chunks from `stream_tool.stream({"batch_seconds": 30})`, appends each chunk incrementally to context (not full refresh), then triggers one LLM processing per batch.

**Key constraints**:
- `batch_seconds` is a latency/cost trade-off: shorter latency = more frequent LLM calls.
- Context append strategy: append **incremental** data, don't resend full context (prevents token linear explosion).
- Long-running processes must implement `close()` and call it when the Agent stops.

> Full implementation → [`references/streaming-tools.md`](references/streaming-tools.md)

## LLM-as-Tool Pattern (P25)

**Definition**: Encapsulate one LLM API call as the implementation body of a tool — not just using LLM to call tools, but reversing the roles. Typical use cases: classification, entity extraction, sentiment judgment, format conversion — logically a "tool" (clear input/output), but using LLM is more reliable than rules.

**Model selection (must verify via WebFetch artificialanalysis.ai)**:
- Ultra-low cost → current cheapest nano-level model (Gemini / GPT / Haiku nano tier)
- Medium cost → mini-level, balances cost and quality
- High quality → frontier-level (Claude Sonnet / GPT-5 standard tier)
- **Principle**: simple classification uses nano; complex intent/compliance judgment uses frontier. Cost difference 10–50×.

**Example shape**: `ClassifyMessageTool.call(message)` internally calls `client.messages.create(...)` with a system prompt that spells out the allowed categories and demands JSON output `{"category": ..., "confidence": 0.0-1.0, "reasoning": ...}`. The result becomes a typed `ClassificationResult`.

**Key difference from ordinary tools**:

| Dimension | Ordinary Tool | LLM-as-Tool |
|-----------|-------------|-------------|
| Implementation | API / rules / DB query | LLM API call |
| Output determinism | Deterministic | Probabilistic (needs confidence threshold) |
| Cost | Fixed | Floats with token count |
| Applicable scenarios | Structured operations | Semantic judgment, classification, extraction |

**Low-confidence handling**: if `result.confidence < 0.7`, **degrade** — route to human review queue, don't blindly proceed.

## Known Pitfalls

1. **Tool explosion syndrome** — Creating separate tools for each API endpoint inflates tool count to 50+; LLM selection accuracy drops off a cliff. Fix: merge similar tools into parameterized tools (e.g. `database_query` instead of `get_users` / `get_orders` / `get_products`). Keep core tools ≤ 15.
2. **MCP cold-start latency** — stdio MCP servers have 2–5 s first-call latency due to process startup. Fix: connection pool + pre-warm, or use Streamable HTTP + resident service.
3. **Tool description / schema drift** — LLM understands function from description but constructs parameters from schema; inconsistency causes call failures. Fix: auto-generate descriptions from schema, or add consistency check in CI.
4. **Concurrency safety marking missing** — All-serial is slow; blind parallel causes race conditions. Fix: strictly enforce "default serial + explicit concurrency-safe marking"; document rationale per tool.
5. **Tool result truncation silently failing** — Huge results (e.g. reading entire log file) silently truncated; LLM decides on incomplete info. Fix: tool layer implements result size check; return summary + pagination hint instead of silent truncation.

## Further Reading

| Topic | Resource |
|-------|----------|
| Tool interface complete reference (30+ methods) | [`references/tool-interface-full.md`](references/tool-interface-full.md) |
| External API tool full implementation | [`references/external-api-tools.md`](references/external-api-tools.md) |
| Concurrency strategy detailed comparison | [`references/concurrency-strategies.md`](references/concurrency-strategies.md) |
| Edit format comparison | [`references/edit-format-comparison.md`](references/edit-format-comparison.md) |
| Tool call permissions & sandbox | `/agentforge-security` |
| Tool call observability | `/agent-observability` |
| Building MCP servers | `/mcp-builder` |

## Tool System Checklist

- [ ] Tool interface defined (at minimum: name, schema, call, validateInput)
- [ ] Each tool annotated with concurrency safety
- [ ] Partitioned concurrency implemented (read-only parallel / write serial)
- [ ] Error messages include fix suggestions
- [ ] Total tool count ≤ 15 (core) + MCP on demand
- [ ] Supports MCP stdio transport

## Reverse Audit (Diagnose Mode)

> Called by `/agentforge-diagnose` — D2 tool dimension static audit.

| # | Check | How to Check | Pass Standard |
|---|-----------|-------------|--------------|
| T1 | Tool count reasonable | `grep -rn "@tool\|register_tool\|add_tool" src/ \| wc -l` | ≤ 10 core tools (≤ 15 including MCP) |
| T2 | Tool descriptions clear | Read registration code; check docstring/description | Each tool has clear usage documentation |
| T3 | Supports concurrent execution | `grep -rn "Promise.all\|asyncio.gather\|go func" src/` | Concurrency patterns OR explicit "serial by design" comment |
| T4 | Large data not passed directly | Check tool return handling | Binary/large files use path references, not embedded |
| T5 | Tool results have limits | `grep -rn "max_length\|truncat\|limit" src/ \| grep -i tool` | `max_tokens` or length control |

**High-probability issues**: Tool count > 15 (P1 — success rate drops), all tools serial with no concurrency (P2 — latency), no tool descriptions (P1 — LLM picks wrong tool).

## Next Step

Tool system design complete → **`/agentforge-context`** (Phase 3: Context Engineering)
