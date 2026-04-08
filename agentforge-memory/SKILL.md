---
name: agentforge-memory
description: AgentForge Phase 4 — Memory system selection. Three-school decision tree (File Memory / Block Memory / Hierarchical Semantic Memory) + progress file design + session persistence. Triggered when the user says "Agent memory", "cross-session persistence", or "agent state persistence".
triggers:
  - Agent memory
  - cross-session persistence
  - agent state persistence
metadata:
  version: "2.0.0"
  last_updated: "2026-04-06"
  category: "agent-engineering"
---

# AgentForge Phase 4: Memory System Selection

> Previous: `/agentforge-context` | Next: `/agentforge-security` | Series entry: `/agentforge`
> Deep theory: `/llm-agent-memory`, `/agent-episodic-memory`, `/agent-semantic-memory`

## Core Insight

The memory system is the key to transforming an agent from a "one-off tool" into a "long-term partner."

**Three first principles**:
1. **Memory ≠ Storage** — Storage is an IO problem; memory is a cognitive problem of "what to remember, what to forget, when to recall"
2. **Structure determines retrieval quality** — Flat KV can't store relationships; Markdown can't do semantic search; choosing the wrong structure later is extremely costly to migrate
3. **Memory is a product characteristic** — The memory paradigm directly shapes user experience. File memory = transparent and controllable; Block memory = automatic and seamless; Semantic memory = intelligent but unexplainable

## 3-School Decision Tree

```
What level of memory does your agent need?
│
├─ Single-user CLI agent, memory is an auxiliary feature
│  Does it need to be user-editable and auditable?
│  ├─ Yes → File Memory (MEMORY.md school)
│  │        Representative: Claude Code [CC]
│  │        Strengths: git-trackable, human-readable, zero dependencies
│  │        Tradeoffs: no semantic search, manual maintenance, ~25KB scale limit
│  └─ No → Block Memory (structured block school)
│           Representative: Letta [LT]
│           Strengths: agent can read/write autonomously, multi-tenant support, queryable
│           Tradeoffs: needs persistence backend, opaque
│
├─ Multi-user SaaS / multi-agent system
│  Is memory a core product feature?
│  ├─ Yes → Hierarchical Semantic Memory (hierarchical semantic school)
│  │        Representative: MemU [MU]
│  │        Strengths: semantic search, auto-classification, pluggable pipeline
│  │        Tradeoffs: complex architecture, needs embedding models, high operational cost
│  └─ No → Block Memory + SQLite
│           Sufficient for multi-tenancy, without semantic search overhead
│
└─ Research/experimentation scenarios
   → Use `/llm-agent-memory` directly (Mem0/MemOS/NS-Mem selection)
```

## School One: File Memory [CC]

Claude Code's MEMORY.md is the simplest production-grade memory system.

### Architecture

```
~/.claude/MEMORY.md          # Index file (≤200 lines / 25KB)
├── project_foo.md            # Project-level memory
├── feedback_bar.md           # User feedback memory
├── user_preferences.md        # User preferences
└── reference_xyz.md          # Reference knowledge
```

### Auto-Extraction Mechanism

```
Main Agent Loop
    ↓ Every N tool calls (or user explicitly /memory)
    fork child process
    ├─ Read current conversation history
    ├─ Use LLM to determine if there's information worth remembering
    ├─ Yes → write/update MEMORY.md
    └─ No → skip
    Main loop not blocked
```

### KAIROS Mode [CC]

Claude Code's KAIROS is an append-only journal-style memory mode, suited for scenarios requiring a complete timeline rather than a structured index.

**Core mechanism**:
- **Append-only log** — All memory entries appended in chronological order; existing entries never modified (journal format)
- **Entry format** — Each memory entry carries timestamp, source, and content, forming a complete cognitive log
- **Nightly /dream processing** — Periodically (e.g., every night) execute `/dream` command, where LLM processes accumulated logs to:
  - Merge duplicate/conflicting entries
  - Extract cross-entry patterns and insights
  - Compress low-value entries
  - Generate high-level summaries
- **Design philosophy** — Zero cognitive load at write time (append only); organization deferred to batch processing phase

**Difference from standard MEMORY.md**:
- Standard mode: structured index, real-time updates, suited for actionable knowledge
- KAIROS mode: timeline log, delayed organization, suited for experience accumulation and reflection

### Applicability

- Single-user CLI agent
- Memory volume < 25KB (~50 structured memories)
- Needs git tracking of memory changes
- No semantic search required
- KAIROS mode additionally suited for: scenarios needing complete decision history, value reflection and pattern discovery

> Deep implementation details → `references/memory-paradigms-comparison.md`

## School Two: Block Memory [LT]

Letta's design gives agents the ability to "self-edit their memory."

### Core Concepts

```
Core Memory (within context window, always visible)
├── persona: "I am a coding assistant, Rust-preferred..."  [read_only=false]
└── human: "User is a backend engineer, prefers concise..."     [read_only=false]

Archival Memory (long-term storage, requires active retrieval)
└── Semantic index, supports archival_memory_search(query, k)

Recall Memory (recent conversation, automatic weighting)
└── Last N turns, weighted by time decay
```

### 6 CRUD Operations (Complete Tool Set)

The agent's tool list includes complete memory CRUD operations, arranged by evolution complexity:

**Basic operations (v1)**:
- `core_memory_append(key, value)` — Append content to block end (auto newline)
- `core_memory_replace(key, old, new)` — Precise text replacement within block (old must exist or error)

**Strict operations (v2)**:
- `memory_replace(key, old, new)` — v2 strict replacement, additionally detects line number prefix pollution and duplicate content, prevents agent from writing rendered formatting back into memory
- `memory_insert(key, value, line_number)` — Insert content by line number (line_number=-1 means append to end), supports precise position control

**Batch operations**:
- `memory_rethink(key, new_content)` — Completely rewrite entire block content, suited for scenarios needing major reorganization
- `memory_apply_patch(patch)` — Unified diff format, modify multiple blocks in one operation, patch format similar to unified diff

**Archival operations**:
- `archival_memory_insert(content)` — Archive to long-term storage
- `archival_memory_search(query, k)` — Semantic retrieval

### Safety Mechanisms

- **Deep Copy isolation** — All tools operate on a deepcopy of Core Memory; changes are only written back after verification, preventing partial writes from corrupting state
- **Read-Only protection** — Verify all blocks marked `read_only=true` are unmodified before persistence; blocked even if agent attempts modification

### 3 Rendering Modes

When Core Memory is injected into the context window, different rendering formats are supported:
1. **Standard XML mode** — `<block name="persona">content</block>`, most concise
2. **Line number mode** — Each line prefixed with line number, paired with `memory_insert` line-number operations
3. **Git memory mode** — Similar to git diff rendering, shows change history, suited for audit scenarios

### Applicability

- Needs agent autonomous memory management (no external scripts)
- Multi-tenant scenarios (each user/session has independent Core Memory)
- Long-term storage with occasional retrieval
- Needs precise control over memory modification granularity (line-level insertion/diff patch) — choose v2 operations

## School Three: Hierarchical Semantic Memory [MU]

MemU's filesystem metaphor + pipeline architecture, suited for memory as a core product feature.

### 3-Tier Storage Hierarchy

```
L1 Category (classification tier)
├── name: "preferences"
├── description: "User's personal preferences and habits"
├── summary: "User prefers concise code style, uses Rust..." (LLM-generated summary)
└── embedding: [0.12, -0.34, ...] (vector representation of summary)

L2 Item (entry tier, 6 types)
├── profile  — User profile (identity, role, background)
├── event    — Event memory (what happened, when, where)
├── knowledge — Domain knowledge (technical concepts, business rules)
├── behavior — Behavioral patterns (habits, preferences, workflows)
├── skill    — Capability memory (skills user has mastered, proficiency)
└── tool     — Tool memory (commonly used tools, configurations, usage)

L3 Resource (resource tier)
├── url: "https://..."
├── modality: "text" | "image" | "audio" | "video"
├── local_path: "/path/to/cached/file"
├── caption: "Text description of resource"
└── embedding: [0.08, -0.21, ...]
```

### Dual Pipeline

```
memorize(text)                    retrieve(query)
    ↓                                 ↓
preprocess                       decompose (query decomposition)
    ↓                                 ↓
type_extract (memory type identification)   search (parallel multi-storage search)
    ↓                                 ↓
categorize (auto-classification)             rerank (re-ranking)
    ↓                                 ↓
store (persistence)                return (return top-k)
```

### 7-Step RAG Retrieval (with Adequacy Checks)

The retrieval pipeline actually executes 7 steps; the core innovation is LLM adequacy judgment at each level:

```
1. Query decomposition → split user query into sub-queries
2. L1 Category retrieval → find relevant categories
3. ★ Adequacy check 1 → LLM judges whether Category-level summary is sufficient to answer
   ├─ Sufficient → return directly (save tokens)
   └─ Not sufficient → continue deeper + rewrite query (more precise)
4. L2 Item retrieval → search for entries under relevant categories
5. ★ Adequacy check 2 → LLM judges whether Item-level information is sufficient
   ├─ Sufficient → return
   └─ Not sufficient → continue + rewrite query again
6. L3 Resource retrieval → get associated resources
7. ★ Adequacy check 3 → final judgment, merge results from all tiers and return
```

**Design point**: Each time an adequacy check fails, LLM rewrites the query based on already-obtained information (query rewriting), making the next-tier retrieval more precise. This avoids the waste of traditional RAG "query all the way through" approach.

### Applicability

- Memory is a core product feature (e.g., personalized assistant, long-term companion agent)
- Needs semantic search and auto-classification
- Has embedding model budget
- Team capable of maintaining pipeline
- Multi-modal memory needed (text + image + audio/video) — choose L3 Resource tier

### Multi-Modal Memory Notes

L3 Resource tier natively supports `image / audio / video`, but storage and recall strategies differ fundamentally from text:

| Modality | Recommended Storage | Embedding Solution | Recall Injection Cost |
|----------|--------------------|--------------------|---------------------|
| Image | Local path + caption | CLIP or multimodal embedding | High (~1500 token/image direct injection) |
| Audio | Local path + **transcript text** | Text embedding (on transcript) | Low (only text injected) |
| Video | Key frames + transcript text | Frame embedding + text embedding | High (grows linearly with frame count) |
| Document | Chunked text + URL | Text embedding | Medium |

**Core constraints**:
1. **Images: prefer caption recall, inject original on demand** — Use image description text as retrieval index; only inject base64/URL when task truly needs to "see" the image (saves ~1500 tokens/image)
2. **Audio: transcript text is first-class citizen** — LLM doesn't directly process raw audio; all audio memories are transcribed before embedding; original files archived only
3. **Image/text embedding dimensions differ** — CLIP and Ada/Cohere embeddings have different dimensions; store separately or use bridge embedding (e.g., ColPali); cannot mix in the same vector index

> Real-time multimodal capability comparison → https://artificialanalysis.ai

> Complete three-school implementation comparison → `references/memory-paradigms-comparison.md`

## Episodic Memory Granularity Decision

> **Background**: Real-time recording agents (meeting assistant, monitoring agent, customer service session recorder) face a fundamental problem — store complete originals or generate summaries? Making the wrong choice at this decision point becomes extremely expensive later (rewriting the entire memory system).

### Granularity Decision Tree

```
Does your agent need to retrieve specific details afterward?
│
├─ Yes (needs precise citation: specific wording, numbers, names)
│  Storage granularity: sentence-level / paragraph-level complete text
│  └─ Tradeoff: large storage (~10K token/hour meeting), high token cost on recall
│
├─ No (only needs context understanding: decisions, viewpoints, gist)
│  Storage granularity: paragraph summary (300-500 token/5 minutes)
│  └─ Tradeoff: irreversible detail loss; cannot answer "what was specifically said"
│
└─ Need both
   → Dual-track storage: real-time complete record (hot tier), periodic summary (cold tier)
   → Dual-track tradeoff: 2× storage, 2× pipeline complexity
```

### Three Granularity Modes

| Mode | Unit | Storage Size | Use Case |
|------|------|-------------|---------|
| **Sentence-level storage** | 1 record per sentence | ~100KB/hour | Legal/medical needing precise citation |
| **Paragraph summary** | 1 summary per 3-5 minutes | ~5KB/hour | General business meetings, focus on decisions not wording |
| **Dual-track (original + summary)** | Original + 1 summary per segment | ~80KB/hour | High-value scenarios (important client meetings, technical reviews) |

### Implementation Points

**Paragraph summary (recommended default)**:

```python
class EpisodicMemoryWriter:
    SEGMENT_TOKENS = 500  # How many tokens accumulate before triggering summary
    
    def __init__(self, storage: MemoryStorage):
        self.buffer: list[str] = []
        self.buffer_tokens = 0
        self.storage = storage
    
    def ingest(self, utterance: str) -> None:
        self.buffer.append(utterance)
        self.buffer_tokens += count_tokens(utterance)
        if self.buffer_tokens >= self.SEGMENT_TOKENS:
            self._flush()
    
    def _flush(self) -> None:
        if not self.buffer:
            return
        # Use LLM to generate paragraph summary, don't store original
        summary = self._summarize(self.buffer)
        self.storage.write({
            "type": "episodic_segment",
            "summary": summary,
            "timestamp": now_iso(),
            "token_count": self.buffer_tokens,
            # Content hash as audit fingerprint, don't store original content
            "content_hash": sha256("\n".join(self.buffer)),
        })
        self.buffer.clear()
        self.buffer_tokens = 0
```

**Key design decisions** (must confirm in Phase 0 Spec stage):
1. Whether precise citation of original text is needed → affects granularity selection
2. Whether compliance requirements prohibit storing original conversations → affects whether only summaries can be stored
3. Retrieval latency requirements → finer granularity = slower retrieval (more vector calculations)
4. Multi-tenant scenarios: granularity choice affects storage isolation cost

> Complete implementation comparison → `/agent-episodic-memory`

## Progress File Design

Progress files are the key to agents resuming work state across sessions.

### JSON Trumps Markdown

**Core reason**: When appending to Markdown, agents tend to "rewrite the full text" rather than precisely append, causing history loss. JSON's structured format makes agents more likely to precisely modify specific fields.

### Recommended Template

```json
{
  "project": "project-name",
  "last_updated": "2026-04-06T10:30:00Z",
  "current_phase": "module-2",
  "modules": [
    {
      "name": "module-1",
      "status": "PASS",
      "verified_at": "2026-04-06T09:00:00Z",
      "verification_command": "cargo test --lib",
      "verification_output_hash": "sha256:abc123...",
      "notes": "31 tests passed"
    },
    {
      "name": "module-2",
      "status": "IN_PROGRESS",
      "started_at": "2026-04-06T09:30:00Z",
      "blockers": []
    }
  ],
  "session_history": [
    {
      "session_id": "sess_001",
      "started_at": "2026-04-06T08:00:00Z",
      "ended_at": "2026-04-06T09:30:00Z",
      "tokens_used": 125000,
      "modules_completed": ["module-1"]
    }
  ]
}
```

> More patterns and comparisons → `references/progress-file-patterns.md`

## Multi-Tenant Memory Key Namespace Design

**Problem**: In multi-user SaaS or multi-agent systems, improper memory key design leads to:
- **Leakage**: User A's memory matches User B's queries
- **Pollution**: Memory written by Agent A interferes with Agent B's behavior
- **GDPR difficulty**: Cannot precisely delete all memories for a specific user

### Namespace Design Principles

```
Format: {scope}:{entity_id}:{type}:{key}

Scope hierarchy (outer to inner):
├── org:{org_id}               — Organization level (shared knowledge, rules)
│   ├── user:{user_id}         — User level (preferences, history, behavioral patterns)
│   │   ├── session:{sess_id}  — Session level (current task context)
│   │   └── project:{proj_id} — Project level (cross-session project memory)
│   └── agent:{agent_id}       — Agent level (agent's own metacognition)
└── global:                    — Global level (read-only reference knowledge)

Example keys:
  org:acme:user:u123:feedback:code_style
  org:acme:project:frontend-v2:context:architecture
  global:knowledge:python:best_practices
```

### Per-School Namespace Implementation

**File Memory (single-user CLI)**: Directory is namespace
```
~/.claude/projects/{project_hash}/memory/
├── user_preferences.md    # user-level memory
├── project_context.md     # project-level memory
└── MEMORY.md              # index
```

**Block Memory (Letta multi-tenant)**: `agent_id` isolation
```python
# Each user corresponds to an independent agent instance
agent = client.create_agent(
    name=f"user-{user_id}-agent",
    # Core Memory is private to this agent, physically isolated
)
# Queries must specify agent_id, cannot accidentally access cross-agent
messages = client.send_message(agent_id=agent.id, ...)
```

**Semantic Memory (MemU / pgvector)**: Column-level tenant isolation
```sql
CREATE TABLE memories (
    id          UUID DEFAULT gen_random_uuid(),
    tenant_id   VARCHAR NOT NULL,   -- Tenant ID (must be provided on query)
    user_id     VARCHAR NOT NULL,   -- User ID
    scope       VARCHAR NOT NULL,   -- 'session' | 'project' | 'org'
    key         VARCHAR NOT NULL,
    content     TEXT,
    embedding   vector(1536),
    PRIMARY KEY (id)
);

-- All queries enforced with tenant_id filter (Row-Level Security)
CREATE POLICY tenant_isolation ON memories
    USING (tenant_id = current_setting('app.tenant_id'));

-- Precisely delete all memories for a user (GDPR right to erasure)
DELETE FROM memories WHERE tenant_id = ? AND user_id = ?;
```

### Access Control Matrix

| Operation | session | user | project | org | global |
|-----------|---------|------|---------|-----|--------|
| Current user read | ✓ | ✓ | ✓ (participating projects) | ✓ | ✓ |
| Current user write | ✓ | ✓ | ✓ (participating projects) | ✗ | ✗ |
| Other user read | ✗ | ✗ | ✓ (shared projects) | ✓ | ✓ |
| Agent cross-tenant read | ✗ | ✗ | ✗ | ✗ (unless authorized) | ✓ |

**Iron rule**: Memory read API must forcibly carry `tenant_id` parameter; interface design must never allow "no-tenant full query."

### Cross-User Aggregated Memory Pattern

**Problem**: Multi-tenant isolation is a security baseline, but some scenarios require extracting **aggregated insights** from multiple users' behaviors under isolation. For example:
- "Department-level common questions" — extract Top 10 FAQ from 100 users' independent sessions
- "Organization-level best practices" — aggregate team norms from multiple developers' coding memories
- "Product improvement signals" — discover common pain points from user failure memories

The essential difference from "leakage": **Aggregated memory contains no raw data from any individual user, only statistically/refined insights.**

**Three aggregation patterns**:

```
Pattern A: Offline aggregation (recommended for org knowledge base)
    Background job periodically scans all user-level memories within org
    → Extract high-frequency patterns (clustering / LLM summary)
    → Write to org:{org_id}:knowledge:faq (org-level read-only memory)
    → Inject org-level memory on user query; user cannot perceive source

Pattern B: Real-time voting aggregation (recommended for FAQ updates)
    Each time agent generates high-quality answer, record "answer hash"
    → When same question answered N times, trigger aggregation write to org level
    → Threshold N (recommended 5-10) prevents noise writes

Pattern C: Explicit admin elevation
    User/admin actively "elevates" their user-level memory to org level
    → Fully controlled, no automatic aggregation
    → Suited for enterprise scenarios with strict knowledge management
```

**Implementation points (PostgreSQL solution)**:

```sql
-- Org-level aggregated memory table (write-only, append-only)
CREATE TABLE org_knowledge (
    id          UUID DEFAULT gen_random_uuid(),
    org_id      VARCHAR NOT NULL,
    category    VARCHAR NOT NULL,   -- 'faq' | 'best_practice' | 'pain_point'
    content     TEXT NOT NULL,
    source_count INT DEFAULT 1,     -- Anonymous count of how many users contributed
    confidence  FLOAT DEFAULT 0.5,  -- Aggregation confidence
    embedding   vector(1536),
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (id)
);

-- During aggregation: only store statistical results, not original user data
INSERT INTO org_knowledge (org_id, category, content, source_count, confidence)
SELECT 
    org_id,
    'faq',
    summarize_cluster(cluster_texts),  -- LLM summary, does not contain originals
    COUNT(*),
    AVG(similarity_score)
FROM user_memory_clusters
WHERE org_id = ? AND cluster_size >= 5  -- Aggregate only when at least 5 people asked
GROUP BY org_id, cluster_id;
```

**Security principles**:
1. Aggregation job execution permissions > regular user permissions; requires service account separate authorization
2. Aggregation results store only source_count (count), not source_user_ids (user list)
3. Aggregated content passes through PII filtering (removes names, emails, usernames in code paths, etc.)
4. Aggregation memory deletion strategy: admin deletion, not triggered by user GDPR deletion request

## Session Persistence Selection

```
What are your persistence needs?
│
├─ Single user, local CLI → Filesystem (JSON/SQLite)
│  Simplest solution. Claude Code uses files, OpenCode uses SQLite [OC]
│
├─ Multi-user, need queries → SQLite + WAL
│  OpenCode solution [OC]: sessions/messages/files three tables
│  WAL mode supports concurrent reads/writes
│
└─ Multi-user, need scaling → PostgreSQL
   MemU solution [MU]: supports profile-based storage isolation
   Letta solution [LT]: SQLAlchemy ORM, multi-backend support
```

### OpenCode's SQLite Solution [OC]

```sql
-- Three-table structure
sessions (id, title, model, created_at, updated_at)
messages (id, session_id, role, content, tokens, created_at)
files    (id, session_id, path, content, created_at)

-- PubSub notifies of changes
SessionBroker.publish(SessionCreated{id, title})
MessageBroker.publish(MessageAdded{session_id, message})
```

Paired with PubSub for real-time UI updates without polling.

## Auto Memory Extraction [CC]

Claude Code's forked agent mode is the most elegant auto-memory extraction solution.

### Why Fork?

1. **Doesn't block main loop** — memory extraction is low-priority
2. **Independent context** — child process has full conversation history but doesn't affect main agent state
3. **Failure-safe** — child process crash doesn't affect main agent

### Extraction Timing

- Every N tool calls (Claude Code default behavior)
- User explicit request (`/memory` command)
- Before session ends
- When compact is triggered (extract memories while compacting context)

### Extraction Quality

Extraction prompts should distinguish memory types:
- **user**: user preferences, habits, identity information
- **feedback**: user corrections to agent behavior
- **project**: project architecture, tech stack, conventions
- **reference**: reusable technical knowledge

## Engineering Persistence vs LLM Cognitive Memory (P22)

The three memory schools (episodic/semantic/working) in Phase 4 are all **LLM cognitive memory** — helping LLM remember information across sessions. But stateless services like webhook agents need **engineering persistence** — preventing duplicate processing, caching expensive computations, storing configuration state. The two have completely different purposes and shouldn't use the same framework.

**Decision branch (ask this before deciding among the three schools)**:

```
Does LLM need to "remember" anything across sessions?
  Yes → Enter three-school decision (episodic/semantic/working)
  No → You probably just need engineering persistence (see below), use Redis/SQLite directly, no memory system needed
```

**Four engineering persistence patterns:**

```python
import redis.asyncio as redis
import sqlite3
from datetime import datetime, timedelta

# Pattern 1: Idempotency cache (prevent duplicate processing)
class IdempotencyCache:
    def __init__(self, client: redis.Redis, ttl_hours: int = 24):
        self.r = client
        self.ttl = ttl_hours * 3600

    async def is_processed(self, event_id: str) -> bool:
        return await self.r.exists(f"processed:{event_id}") > 0

    async def mark_processed(self, event_id: str) -> None:
        await self.r.set(f"processed:{event_id}", "1", ex=self.ttl)

# Pattern 2: Request result cache (expensive LLM call cache)
class ClassificationCache:
    def __init__(self, client: redis.Redis, ttl_minutes: int = 60):
        self.r = client
        self.ttl = ttl_minutes * 60

    async def get(self, text_hash: str) -> dict | None:
        raw = await self.r.get(f"classify:{text_hash}")
        return json.loads(raw) if raw else None

    async def set(self, text_hash: str, result: dict) -> None:
        await self.r.set(f"classify:{text_hash}", json.dumps(result), ex=self.ttl)

# Pattern 3: Config/rule storage (runtime-updatable)
# → SQLite or Redis Hash, not LLM memory
CREATE TABLE triage_rules (
    pattern TEXT PRIMARY KEY,
    category TEXT,
    auto_create_issue BOOLEAN,
    updated_at TIMESTAMP
);

# Pattern 4: Operation log (audit + resume)
# → Append-only write, not LLM episodic memory
```

**Key distinctions:**

| Need | Right Solution | Wrong Solution |
|------|---------------|---------------|
| Prevent same event from being processed twice | Redis idempotency cache | LLM working memory |
| Avoid repeating LLM classification calls | Redis result cache | Episodic memory retrieval |
| Store classification rules | SQLite config table | Semantic memory vector store |
| Remember what user said across N sessions | LLM episodic/semantic memory ✓ | Redis cache |

---

## Current State (April 2026)

1. **File Memory Still the Optimal CLI Agent Solution** — Claude Code's MEMORY.md pattern is widely validated; its simplicity and git-trackable nature make it irreplaceable for single-user CLI scenarios. KAIROS mode (append-only + /dream organization) is being adopted by more projects.
2. **Block Memory Sinking to Agent OS Layer** — Letta's Core/Archival/Recall three-tier architecture is transitioning from application layer to standard Agent platform capability. Multiple agent frameworks are beginning to build in similar structured memory CRUD interfaces; memory management shifting from "self-built" to "platform-provided."
3. **Semantic Memory Cost Threshold Plummeting** — High-quality embedding model inference costs (Cohere embed v4, OpenAI text-embedding-3-large, verified: 2026-04-08) have dropped below $0.02/MTok, making hierarchical semantic memory go from "only large teams can afford" to "individual developers can deploy."
4. **Memory Security Becomes New Topic** — User preferences, behavioral patterns, project details stored in agent memory constitute privacy-sensitive data. GDPR/CCPA compliance requires memory systems to support "right to erasure" (delete all memories for a specific user on demand), which technically tensions with distributed storage of semantic memory.
5. **Cross-Agent Memory Sharing Protocol Sprouting** — In multi-agent systems, different agents need to share some memory (project context, user preferences) while isolating their respective working memories. Memory sharing protocols based on namespace + access control are beginning to show standardization trends.
6. **RAG + Light Fine-tuning Hybrid Architecture Becomes 2026 New Standard** — In customer service/knowledge base agent scenarios, pure RAG accuracy ~89%, pure Fine-tuning ~91%, combined reaching 96%. Selection guide: frequent knowledge updates (daily/weekly) → prioritize RAG (monthly cost $500-2000 vs FT retraining $20K+); domain tone/terminology injection → FT patch; multi-hop reasoning → Agentic RAG (but must add external verification hooks to prevent self-critique loops from amplifying hallucinations). Note: Agentic RAG has higher hallucination risk than pure RAG on open-ended questions; acceptance must include hallucination rate sampling (see `/agentforge-benchmark`).

## Known Pitfalls

1. **Memory bloat out of control** — Agent auto-extracts memories but lacks culling mechanism; MEMORY.md quickly swells to limit, filled with low-value entries (e.g., "user said thank you"). Solution: implement memory value scoring + periodic /dream organization; auto-demote low-score entries to archival tier or delete. Set memory type quotas (e.g., feedback max 20 entries).
2. **Progress file rewritten by agent** — When using Markdown-format progress files, agent tends to "rewrite entire file" rather than precisely append, causing history loss. Solution: enforce JSON format progress files; agents modify JSON more precisely (modify specific fields rather than rewrite).
3. **Memory consistency drift** — Same information stored repeatedly across multiple memory entries but with inconsistent content (e.g., user preference says "prefers Python" in v1 entry, "prefers Rust" in v2); agent randomly retrieves one on recall causing inconsistent behavior. Solution: deduplication + conflict checking at memory write time; update rather than append when new information conflicts with existing entries.
4. **Semantic retrieval "similar words, different meanings" problem** — High vector similarity doesn't equal semantic relevance. "Python memory management" and "Python memory system" are semantically different but vector-close. Solution: semantic retrieval results must pass through LLM rerank or adequacy check (MemU's 7-step RAG solution); pure vector search cannot be used as final result.
5. **Session persistence vs privacy conflict** — Default persisting all session content causes sensitive information (API keys, passwords, internal URLs) to be permanently stored. Solution: implement sensitive information filtering on session persistence (regex + LLM judgment); mark sensitive content as ephemeral and don't write to persistence layer.

## Further Reading

| Topic | Resource |
|-------|---------|
| Complete three-school implementation comparison (File/Block/Semantic) | [`references/memory-paradigms-comparison.md`](references/memory-paradigms-comparison.md) |
| Progress file patterns and templates | [`references/progress-file-patterns.md`](references/progress-file-patterns.md) |
| Memory selection underlying principles | `/llm-agent-memory` |
| Episodic memory (event sequence) design | `/agent-episodic-memory` |
| Semantic memory (vector + knowledge graph) design | `/agent-semantic-memory` |
| Context compression vs memory extraction boundary | `/agentforge-context` |

## Memory System Checklist

- [ ] Selected memory paradigm (file / block / hierarchical semantic)
- [ ] Memory storage has clear capacity ceiling and culling strategy
- [ ] Progress file uses JSON format (not Markdown)
- [ ] Session persistence solution selected (file / SQLite / PostgreSQL)
- [ ] Implemented auto memory extraction (or have clear manual extraction process)
- [ ] Memory retrieval has quality assurance (not just vector similarity)
- [ ] Multi-session scenario memory isolation strategy clear (per-user / per-project / global)
- [ ] Multi-modal scenario: images prefer caption storage, audio prefers transcript storage, don't directly store raw binary as recall index

## Reverse Audit (Diagnose Mode)

> Called by `/agentforge-diagnose` — static audit of existing code across D4 Memory dimensions.

| # | Check Item | How | Pass Criteria |
|---|-----------|-----|---------------|
| M1 | Memory school identifiable | Search for .md file writes, sqlite/redis operations, embedding calls | Can determine which of File/Block/Semantic is used |
| M2 | Cross-session persistence | `grep -rn "json.dump\|sqlite\|redis\|pickle\|persist" src/` | Has file/DB writes; state doesn't disappear on process termination |
| M3 | Memory capacity bounded | Look at write logic; is there max_entries/TTL/eviction strategy | Unlimited append write = warning |
| M4 | Pollution protection | Look at update logic; is there deduplication/conflict checking | Has basic consistency protection (won't write contradictory info) |
| M5 | Deletion support | `grep -rn "delete\|remove\|forget" src/ \| grep -i mem` | Has interface to delete memory (right to erasure / error correction) |

**High-probability issues**: Forgets on restart (all in-memory P1), memory unbounded growth (P2 performance hazard), cannot delete erroneous memories (P2 user experience)

## Next Step

Memory system selection complete → **`/agentforge-security`** (Phase 5: Security & Sandbox)
