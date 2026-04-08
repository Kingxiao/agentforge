---
name: agentforge-harness
description: AgentForge Phase 6 - Harness Engineering. CLAUDE.md/AGENTS.md authoring, Hook configuration, Agent failure diagnosis, architectural constraints, verification loops, team collaboration. The official successor to harness-engineering. Triggered when the user says "harness", "agent reliability", "Hook configuration", "CLAUDE.md", or "agent keeps making the same mistake".
triggers:
  - harness
  - agent reliability
  - Hook configuration
  - CLAUDE.md
  - agent keeps making the same mistake
  - agent failure
  - hashimoto loop
metadata:
  version: "2.0.0"
  last_updated: "2026-04-06"
  category: "agent-engineering"
---

> Previous: `/agentforge-security` | Next: `/agentforge-multiagent` | Series entry: `/agentforge`

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

## Loop Detection Patterns

Agents in long-running tasks may enter dead loops (repeating the same operation, ping-pong alternation, output not changing). Production-grade loop detection schemes [v2 research]:

| Agent | Detection Method | Threshold |
|-------|-----------------|-----------|
| OpenClaw [OW] | 4 detectors: signature comparison + echo detection + ping-pong + global circuit breaker | 30 global cap |
| Cline [CL] | Signature comparison (output hash) | 3/5 dual threshold |
| Claude Code [CC] | Compaction circuit breaker | 3 consecutive compaction failures |

**Design recommendation**: Implement signature comparison at minimum (simplest and most effective), layer a global circuit breaker as a safety net for complex systems.

## Dry-Run Mode (Universal Harness Pattern for High-Risk API Write Operations)

**Problem**: When an agent performs write operations on external systems (GitHub PR creation, Jira issue creation, sending emails, production deployments), the actions are often irreversible or difficult to roll back once executed. A Layer 3 Policy Engine can intercept shell commands, but cannot intercept "legal but irreversible API calls."

Dry-Run Mode is the standard harness wrapper for high-risk write tools — **preview first, confirm, then execute**.

### Implementation Pattern

```python
class GitHubPRTool(BaseTool):
    def call(self, input: PRInput) -> ToolResult:
        # Build description of "what will be executed"
        preview = self._build_preview(input)
        
        # Dry-run mode: show preview only, don't execute
        if input.dry_run or self._is_dry_run_context():
            return ToolResult(
                status="dry_run",
                preview=preview,
                message=f"[DRY RUN] About to execute:\n{preview}\n\nPass dry_run=false to confirm execution"
            )
        
        # Actual execution
        return self._execute(input)
    
    def _build_preview(self, input):
        return f"""
        CREATE PR:
          Title: {input.title}
          Target branch: {input.base} ← {input.head}
          Files changed: {len(input.files)} files
          Linked Issues: {input.issue_refs}
        """
```

### Tool Interface Extensions

Add Dry-Run support to the tool interface (decision in `/agentforge-tools`):

| Method | Purpose |
|--------|---------|
| `isDryRunSupported()` | Declares that this tool supports dry-run preview mode |
| `dryRun(input)` | Returns a structured description of "what will be executed" without side effects |
| `isHighRisk()` | Marks the tool as high-risk; Agent decision layer auto-adds dry-run as a prerequisite step |

### Declare Dry-Run Strategy in CLAUDE.md

```markdown
## High-Risk Tool Operation Rules

The following tools must first execute with dry_run=true to show a preview, then wait for user confirmation before actual execution:
- create_github_pr: PR creation is irreversible
- deploy_to_production: Production deployment affects all users
- send_notification: Notifications cannot be recalled once sent
- delete_resource: Deletion operations are typically irreversible

Dry-run output format:
1. Show complete operation description of "what will be executed"
2. List impact scope (how many users/files/data are affected)
3. Wait for explicit confirmation ("confirm execute" or "cancel")
```

### Relationship with Layer 3 Policy Engine

| Mechanism | Applicable To | Blocking Method |
|-----------|--------------|-----------------|
| Layer 3 Starlark Policy | Shell commands (`rm -rf`, `git push`) | Rule matching |
| Dry-Run Mode | API write operations (HTTP POST/DELETE/PUT) | Tool-layer wrapper, preview then confirm |
| Guardian AI | Semantic-level risk assessment | LLM evaluating intent |

The three are complementary, not mutually exclusive. High-risk API tools = Dry-Run + Guardian AI dual protection.

## Long-Running Agent Harness Patterns

> **Use case**: Agents running continuously for hours (meeting assistant, monitoring agent, background processing daemon) with no natural "task completion point." Standard harnesses assume "task done → agent stops" — this assumption doesn't hold for long-running agents.

### Limitations of Stop Hooks

A standard Stop hook fires when the agent naturally stops. Long-running agents don't stop voluntarily, so:

- The Stop hook's "completion verification" becomes meaningless
- The progress file's "write after each round" pattern can't support recovery
- Context compaction must be triggered proactively, not waited for until overflow

This isn't a bug — it's a **different problem domain** requiring a different harness pattern.

### Three Core Components of Long-Running Harnesses

**1. Heartbeat**

Confirms the agent is still alive and prevents silent death (process running but logic in an infinite loop):

```python
class AgentHealthMonitor:
    HEARTBEAT_INTERVAL = 30  # seconds
    MAX_SILENT_SECONDS = 120  # alert threshold exceeded
    
    async def run(self, agent_loop):
        last_heartbeat = time.time()
        async for event in agent_loop:
            last_heartbeat = time.time()
            await self._process(event)
            # Periodically write heartbeat to PROGRESS.md
            if time.time() - last_heartbeat > self.HEARTBEAT_INTERVAL:
                await self._write_heartbeat()
    
    async def _write_heartbeat(self):
        # Write to persistent storage; external monitoring can read
        heartbeat = {
            "ts": now_iso(),
            "status": "alive",
            "events_processed": self.count,
        }
        await self.storage.update("heartbeat", heartbeat)
```

**2. Checkpoint**

Periodically persists agent state to support crash recovery:

```python
class CheckpointManager:
    CHECKPOINT_INTERVAL = 300  # checkpoint every 5 minutes
    
    async def maybe_checkpoint(self, state: AgentState) -> None:
        if time.time() - self.last_checkpoint < self.CHECKPOINT_INTERVAL:
            return
        
        checkpoint = {
            "ts": now_iso(),
            "context_summary": state.context.compress_to_summary(),
            "actions_taken": state.action_log[-50:],  # last 50 actions
            "pending_notifications": state.notification_queue,
        }
        await self.storage.write_checkpoint(checkpoint)
        self.last_checkpoint = time.time()
```

**3. Resume**

When a new session starts, restore from the latest checkpoint rather than starting from scratch:

```python
async def resume_or_start(storage: Storage) -> AgentState:
    checkpoint = await storage.load_latest_checkpoint()
    
    if checkpoint and checkpoint_is_fresh(checkpoint, max_age_seconds=3600):
        # Resume from checkpoint
        state = AgentState.from_checkpoint(checkpoint)
        logger.info(f"Resuming session, checkpoint time: {checkpoint['ts']}")
    else:
        # Fresh start
        state = AgentState.new()
        logger.info("Starting agent fresh")
    
    return state
```

### Declare Long-Running Strategy in CLAUDE.md

```markdown
## Continuous Running Mode

This agent runs continuously with no natural completion point.

Heartbeat interval: 30 seconds
Checkpoint interval: 5 minutes
Max session duration (single run): 4 hours (graceful restart after timeout)

Resume strategy:
- Auto-resume from latest checkpoint after crash (no manual intervention needed)
- Fresh start if checkpoint is older than 1 hour (prevents state pollution)
- Send "[Resumed]" notification to user on restore
```

### Comparison with Standard Harness

| Dimension | Standard Harness | Long-Running Harness |
|-----------|-----------------|---------------------|
| Termination trigger | Task completion | External signal (SIGTERM / time limit) |
| Stop hook | Completion verification | Graceful shutdown (flush buffer + write checkpoint) |
| Progress file | Write on each module completion | Periodic write every N seconds (not dependent on "completion" events) |
| Context compaction | Triggered near overflow | Proactively on time window |
| Error recovery | Manual restart | Auto-resume from checkpoint |

---

## HTTP Service Agent Harness Pattern (P24)

The long-running Daemon mode (Heartbeat + Checkpoint + Resume) from P15/P16 targets continuously looping agent processes. HTTP service agents (FastAPI/Express-hosted webhook agents) have a completely different liveness definition: **service health ≠ process is running**, but rather **requests are being handled correctly**.

**Decision branch:**
```
Is your agent an HTTP service (receiving Webhook / REST requests)?
  Yes → Use HTTP service Harness (see below)
        Not needed: Heartbeat process / CheckpointManager / resume_or_start()
        Required: Healthcheck endpoint / graceful shutdown / connection pool / idempotent dedup
  No → Use Daemon Harness (P15/P16)
```

**HTTP Service Harness Core Four-Pack:**

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
import asyncio
import httpx

# 1. Healthcheck endpoint (K8s readiness/liveness probe target)
@app.get("/health")
async def healthcheck():
    checks = {
        "redis": await redis_client.ping(),
        "anthropic_reachable": True,
    }
    if not all(checks.values()):
        raise HTTPException(503, detail=checks)
    return {"status": "ok", "checks": checks}

# 2. Graceful shutdown (wait for in-flight requests to finish before exiting)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize connection pool (reused across requests)
    app.state.http_client = httpx.AsyncClient()
    yield
    # Shutdown: wait for in-flight requests to complete
    await app.state.http_client.aclose()

app = FastAPI(lifespan=lifespan)

# 3. Fast ACK + async processing (meets Webhook 3s timeout requirement)
@app.post("/webhook/slack/events")
async def handle_event(request: Request):
    payload = await request.json()
    # Fast ACK (<1s), actual processing pushed to background task
    asyncio.create_task(process_event_async(payload))
    return {"ok": True}

# 4. Idempotency protection (must use alongside HTTP service Harness)
async def process_event_async(payload: dict):
    event_id = payload.get("event_id", "")
    if event_id and await idempotency_cache.is_processed(event_id):
        return  # Duplicate request, ignore
    await idempotency_cache.mark_processed(event_id)
    # Actual agent logic...
```

**Comparison with Daemon Harness:**

| Dimension | Daemon Harness (P15/P16) | HTTP Service Harness (P24) |
|-----------|-------------------------|---------------------------|
| Liveness detection | Heartbeat process internal periodic reporting | /health HTTP endpoint |
| Failure recovery | Resume from Checkpoint | Restart Pod + idempotent processing |
| State persistence | CheckpointManager serialization | Redis / DB (per-request) |
| Shutdown handling | Save current Loop state | Wait for in-flight requests to complete |

---

## Anti-Patterns to Avoid

- **The encyclopedia CLAUDE.md** — A 500-line instruction manual dilutes everything. Keep it focused. OpenAI learned: "When everything is 'important,' nothing is."
- **Role-based sub-agents** — "Frontend engineer" and "backend engineer" sub-agents don't work. Use sub-agents for context isolation, not role specialization.
- **Tool maximalism** — More tools = worse results. Vercel removed 80% of their tools and improved. If a CLI tool exists in training data, prefer it over an MCP server.
- **Prompt-only fixes** — If you're fixing the same problem by re-explaining in the prompt, you need a mechanical fix (hook, linter, structural test), not more words.
- **Speculative rules** — Never add rules for problems that haven't happened. Each rule should trace to a real failure.
- **Fighting the Bitter Lesson** — If every model upgrade makes your harness more complex, redesign. Good harnesses get simpler over time.

## Current State (April 2026)

1. **Harness-as-Leverage Validated by Data** — LangChain on Terminal Bench 2.0 improved from 52.8% to 66.5% by changing only the harness (no model change). Anthropic internal benchmarks show good CLAUDE.md improves complex task success rate by 20-40%.
2. **Improving Model Capabilities Compress Harness Complexity** — Opus/Sonnet-class models now naturally follow many coding conventions that previously required explicit rules. Bitter Lesson effect accelerating: a project needing 200 lines of CLAUDE.md in 2025 achieves the same results with 80 lines in 2026.
3. **Hook Ecosystem Standardizing** — Claude Code hooks API (PreToolUse/PostToolUse/Stop) has become a de facto standard; Codex/OpenCode and other competitors are beginning to adopt compatible hook lifecycle models.
4. **Multi-Agent Harness Is the New Frontier** — Single-agent harness methodologies are mature, but harness design patterns for multi-agent collaboration scenarios (worktree isolation, sub-agent instruction passing, cross-agent state synchronization) are still evolving rapidly.
5. **Progress Files Shifting from Markdown to JSON** — Anthropic evidence shows agents have 60% lower accidental overwrite rate on structured JSON progress files vs Markdown. Structured format is becoming best practice.

## Known Pitfalls

1. **Stop Hook Infinite Loop** — Check failure in a Stop hook prevents the agent from stopping, the agent retries and triggers the Stop hook again, creating a dead loop. Solution: Stop hooks MUST check the `stop_hook_active` flag; on second trigger, pass through directly.
2. **CLAUDE.md Signal Dilution** — CLAUDE.md exceeding 200 lines causes key rules to be ignored by the model; the more rules, the lower the compliance rate. Solution: Periodically audit and remove rules the model now follows naturally, keeping signal-to-noise ratio high.
3. **Hook and CI Redundant Verification** — PreToolUse hook checks that completely duplicate the CI pipeline slow down the development loop without adding security. Solution: hooks only do fast local checks (formatting, basic lint); full testing belongs in CI.
4. **Cross-Session Progress Loss** — Relying on agent memory rather than persistent progress files means new sessions start with the agent repeating already-completed work. Solution: Enforce JSON progress files, write commit hashes as checkpoints after each phase completion.

## Harness Engineering Checklist

- [ ] Project root has a CLAUDE.md
- [ ] Contains build/test/lint commands
- [ ] Coding conventions documented (core conventions only)
- [ ] Has pre-commit hook enforcing test pass
- [ ] Auto-formats after file writes
- [ ] Architectural constraints documented with rationale
- [ ] Progress file for multi-session tasks
- [ ] Every CLAUDE.md rule traces to a real agent failure
- [ ] CLAUDE.md under 200 lines (under 60 for small projects)
- [ ] Periodic harness simplification review conducted
- [ ] Skill feedback log in active use

## Further Reading

| Topic | Resource |
|-------|---------|
| Seven-layer harness component detailed implementation | [`references/components.md`](references/components.md) |
| Hook complete reference (CC/Python/Rust recipes) | [`references/hooks.md`](references/hooks.md) |
| Real project CLAUDE.md examples | [`references/examples.md`](references/examples.md) |
| Agent failure pattern diagnosis guide | [`references/diagnostics.md`](references/diagnostics.md) |
| Team collaboration / multi-agent / AI product harnesses | [`references/advanced.md`](references/advanced.md) |
| Seven-layer cross-agent comparison (CC/CX/OC/CL/OW) | [`references/seven-layer-comparison.md`](references/seven-layer-comparison.md) |
| Context layering and Prompt Cache | `/agentforge-context` |
| Sub-agent permissions and worker isolation | `/agentforge-multiagent` |
| Loop detection and sandbox constraints | `/agentforge-security` |

## Reverse Audit (Diagnose Mode)

> Called by `/agentforge-diagnose` — static audit of existing code across D6 Harness dimensions.

| # | Check Item | How | Pass Criteria |
|---|-----------|-----|---------------|
| H1 | CLAUDE.md/AGENTS.md exists | `ls CLAUDE.md AGENTS.md 2>/dev/null` | Agent context config file in root directory |
| H2 | Test pre-commit gate | `cat .claude/settings.json \| grep -A5 "PreToolUse"` or CI config | pre-commit hook or CI runs tests before commit |
| H3 | Progress tracking mechanism | `find . -name "progress*.json" -o -name "PROGRESS.md" 2>/dev/null` | Multi-session project has a progress file |
| H4 | Build verification | `cat .github/workflows/*.yml \| grep -A3 "run:"` — check CI steps | CI runs build + lint, failures block merge |
| H5 | CLAUDE.md rules traceable | Read CLAUDE.md, determine whether each rule has a specific source | No speculative rules with unknown origins (Bitter Lesson check) |

**High-probability issues**: No CLAUDE.md (P2 agent has no context config), no test pre-commit gate (P1 can commit broken code), CLAUDE.md exceeds 200 lines (P2 rule dilution effect)
