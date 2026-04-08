# 上下文压缩算法参考

> 来源：Claude Code、OpenCode、Aider、Letta 的压缩实现对比

## Claude Code 的 Auto-Compact 算法 [CC]

### 触发条件

```typescript
// src/services/compact/autoCompact.ts
function calculateTokenWarningState(usage, model) {
  const percentLeft = 1 - (usage.total / model.contextWindow);
  return {
    isAboveWarningThreshold: percentLeft < 0.2,     // 20% 剩余
    isAboveErrorThreshold: percentLeft < 0.1,        // 10% 剩余
    isAboveAutoCompactThreshold: percentLeft < 0.05, // 5% 剩余
  };
}
```

### 压缩流程

```
1. 按 API 轮次分组消息 (grouping.ts)
   → 每个"轮次" = 一次 API 调用 + 工具执行 + 结果

2. Fork 子进程做摘要 (compact.ts)
   → 隔离上下文，避免阻塞主循环
   → 用 LLM 生成摘要

3. 工具使用单独摘要 (toolUseSummaryGenerator.ts)
   → 长工具输出（如大文件内容）有独立压缩逻辑
   → 保留关键信息，丢弃冗余

4. 插入压缩边界标记 (createCompactBoundaryMessage)
   → 让后续消息知道"这里之前被压缩了"

5. 触发 POST_COMPACT hook
   → 更新文件缓存
   → 刷新会话状态
```

## OpenCode 的 Summarize 算法 [OC]

```go
func (a *agent) Summarize(ctx, sessionID) error {
    // 1. 获取所有历史消息
    messages := a.messageService.List(ctx, sessionID)
    
    // 2. 用专用 summarizer agent（可以是更便宜的模型）
    summary := a.summarizeProvider.SendMessages(ctx, messages, nil)
    
    // 3. 创建摘要消息
    summaryMsg := a.messageService.Create(ctx, {
        SessionID: sessionID,
        Role:      "assistant",
        Content:   summary,
    })
    
    // 4. 设置 session 的 SummaryMessageID
    a.sessionService.Update(ctx, sessionID, {
        SummaryMessageID: summaryMsg.ID,
    })
    
    // 5. 后续 Run() 从摘要点开始
    // 只加载 summary + 之后的消息
}
```

## Letta 的分层压缩 [LT]

```
核心记忆（Context Window 内）
    ↓ 溢出时
摘要记忆（压缩后保留）
    ↓ 进一步溢出
归档记忆（长期存储，搜索访问）
    ↓
回忆记忆（近期上下文，加权检索）
```

**Heartbeat 机制**：Agent 可以主动请求继续思考（`REQ_HEARTBEAT_MESSAGE`），不需要用户触发。这让 Agent 可以在单轮中做更深的推理。

## 压缩质量的关键指标

1. **信息保留率**：压缩后能否回答关于历史的问题
2. **Token 压缩比**：压缩前/后的 token 数量比
3. **延迟**：压缩本身的耗时（不应阻塞用户交互）
4. **幂等性**：对同一内容多次压缩结果是否一致

## 选型建议

| 场景 | 推荐方案 |
|------|---------|
| 短会话 (< 20 轮) | 不需要压缩 |
| 中等会话 (20-100 轮) | Claude Code 式 auto-compact |
| 长会话 (100+ 轮) | OpenCode 式 session 分支 + summary |
| 持久 Agent（跨天/周） | Letta 式分层记忆 |
