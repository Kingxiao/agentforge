# Context Compaction Algorithms Reference

> Sources: Claude Code, OpenCode, Aider, and Letta — a comparison of compaction implementations

## Claude Code's Auto-Compact Algorithm [CC]

### Trigger Conditions

```typescript
// src/services/compact/autoCompact.ts
function calculateTokenWarningState(usage, model) {
  const percentLeft = 1 - (usage.total / model.contextWindow);
  return {
    isAboveWarningThreshold: percentLeft < 0.2,     // 20% remaining
    isAboveErrorThreshold: percentLeft < 0.1,        // 10% remaining
    isAboveAutoCompactThreshold: percentLeft < 0.05, // 5% remaining
  };
}
```

### Compression Flow

```
1. Group messages by API turn (grouping.ts)
   → One "turn" = one API call + tool execution + result

2. Fork a child process for summarization (compact.ts)
   → Isolates the context, avoids blocking the main loop
   → Uses an LLM to generate the summary

3. Tool usage gets a separate summary (toolUseSummaryGenerator.ts)
   → Long tool outputs (e.g., large file contents) have independent compaction logic
   → Preserves key information, discards redundancy

4. Insert compact boundary markers (createCompactBoundaryMessage)
   → Lets subsequent messages know "this was compressed"

5. Trigger POST_COMPACT hook
   → Update file cache
   → Refresh session state
```

## OpenCode's Summarize Algorithm [OC]

```go
func (a *agent) Summarize(ctx, sessionID) error {
    // 1. Fetch all historical messages
    messages := a.messageService.List(ctx, sessionID)

    // 2. Send to a dedicated summarizer agent (can use a cheaper model)
    summary := a.summarizeProvider.SendMessages(ctx, messages, nil)

    // 3. Create a summary message
    summaryMsg := a.messageService.Create(ctx, {
        SessionID: sessionID,
        Role:      "assistant",
        Content:   summary,
    })

    // 4. Set the session's SummaryMessageID
    a.sessionService.Update(ctx, sessionID, {
        SummaryMessageID: summaryMsg.ID,
    })

    // 5. Subsequent Run() calls start from the summary point
    // Only loads: summary + messages after it
}
```

## Letta's Layered Compression [LT]

```
Core Memory (within Context Window)
    ↓ When overflow occurs
Summary Memory (preserved after compression)
    ↓ On further overflow
Archived Memory (long-term storage, searchable)
    ↓
Recalled Memory (recent context, weighted retrieval)
```

**Heartbeat Mechanism**: An agent can proactively request continued thinking (`REQ_HEARTBEAT_MESSAGE`) without user intervention. This enables the agent to engage in deeper reasoning within a single turn.

## Key Metrics for Compression Quality

1. **Information Retention Rate**: Whether the compressed context can still answer questions about history
2. **Token Compression Ratio**: Token count before vs. after compression
3. **Latency**: How long compression itself takes (should not block user interaction)
4. **Idempotency**: Whether compressing the same content multiple times yields consistent results

## Selection Guidance

| Scenario | Recommended Approach |
|----------|---------------------|
| Short sessions (< 20 turns) | No compression needed |
| Medium sessions (20-100 turns) | Claude Code-style auto-compact |
| Long sessions (100+ turns) | OpenCode-style session branching + summary |
| Persistent agents (cross-day/week) | Letta-style tiered memory |
