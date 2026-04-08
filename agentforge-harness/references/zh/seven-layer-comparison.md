# 7 层模型：5 Agent 分层实现对照

> 来源：研究报告 Chapter 3.2（L145-L155）
> 同一个 7 层模型，5 个 Agent 的具体实现差异

| 层级 | Claude Code | Codex CLI | OpenCode | Aider | Cline |
|------|------------|-----------|----------|-------|-------|
| **L1 上下文** | 多层 CLAUDE.md + auto-memory + prompt cache | AGENTS.md + config.toml | .opencode.json + contextPaths | Repo Map (AST) | 模块化 prompt variants |
| **L2 工具** | 40+ tools, async generator | Rust handlers + Starlark policy | 15+ Go tools + MCP | 命令式 (无 schema) | 36+ proto-defined tools |
| **L3 状态** | transcript.jsonl + session memory | Event sourcing + turn history | SQLite + PubSub | Git commits + chat history | Disk persistence + context tracker |
| **L4 约束** | Permission rules + deny lists | Seatbelt/Landlock/bwrap sandbox | Permission request channel | 无（直接文件系统） | Auto-approve patterns |
| **L5 验证** | Pre-commit hooks + stop hooks | execpolicy + guardian AI review | LSP diagnostics | 反射循环 (max 3) | 循环检测 |
| **L6 熵管理** | Auto-compact + file state cache | 无明确机制 | Auto-compact at 95% | Chat history summarizer | Incremental change tracker |
| **L7 人机交互** | Permission UI + plan mode | Approval dialog (exec/patch/network) | TUI permission dialog | CLI 确认 | Webview 审批 UI |

## 各层的设计模式

- **L1**：Claude Code 的 5 层分级加载最成熟；Aider 的 Repo Map 提供无需搜索的全局视野
- **L2**：Claude Code 工具数最多但有延迟加载优化；Aider 最少（~10）但足够
- **L3**：OpenCode 的 SQLite+PubSub 最持久；Claude Code 的 transcript 最轻量
- **L4**：Codex CLI 的 OS 级沙箱最严格；Aider 无约束（信任本地环境）
- **L5**：Aider 的反射循环（编辑→检查→重试 max 3 次）最优雅
- **L6**：Claude Code 的 fork 子进程压缩最高效；Codex 无此机制
- **L7**：Cline 的 Webview UI 最丰富；Aider 最简（CLI 确认）
