---
name: agentforge-autoplan
description: AgentForge Phase 10 — full-pipeline orchestrator. Serial execution of Phase 0→9, auto-handling mechanical decisions, deferring only judgment calls to humans. Triggers when user says "build an Agent", "agentforge autoplan", "one-shot build", or "full pipeline". When the user provides repo code or an existing Agent, automatically switches to diagnosis mode and invokes agentforge-diagnose.
triggers:
  - build an agent
  - agentforge autoplan
  - one-shot build
  - agent full pipeline
  - agent autoplan
  - diagnose agent
  - audit agent code
  - review this agent
metadata:
  version: "2.1.0"
  last_updated: "2026-04-08"
  category: "agent-engineering"
---

# AgentForge Phase 10: Full-Pipeline Orchestration

> Series entry: `/agentforge` | Covers Phase 0→8 in full
> Reference: `/gstack-autoplan` (equivalent orchestrator for Web products)

## Mode Detection (Orchestrator Entry Point)

**The first step when the orchestrator starts is to determine which mode applies**, then route to the corresponding flow.

```
User input
    ↓
Detect keywords / context
    ↓
┌─────────────────────────────────────────────────────┐
│ Any of these signals → Diagnosis mode (→ /agentforge-diagnose) │
│  • Repo path / code files provided                  │
│  • "existing Agent" / "existing code" / "help me review" │
│  • "diagnose" / "audit" / "what's wrong" / "why isn't it working" │
│  • "optimize" + no "new" / "build" intent          │
├─────────────────────────────────────────────────────┤
│ These signals → Build mode (continue this skill's pipeline)    │
│  • "build" / "make one" / "new" / "from scratch"   │
│  • Agent idea description provided (but no existing code)       │
│  • "autoplan" with no attached code context        │
└─────────────────────────────────────────────────────┘
    ↓
When uncertain: ask directly "Are you building a new Agent or diagnosing an existing one?"
```

**When diagnosis mode activates**:
1. Switch to `/agentforge-diagnose` and execute according to its protocol
2. After diagnosis completes, if user wants fixes, return to the corresponding Phase in this skill to execute fixes
3. This skill's "build pipeline" does NOT run in diagnosis mode

---

## Core Understanding

Building an Agent is a 9-phase pipeline. Each phase has clear inputs and outputs. The orchestrator's job: **automatically handle mechanical decisions, only escalate genuinely judgment-heavy calls to humans.**

Not every Agent needs to run all 9 phases. The orchestrator automatically skips inapplicable phases based on the scenario.

## Orchestration Pipeline

```
Phase 0 (spec)        → Agent positioning and feasibility
    ↓ Output: Agent Spec document
Phase 1 (architecture) → Architecture selection
    ↓ Output: Loop paradigm choice (5 options) + Language + Provider plan
Phase 2 (tools)        → Tool system design
    ↓ Output: Tool interface + Concurrency strategy + MCP integration plan
Phase 3 (context)      → Context engineering
    ↓ Output: Prompt layering + Cache strategy + Compact plan
Phase 4 (memory)       → Memory system selection
    ↓ Output: Memory paradigm + Progress file + Session persistence plan
Phase 5 (security)     → Security / Sandbox / Permissions
    ↓ Output: Security layers + Approval workflow + Sandbox approach
Phase 6 (harness)      → Harness engineering
    ↓ Output: CLAUDE.md + Hook configuration + Verification loop
Phase 7 (multiagent)   → Multi-Agent coordination (optional)
    ↓ Output: Spawn mode + Communication protocol
Phase 8 (ship)         → Packaging and release
    ↓ Output: Packaging config + CI/CD + Version management
```

## Decision Division of Labor

### Users Only Decide 5 Things

When the orchestrator starts, extract these 5 items from whatever information the user has already provided. Ask about whichever is missing — don't ask anything else:

| # | User Decision | How to Ask |
|---|-------------|-----------|
| 1 | **Agent idea**: what it does | "Describe what your Agent should accomplish in 1-3 sentences." |
| 2 | **Positioning**: who uses it, where | "Who will use it? How frequently? What environment?" |
| 3 | **Initial effect expectation** | "What quality bar for v1: usable / stable / production-grade?" |
| 4 | **Budget tier** | "What's your acceptable monthly API cost range (see tier table below)? Do you need China-accessible models only?" |
| 5 | **Acceptance criteria** | "What would make you say this Agent is done? Describe it naturally." |

### All Technical Choices Are Automated

The following are **decided autonomously by the orchestrator, never asked of the user**:

| Technical Decision | Auto-Decision Basis |
|-------------------|---------------------|
| Programming language | Auto-selected by deployment scenario, performance needs, delivery speed |
| Architecture paradigm (7 Loop types) | Auto-selected by interaction pattern and trigger method |
| LLM model | Auto-matched by budget tier + China constraint |
| Framework/library selection | Auto-selected by language + scenario, simplest first |
| Memory system | Auto-selected by user count and memory importance |
| Security tier | Auto-set by usage context (personal / team / external) |
| Tool interface complexity | Auto-decided by prototype vs. production stage |
| Concurrency strategy | Auto-inferred by tool type |
| Multi-Agent | Auto-determined by task parallelizability |
| Packaging approach | Auto-selected by distribution target |

**China constraint exception**: When user mentions "China", "Mainland China", "can't use OpenAI/Claude", automatically switch to China-accessible solutions (DeepSeek / Alibaba Qwen / Baidu Qianfan) — no need to ask for specific model names.

### When You Must Ask the User: Present Experience, Not Technical Specs

When a technical choice genuinely needs user input (rare cases), **don't present technical options — present experience differences**:

```
❌ Wrong: "claude-sonnet-4-6 or claude-haiku-4-5?"
❌ Wrong: "Block Memory or File Memory?"

✅ Right:
"This task has two directions with noticeably different outcomes — your call:
  Direction A (~$10/month): Handles 85% of tasks, occasional errors on complex cases, needs occasional oversight
  Direction B (~$40/month): Handles complex tasks reliably, almost no need to monitor
  Which do you prefer?"
```

### 6 Automated Decision Principles

### 1. Completeness First
Cover all edge cases — no "we'll add it later" gaps.

**Application**: When designing tool interfaces, prefer to over-define `isReadOnly()`, `isExpensive()` and other methods rather than "implement simply first."

### 2. Pragmatic Choices
When options are equivalent, pick the simpler one. Technically achievable ≠ should do it.

**Application**: Memory system selection — if file memory suffices, don't reach for block memory.

### 3. DRY (Don't Repeat Yourself)
Each piece of information lives in exactly one place. Applies to config, constants, type definitions.

**Application**: Provider endpoint defined once in config file; code references the config.

### 4. Explicit Over Implicit
Every decision has a traceable rationale. "Default" is not a reason.

**Application**: When selecting Async Generator paradigm (from 7 options), record "because streaming output + TypeScript ecosystem needed."

### 5. Bias for Action
Default to forward motion, not waiting. When information is insufficient: state judgment → propose plan → flag uncertainties.

**Application**: Don't block the entire Phase 1 because "Provider plan isn't settled yet" — use the most likely option and continue.

### 6. Conservative on Security
When in doubt on permissions/sandboxing, pick the stricter option. Can always loosen later; security vulnerabilities are hard to recall.

**Application**: Unsure if sub-Agent needs file write permissions → default to deny.

Boundary case principle: When technical feasibility is disputed, Agent completes a draft first then human evaluates; security-related disputes escalate to human decision directly.

## Decision Classification

| Type | Definition | How It's Handled | Example |
|------|-----------|-----------------|---------|
| **Mechanical** | Has clear optimal solution | Auto-handle | File format, import style, concurrency strategy |
| **Taste** | Multiple equivalent options | Auto-handle + record rationale | Naming style, directory structure, framework choice |
| **Technical Selection** | Language/model/architecture decisions | **Auto-handle** (see technical selection table) | Language: Python/Go, model matched to budget |
| **User Challenge** | Affects product direction — the 5 user questions | Must be human-decided | Idea, positioning, effect expectation, budget, acceptance |
| **Premise Assumption** | Assumption may be wrong | Must be human-confirmed | "Assuming target users are developers" |

**Iron rule**: Orchestrator only asks user about "User Challenge" and "Premise Assumption" — never blocks on technical selections.

## Phase Skip Logic

Not every Agent needs all phases:

```
Does your Agent need multi-Agent coordination?
├─ No → Skip Phase 7 (multiagent)
└─ Yes → Execute Phase 7

Does your Agent need cross-session memory?
├─ No → Skip Phase 4 (memory)
└─ Yes → Execute Phase 4

Is your Agent user-facing?
├─ No (internal tool) → Phase 5 (security) simplified to minimal permissions
└─ Yes → Phase 5 executed in full

Does your Agent need to be distributed to others?
├─ No (self-use only) → Skip Phase 8 (ship)
└─ Yes → Execute Phase 8
```

**Non-skippable phases**: Phase 0 (spec), Phase 1 (architecture), Phase 2 (tools), Phase 6 (harness). These 4 are minimum requirements for any Agent.

## Orchestration Execution Protocol

### Startup

```
User calls /agentforge-autoplan
    ↓
Read user's existing Agent description / requirements
    ↓
Determine starting Phase:
  ├─ From scratch → Phase 0
  ├─ Spec exists → Phase 1
  ├─ Architecture exists → Phase 2
  └─ Resume mid-stream → Read progress file, resume from last checkpoint
```

### Per-Phase Execution Flow

```
1. Call corresponding /agentforge-{phase} skill
2. Collect decision points from skill output
3. Auto-handle or ask user per decision classification
4. Record all decisions to progress file
5. Verify all Phase checklist items pass
6. Output Phase summary → proceed to next Phase
```

### Progress File Format

```json
{
  "agent_name": "my-coding-agent",
  "started_at": "2026-04-06T10:00:00Z",
  "current_phase": 2,
  "phases": {
    "0": {
      "status": "completed",
      "decisions": [
        {"type": "user_challenge", "question": "Agent type?", "answer": "Coding Agent"},
        {"type": "mechanical", "question": "Interaction mode?", "answer": "CLI", "auto": true}
      ],
      "output": "spec.md"
    },
    "1": {
      "status": "completed",
      "decisions": [...],
      "output": "architecture.md"
    },
    "2": {
      "status": "in_progress",
      "decisions": [],
      "output": null
    }
  },
  "skipped_phases": [7],
  "skip_reasons": {"7": "Single Agent, no multi-Agent coordination needed"}
}
```

### Cross-Phase Context Handoff Template

**Root problem**: Each agentforge-* skill call starts with fresh context (especially in multi-session or subagent execution), not automatically inheriting previous-phase decisions. Without a structured handoff mechanism, Phase 3 might use architecture assumptions that contradict Phase 1, and Phase 5 might be unaware of which external APIs Phase 2 selected (causing security audit gaps).

**Solution**: At the end of each Phase, besides writing the progress file, output a concise "handoff summary" for the next Phase to consume by injecting into the skill call context.

**Handoff contracts per Phase**:

| Phase | Required Key Outputs | Next Phase Consumer |
|-------|---------------------|-----------------|
| 0 Spec | Agent type, deployment form, target users, processing plane, key constraints, SLA requirements | Phase 1 (architecture basis) |
| 1 Architecture | Loop paradigm (5-of-5), language, Provider, multi-channel flag | Phase 2/3/5/6 (all depend on it) |
| 2 Tools | Tool list (incl. external API call list), concurrency strategy, MCP tools | Phase 3 (context budget), Phase 5 (security audit scope) |
| 3 Context | Context window size, Prompt Cache boundary, compaction strategy | Phase 4 (memory vs. compaction boundary) |
| 4 Memory | Memory paradigm, persistence solution, multi-tenancy flag | Phase 5 (RLS requirements), Phase 7 (shared memory design) |
| 5 Security | Sandbox tier, approval workflow requirements, per-tool permission list | Phase 6 (harness hook config), Phase 8 (CI/CD gate) |
| 6 Harness | CLAUDE.md rules summary, hook config, verification commands | Phase 8 (CI integration) |
| 7 MultiAgent | Spawn mode, communication protocol, Agent count | Phase 8 (single-process vs. multi-process packaging) |

**Handoff summary format** (written to progress file `handoff_summary` field at Phase completion):

```json
{
  "phases": {
    "0": {
      "status": "completed",
      "handoff_summary": {
        "agent_type": "RAG Q&A Bot",
        "deployment_form": "Slack Bot (HTTP mode)",
        "language": "TypeScript",
        "loop_paradigm": null,
        "external_apis": ["Confluence API", "Slack Events API"],
        "data_sources": ["Confluence", "Internal Wiki"],
        "privacy_level": "internal-only",
        "sla": {"p95_latency_ms": 3000, "availability": "99.5%"},
        "key_constraints": ["Data must not leave internal network", "Enterprise intranet users only"]
      }
    },
    "1": {
      "status": "completed",
      "handoff_summary": {
        "loop_paradigm": "Async Generator",
        "language": "TypeScript",
        "provider": "Anthropic claude-sonnet-4-6",
        "multi_channel": false,
        "vector_db": "pgvector",
        "embedding_model": "text-embedding-3-small"
      }
    }
  }
}
```

> **Model ID staleness**: Examples like `claude-sonnet-4-6` (verified: 2026-04-08), `text-embedding-3-small` (verified: 2026-04-08) are for format reference only. Actual values are auto-inferred by Phase 1 architecture phase; re-verify via WebFetch if older than 90 days.

**Context injection protocol when calling next Phase skill**:

```
When calling /agentforge-{next_phase}, must prepend to prompt:

"Previous phase decisions:
- Agent type: RAG Q&A Bot (Slack Bot, HTTP mode)
- Architecture: Async Generator, TypeScript, Anthropic
- External APIs: Confluence API, Slack Events API
- Privacy: data must not leave internal network
[...remaining handoff_summary content...]

Now proceeding with Phase {N}."
```

Without this injection, the skill starts from scratch and may make decisions that contradict earlier phases (e.g., Phase 5 selects a sandbox requiring network access, but Phase 0 requires data to stay within the intranet).

### Completion Protocol

After each Phase, the orchestrator outputs one of three states:

| State | Meaning | Next Action |
|-------|---------|------------|
| `DONE` | Phase complete, no outstanding issues | Auto-proceed to next Phase |
| `DONE_WITH_CONCERNS` | Phase complete, but with risk flags | Record risks, proceed |
| `BLOCKED` | Phase cannot complete | Pause, report blocker to user |

When all Phases are complete, output the final report:
- Complete record of all decisions
- Rationale for all automated decisions
- All risk flags
- Recommended next steps

## Relationship with Other Orchestrators

| Orchestrator | Domain | Common Ground |
|--------------|--------|--------------|
| `/gstack-autoplan` | Web product full pipeline | 6 decision principles, decision classification, completion protocol |
| `/skill-orchestrator` | Consulting skill chains | Serial orchestration, progress tracking |
| `/dev-orchestrator` | Multi-Agent development | Sub-agent coordination, Git workflow |

`agentforge-autoplan` focuses on **Agent construction process**, not deployment/operations (use `/cloud-deployment`) or business processes (use `/skill-orchestrator`).

## Current State (April 2026)

1. **Agent build tooling is highly fragmented** — No unified standard from Spec to release; teams switch repeatedly between LangGraph/CrewAI/Autogen/Vercel AI SDK, each switch causes 30-50% architecture rework. The orchestrator's value is locking the decision chain and reducing mid-course pivots.
2. **"One-click Agent generation" products emerging but quality is questionable** — Wordware, Dify, Coze and other no-code Agent platforms attracted many non-technical users, but generated Agents generally fall short on error recovery, security isolation, and context management. Full-pipeline orchestrator targets professional developers seeking engineering-grade solutions.
3. **Phase skip logic increasingly important** — Practice shows 70%+ of Agent projects don't need Phase 7 (multi-Agent), 40%+ don't need Phase 8 (shipping), but almost all projects underestimate Phase 5 (security) workload. Orchestrator needs to guide security investment more proactively.
4. **Progress persistence shifting from "optional" to "required"** — Agent build cycles extending from "done in a day" to "multi-day iteration"; cross-session resume capability directly determines the orchestrator's practical usability.

## Known Pitfalls

1. **Over-automating judgment calls** — Orchestrator auto-handles "premise assumption" questions that should be user decisions in pursuit of "smooth experience," causing Agent direction to drift. Fix: Strictly enforce four-type decision classification, never auto-handle "user challenge" and "premise assumption" — better to ask once more than make a directional decision for the user.
2. **Cross-phase dependency loss** — Phase 3 (context) decisions depend on Phase 1 (architecture) output, but progress file only records final results not derivation process, causing decisions to disconnect on mid-stream resume. Fix: Progress file must record full derivation chain for each decision, including input basis and alternatives considered.
3. **Skipping a Phase ≠ zero cost** — Marking "skipped Phase 7" and jumping to Phase 8, but Phase 8's packaging strategy actually depends on "are there sub-agents" information. Fix: Skipped Phases still need minimal declarations (e.g., "no sub-agents") for downstream Phase consumption.
4. **Orchestrator itself becomes bottleneck** — Serial execution of 9 Phases means single-Phase blocking freezes the entire pipeline. Fix: Identify Phase pairs that can parallelize (e.g., Phase 4 memory and Phase 5 security in some scenarios), annotate parallel windows in the progress file.
5. **Decision fatigue causes user abandonment** — When 5+ "user challenge" questions are asked in sequence, users tend to answer randomly or quit. Fix: Merge multiple related decisions into one structured question with recommended options and rationale.

## Further Reading

| Topic | Resource |
|-------|---------|
| Phase 0: Requirements & Spec | `/agentforge-spec` |
| Phase 1: Architecture Selection | `/agentforge-architecture` |
| Phase 2: Tool System Design | `/agentforge-tools` |
| Phase 3: Context Engineering | `/agentforge-context` |
| Phase 4: Memory System | `/agentforge-memory` |
| Phase 5: Security & Permissions | `/agentforge-security` |
| Phase 6: Harness Engineering | `/agentforge-harness` |
| Phase 7: Multi-Agent Coordination | `/agentforge-multiagent` |
| Phase 8: Packaging & Release | `/agentforge-ship` |
| Phase 11: Self-Evolution | `/agentforge-evolution` |
| Phase 12: Testing, Acceptance & Benchmarking | `/agentforge-benchmark` |
| Cloud Deployment & Operations | `/cloud-deployment` |

## Orchestration Checklist

- [ ] Confirmed starting Phase (from scratch / mid-stream / resume)
- [ ] Confirmed skipped Phases and reasons
- [ ] All checklist items passed for each Phase
- [ ] All "User Challenge" decisions confirmed by user
- [ ] All "Premise Assumption" decisions confirmed by user
- [ ] Progress file kept current
- [ ] Final report includes complete decision record

## Full-Autonomous vs. Guided Mode Invocation Protocol

### Two Invocation Modes

| Mode | Trigger Phrase | Orchestration Behavior |
|------|---------------|----------------------|
| **Guided mode** (default) | "Help me design an Agent" | Asks user at every decision point; user participates throughout |
| **Full-autonomous mode** | "Execute agentforge full pipeline autonomously" | Mechanical + taste decisions auto-handled; only pauses on "user challenge" and "premise assumption" |

### Full-Autonomous Mode Execution Protocol

When user specifies full-autonomous mode, the orchestrator drives Phase-to-Phase transitions as follows:

**1. Auto-transition logic after Phase completion**

```
Current Phase outputs DONE
    ↓
Read handoff_summary from progress file (this Phase's output)
    ↓
Build injection prompt for next Phase:
  "Previous phase decisions:
   [handoff_summary content]
   Now proceeding with Phase N."
    ↓
Call /agentforge-{next_phase}, using injection prompt as context prefix
    ↓
Continue until encountering "user challenge" or "premise assumption" decision → pause and ask user
```

**2. Criteria for when to genuinely pause**

Orchestrator should interrupt and ask user only when:
- A "premise assumption" issue is discovered (e.g., "Assuming target users are developers" — this assumption may be wrong)
- A "user challenge" decision is encountered (e.g., "Agent type: RAG or Code Agent?")
- Phase status becomes `BLOCKED` (missing required input to continue)

**3. Cases where it should NOT pause** (common orchestrator over-caution)

```
❌ Wrong: "I'm about to do X — OK?"
❌ Wrong: Asking for confirmation on taste decisions (naming style, directory structure)
✓ Right: Auto-handle mechanical decisions, record rationale, report in final summary
```

### Quick Start

**Guided mode**:
```
I want to build a [describe your Agent].
```

**Full-autonomous mode**:
```
Execute agentforge full pipeline autonomously. Agent description: [describe].
Auto-handle mechanical and taste decisions; only ask when "user challenge" or "premise assumption" encountered.
```

Orchestrator starts from Phase 0, auto-transitioning between Phases per the mode.
