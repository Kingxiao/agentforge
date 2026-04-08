# Sub-Agent Spawn Mode Implementation Details

> Sources: Claude Code, Codex CLI, OpenCode multi-agent implementations

## Claude Code's AgentTool Implementation [CC]

```typescript
// src/tools/AgentTool/AgentTool.tsx
export async function* call(input: {
  description: string;
  prompt: string;
  run_in_background?: boolean;
  isolation?: "worktree" | "remote";
  model?: string;
}) {
  const agentId = createAgentId();
  
  if (input.run_in_background) {
    // Async mode: returns agentId immediately
    registerAsyncAgent(agentId, input);
    launchInBackground(agentId, input);
    yield { status: "async_launched", agentId };
  } else if (input.isolation === "worktree") {
    // Worktree mode: create isolated environment
    const worktree = await createGitWorktree();
    const result = await runInWorktree(worktree, input);
    await cleanupWorktree(worktree, result.hasChanges);
    yield { status: "completed", result, branch: worktree.branch };
  } else {
    // Synchronous mode: wait for completion
    const result = await runAgent(agentId, input);
    yield { status: "completed", result };
  }
}
```

## Disabled Tool List [CC]

```typescript
const CUSTOM_AGENT_DISALLOWED_TOOLS = [
  "EnterPlanMode",
  "ExitPlanMode",
  "EnterWorktree",   // Prevent nested worktree
  "TeamCreate",
  "TeamDelete",
  "Agent",           // Prevent recursive spawn
];
```

## Codex CLI's Agent Control [CX]

```rust
// codex-rs/core/src/agent/control.rs (42KB)
pub async fn spawn_agent(
    &self,
    config: Config,
    initial_operation: Op,
    session_source: Option<SessionSource>,
) -> CodexResult<ThreadId> {
    let thread_id = ThreadId::new();
    let agent = Agent::new(config, thread_id.clone());
    
    // Register to global registry
    self.registry.lock().await.insert(thread_id.clone(), agent);
    
    // Submit initial operation
    agent.submit(initial_operation).await?;
    
    Ok(thread_id)
}
```

### Inter-Agent Communication

```rust
Op::InterAgentCommunication {
    communication: AgentMessage {
        from: ThreadId,
        to: ThreadId,
        content: String,
        metadata: HashMap<String, Value>,
    }
}
```

## OpenCode's Session Inheritance [OC]

```go
// Child agent inherits via Session
type Session struct {
    ID              string
    ParentSessionID string  // Points to parent Session
    Title           string
    PromptTokens    int64
    CompletionTokens int64
    Cost            float64  // Auto-aggregates to parent
}

// AgentTool creates child Session
func (t *AgentTool) Run(ctx, call) (ToolResponse, error) {
    childSession := t.sessionService.Create(ctx, {
        ParentSessionID: currentSessionID(ctx),
    })
    
    // Run agent in child Session
    result := t.agent.Run(ctx, childSession.ID, call.Prompt)
    return ToolResponse{Content: result}, nil
}
```

## Worktree Isolation Implementation Details

```bash
# Create isolated worktree
git worktree add /tmp/agent-worktree-{uuid} -b agent/{task-name}

# Agent works in worktree
cd /tmp/agent-worktree-{uuid}
# ... execute task ...

# On completion, check for changes
if git diff --quiet && git diff --cached --quiet; then
    # No changes, clean up directly
    git worktree remove /tmp/agent-worktree-{uuid}
    git branch -D agent/{task-name}
else
    # Has changes, keep branch for main agent to merge
    git add -A && git commit -m "agent: {task-description}"
    git worktree remove /tmp/agent-worktree-{uuid}
    # Return branch name to main Agent
fi
```

## Progress Tracking

```typescript
// Claude Code's progress UI
interface AgentProgress {
  agentId: string;
  description: string;
  status: "running" | "completed" | "failed";
  progress?: string;       // Current step description
  startedAt: number;
  completedAt?: number;
}

// TUI bottom bar displays:
// [Agent 1: Searching API usage...] [Agent 2: ✓ Done] [Agent 3: Running tests...]
```
