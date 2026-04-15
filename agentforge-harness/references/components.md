# Harness Components: Detailed Implementation Guide

## 1. Context Engineering — What the Agent Sees

### CLAUDE.md Hierarchy

Claude Code loads CLAUDE.md files hierarchically. Use this for progressive disclosure:

- **Global** (`~/.claude/CLAUDE.md`): Personal preferences that apply everywhere (language, style)
- **Project root** (`/project/CLAUDE.md`): Build commands, architecture, project-wide rules
- **Sub-directory** (`/project/src/CLAUDE.md`): Domain-specific rules loaded only when agent enters that directory

### Key Principles

**Map, not manual.** OpenAI's lesson: a short CLAUDE.md (~100 lines) pointing to deeper docs outperforms a monolithic instruction file. The CLAUDE.md is a table of contents. Detailed specs live in the codebase itself (READMEs, design docs, type definitions).

**Earn every line.** Each rule should trace to a real agent failure. If you can't name the failure a rule prevents, the rule probably shouldn't exist.

**Machine-readable over human-readable.** Agents parse structured formats better. Prefer:
```markdown
## Import Rules
- NEVER import from `src/infrastructure/` in `src/domain/`
- ALWAYS use path aliases: `@/components/` not `../../components/`
```
Over vague guidance like "keep imports clean."

### Progressive Disclosure with Skills

If your project has specialized domains, consider organizing knowledge as skill-like subdirectories with their own CLAUDE.md files. The agent only loads context when it enters that domain.

## 2. Tool Orchestration — What the Agent Can Do

### The "Less is More" Principle

Empirical finding: Vercel removed 80% of their agent's tools and got better results. More tools means more decision surface, more token waste, and more confused tool selection.

Guidelines:
- If a CLI tool exists in training data (git, npm, docker, grep, jq), prefer it over an MCP server
- If an MCP server duplicates CLI functionality, remove the MCP server
- Only add tools when the agent demonstrably lacks a needed capability

### Sub-Agents for Context Isolation

Sub-agents work best as context firewalls, not role players:

**Good pattern:**
```
Main agent → spawns sub-agent for "research how pagination works in this codebase"
           → sub-agent returns summary
           → main agent continues with clean context
```

**Bad pattern:**
```
Main agent → spawns "frontend engineer" sub-agent
           → spawns "backend engineer" sub-agent
           → tries to coordinate
           → tool thrash, worse results
```

Sub-agents prevent intermediate noise (file contents, error messages, debugging output) from contaminating the orchestration thread.

### Iterative Retrieval for Subagent Context

Subagents spawned with "here's the task, figure it out" fail because they can't predict what context they need. Send everything = token overflow. Send nothing = hallucination. Send guesses = usually wrong terms for this codebase.

Pattern: progressive refinement loop, max 3 cycles.

1. **DISPATCH** — broad initial query (patterns + keywords + excludes)
2. **EVALUATE** — score each retrieved item 0-1 for relevance to task:
   - 0.8-1.0: directly implements target functionality
   - 0.5-0.7: contains related patterns or types
   - 0.2-0.4: tangentially related
   - 0-0.2: exclude
3. **REFINE** — drop < 0.2; add newly discovered terms/paths to next query
4. **LOOP** — exit when ≥ 3 items score > 0.7 without critical gaps

Enforce the scoring protocol at the harness level: subagents MUST return relevance scores with findings. If a subagent's return lacks scores, a hook or the main agent's validation step rejects it and requests a re-run.

Why this belongs in harness engineering: "agents hallucinate" (First Principle #4) and "context rots" (#2) both degrade when subagents operate without feedback on their own retrieval quality. Scoring turns an open-ended "go find stuff" into a measurable process with a termination condition.

Reference: ECC's `skills/iterative-retrieval/SKILL.md` for full pseudocode and two worked examples (bug fix, feature implementation with terminology mismatch).

## 3. Memory & State — What Persists

### Progress File Pattern

For multi-session work, maintain a structured progress file. **Use JSON rather than Markdown** — Anthropic found that agents are less likely to inappropriately modify JSON files:

```json
{
  "goal": "Build e-commerce checkout system",
  "completed": [
    {"id": 1, "name": "Product catalog API", "status": "done", "commit": "abc123"},
    {"id": 2, "name": "Shopping cart", "status": "done", "commit": "def456"}
  ],
  "current": {
    "id": 3,
    "name": "Payment integration",
    "status": "in_progress",
    "done": "Stripe webhook endpoint",
    "next": "Implement checkout flow UI"
  },
  "architecture_decisions": [
    {"decision": "Use Stripe Elements for PCI compliance", "date": "2026-03-20"}
  ],
  "known_issues": [
    "Cart total calculation rounds incorrectly for 3+ decimal currencies"
  ]
}
```

### Git as External Memory

The commit history is a powerful form of external memory. Encourage atomic commits with descriptive messages. The agent can read git log to reconstruct context for a new session.

## 4. Architectural Constraints — What the Agent Cannot Do

### Why Constraints Help

Counterintuitively, constraining the solution space makes agents more productive. When an agent can generate anything, it wastes tokens exploring dead ends. When the harness defines clear boundaries, the agent converges faster.

### Encoding Constraints

Three levels of enforcement, from weakest to strongest:

1. **Documentation** (CLAUDE.md rules) — Agent may ignore under pressure
2. **Linter rules** — Mechanical, catches violations at commit time
3. **Structural tests** — Fail the build if architecture is violated

Always prefer stronger enforcement when possible. A lint rule is worth more than a paragraph of explanation.

### Linter Error Messages as Instructions

Write linter error messages so the agent can self-correct:

**Bad:** `Error: Invalid import`
**Good:** `Error: src/domain/User.ts imports from src/infrastructure/. Domain layer must not depend on infrastructure. Use a repository interface in src/domain/interfaces/ instead.`

The error message becomes the remediation instruction.

### Risk-Scored Constraints (Continuous, Not Binary)

Beyond binary allow/block rules, harnesses can score risk continuously and route to graduated responses:

- **Allow** (score < 0.3): proceed silently
- **Review** (0.3-0.6): log and surface to user but don't block
- **Confirm** (0.6-0.85): require explicit user approval
- **Block** (> 0.85): refuse execution

Compose the score from orthogonal axes that sum to 0-1:

1. **Base tool risk** — Bash (0.20) > Write/MultiEdit (0.15) > Edit (0.10) > others (0.05)
2. **File sensitivity** — secrets/credentials (+0.25); shared infra like Dockerfile, migrations, production configs (+0.15)
3. **Blast radius** — shared-state patterns like `git push --force origin main`, `rm -rf .` (+0.35); wide-scope patterns like `**`, `--recursive`, `--all` (+0.25)
4. **Irreversibility** — destructive like `rm -rf`, `git reset --hard`, `DROP TABLE` (+0.45); moderately irreversible like `git push -f`, `DELETE FROM` (+0.40)

Pattern source lists (copy into your hook):
- Secret: `.env`, `secret`, `credential`, `token`, `api_key`, `id_rsa`, `.pem`, `.key`
- Shared infra: `Cargo.toml`, `package.json`, `Dockerfile`, `.github/workflows`, `schema`, `migration`
- Blast radius: `**`, `/*`, `--all`, `--recursive`, `find ... xargs`, `origin main`, `rm -rf .`
- Irreversible: `rm -rf`, `git reset --hard`, `git clean -fd`, `drop database`, `drop table`, `truncate`

Implement as a PreToolUse hook: read stdin, score, print reasons, exit accordingly (0 for Allow, 0 + stderr warning for Review, 2 for Confirm/Block).

Why this matters: binary allow/block produces false positives (blocks legitimate work) or false negatives (misses combined risks). A 4-axis scalar captures "this command would be fine alone but is dangerous in this combination" — e.g., `rm -rf` alone scores 0.65 (confirm), but `rm -rf . && git push --force` scores 1.0 (block).

Complements but does not replace Dry-Run Mode (main SKILL.md): Dry-Run is tool-layer preview for API writes; risk scoring is shell-command scoring for Bash-like tools.

Reference: ECC's `ecc2/src/observability/mod.rs:60-218` provides a complete Rust implementation with tests that verify combined-risk blocking.

## 5. Verification & Feedback — How the System Self-Corrects

### Test-Before-Commit (Essential Hook)

The single most impactful harness improvement: agents cannot commit code that fails tests.

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

The matcher targets `Bash` (the tool name), then the script checks stdin to see if the bash command contains `git commit`. Exit code is captured before piping to `tail` — piping loses the original exit code.

### Build-Before-Done (Stop Hook)

Prevent the agent from declaring completion with a broken build:

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

The `stop_hook_active` check prevents infinite loops — without it, a failing build causes the agent to retry endlessly.

### The Reasoning Budget Sandwich

LangChain's finding: allocate high reasoning effort to planning and verification, standard effort to implementation. Planning and verification are where mistakes are most costly.

### Synchronous vs Asynchronous Back-Pressure

Hooks are synchronous — they fire on a specific tool use and return a verdict immediately. This covers simple checks: lint on write, test before commit, block dangerous bash.

Some verifications cannot fit a single tool use:

- "Has this session drifted from the original plan over the last hour?"
- "Are there crashed sessions from before the harness restarted?"
- "Should we auto-merge worktrees that have been clean and conflict-free for > 10 minutes?"
- "Has the agent been stuck in a retry loop across tool calls?"

These need an async daemon loop that polls on a fixed interval:

```
loop every N seconds:
  check_session_health         // mark stale/crashed
  dispatch_scheduled_tasks      // cron-like follow-ups
  coordinate_shared_resources   // auto-merge, auto-prune, conflict detection
  sleep(heartbeat_interval)
```

Key insight: polling is easier to debug and pause/resume than event-driven dispatch. For multi-agent or multi-session systems, the tick count is a natural timestamp — which is the primary requirement for time-travel debugging.

When to use which:
- **Synchronous hook** — verifying a single operation right now (build passes, no secrets leaked, test-before-commit)
- **Async daemon** — tracking drift, coordinating multiple sessions, scheduled maintenance, anything that requires comparing state across time

This complements the **Long-Running Agent Harness** pattern (main SKILL.md): that pattern handles agents that never naturally terminate (meeting assistants, monitors). This section addresses *verifications* that can't fit inside a single tool invocation — applicable even to short-lived agents in multi-session workflows.

Reference: see ECC's `ecc2/src/session/daemon.rs:20-56` for a 7-pass daemon loop that handles session checks, scheduled dispatch, remote dispatch, backlog coordination, auto-merge, auto-prune, and pending-session activation — all on a single heartbeat.

## 6. Entropy Management — Fighting Decay

### The Problem

Agent-generated code accumulates entropy differently than human code: documentation drifts, naming conventions diverge, dead code grows, patterns fragment. OpenAI's team spent 20% of each week cleaning "AI slop" before automating cleanup.

### Solutions

- **Periodic review tasks:** Regularly ask the agent to scan for inconsistencies
- **Convention enforcement:** Add lint rules for naming conventions, file organization
- **Documentation freshness:** When modifying code, require updating related docs in the same commit
- **Architectural audits:** Periodically ask the agent to verify module boundaries are respected

Add to CLAUDE.md:
```markdown
## Maintenance Rules
- When modifying a function, update its JSDoc/docstring in the same commit
- When adding a new module, update the Architecture section of this file
- When adding a new dependency, document why in the commit message
```

## 7. Human-in-the-Loop — When Humans Intervene

### Default to Conservative

Start with the agent asking for approval on:
- Any destructive operation (file deletion, database changes)
- External API calls (especially authenticated ones)
- Operations that can't be undone

Relax controls as you build confidence in specific categories.

### Code Review Remains Essential

AI-authored code has been found to contain more logic errors and security vulnerabilities than human-written code. The harness handles mechanical quality; humans handle judgment, taste, and security review.

### The Right Intervention Points

- **Before execution:** Planning review (approve the approach before implementation)
- **After execution:** Code review (approve the result before merge)
- **At boundaries:** When the agent needs to make architectural decisions with long-term implications
