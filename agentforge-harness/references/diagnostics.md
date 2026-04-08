# Agent Failure Diagnostics Guide

When Claude Code isn't performing well, use this guide to diagnose and fix the root cause.

## Symptom → Diagnosis → Fix

### "Agent keeps making the same mistake"

**Diagnosis:** Missing constraint in CLAUDE.md or missing mechanical enforcement.

**Fix options (weakest to strongest):**
1. Add explicit rule to CLAUDE.md with example of correct behavior
2. Add a linter rule that catches the pattern
3. Add a hook that blocks the action unless conditions are met

If option 1 doesn't work after 2-3 attempts, escalate to option 2 or 3. Repeated prompt-based fixes for the same problem indicate a need for mechanical enforcement.

### "Agent tries to do too much at once / one-shots everything"

**Diagnosis:** Task is too large for a single context window. Agent lacks decomposition guidance.

**Fix:**
- Break the task into explicit subtasks before starting
- Use plan mode (Shift+Tab ×2 or `/plan`) to review and approve the plan first
- Add to CLAUDE.md: "For features with more than 3 files, create a plan listing all files to modify before writing any code."
- For very large tasks, use the initializer pattern: first session creates a feature list / progress tracker, subsequent sessions work one feature at a time

### "Agent loses context in long sessions"

**Diagnosis:** Context rot. The context window has filled with intermediate outputs that dilute the original instructions.

**Fix:**
- Use `/compact` after completing each logical unit of work
- Use `/clear` when switching between unrelated tasks
- Move detailed instructions into sub-directory CLAUDE.md files (only loaded when needed)
- For multi-session projects, maintain a progress file that summarizes state

### "Agent commits code that doesn't compile / breaks tests"

**Diagnosis:** Missing verification hooks.

**Fix:**
Add PreToolUse hooks that match `Bash` and check for `git commit` in stdin:
```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "INPUT=$(cat); CMD=$(echo \"$INPUT\" | jq -r '.tool_input.command // empty'); echo \"$CMD\" | grep -q 'git commit' && { RESULT=$(npm run build && npm test 2>&1); RC=$?; echo \"$RESULT\" | tail -20; [ $RC -ne 0 ] && exit 2 || exit 0; } || exit 0"
      }]
    }]
  }
}
```
Add Stop hooks to verify before the agent declares done (with loop prevention):
```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "INPUT=$(cat); [ \"$(echo $INPUT | jq -r '.stop_hook_active')\" = 'true' ] && exit 0; RESULT=$(npm run build && npm test 2>&1); RC=$?; echo \"$RESULT\" | tail -20; [ $RC -ne 0 ] && exit 2 || exit 0"
      }]
    }]
  }
}
```

### "Agent creates wrong file structure / violates architecture"

**Diagnosis:** Architecture not documented or not enforced.

**Fix:**
1. Document the architecture explicitly in CLAUDE.md with allowed/forbidden import patterns
2. Add structural rules: "New files in `src/features/` must follow the pattern: `feature-name/{components,hooks,api,types}.ts`"
3. If available, add lint rules or structural tests that enforce the architecture
4. Consider adding module-level CLAUDE.md files that describe the module's role and boundaries

### "Agent generates verbose / boilerplate-heavy code"

**Diagnosis:** Missing style guidance.

**Fix:**
Add coding style preferences to CLAUDE.md:
```markdown
## Style
- Prefer concise, idiomatic code over verbose defensive code
- Use early returns to reduce nesting
- Extract reusable logic into utility functions rather than inline repetition
- Prefer composition over inheritance
```

### "Agent hallucinates APIs / uses non-existent functions"

**Diagnosis:** Agent is working from training data rather than actual codebase.

**Fix:**
1. Add to CLAUDE.md: "Before using any function or API, verify it exists by reading the source file."
2. For external libraries, specify versions in CLAUDE.md: "We use React Query v5 (useQuery, useMutation). Do NOT use v4 patterns (useQuery with onSuccess callback)."
3. Consider adding relevant type definitions or API docs as reference files

### "Agent produces inconsistent naming / formatting"

**Diagnosis:** Conventions not documented or not auto-enforced.

**Fix:**
1. Document naming conventions explicitly: "Components: PascalCase. Hooks: camelCase with `use` prefix. Files: kebab-case."
2. Add PostToolUse hook for auto-formatting (prettier, black, etc.)
3. Add lint rules for naming conventions

### "Agent works well initially but degrades over a long conversation"

**Diagnosis:** Classic context rot. Model instruction-following ability decreases as context grows.

**Fix:**
- Use `/compact` proactively every 10-15 tool calls
- Use `/clear` between distinct phases of work
- Break large tasks into separate sessions, connected by progress files
- Keep CLAUDE.md focused — remove anything the agent hasn't needed recently

### "Agent ignores rules in CLAUDE.md"

**Diagnosis:** Either the CLAUDE.md is too long (rules get diluted) or the rule is too vague.

**Fix:**
1. Shorten CLAUDE.md — remove rules that haven't been needed
2. Make rules specific and actionable: "Use `@/components/` path alias" not "Keep imports organized"
3. Move the most critical rules to the top of the file
4. For truly critical rules, enforce mechanically with hooks or linters instead of relying on the agent reading them

### "Hooks block every commit / agent is stuck in a loop"

**Diagnosis:** PreToolUse hook is failing on every invocation, or Stop hook is looping endlessly.

**Common causes and fixes:**
1. **No test suite exists** — Hook runs `npm test` or `pytest` but the project has no tests. Remove the test hook until tests are set up, or gate it: `[ -f package.json ] && npm test || exit 0`
2. **Wrong command for stack** — Hook uses `npm test` in a Python project. Match hook commands to your tech stack.
3. **Stop hook infinite loop** — Missing `stop_hook_active` check. Add: `[ "$(echo $INPUT | jq -r '.stop_hook_active')" = 'true' ] && exit 0` at the start of every Stop hook.
4. **jq not installed** — Hooks that parse stdin fail silently. Install: `brew install jq` or `apt install jq`.

**Quick fix:** Temporarily disable all hooks by adding `"disableAllHooks": true` to settings.json, then fix hooks one at a time.

## The Escalation Ladder

When a problem persists:

```
Level 1: Add/clarify a rule in CLAUDE.md
         ↓ (if still happening after 2-3 tasks)
Level 2: Add a hook for mechanical enforcement
         ↓ (if not hookable)
Level 3: Add a linter rule or structural test
         ↓ (if fundamental architecture issue)
Level 4: Restructure the project to make the wrong thing impossible
```

Each level trades flexibility for reliability. Only escalate when the lighter approach has failed.
