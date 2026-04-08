# Prompt Cache: A Practical Guide

> Source: Claude Code `src/services/api/claude.ts` cache implementation

## How It Works

The Anthropic API caches identical system prompt prefixes server-side.

| TTL Option | Write Cost | Read Cost | Use Case |
|-----------|------------|------------|----------|
| 5 minutes (default) | 1× normal | 0.1× normal | Intra-session reuse; stable short-term knowledge bases |
| 1 hour (`"ttl": "1h"`, added 2025) | 2× normal | 0.1× normal | Cross-request reuse; very large system prompts |

- **Max breakpoints**: 4 per message
- **Min token threshold**: Opus 4096 / Sonnet 2048 / others 1024 (below threshold = no caching)
- **Workspace isolation**: Different API keys have isolated caches (enforced 2026-02-05)

```json
// Default 5-minute TTL
{"type": "ephemeral"}

// 1-hour TTL (suited for large knowledge bases and long-stable system prompts)
{"type": "ephemeral", "ttl": "1h"}
```

> verified: 2026-04-08 (Anthropic official docs + SDK changelog)

## Static/Dynamic Separation Architecture [CC]

```
System Prompt Layout:

┌──────────────────────────────┐
│  [STATIC ZONE]               │ ← cache_control: "ephemeral"
│  • Identity directives       │
│  • Behavioral rules          │
│  • Tool definitions (core)   │
│  • CLAUDE.md contents         │
│  • Coding conventions         │
├──────────────────────────────┤ ← SYSTEM_PROMPT_DYNAMIC_BOUNDARY
│  [DYNAMIC ZONE]              │ ← Not cached; recalculated every turn
│  • Git status                │
│  • MCP tool list (mutable)   │
│  • Current session context    │
│  • Task notifications         │
└──────────────────────────────┘
```

## Cache Invalidation Triggers

The following operations cause a cache miss:
1. **MCP server connect/disconnect** — tool list changes
2. **CLAUDE.md modification** — static zone content changes
3. **Model switch** — caches are not shared across models
4. **Tool enable/disable** — tool definition list changes

Claude Code has a `promptCacheBreakDetection` module that specifically monitors these conditions [CC].

## Cost Analysis

Assuming a 10,000-token system prompt (Sonnet 4.6 pricing) and 50 turns:

| Scenario | Turn 1 Cost | Subsequent Turns | 50 Turns Total |
|----------|-------------|-------------------|----------------|
| No cache | $0.030 | $0.030 | $1.500 |
| 5-min TTL cache | $0.0375 | $0.003 | $0.184 |
| 1-hour TTL cache | $0.060 | $0.003 | $0.207 |
| **5-min savings** | -25% | **90%** | **87.7%** |
| **1-hour savings** | -100% | **90%** | **86.2%** |

> Note: The 1-hour TTL has higher write costs (×2 vs ×1.25), but for cross-session reuse (multiple daily requests to the same large system prompt), it offers better overall value.

## Implementation Checklist

- [ ] System prompt has a clear static/dynamic boundary
- [ ] Static zone content remains unchanged during the session
- [ ] Added `cache_control: "ephemeral"` header
- [ ] MCP tool definitions are in the dynamic zone
- [ ] Monitoring cache hit rate (via `cacheReadTokens` field)
