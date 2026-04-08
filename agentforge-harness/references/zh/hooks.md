# Claude Code Hooks Reference

Hooks are deterministic scripts that execute at specific points in Claude Code's lifecycle. Unlike prompt instructions (which are requests the model may interpret flexibly), hooks fire every time, without exception.

## Correct JSON Format

Every hook uses this nested structure. Getting this wrong will silently fail:

```json
{
  "hooks": {
    "EventName": [
      {
        "matcher": "ToolNameRegex",
        "hooks": [
          {
            "type": "command",
            "command": "your-command-here"
          }
        ]
      }
    ]
  }
}
```

Key structural rules:
- `matcher` is a **regex matching tool names** (case-sensitive): `Bash`, `Write`, `Edit`, `MultiEdit`, `Read`, `Glob`, `Grep`, `Agent`
- Use `|` for multiple tools: `"Edit|Write|MultiEdit"`
- Use `"*"`, `""`, or omit matcher to match all tools
- `hooks` is an **array** — you can chain multiple commands per matcher
- `type` must be specified — most common is `"command"`

## Exit Codes (Critical)

- **Exit 0**: Success. Execution continues. Stdout shown in transcript mode (Ctrl-R) but NOT seen by Claude.
- **Exit 1**: Warning only. Logged but does NOT block the action.
- **Exit 2**: **Blocks the action.** Stderr is fed back to Claude as remediation instructions.

For PreToolUse security hooks, you MUST use `exit 2` to actually block. `exit 1` only warns.

## Data Flow

Hooks receive JSON via **stdin** — this is the primary and most reliable data source. Some environment variables are also available but stdin should be preferred for tool input data:

- `$CLAUDE_PROJECT_DIR` — absolute path to project root (reliable)
- `$CLAUDE_TOOL_INPUT_FILE_PATH` — file path for file operations (available in PostToolUse for Write/Edit/MultiEdit)

**Important:** Environment variables like `$CLAUDE_TOOL_INPUT` and `$CLAUDE_FILE_PATHS` may be empty in some Claude Code versions. Always prefer reading stdin JSON for tool input data.

Stdin JSON example for PreToolUse:
```json
{
  "session_id": "abc123",
  "tool_name": "Bash",
  "tool_input": {"command": "git commit -m 'fix bug'"},
  "cwd": "/Users/you/project",
  "hook_event_name": "PreToolUse"
}
```

To read stdin in bash: `INPUT=$(cat); CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty')`

**Prerequisite:** Hooks that parse stdin JSON require `jq`. Install with `brew install jq` (macOS) or `apt install jq` (Linux).

## Key Lifecycle Events

| Event | When | Common use |
|-------|------|------------|
| **Setup** | Claude Code CLI 启动时 | 环境检测、依赖检查 |
| **SessionStart** | Session start/resume/clear/compact | Inject context, set env vars |
| **SessionEnd** | 会话结束 | 清理临时文件、保存状态 |
| **UserPromptSubmit** | Before prompt reaches Claude | Validate/enhance prompts |
| **PreToolUse** | Before a tool executes | Block dangerous operations |
| **PostToolUse** | After a tool succeeds | Auto-format, lint, log |
| **PostToolUseFailure** | After a tool fails | 重试策略、错误上报、降级处理 |
| **Notification** | 通知事件 | 自定义通知处理 |
| **PreCompact** | Before auto-compact | 保存关键上下文到文件 |
| **PostCompact** | After auto-compact | 重新加载缓存、刷新文件状态 |
| **SubagentStart** | Subagent spawned | 注入子 Agent 规则、设置权限 |
| **SubagentStop** | Subagent completes | Validate subagent work |
| **Stop** | Agent considers itself done | Verify build/tests pass |
| **StopFailure** | Stop hook 执行失败 | 错误处理、告警 |
| **PermissionRequest** | 权限申请 | 自定义权限决策（approve/block） |
| **PermissionDenied** | 权限被拒绝 | 记录审计日志 |
| **TeammateIdle** | 队友 Agent 空闲 | 任务再分配 |
| **TaskCreated** | 任务创建 | 任务追踪、日志 |
| **TaskCompleted** | 任务完成 | 验证、通知 |
| **Elicitation** | MCP 引出事件 | 自定义引出处理 |
| **ElicitationResult** | 引出结果 | 结果验证 |
| **ConfigChange** | 配置变更 | 重新加载、验证 |
| **WorktreeCreate** | Worktree 创建 | 初始化隔离环境 |
| **WorktreeRemove** | Worktree 移除 | 清理、合并结果 |
| **InstructionsLoaded** | CLAUDE.md 等指令文件加载后 | 校验指令完整性、注入动态规则 |
| **CwdChanged** | 工作目录切换 | 加载目录级 CLAUDE.md、更新上下文 |
| **FileChanged** | 文件被外部修改 | 自动重新加载、触发增量编译 |

> 总计 27 个 Hook 事件（源码验证：`coreTypes.ts:25-53`）。Setup 和 SessionStart 为 ALWAYS_EMITTED（不依赖配置）。

SessionStart and UserPromptSubmit stdout is injected into Claude's context automatically.

## Production-Ready Recipes

### Auto-format after file writes

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "npx prettier --write \"$CLAUDE_TOOL_INPUT_FILE_PATH\" 2>/dev/null || true"
          }
        ]
      }
    ]
  }
}
```

### Block dangerous commands

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "INPUT=$(cat); echo \"$INPUT\" | jq -r '.tool_input.command' | grep -qE 'rm -rf|DROP TABLE|--force push' && { echo 'Blocked: use a safer alternative.' >&2; exit 2; } || exit 0"
          }
        ]
      }
    ]
  }
}
```

### Require tests before git commit

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "INPUT=$(cat); CMD=$(echo \"$INPUT\" | jq -r '.tool_input.command // empty'); echo \"$CMD\" | grep -q 'git commit' && { RESULT=$(npm test 2>&1); RC=$?; echo \"$RESULT\" | tail -20; [ $RC -ne 0 ] && exit 2 || exit 0; } || exit 0"
          }
        ]
      }
    ]
  }
}
```

### Verify build on Stop (with infinite loop prevention)

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "INPUT=$(cat); [ \"$(echo $INPUT | jq -r '.stop_hook_active')\" = 'true' ] && exit 0; RESULT=$(npm run build 2>&1); RC=$?; echo \"$RESULT\" | tail -10; [ $RC -ne 0 ] && exit 2 || exit 0"
          }
        ]
      }
    ]
  }
}
```

**Critical:** Without the `stop_hook_active` check, Stop hooks with `exit 2` create infinite loops. Always gate on this field.

### Inject context at session start

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "echo '{\"additionalContext\": \"Branch: '$(git branch --show-current)'. Last commit: '$(git log --oneline -1)'\"}'"
          }
        ]
      }
    ]
  }
}
```

## Commands by Tech Stack

Substitute these into the recipes above based on your project:

| Stack | Test | Format | Build / Type Check |
|-------|------|--------|-------------------|
| Node.js/TS | `npm test` | `npx prettier --write` | `npm run build` |
| Python | `python -m pytest --tb=short` | `python -m black` | `python -m mypy src/` |
| Rust | `cargo test` | `cargo fmt` | `cargo build` |
| Go | `go test ./...` | `gofmt -w` | `go build ./...` |

## Configuration Locations

| File | Scope | Git tracked? |
|------|-------|-------------|
| `~/.claude/settings.json` | All projects (personal) | No |
| `.claude/settings.json` | This project (team) | Yes |
| `.claude/settings.local.json` | This project (personal) | No |

Team standards go in `.claude/settings.json`. Personal preferences in `.local.json`.

## Best Practices

- **Use script files for complex hooks.** Inline one-liners are hard to debug. Put logic in `.claude/hooks/script-name.sh` and reference it: `{"type": "command", "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/pre-commit-check.sh"}`
- **Prefer stdin JSON over environment variables.** Some env vars (`$CLAUDE_FILE_PATHS`, `$CLAUDE_TOOL_INPUT`) may be empty in certain Claude Code versions. Stdin JSON is the most reliable data source. `$CLAUDE_PROJECT_DIR` and `$CLAUDE_TOOL_INPUT_FILE_PATH` are reliable.
- **Use exit 2, not exit 1, for blocking.** Exit 1 only warns.
- **Write errors to stderr.** Stdout goes to transcript; stderr goes to Claude as remediation instructions.
- **Check `stop_hook_active` in Stop hooks.** Prevents infinite loops.
- **Keep hooks under 200ms.** Slow hooks degrade the experience.
- **Hooks fire for subagents too.** Verify with `/hooks` command.
- **Only add test hooks if tests exist.** A test hook on a project with no test suite blocks every commit.
- **Test manually:** `echo '{"tool_name":"Bash","tool_input":{"command":"ls"}}' | ./hook.sh; echo $?`
