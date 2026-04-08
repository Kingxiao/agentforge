# 6 Automated Decision Principles Explained

> Source: gstack-autoplan decision framework, adapted for Agent construction scenarios

## Principle 1: Completeness First

**Rule**: Cover all edge cases — no "we'll add it later" gaps.

**Good examples**:
- Tool interface defines `isReadOnly()`, `isExpensive()`, `needsConfirmation()` and all other semantic methods
- Security model covers 6 layers from tool-level to container-level
- Error handling covers all scenarios: timeout, rate limit, auth failure, etc.

**Bad examples**:
- "Build core features first, add error handling later" → never gets added
- "Support one Provider first, abstract multi-Provider later" → refactoring cost is 10x when you get there

**Boundary**: Completeness ≠ over-engineering. If an edge case has < 1% probability and manageable impact, logging is acceptable over full treatment.

## Principle 2: Pragmatic Choices

**Rule**: When options are equivalent, pick the simpler one. Complexity is a cost, not a feature.

**Good examples**:
- File memory suffices → don't reach for block memory
- `grep` handles the search → don't build an AST index
- Single Agent handles the task → don't introduce multi-Agent

**Bad examples**:
- Introducing a message queue for "architectural elegance" when there's only one consumer
- Using microservices for "scalability" when there's only one service

**Boundary**: Pragmatic ≠ lazy. If a simple solution's expansion cost clearly exceeds the initial cost of a slightly more complex approach, pick the latter. Benchmark: likely need to expand within 6 months?

## Principle 3: DRY (Don't Repeat Yourself)

**Rule**: Each piece of information lives in exactly one place.

**Good examples**:
- API endpoint defined only in `.env` / config file; code references the config
- Tool schema auto-generated from code, not hand-written JSON
- Error messages defined in one place, referenced by all modules

**Bad examples**:
- Hardcoding API endpoint in test file (duplicates the config file)
- `MAX_RETRIES = 3` defined separately in multiple files

**Boundary**: Simple logic under 3 lines, even if similar, doesn't need extraction. Over-DRY is worse than moderate duplication — abstraction has its own costs.

## Principle 4: Explicit Over Implicit

**Rule**: Every decision has a traceable rationale.

**Good examples**:
- Architecture doc records "chose Async Generator because streaming output + TS ecosystem needed"
- Security decision records "chose OS-level sandbox because Agent executes untrusted code"
- Skipping a Phase? Record the reason.

**Bad examples**:
- "Using Rust because Rust is good" → not a reason
- "Default config is fine" → default isn't a reason; explain why the default fits

**Boundary**: Mechanical decisions (file format, import style) don't need long justifications — one sentence is enough. Taste decisions need reasoning. User-challenged decisions need full analysis.

## Principle 5: Bias for Action

**Rule**: Default to forward motion, not waiting. When information is insufficient: state the judgment → propose a plan → flag uncertainties.

**Good examples**:
- Provider not yet decided: "Provisional: Anthropic Claude as primary Provider (best Agent specialization), adjustable later"
- Uncertain if user needs multi-Agent: "Recommend skipping Phase 7, add if needed later"

**Bad examples**:
- "Please confirm Provider before continuing" → if Provider choice doesn't affect Phase 2 tool design, proceed anyway
- "Please confirm if XXX feature is needed" → if the answer doesn't affect the current Phase, don't block on it

**Boundary**: Decisions involving security, cost, or irreversibility cannot be "move fast and fix later." Security-related uncertainties must block progress.

## Principle 6: Conservative on Security

**Rule**: When in doubt on permissions/sandboxing, pick the stricter option.

**Good examples**:
- Unsure if sub-Agent needs file write → default to deny
- Unsure if OS-level sandbox is needed → default to enable
- Unsure if API key needs encrypted storage → default to encrypt

**Bad examples**:
- "Don't add permission controls yet, we'll add them if issues come up"
- "Test environment doesn't need security checks" (test environment security gaps get copied to production)

**Boundary**: Conservative on security ≠ security paranoid. If an Agent only reads local files and has no network access, container-level isolation isn't needed. Security measures should match the threat model.

---

## Decision Classification Flowchart

```
Encountering a decision fork
    ↓
Is there a single optimal solution?
├─ Yes → Mechanical decision → Handle automatically
└─ No ↓

Does this decision affect product direction / user experience / business model?
├─ Yes → User challenge → Human required
└─ No ↓

Is this decision based on possibly incorrect assumptions?
├─ Yes → Premise assumption → Human confirmation required
└─ No → Taste decision → Handle automatically + record rationale
```

## Automated Decision Output Format

```markdown
### Automated Decision: [Decision Name]
- **Type**: Mechanical / Taste
- **Choice**: [Selected approach]
- **Rationale**: [One sentence]
- **Principle**: [Applicable decision principle number]
- **Reversibility**: High / Medium / Low
```

## Human Intervention Request Format

```markdown
### Your Decision Needed: [Decision Name]
- **Type**: User challenge / Premise assumption
- **Context**: [Why this decision is needed]
- **Options**:
  A. [Option A] — [pros/cons]
  B. [Option B] — [pros/cons]
- **My Lean**: [if applicable]
- **Impact Scope**: [which subsequent Phases this affects]
```
