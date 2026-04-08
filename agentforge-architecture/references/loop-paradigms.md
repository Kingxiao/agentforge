---
name: agentforge-architecture-references-loop-paradigms
description: Agent Loop Paradigm Reference. Deep dive into 4 loop paradigms with source annotations from 9 production-grade Agent codebases (2026-04-06).
triggers:
  - agent loop paradigm
  - agent loop
  - agent runtime
  - Async Generator
  - PubSub
  - reflection chain
---

# Agent Loop Paradigms: Deep Reference

> Source: Reverse engineering 9 production-grade Agent codebases (2026-04-06)
> Main doc annotations: [CC]=Claude Code, [CX]=Codex CLI, [OC]=OpenCode, [AD]=Aider

## Paradigm 1: Async Generator Loop Implementation Details

### Claude Code Full Flow [CC]

```
src/query.ts (~5000 lines)

User Input
    ↓
[processUserInput] → Normalize messages + attachment handling
    ↓
[fetchSystemPromptParts] → Load CLAUDE.md, memory, context
    ↓
[queryModelWithStreaming] → API call
    ├─ System prompt (context.ts)
    ├─ Message history (normalized)
    ├─ Tools (assembleToolPool dynamic assembly)
    └─ Betas (thinking, JSON output, etc.)
    ↓
[Stream Processing]
    ├─ Content delta accumulation
    ├─ Tool use block streaming parse (StreamingToolExecutor)
    ├─ Hook execution (postSampling, stopHooks)
    └─ Progress feedback
    ↓
[Tool Execution] → runTools()
    ├─ Partitioned by concurrency safety
    ├─ Serial: state-changing tools
    ├─ Parallel: read-only tools
    └─ Results accumulated into messages
    ↓
[Token Budget Check]
    ├─ Auto-compact (fork subprocess when threshold exceeded)
    ├─ Continuation nudge (approaching limit)
    └─ Terminal state (diminishing returns)
    ↓
[Message Persistence] → sessionStorage
```

### Key Code Patterns

```typescript
// Tool execution partitioning (core pattern)
async function runTools(toolUses, context) {
  const { concurrent, sequential } = partition(
    toolUses,
    (t) => t.isConcurrencySafe()
  );
  
  // Parallel execution of read-only tools
  const concurrentResults = await Promise.all(
    concurrent.map(t => executeToolUse(t, context))
  );
  
  // Serial execution of state-changing tools
  for (const tool of sequential) {
    await executeToolUse(tool, context);
  }
}
```

## Paradigm 2: Submission-Handler Implementation Details

### Codex CLI Op Enum [CX]

```rust
// codex-rs/protocol/src/protocol.rs
enum Op {
    UserInput { items, final_output_json_schema },
    UserTurn { items, cwd, approval_policy, sandbox_policy, model, ... },
    InterAgentCommunication { communication },
    ExecApproval { id, turn_id, decision },
    PatchApproval { id, decision },
    ResolveElicitation { server_name, request_id, decision, content },
    RequestPermissionsResponse { id, response },
    DynamicToolResponse { id, response },
    Interrupt,
    Shutdown,
    Compact,
    ListSkills,
    RealtimeConversationStart,
    ListMcpTools,
    RefreshMcpServers,
    ReloadUserConfig,
    // ...32 operation types total
}
```

### TurnContext Structure

Each submission gets an independent TurnContext (Arc-wrapped):
- `cwd`: working directory
- `approval_policy`: AskForApproval settings
- `sandbox_policy`: SandboxPolicy constraints
- `model`: model selection
- `collaboration_mode`: collaboration mode

## Paradigm 3: PubSub Event Loop Implementation Details

### OpenCode PubSub Architecture [OC]

```go
// Generic PubSub Broker
type Broker[T any] struct {
    subs map[chan Event[T]]struct{}
}

// Implementers: Session, Message, Permission, Agent services
type Subscriber[T any] interface {
    Subscribe(context.Context) <-chan Event[T]
}
```

### Agent Event Types

```go
type AgentEvent struct {
    Type    AgentEventType  // Error, Response, Summarize
    Message Message
    Usage   TokenUsage
}
```

### Context Value Injection Pattern

```go
// Inject context before tool execution
ctx = context.WithValue(ctx, tools.SessionIDContextKey, sessionID)
ctx = context.WithValue(ctx, tools.MessageIDContextKey, assistantMsg.ID)
```

## Paradigm 4: Reflection Chain Implementation Details

### Aider's Polymorphic Editing System [AD]

```python
# Edit format as polymorphic attribute of class
class EditBlockCoder(Coder):   edit_format = "diff"
class UnifiedDiffCoder(Coder): edit_format = "udiff"
class PatchCoder(Coder):       edit_format = "patch"
class WholeFileCoder(Coder):   edit_format = "wholefile"
class ArchitectCoder(Coder):   edit_format = "architect"

# Switch at runtime
new_coder = Coder.create(from_coder=existing_coder, edit_format="architect")
```

### Architect Mode (Two-Phase)

1. **Architecture model** (strong model) does high-level planning
2. **Edit model** (can be weak model) executes specific changes

This "plan-execute" separation also appears in Cline (Plan Mode / Act Mode).

## Hidden Constraints in Paradigm Selection

| Constraint | Async Generator | Submission-Handler | PubSub | Reflection Chain |
|------------|----------------|-------------------|--------|--------|
| Minimum implementation lines | ~500 | ~2000 | ~800 | ~300 |
| Streaming UI support | Native | Requires Event conversion | Requires subscription | Requires callback |
| Error recovery | try/finally | match arm | defer | try/except |
| Interruptibility | yield point interrupt | channel close | context cancel | loop break |
| Testing difficulty | Medium (mock generator) | Low (pure functions) | Medium (mock channel) | Low |
| Sub-Agent isolation | fork process | new ThreadId | new Session | new Coder instance |
