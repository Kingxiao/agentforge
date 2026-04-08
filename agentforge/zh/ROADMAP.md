# AgentForge Roadmap

## v2 Core Upgrade: Self-Evolution as a Cross-Cutting Concern

> Decision date: 2026-04-06
> Triggering insight: Self-evolution is not a "premium add-on" — it's "factory standard." AgentForge v1 treating self-evolution as a terminal Phase is a structural mistake.

### Design Principles

1. **Build for the future** — Don't base decisions on the current static reality of Agents, but lay foundations for the coming era of self-evolving Agents
2. **Principles are stable, implementations evolve** — Decision trees and architectural principles remain relatively stable, but specific tech stacks, frameworks, and concepts will shift rapidly. The value of skills lies at the principle level, not the implementation level
3. **Cross-cutting injection, not appended Phase** — Self-evolution capabilities should influence every Phase's decisions, not appended as Phase 10

### Self-Evolution Cross-Cutting Injection by Phase

| Phase | v1 View (Static) | v2 View (Self-Evolution Native) |
|-------|---|---|
| 0 Spec | "Should we build an Agent?" | + "What level of adaptive capability does this Agent need?" |
| 1 Architecture | Choose Loop paradigm | + Choose Loop supporting runtime self-modification (DGM outer loop, metacyclic interpreter pattern) |
| 2 Tools | Fixed toolset | + Dynamic tool registry + automatic tool discovery (Voyager skill synthesis) |
| 3 Context | Static prompt layering | + Automatic prompt search optimization (DSPy Compiler) + adaptive context budgeting |
| 4 Memory | Cross-session persistence | + Experience→skill elevation channel + automatic forgetting/compression (computational economics driven) |
| 5 Security | Tamper resistance | + Self-modifying code sandbox verification loop (DGM sandbox → commit/reset) |
| 6 Harness | Manual Hashimoto Loop | + Automated Hashimoto Loop (Agent observes failure → self-repairs harness) |
| 7 Multi-Agent | Coordinated execution | + Mutual training and co-evolution (SiriuS bootstrapped reasoning) + island model parallel evolution |
| 8 Ship | Package and distribute | + Self-evolving Agent version management (behavior change ≠ code change version semantics) |
| 9 Autoplan | Serial orchestration | + Evolution-aware Phase skip logic ("Does this Agent need self-evolution?" → affects entire pipeline) |

### Pre-Research: Repos to Reverse-Engineer

Already cloned to `reference-material/`:

| Repo | Paradigm | Reverse Priority | Focus |
|------|------|-----------|--------|
| **Darwin Godel Machine** (jennyzzt/dgm) | Self-modifying code → sandbox verification → selection | P0 | Outer loop architecture, sandbox design, git commit/reset decision mechanism |
| **Voyager** (MineDojo/Voyager) | Automatic skill synthesis → verification → storage | P0 | Skill representation, verification loop, skill library organization |

Pending clone:

| Repo | Paradigm | Reverse Priority | Focus |
|------|------|-----------|--------|
| **DSPy** (stanfordnlp/dspy, 33k star) | Automatic prompt search space optimization | P1 | Compiler architecture, search strategy, evaluate→optimize闭环 |
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
