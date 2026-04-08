# Sub-Agent Spawn 模式实现细节

> 来源：Claude Code、Codex CLI、OpenCode 的多 Agent 实现

## Claude Code 的 AgentTool 实现 [CC]

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
    // 异步模式：立即返回 agentId
    registerAsyncAgent(agentId, input);
    launchInBackground(agentId, input);
    yield { status: "async_launched", agentId };
  } else if (input.isolation === "worktree") {
    // Worktree 模式：创建隔离环境
    const worktree = await createGitWorktree();
    const result = await runInWorktree(worktree, input);
    await cleanupWorktree(worktree, result.hasChanges);
    yield { status: "completed", result, branch: worktree.branch };
  } else {
    // 同步模式：等待完成
    const result = await runAgent(agentId, input);
    yield { status: "completed", result };
  }
}
```

## 禁用工具列表 [CC]

```typescript
const CUSTOM_AGENT_DISALLOWED_TOOLS = [
  "EnterPlanMode",
  "ExitPlanMode",
  "EnterWorktree",   // 防嵌套 worktree
  "TeamCreate",
  "TeamDelete",
  "Agent",           // 防递归 spawn
];
```

## Codex CLI 的 Agent 控制 [CX]

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
    
    // 注册到全局 registry
    self.registry.lock().await.insert(thread_id.clone(), agent);
    
    // 提交初始操作
    agent.submit(initial_operation).await?;
    
    Ok(thread_id)
}
```

### Agent 间通信

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

## OpenCode 的 Session 继承 [OC]

```go
// 子 Agent 通过 Session 继承实现
type Session struct {
    ID              string
    ParentSessionID string  // 指向父 Session
    Title           string
    PromptTokens    int64
    CompletionTokens int64
    Cost            float64  // 自动汇总到父
}

// AgentTool 创建子 Session
func (t *AgentTool) Run(ctx, call) (ToolResponse, error) {
    childSession := t.sessionService.Create(ctx, {
        ParentSessionID: currentSessionID(ctx),
    })
    
    // 在子 Session 中运行 Agent
    result := t.agent.Run(ctx, childSession.ID, call.Prompt)
    return ToolResponse{Content: result}, nil
}
```

## Worktree 隔离的实现细节

```bash
# 创建隔离 worktree
git worktree add /tmp/agent-worktree-{uuid} -b agent/{task-name}

# Agent 在 worktree 中工作
cd /tmp/agent-worktree-{uuid}
# ... 执行任务 ...

# 完成后检查是否有修改
if git diff --quiet && git diff --cached --quiet; then
    # 无修改，直接清理
    git worktree remove /tmp/agent-worktree-{uuid}
    git branch -D agent/{task-name}
else
    # 有修改，保留分支供主 Agent 合并
    git add -A && git commit -m "agent: {task-description}"
    git worktree remove /tmp/agent-worktree-{uuid}
    # 返回分支名给主 Agent
fi
```

## 进度追踪

```typescript
// Claude Code 的进度 UI
interface AgentProgress {
  agentId: string;
  description: string;
  status: "running" | "completed" | "failed";
  progress?: string;       // 当前步骤描述
  startedAt: number;
  completedAt?: number;
}

// TUI 底部显示：
// [Agent 1: 搜索 API 用法...] [Agent 2: ✓ 完成] [Agent 3: 运行测试...]
```
