---
name: agentforge-context
description: Agent Context Engineering Guide. Layered system prompts + Prompt Cache + Auto-compact + Progressive Disclosure + Repo Map. Triggered when user says "Agent context", "context engineering", "prompt cache", "auto compact".
triggers:
  - Agent 上下文
  - context engineering
  - prompt cache
  - auto compact
  - 上下文压缩
metadata:
  version: "2.0.0"
  last_updated: "2026-04-06"
  category: "agent-engineering"
---

# AgentForge Phase 3: Context Engineering

> Previous: `/agentforge-tools` | Next: `/agentforge-memory` | Series entry: `/agentforge`
> Prompt optimization: `/prompt-optimizer`

## Core Principles

Context engineering is the agent's "cognitive bandwidth management." Context quality directly determines agent quality.

**Five First Principles**:
1. **Context windows are finite** — Even 200K tokens fill up fast in multi-step tasks
2. **Context decays** — Longer inputs degrade model performance (all models)
3. **Caching is a cost lever** — Prompt Cache hits reduce input token costs by 90%
4. **Progressive disclosure beats flooding** — Provide information on-demand, don't dump everything
5. **Compression is mandatory** — Long sessions need mechanical context compression

## Decision 1: Layered System Prompts

### System Prompt Layering Architecture [CC]

```
Instruction loading system (4 layers, priority low to high):
Layer 1: Global system instructions (/etc/claude-code/CLAUDE.md)
Layer 2: User global instructions (~/.claude/CLAUDE.md)
Layer 3: Project instructions (CLAUDE.md, .claude/CLAUDE.md, .claude/rules/*.md)
Layer 4: Local instructions (CLAUDE.local.md) — git-ignored

Injected separately:
MEMORY.md (~/.claude/MEMORY.md) — Truncated to 25KB, managed independently by memdir module
```

> Note: The instruction loading system in source code is 4 layers (claudemd.ts). MEMORY.md is handled separately by memdir.ts but ultimately also injected into the prompt. Functionally equivalent to 5 layers, but implemented as two independent subsystems.

**Constraints**:
- Single file max 40,000 chars [CC]
- MEMORY.md max 200 lines / 25,000 bytes [CC]
- Supports `@include` directive (`@./path`, `@~/path`, `@/path`) [CC]
- Has circular reference detection [CC]

### Directory-Level Progressive Disclosure [CC]

```
project/
├── CLAUDE.md              # Global: build commands, coding style, architecture overview
├── src/
│   ├── CLAUDE.md          # Source-level: import conventions, module patterns
│   └── api/
│       └── CLAUDE.md      # API-level: endpoint patterns, auth handling
└── tests/
    └── CLAUDE.md          # Test-level: test patterns, mock conventions
```

When the agent enters a directory, that directory's CLAUDE.md loads into context automatically. Released when leaving.

### Agent Comparison

| Agent | Instruction File | Layers | Progressive Disclosure |
|-------|---------|--------|--------|
| Claude Code [CC] | CLAUDE.md | 5 layers | Yes (directory-level) |
| Codex CLI [CX] | AGENTS.md | 2 layers | No |
| OpenCode [OC] | .opencode.json contextPaths | 1 layer | No |
| Cline [CL] | Modular prompt variants | 1 layer | No (but switches by model) |
| OpenHands [OH] | .openhands/ + microagents | 2 layers | Yes (task-based) |
| OpenClaw [OW] | Deterministic ordering + cache boundaries | Multi-layer | Yes (deterministic ordering ensures cache stability) |

## Decision 2: Prompt Cache

### Mechanics

API caches consecutive identical prefixes. Cache hits reduce input token costs by 90%.

### Static/Dynamic Separation [CC]

```
System Prompt
├── [STATIC] Identity, guidelines, rules, tool definitions
│   → Add cache_control: {"type": "ephemeral"}          # 5-minute cache (default)
│   → Or cache_control: {"type": "ephemeral", "ttl": "1h"}  # 1-hour cache (2025 addition)
│     For very large knowledge bases/system prompts that rarely change, 1h is recommended
│     (read cost same 0.1x, write cost 2x vs 1.25x)
│
├── SYSTEM_PROMPT_DYNAMIC_BOUNDARY ← boundary
│
└── [DYNAMIC] MCP state, conversation context, Git status
    → Recalculated every turn, not cached
```

**Optimization principles**:
- Minimize dynamic sections — every uncached section is a cost
- MCP tool definitions are typical cache busters (server connect/disconnect changes the tool list)
- Claude Code has `promptCacheBreakDetection` to detect what operations break the cache [CC]

### Prompt Cache Stability Techniques [OW]

OpenClaw ensures cache hit rates via deterministic file ordering + cache boundary markers:
- Files in system prompts are ordered deterministically (not filesystem traversal order), preventing cache prefix invalidation due to different file discovery orders
- Explicit cache boundary markers isolate high-frequency changing parts outside the cache zone

### Practical Benefits

Assuming system prompt of 10,000 tokens:
- No cache: $0.03 per turn ($3/MTok)
- With cache: First turn $0.0375 (creation cost), subsequent turns $0.003 (10% cost)
- **~50-turn session saves ~$1.35**

## Decision 3: Context Compression (Auto-Compact)

### Trigger Conditions

| Agent | Trigger | Compression Method |
|-------|---------|---------|
| Claude Code [CC] | Token usage exceeds threshold | 4 strategies: auto-compact / micro-compact / context-collapse / snip |
| OpenCode [OC] | 95% context window | Separate summarizer agent |
| Aider [AD] | On model switch | Auto-summarize history |
| Letta [LT] | Memory overflow | Sliding window + archival |
| OpenHands [OH] | Near window limit | Dual-mode Condenser: View (keep all) / Condensation (request compression) |

### Claude Code's 4-Strategy Compression System (Most Mature) [CC]

```
4 compression strategies (coarse to fine):

1. auto-compact    — Triggered when token usage exceeds threshold, compresses entire session
2. micro-compact   — Single message level compression, for individual overly long messages
3. context-collapse — Fold tool call results, keep call signatures but compress outputs
4. snip            — Truncate oversized outputs (e.g., large file contents), keep head and tail

Token usage tracking
    ↓
[calculateTokenWarningState]
    ├─ Exceeds threshold?
    │   YES →
    │   ├─ Group messages by API turn (grouping.ts)
    │   ├─ Fork subprocess (avoid blocking main loop)
    │   ├─ Generate summary with LLM
    │   ├─ Tool use generates separate summary (toolUseSummaryGenerator.ts)
    │   ├─ Insert compact boundary marker (createCompactBoundaryMessage)
    │   └─ Trigger POST_COMPACT hook
    │
    └─ NO → Continue
```

### OpenHands Dual-Mode Dynamic Compression [OH]

```
Condenser mechanism:
├─ View mode     — Keep all messages, no compression (short sessions / debugging)
└─ Condensation mode — Request LLM to compress history, switch dynamically
    ├─ Trigger: Context approaches window limit
    ├─ Compression granularity: Full conversation history → structured summary
    └─ Switching strategy: Runtime auto-switch based on token usage
```

### Implementation Essentials

1. **Don't wait for overflow to compress** — Use `/compact` proactively after completing a logical unit
2. **Summarize tool outputs separately** — Long tool outputs (e.g., large file contents) have separate summarization logic
3. **Trigger hook after compression** — Can update cache, refresh file state after compression

## Decision 4: Repo Map (Codebase Index)

### Aider's AST Indexing Approach [AD]

```python
class RepoMap:
    def get_repo_map(self, chat_files, other_files):
        # Parse all source files' AST using tree-sitter
        # Extract: function signatures, class definitions, import relationships
        # Token-budgeted (default ~1024 tokens)
        # Lets agent "know the codebase structure" without reading all files
```

**Advantage**: Agent sees the entire codebase skeleton without reading files one by one
**Cost**: AST parsing has computational overhead, requires tree-sitter dependency

### Claude Code's Alternative Approach [CC]

No pre-built index; instead provides search tools:
- `Glob` — Search by filename pattern
- `Grep` — Search by content
- `ToolSearch` — Lazy-load tool schemas

**Trade-off**: Search is more flexible but needs additional API turns; Repo Map pays upfront computation cost but gives global view from round one.

### Selection Guidance

```
How large is your codebase?
├─ < 50 files → No Repo Map needed, search tools are sufficient
├─ 50-500 files → Repo Map has clear benefits
└─ > 500 files → Repo Map is mandatory + token budget control
```

## Decision 5: Deferred Tools (Lazy Loading)

### Problem

40+ tools' JSON Schema can consume 5,000+ tokens. Most tools aren't used in most conversations.

### Solution [CC]

```
Initial prompt: Only expose tool names + one-line descriptions
    ↓
When agent needs a tool:
    Call ToolSearch(query="file search")
    ↓
    Return full JSON Schema
    ↓
    Tool is available
```

**Effect**: System prompt token usage reduced by 60-70%

## Decision 6: system-reminder Tag System

### Problem

Agent needs to inject system information (Git status, CLAUDE.md content, task notifications) mid-conversation, but must semantically distinguish from user input.

### Solution [CC]

```xml
<system-reminder>
Git status: main branch, 3 uncommitted files
Current CLAUDE.md rules: ...
</system-reminder>
```

System prompt explicitly tells the model: "Content in these tags comes from the system, unrelated to the context of the message they're in."

**Tag name "reminder" vs "instruction"** reduces risk of malicious prompt injection exploitation [CC].

## Decision 7: Information Position Optimization (Lost in the Middle)

### Problem

LLMs have uneven attention distribution across context positions — beginning and end information is most reliably remembered, middle portions are easily "forgotten." This is a proven conclusion from Nelson F. Liu et al.'s 2023 paper *Lost in the Middle*.

### Application Principles

```
Information placement strategy:
├─ Most important (task goal, decision constraints) → System prompt beginning
├─ Second important (historical decisions, key state) → Latest user message each turn
├─ Tool results → Immediately after the triggering tool call (don't batch then send)
└─ Background material (codebase overview, docs) → Avoid placing in the exact middle of message sequence
```

**Prompt Cache impact**: Static instructions at system prompt beginning (high attention + high cache hit rate), dynamic information at the end (high attention + allows changes) — best of both.

### Visual Input Token Cost

Image inputs are token黑洞 (sinks) — must declare in Spec phase:

| Image Size | Approximate Token Cost |
|---------|------------|
| Small (<500px) | ~300-500 tokens |
| Medium (800-1200px) | ~800-1200 tokens |
| Large / Screenshot (Full HD) | ~1500-2000 tokens |
| Computer-use screenshot (per step) | ~1500 tokens × number of steps |

**Computer-use Agent cost estimate**: A 10-step GUI task ≈ 15,000 tokens in image costs alone, far higher than pure text tasks. Screenshots per step cannot be skipped (visual feedback is the driving force of the loop), but reducing resolution saves 30-50%.

### Large Text Content Truncation Strategy (Webhook / Tool-output Agent必读)

Tool-returned text content (PR diffs, web page body, file contents) can also be token sinks. Unlike images with fixed costs, text content size is unpredictable — truncation strategy must be designed in Phase 3:

**Common oversized scenarios**:

| Scenario | Typical Size | Truncation Strategy |
|---------|---------|---------|
| GitHub PR diff (large PR) | 5K-50K tokens | Prioritize keeping changed lines; skip binary/lock/auto-generated files |
| Web page scraped content | 2K-20K tokens | Extract body paragraphs, remove nav/footer/ads HTML |
| Log files | 10K-500K tokens | Keep only ERROR/WARN lines + 10 lines context before/after |
| Full code file | 2K-30K tokens | Return only lines containing keywords + function signatures |

**PR Diff Truncation Implementation (Python)**:

```python
SKIP_PATTERNS = [
    "*.lock", "*.min.js", "*.min.css", "package-lock.json",
    "yarn.lock", "Cargo.lock", "go.sum", "*.pb.go",  # binary/auto-gen
    "*.png", "*.jpg", "*.gif", "*.ico", "*.woff",    # binary assets
]

def truncate_diff(diff: str, max_tokens: int = 20000) -> str:
    """
    Truncate PR diff to fit token budget.
    Strategy: Skip binary/auto-generated files, prioritize files with highest changed-line density.
    """
    files = parse_diff_by_file(diff)
    
    filtered = []
    skipped = []
    for f in files:
        if any(fnmatch(f.filename, pat) for pat in SKIP_PATTERNS):
            skipped.append(f.filename)
            continue
        filtered.append(f)
    
    # Sort by changed lines descending (prioritize most-changed files)
    filtered.sort(key=lambda f: f.changed_lines, reverse=True)
    
    result_parts = []
    remaining = max_tokens
    for f in filtered:
        tokens = estimate_tokens(f.content)
        if tokens > remaining:
            # Truncate to remaining budget: keep only first N lines
            lines = f.content.split("\n")
            kept = []
            for line in lines:
                kept.append(line)
                remaining -= len(line.split()) // 0.75  # Rough estimate
                if remaining <= 0:
                    kept.append(f"\n... [truncated {len(lines)-len(kept)} lines]")
                    break
            result_parts.append("\n".join(kept))
            break
        result_parts.append(f.content)
        remaining -= tokens
    
    if skipped:
        result_parts.append(f"\n[Skipped {len(skipped)} binary/auto-generated files: {', '.join(skipped[:5])}...]")
    
    return "\n".join(result_parts)
```

**Must inform LLM after truncation**: Note `[diff truncated at N tokens, {M} files skipped]` in user message to avoid agent thinking the diff is complete.

### Extended Thinking Compression Exception

Standard auto-compact cannot compress Extended Thinking's reasoning chain:

```
Regular messages: Can be compressed to summary → saves tokens
Extended Thinking output: Reasoning chain MUST NOT be compressed
    Reason: The reasoning chain is the model's internal intermediate step reference chain;
    compression breaks it, causing subsequent turns to fail to correctly reference prior reasoning conclusions.
```

**Implementation implications**: If agent uses Extended Thinking, compression strategy must keep it intact or discard it entirely — no partial summarization. Mark thinking blocks separately when calculating context budget.

## Decision 8: Multi-Tenant / Multi-Project Context Management

**Problem**: When a single agent instance serves multiple users, code repositories, or projects simultaneously, system prompts cannot be static — each request needs different coding standards, different project architecture descriptions, different security policies.

This is the core architectural difference between **Platform Agents** (multi-channel gateways, SaaS) and **single-user CLI Agents**.

### Context Isolation Layers

```
Static layer (shared across all tenants, strong cache)
├── Agent core capability description
├── Tool definitions
└── Global security policies

Dynamic layer (built per request, not cached)
├── Tenant context (coding standards, architecture description)
│   └── Each repo/project has independent CLAUDE.md
├── User session state (memory, preferences)
└── Current task context (working directory, git status)
```

**Prompt Cache key principle**: Static layer at system prompt beginning with `cache_control: {"type": "ephemeral"}`, dynamic layer after boundary. Larger dynamic layer = lower cache hit rate — this is the core cost trade-off in multi-tenant architectures. 2025 added `"ttl": "1h"` option — for very large system prompts (>10K tokens) recommend 1h cache to reduce write frequency (verified: 2026-04-08).

### Multi-Repo System Prompt Routing

```python
class MultiTenantContextBuilder:
    def __init__(self):
        self.static_prefix = load_global_system_prompt()  # Static layer, strong cache
    
    def build(self, tenant_id: str, repo_path: str) -> list[Message]:
        # Each tenant has independent context configuration
        tenant_config = self.load_tenant_config(tenant_id)  # Coding standards, architecture description
        repo_context = self.load_repo_context(repo_path)    # Corresponding repo's CLAUDE.md
        
        return [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": self.static_prefix,
                        "cache_control": {"type": "ephemeral"}  # Static layer cached
                    },
                    {
                        "type": "text",
                        "text": f"## Current Project\n{tenant_config}\n\n{repo_context}"
                        # Dynamic layer not cached
                    }
                ]
            }
        ]
```

### Preventing Context Leakage

The most dangerous problem in multi-tenant scenarios: User A's context leaking into User B's responses.

**Anti-leakage principles**:
1. **Build context independently per request** — Don't reuse the previous request's messages array
2. **Explicit session ID isolation** — Context components use `session_id + tenant_id` as namespace key
3. **LLM output doesn't mix storage** — Different tenants' conversation histories stored physically isolated
4. **Explicit declaration in system prompt** — Inject `<context scope="tenant:{id}">` tag so model knows context boundaries

### Dynamic Context Content Sources

| Content Type | Source | Cache Strategy |
|---------|------|---------|
| Global rules/capabilities | Static config file | Strong cache (cache_control) |
| Project/repo standards | Repo CLAUDE.md | Per-project cache (content hash) |
| User preferences | User memory system | Per-user cache |
| Current git status | Real-time fetch | Not cached |
| Task context | Current request | Not cached |

**Selection routing**: Multi-tenant + complex context routing →优先选 PubSub Event Loop (OpenCode style) or Plugin Gateway (OpenClaw style) — these two paradigms have more built-in support for multi-tenant isolation. → See `/agentforge-architecture` for architectural paradigms

## Decision 9: RAG Retrieval Result Token Budget Management

**Problem**: When RAG agents inject retrieved document fragments into context, three core questions lack quantitative standards: How many fragments to inject? How many tokens per fragment? How to truncate when exceeding budget? This is the most critical context engineering decision for RAG agents — misconfiguration directly causes precision degradation or cost explosion.

### Token Budget Allocation Framework

```
Typical 32K token context window allocation (by ratio, not fixed value):
├── System prompt + tool definitions    ~3,000 tokens  (9%)
├── Conversation history (compressed)   ~5,000 tokens  (16%)
├── Retrieved results                  ~12,000 tokens (37%)  ← Focus of this decision
└── Current question + generation space ~12,000 tokens (38%)
```

**Key parameters (start with defaults, adjust based on RAGAS evaluation)**:

| Parameter | Recommended Default | Description |
|------|-----------|------|
| Initial retrieval top-K | 20 | Better more than fewer; rerank filters later |
| Injected top-N (after rerank) | 5 | Precision/recall balance point |
| Token limit per fragment | 400 tokens | Truncate excess from tail |
| Total retrieval token budget | Available space × 80% | Dynamic calculation, not hardcoded |

### Two-Stage Retrieval (Retrieve → Rerank)

```
Stage 1: Vector retrieval
    Query vector → FAISS / Qdrant / pgvector
    Returns top-K=20 (by cosine similarity)

Stage 2: Rerank (key to precision improvement)
    top-20 fragments → Cross-Encoder Reranker (e.g., Cohere Rerank / BGE-Reranker)
    Returns top-N=5 (by exact relevance ranking)

Why two stages exist:
    Vector retrieval: Fast (milliseconds), but similarity ≠ relevance (semantic space distortion)
    Reranker: Slower (independent computation per pair), but more precise relevance
    Cost: Reranker is usually 10-100x cheaper than LLM — high cost-performance precision improvement
```

### Fragment Injection Format (With Required Metadata)

```xml
<retrieved_documents>
<doc id="1" source="Confluence/Architecture/ADR-042" score="0.87" date="2025-12">
  [Document content, max 400 tokens, truncate tail if exceeded, preserve source without truncation]
</doc>
<doc id="2" source="Internal Wiki/Deployment Guide" score="0.81" date="2026-01">
  [Document content]
</doc>
</retrieved_documents>
```

**Metadata must include**:
- `source`: Source path (user traceability + security audit + Faithfulness scoring basis)
- `score`: Relevance score (lets model perceive credibility; low-score fragments can be marked "limited reference value")
- `date`: Document date (model can judge timeliness; deprioritize stale documents)

### Position Strategy (Lost in the Middle Applied to RAG)

```
Final context layout (optimal):
  [System prompt]
  [Retrieved fragment #1, #2]     ← Beginning (high attention zone, most relevant first)
  [Conversation history]
  [Retrieved fragment #3, #4, #5] ← End (high attention zone, second-most relevant)
  [Current user question]

Common wrong layout (avoid):
  [System prompt]
  [Conversation history]
  [All retrieved fragments #1-#5]  ← All piled in middle →实测 Faithfulness drops 15-20%
  [Current user question]
```

### Dynamic Budget Calculation

```python
def compute_retrieval_budget(
    context_window: int,
    system_prompt_tokens: int,
    conversation_tokens: int,
    max_generation_tokens: int = 2048,
    num_chunks: int = 5,
) -> tuple[int, int]:
    """
    Returns: (total_retrieval_budget, max_tokens_per_chunk)
    Dynamically calculated before each RAG call to avoid hardcoded overflow.
    """
    available = (
        context_window
        - system_prompt_tokens
        - conversation_tokens
        - max_generation_tokens
    )
    retrieval_budget = int(available * 0.80)  # Keep 20% safety buffer
    max_per_chunk = min(400, retrieval_budget // num_chunks)
    return retrieval_budget, max_per_chunk
```

### RAG Context Engineering Checklist

- [ ] Implemented two-stage retrieval (vector retrieval → Reranker, not single-stage vector similarity)
- [ ] Dynamic retrieval token budget calculated each turn (not hardcoded fixed value)
- [ ] Fragment metadata includes source / score / date
- [ ] High-score fragments placed at context beginning and end (Lost in the Middle optimization)
- [ ] When truncating, preserve source metadata (can't truncate source along with content)
- [ ] RAGAS Context Precision > 0.7 (ratio of truly useful among 5 injected fragments)

## Decision 10: Dynamic Model Routing (Cross-Model Routing)

### From Static Tiers to Dynamic Routing

Hardcoded model tier tables ("Haiku cheap / Sonnet balanced / Opus strongest") become outdated within three months — Gemini 3 Flash already outperforms Claude Sonnet on multiple benchmarks at 1/5 the cost.

**Correct routing basis: task type, not difficulty score.**

```
Task type routing (before selecting model for each type, WebFetch latest benchmarks first):
├─ Pure text reasoning → Cost-performance priority: WebFetch artificialanalysis.ai comparison
├─ Multimodal (image/video/audio) → Primary model must natively support that input plane
├─ Very long context (>200K tokens) → WebFetch openrouter.ai/models for window size
├─ Real-time/low-latency (<200ms) → Realtime API (only OpenAI/Gemini supported)
├─ Coding-specialized → WebFetch aider.chat/docs/leaderboards for SWE-bench latest rankings
└─ Visual Agent / Computer-use → Need WebFetch vendor changelog to confirm current model supports this capability (capabilities iterate fast, not suitable for hardcoding)
```

**Capability freshness check protocol** (from `/agentforge-tools`):
Before finalizing model selection, must WebFetch the following real-time data (don't use static记忆 from training data):

| Check | Real-Time Source |
|--------|---------|
| Comprehensive cost-performance ranking | https://artificialanalysis.ai |
| Coding agent specialization | https://aider.chat/docs/leaderboards |
| Each model's context window | https://openrouter.ai/models |
| Multimodal capability GA status | Corresponding platform changelog (see `/agentforge-tools` capability freshness check table) |

**Model ID hardcoding rule**: When specific model IDs appear in skill files, must attach `verified: YYYY-MM-DD` comment. Older than 90 days without verification is considered stale — must WebFetch to confirm before use. Skills themselves should not become the static source of truth for model selection — only provide selection dimensions and WebFetch targets.

## Decision 11: Prompt Variants (Model Adaptation)

Different model families have different preferences for understanding system prompts (XML vs Markdown tags, explicit tool call formats, etc.). Feeding the same system prompt to all models yields huge performance differences.

**Cline's approach [CL]**: 11 model families × 13 SystemPromptSection components, PromptRegistry matches variant by model_id, variant only covers differing components (doesn't rewrite entire prompt).

**Preventing maintenance explosion**: Only cover components that truly differ + automated regression testing + clean up variants when model exits.

> Complete implementation (PromptRegistry code, matcher patterns, explosion-prevention strategy) → [`references/prompt-variants.md`](references/prompt-variants.md)

## Context Management for Long-Running Scenarios

> **Trigger**: Agent runs continuously 60+ minutes (meeting assistant, monitoring agent, long-duration research task), or RAG agent executes multiple retrieval rounds within the same session.

### P9: Sliding Window Compression (60+ Minute Sessions)

Standard auto-compact works under the assumption of "compress after completing a task." Long-running agents have no natural task endpoint — no compression means context explodes linearly; over-aggressive compression loses ongoing context.

**Strategy: Time-window-based layered compression**

```
Context layers (long-running):
├── Hot layer (last 15 minutes) — Keep full conversation
├── Warm layer (15-45 minutes)  — Keep paragraph-level summaries
└── Cold layer (45+ minutes) — Only keep key decisions and action logs

Trigger timing:
  Execute cold layer compression every N minutes (recommended 10-15 minutes)
  Rather than waiting for token overflow (by the time overflow happens, there's no time for graceful compression)
```

**Key implementation principles**:
1. **Compress by time, not by "completion level"** — Long-running has no completion point
2. **Preserve "decision anchors"** — After compression, still retain entries like "Already made decision X, reason was Y"
3. **Hot layer not compressed** — Keep recent 15 minutes in original text to prevent current task context from being corrupted
4. **Checkpoint writes to persistent storage** — Before each compression, write full state to external storage to support session recovery

### P10: RAG Budget Dynamic Tracking for Long-Running Scenarios

The `compute_retrieval_budget()` in Decision 9 is for **single call** calculation. In long-running scenarios, `conversation_tokens` grows with the session, and RAG budget **shrinks round by round** — if not recalculated, the 30th retrieval might silently truncate because it already exceeded budget.

**Error pattern**:

```python
# ❌ Wrong: Fixed budget after first calculation
budget, per_chunk = compute_retrieval_budget(...)  # Calculated once only
for event in stream:
    docs = rag.retrieve(event, token_budget=budget)  # Budget doesn't update, gradually overflows
```

**Correct pattern**: Recalculate each round

```python
# ✓ Correct: Dynamic calculation of current available budget each round
for event in stream:
    current_conv_tokens = count_tokens(context.messages)
    budget, per_chunk = compute_retrieval_budget(
        context_window=200_000,
        system_prompt_tokens=SYSTEM_TOKENS,
        conversation_tokens=current_conv_tokens,  # Real-time input, not cached
        max_generation_tokens=2048,
    )
    # Degrade when budget insufficient: reduce top-N, don't error
    top_n = max(2, budget // per_chunk) if budget > 1000 else 0
    docs = rag.retrieve(event, top_n=top_n, max_tokens_per_chunk=per_chunk)
```

**Budget exhaustion degradation strategy**:

| Budget Range | Strategy |
|---------|------|
| > 6,000 tokens | Normal retrieval (top-5, 400 tokens/fragment) |
| 2,000-6,000 tokens | Degraded retrieval (top-3, 300 tokens/fragment) |
| 500-2,000 tokens | Minimal retrieval (top-1, most relevant only) |
| < 500 tokens | Skip RAG, rely on LLM's existing knowledge |

## Stateless Agent Context Patterns (P21)

Decisions 1-11 all assume the agent has **conversation history** — multi-turn interaction, memory compression, RAG budget management. But Event-driven Webhook Agents (Paradigm 6) are stateless: each HTTP request is independent, no history, no session. In this scenario, most of the 11 decisions don't apply.

**Decision branch:**

```
Is your agent working in stateless HTTP requests?
  Yes → Use "single-request context mode" (see below)
       Skip: Decision 3 (compression) / Decision 8 (multi-tenant persistent context) / Long-running scenario management
       Keep: Decision 1 (system prompt layering) / Decision 2 (Prompt Cache) / Decision 4 (Repo Map)
  No → Normally proceed through all 11 decisions
```

**Single-request context construction mode:**

```python
def build_request_context(event: dict) -> list[dict]:
    """Context construction for stateless Webhook Agent — independent per request, no history accumulation"""

    system = """You are a GitHub issue triage agent.
    Classify the message and create issues when appropriate.
    Respond with JSON: {"action": "create_issue|reply|ignore", "category": "...", "summary": "..."}
    """

    # No history: only inject static context relevant to current request
    user_message = f"""
    Platform: Slack
    Channel: #{event.get('channel_name', 'unknown')}
    User: {event.get('user', 'unknown')}
    Message: {event.get('text', '')}
    Timestamp: {event.get('ts', '')}
    """

    return [{"role": "user", "content": user_message}]

# Key constraints:
# - Don't pass historical message list (no conversation_history parameter)
# - System prompt can use Prompt Cache (static part is stable)
# - No Auto-compact needed (single round ends immediately)
# - If "remembering" across requests needed → use external storage (Redis/DB), not in LLM context
```

**Fundamental difference from continuous conversation mode:**

| Dimension | Conversation Agent | Stateless Webhook Agent |
|--------|---------|-------------------|
| Context construction | Append history, grow dynamically | Rebuild each time, fixed size |
| Compression strategy | Must have (prevent explosion) | Not needed |
| RAG budget | Dynamically shrinks with history | Statically allocated |
| Prompt Cache | Dynamic + static partition | Static only (system prompt) |

---

## Current Status (April 2026)

1. **1M token context windows becoming mainstream** — Claude and Gemini both support 1M+ token contexts, but "fitting in" doesn't equal "using well."实测 shows significant model performance degradation after 200K tokens; core context engineering is still "less but better" not "more is better."
2. **Prompt Cache is now standard, 1-hour cache option added** — Anthropic provides two TTLs: default 5 minutes (write 1.25x, read 0.1x) and 1 hour (write 2x, read 0.1x, `"ttl": "1h"`, verified: 2026-04-08). Large system prompts that rarely change should use 1h option to reduce write frequency; session-level context uses default 5 minutes. Cache miss can cause 10x cost increase; industry best practice is strict static/dynamic separation + deterministic ordering.
3. **Auto-compact has gone from luxury to necessity** — As agent task complexity increases (50+ turn conversations becoming normal), agents without automatic compression mechanisms degrade severely in long sessions. Claude Code's 4-strategy compression system is widely copied.
4. **Repo Map + Code Search dual-track parallel** — Pure search mode (Claude Code style) and pre-built index mode (Aider style) are converging. New trend: Use Repo Map for global view in first round, then search tools for precise positioning — complementary, not mutually exclusive.
5. **Dynamic context adaptation is emerging** — The first four trends are all **static optimizations** (at design time, decide "what content goes where"). The next frontier is **dynamic adaptation**: at runtime, choose what content to inject based on task state. OpenHands' Microagent system is a typical implementation — match lightweight specialized knowledge fragments (< 500 tokens) by task keywords (repo name, error type, tech stack) and inject on-demand, avoiding full-load context decay. Core difference: static optimization solves "context capacity" problem; dynamic adaptation solves "context relevance" problem. Platform-type agents (multi-channel, multi-task) must plan for dynamic adaptation mechanisms; Coding Agents can use Repo Map as a lightweight alternative.

## Known Pitfalls

1. **Cache prefix instability** — Dynamic loading/unloading of MCP tools causes system prompts to change frequently, Prompt Cache hit rate plummets to < 10%. Solution: Put MCP tool definitions in the dynamic zone (after cache boundary), or implement deterministic ordering of tool lists to stabilize cache prefix.
2. **Over-compression causes task regression** — Auto-compact too aggressively compresses history; agent loses key context, repeats completed work or overturns prior decisions. Solution: Preserve "decision anchors" during compression (key decisions and their reasons); tool call summaries preserve input/output signatures, not just conclusions.
3. **system-reminder injection bloat** — As hooks, plugins, MCP status and other system information accumulates, system-reminder proportion of context grows out of control (> 30%). Solution: Implement token budget for system-reminders; when exceeded, prune by priority, lower-priority information degrades to lazy loading.
4. **Prompt Variants maintenance explosion** — Maintaining independent prompt variants for each model family; maintenance cost grows exponentially as model count increases. Solution: Use component-level overrides (only override differing parts) + automated regression testing, rather than maintaining complete prompt copies for each model.
5. **Progressive disclosure timing misjudgment** — Directory-level CLAUDE.md repeatedly loads/unloads when agent frequently crosses directories, increasing token consumption rather than reducing it. Solution: Implement load hysteresis (delayed unload) — don't immediately unload instructions when agent briefly leaves a directory.

## Further Reading

| Topic | Resource |
|------|------|
| Complete Prompt Cache implementation guide | [`references/prompt-cache-guide.md`](references/prompt-cache-guide.md) |
| Context compression algorithm comparison | [`references/compaction-algorithms.md`](references/compaction-algorithms.md) |
| Hook events (POST_COMPACT / PRE_COMPACT) | `/agentforge-harness` |
| Memory vs compression boundary decision | `/agentforge-memory` |
| Prompt quality optimization | `/prompt-optimizer` |
| Cross-session memory persistence principles | `/llm-agent-memory` |

## Context Engineering Checklist

- [ ] Implemented system prompt layering (at least 2 layers: global + project)
- [ ] Clear separation between static/dynamic prompts
- [ ] Prompt Cache supported (static zone has cache_control)
- [ ] Implemented auto-compact mechanism (or at least manual compact)
- [ ] Tool definitions support lazy loading (when tool count > 20)
- [ ] System-injected information wrapped in tags to prevent prompt injection
- [ ] Has Repo Map or equivalent codebase overview mechanism (when codebase > 50 files)
- [ ] Important information placed at beginning or end (Lost in the Middle optimization)
- [ ] Estimated visual token costs when containing image inputs (~1500 tokens/screenshot)
- [ ] Extended Thinking compression strategy exempts reasoning chain
- [ ] WebFetch latest benchmarks before model selection (don't rely on static tier tables)
- [ ] RAG Agent: Implemented two-stage retrieval (vector retrieval → Reranker), dynamically calculated per-turn token budget
- [ ] RAG Agent: Retrieved fragments include source/score/date metadata, high-score fragments placed at context head and tail

## Reverse Audit (Diagnose Mode)

> Called by `/agentforge-diagnose` — D3 context dimension static audit on existing code.

| # | Check | How to Check | Pass Standard |
|---|--------|---------|---------|
| C1 | Prompt externalization | `grep -rn "system_prompt\s*=\s*[\"']" src/ \| head -5` | System prompt in separate file, not inline string |
| C2 | Large text truncation strategy | `grep -rn "truncat\|max_token\|[:截断]" src/` | Truncation logic exists for PR diffs/logs/scraped results |
| C3 | Static/dynamic separation | Read messages construction code, check if static instructions and dynamic data are separated | Static system instructions not concatenated with dynamic data each request |
| C4 | Untrusted content isolation | `grep -rn "system_prompt\|messages\[0\]" src/` check external content injection points | External content wrapped in XML tags, placed in user message |
| C5 | Inform LLM when truncating | Read truncation logic, check if prompt includes "content truncated" note | After truncation, has `[diff truncated at N tokens]` type prompt |

**High-probability issues**: Large external content (PR diff/logs) no truncation, fed directly (P0 context overflow), Prompt Injection protection missing (P0 security), system prompt hardcoded cannot hot-reload (P2 maintainability)

## Next Step

After context engineering is complete → **`/agentforge-memory`** (Phase 4: Memory system selection)
