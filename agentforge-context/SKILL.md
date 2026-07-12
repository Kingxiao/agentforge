---
name: agentforge-context
disable-model-invocation: true
description: Internal AgentForge Phase 3 context guide. Load only when explicitly named or selected by the agentforge router; do not auto-trigger for ordinary context, prompt, cache, or compaction questions.
triggers:
  - agent context
  - context engineering
  - prompt cache
  - auto compact
  - context compression
metadata:
  version: "2.1.0"
  last_updated: "2026-04-12"
  category: "agent-engineering"
---

# AgentForge Phase 3: Context Engineering

> Previous: `/agentforge-tools` | Next: `/agentforge-memory` | Series entry: `/agentforge`
> Prompt optimization: `/prompt-optimizer`

## Core Principles

Context engineering is the agent's "cognitive bandwidth management." Five first principles:

1. **Context windows are finite** — Even 200K tokens fill up fast in multi-step tasks.
2. **Context decays** — Longer inputs degrade model performance (all models).
3. **Caching is a cost lever** — Prompt Cache hits reduce input token costs by ~90%.
4. **Progressive disclosure beats flooding** — Provide information on demand.
5. **Compression is mandatory** — Long sessions need mechanical context compression.

> **Empirical anchor (verified 2026-04-12)**: Anthropic's multi-agent research team decomposed performance variance on the BrowseComp benchmark (https://www.anthropic.com/engineering/multi-agent-research-system, 2025-06-13) and found **"token usage by itself explains 80% of the variance"** in performance; token usage + number of tool calls + model choice together explain **95%** of variance. Translation: **how you fill the context is a bigger lever than which model you pick.** Context engineering is not a nice-to-have — it is the single largest performance knob in a multi-agent system.

## Decision 1: Layered System Prompts

### System Prompt Layering Architecture [CC]

Instruction loading system has 4 layers (priority low → high):
- **Layer 1 — Global system instructions** (`/etc/claude-code/CLAUDE.md`)
- **Layer 2 — User global instructions** (`~/.claude/CLAUDE.md`)
- **Layer 3 — Project instructions** (`CLAUDE.md`, `.claude/CLAUDE.md`, `.claude/rules/*.md`)
- **Layer 4 — Local instructions** (`CLAUDE.local.md`, git-ignored)

Plus `MEMORY.md` (~/.claude/MEMORY.md), truncated to 25KB, managed independently by the memdir subsystem. Functionally a 5th layer but implemented separately.

**Constraints** [CC]:
- Single file max 40,000 chars
- MEMORY.md max 200 lines / 25,000 bytes
- Supports `@include` directive (`@./path`, `@~/path`, `@/path`)
- Has circular reference detection

### Directory-Level Progressive Disclosure [CC]

Place `CLAUDE.md` at directory boundaries — project root (global rules), `src/` (module patterns), `src/api/` (endpoint rules), `tests/` (test conventions). When the agent enters a directory, that directory's CLAUDE.md loads into context; released on leave.

### Agent Comparison

| Agent | Instruction File | Layers | Progressive Disclosure |
|-------|---------|--------|--------|
| Claude Code [CC] | CLAUDE.md | 5 layers | Yes (directory-level) |
| Codex CLI [CX] | AGENTS.md | 2 layers | No |
| OpenCode [OC] | .opencode.json contextPaths | 1 layer | No |
| Cline [CL] | Modular prompt variants | 1 layer | No (switches by model) |
| OpenHands [OH] | .openhands/ + microagents | 2 layers | Yes (task-based) |
| OpenClaw [OW] | Deterministic ordering + cache boundaries | Multi-layer | Yes (deterministic ordering ensures cache stability) |

## Decision 2: Prompt Cache

### Mechanics

API caches consecutive identical prefixes. Cache hits reduce input token costs by ~90%.

### Static/Dynamic Separation [CC]

```
System Prompt
├── [STATIC] Identity, guidelines, rules, tool definitions
│   → cache_control: {"type": "ephemeral"}           # 5-minute cache (default)
│   → or {"type": "ephemeral", "ttl": "1h"}           # 1-hour cache (2025 addition)
│
├── SYSTEM_PROMPT_DYNAMIC_BOUNDARY ← cache boundary
│
└── [DYNAMIC] MCP state, conversation context, Git status
    → Recalculated every turn, not cached
```

For very large rarely-changing prompts, use `ttl: 1h` (write 2x vs 1.25x, same 0.1x read). Session-level context stays on the 5-minute default.

**Optimization**:
- Minimize dynamic sections — every uncached section is a cost.
- MCP tool definitions are typical cache busters (connect/disconnect changes the tool list).
- Claude Code has `promptCacheBreakDetection` to detect what operations break the cache [CC].

### Prompt Cache Stability Techniques [OW]

OpenClaw stabilizes cache hit rates via:
- **Deterministic file ordering** — files in system prompts are sorted deterministically (not filesystem traversal order), preventing cache prefix invalidation.
- **Explicit cache boundary markers** — isolate high-frequency changing parts outside the cache zone.

### Practical Benefit

Assuming 10,000-token system prompt: no cache $0.03/turn ($3/MTok). With cache: first turn $0.0375 (write), subsequent turns $0.003 (read). **~50-turn session saves ~$1.35.**

## Decision 3: Context Compression (Auto-Compact)

### Trigger Conditions

| Agent | Trigger | Compression Method |
|-------|---------|---------|
| Claude Code [CC] | Token usage exceeds threshold | 4 strategies: auto-compact / micro-compact / context-collapse / snip |
| OpenCode [OC] | 95% context window | Separate summarizer agent |
| Aider [AD] | On model switch | Auto-summarize history |
| Letta [LT] | Memory overflow | Sliding window + archival |
| OpenHands [OH] | Near window limit | Dual-mode Condenser: View / Condensation |

### Claude Code's 4-Strategy System [CC]

Four strategies, coarse to fine: **auto-compact** (session-wide when tokens exceed threshold), **micro-compact** (single overly-long message), **context-collapse** (fold tool-call results, keep signatures, compress outputs), **snip** (truncate oversized outputs, keep head+tail).

Pipeline when threshold hit: group messages by API turn → fork subprocess (don't block main loop) → LLM generates summary → tool_use gets its own summary generator → insert `compact boundary` marker → trigger POST_COMPACT hook.

### OpenHands Dual-Mode Dynamic Compression [OH]

Condenser has two modes — **View** (keep all messages, no compression — short sessions / debugging) and **Condensation** (LLM compresses full history to structured summary when context approaches window limit). Runtime switches based on token usage.

### Implementation Essentials

1. **Don't wait for overflow** — Use `/compact` proactively after completing a logical unit.
2. **Summarize tool outputs separately** — Long tool outputs have their own summarization logic.
3. **Trigger hook after compression** — Update cache, refresh file state after compression.

## Decision 4: Repo Map (Codebase Index)

**Aider's AST approach [AD]**: `RepoMap.get_repo_map()` parses source files via tree-sitter, extracts function signatures / class definitions / import relationships, packs into a token budget (default ~1024 tokens). Advantage: global skeleton from round one. Cost: AST parsing overhead + tree-sitter dependency.

**Claude Code's alternative [CC]**: No pre-built index. Instead: `Glob` (filename), `Grep` (content), `ToolSearch` (lazy tool schemas). More flexible but costs additional API turns per lookup.

**Selection guidance**: < 50 files → search tools suffice; 50–500 files → Repo Map has clear benefits; > 500 files → Repo Map mandatory + strict token budget.

## Decision 5: Deferred Tools (Lazy Loading)

40+ tools' JSON Schemas can consume 5,000+ tokens. Most tools aren't used in most conversations.

**Solution [CC]**: Initial prompt exposes only tool names + one-line descriptions. When the agent needs a tool, it calls `ToolSearch(query="file search")` to get the full JSON Schema. **Effect: system prompt token usage reduced by 60–70%.**

## Decision 6: system-reminder Tag System

Agent needs to inject system info (git status, CLAUDE.md, notifications) mid-conversation, but must semantically distinguish from user input.

**Solution [CC]**: Wrap in `<system-reminder>…</system-reminder>`. System prompt explicitly tells the model: "content in these tags comes from the system, unrelated to the surrounding message context."

The tag name **"reminder" vs "instruction"** reduces risk of malicious prompt-injection exploitation [CC].

## Decision 7: Information Position Optimization (Lost in the Middle)

LLMs have uneven attention — beginning and end of context are reliably remembered; middle portions are easily forgotten. Proven by Liu et al., 2023 *Lost in the Middle*.

### Application Principles

- **Most important** (task goal, decision constraints) → system prompt beginning.
- **Second important** (historical decisions, key state) → latest user message each turn.
- **Tool results** → immediately after the triggering tool call (don't batch).
- **Background material** (codebase overview, docs) → avoid the exact middle of the sequence.

**Prompt Cache synergy**: static instructions at system prompt beginning (high attention + high cache hit), dynamic info at the end (high attention + allows changes) — best of both.

### Visual Input Token Cost

Image inputs are token sinks — declare in Phase 0 Spec:

| Image Size | Approximate Token Cost |
|---------|------------|
| Small (<500px) | ~300–500 tokens |
| Medium (800–1200px) | ~800–1200 tokens |
| Large / Screenshot (Full HD) | ~1500–2000 tokens |
| Computer-use screenshot (per step) | ~1500 tokens × number of steps |

A 10-step GUI task ≈ 15,000 tokens in image costs alone. Screenshots per step can't be skipped (visual feedback drives the loop) but reducing resolution saves 30–50%.

### Large Text Content Truncation Strategy (Webhook / Tool-output Agent)

Tool-returned text (PR diffs, web page body, file contents) is unpredictable in size — truncation strategy must be designed in Phase 3.

| Scenario | Typical Size | Truncation Strategy |
|---------|---------|---------|
| GitHub PR diff (large PR) | 5K–50K tokens | Prioritize changed lines; skip binary/lock/auto-generated files |
| Web page scraped content | 2K–20K tokens | Extract body paragraphs, remove nav/footer/ads HTML |
| Log files | 10K–500K tokens | Keep only ERROR/WARN lines + 10 lines context around each |
| Full code file | 2K–30K tokens | Return only lines matching keywords + function signatures |

**Truncation algorithm (principle)**: Parse by file → filter binary/auto-gen patterns (`*.lock`, `*.min.*`, `*.pb.go`, binary assets) → sort remaining files by changed-line density descending → fit into token budget greedily → when budget runs out on a file, keep only first N lines with `[truncated M lines]` marker.

**Must inform LLM after truncation**: Inject `[diff truncated at N tokens, M files skipped]` so the agent doesn't assume the diff is complete.

### Extended Thinking Compression Exception

Standard auto-compact cannot compress Extended Thinking's reasoning chain — the chain is the model's internal intermediate reference; compression breaks subsequent turns that reference prior reasoning conclusions. Implementation: if the agent uses Extended Thinking, compression strategy must keep thinking blocks intact **or** discard them entirely — no partial summarization. Mark thinking blocks separately when calculating context budget.

## Decision 8: Multi-Tenant / Multi-Project Context Management

When a single agent instance serves multiple users, repos, or projects, system prompts cannot be static — each request needs different coding standards, project architecture, security policies. This is the core architectural difference between **Platform Agents** (multi-channel gateways, SaaS) and **single-user CLI Agents**.

### Context Isolation Layers

- **Static layer** (shared across tenants, strong cache): agent core capability description, tool definitions, global security policies.
- **Dynamic layer** (built per request, not cached): tenant context (coding standards, architecture), user session state (memory, preferences), current task context (working directory, git status).

**Prompt Cache key principle**: static layer at system prompt beginning with `cache_control: {"type": "ephemeral"}`, dynamic layer after the boundary. Larger dynamic layer = lower cache hit rate — the core cost trade-off in multi-tenant architectures. For very large system prompts (>10K tokens) the 1h cache option reduces write frequency (verified: 2026-04-08).

### Multi-Repo System Prompt Routing

**Builder pattern (principle)**: Load global system prompt once at startup (static prefix). Per request, load tenant config (coding standards) + repo context (project CLAUDE.md). Assemble message with static prefix first (marked `cache_control: ephemeral`), then dynamic layer (`## Current Project` + tenant config + repo context) after the cache boundary. Static hits cache across all tenants; dynamic rebuilt per request without cache pollution.

### Preventing Context Leakage

Dangerous failure mode: User A's context leaking into User B's responses.

- **Build context independently per request** — don't reuse the previous request's messages array.
- **Explicit session ID isolation** — components use `session_id + tenant_id` as namespace key.
- **Physically isolate history storage** — different tenants' conversation histories stored separately.
- **Explicit declaration in system prompt** — inject `<context scope="tenant:{id}">` so the model knows context boundaries.

### Dynamic Context Content Sources

| Content Type | Source | Cache Strategy |
|---------|------|---------|
| Global rules/capabilities | Static config file | Strong cache (cache_control) |
| Project/repo standards | Repo CLAUDE.md | Per-project cache (content hash) |
| User preferences | User memory system | Per-user cache |
| Current git status | Real-time fetch | Not cached |
| Task context | Current request | Not cached |

**Selection routing**: Multi-tenant + complex context routing → prefer PubSub Event Loop (OpenCode style) or Plugin Gateway (OpenClaw style) — these paradigms have built-in support for multi-tenant isolation. See `/agentforge-architecture`.

## Decision 9: RAG Retrieval Result Token Budget Management

When RAG agents inject retrieved fragments into context, three questions need quantitative answers: how many fragments? how many tokens each? how to truncate when over budget? Misconfiguration causes precision degradation or cost explosion.

### Token Budget Allocation (32K window as reference)

- System prompt + tool definitions: ~3,000 tokens (9%)
- Conversation history (compressed): ~5,000 tokens (16%)
- Retrieved results: ~12,000 tokens (37%) ← focus of this decision
- Current question + generation space: ~12,000 tokens (38%)

**Key parameters (start defaults, adjust via RAGAS eval)**:

| Parameter | Recommended Default | Description |
|------|-----------|------|
| Initial retrieval top-K | 20 | More is better; rerank filters later |
| Injected top-N (after rerank) | 5 | Precision/recall balance point |
| Token limit per fragment | 400 tokens | Truncate excess from tail |
| Total retrieval token budget | Available × 80% | Dynamic, not hardcoded |

### Two-Stage Retrieval (Retrieve → Rerank)

1. **Vector retrieval** — query vector → FAISS / Qdrant / pgvector → top-K=20 by cosine similarity. Fast (ms) but similarity ≠ relevance.
2. **Rerank** — top-20 → Cross-Encoder Reranker (Cohere Rerank, BGE-Reranker) → top-N=5 by exact relevance. Slower but much more precise. Reranker is usually 10–100× cheaper than LLM — high-cost-performance precision lift.

### Fragment Injection Format

Wrap in `<retrieved_documents>` with per-doc metadata: `id`, `source` (traceability + audit + Faithfulness basis), `score` (credibility — model can mark low-score as "limited reference"), `date` (timeliness — deprioritize stale docs). Source must **never** be truncated along with content.

### Position Strategy (Lost in the Middle Applied to RAG)

Optimal layout: `[System prompt] [Fragments #1, #2] [Conversation history] [Fragments #3, #4, #5] [Current user question]`. Most relevant fragments at beginning and end (high attention zones). Piling all fragments in the middle empirically drops RAGAS Faithfulness 15–20%.

### Dynamic Budget Calculation

**Formula (must recalculate before every RAG call)**:
```
available         = context_window - system_prompt_tokens - conversation_tokens - max_generation_tokens
retrieval_budget  = available × 0.80              # 20% safety buffer
max_per_chunk     = min(400, retrieval_budget / num_chunks)
```
Hardcoding to a fixed value causes silent overflow once conversation grows. See P10 below for long-running degradation strategy.

### RAG Context Engineering Checklist

- [ ] Two-stage retrieval (vector → reranker)
- [ ] Dynamic retrieval token budget per turn
- [ ] Fragment metadata includes source / score / date
- [ ] High-score fragments at context head and tail (Lost in the Middle)
- [ ] When truncating, preserve source metadata
- [ ] RAGAS Context Precision > 0.7

## Decision 10: Dynamic Model Routing (Cross-Model Routing)

### From Static Tiers to Dynamic Routing

Hardcoded tier tables ("Haiku cheap / Sonnet balanced / Opus strongest") become outdated within three months. Gemini 3 Flash already outperforms Claude Sonnet on multiple benchmarks at 1/5 the cost.

**Correct routing basis: task type, not difficulty score.** Before finalizing, WebFetch the latest benchmarks — don't rely on training-data memory.

Task type routing:
- Pure text reasoning → cost-performance leader (artificialanalysis.ai)
- Multimodal (image/video/audio) → native support for that input plane
- Very long context (>200K tokens) → openrouter.ai/models for window size
- Real-time / low-latency (<200ms) → Realtime API (OpenAI/Gemini)
- Coding-specialized → aider.chat leaderboards for SWE-bench ranking
- Visual Agent / Computer-use → vendor changelog for current-model support

**Capability freshness check protocol** (from `/agentforge-tools`):

| Check | Real-Time Source |
|--------|---------|
| Cost-performance ranking | https://artificialanalysis.ai |
| Coding agent specialization | https://aider.chat/docs/leaderboards |
| Context window per model | https://openrouter.ai/models |
| Multimodal GA status | Platform changelog (see `/agentforge-tools`) |

**Model ID hardcoding rule**: any specific model ID in skill files must carry a `verified: YYYY-MM-DD` comment. Older than 90 days → re-verify via WebFetch before use. Skills should not become static sources of truth for model selection.

## Decision 11: Prompt Variants (Model Adaptation)

Different model families have different system-prompt preferences (XML vs. Markdown tags, tool-call format, section ordering). Same prompt across all models yields huge performance differences.

**Cline's approach [CL]**: 11 model families × 13 SystemPromptSection components. PromptRegistry matches variant by `model_id`; a variant only overrides differing components (doesn't rewrite entire prompt).

**Preventing maintenance explosion**: cover only truly-differing components + automated regression testing + clean up variants when a model exits.

> Complete implementation (PromptRegistry, matcher patterns, explosion-prevention) → [`references/prompt-variants.md`](references/prompt-variants.md)

## Decision 12: Per-Model Behavioral Guidance (Execution Correction Layer)

Prompt variants (D11) handle **structural** differences. A different problem: the same instruction produces different **behavioral** outputs across model families. GPT/Codex tends to ask for confirmation instead of acting; Gemini skips parallel tool calls; reasoning models need explicit scratchpad boundaries.

**Hermes approach [HR]**: Per-model-family constants committed to source, generated by automated behavioral benchmarks. Example blocks targeting known failure modes:

- **OpenAI family**: `<tool_persistence>` (keep calling tools until done, don't pause), `<mandatory_tool_use>` (do, don't describe), `<act_dont_ask>` (act on reasonable assumptions — counter GPT's "should I proceed?" habit).
- **Google/Gemini family**: use absolute paths, batch independent tool calls in parallel in one response (counter Gemini's sequential-call bias), don't re-read files already read this session.

Injected at the API call layer, **on top of** prompt variants — not as replacements.

### How Behavioral Guidance Gets Generated

Do not author by hand. Each constant is a distillation of automated benchmark results:
1. Define a behavioral benchmark suite (e.g. "task requiring 5 sequential tool calls" × 20 variants × 3 repetitions).
2. Run against each target model family.
3. Identify systematic failure modes.
4. Write minimal instruction that eliminates the failure mode.
5. Verify: re-run benchmark, confirm improvement.
6. Commit constants with `verified: YYYY-MM-DD` comment — re-verify after any model release that changes tool_call behavior.

### Decision Matrix

| Agent Type | Worth Building? | Cost |
|-----------|-----------------|------|
| Single-model, fixed provider | No — hardcode known needs | — |
| Multi-provider from day one | Yes | ~1 day per family for benchmark + constant |
| Agent OS / gateway (serves N backends) | Essential — users bring their own models | First-class routing layer |
| Research agent on best-available model | Yes, but date-stamp everything | Benchmark re-run on each release |

**Integration with D11**: system prompt assembly order — (1) base prompt, (2) PromptVariant sections, (3) per-model behavioral guidance (injected **last** so it can override structural defaults).

## Context Management for Long-Running Scenarios

> **Trigger**: Agent runs continuously 60+ minutes (meeting assistant, monitoring agent, long-duration research), or RAG agent executes multiple retrieval rounds per session.

### P9: Sliding Window Compression (60+ Minute Sessions)

Standard auto-compact assumes "compress after completing a task." Long-running agents have no natural task endpoint.

**Strategy — time-window layered compression**:
- **Hot layer** (last 15 min) — keep full conversation.
- **Warm layer** (15–45 min) — paragraph-level summaries.
- **Cold layer** (45+ min) — only key decisions and action logs.

Trigger cold-layer compression every 10–15 minutes, not on overflow (by then there's no time for graceful compression).

**Implementation principles**:
1. Compress by time, not "completion level" — long-running has no completion point.
2. Preserve "decision anchors" — after compression retain "made decision X, reason Y".
3. Hot layer not compressed — keep recent 15 min verbatim.
4. Checkpoint to persistent storage before each compression (supports session recovery).

### P10: RAG Budget Dynamic Tracking for Long-Running

D9's `compute_retrieval_budget()` is for a single call. Long-running sessions grow `conversation_tokens`, so the RAG budget shrinks round by round. Recalculate each round.

**Correct pattern (principle)**: per event, count current conversation tokens live, recompute `budget, per_chunk` via the D9 formula, degrade gracefully — if budget < threshold, reduce `top_n`, don't error.

**Budget exhaustion degradation**:

| Budget Range | Strategy |
|---------|------|
| > 6,000 tokens | Normal retrieval (top-5, 400 tokens/fragment) |
| 2,000–6,000 | Degraded (top-3, 300 tokens/fragment) |
| 500–2,000 | Minimal (top-1, most relevant only) |
| < 500 | Skip RAG, rely on LLM's knowledge |

## Stateless Agent Context Patterns (P21)

Decisions 1–11 assume the agent has conversation history. **Event-driven Webhook Agents** (Paradigm 6) are stateless — each HTTP request is independent, no session. Most of the 11 decisions don't apply.

**Decision branch**:
- Stateless HTTP requests? → single-request context mode. **Skip**: D3 (compression), D8 (multi-tenant persistent context), long-running management. **Keep**: D1 (layering), D2 (Prompt Cache), D4 (Repo Map).
- Otherwise → normally proceed through all 11 decisions.

**Single-request context construction (principle)**: Build messages per request from scratch — no `conversation_history` parameter. Inject only static system prompt + current event payload (channel, user, message, timestamp) formatted into a single user message. System prompt can still use Prompt Cache (stable across requests). Auto-compact not needed (single-round, terminates immediately). If cross-request "memory" is required, persist to external storage (Redis/DB) and re-fetch per request — never hold history inside LLM context.

**Fundamental difference**:

| Dimension | Conversation Agent | Stateless Webhook Agent |
|--------|---------|-------------------|
| Context construction | Append history, grow dynamically | Rebuild each time, fixed size |
| Compression strategy | Mandatory (prevent explosion) | Not needed |
| RAG budget | Dynamically shrinks with history | Statically allocated |
| Prompt Cache | Dynamic + static partition | Static only (system prompt) |

## Decision 13: Context Reconstruction from Persistent Event Log

> Source: Anthropic Managed Agents architecture — https://www.anthropic.com/engineering/managed-agents (published 2026-04-10, verified 2026-04-11). Validated principle.

All prior Decisions treat context as a **consumable** — it fills up, gets compressed or truncated, and information is irreversibly lost. D13 introduces an alternative: context as a **reconstructed view** from a durable event log.

### The Problem with Irreversible Compression

Traditional compression is one-way: `Full context → Compact/Truncate → Shorter context → information lost forever`.

Anthropic's internal experience: a context-reset harness added for Claude Sonnet 4.5 became "dead weight" when Claude Opus 4.5 no longer needed it — but by then the original events were gone and the harness couldn't reconstruct richer context for the more capable model.

**Core insight**: If you persist raw events before compressing, you can always reconstruct context with a different strategy later. Compression becomes a **policy choice**, not an **irreversible loss**.

### Two-Phase Context Management

1. **Persist (write-ahead)** — every tool call, LLM response, user message → append to event log (JSONL/SQLite) **before** any compression decision.
2. **Reconstruct (read-on-demand)** — when building context for the next turn: read events from the log (positional slicing), apply transformation pipeline (summarize old, keep recent verbatim), inject into context. Transformations can change per model, per task phase, per budget.

### Interface Design (Minimal)

Two pluggable components:
- **`SessionLog`** — append-only durable store. `append(event) → seq`; `get_events(since, until)` by position range. Backed by JSONL/SQLite.
- **`ContextReconstructor`** — stateless, swappable. `build_context(log, budget_tokens)` reads events and produces the next turn's context under a token budget.

**Key constraint**: `SessionLog` outlives any single reconstruction strategy. Compression policies become hot-swappable; raw history is preserved.

### When to Use This vs. Traditional Compression

- Session ≤ 50 turns / < 1 hour → traditional compression (D3) is sufficient.
- Long-lived + needs crash recovery mid-session → event log mandatory.
- Long-lived + serves multiple model tiers → event log enables per-model reconstruction.
- Long-lived otherwise → event log optional.

### Relationship to Other Decisions

- **D3 (Compression)** — becomes one reconstruction strategy among many.
- **D4 (Repo Map)** — static index; event log is dynamic session history — complementary.
- **P4 Memory** — memory = cross-session persistence; event log = within-session persistence. Event log feeds memory (extract key decisions at session end).

### Anti-pattern: Event Log Without Reconstruction Strategy

Persisting events is cheap; building a good `ContextReconstructor` is hard. If you persist events but always dump the full log into context, you've just created an expensive version of "no compression." The value comes from **selective, strategy-driven reconstruction**.

---

## Current Status (April 2026)

1. **1M token context windows mainstream** — Claude and Gemini both support 1M+. "Fitting in" ≠ "using well." Empirically, model performance degrades significantly after 200K tokens; the principle remains "less but better."
2. **Prompt Cache standard, 1h option added** — Anthropic offers default 5 min (write 1.25×, read 0.1×) and 1h (write 2×, read 0.1×). Cache miss can cost 10×; best practice: strict static/dynamic separation + deterministic ordering.
3. **Auto-compact mandatory** — 50+ turn sessions are normal; agents without automatic compression degrade severely. Claude Code's 4-strategy system is widely copied.
4. **Repo Map + Code Search converging** — Pure search (Claude Code) and pre-built index (Aider) are merging. New trend: Repo Map for round-one global view, search tools for precise positioning.
5. **Dynamic context adaptation emerging** — OpenHands' Microagent system matches lightweight knowledge fragments (<500 tokens) by task keywords and injects on demand. Static optimization solves capacity; dynamic adaptation solves relevance. Platform agents must plan for dynamic adaptation; Coding Agents can use Repo Map as a lightweight alternative.

## Known Pitfalls

1. **Cache prefix instability** — Dynamic MCP tool load/unload breaks cache (< 10% hit rate). Fix: MCP tools in the dynamic zone **or** deterministic tool ordering.
2. **Over-compression causes task regression** — Agent loses key context, repeats completed work, overturns prior decisions. Fix: preserve "decision anchors"; tool-call summaries retain input/output signatures, not just conclusions.
3. **system-reminder injection bloat** — Hooks + plugins + MCP status accumulate > 30% of context. Fix: token budget for reminders; prune by priority; low-priority degrades to lazy loading.
4. **Prompt Variants maintenance explosion** — Complete prompt copies per model family scale exponentially. Fix: component-level overrides + automated regression testing.
5. **Progressive disclosure timing misjudgment** — Frequent directory crossing repeatedly loads/unloads `CLAUDE.md`, increasing tokens. Fix: load hysteresis — delayed unload.

## Further Reading

| Topic | Resource |
|------|------|
| Complete Prompt Cache implementation | [`references/prompt-cache-guide.md`](references/prompt-cache-guide.md) |
| Context compression algorithm comparison | [`references/compaction-algorithms.md`](references/compaction-algorithms.md) |
| Hook events (POST_COMPACT / PRE_COMPACT) | `/agentforge-harness` |
| Memory vs compression boundary | `/agentforge-memory` |
| Prompt quality optimization | `/prompt-optimizer` |
| Cross-session memory principles | `/llm-agent-memory` |

## Context Engineering Checklist

- [ ] System prompt layering (at least 2 layers: global + project)
- [ ] Clear static/dynamic separation
- [ ] Prompt Cache supported (static zone has cache_control)
- [ ] Auto-compact (or at least manual compact) implemented
- [ ] Tool definitions support lazy loading (> 20 tools)
- [ ] System-injected info wrapped in tags (prompt-injection defense)
- [ ] Repo Map or equivalent (codebase > 50 files)
- [ ] Important information at head or tail (Lost in the Middle)
- [ ] Visual token costs estimated for image inputs
- [ ] Extended Thinking exempted from compression
- [ ] WebFetch benchmarks before model selection
- [ ] RAG Agent: two-stage retrieval + dynamic per-turn budget
- [ ] RAG Agent: fragment metadata (source/score/date); high-score at head/tail

## Reverse Audit (Diagnose Mode)

> Called by `/agentforge-diagnose` — D3 context dimension static audit on existing code.

| # | Check | How to Check | Pass Standard |
|---|--------|---------|---------|
| C1 | Prompt externalization | `grep -rn "system_prompt\s*=\s*[\"']" src/ \| head -5` | System prompt in separate file, not inline string |
| C2 | Large text truncation | `grep -rn "truncat\|max_token" src/` | Truncation logic for PR diffs/logs/scraped results |
| C3 | Static/dynamic separation | Read messages construction; check static/dynamic split | Static instructions not concatenated with dynamic data each request |
| C4 | Untrusted content isolation | `grep -rn "system_prompt\|messages\[0\]" src/` | External content wrapped in XML tags, placed in user message |
| C5 | Inform LLM when truncating | Read truncation logic; check for "content truncated" note | After truncation, has `[diff truncated at N tokens]` marker |

**High-probability issues**: Large external content fed without truncation (P0 context overflow), Prompt Injection protection missing (P0 security), system prompt hardcoded cannot hot-reload (P2 maintainability).

## Next Step

After context engineering is complete → **`/agentforge-memory`** (Phase 4: Memory system selection)
