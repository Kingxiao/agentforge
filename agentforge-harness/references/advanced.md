# Advanced Harness Engineering

## 1. Team Harness Collaboration

### The Shared Harness Model

A team's harness lives across three git-tracked artifacts:

```
project/
├── CLAUDE.md                    # Shared rules (git-tracked)
├── .claude/
│   ├── settings.json            # Shared hooks & permissions (git-tracked)
│   ├── settings.local.json      # Personal overrides (git-ignored)
│   ├── commands/                # Shared slash commands (git-tracked)
│   └── agents/                  # Shared sub-agents (git-tracked)
```

When a new team member clones the repo, they immediately get the full harness. No onboarding needed for the agent — the harness IS the onboarding.

### PR Review for Harness Changes

Treat CLAUDE.md modifications as seriously as API changes — they affect every team member's agent behavior.

**PR template for harness changes:**

```markdown
## Harness Change

**What failed:** [Describe the agent failure that prompted this change]
**Fix type:** [CLAUDE.md rule | Hook | Linter rule | Structural test]
**Change:** [What was added/modified/removed]
**Verified by:** [How you confirmed the fix works]
**Reversible:** [Yes/No — can this be removed if the model improves?]
```

The "What failed" field enforces the Hashimoto principle: every rule traces to a real failure. If you can't fill this field, the change is speculative and should not be merged.

### Onboarding Checklist

When a new team member joins:

1. Clone the repo — they automatically get CLAUDE.md, hooks, commands, sub-agents
2. Run `claude` in the project — the agent already knows the architecture, conventions, and build commands
3. Review `.claude/settings.json` — understand what hooks enforce and why
4. Create `.claude/settings.local.json` for personal preferences (editor integration, notification hooks)
5. Read CLAUDE.md once — the same document that guides the agent also guides the human

### Evolving the Team Harness

- **Weekly harness review:** As a team, review if any CLAUDE.md rules can be removed because the model now handles them natively, or generalized because multiple specific rules share a pattern.
- **Failure log:** Maintain a lightweight log (issue tracker or shared doc) of agent failures. This is the raw material for harness improvements.
- **Avoid harness forks:** If sub-teams add rules specific to their domain, use sub-directory CLAUDE.md files rather than adding domain-specific rules to the root file.

## 2. Multi-Agent Coordination

### Git as Inter-Agent Protocol

When multiple AI tools work on the same codebase (Claude Code, Cursor, Codex, Devin), git is the shared state layer:

```
           ┌─────────────┐
           │   Git Repo   │
           │  (source of  │
           │    truth)    │
           └──────┬───────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
┌───▼───┐   ┌────▼────┐   ┌───▼───┐
│Claude │   │ Cursor  │   │ Codex │
│ Code  │   │         │   │       │
└───────┘   └─────────┘   └───────┘
```

Rules for multi-agent coordination:

- **Atomic commits** — Each agent commits small, self-contained changes. Descriptive commit messages serve as inter-agent documentation.
- **Branch isolation** — Each agent works on its own branch. Merge conflicts are the signal that scopes overlap and need to be redesigned.
- **Feature ownership** — Assign features or modules to one agent at a time. Two agents editing the same file is a recipe for merge conflicts and logical contradictions.

### Instruction File Compatibility

Different tools read different instruction files:

| Tool | Reads | Format |
|------|-------|--------|
| Claude Code | `CLAUDE.md` | Markdown with conventions |
| Codex / OpenCode | `AGENTS.md` | Markdown with conventions |
| Cursor | `.cursorrules` | Markdown rules |
| Windsurf | `.windsurfrules` | Markdown rules |
| Any agent | `.github/copilot-instructions.md` | GitHub Copilot format |

If you use multiple tools, you have two options:

**Option A: Single source of truth.** Write CLAUDE.md as the primary file. Use a script or symbolic link to generate the others:
```bash
# In a pre-commit hook or CI step
cp CLAUDE.md AGENTS.md
cp CLAUDE.md .cursorrules
```

**Option B: Shared core + tool-specific addenda.** Keep common rules in a shared file, with tool-specific files importing or referencing it.

### CI as Universal Harness

The CI/CD pipeline is the one harness that validates ALL agents' output:

```yaml
# .github/workflows/agent-quality.yml
name: Agent Quality Gate
on: [pull_request]
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm run lint          # Convention enforcement
      - run: npm run build         # Compilation check
      - run: npm test              # Functional verification
      - run: npm run typecheck     # Type safety
```

This is agent-agnostic — it catches problems regardless of which tool produced the code. Think of CI as the "Stop hook" that works across all agents.

## 3. Non-Coding Harness Templates

Harness engineering applies to any structured task Claude Code performs, not just writing code. The same principles work: constrain, verify, iterate.

### Research & Analysis Harness

Create `research/CLAUDE.md`:

```markdown
# Research Standards

## Process
1. Define the research question explicitly before searching
2. Search 5-10 diverse sources (not just the first results)
3. Cross-verify: any key claim requires 3+ independent sources
4. Track all sources with URLs for traceability

## Output Structure
- Executive summary (3-5 sentences, conclusion first)
- Key findings (organized by theme, not by source)
- Evidence quality assessment (strong/moderate/weak for each finding)
- Contradictions and open questions (what sources disagree on)
- Source list with access dates

## Rules
- Distinguish between facts, expert opinions, and speculation
- Flag when evidence is thin: "Based on limited data..."
- Never present a single source's claim as established fact
- State confidence level explicitly: high/medium/low
```

### Translation Harness

Create `translation/CLAUDE.md`:

```markdown
# Translation Standards

## Rules
- Preserve all technical terminology with original in parentheses on first use
- Maintain paragraph structure of the original document
- Preserve all metadata: author, date, version numbers, headers
- Use target language conventions for date/number formatting
- Flag culturally-specific references that may need localization notes

## Quality Checks
- Output must have same paragraph count as input
- All proper nouns preserved unchanged
- No content added that wasn't in the original
- No content omitted without explicit [omitted: reason] marker

## Process
1. Read entire document before translating any section
2. Create terminology glossary for domain-specific terms
3. Translate section by section, maintaining cross-references
4. Review complete translation for consistency
```

### Data Analysis Harness

Create `analysis/CLAUDE.md`:

```markdown
# Data Analysis Standards

## Process
1. Examine data shape first: rows, columns, types, missing values
2. State assumptions before any analysis
3. Show intermediate results at each step
4. Validate results with sanity checks (totals, ranges, distributions)

## Rules
- Never modify the original data file — work on copies
- All charts must have labeled axes, title, and units
- Report sample sizes alongside any percentage or average
- Acknowledge limitations: selection bias, missing data, small samples
- Distinguish correlation from causation explicitly

## Output
- Summary of findings (3-5 bullet points)
- Methodology description (reproducible steps)
- Visualizations with annotations
- Raw data references (file paths, row ranges)
- Confidence assessment and caveats
```

### Content Creation Harness

Create `content/CLAUDE.md`:

```markdown
# Content Creation Standards

## Rules
- Match the specified tone and audience throughout
- Include concrete examples for every abstract claim
- Respect word count targets (±10%)
- Cite sources for factual claims
- Structure: hook → context → substance → takeaway

## Quality Checks
- Read opening paragraph: does it compel reading further?
- Read closing paragraph: does it leave a clear takeaway?
- Check every heading: does it accurately describe its section?
- Check every claim: is it supported or just asserted?
```

### Using Hooks for Non-Coding Tasks

Stop hooks work for any task — not just code builds:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "INPUT=$(cat); [ \"$(echo $INPUT | jq -r '.stop_hook_active')\" = 'true' ] && exit 0; [ -f output/report.md ] && exit 0 || { echo 'No report file found at output/report.md' >&2; exit 2; }"
          }
        ],
        "description": "Ensure report file was actually created before stopping"
      }
    ]
  }
}
```

## 4. AI Product Harness Architecture

When building a product that uses AI agents, the same seven harness layers apply — but the implementation surfaces change.

### The Product Harness Stack

```
User Request
     ↓
┌─────────────────────────────┐
│  INPUT HARNESS              │
│  - Input validation         │
│  - Intent classification    │
│  - Rate limiting            │
│  - PII detection/redaction  │
└─────────────┬───────────────┘
              ↓
┌─────────────────────────────┐
│  CONTEXT HARNESS            │
│  - RAG retrieval            │
│  - User history injection   │
│  - System prompt assembly   │
│  - Tool/capability scoping  │
└─────────────┬───────────────┘
              ↓
┌─────────────────────────────┐
│  EXECUTION HARNESS          │
│  - Model call with timeout  │
│  - Tool use constraints     │
│  - Token budget enforcement │
│  - Retry with backoff       │
└─────────────┬───────────────┘
              ↓
┌─────────────────────────────┐
│  OUTPUT HARNESS             │
│  - Format validation        │
│  - Factual spot-checks      │
│  - Safety filtering         │
│  - Confidence scoring       │
└─────────────┬───────────────┘
              ↓
┌─────────────────────────────┐
│  FEEDBACK HARNESS           │
│  - Error logging            │
│  - User feedback capture    │
│  - Trajectory recording     │
│  - Failure → constraint     │
│    (Hashimoto Loop at       │
│     product scale)          │
└─────────────────────────────┘
```

### Mapping Seven Layers to Product Scale

| Harness Layer | Claude Code Implementation | Product Implementation |
|---------------|---------------------------|----------------------|
| Context Engineering | CLAUDE.md, sub-directory files | System prompt assembly, RAG pipeline, user context injection |
| Tool Orchestration | MCP servers, CLI tools | API integrations, tool permission matrix, capability scoping per user role |
| Memory & State | Progress files, git history | Session state, user preferences, conversation history, long-term memory store |
| Architectural Constraints | Linter rules, import boundaries | Input/output schemas, API contracts, rate limits, token budgets |
| Verification & Feedback | Test-before-commit hooks | Output validators, factual checks, A/B testing, user feedback loops |
| Entropy Management | Periodic cleanup agents | Prompt drift monitoring, regression testing, documentation freshness checks |
| Human-in-the-Loop | Approval workflows | Escalation paths, human review queues, confidence-based routing |

### The Product Hashimoto Loop

At product scale, the Hashimoto Loop becomes an operational process:

```
User reports bad output
        ↓
   Log the failure (input, output, context, expected)
        ↓
   Classify: is this a prompt issue, tool issue, retrieval issue, or model limitation?
        ↓
   Fix at the appropriate layer:
     → Prompt issue → Update system prompt or few-shot examples
     → Tool issue → Fix tool definition, add validation
     → Retrieval issue → Improve RAG pipeline, add knowledge
     → Model limitation → Add output post-processing or fallback
        ↓
   Deploy fix with regression test
        ↓
   Monitor: does the fix hold? Does it create new issues?
        ↓
   Repeat
```

### Key Product Harness Principles

**Capture trajectories as a data asset.** Every agent interaction (input → actions → output → user feedback) is training data for improving the system. The harness that captures the richest trajectories has the strongest competitive moat.

**Fail gracefully, not silently.** When the agent can't complete a task, the harness should provide a useful fallback (human escalation, partial result, clear error message) rather than hallucinating an answer.

**Scope agent autonomy to risk.** Low-risk actions (formatting, summarizing) can be fully autonomous. High-risk actions (sending emails, modifying databases, financial transactions) need human approval gates. The harness enforces this classification mechanically.

**Observe everything.** Log every model call, tool use, retrieval result, and output. Without observability, you're flying blind — you can't run the Hashimoto Loop if you don't know what failed.

**Build for deletion at every layer.** As models improve, product harness components become removable — an output spell-checker becomes unnecessary when the model stops making spelling errors. Design each component to be independently removable without cascading failures.
