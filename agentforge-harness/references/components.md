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
