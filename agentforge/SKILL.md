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
  version: "2.1.0"
  last_updated: "2026-04-08"
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

## Series Navigation

Route to the correct skill based on the user's current phase:

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
→ For orchestrating existing Agents: `/dev-orchestrator`
→ For deep theory: `/multiagent-topology`, `/stigmergy-coordination`, `/collective-intelligence-design`

### Phase 8 → Packaging & Release
"How to package? How to distribute? How to configure CI/CD?"
→ **`/agentforge-ship`**
→ For Rust deployment: `/deployment-rust`
→ For cloud deployment: `/cloud-deployment`
→ For post-deployment verification: `/deploy-verifier`

### Phase 9 → Full-Process Orchestration
"One-button Phase 0→8, automatically handles mechanical decisions"
→ **`/agentforge-autoplan`**

### Phase 10 → Self-Evolution Core
"Has a runnable Agent, needs to add self-evolution capability"
→ **`/agentforge-evolution`**
→ Standalone series: `/selfevolving-agent-architecture` (20 skills)

### Phase 11 → Testing, Acceptance & Benchmarking
"How to test the Agent? How to set acceptance criteria? How does it compare to industry standards?"
→ **`/agentforge-benchmark`**

### Reverse Engineering Entry → Diagnosis & Optimization of Existing Agents
"Has an existing Agent, wants to know where problems are / why performance is poor / how to improve"
→ **`/agentforge-diagnose`**
→ Supports four modes: Mode A (static code audit) / Mode B (online Agent + symptoms) / Mode C (symptoms-only inference) / Mode D (runtime probe testing)
→ Auto-routing: `/agentforge-autoplan` also routes here when detecting "existing Agent" signals

### Deep Self-Evolution
More systematic self-evolution methodology → **`/selfevolving-agent-architecture`** (standalone series, 20 skills)

## How to Use

### When the user knows exactly what they want to do
Directly route to the corresponding Phase skill.

### When the user says "I want to build an Agent" but isn't sure where to start
Ask questions in this order:

1. **Goal**: "What problem does this Agent solve? Who uses it?"
2. **Interaction mode**: "CLI? IDE plugin? Web service? API?"
3. **Technical constraints**: "Any language preference? Existing codebase?"
4. **Security requirements**: "Can the Agent modify files? Execute commands? Does it need a sandbox?"

Route to Phase 1 (architecture selection) based on answers.

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

1. **Premature selection** — Skipping Phase 0 (requirements definition) and jumping directly to Phase 1 (architecture selection), leading to unsuitable paradigm choices. Solution: Always start with `/agentforge-spec`, even if it feels "already clear"
2. **Tool count inflation** — Installing too many tools on the Agent actually reduces performance. Vercel improved after deleting 80% of their tools. Solution: Follow `/agentforge-tools` "less is more" principle
3. **Neglecting Harness** — Spending 90% of effort tuning prompts and 0% building constraint systems makes the Agent unreliable. Solution: Phase 6 (Harness) is a required, non-skippable phase
4. **Cross-phase leakage** — Starting to write code during architecture design, resulting in rework. Solution: Strictly follow Phase sequence. Each Phase has a clear output checklist
5. **Closed-source illusion** — Designing based on Cursor/Devin's marketing because they're closed-source. Solution: This series is based only on verifiable open-source code. Closed-source Agents are only annotated for behavioral observation †

## References

- Full research report: `领域知识/multi-agents/agent-architecture-research/00-FULL-STUDY.md`
- Wave 2 deep reverse engineering report: `领域知识/multi-agents/agent-architecture-research/wave2-deep-reverse-engineering.md`
- Wave 3 tier-2 analysis report: `领域知识/multi-agents/agent-architecture-research/wave3-tier2-analysis.md`
- Horizontal comparison matrix (11 Agents × 14 dimensions): `~/.claude/skills/agentforge/references/agent-comparison-matrix.md`
- Code path index: `~/.claude/skills/agentforge/references/code-path-index.md`
- Design pattern library: `memory/agent_design_patterns.md`
- Anti-pattern library: `memory/agent_anti_patterns.md`
