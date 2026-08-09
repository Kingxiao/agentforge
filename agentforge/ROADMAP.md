# AgentForge Roadmap

> Archived v2 research proposal. It is not normative skill guidance and is superseded by `series-manifest.json` plus the v3.0 phase files (2026-08-08). In particular, controlled evolution is optional Phase 11 and never grants self-modification authority.

## v2 Core Upgrade: Self-Evolution as a Cross-Cutting Concern

> Decision date: 2026-04-06
> Triggering insight: Self-evolution is not a "premium add-on" — it's "factory standard." AgentForge v1 treating self-evolution as a terminal Phase is a structural mistake.

### Design Principles

1. **Build for the future** — Don't base decisions on the current static reality of Agents, but lay foundations for the coming era of self-evolving Agents
2. **Principles are stable, implementations evolve** — Decision trees and architectural principles remain relatively stable, but specific tech stacks, frameworks, and concepts will shift rapidly. The value of skills lies at the principle level, not the implementation level
3. **Feedback is cross-cutting; mutation is not** — observability, evaluation, and rollback affect many phases. Controlled evolution remains optional Phase 11 and does not authorize automatic modification.

### Self-Evolution Cross-Cutting Injection by Phase

| Phase | v1 View (Static) | v2 View (Self-Evolution Native) |
|-------|---|---|
| 0 Spec | "Should we build an Agent?" | + "What level of adaptive capability does this Agent need?" |
| 1 Architecture | Choose Loop paradigm | + Preserve explicit evaluation and rollback boundaries for future controlled experiments |
| 2 Tools | Fixed toolset | + Consider a versioned tool registry only when measured adaptation needs justify it |
| 3 Context | Static prompt layering | + Automatic prompt search space optimization (DSPy Compiler) + adaptive context budgeting |
| 4 Memory | Cross-session persistence | + Experience→skill elevation channel + automatic forgetting/compression (computational economics driven) |
| 5 Security | Tamper resistance | + Isolate candidate experiments; promotion and rollback follow authorized host workflows |
| 6 Harness | Manual Hashimoto Loop | + Automated Hashimoto Loop (Agent observes failure → self-repairs harness) |
| 7 Multi-Agent | Coordinated execution | + Mutual training and co-evolution (SiriuS bootstrapped reasoning) + island model parallel evolution |
| 8 Ship | Package and distribute | + Self-evolving Agent version management (behavior change ≠ code change version semantics) |
| 9 Production | Runtime operation | + Monitor drift and retain reversible rollout evidence |
| 10 Autoplan | Serial orchestration | + Ask whether controlled evolution is applicable; default to N/A without evidence and authorization |
| 11 Evolution | Optional experiments | + Propose, isolate, evaluate, approve, promote or discard |
| 12 Benchmark | Acceptance | + Held-out regression and non-inferiority gates for any candidate change |

### Pre-Research: Repos to Reverse-Engineer

Already cloned to `reference-material/`:

| Repo | Paradigm | Reverse Priority | Focus |
|------|------|-----------|--------|
| **Darwin Godel Machine** (jennyzzt/dgm) | Self-modifying code → sandbox verification → selection | P0 | Outer loop architecture, sandbox design, git commit/reset decision mechanism |
| **Voyager** (MineDojo/Voyager) | Automatic skill synthesis → verification → storage | P0 | Skill representation, verification loop, skill library organization |

Pending clone:

| Repo | Paradigm | Reverse Priority | Focus |
|------|------|-----------|--------|
| **DSPy** (stanfordnlp/dspy, 33k star) | Automatic prompt search space optimization | P1 | Compiler architecture, search strategy, evaluate→optimize closed loop |
| **AgentEvolver** (modelscope/AgentEvolver, 1.3k star) | System-level self-evolution (prompt+tools+reasoning chain) | P1 | RL signal driving, multi-layer optimization objectives |
| **SiriuS** (zou-group/sirius) | Multi-Agent mutual training bootstrapped reasoning | P2 | Cross-Agent knowledge transfer mechanism |
| **SCOPE** (JarvisPei/SCOPE) | Evolutionary algorithm optimizing prompts | P2 | Mutation/crossover/fitness in prompt space implementation |
| **recursive-improve** (kayba-ai/recursive-improve) | Lightweight recursive self-improvement | P3 | Minimal viable self-improvement loop, fast integration reference |

### Execution Plan

**Phase 1: Reverse Engineering Research** (waiting for user trigger)
- Deep-reverse DGM + Voyager → extract actionable self-evolution patterns
- Clone + shallow-read DSPy / AgentEvolver / SiriuS
- Deliverable: Self-evolution Pattern Library (format similar to agent_design_patterns.md)

**Phase 2: Injection Design**
- For each agentforge Phase, design specific self-evolution cross-cutting injection content
- Determine which are principle-level (stable) vs implementation-level (variable)
- Determine which selfevolving-* skill content should be elevated into agentforge Phases
- Deliverable: v2 diff for each Phase

**Phase 3: Execution Upgrade**
- Update SKILL.md + references for each Phase
- Reposition selfevolving series: from "self-evolution getting started" to "extreme scenario deep reference"
- Update navigator routing

### Principles Memo

- **Don't wait for reverse-engineering to finish before planning, but don't start implementation until it's done** — speculative rules are an anti-pattern
- **Principles > Implementation** — skills teach "why choose this direction" and "how to judge," not "which framework to use"
- **Building for the future ≠ predicting the future** — laying interfaces for change, not prematurely implementing hypothetical features
- **Reference sources will continue expanding** — the list above is not a closed set; add excellent new repos as they appear
