# Agent Loop 范式深度参考

> 来源：9 个生产级 Agent 源码逆向工程（2026-04-06）
> 主文档标注：[CC]=Claude Code, [CX]=Codex CLI, [OC]=OpenCode, [AD]=Aider

## 范式一：Async Generator Loop 实现细节

### Claude Code 的完整流程 [CC]

```
src/query.ts (~5000 行)

用户输入
    ↓
[processUserInput] → 规范化消息 + 附件处理
    ↓
[fetchSystemPromptParts] → 加载 CLAUDE.md, 记忆, 上下文
    ↓
[queryModelWithStreaming] → API 调用
    ├─ System prompt (context.ts)
    ├─ Message history (normalized)
    ├─ Tools (assembleToolPool 动态组装)
    └─ Betas (thinking, JSON output 等)
    ↓
[Stream Processing]
    ├─ Content delta 累积
    ├─ Tool use block 流式解析 (StreamingToolExecutor)
    ├─ Hook 执行 (postSampling, stopHooks)
    └─ 进度反馈
    ↓
[Tool Execution] → runTools()
    ├─ 按并发安全性分区
    ├─ 串行：状态变更工具
    ├─ 并行：只读工具
    └─ 结果累积到 messages
    ↓
[Token Budget Check]
    ├─ Auto-compact（超阈值时 fork 子进程）
    ├─ Continuation nudge（接近限制时）
    └─ Terminal state（收益递减时）
    ↓
[Message Persistence] → sessionStorage
```

### 关键代码模式

```typescript
// 工具执行分区（核心模式）
async function runTools(toolUses, context) {
  const { concurrent, sequential } = partition(
    toolUses,
    (t) => t.isConcurrencySafe()
  );
  
  // 并行执行只读工具
  const concurrentResults = await Promise.all(
    concurrent.map(t => executeToolUse(t, context))
  );
  
  // 串行执行状态变更工具
  for (const tool of sequential) {
    await executeToolUse(tool, context);
  }
}
```

## 范式二：Submission-Handler 实现细节

### Codex CLI 的 Op 枚举 [CX]

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
    // ...共 32 个操作类型
}
```

### TurnContext 结构

每次提交获得独立的 TurnContext（Arc 包装）：
- `cwd`: 工作目录
- `approval_policy`: AskForApproval 设置
- `sandbox_policy`: SandboxPolicy 约束
- `model`: 模型选择
- `collaboration_mode`: 协作模式

## 范式三：PubSub Event Loop 实现细节

### OpenCode 的 PubSub 架构 [OC]

```go
// 泛型 PubSub Broker
type Broker[T any] struct {
    subs map[chan Event[T]]struct{}
}

// 实现者：Session, Message, Permission, Agent 服务
type Subscriber[T any] interface {
    Subscribe(context.Context) <-chan Event[T]
}
```

### Agent 事件类型

```go
type AgentEvent struct {
    Type    AgentEventType  // Error, Response, Summarize
    Message Message
    Usage   TokenUsage
}
```

### Context Value 注入模式

```go
// 工具执行前注入上下文
ctx = context.WithValue(ctx, tools.SessionIDContextKey, sessionID)
ctx = context.WithValue(ctx, tools.MessageIDContextKey, assistantMsg.ID)
```

## 范式四：反射式链实现细节

### Aider 的多态编辑系统 [AD]

```python
# 编辑格式作为类的多态属性
class EditBlockCoder(Coder):   edit_format = "diff"
class UnifiedDiffCoder(Coder): edit_format = "udiff"
class PatchCoder(Coder):       edit_format = "patch"
class WholeFileCoder(Coder):   edit_format = "wholefile"
class ArchitectCoder(Coder):   edit_format = "architect"

# 运行时切换
new_coder = Coder.create(from_coder=existing_coder, edit_format="architect")
```

### Architect 模式（两阶段）

1. **架构模型**（强模型）做高层规划
2. **编辑模型**（可以是弱模型）执行具体修改

这种"规划-执行"分离模式在 Cline 中也有体现（Plan Mode / Act Mode）。

## 范式选型的隐藏约束

| 约束 | Async Generator | Submission-Handler | PubSub | 反射链 |
|------|----------------|-------------------|--------|--------|
| 最小实现行数 | ~500 | ~2000 | ~800 | ~300 |
| 流式UI支持 | 原生 | 需要 Event 转换 | 需要订阅 | 需要回调 |
| 错误恢复 | try/finally | match arm | defer | try/except |
| 可中断性 | yield 点中断 | channel close | context cancel | 循环 break |
| 测试难度 | 中（mock generator） | 低（纯函数） | 中（mock channel） | 低 |
| 子 Agent 隔离 | fork 进程 | 新 ThreadId | 新 Session | 新 Coder 实例 |
