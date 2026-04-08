# 7-Layer Model: 5 Agent Implementation Comparison

> Source: Research Report Chapter 3.2 (L145-L155)
> Same 7-layer model — specific implementation differences across 5 agents

| Layer | Claude Code | Codex CLI | OpenCode | Aider | Cline |
|-------|------------|-----------|----------|-------|-------|
| **L1 Context** | Multi-layer CLAUDE.md + auto-memory + prompt cache | AGENTS.md + config.toml | .opencode.json + contextPaths | Repo Map (AST) | Modular prompt variants |
| **L2 Tools** | 40+ tools, async generator | Rust handlers + Starlark policy | 15+ Go tools + MCP | Imperative (no schema) | 36+ proto-defined tools |
| **L3 State** | transcript.jsonl + session memory | Event sourcing + turn history | SQLite + PubSub | Git commits + chat history | Disk persistence + context tracker |
| **L4 Constraints** | Permission rules + deny lists | Seatbelt/Landlock/bwrap sandbox | Permission request channel | None (direct filesystem) | Auto-approve patterns |
| **L5 Verification** | Pre-commit hooks + stop hooks | execpolicy + guardian AI review | LSP diagnostics | Reflective loop (max 3) | Loop detection |
| **L6 Entropy Management** | Auto-compact + file state cache | No explicit mechanism | Auto-compact at 95% | Chat history summarizer | Incremental change tracker |
| **L7 Human-in-the-Loop** | Permission UI + plan mode | Approval dialog (exec/patch/network) | TUI permission dialog | CLI confirmation | Webview approval UI |

## Design Patterns by Layer

- **L1**: Claude Code's 5-layer hierarchical loading is most mature; Aider's Repo Map provides global view without searching
- **L2**: Claude Code has the most tools but with lazy-loading optimization; Aider has the fewest (~10) but sufficient
- **L3**: OpenCode's SQLite+PubSub is most persistent; Claude Code's transcript is most lightweight
- **L4**: Codex CLI's OS-level sandbox is most strict; Aider has no constraints (trusts local environment)
- **L5**: Aider's reflective loop (edit→check→retry max 3) is most elegant
- **L6**: Claude Code's fork subprocess compression is most efficient; Codex has no such mechanism
- **L7**: Cline's Webview UI is richest; Aider is simplest (CLI confirmation)
