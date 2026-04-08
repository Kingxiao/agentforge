# Memory Paradigm Deep Dive: Implementation Comparison

> Engineering details of three schools of thought. Use alongside SKILL.md's decision tree.

## File Memory [CC]

### MEMORY.md Structure

```markdown
# Memory Index

## User Preferences
- [Coding style preferences](user_coding_style.md) — Rust-first, functional style, Result-based error handling

## Projects
- [ProjectX Architecture](project_x_architecture.md) — Microservices, gRPC, PostgreSQL
- [ProjectY Status](project_y_status.md) — MVP stage, 3/7 modules complete

## Feedback
- [Debugging habits](feedback_debugging.md) — User dislikes excessive logging, prefers breakpoint debugging
```

### Constraint Parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| MEMORY.md max lines | 200 lines | [CC] |
| MEMORY.md max bytes | 25,000 bytes | [CC] |
| Max chars per memory file | 40,000 chars | [CC] |
| Memory types | user / feedback / project / reference | [CC] |
| Load timing | Injected into system prompt at session start | [CC] |
| Priority level | Layer 5 (highest priority) | [CC] |

### Auto-Extraction Implementation [CC]

```
Trigger conditions:
  - Every N tool calls (internal counter)
  - User inputs /memory
  - Compact triggered

Extraction flow:
  1. Fork child process (independent context, doesn't block main loop)
  2. Child process receives full conversation history
  3. LLM determines if there's new information worth remembering
  4. If yes → determine type (user/feedback/project/reference)
  5. Check for conflicts with existing memories → update or create new
  6. Write to MEMORY.md index + corresponding .md file
  7. Child process exits
```

### Strengths and Limitations

**Strengths**:
- Zero external dependencies — filesystem only
- Git-trackable — complete history of memory changes
- Human-auditable — open the file and see what the agent remembered
- Cross-agent shareable — any agent that can read Markdown can use it

**Limitations**:
- No semantic search — relies on index file title matching only
- Capacity ceiling — 25KB equals roughly 50-100 structured memories
- Manual maintenance — too many memories requires manual pruning
- No multi-tenancy — single-user design

## Block Memory [LT]

### Block Class Definition

```python
class Block:
    label: str          # e.g., "persona", "human", "project"
    value: str          # actual content
    limit: int          # character limit (default 2000)
    read_only: bool     # whether agent can modify
    
    # System tracks token usage
    # Core Memory Block content always in system prompt
```

### Three-Tier Memory Architecture

**Core Memory (within context window)**:
```
Always in system prompt, visible to agent every turn.
Stores high-frequency critical information:
  - persona block: Agent identity and capability description
  - human block: User profile and preferences
  - Custom blocks: Project status, task context, etc.

Modification methods: Agent uses built-in tools
  core_memory_append(label, content)
  core_memory_replace(label, old_text, new_text)
```

**Archival Memory (long-term storage)**:
```
Not in context window; requires active retrieval by agent.
Supports semantic search (embedding + vector index).
No capacity limit (bounded by backend storage).

Operations:
  archival_memory_insert(content)          → store
  archival_memory_search(query, k=10)      → semantic search top-k
```

**Recall Memory (recent conversation)**:
```
Automatically managed; no explicit operations needed from agent.
Last N turns of conversation, weighted by time decay.
Used for "what was said just now" type of short-term recall.
```

### Heartbeat Mechanism [LT]

Letta's distinctive design: agents can proactively request "call me again."

```
Agent returns:
{
  "tool_calls": [...],
  "request_heartbeat": true   ← tells system "call me again after tool execution"
}

Use cases:
  - Continuous multi-step operations (no user input needed to continue)
  - Background memory organization
  - Autonomous archival memory exploration
```

### Persistence [LT]

```
SQLAlchemy ORM
├── agents table (Agent config + Core Memory snapshot)
├── blocks table (all Block content)
├── passages table (Archival Memory entries + embedding)
├── messages table (conversation history = Recall Memory)
└── tools table (Agent available tool definitions)

Supported backends: SQLite (dev) / PostgreSQL (production)
```

### Strengths and Limitations

**Strengths**:
- Agent self-managed — doesn't depend on external scripts or forked processes
- Multi-tenancy native — each agent instance has independent Block set
- Semantic retrieval — Archival Memory supports vector search
- Extensible — custom Block types and tools

**Limitations**:
- Opaque — users can't easily audit what the agent has remembered
- Core Memory capacity limited — each Block defaults to 2000 characters
- Depends on embedding model — Archival Memory requires vectorization
- Cold start problem — new agents have empty Core Memory

## Hierarchical Semantic Memory [MU]

### Filesystem Metaphor

```
memory_store/
├── preferences/
│   ├── coding_style.json      # {"type": "preference", "content": "..."}
│   ├── communication.json
│   └── tools.json
├── relationships/
│   ├── colleague_alice.json
│   └── manager_bob.json
├── knowledge/
│   ├── rust_patterns.json
│   └── architecture_decisions.json
└── context/
    ├── current_project.json
    └── recent_decisions.json
```

### memorize() Pipeline [MU]

```
Input: raw text
    ↓
Step 1: preprocess
    - Remove noise (duplicates, meaningless content)
    - Normalize format
    ↓
Step 2: type_extract (LLM call)
    - Determine memory type: preference / relationship / knowledge / context
    - Extract structured fields
    ↓
Step 3: categorize (LLM call)
    - Determine which directory it belongs to
    - Check for conflicts with existing memories
    - Conflict → merge strategy (overwrite / append / version)
    ↓
Step 4: store
    - Write to corresponding directory
    - Update index
    - Generate embedding (for subsequent retrieval)
    - Return revision token (for version tracking)
```

### retrieve() Pipeline [MU]

```
Input: query text
    ↓
Step 1: decompose (LLM call)
    - Break complex query into sub-queries
    - Example: "User's recent Rust project architecture decisions"
      → ["user Rust preferences", "recent architecture decisions", "project context"]
    ↓
Step 2: search (parallel execution)
    - For each sub-query, search in all relevant directories
    - Hybrid vector similarity + keyword matching
    ↓
Step 3: rerank (LLM call)
    - Re-rank candidate results by relevance
    - Consider time decay (recent memories weighted higher)
    ↓
Step 4: return
    - Return top-k results
    - Include source directory and confidence score
```

### Pipeline Versioning [MU]

```python
# Every memorize returns a revision token
revision = memory.memorize("User prefers Rust over Go")
# → "rev_20260406_001"

# Can rollback to a specific version
memory.rollback("rev_20260406_001")

# Use cases:
# - A/B testing different memory strategies
# - Rolling back erroneous memory extractions
# - Auditing memory change history
```

### Pluggable Backends [MU]

```
MemoryBackend interface:
  - InMemoryBackend    → testing/development
  - SQLiteBackend      → single-machine production
  - PostgresBackend    → multi-machine scaling

LLM Profile Routing:
  - embedding: lightweight model (e.g., text-embedding-3-small)
  - type_extract: medium model (e.g., claude-haiku)
  - rerank: strong model (e.g., claude-sonnet)
  - Different steps use different models, balancing cost and quality
```

### Strengths and Limitations

**Strengths**:
- Semantic search — not just keyword matching
- Auto-classification — reduces manual maintenance
- Pipeline is pluggable — each step independently replaceable
- Version control — memory changes are traceable and rollback-able

**Limitations**:
- Architecture complexity — one memorize may trigger 2-3 LLM calls
- High cost — embedding + LLM classification + LLM reranking
- Slow cold start — need sufficient memory accumulation before semantic search value shows
- Operational overhead — need to manage embedding models, vector indices, backend storage

## Three-School Summary

| Dimension | File [CC] | Block [LT] | Hierarchical [MU] |
|-----------|-----------|------------|---------------------|
| Complexity | Low | Medium | High |
| External dependencies | None | SQLite/PG | SQLite/PG + Embedding |
| Semantic search | None | Archival tier only | Global |
| Capacity ceiling | ~25KB | Core limited, Archival unlimited | Unlimited |
| Agent self-managed | No (fork extraction) | Yes (built-in tools) | Yes (pipeline auto) |
| Human-auditable | Excellent (Markdown) | Moderate (need DB query) | Poor (scattered + embedding) |
| Multi-tenancy | No | Native | Native |
| Suitable scale | 1 person / 1 Agent | Multi-user / Multi-Agent | Platform-level |
| Implementation cost | 1 day | 1 week | 2-4 weeks |
