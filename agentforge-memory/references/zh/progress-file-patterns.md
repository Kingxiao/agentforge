# Progress File Design Patterns

> Design patterns for agents to resume work state across sessions.

## Why JSON Trumps Markdown [CC]

### The Problem

Agents (especially LLM-driven agents) have a systematic weakness when handling Markdown progress files: they tend to **rewrite the entire file rather than precisely modifying** specific entries.

```
Scenario: Agent completes module-3, needs to update progress file

Typical Markdown progress file failure mode:
1. Agent reads entire PROGRESS.md
2. Agent generates "updated version"
3. During generation, details from earlier modules get compressed or lost due to LLM summarization tendency
4. Write → incomplete history

JSON progress file advantages:
1. Agent reads JSON
2. Agent precisely modifies modules[2].status = "PASS"
3. All other fields unchanged
4. Write → complete history
```

### Quantified Comparison

| Dimension | Markdown | JSON |
|-----------|----------|------|
| History loss risk | High (full-rewrite update) | Low (field-level update) |
| Machine-parseable | Weak (requires format conventions) | Strong (standard parsers) |
| Human-readable | Excellent | Good (with formatting) |
| Conflict merging | Difficult | Moderate (JSON diff tools) |
| Append operations | Ambiguous (agent doesn't know where to append) | Clear (push to array) |

## JSON Progress File Templates [CC]

### Minimal Viable Version

```json
{
  "project": "my-agent",
  "schema_version": 1,
  "last_updated": "2026-04-06T10:30:00Z",
  "current_phase": "module-2",
  "modules": [
    {
      "name": "module-1-provider-abstraction",
      "status": "PASS",
      "risk_level": "medium",
      "verified_at": "2026-04-06T09:00:00Z",
      "verification": {
        "command": "cargo test --lib provider",
        "exit_code": 0,
        "output_hash": "sha256:abc123def456...",
        "summary": "12 tests passed, 0 failed"
      },
      "files_changed": [
        "src/provider/mod.rs",
        "src/provider/anthropic.rs"
      ],
      "notes": "Provider trait design参考 OpenCode 的 StreamResponse 接口"
    },
    {
      "name": "module-2-tool-system",
      "status": "IN_PROGRESS",
      "risk_level": "high",
      "started_at": "2026-04-06T09:30:00Z",
      "blockers": [
        "MCP SDK version compatibility待确认"
      ],
      "subtasks": [
        {"name": "tool-interface", "status": "DONE"},
        {"name": "tool-registry", "status": "IN_PROGRESS"},
        {"name": "mcp-integration", "status": "BLOCKED"}
      ]
    },
    {
      "name": "module-3-context-engine",
      "status": "PENDING",
      "risk_level": "low",
      "depends_on": ["module-2-tool-system"]
    }
  ]
}
```

### Full Version (with session tracking and cost)

```json
{
  "project": "my-agent",
  "schema_version": 2,
  "last_updated": "2026-04-06T14:00:00Z",
  "current_phase": "module-3",
  "total_cost_usd": 4.52,
  
  "modules": [
    {
      "name": "module-1",
      "status": "PASS",
      "verified_at": "2026-04-06T09:00:00Z",
      "verification": {
        "command": "cargo test --lib",
        "exit_code": 0,
        "output_hash": "sha256:...",
        "summary": "31 tests passed"
      },
      "cost_usd": 1.23,
      "session_ids": ["sess_001"]
    }
  ],
  
  "session_history": [
    {
      "session_id": "sess_001",
      "started_at": "2026-04-06T08:00:00Z",
      "ended_at": "2026-04-06T09:30:00Z",
      "model": "claude-sonnet-4-6",
      "tokens": {
        "input": 85000,
        "output": 40000,
        "cache_read": 62000,
        "cache_create": 12000
      },
      "cost_usd": 1.23,
      "modules_completed": ["module-1"],
      "compact_count": 2,
      "notes": "First session, completed Provider abstraction layer"
    },
    {
      "session_id": "sess_002",
      "started_at": "2026-04-06T10:00:00Z",
      "ended_at": "2026-04-06T12:00:00Z",
      "model": "claude-sonnet-4-6",
      "tokens": {
        "input": 120000,
        "output": 55000,
        "cache_read": 95000,
        "cache_create": 8000
      },
      "cost_usd": 1.85,
      "modules_completed": ["module-2"],
      "compact_count": 3,
      "notes": "Tool system completed, MCP integration used mock backend"
    }
  ],
  
  "issues_discovered": [
    {
      "id": "ISS-001",
      "severity": "medium",
      "description": "Provider error handling does not cover rate limit scenarios",
      "discovered_in": "module-2",
      "status": "DEFERRED",
      "reason": "Does not affect MVP, planned for module-5"
    }
  ]
}
```

## Markdown Progress File (Reference for Comparison) [CC]

CLAUDE.md recommended PROGRESS.md format from Claude Code:

```markdown
## module-1-provider - 2026-04-06T09:00:00Z

### Verification Command
cargo test --lib provider

### Verification Output
running 12 tests
test provider::anthropic::test_send ... ok
test provider::anthropic::test_stream ... ok
...
test result: ok. 12 passed; 0 failed

### Status: PASS

---

## module-2-tools - 2026-04-06T12:00:00Z
...
```

**Problems**:
- Agent updating module-2 may rewrite module-1's verification output
- No structured cost tracking
- Hard to parse programmatically (needs regex for `### Status: PASS`)
- Good for human reading, bad for machine consumption

**When Markdown is still the right choice**:
- Small project scale (< 5 modules)
- No need for programmatic progress parsing
- Team members need to read directly on GitHub

## Session Metadata Pattern [OC]

OpenCode uses SQLite + PubSub for session state management:

```sql
-- Schema (Goose migration management)
CREATE TABLE sessions (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL DEFAULT '',
    model       TEXT NOT NULL DEFAULT '',
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Progress tracking
    summary     TEXT,          -- LLM-generated session summary
    message_count INTEGER DEFAULT 0
);

CREATE TABLE messages (
    id          TEXT PRIMARY KEY,
    session_id  TEXT NOT NULL REFERENCES sessions(id),
    role        TEXT NOT NULL,   -- user / assistant / system / tool
    content     TEXT NOT NULL,
    
    -- Token tracking
    input_tokens  INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- File snapshots (version of files edited during session)
CREATE TABLE files (
    id          TEXT PRIMARY KEY,
    session_id  TEXT NOT NULL REFERENCES sessions(id),
    path        TEXT NOT NULL,
    content     TEXT NOT NULL,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### PubSub Real-Time Notifications [OC]

```go
// Session state changes broadcast via PubSub
type SessionBroker struct {
    subscribers map[string]chan SessionEvent
}

// Event types
type SessionEvent struct {
    Type      string  // "created" | "updated" | "deleted"
    SessionID string
    Data      any
}

// UI subscribes to session changes, no polling needed
ch := broker.Subscribe("session-*")
for event := range ch {
    updateUI(event)
}
```

**Strengths**:
- WAL mode supports concurrent reads/writes
- PubSub decouples UI and data layer
- File snapshots support rollback
- SQL queries are flexible (e.g., "token usage in past 7 days")

## Cost Tracking Patterns

### Basic Token Billing [CC] [OC]

```
After each API call, record:
{
  "input_tokens": 8500,
  "output_tokens": 2300,
  "cache_creation_tokens": 1200,    // First cache creation (1.25× cost)
  "cache_read_tokens": 6800,        // Cache hit (0.1× cost)
}

Cost calculation:
cost = (input - cache_read) * input_price
     + cache_read * input_price * 0.1
     + cache_creation * input_price * 1.25
     + output * output_price
```

### Session-Level Aggregation

```json
{
  "session_cost": {
    "api_calls": 47,
    "total_input_tokens": 425000,
    "total_output_tokens": 89000,
    "cache_hit_rate": 0.73,
    "total_cost_usd": 2.14,
    "cost_per_module": {
      "module-1": 0.45,
      "module-2": 1.12,
      "module-3": 0.57
    }
  }
}
```

### Budget Guard

```
Set budget ceiling in progress file:
{
  "budget": {
    "max_per_session_usd": 5.00,
    "max_per_module_usd": 3.00,
    "max_total_usd": 20.00,
    "alert_threshold": 0.8
  }
}

Agent checks after each API call:
if session_cost > budget.max_per_session * budget.alert_threshold:
    warn("Approaching session budget limit")
if session_cost > budget.max_per_session:
    stop("Session budget limit reached, need user confirmation to continue")
```

## Selection Guide

```
What level of progress tracking does your agent need?
│
├─ Solo development, < 5 modules
│  → JSON progress file (minimal viable version)
│  → File in project root: progress.json
│
├─ Team development, need UI display
│  → SQLite + PubSub [OC]
│  → Supports real-time UI updates, flexible SQL queries
│
└─ Platform-level, multi-project multi-agent
   → PostgreSQL + Event Sourcing
   → Complete audit trail, cross-project analysis
```
