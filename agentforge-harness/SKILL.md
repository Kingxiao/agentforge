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
  version: "2.2.0"
  last_updated: "2026-05-14"
  category: "agent-engineering"
origin: self
authored_by: zichuan
confirmed_at: "2026-05-14"
---

> Previous: `/agentforge-security` | Next: `/agentforge-multiagent` | Series entry: `/agentforge`

# Harness Engineering

A discipline for designing constraints, tools, feedback loops, and environmental infrastructure that make AI coding agents reliable at scale. Core principle: **when an agent fails, engineer a system-level fix so the failure never recurs — don't just retry.**

## First Principles

Five fundamental constraints drive why harnesses exist:

1. **Context windows are finite** — even 200K tokens fill quickly during multi-step tasks.
2. **Context rots** — model performance degrades as input length grows, even within limits.
3. **Agents are stateless** — no memory persists between sessions unless the harness provides it.
4. **Agents hallucinate** — they fabricate APIs, variable names, function signatures with confidence.
5. **Agents skip verification** — they declare victory with failing tests. The harness forces test-pass before commit.

### Evidence: the harness is the leverage

Two production datapoints (verified 2026-04-12) show harness work outperforming model work:

- **LangChain on Terminal Bench 2.0** — deepagents-cli improved from **52.8 → 66.5** (+13.7 points) by **changing only the harness, not the model**, jumping from Top 30 to Top 5. Source: [LangChain blog "Improving Deep Agents with harness engineering"](https://blog.langchain.com/improving-deep-agents-with-harness-engineering/).
- **Vercel d0 (text-to-SQL agent)** — deleted 80% of tools (16 → 1 bash capability) + added sandbox. Result: success rate **80% → 100%**, **40% fewer tokens**, **40% fewer steps**, **3.5× faster** (274 s → 77 s). Source: [Vercel blog "We removed 80% of our agent's tools"](https://vercel.com/blog/we-removed-80-percent-of-our-agents-tools) (Dec 2025).

**The model is commodity; the harness is leverage.** Both cases: same model, different harness → step-change in outcome. If your agent underperforms, assume harness gap before model gap.

## The Hashimoto Loop (Core Methodology)

Every harness improvement follows this cycle: Agent attempts task → observe failure → diagnose "what capability or constraint is missing?" → choose fix type (simple behavioral → CLAUDE.md; complex/recurring → tool, hook, or structural test) → verify the fix prevents recurrence → repeat.

**Each line in a good CLAUDE.md traces to a specific past agent failure. Never add speculative rules.**

### Automated Hashimoto Loop (L3b — Hermes Pattern)

A learning agent can close the loop autonomously: task completes → trajectory saved to JSONL (completed vs failed separation) → hindsight retrospective analyzes the trajectory (did agent repeat a mistake N times? use a suboptimal tool sequence? was a skill missing?) → skill patch proposed → security scan → atomic write → next task benefits.

Key difference from L3a: observation and diagnosis are performed by the agent itself. The human's role shifts from firefighter to **curriculum designer** — setting the benchmark, not watching every run.

Viable only when: (a) trajectories are reliably captured, (b) the agent has skill write access with rollback, (c) validation (benchmark run) gates patch → deploy. Without all three, autonomous skill updates amplify errors instead of correcting them.

## Harness Components (Seven Layers)

> Detailed implementation per layer → [`references/components.md`](references/components.md)

1. **Context Engineering** — What the agent sees (CLAUDE.md, progressive disclosure, knowledge architecture)
2. **Tool Orchestration** — What the agent can do (fewer tools = better; sub-agents for context isolation)
3. **Memory & State** — What persists across sessions (progress files, feature lists, git checkpoints)
4. **Architectural Constraints** — What the agent cannot do (dependency rules, linters, structural tests)
5. **Verification & Feedback** — How the system self-corrects (test-before-commit, back-pressure hooks)
6. **Entropy Management** — Fighting codebase decay (periodic cleanup tasks, documentation consistency)
7. **Human-in-the-Loop** — When humans must intervene (approval workflows, review gates)

## Applying Harness Engineering

### Task: Initialize a New Project Harness

1. **Examine the project** — read tech stack (check `package.json` / `Cargo.toml` / `pyproject.toml` / `go.mod` / `pom.xml`), build/test commands, existing CLAUDE.md, `.claude/`, linter configs, CI files.
2. **Create a minimal CLAUDE.md** at project root. If one exists, read it first and improve — existing rules likely encode hard-won lessons. Claude Code's `/init` can auto-generate a starter.
3. **Sub-directory CLAUDE.md** files only where domain-specific rules are needed.
4. **Configure hooks** in `.claude/settings.json` for mechanical enforcement, adapted to the detected stack. Only add test-before-commit hooks if a working test suite exists. → [`references/hooks.md`](references/hooks.md) for Node.js / Python / Rust recipes.
5. **Explain the Hashimoto Loop** — tell the user this is a living document that grows from observed failures.

**CLAUDE.md template (minimal start)**: frontmatter with project overview (one sentence), tech stack, commands (build/test/lint/dev), architecture (2–3 sentences), rules (start with 2–3 essential — add as failures reveal gaps), known pitfalls (empty at start; each entry documents a specific failure pattern observed during agent use).

**Keep under 200 lines (ideally under 60 for small projects). Every rule earns its place through a documented failure.**

### Task: Diagnose and Fix Agent Failures

When Claude Code keeps making a specific mistake:

1. **Identify the pattern** — what went wrong, how often, in what context.
2. **Classify the fix type**:
   - **Behavioral** (wrong convention, forgotten step) → add a rule to CLAUDE.md.
   - **Mechanical** (skips tests, commits broken code) → add a hook.
   - **Structural** (wrong dependencies, violates architecture) → linter rule or structural test.
   - **Context** (loses track in long sessions) → improve progressive disclosure or add sub-directory CLAUDE.md.
3. **Implement** using the appropriate mechanism.
4. **Verify** by describing a test scenario.

### Task: Configure Hooks (Back-Pressure)

Hooks enforce mechanical constraints at specific lifecycle events. Read [`references/hooks.md`](references/hooks.md) for the full reference.

**Common patterns for `.claude/settings.json`** (nested `hooks` array with `type` — this exact structure is required):

- **PreToolUse / matcher `Bash`** — intercept `git commit` sub-commands; run tests; `exit 2` if they fail.
- **PostToolUse / matcher `Write|Edit|MultiEdit`** — auto-format the changed file (`prettier`, `black`, `rustfmt`, …).
- **Stop hook** — run a final build; exit 2 if it fails. **Must check `stop_hook_active`** to prevent infinite loops.

**Adapt commands to your stack**: Node.js uses `npm test` / `npx prettier` / `npm run build`; Python uses `python -m pytest` / `python -m black` / `python -m mypy src/`.

**Key format rules**: `matcher` matches **tool names** (`Bash`, `Write`, `Edit`, `MultiEdit`), NOT commands like "git commit". Use `exit 2` to block actions (not `exit 1`). Hooks parsing stdin require `jq` (`brew install jq` / `apt install jq`).

**Principle**: use deterministic tools for what they handle well (formatting, linting, testing). Reserve agent intelligence for judgment and reasoning.

### Task: Optimize Context for Long Sessions

1. **Use `/compact` proactively** — don't wait for context to fill. Compact after completing a logical unit.
2. **Use `/clear` between phases** — when switching from planning to implementation, or between unrelated features.
3. **Sub-directory CLAUDE.md for progressive disclosure**: root (global: build commands, style, architecture overview), `src/` (source-specific: import conventions, module patterns), `src/api/` (endpoint patterns, auth), `src/components/` (naming, prop patterns), `tests/` (test patterns, mock conventions).
4. **For multi-session projects, maintain a progress file — prefer JSON over Markdown** (Anthropic found agents are less likely to accidentally overwrite structured JSON). Structure: `goal`, `completed[]` with feature/commit/status, `current` with feature/status/done/next, `known_issues[]` with references.

### Task: Use Claude Code's Built-in Features

- **`/init`** — auto-generates a starter CLAUDE.md by analyzing the project.
- **`/hooks`** — read-only browser for inspecting all configured hooks.
- **`/compact`** — manually trigger context compaction.
- **`/clear`** — full context reset for switching unrelated tasks.
- **Plan mode** (Shift+Tab ×2 or `/plan`) — Edit → Auto-Accept → Plan cycle. Claude analyzes and plans without making changes until approved.
- **Custom commands** — `.claude/commands/*.md` (project) or `~/.claude/commands/*.md` (personal).
- **Sub-agents** — `.claude/agents/*.md` to create specialized sub-agents with custom system prompts and tool permissions.
- **Settings hierarchy** — `~/.claude/settings.json` (global) → `.claude/settings.json` (team, git-tracked) → `.claude/settings.local.json` (personal, git-ignored).

### Task: Review and Simplify a Harness

When auditing an existing harness, or after a major model update:

1. Read current CLAUDE.md and all sub-directory CLAUDE.md files.
2. **Identify candidates for removal**: rules the model now follows naturally; overly specific rules that could be generalized; conflicts/duplicates; complex workarounds that newer models handle natively.
3. **Apply the Bitter Lesson test**: if the harness has grown more complex over time without the project growing proportionally, it's likely over-engineered.
4. **Simplify**: merge, generalize, or delete. A shorter CLAUDE.md with higher-signal rules outperforms a long one.

**Design principle**: **build for deletion.** Every harness component encodes an assumption about model limitations — those assumptions expire. If the harness keeps getting more complex as models improve, you are over-engineering.

### Task: Adopt a Borrowed Component

When copying a skill, hook, rule, or pattern from another project into this harness:

1. **Tag origin in frontmatter:**
   ```yaml
   origin: <source-project-or-repo>
   verified: YYYY-MM-DD
   source_path: <file-path-with-line-numbers>
   ```
2. **Quote the source** — include one line in the skill/hook explaining "why we believe this works," with a file + line number reference to the original. Survives the inevitable "why is this here?" six months later.
3. **Set a re-verification horizon** — after 90 days, re-read the source. Upstream evolves; borrowed components drift from their origin and become unmaintained orphans otherwise.
4. **Note explicit adaptations** — what changed from the source and why. If nothing changed, say so ("verbatim copy"). Hidden adaptations produce silent divergence bugs.
5. **Apply Bitter Lesson to borrowed items** — if a borrowed component exists because its source project needed it but your project doesn't have that failure mode, don't adopt it. Borrowing is not collection.

Prevents "borrowed but forgotten" drift — 6 months later nobody (including you) knows if the component still matches its source or has silently diverged.

### Meta-Harness Design Principle: Stable Interfaces, Swappable Implementation

> Source: Anthropic Managed Agents architecture — https://www.anthropic.com/engineering/managed-agents (published 2026-04-10, verified 2026-04-11), validated by Sonnet 4.5 → Opus 4.5 upgrade.

Anthropic documented a concrete case: context-reset logic added for Claude Sonnet 4.5 became unnecessary when Claude Opus 4.5 handled context natively — but the harness code stayed, adding latency and complexity for zero benefit.

**Principle**: Be opinionated about interfaces, not implementation.

- **Stable** (keep across model upgrades): interface shapes (`execute(name, input) → string`); event lifecycle (PreToolUse / PostToolUse / Stop); session persistence format (JSONL / SQLite schema); security boundaries (what can/cannot access credentials).
- **Swappable** (expect to change per model generation): compression strategy; prompt structure; approval thresholds; loop-detection sensitivity.

**Practical test**: after a major model upgrade, audit each harness rule — if the model now follows it naturally without the rule, delete it. **A good harness shrinks as models improve.**

### Task: Design Architectural Constraints

1. Define clear module boundaries — which modules can import from which.
2. Encode in CLAUDE.md with rationale. Example: `src/domain/` must not import from `src/infrastructure/` (domain layer is pure); `src/api/` handlers must use the service layer; database queries go through repository classes. Rationale: strict layering prevents agents from creating shortcuts that compile but violate separation of concerns.
3. Add structural tests where possible (custom lint rules that check import paths).
4. **Write linter error messages as remediation instructions** — the agent reads error messages to self-correct.

### Task: Set Up Team Harness Collaboration

1. **Shared harness lives in git** — `.claude/settings.json` and root `CLAUDE.md` are git-tracked; all team members get the same constraints automatically.
2. **Personal preferences stay local** — `.claude/settings.local.json` (git-ignored) for individual hook tweaks.
3. **Treat CLAUDE.md changes like code changes** — PR review for harness modifications.
4. **Onboarding = harness** — a good CLAUDE.md simultaneously teaches the agent AND new team members how the codebase works.

### Task: Coordinate Multiple AI Coding Tools

Using Claude Code alongside Cursor, Codex, or others on the same codebase:

1. **Git as shared memory** — all agents read/write through git. Atomic commits with descriptive messages become the inter-agent communication protocol.
2. **CLAUDE.md / AGENTS.md dual format** — maintain both if needed; CLAUDE.md for Claude Code, AGENTS.md for Codex/OpenCode. Keep shared rules in sync.
3. **Divide by scope, not role** — Agent A handles backend module, Agent B handles frontend. Don't have two agents editing the same files.
4. **CI as universal verifier** — the one harness component that validates all agents' output equally.

### Task: Apply Harness Thinking Beyond Coding

Harness principles apply to any task — research, documentation, data analysis, content creation. Create task-specific CLAUDE.md files (e.g. Research Standards: search 5+ sources, cross-verify with 3 independent sources, list URLs, flag uncertainty, conclusion-first structure). Use Stop hooks for non-coding verification (output files exist, required sections present, word counts met). Progress files work for any multi-session task.

### Task: Design AI Product Harness Architecture

Building a product using AI agents internally — the same seven layers apply at product scale:

1. **Input harness** — validate and structure user input before it reaches the model; sanitize, classify, route.
2. **Execution harness** — constrain what the agent can do: tool access controls, rate limits, timeout, resource budgets.
3. **Output harness** — verify agent output before returning to user: factual checks, format validation, safety filters, confidence scoring.
4. **Feedback harness** — capture every failure as structured data; each user-reported error feeds back into constraint refinement (Hashimoto Loop at product scale).
5. **Observability harness** — log every agent action, tool call, decision point.

## Self-Evolution: The Skill Improves Itself

This skill applies the Hashimoto Loop to its own content. Claude Code can modify skill files at runtime; changes take effect immediately via live change detection.

- **Record feedback** to `scripts/feedback.jsonl` with fields `{date, category, description, fix_applied, file_affected}`. Categories: `hooks`, `claude-md`, `context`, `architecture`, `diagnostics`, `examples`, `advanced`, `other`.
- **Evolve** when accumulated feedback warrants: read log → identify patterns → propose changes with diff → user approval → update files → log evolution to `scripts/changelog.md`. Always get user approval before modifying skill files. Apply Bitter Lesson to the skill itself.

## Loop Detection Patterns

Long-running agents may enter dead loops (same operation repeated, ping-pong alternation, output not changing).

| Agent | Detection Method | Threshold |
|-------|-----------------|-----------|
| OpenClaw [OW] | 4 detectors: signature comparison + echo detection + ping-pong + global circuit breaker | 30 global cap |
| Cline [CL] | Signature comparison (output hash) | 3/5 dual threshold |
| Claude Code [CC] | Compaction circuit breaker | 3 consecutive compaction failures |

**Recommendation**: Implement signature comparison at minimum (simplest, most effective); layer a global circuit breaker as safety net for complex systems.

## Dry-Run Mode (Universal Harness Pattern for High-Risk API Write Operations)

When an agent performs write operations on external systems (PR creation, Jira issues, emails, production deployments), the actions are often irreversible. Layer 3 policy engines can intercept shell commands but cannot intercept "legal but irreversible API calls." **Dry-Run Mode is the standard wrapper for high-risk write tools — preview first, confirm, then execute.**

**Implementation pattern (principle)**: Every high-risk tool's `call(input)` first builds a structured preview. If `input.dry_run` or the context is in dry-run mode, return `{status: "dry_run", preview, message}` without executing. Otherwise execute. Preview should describe what will be executed (e.g. for `create_github_pr`: title, target branch, files changed, linked issues).

**Tool interface extensions** (see `/agentforge-tools`):

| Method | Purpose |
|--------|---------|
| `isDryRunSupported()` | Declares dry-run preview support |
| `dryRun(input)` | Returns structured description without side effects |
| `isHighRisk()` | Marks tool as high-risk; decision layer auto-adds dry-run as prerequisite |

**Declare Dry-Run strategy in CLAUDE.md**: list high-risk tools (`create_github_pr` — irreversible; `deploy_to_production` — affects all users; `send_notification` — cannot be recalled; `delete_resource` — typically irreversible). Dry-run output format: show complete operation description, list impact scope (users/files/data affected), wait for explicit confirmation.

**Relationship with Layer 3 Policy Engine**:

| Mechanism | Applies To | Blocking Method |
|-----------|--------------|-----------------|
| Layer 3 Starlark | Shell commands (`rm -rf`, `git push`) | Rule matching |
| Dry-Run Mode | API writes (HTTP POST/DELETE/PUT) | Tool-layer wrapper, preview then confirm |
| Guardian AI | Semantic-level risk | LLM evaluating intent |

Complementary, not exclusive. High-risk API tools = Dry-Run + Guardian AI dual protection.

## Long-Running Agent Harness Patterns

> **Use case**: Agents running continuously for hours (meeting assistant, monitoring, background processing) with no natural "task completion point." Standard harnesses assume "task done → agent stops" — long-running doesn't.

### Limitations of Stop Hooks

Standard Stop hooks fire when the agent naturally stops. Long-running agents don't stop voluntarily, so: (1) Stop hook "completion verification" becomes meaningless; (2) progress-file "write after each round" can't support recovery; (3) context compaction must be triggered proactively, not on overflow. **Different problem domain → different harness pattern.**

### Three Core Components

**1. Heartbeat** — confirms the agent is alive, prevents silent death (process running but logic stuck). `AgentHealthMonitor` writes a heartbeat to `PROGRESS.md` every 30 s (`HEARTBEAT_INTERVAL`); alert threshold exceeded at 120 s of silence. Persistent storage so external monitoring can read.

**2. Checkpoint** — periodically persists agent state for crash recovery. `CheckpointManager.maybe_checkpoint()` every 300 s, writing `{ts, context_summary, actions_taken[-50:], pending_notifications}` to durable storage.

**3. Resume** — on new session start, restore from latest checkpoint rather than scratch. `resume_or_start()` loads the latest checkpoint; if fresh (< 1 hour old), resume; otherwise fresh start (prevents state pollution).

### Declare Long-Running Strategy in CLAUDE.md

State explicitly: heartbeat interval (30 s), checkpoint interval (5 min), max session duration (e.g. 4 hours with graceful restart on timeout), resume strategy (auto-resume after crash; fresh start if checkpoint is older than 1 hour; send `[Resumed]` notification to user).

### Comparison with Standard Harness

| Dimension | Standard Harness | Long-Running Harness |
|-----------|-----------------|---------------------|
| Termination trigger | Task completion | External signal (SIGTERM / time limit) |
| Stop hook | Completion verification | Graceful shutdown (flush buffer + write checkpoint) |
| Progress file | Write on each module completion | Periodic write every N seconds |
| Context compaction | Triggered near overflow | Proactive time-window |
| Error recovery | Manual restart | Auto-resume from checkpoint |

## HTTP Service Agent Harness Pattern (P24)

The long-running Daemon mode (Heartbeat + Checkpoint + Resume) targets continuously looping agent processes. **HTTP service agents** (FastAPI/Express webhook agents) have a completely different liveness definition: **service health ≠ process is running** — it means requests are being handled correctly.

**Decision branch**: HTTP service (Webhook / REST) → HTTP service Harness below (no Heartbeat process / CheckpointManager / `resume_or_start()` needed; instead: healthcheck endpoint + graceful shutdown + connection pool + idempotent dedup). Otherwise → Daemon Harness above.

**HTTP Service Harness — four mandatory components**:

1. **Healthcheck endpoint** — `/health` that probes dependencies (Redis ping, upstream API reachability) and returns 503 if any fail. Target for K8s readiness/liveness probes.
2. **Graceful shutdown** — via FastAPI `lifespan` contextmanager: startup initializes shared connection pool (e.g. `httpx.AsyncClient`); shutdown waits for in-flight requests, then closes the pool.
3. **Fast ACK + async processing** — webhook endpoints must return in < 1 s (most platforms enforce a 3 s timeout). Push actual work to a background task (`asyncio.create_task(process_event_async(payload))`); return `{"ok": True}` immediately.
4. **Idempotency protection** — webhook platforms deliver duplicates. Before real processing, check `idempotency_cache.is_processed(event_id)`; mark processed at start of processing.

**Comparison**:

| Dimension | Daemon Harness | HTTP Service Harness |
|-----------|-------------------------|---------------------------|
| Liveness detection | Heartbeat process internal reporting | `/health` HTTP endpoint |
| Failure recovery | Resume from checkpoint | Restart Pod + idempotent processing |
| State persistence | `CheckpointManager` serialization | Redis / DB (per-request) |
| Shutdown handling | Save current loop state | Wait for in-flight requests |

## Learning Harness (Hermes Pattern)

The constraint harness (CLAUDE.md + hooks + structural tests) prevents the agent from doing the wrong thing. A **learning harness** enables the agent to improve what it does right — capturing successful trajectories, distilling them into reusable skills, closing the loop without human intervention at every step. Two orthogonal dimensions; most agents only have the constraint harness.

### The Two Dimensions

| Dimension | Constraint Harness | Learning Harness |
|-----------|-------------------|-----------------|
| Goal | Prevent wrong actions | Improve correct actions |
| Mechanism | Hooks, linters, CLAUDE.md rules | Trajectory capture, skill synthesis, benchmark validation |
| Trigger | Agent about to do something | Agent just finished something |
| Human role | Author of rules | Author of benchmarks |
| Failure mode | Agent breaks the rules | Agent optimizes the wrong metric |

### Components

1. **Trajectory capture infrastructure** — split by outcome (`save_trajectory(…, completed=True) → trajectory_samples.jsonl`; failed → `failed_trajectories.jsonl`). Critical: strip ephemeral context before saving (persona injection, session IDs — not generalizable). Both files feed different training pipelines: completed = positive examples (imitate), failed = negative examples (DPO preference tuning).
2. **Skill write access with safety gates** — atomic writes (`tempfile.mkstemp()` + `os.replace()`, crash-safe); security scan on every write (identical to hub-installed skills); rollback on scan block (agent gets rejection reason, can revise); cache invalidation (in-process LRU + disk snapshot cleared); fuzzy match on patch failure (returns file preview for model self-correction).
3. **Validation between patch and deploy** — autonomous skill updates without validation amplify errors. Minimum gate: run a benchmark subset after each skill update; score drops → revert; score improves or holds → deploy, log.
4. **Hindsight retrospective analysis** — after completing a trajectory, the agent reviews it *in a separate context* with full trajectory access. Questions: Did I repeat any tool sequence 3+ times before finding the right approach? (package as skill step) Did I recover from an error not covered in any existing skill? (patch the skill) Did I complete a 5+ step task with no existing skill? (create new skill).

Hindsight runs **after** the task in a separate context — prevents the agent from modifying its own behavior mid-task.

### When to Build

**Build it when**: the agent performs repeated similar tasks (skill synthesis has high ROI); you have a measurable benchmark to validate skill changes against; the task domain evolves over time.

**Don't build it when**: each task is unique (trajectories don't generalize); no reliable success/failure signal (can't split trajectories meaningfully); no validation benchmark (autonomous updates without validation are net negative).

The constraint harness is always needed. The learning harness is only needed when the agent will run enough tasks that accumulated trajectory data exceeds what a human can review.

## Mandatory Self-Enforcement Checkpoints

> Origin: Aindex weekly retro 2026-04-21~04-27 — 57/88 user messages flagged 4 categories of agent violations (16 unverified fixes, 26 hardcoded business enums, 5 off-topic answers, 9 shallow root-cause). User's strong-frustration baseline broken 2026-04-21. Memory-only rules had been in place 4 months without behavioral shift → soft rules confirmed insufficient. The four CHECKPOINT below are the agent-side soft layer paired with hook-layer hard enforcement (verification-summary-guard, config-drift-guard) per dual-layer C plan (approved 2026-05-14).

### CHECKPOINT 1 — Before claiming a fix
All of (a)+(b)+(c) required:
- (a) A Bash tool call has occurred in the current transcript window
- (b) Its `stdout` contains at least one literal marker: `PASS` / `FAIL` / `test passed` / `test failed` / `✓` / `✗` / `tests passed` / `ok N`
- (c) ≥2 lines of that stdout are quoted in the response's verification block

Until all three are satisfied, the phrases `已修复` / `修好了` / `搞定了` / `fix done` / `修复完成` are prohibited. Hook `verification-summary-guard.sh` enforces (a)+(b) mechanically as of 2026-05-14.

### CHECKPOINT 2 — Before stating a root cause
Evidence trio (a)+(b)+(c), all three required:
- (a) Read of target project config (`.config/`, `config.toml`, `.env`, `pyproject.toml`, `Cargo.toml`)
- (b) WebSearch on the exact error string / symptom signature
- (c) Grep of reference codebase (`~/.openclaw/借鉴/openhands/`, `openclaw/`, or comparable prior art) — at least one citation in `path/to/file:NN` form

Without all three, conclusions must be labelled `hypothesis`, not `root cause`. Canonical rule: `feedback_search_strategy.md:70-83`. This checkpoint is its enforcement view (no dedicated hook yet — soft layer only).

### CHECKPOINT 3 — Before claiming "hardcoding cleaned"
Grep each touched file for CJK-rich list constants (`≥5` strings containing 汉字) — paste the grep command and its empty-result confirmation. The hook `config-drift-guard.sh` mirrors this check on write; this checkpoint forces author-side parity so the hook never has to fire as the first detection.

### CHECKPOINT 4 — Before answering "what is X" / "which X" / "specifically what"
Read or Grep the referenced source and quote actual lines. Abstract paraphrases ("there's logic that handles X") are prohibited for factual queries. Citation format: `path/to/file:NN-MM` + fenced quoted block. Source: `feedback_hybrid_execution.md` scenario 3.

### Enforcement Map

| Checkpoint | Soft layer (this skill) | Hard layer (hook) |
|---|---|---|
| 1 — fix claim | this section | `verification-summary-guard.sh` (Stop) |
| 2 — root cause | this section | none — soft only |
| 3 — hardcoding cleaned | this section | `config-drift-guard.sh` (PreToolUse Write/Edit) |
| 4 — "what / which" query | this section | none — soft only |

Soft-only checkpoints (2 + 4) rely on agent compliance; promote to hook layer if weekly retro detects sustained violations.

## Anti-Patterns to Avoid

- **The encyclopedia CLAUDE.md** — A 500-line instruction manual dilutes everything. OpenAI learned: "When everything is 'important,' nothing is."
- **Role-based sub-agents** — "Frontend engineer" / "backend engineer" sub-agents don't work. Use sub-agents for context isolation, not role specialization.
- **Tool maximalism** — More tools = worse results. Vercel removed 80% of their tools and improved. If a CLI tool exists in training data, prefer it over an MCP server.
- **Prompt-only fixes** — If you're fixing the same problem by re-explaining in the prompt, you need a mechanical fix (hook, linter, structural test), not more words.
- **Speculative rules** — Never add rules for problems that haven't happened. Each rule should trace to a real failure.
- **Fighting the Bitter Lesson** — If every model upgrade makes your harness more complex, redesign. Good harnesses get simpler over time.
- **Secondhand research as firsthand evidence** — When the main agent uses subagents (Explore, general-purpose) for research, the subagent's summary is secondhand. Treating it as "already scanned" leads to: (a) skipping firsthand reads of critical code, (b) compounding subagent hallucinations, (c) confident-sounding conclusions with no traceable citations. Rule: any borrowing/migration judgment MUST cite file path + line number + direct quote. Agent-transcribed summaries are insufficient. If the decision cost is high, do the read yourself. Applies recursively — if you're about to recommend a pattern from a file, verify the file still says what you remember.

## Current State (April 2026)

1. **Harness-as-Leverage validated by data** — LangChain on Terminal Bench 2.0 improved from 52.8% to 66.5% via harness change alone. Anthropic internal benchmarks: good CLAUDE.md improves complex task success rate by 20–40%.
2. **Improving model capabilities compress harness complexity** — Opus/Sonnet-class models naturally follow many coding conventions that previously required explicit rules. Bitter Lesson effect accelerating: a project needing 200 lines of CLAUDE.md in 2025 now achieves the same results with 80 lines.
3. **Hook ecosystem standardizing** — Claude Code's hooks API (PreToolUse / PostToolUse / Stop) is a de facto standard; Codex / OpenCode and other competitors adopting compatible lifecycles.
4. **Multi-Agent harness is the new frontier** — Single-agent methodology is mature, but multi-agent patterns (worktree isolation, sub-agent instruction passing, cross-agent state sync) are still evolving.
5. **Progress files shifting from Markdown to JSON** — Anthropic evidence shows agents have 60% lower accidental overwrite rate on structured JSON vs Markdown. Structured format becoming best practice.

## Known Pitfalls

1. **Stop Hook infinite loop** — Check failure in a Stop hook prevents the agent from stopping; retries trigger the Stop hook again. Solution: Stop hooks **must** check `stop_hook_active`; on second trigger, pass through directly.
2. **CLAUDE.md signal dilution** — Exceeding 200 lines causes key rules to be ignored; more rules = lower compliance rate. Solution: periodic audit; remove rules the model now follows naturally.
3. **Hook and CI redundant verification** — PreToolUse hooks that fully duplicate CI slow the dev loop without adding safety. Solution: hooks do fast local checks only (formatting, basic lint); full testing in CI.
4. **Cross-session progress loss** — Relying on agent memory rather than persistent progress files means new sessions repeat completed work. Solution: enforce JSON progress files; write commit hashes as checkpoints after each phase.

## Harness Engineering Checklist

- [ ] Project root has a CLAUDE.md
- [ ] Contains build/test/lint commands
- [ ] Coding conventions documented (core only)
- [ ] Pre-commit hook enforcing test pass
- [ ] Auto-format on file writes
- [ ] Architectural constraints documented with rationale
- [ ] Progress file for multi-session tasks
- [ ] Every CLAUDE.md rule traces to a real agent failure
- [ ] CLAUDE.md under 200 lines (under 60 for small projects)
- [ ] Periodic harness simplification review
- [ ] Skill feedback log in active use

## Further Reading

| Topic | Resource |
|-------|---------|
| Seven-layer harness component implementation | [`references/components.md`](references/components.md) |
| Hook complete reference (CC / Python / Rust recipes) | [`references/hooks.md`](references/hooks.md) |
| Real project CLAUDE.md examples | [`references/examples.md`](references/examples.md) |
| Agent failure pattern diagnosis | [`references/diagnostics.md`](references/diagnostics.md) |
| Team / multi-agent / AI product harnesses | [`references/advanced.md`](references/advanced.md) |
| Seven-layer cross-agent comparison | [`references/seven-layer-comparison.md`](references/seven-layer-comparison.md) |
| Context layering and Prompt Cache | `/agentforge-context` |
| Sub-agent permissions and worker isolation | `/agentforge-multiagent` |
| Loop detection and sandbox constraints | `/agentforge-security` |

## Reverse Audit (Diagnose Mode)

> Called by `/agentforge-diagnose` — D6 Harness dimension static audit.

| # | Check | How | Pass Criteria |
|---|-----------|-----|---------------|
| H1 | CLAUDE.md/AGENTS.md exists | `ls CLAUDE.md AGENTS.md 2>/dev/null` | Agent context config in root |
| H2 | Test pre-commit gate | `cat .claude/settings.json \| grep -A5 "PreToolUse"` or CI config | Pre-commit hook or CI runs tests before commit |
| H3 | Progress tracking | `find . -name "progress*.json" -o -name "PROGRESS.md"` | Multi-session project has a progress file |
| H4 | Build verification | `cat .github/workflows/*.yml \| grep -A3 "run:"` | CI runs build + lint; failures block merge |
| H5 | CLAUDE.md rules traceable | Read CLAUDE.md; trace each rule to a source | No speculative rules with unknown origins (Bitter Lesson check) |

**High-probability issues**: No CLAUDE.md (P2 — agent has no context config); no test pre-commit gate (P1 — can commit broken code); CLAUDE.md exceeds 200 lines (P2 — rule dilution).
