# Agent 注册表与生命周期管理模式

> 来源：Codex CLI ThreadManager、OpenCode Session 继承、Claude Code Agent 进度追踪

## Codex CLI：ThreadManager 模式 [CX]

Codex 用 Rust 实现了完整的 Agent 注册表：

```rust
// 核心结构
struct AgentRegistry {
    agents: HashMap<ThreadId, AgentHandle>,
    parent: Weak<ThreadManager>,  // 弱引用防循环
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

### 生命周期

```
spawn_agent(config, initial_op)
    → ThreadId
    → 注册到 registry
    ↓
monitor(thread_id)
    → AgentStatus（轮询或事件通知）
    ↓
cleanup(thread_id)
    → 释放资源
    → 从 registry 移除
```

### Agent 间通信

```rust
// 通过 Op 枚举传递消息
Op::InterAgentCommunication {
    communication: AgentMessage {
        from: ThreadId,      // 发送者
        to: ThreadId,        // 接收者
        content: String,     // 消息内容
        metadata: HashMap<String, Value>,
    }
}
```

**关键设计决策**：
- 消息通过 channel 传递，非共享内存
- 父 Agent 持有子 Agent 的强引用，反向是弱引用
- 子 Agent 崩溃不会导致父 Agent 崩溃（错误隔离）

---

## OpenCode：Session 继承模式 [OC]

OpenCode 用 Go 的 Session 机制实现父子关系：

```go
type Session struct {
    ID               string
    ParentSessionID  string   // 指向父 Session，空表示根
    Title            string
    PromptTokens     int64
    CompletionTokens int64
    Cost             float64  // 自动汇总到父
    CreatedAt        time.Time
    UpdatedAt        time.Time
}
```

### AgentTool 创建子 Session

```go
func (t *AgentTool) Run(ctx context.Context, call ToolCall) (ToolResponse, error) {
    // 创建子 Session
    childSession := t.sessionService.Create(ctx, CreateSessionParams{
        ParentSessionID: currentSessionID(ctx),
        Title:           call.Description,
    })
    
    // 在子 Session 中运行 Agent
    result := t.agent.Run(ctx, childSession.ID, call.Prompt)
    
    // 成本自动汇总到父 Session
    return ToolResponse{Content: result}, nil
}
```

**关键设计决策**：
- Session 是持久化的（SQLite），重启后可恢复
- 成本（token 数、费用）自动向上汇总
- 子 Session 完成后不删除，保留审计轨迹

---

## Claude Code：异步 Agent 进度追踪 [CC]

Claude Code 的 Agent 管理更轻量，专注于异步进度追踪：

```typescript
interface AgentProgress {
    agentId: string;
    description: string;
    status: "running" | "completed" | "failed";
    progress?: string;      // 当前步骤描述
    startedAt: number;
    completedAt?: number;
}
```

### 生命周期

```
registerAsyncAgent(agentId, {description, prompt, model})
    ↓
updateAgentProgress(agentId, progress)  // 流式更新
    ↓
completeAgentTask(agentId, result)      // 完成
    ↓
enqueueAgentNotification()              // 通知主循环
    ↓
removeAgent(agentId)                    // 清理
```

### TUI 进度显示

```
底部状态栏：
[Agent 1: 搜索 API 用法...] [Agent 2: ✓ 完成] [Agent 3: 运行测试...]
```

**关键设计决策**：
- 不持久化 Agent 状态（会话内有效）
- 通知机制：Agent 完成后入队，主循环消费
- 进度是纯 UI 概念，不影响 Agent 执行逻辑

---

## 模式对比

| 维度 | Codex (Rust) | OpenCode (Go) | Claude Code (TS) |
|------|-------------|---------------|-----------------|
| 注册表 | HashMap + 强/弱引用 | Session 表 (SQLite) | 内存 Map |
| 持久化 | 否 | 是（SQLite） | 否 |
| 父子关系 | ThreadId 引用 | ParentSessionID | agentId 标识 |
| 通信方式 | Op 消息 + channel | PubSub 事件 | 通知队列 |
| 成本追踪 | 无 | 自动汇总到父 | 无 |
| 错误隔离 | 弱引用防级联 | Session 独立 | try-catch 隔离 |
| 复杂度 | 高（完整系统） | 中（Session 继承） | 低（最小实现） |

## 选型建议

```
你的 Agent 系统需要什么级别的管理？
│
├─ 只需要并行执行几个子任务
│  → Claude Code 模式：内存 Map + 通知队列
│
├─ 需要跨会话恢复、成本追踪
│  → OpenCode 模式：Session 表 + 自动汇总
│
└─ 需要复杂的 Agent 间通信、错误隔离
   → Codex 模式：完整注册表 + channel 通信
```
