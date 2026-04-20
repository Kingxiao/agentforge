# Agent Registry and Lifecycle Management Patterns

> Sources: Codex CLI ThreadManager, OpenCode Session inheritance, Claude Code Agent progress tracking

## Codex CLI: ThreadManager Pattern [CX]

Codex implements a complete Agent registry in Rust:

```rust
// Core structure
struct AgentRegistry {
    agents: HashMap<ThreadId, AgentHandle>,
    parent: Weak<ThreadManager>,  // Weak reference prevents cycles
}

struct AgentHandle {
    thread_id: ThreadId,
    config: Config,
    status: AgentStatus,
    created_at: Instant,
}

enum AgentStatus {
    Running,
    Completed(CompletionResult),
    Failed(AgentError),
    Cancelled,
}
```

### Lifecycle

```
spawn_agent(config, initial_op)
    → ThreadId
    → Register to registry
    ↓
monitor(thread_id)
    → AgentStatus (polling or event notification)
    ↓
cleanup(thread_id)
    → Release resources
    → Remove from registry
```

### Inter-Agent Communication

```rust
// Messages passed via Op enum
Op::InterAgentCommunication {
    communication: AgentMessage {
        from: ThreadId,      // sender
        to: ThreadId,        // receiver
        content: String,     // message content
        metadata: HashMap<String, Value>,
    }
}
```

**Key design decisions**:
- Messages passed via channels, not shared memory
- Parent holds strong reference to child agents; reverse is weak reference
- Child agent crash doesn't cause parent crash (error isolation)

---

## OpenCode: Session Inheritance Pattern [OC]

OpenCode uses Go's Session mechanism for parent-child relationships:

```go
type Session struct {
    ID               string
    ParentSessionID  string   // points to parent Session, empty means root
    Title            string
    PromptTokens     int64
    CompletionTokens int64
    Cost             float64  // auto-aggregated to parent
    CreatedAt        time.Time
    UpdatedAt        time.Time
}
```

### AgentTool Creates Child Session

```go
func (t *AgentTool) Run(ctx context.Context, call ToolCall) (ToolResponse, error) {
    // Create child session
    childSession := t.sessionService.Create(ctx, CreateSessionParams{
        ParentSessionID: currentSessionID(ctx),
        Title:           call.Description,
    })
    
    // Run agent in child session
    result := t.agent.Run(ctx, childSession.ID, call.Prompt)
    
    // Cost auto-aggregated to parent session
    return ToolResponse{Content: result}, nil
}
```

**Key design decisions**:
- Sessions are persisted (SQLite); recoverable after restart
- Cost (token count, fees) auto-rolls up to parent
- Child sessions aren't deleted after completion; audit trail preserved

---

## Claude Code: Async Agent Progress Tracking [CC]

Claude Code's agent management is lighter-weight, focused on async progress tracking:

```typescript
interface AgentProgress {
    agentId: string;
    description: string;
    status: "running" | "completed" | "failed";
    progress?: string;      // current step description
    startedAt: number;
    completedAt?: number;
}
```

### Lifecycle

```
registerAsyncAgent(agentId, {description, prompt, model})
    ↓
updateAgentProgress(agentId, progress)  // streaming updates
    ↓
completeAgentTask(agentId, result)      // completion
    ↓
enqueueAgentNotification()              // notify main loop
    ↓
removeAgent(agentId)                    // cleanup
```

### TUI Progress Display

```
Bottom status bar:
[Agent 1: Searching API usage...] [Agent 2: ✓ Done] [Agent 3: Running tests...]
```

**Key design decisions**:
- Agent state not persisted (valid within session only)
- Notification mechanism: agent completes → enqueued → main loop consumes
- Progress is purely a UI concept; doesn't affect agent execution logic

---

## Pattern Comparison

| Dimension | Codex (Rust) | OpenCode (Go) | Claude Code (TS) |
|-----------|-------------|---------------|-----------------|
| Registry | HashMap + strong/weak refs | Session table (SQLite) | In-memory Map |
| Persistence | No | Yes (SQLite) | No |
| Parent-child | ThreadId reference | ParentSessionID | agentId tag |
| Communication | Op messages + channel | PubSub events | Notification queue |
| Cost tracking | None | Auto-rollup to parent | None |
| Error isolation | Weak refs prevent cascade | Sessions independent | try-catch isolation |
| Complexity | High (complete system) | Medium (Session inheritance) | Low (minimal implementation) |

## Selection Guide

```
What level of management does your agent system need?
│
├─ Just need to run a few sub-tasks in parallel
│  → Claude Code pattern: in-memory Map + notification queue
│
├─ Need cross-session recovery, cost tracking
│  → OpenCode pattern: Session table + auto-rollup
│
└─ Need complex inter-agent communication, error isolation
   → Codex pattern: complete registry + channel communication
```
