# Phase Acceptance Criteria + Effort Estimates + Technology Quick Reference

> Source: Research Report Chapter 13 (L942-L097)
> Definition of "when is it done" + specific directory structure blueprints for each phase

## 6-Phase Acceptance Criteria

| Phase | Effort Estimate | Acceptance Criteria |
|-------|----------------|---------------------|
| **Phase 1: Minimum Viable Agent** | 1-2 days | Agent independently handles simple bug fixes (read code → locate → modify → verify) |
| **Phase 2: Context Engineering** | 3-5 days | Still correctly references early context after 50+ turns in a long session |
| **Phase 3: Security & Permissions** | 3-5 days | Cannot execute dangerous commands via prompt injection |
| **Phase 4: Tool Ecosystem Expansion** | 5-7 days | Connects external services (database, APIs) via MCP and uses them correctly |
| **Phase 5: Multi-Agent & Memory** | 5-7 days | New session automatically resumes last unfinished task progress |
| **Phase 6: UI & Productization** | 5-7 days | Non-technical users complete first use within 3 minutes |

**Total**: 20-33 days (1 person, full-time)

## Directory Structure Blueprint Per Phase

### Phase 1: Minimum Viable Agent
```
├── agent_loop.rs/go/ts    # Main loop (LLM → Tool → LLM)
├── provider.rs/go/ts      # LLM API client
├── tools/
│   ├── bash.rs            # Shell execution
│   ├── read.rs            # File read
│   └── write.rs           # File write
└── main.rs                # Entry point
```

### Phase 2: Context Engineering
```
New additions:
├── context/
│   ├── system_prompt.rs   # Layered system prompt
│   ├── claude_md.rs       # CLAUDE.md loader
│   └── compact.rs         # Context compaction
├── config/
│   └── config.rs          # Configuration system
└── tools/
    ├── glob.rs            # File search
    └── grep.rs            # Content search
```

### Phase 3: Security & Permissions
```
New additions:
├── permissions/
│   ├── rules.rs           # Permission rules engine
│   ├── approval.rs        # Approval workflow
│   └── deny_tracking.rs   # Denial logging
├── sandbox/
│   └── policy.rs          # Execution policy
└── hooks/
    ├── pre_tool.rs        # Pre-tool execution hook
    └── post_tool.rs       # Post-tool execution hook
```

### Phase 4: Tool Ecosystem Expansion
```
New additions:
├── tools/
│   ├── edit.rs            # Precise replacement edit
│   ├── web_fetch.rs       # Web fetch
│   ├── web_search.rs      # Web search
│   ├── lsp.rs             # LSP integration
│   └── agent.rs           # Sub-agent tool
├── mcp/
│   ├── client.rs          # MCP client
│   └── registry.rs        # MCP tool registry
└── tools/
    └── orchestrator.rs    # Tool concurrency orchestration
```

### Phase 5: Multi-Agent & Memory
```
New additions:
├── agents/
│   ├── spawner.rs         # Agent spawner
│   ├── registry.rs        # Agent registry
│   └── communication.rs   # Inter-Agent communication
├── memory/
│   ├── auto_memory.rs     # Automatic memory extraction
│   ├── memory_file.rs     # Memory file management
│   └── index.rs           # Memory index
└── session/
    ├── session.rs         # Session management
    ├── history.rs         # History persistence
    └── progress.rs        # Progress tracking
```

### Phase 6: UI & Productization
```
New additions:
├── tui/
│   ├── app.rs             # TUI framework
│   ├── chat.rs            # Chat interface
│   ├── permissions.rs     # Permission dialog
│   └── status.rs          # Status bar
├── cli/
│   ├── commands.rs        # Slash commands
│   └── streaming.rs       # Streaming output
└── bridge/
    └── api.rs             # IDE integration API
```

## Technology Quick Reference

| Decision Point | Recommended Approach | Rationale |
|---------------|---------------------|-----------|
| **Language** | Rust or Go | Performance + type safety + concurrency; TS also works but higher runtime overhead |
| **LLM SDK** | Direct HTTP calls | SDK versions update too fast; direct calls give more control |
| **TUI Framework** | ratatui (Rust) / Bubble Tea (Go) / Ink (TS) | Best option in each ecosystem |
| **Database** | SQLite (WAL mode) | Embedded, zero-config, fast enough |
| **Config Format** | TOML | Human-readable, clear hierarchy, comment-friendly |
| **Tool Schema** | JSON Schema | Industry standard, all LLM APIs support it |
| **IPC** | JSON-RPC over stdio | Simple, cross-platform, dependency-free |

## Key Decision Notes

- **Direct HTTP calls over LLM SDK**: Among 9 Agents surveyed, Codex CLI and OpenCode both chose to implement their own HTTP clients rather than use official SDKs. Reason: SDK versions update weekly while Agent release cycles are monthly — frequent breaking changes are a maintenance nightmare.
- **SQLite WAL mode**: OpenCode uses SQLite for session persistence (three-table structure), while Claude Code uses JSON files. SQLite has an edge when you need to query historical sessions.
- **TOML > YAML > JSON**: Codex CLI uses TOML for configuration, citing comment support and no indentation sensitivity issues like YAML.
