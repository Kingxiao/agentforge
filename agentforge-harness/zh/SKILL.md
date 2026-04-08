---
name: agentforge-harness
description: AgentForge Phase 6 - Harness 工程。CLAUDE.md/AGENTS.md 编写、Hook 配置、Agent 失败诊断、架构约束、验证循环、团队协作。agentforge 系列成员，原 harness-engineering 的正式继任。当用户说「harness」「agent reliability」「Hook 配置」「CLAUDE.md」「agent 老犯同一个错」时触发。
triggers:
  - harness
  - agent reliability
  - Hook 配置
  - CLAUDE.md
  - agent 老犯同一个错
  - agent failure
  - hashimoto loop
metadata:
  version: "2.0.0"
  last_updated: "2026-04-06"
  category: "agent-engineering"
---

> 上一步：`/agentforge-security` | 下一步：`/agentforge-multiagent` | 系列入口：`/agentforge`

# Harness Engineering

A discipline for designing constraints, tools, feedback loops, and environmental infrastructure that make AI coding agents reliable at scale. The core principle: **when an agent fails, engineer a system-level fix so the failure never recurs — don't just retry.**

## First Principles

Five fundamental constraints drive why harnesses exist:

1. **Context windows are finite** — even 200K tokens fill quickly during multi-step tasks. The harness manages what enters and exits context.
2. **Context rots** — model performance degrades as input length grows, even within limits. Every model tested shows this. The harness keeps context lean.
3. **Agents are stateless** — no memory persists between sessions unless the harness provides it. Progress files, git history, and structured artifacts bridge sessions.
4. **Agents hallucinate** — they fabricate APIs, variable names, and function signatures with confidence. The harness provides mechanical verification.
5. **Agents skip verification** — they declare victory with failing tests. The harness forces test-pass before commit.

The evidence is clear: LangChain improved from 52.8% to 66.5% on Terminal Bench 2.0 by changing only the harness, not the model. The model is commodity; the harness is leverage.

## The Hashimoto Loop (Core Methodology)

Every harness improvement follows this cycle:

```
Agent attempts task
       ↓
  Observe failure
       ↓
  Diagnose: "What capability or constraint is missing?"
       ↓
  Choose fix type:
    → Simple behavioral fix → Update CLAUDE.md
    → Complex/recurring fix → Build a tool, hook, or structural test
       ↓
  Verify the fix prevents recurrence
       ↓
  Repeat
```

Each line in a good CLAUDE.md traces to a specific past agent failure. Never add speculative rules.

## Harness Components (Seven Layers)

Read `references/components.md` for detailed implementation of each layer:

1. **Context Engineering** — What the agent sees (CLAUDE.md, progressive disclosure, knowledge architecture)
2. **Tool Orchestration** — What the agent can do (fewer tools = better results; sub-agents for context isolation)
3. **Memory & State** — What persists across sessions (progress files, feature lists, git checkpoints)
4. **Architectural Constraints** — What the agent cannot do (dependency rules, linters, structural tests)
5. **Verification & Feedback** — How the system self-corrects (test-before-commit, back-pressure hooks)
6. **Entropy Management** — Fighting codebase decay (periodic cleanup tasks, documentation consistency)
7. **Human-in-the-Loop** — When humans must intervene (approval workflows, review gates)

## Applying Harness Engineering

### Task: Initialize a New Project Harness

When the user wants to set up harness engineering for a project:

1. **Examine the project** — Read the project structure, tech stack, build/test commands, and any existing configuration. Detect the stack by checking for: `package.json` (Node.js), `Cargo.toml` (Rust), `pyproject.toml` / `requirements.txt` (Python), `go.mod` (Go), `pom.xml` / `build.gradle` (Java). Also check for existing CLAUDE.md, `.claude/` directory, linter configs, and CI files.
2. **Create a minimal CLAUDE.md** at project root following the template below. If one already exists, read it first and improve it rather than replacing — existing rules likely encode hard-won lessons. You can also use `/init` in Claude Code to auto-generate a starter CLAUDE.md.
3. **Set up sub-directory CLAUDE.md files** only where domain-specific rules are needed
4. **Configure hooks** in `.claude/settings.json` for mechanical enforcement. Adapt hook commands to the tech stack detected in step 1 — use the correct test runner, formatter, and build tool. See `references/hooks.md` for Node.js and Python recipes. Only add test-before-commit hooks if the project has a working test suite.
5. **Explain the Hashimoto Loop** — tell the user this is a living document that grows from observed failures

**CLAUDE.md Template (Minimal Start):**

```markdown
# Project Overview
[One sentence: what this project is]

## Tech Stack
[Languages, frameworks, key dependencies]

## Commands
- Build: `[command]`
- Test: `[command]`
- Lint: `[command]`
- Dev server: `[command]`

## Architecture
[2-3 sentences on project structure and key patterns]

## Rules
[Start with 2-3 essential rules only. Add more as agent failures reveal gaps.]

## Known Pitfalls
[Empty at start. Each entry documents a specific failure pattern observed during agent use.]
```

Keep this under 200 lines (ideally under 60 for small projects). Every rule should earn its place through a documented failure.

### Task: Diagnose and Fix Agent Failures

When the user reports that Claude Code keeps making a specific mistake:

1. **Identify the failure pattern** — Ask what went wrong, how often, and in what context
2. **Classify the fix type:**
   - **Behavioral** (agent uses wrong convention, forgets a step) → Add a rule to CLAUDE.md
   - **Mechanical** (agent skips tests, commits broken code) → Add a hook
   - **Structural** (agent creates wrong dependencies, violates architecture) → Add a linter rule or structural test
   - **Context** (agent loses track in long sessions) → Improve progressive disclosure or add sub-directory CLAUDE.md
3. **Implement the fix** using the appropriate mechanism
4. **Verify** by describing a test scenario

### Task: Configure Hooks (Back-Pressure)

Hooks enforce mechanical constraints at specific lifecycle events. Read `references/hooks.md` for the full hook reference.

Common patterns for `.claude/settings.json` (note the nested `hooks` array with `type` — this exact structure is required).

**Adapt commands to your stack.** The example below uses Node.js. For Python, replace `npm test` with `python -m pytest`, `npx prettier` with `python -m black`, and `npm run build` with `python -m mypy src/`. See `references/hooks.md` for Python-specific recipes.

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
        ],
        "description": "Tests must pass before any git commit"
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "npx prettier --write \"$CLAUDE_TOOL_INPUT_FILE_PATH\" 2>/dev/null || true"
          }
        ],
        "description": "Auto-format after file write"
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "INPUT=$(cat); [ \"$(echo $INPUT | jq -r '.stop_hook_active')\" = 'true' ] && exit 0; RESULT=$(npm run build 2>&1); RC=$?; echo \"$RESULT\" | tail -10; [ $RC -ne 0 ] && exit 2 || exit 0"
          }
        ],
        "description": "Build must succeed before agent stops (with loop prevention)"
      }
    ]
  }
}
```

Key format rules: `matcher` matches **tool names** (`Bash`, `Write`, `Edit`, `MultiEdit`), NOT commands like "git commit". Use `exit 2` to block actions (not `exit 1`). Stop hooks MUST check `stop_hook_active` to prevent infinite loops. Hooks that parse stdin require `jq` — install it first (`brew install jq` / `apt install jq`). Read `references/hooks.md` for full details.

The principle: use deterministic tools for what they handle well (formatting, linting, testing). Reserve agent intelligence for judgment and reasoning.

### Task: Optimize Context for Long Sessions

When the user works on complex, multi-step tasks:

1. **Use `/compact` proactively** — Don't wait for context to fill. Compact after completing a logical unit of work.
2. **Use `/clear` between phases** — When switching from planning to implementation, or between unrelated features.
3. **Structure sub-directory CLAUDE.md files** for progressive disclosure:

```
project/
├── CLAUDE.md              # Global: build commands, coding style, architecture overview
├── src/
│   ├── CLAUDE.md          # Source-specific: import conventions, module patterns
│   ├── api/
│   │   └── CLAUDE.md      # API-specific: endpoint patterns, auth handling
│   └── components/
│       └── CLAUDE.md      # Component-specific: naming, prop patterns
└── tests/
    └── CLAUDE.md          # Test-specific: test patterns, mock conventions
```

4. **For multi-session projects**, maintain a progress file. Prefer JSON over Markdown — Anthropic found agents are less likely to accidentally overwrite structured JSON:

```json
{
  "goal": "Build notification system",
  "completed": [
    {"feature": "Auth flow", "commit": "abc123", "status": "done"},
    {"feature": "User profile", "commit": "def456", "status": "done"}
  ],
  "current": {
    "feature": "Notification system",
    "status": "in_progress",
    "done": "API endpoints",
    "next": "Build notification dropdown component"
  },
  "known_issues": [
    "Auth token refresh race condition — see src/auth/refresh.ts:42"
  ]
}
```

### Task: Use Claude Code's Built-in Features

Claude Code provides several harness-relevant features out of the box:

- **`/init`** — Auto-generates a starter CLAUDE.md by analyzing your project
- **`/hooks`** — Read-only browser for inspecting all configured hooks
- **`/compact`** — Manually trigger context compaction to keep sessions lean
- **`/clear`** — Full context reset for switching between unrelated tasks
- **Plan mode (Shift+Tab ×2 or `/plan`)** — Cycle through Edit → Auto-Accept → Plan mode. In plan mode Claude analyzes and plans without making changes until you approve. Use for complex tasks.
- **Custom commands** — Place `.md` files in `.claude/commands/` for project-specific slash commands, or `~/.claude/commands/` for personal ones
- **Sub-agents** — Place `.md` files in `.claude/agents/` to create specialized sub-agents with custom system prompts and tool permissions
- **Settings hierarchy** — `~/.claude/settings.json` (global) → `.claude/settings.json` (team, git-tracked) → `.claude/settings.local.json` (personal, git-ignored)

### Task: Review and Simplify a Harness

When the user wants to audit their existing harness, or after a major model update:

1. **Read the current CLAUDE.md** and all sub-directory CLAUDE.md files
2. **Identify candidates for removal:**
   - Rules the model now follows naturally (test by temporarily removing and observing)
   - Overly specific rules that could be generalized
   - Rules that conflict or duplicate
   - Complex workarounds that newer models handle natively
3. **Apply the Bitter Lesson test:** If the harness has grown more complex over time without the project growing proportionally, it's likely over-engineered
4. **Simplify:** Merge, generalize, or delete rules. A shorter CLAUDE.md with higher-signal rules outperforms a long one

The design principle: **build for deletion.** Every harness component encodes an assumption about model limitations. Those assumptions expire. If your harness keeps getting more complex as models improve, you are over-engineering.

### Task: Design Architectural Constraints

When the user wants to enforce code structure for agent reliability:

1. **Define clear module boundaries** — Which modules can import from which
2. **Encode as rules in CLAUDE.md** with rationale:

```markdown
## Architecture Constraints
- `src/domain/` MUST NOT import from `src/infrastructure/` (domain layer is pure)
- `src/api/` handlers MUST use service layer, never access repository directly
- All database queries MUST go through repository classes in `src/repositories/`

Rationale: Strict layering prevents agents from creating shortcuts that compile but violate separation of concerns.
```

3. **Add structural tests** where possible (e.g., custom lint rules that check import paths)
4. **Write linter error messages as remediation instructions** — The agent reads error messages to self-correct

### Task: Set Up Team Harness Collaboration

When multiple people share a codebase and use Claude Code:

1. **Shared harness lives in git** — `.claude/settings.json` and root `CLAUDE.md` are git-tracked. All team members get the same constraints automatically.
2. **Personal preferences stay local** — `.claude/settings.local.json` (git-ignored) for individual hook tweaks or experimental rules.
3. **Treat CLAUDE.md changes like code changes** — PR review for harness modifications. Each rule change affects every team member's agent behavior.
4. **Onboarding = harness** — A good CLAUDE.md simultaneously teaches the agent AND new team members how the codebase works.

Read `references/advanced.md` for team workflow patterns including PR review templates for harness changes and onboarding checklists.

### Task: Coordinate Multiple AI Coding Tools

When using Claude Code alongside Cursor, Codex, or other agents on the same codebase:

1. **Git as shared memory** — All agents read/write through git. Atomic commits with descriptive messages become the inter-agent communication protocol.
2. **CLAUDE.md / AGENTS.md dual format** — Maintain both files if needed. CLAUDE.md for Claude Code, AGENTS.md for Codex/OpenCode. Keep shared rules in sync.
3. **Divide by scope, not role** — Agent A handles backend module, Agent B handles frontend. Don't have two agents editing the same files.
4. **CI as universal verifier** — The CI pipeline is the one harness component that validates ALL agents' output equally.

Read `references/advanced.md` for multi-agent coordination patterns.

### Task: Apply Harness Thinking Beyond Coding

Harness engineering principles apply to any Claude Code task, not just writing code — research, documentation, data analysis, content creation:

1. **Create task-specific CLAUDE.md files** in project subdirectories for non-coding workflows:

```markdown
# Research Standards
- Search 5+ sources before drawing conclusions
- Cross-verify: any key claim needs 3 independent sources
- Always list sources with URLs
- Flag uncertainty explicitly: "high confidence" vs "tentative"
- Output structure: conclusion first, then evidence, then caveats
```

2. **Use hooks for non-coding verification** — A Stop hook can check that output files exist, that required sections are present, or that word counts meet targets.
3. **Progress files work for any multi-session task** — Not just features, but research phases, document drafts, analysis stages.

Read `references/advanced.md` for non-coding harness templates (research, translation, data analysis, content creation).

### Task: Design AI Product Harness Architecture

When building a product or service that uses AI agents internally:

1. **Input harness** — Validate and structure user input before it reaches the model. Sanitize, classify, route to appropriate processing pipeline.
2. **Execution harness** — Constrain what the agent can do: tool access controls, rate limits, timeout policies, resource budgets.
3. **Output harness** — Verify agent output before returning to user: factual checks, format validation, safety filters, confidence scoring.
4. **Feedback harness** — Capture every failure as structured data. Each user-reported error feeds back into constraint refinement (the Hashimoto Loop at product scale).
5. **Observability harness** — Log every agent action, tool call, and decision point. You cannot improve what you cannot measure.

The same seven layers (context, tools, memory, constraints, verification, entropy management, human-in-the-loop) apply at product scale, just with different implementation surfaces.

Read `references/advanced.md` for AI product harness architecture patterns.

## Self-Evolution: The Skill Improves Itself

This skill practices what it preaches — it applies the Hashimoto Loop to its own content. Claude Code can modify skill files at runtime, and changes take effect immediately via live change detection.

### Task: Record Harness Skill Feedback

When the skill gives guidance that turns out to be wrong, incomplete, or suboptimal, record the feedback so it can drive improvements:

1. **Append to the feedback log** at `scripts/feedback.jsonl` within the skill directory:

```json
{"date": "2026-03-26", "category": "hooks", "description": "PreToolUse hook for git commit also triggers on 'git commit-tree' internal commands, causing false blocks", "fix_applied": "Added word boundary to grep pattern", "file_affected": "references/hooks.md"}
```

2. Categories: `hooks`, `claude-md`, `context`, `architecture`, `diagnostics`, `examples`, `advanced`, `other`

### Task: Evolve the Harness Skill

When the user asks to review and improve this skill, or when accumulated feedback warrants it:

1. **Read the feedback log** — `scripts/feedback.jsonl` within the skill directory
2. **Identify patterns** — Recurring categories indicate systemic gaps
3. **Propose changes** — Show the user what would change and why, before modifying any file
4. **Update the skill files** — After user approval, modify the relevant `.md` files directly. Changes take effect in the current session via live change detection.
5. **Log the evolution** — Append to `scripts/changelog.md`:

```markdown
## [date] — Evolution from feedback
- **Changed:** [what file, what modification]
- **Reason:** [which feedback entries drove this]
- **Verified:** [how the fix was confirmed]
```

Evolution principles:
- **Always get user approval before modifying skill files.** Show a diff or summary of proposed changes.
- **Apply Bitter Lesson to the skill itself.** If a section exists because the model used to need it but no longer does, remove it.
- **Keep the feedback log** — it is the skill's institutional memory, the raw material for future improvements.
- **Run `scripts/evolve.sh`** to see a summary of accumulated feedback and patterns.

## Loop Detection Patterns（循环检测）

Agent 在长任务中可能进入死循环（重复相同操作、ping-pong 交替、输出无变化）。生产级 Agent 的循环检测方案 [v2 研究]：

| Agent | 检测方式 | 阈值 |
|-------|---------|------|
| OpenClaw [OW] | 4 种检测器：签名比较 + 回声检测 + ping-pong + 全局断路器 | 30 次全局上限 |
| Cline [CL] | 签名比较（输出 hash） | 3/5 双阈值 |
| Claude Code [CC] | Compaction 电路断路器 | 连续 3 次压缩失败 |

**设计建议**：至少实现签名比较（最简单有效），复杂系统叠加全局断路器作为兜底。

## Dry-Run 模式（高风险 API 写操作的通用 Harness 模式）

**问题**：Agent 对外部系统执行写操作（GitHub 发 PR、Jira 创建 Issue、发送邮件、部署生产环境）时，一旦执行就不可逆或难以回滚。Layer 3 Policy Engine 能拦截 shell 命令，但拦截不了"合法但后果不可逆的 API 调用"。

**Dry-Run 模式**是对高风险写操作工具的标准 Harness 封装——**先预览、再确认、才执行**。

### 实现模式

```python
class GitHubPRTool(BaseTool):
    def call(self, input: PRInput) -> ToolResult:
        # 构建"将要执行的操作"描述
        preview = self._build_preview(input)
        
        # Dry-run 模式：只展示预览，不执行
        if input.dry_run or self._is_dry_run_context():
            return ToolResult(
                status="dry_run",
                preview=preview,
                message=f"[DRY RUN] 将要执行：\n{preview}\n\n调用时传 dry_run=false 确认执行"
            )
        
        # 实际执行
        return self._execute(input)
    
    def _build_preview(self, input):
        return f"""
        CREATE PR:
          标题: {input.title}
          目标分支: {input.base} ← {input.head}
          文件变更: {len(input.files)} 个文件
          关联 Issue: {input.issue_refs}
        """
```

### 工具接口扩展

在工具接口（`/agentforge-tools` 决策一）中添加 Dry-Run 支持：

| 方法 | 作用 |
|------|------|
| `isDryRunSupported()` | 声明该工具支持 dry-run 预览模式 |
| `dryRun(input)` | 返回"将要执行的操作"的结构化描述，不产生副作用 |
| `isHighRisk()` | 标记高风险工具，Agent 决策层自动添加 dry-run 前置步骤 |

### 在 CLAUDE.md 中声明 Dry-Run 策略

```markdown
## 高风险工具操作规则

以下工具必须先执行 dry_run=true 展示预览，等待用户确认后再执行：
- create_github_pr：创建 PR 不可撤销
- deploy_to_production：生产部署影响所有用户
- send_notification：通知发出无法召回
- delete_resource：删除操作通常不可逆

Dry-run 输出格式：
1. 展示"将要执行"的完整操作描述
2. 列出影响范围（影响了多少用户/文件/数据）
3. 等待明确确认（"确认执行" 或 "取消"）
```

### 与 Layer 3 Policy Engine 的关系

| 机制 | 适用 | 拦截方式 |
|------|------|---------|
| Layer 3 Starlark Policy | Shell 命令 (`rm -rf`, `git push`) | 规则匹配 |
| Dry-Run 模式 | API 写操作（HTTP POST/DELETE/PUT）| 工具层封装，预览后确认 |
| Guardian AI | 语义级风险判断 | LLM 评估意图 |

三者互补，不互斥。高风险 API 工具 = Dry-Run + Guardian AI 双重保障。

## 长时间运行 Agent 的 Harness 模式

> **适用场景**：持续运行数小时（会议助手、监控 Agent、后台处理 daemon），没有自然的"任务完成点"。标准 Harness 假设"任务完成 → Agent 停止"，这个假设在持续运行场景下不成立。

### Stop Hook 的局限性

标准 Stop hook 在 Agent 自然停止时触发。持续运行 Agent 不会主动停止，因此：

- Stop hook 的"完成验证"失去意义
- 进度文件的"单轮完成后写入"模式不足以支持恢复
- 上下文压缩必须主动触发，而非等到溢出

这不是 bug，是**不同的问题域**——需要不同的 Harness 模式。

### 长时间运行 Harness 的三个核心组件

**1. 心跳机制（Heartbeat）**

确认 Agent 仍在运行，防止静默死亡（进程存活但逻辑死循环）：

```python
class AgentHealthMonitor:
    HEARTBEAT_INTERVAL = 30  # 秒
    MAX_SILENT_SECONDS = 120  # 超过此阈值告警
    
    async def run(self, agent_loop):
        last_heartbeat = time.time()
        async for event in agent_loop:
            last_heartbeat = time.time()
            await self._process(event)
            # 定期写入 heartbeat 到 PROGRESS.md
            if time.time() - last_heartbeat > self.HEARTBEAT_INTERVAL:
                await self._write_heartbeat()
    
    async def _write_heartbeat(self):
        # 写入持久存储，外部监控可读取
        heartbeat = {
            "ts": now_iso(),
            "status": "alive",
            "events_processed": self.count,
        }
        await self.storage.update("heartbeat", heartbeat)
```

**2. 检查点（Checkpoint）**

定期持久化 Agent 状态，支持崩溃恢复：

```python
class CheckpointManager:
    CHECKPOINT_INTERVAL = 300  # 每 5 分钟打一次检查点
    
    async def maybe_checkpoint(self, state: AgentState) -> None:
        if time.time() - self.last_checkpoint < self.CHECKPOINT_INTERVAL:
            return
        
        checkpoint = {
            "ts": now_iso(),
            "context_summary": state.context.compress_to_summary(),
            "actions_taken": state.action_log[-50:],  # 最近 50 条操作
            "pending_notifications": state.notification_queue,
        }
        await self.storage.write_checkpoint(checkpoint)
        self.last_checkpoint = time.time()
```

**3. 恢复（Resume）**

新会话启动时，从最近检查点恢复而非从零开始：

```python
async def resume_or_start(storage: Storage) -> AgentState:
    checkpoint = await storage.load_latest_checkpoint()
    
    if checkpoint and checkpoint_is_fresh(checkpoint, max_age_seconds=3600):
        # 从检查点恢复
        state = AgentState.from_checkpoint(checkpoint)
        logger.info(f"恢复会话，检查点时间：{checkpoint['ts']}")
    else:
        # 全新启动
        state = AgentState.new()
        logger.info("全新启动 Agent")
    
    return state
```

### 在 CLAUDE.md 中声明长时间运行策略

```markdown
## 持续运行模式

本 Agent 持续运行，无自然完成点。

心跳间隔：30 秒
检查点间隔：5 分钟
最大会话时长（单次）：4 小时（超时后优雅重启）

恢复策略：
- 崩溃后自动从最近检查点恢复（无需人工干预）
- 检查点超过 1 小时则全新启动（避免状态污染）
- 恢复时向用户发送"[已恢复运行]"通知
```

### 与标准 Harness 的比较

| 维度 | 标准 Harness | 长时间运行 Harness |
|------|------------|-----------------|
| 终止触发 | 任务完成 | 外部信号（SIGTERM/时间限制）|
| Stop hook | 完成验证 | 优雅关闭（flush buffer + 写检查点）|
| 进度文件 | 每个模块完成后写 | 每 N 秒定时写（不依赖"完成"事件）|
| 上下文压缩 | 接近溢出时触发 | 按时间窗口主动触发 |
| 错误恢复 | 人工重启 | 自动从检查点恢复 |

---

## HTTP 服务 Agent 的 Harness 模式（P24）

P15/P16 的长时运行 Daemon 模式（Heartbeat + Checkpoint + Resume）针对持续循环的 Agent 进程。HTTP 服务 Agent（FastAPI/Express 托管的 Webhook Agent）有完全不同的活跃性定义：**服务健康 ≠ 进程在运行**，而是 **请求能被正确处理**。

**判断分支：**
```
你的 Agent 是否是 HTTP 服务（接收 Webhook / REST 请求）？
  是 → 使用 HTTP 服务 Harness（见下）
       不需要：Heartbeat 进程 / CheckpointManager / resume_or_start()
       必须有：Healthcheck 端点 / 优雅停机 / 连接池 / 幂等去重
  否 → 使用 Daemon Harness（P15/P16）
```

**HTTP 服务 Harness 核心四件套：**

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
import asyncio
import httpx

# 1. Healthcheck 端点（K8s readiness/liveness probe 目标）
@app.get("/health")
async def healthcheck():
    checks = {
        "redis": await redis_client.ping(),
        "anthropic_reachable": True,
    }
    if not all(checks.values()):
        raise HTTPException(503, detail=checks)
    return {"status": "ok", "checks": checks}

# 2. 优雅停机（处理完进行中的请求再退出）
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动：初始化连接池（跨请求复用）
    app.state.http_client = httpx.AsyncClient()
    yield
    # 停机：等待进行中的请求完成
    await app.state.http_client.aclose()

app = FastAPI(lifespan=lifespan)

# 3. 快速 ACK + 异步处理（满足 Webhook 3s 超时要求）
@app.post("/webhook/slack/events")
async def handle_event(request: Request):
    payload = await request.json()
    # 快速 ACK（<1s），实际处理推到后台 task
    asyncio.create_task(process_event_async(payload))
    return {"ok": True}

# 4. 幂等保护（必须与 HTTP 服务 Harness 一起使用）
async def process_event_async(payload: dict):
    event_id = payload.get("event_id", "")
    if event_id and await idempotency_cache.is_processed(event_id):
        return  # 重复请求，直接忽略
    await idempotency_cache.mark_processed(event_id)
    # 实际 Agent 逻辑...
```

**与 Daemon Harness 的对比：**

| 维度 | Daemon Harness（P15/P16） | HTTP 服务 Harness（P24） |
|------|--------------------------|------------------------|
| 活跃性检测 | Heartbeat 进程内定时上报 | /health HTTP 端点 |
| 故障恢复 | 从 Checkpoint 恢复 | 重启 Pod + 幂等处理 |
| 状态持久化 | CheckpointManager 序列化 | Redis / DB（请求级） |
| 停机处理 | 保存当前 Loop 状态 | 等待进行中请求完成 |

---

## Anti-Patterns to Avoid

- **The encyclopedia CLAUDE.md** — A 500-line instruction manual dilutes everything. Keep it focused. OpenAI learned: "When everything is 'important,' nothing is."
- **Role-based sub-agents** — "Frontend engineer" and "backend engineer" sub-agents don't work. Use sub-agents for context isolation, not role specialization.
- **Tool maximalism** — More tools = worse results. Vercel removed 80% of their tools and improved. If a CLI tool exists in training data, prefer it over an MCP server.
- **Prompt-only fixes** — If you're fixing the same problem by re-explaining in the prompt, you need a mechanical fix (hook, linter, structural test), not more words.
- **Speculative rules** — Never add rules for problems that haven't happened. Each rule should trace to a real failure.
- **Fighting the Bitter Lesson** — If every model upgrade makes your harness more complex, redesign. Good harnesses get simpler over time.

## 当前状态 (2026年4月)

1. **Harness-as-Leverage 被数据验证** — LangChain 在 Terminal Bench 2.0 上仅改 harness（不换模型）从 52.8% 升至 66.5%，Anthropic 内部基准测试显示良好的 CLAUDE.md 对复杂任务成功率提升 20-40%
2. **模型能力持续提升压缩 Harness 复杂度** — Opus/Sonnet 级模型已能自然遵守许多曾需显式规则约束的编码规范，Bitter Lesson 效应加速：2025 年需要 200 行 CLAUDE.md 的项目在 2026 年同等效果只需 80 行
3. **Hook 生态标准化** — Claude Code hooks API（PreToolUse/PostToolUse/Stop）已成为事实标准，Codex/OpenCode 等竞品开始兼容相同的 hook 生命周期模型
4. **Multi-Agent Harness 成为新前沿** — 单 Agent harness 方法论成熟，但多 Agent 协作场景（worktree 隔离、sub-agent 指令传递、跨 Agent 状态同步）的 harness 设计模式仍在快速演化
5. **进度文件从 Markdown 迁移到 JSON** — Anthropic 实证发现 Agent 对 JSON 格式进度文件的意外覆盖率比 Markdown 低 60%，结构化格式正在成为最佳实践

## Known Pitfalls

1. **Stop Hook 无限循环** — Stop hook 中的检查失败会阻止 Agent 停止，Agent 重试又触发 Stop hook，形成死循环。解决方案：Stop hook 必须检查 `stop_hook_active` 标志位，第二次触发时直接放行
2. **CLAUDE.md 信号稀释** — 超过 200 行的 CLAUDE.md 导致关键规则被模型忽略，规则越多遵守率越低。解决方案：定期审计删除已被模型自然遵守的规则，保持高信噪比
3. **Hook 与 CI 重复验证** — PreToolUse hook 做的检查与 CI pipeline 完全重复，导致开发循环变慢但不增加安全性。解决方案：hook 只做快速本地检查（格式化、基本 lint），完整测试留给 CI
4. **跨会话进度丢失** — 依赖 Agent 记忆而非持久化进度文件，新会话启动时 Agent 重复已完成的工作。解决方案：强制使用 JSON 进度文件，每个阶段完成后写入 commit hash 作为检查点

## Harness 工程检查清单

- [ ] 项目根目录有 CLAUDE.md
- [ ] 包含构建/测试/lint 命令
- [ ] 编码约定有文档（仅核心规范）
- [ ] 有 pre-commit hook 强制测试通过
- [ ] 写文件后自动格式化
- [ ] 架构约束有说明和理由
- [ ] 多会话任务有进度文件
- [ ] CLAUDE.md 每条规则都源于真实 agent 失败
- [ ] CLAUDE.md 在 200 行以内（小项目 60 行以内）
- [ ] 定期做 harness 精简审查
- [ ] Skill 反馈日志在使用中

## 延伸阅读

| 主题 | 资源 |
|------|------|
| 7 层 Harness 组件详细实现 | [`references/components.md`](references/components.md) |
| Hook 完整参考（CC/Python/Rust 配方） | [`references/hooks.md`](references/hooks.md) |
| 真实项目 CLAUDE.md 示例 | [`references/examples.md`](references/examples.md) |
| Agent 失败模式诊断指南 | [`references/diagnostics.md`](references/diagnostics.md) |
| 团队协作 / 多 Agent / AI 产品 Harness | [`references/advanced.md`](references/advanced.md) |
| 7 层跨 Agent 对比（CC/CX/OC/CL/OW） | [`references/seven-layer-comparison.md`](references/seven-layer-comparison.md) |
| 上下文分层与 Prompt Cache | `/agentforge-context` |
| Sub-agent 权限与 Worker 隔离 | `/agentforge-multiagent` |
| Loop 检测与沙箱约束 | `/agentforge-security` |

## 逆向审计（Diagnose Mode）

> 由 `/agentforge-diagnose` 调用——对已有代码进行 D6 Harness 维度静态审计。

| # | 检查项 | 检查方式 | 通过标准 |
|---|--------|---------|---------|
| H1 | 存在 CLAUDE.md/AGENTS.md | `ls CLAUDE.md AGENTS.md 2>/dev/null` | 根目录有 Agent 上下文配置文件 |
| H2 | 测试前置门禁 | `cat .claude/settings.json \| grep -A5 "PreToolUse"` 或查 CI 配置 | pre-commit hook 或 CI 在提交前跑测试 |
| H3 | 进度追踪机制 | `find . -name "progress*.json" -o -name "PROGRESS.md" 2>/dev/null` | 多 session 项目有 progress 文件 |
| H4 | 构建验证 | `cat .github/workflows/*.yml \| grep -A3 "run:"` — 看 CI 步骤 | CI 跑 build + lint，失败阻断合并 |
| H5 | CLAUDE.md 规则可追溯 | 读 CLAUDE.md，判断每条规则是否有具体来源 | 无"规则来源不明"的臆想规则（Bitter Lesson 检查） |

**高概率问题**：无 CLAUDE.md（P2 Agent 无上下文配置）、无测试前置门禁（P1 可提交破坏性代码）、CLAUDE.md 超过 200 行（P2 规则稀释效应）
