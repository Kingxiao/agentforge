---
name: agentforge
description: The single entry point for building top-tier AI Agents. Determine the user's current phase and route to the correct skill in the agentforge-* series. Triggered when user says "build an Agent", "create an Agent", "Agent architecture", or "develop an Agent". Also supports diagnosis, audit, and optimization of existing Agents.
triggers:
  - build an agent
  - create an agent
  - agent architecture
  - agent framework
  - develop an agent
  - agent development
  - diagnose an agent
  - audit an agent
  - optimize an existing agent
metadata:
  version: "2.2.0"
  last_updated: "2026-04-12"
  category: "agent-engineering"
---

# AgentForge — Engineering Series for Building Top-Tier AI Agents

> Extracted through source-level reverse engineering of 11 production-grade Agents (Claude Code / Codex CLI / OpenCode / Aider / Cline / OpenClaw / OpenHands / Goose / Letta / MemU / Cursor).
> Knowledge source: `领域知识/multi-agents/agent-architecture-research/`

## Core Formula

**Agent = LLM + Tool Loop + State + Constraints**

- **LLM**: Reasoning engine (decides "what to do" and "how to do it")
- **Tool Loop**: Execution loop (converts decisions into world-state changes)
- **State**: Memory and context (ensures each step's decisions are based on historical information)
- **Constraints**: Constraint system (prevents Agent from causing damage)

## Framing: The Autonomy Slider, Not the "Year of Agents"

> Source: Andrej Karpathy — ["2025 LLM Year in Review"](https://karpathy.bearblog.dev/year-in-review-2025/) and related 2025–2026 talks (verified 2026-04-12).

Before choosing any phase below, internalize Karpathy's framing. Two quotes:

1. **"When I see things like 'oh 2025 is the year of agents' I get very concerned… this is the decade of agents."** — Agents are a 10-year build-out, not a 2025 product launch. Your agentforge decisions should be made with a decade horizon, not a quarter.
2. **"An autonomy slider that lets the human decide how much control to cede to the AI."** — Agent autonomy is not a boolean. It's a spectrum.

### The Autonomy Slider (Tesla Analogy)

Karpathy draws on his Tesla experience: **basic assistance → lane keeping → navigate-on-autopilot → FSD supervised**. Each level **delivers value on its own** and becomes the foundation for the next. The mistake is jumping to FSD without lane keeping working.

Apply the same to agents:

| Level | Agent analogue | User's cognitive load | Example |
|---|---|---|---|
| **0 — Suggestion** | AI suggests, human types | Very high | Autocomplete, inline hints |
| **1 — Augmented LLM** | Single LLM call + retrieval + tools; human approves each action | High | Cursor tab, Copilot chat |
| **2 — Workflow** | Predefined code path orchestrates LLM calls; human supervises outcomes | Medium | Prompt chaining, routing, evaluator-optimizer |
| **3 — Scoped agent loop** | LLM directs its own loop within a narrow domain; human approves consequential actions | Low–Medium | Claude Code in a repo, Aider, Codex CLI |
| **4 — Supervised autonomy** | Agent runs multi-hour tasks, human reviews output + rare interruptions | Low (review-only) | Devin-style task agents, background research agents |
| **5 — Full autonomy** | Agent operates with minimal oversight over open-ended goals | Minimal (exception only) | Not production-ready in 2026 per Karpathy; aspirational |

### Decision axis for Phase 0

For any agent project, **two orthogonal questions** must be answered **before** you pick a loop paradigm:

1. **What's the minimum autonomy level that delivers user value?** — Start one level lower than feels necessary. Each level has 3–10× the engineering cost of the one below it.
2. **Can the current model reliably achieve that level in your domain?** — If not, ship the level below and let the next model release upgrade you.

**Karpathy's timeline (verified 2026-04-12)**:
- **2025–2026**: Stronger code/ops copilots + early robust UI-control (we are here).
- **2027–2029**: Memory adapters + autonomy sliders reaching 70–90% on scoped workflows.
- **2030–2035**: Broad enterprise-grade agent platforms with measurable SLAs.

**Implication**: if you are building an agent in 2026 aimed at Level 4+ autonomy, you are building a research artifact, not a product. Ship Level 2–3 first.

### Why this framing is the most important thing in the series

Every subsequent phase (architecture, tools, context, memory, …) is a **downstream consequence** of your autonomy-level target. A Level 1 augmented LLM doesn't need Phase 7 multi-agent or Phase 11 self-evolution. A Level 4 supervised autonomy agent needs **every** phase. Picking the wrong level is the root cause of the **1-in-10 production arrival rate** documented in agentforge-spec.

**Iron rule**: your autonomy-level target is the single largest determinant of engineering cost and schedule. Set it deliberately, defend it against scope creep, revisit it whenever the underlying model family changes.

## Series Navigation

Route to at most one phase skill based on the user's current question. Do not
preload the series, chain phases, or force a workshop when the host can answer
the scoped question directly. Phase skills are explicit/router-only and never
expand authorization for file, network, sub-agent, release, or deployment work.

### Phase 0 → Requirements Definition
"What Agent am I building? For whom? What problem does it solve?"
→ **`/agentforge-spec`**
→ For broader AI product judgment: `/ai-product-manager`

### Phase 1 → Architecture Selection
"Which loop paradigm? What language? What Provider?"
→ **`/agentforge-architecture`**
→ When cognitive theory depth is needed: `/cognitive-architecture`

### Phase 2 → Tool System
"How to design the tool interface? Concurrency strategy? How to integrate MCP?"
→ **`/agentforge-tools`**
→ When building MCP servers: `/mcp-builder`

### Phase 3 → Context Engineering
"How to layer system prompts? How to use Prompt Cache? How to compress?"
→ **`/agentforge-context`**
→ For prompt optimization: `/prompt-optimizer`

### Phase 4 → Memory System
"How to persist across sessions? Which memory paradigm? How to design progress files?"
→ **`/agentforge-memory`**
→ For underlying principles: `/llm-agent-memory`, `/agent-episodic-memory`, `/agent-semantic-memory`

### Phase 5 → Security & Sandbox
"How to design permissions? Is OS sandbox needed? How to do approval flows?"
→ **`/agentforge-security`**
→ For OWASP/STRIDE audit: `/security-auditor`

### Phase 6 → Harness Engineering
"How to configure Hooks? How to write CLAUDE.md? How to auto-verify?"
→ **`/agentforge-harness`**

### Phase 7 → Multi-Agent Coordination
"How to spawn Sub-agents? Communication protocol? Git collaboration?"
→ **`/agentforge-multiagent`**
→ For orchestrating existing agents, use the host's native sub-agent and worktree controls.
→ For deep theory: `/multiagent-topology`, `/stigmergy-coordination`, `/collective-intelligence-design`

### Phase 8 → Packaging & Release
"How to package? How to distribute? How to configure CI/CD?"
→ **`/agentforge-ship`**
→ For Rust deployment: `/deployment-rust`
→ For cloud deployment: `/cloud-deployment`
→ For post-deployment verification: `/deploy-verifier`

### Phase 9 → Production Runtime
"Agent deployed as a service — how to keep it alive, scale it, recover from failures?"
→ **`/agentforge-production`**
→ Skip if Agent is CLI-only (no service runtime needed)
→ Covers: Brain/Hands/Session decoupling, lazy provisioning, credential isolation, observability, scaling

### Phase 10 → Full-Process Orchestration
"Run the complete AgentForge Phase 0→9 pipeline" (explicit opt-in only)
→ **`/agentforge-autoplan`**

### Phase 11 → Self-Evolution Core
"Has a runnable Agent, needs to add self-evolution capability"
→ **`/agentforge-evolution`**
→ Standalone series: `/selfevolving-agent-architecture` (20 skills)

### Phase 12 → Testing, Acceptance & Benchmarking
"How to test the Agent? How to set acceptance criteria? How does it compare to industry standards?"
→ **`/agentforge-benchmark`**

### Reverse Engineering Entry → Diagnosis & Optimization of Existing Agents
"Has an existing Agent, wants to know where problems are / why performance is poor / how to improve"
→ **`/agentforge-diagnose`**
→ Supports four modes: Mode A (static code audit) / Mode B (online Agent + symptoms) / Mode C (symptoms-only inference) / Mode D (runtime probe testing)
→ Route here only when the user explicitly requests AgentForge diagnosis.

### Deep Self-Evolution
More systematic self-evolution methodology → **`/selfevolving-agent-architecture`** (standalone series, 20 skills)

## Phase Applicability by Agent Type (Quick Skip Guide)

> Added 2026-04-11. Not every Agent type needs every Phase. Use this matrix to skip irrelevant Phases and focus effort.

| Phase | Coding Agent | Webhook Agent | Research Agent | Data Agent | GUI/Browser Agent | Voice Agent | Personal Agent |
|-------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **P0 Spec** | MUST | MUST | MUST | MUST | MUST | MUST | MUST |
| **P1 Architecture** | MUST | MUST | MUST | MUST | MUST | MUST | MUST |
| **P2 Tools** | MUST | light | MUST | MUST | MUST | light | light |
| **P3 Context** | MUST | skip | MUST | light | MUST | light | MUST |
| **P4 Memory** | light | skip | light | skip | skip | skip | MUST |
| **P5 Security** | MUST | MUST | light | MUST | MUST | light | light |
| **P6 Harness** | MUST | light | light | light | light | light | light |
| **P7 MultiAgent** | optional | skip | optional | skip | skip | skip | skip |
| **P8 Ship** | MUST | MUST | MUST | MUST | MUST | MUST | MUST |
| **P9 Production** | skip (CLI) | MUST | skip | optional | skip | MUST | optional |
| **P10 Autoplan** | optional | optional | optional | optional | optional | optional | optional |
| **P11 Evolution** | optional | skip | optional | skip | skip | skip | optional |
| **P12 Benchmark** | MUST | light | MUST | light | light | light | light |

**Legend**: MUST = core phase, don't skip | light = skim for relevant decisions only | skip = not applicable | optional = only if needed

**Type-specific Phase guidance gaps** (known, to be addressed in future updates):
- **Research Agent**: P3 lacks hallucination-rate control quantitative baselines
- **Data Agent**: P5 lacks Agent-specific SQL injection guidance (differs from web app SQL injection)
- **Voice Agent**: P1 Realtime API pricing needs update (now billed per audio second, not per token)
- **GUI/Browser Agent**: P0 lacks screenshot vs CDP cost comparison at Practical budget tier

## How to Use

### When the user knows exactly what they want to do
Answer directly unless the user named AgentForge or the phase skill provides a
specific decision artifact that materially improves the task. If so, load only
the corresponding phase skill.

### When the user says "I want to build an Agent" but isn't sure where to start
Ask questions in this order:

1. **Goal**: "What problem does this Agent solve? Who uses it?"
2. **Interaction mode**: "CLI? IDE plugin? Web service? API?"
3. **Technical constraints**: "Any language preference? Existing codebase?"
4. **Security requirements**: "Can the Agent modify files? Execute commands? Does it need a sandbox?"

Use the smallest sufficient response. Route to Phase 1 only if an architecture
decision remains and the AgentForge workflow is actually desired.

### When the user encounters a specific problem during the build process
Identify which Phase the problem belongs to and route to the corresponding skill.

## Series Design Principles

1. **Each skill solves only one phase's decisions** — no cross-phase contamination
2. **Routing over duplication** — agentforge-* skills don't replicate existing skill content; they route to them when needed
3. **Decision tree driven** — each skill starts with a selection decision tree, not theoretical explanation
4. **Evidence driven** — every recommendation is annotated with source Agents ([CC]=Claude Code, [CX]=Codex, [OC]=OpenCode, [AD]=Aider, [CL]=Cline, [OW]=OpenClaw, [OH]=OpenHands, [GS]=Goose, [LT]=Letta, [MU]=MemU, [CR]=Cursor)
5. **Bitter Lesson compatible** — annotations indicate which patterns may become obsolete with model upgrades

## Current State (April 2026)

- **Agent framework explosion**: Between 2025-2026, mainstream open-source Agents grew from 3-4 to 11+, with competition shifting from "what it can do" to "how good are the constraints" (security/sandbox/observability)
- **Harness > Model**: LangChain improved from 52.8% to 66.5% (Terminal Bench 2.0) by just improving Harness — validating that "models are commodities, constraints are leverage"
- **MCP becoming standard**: Model Context Protocol adopted by Claude Code / OpenCode / Cline / Goose, etc. Tool integration no longer requires custom adapters
- **Agent OS concept emerging**: OpenClaw shifting from IDE extension positioning to multi-channel gateway + plugin system, marking Agent's transition from tool to platform
- **Reverse entry `/agentforge-diagnose`**: Supports static code audit, runtime probe testing (L2/L3 standard probe library), and merged static/dynamic analysis of existing Agents

## Known Pitfalls

1. **Premature selection** — Choosing architecture before key constraints are known. Ask only the missing questions that change the decision; do not force Phase 0 when the context is already sufficient.
2. **Tool count inflation** — Installing too many tools on the Agent actually reduces performance. Vercel improved after deleting 80% of their tools. Solution: Follow `/agentforge-tools` "less is more" principle
3. **Neglecting Harness** — Underinvesting in verification and constraints can make an Agent unreliable. Apply only the harness work justified by observed failure modes; it is not automatically a mandatory phase.
4. **Process inflation** — Running every phase for a small, well-scoped Agent wastes context and delays feedback. Skip phases with no decision to make and validate early with code or tests when appropriate.
5. **Closed-source illusion** — Designing based on Cursor/Devin's marketing because they're closed-source. Solution: This series is based only on verifiable open-source code. Closed-source Agents are only annotated for behavioral observation †

## References

- Full research report: `领域知识/multi-agents/agent-architecture-research/00-FULL-STUDY.md`
- Wave 2 deep reverse engineering report: `领域知识/multi-agents/agent-architecture-research/wave2-deep-reverse-engineering.md`
- Wave 3 tier-2 analysis report: `领域知识/multi-agents/agent-architecture-research/wave3-tier2-analysis.md`
- Horizontal comparison matrix (11 Agents × 14 dimensions): `~/.claude/skills/agentforge/references/agent-comparison-matrix.md`
- Code path index: `~/.claude/skills/agentforge/references/code-path-index.md`
- Design pattern library: `memory/agent_design_patterns.md`
- Anti-pattern library: `memory/agent_anti_patterns.md`
