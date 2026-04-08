# agentforge

**An AI skill series for engineering production AI agents.**  
Invoke `/agentforge`. The AI handles the rest — from spec to self-evolution.

---

## What This Is

agentforge is a 14-skill series. Each skill is a structured methodology loaded into an AI agent. When you invoke `/agentforge-spec`, the AI runs a proven engineering process — not a guess — extracted from reverse-engineering 11 production agents:

> Claude Code · Codex CLI · OpenCode · Aider · Cline · OpenClaw · OpenHands · Goose · Letta · MemU · Cursor

The result: agents that ship, don't hallucinate their own APIs, and recover from failures instead of silently drifting.

---

## Why This Exists

The model is not why your agent fails. The harness is.

LangChain improved from **52.8% → 66.5%** on Terminal Bench 2.0 with zero model changes — only harness changes. Five structural reasons agents fail in production:

1. **Context windows fill** — unmanaged context causes performance collapse before the task ends
2. **Context rots** — even within limits, model quality degrades as input grows
3. **Agents are stateless** — no memory between sessions unless the harness provides it
4. **Agents hallucinate** — APIs, file paths, function signatures fabricated with confidence
5. **Agents skip verification** — declare victory with failing tests unless mechanically blocked

agentforge is the systematic answer to all five.

---

## The 11-Phase Framework

```
Phase 0  → agentforge-spec          Should you build this Agent at all?
Phase 1  → agentforge-architecture  Loop paradigm, tool dispatch, state model
Phase 2  → agentforge-tools         Tool design, MCP integration, concurrency
Phase 3  → agentforge-context       Context budgets, compression, prompt variants
Phase 4  → agentforge-memory        Episodic / semantic / procedural memory
Phase 5  → agentforge-security      6-layer security model, sandbox, permissions
Phase 6  → agentforge-harness       Hashimoto Loop, hooks, constraint engineering
Phase 7  → agentforge-multiagent    Orchestrator/subagent patterns, A2A protocols
Phase 8  → agentforge-ship          Packaging, CI/CD, versioning, release
Phase 9  → agentforge-autoplan      Automated orchestration and meta-planning
Phase 10 → agentforge-evolution     Self-evolution: DGM, Voyager, DSPy patterns
Phase X  → agentforge-diagnose      Diagnose a failing agent (any phase)
Phase X  → agentforge-benchmark     Benchmark and evaluate agent performance
```

The **Hashimoto Loop** runs through every phase:

```
Agent attempts task
      ↓
Observe failure
      ↓
Diagnose: what capability or constraint is missing?
      ↓
Fix type:
  → Behavioral   → update system prompt / config
  → Mechanical   → add hook or structural test
  → Architectural → redesign the constraint layer
      ↓
Verify recurrence is prevented
      ↓
Repeat
```

---

## Installation

Copy skill directories into your AI agent's skill folder:

```bash
git clone https://github.com/Kingxiao/agentforge.git
cp -r agentforge/agentforge* <your-agent-skills-directory>/
```

Then invoke from within your agent session:

```
/agentforge           # Entry point — AI determines your phase and routes
/agentforge-spec      # Start from scratch
/agentforge-diagnose  # Debug a failing agent
/agentforge-harness   # Set up hooks and constraint layer
```

Refer to your AI agent platform's documentation for the correct skill directory path and invocation syntax.

---

## What You Get After Running /agentforge

A production agent with:

- **Spec** — validated feasibility before a line of code is written
- **Architecture** — loop paradigm chosen against 11 real-world patterns
- **Tool layer** — typed interfaces, retry logic, MCP integration where warranted
- **Context strategy** — compression schedule, cache policy, prompt variants
- **Memory system** — right tier for the use case (episodic / semantic / procedural)
- **Security layer** — OS sandbox, permission model, RAG injection defense
- **Harness** — hooks that mechanically prevent the top 5 failure modes
- **Multi-agent** — spawn protocols, result verification, orchestration patterns
- **Observability** — structured logs, cost tracking, SLA monitoring

---

## This Is Not a Runtime Library

| | agentforge | LangChain / CrewAI / LangGraph |
|---|---|---|
| **Type** | AI skill series | Python runtime framework |
| **What it produces** | Engineering methodology + constraints | Running code |
| **Model dependency** | None | None |
| **Self-evolution** | Phase 10, cross-cutting | Not a concept |

agentforge does not import into your code. It is the *knowledge* layer that makes an AI agent competent at engineering other AI agents.

---

## Source

Knowledge extracted from source-level analysis of:

| Agent | Stars | Key Pattern Extracted |
|-------|-------|-----------------------|
| Claude Code | — | 27-event hook system, Hashimoto Loop |
| Codex CLI | — | OS-level sandbox, Guardian AI, Starlark policy engine |
| OpenCode | 95K+ | PubSub event bus, LSP integration, Go single-binary |
| Cline | 60K+ | Modular prompt variants, zero-trust tool model |
| OpenClaw | 60K+ | Gateway/Channel/LLM 3-layer, 100+ skill OS |
| OpenHands | 65K+ | 6-backend runtime, Microagent system |
| Aider | 30K+ | Repo map, fuzzy edit matching, reflection chain |
| Letta | 15K+ | Block memory, self-modifying memory CRUD |
| Goose | — | Rust Agent loop, native MCP |
| MemU | — | Pipeline versioning, rollback |
| Cursor | 40K+ | Multi-agent parallel orchestration (behavior observed) |

---

## Roadmap

**v2 — Self-Evolution as a Cross-Cutting Concern**

v1 treats self-evolution as a terminal Phase 10. v2 injects it into every phase:

- Phase 1: Loop paradigm that supports runtime self-modification (DGM outer loop)
- Phase 2: Dynamic tool registry + automatic tool discovery (Voyager skill synthesis)
- Phase 3: Automatic prompt optimization (DSPy Compiler)
- Phase 4: Experience→skill elevation channel
- Phase 6: Automated Hashimoto Loop (agent observes failure → self-repairs harness)

See [ROADMAP.md](agentforge/ROADMAP.md) for full v2 plan.

---

## License

MIT

---

*Built through source-level reverse engineering of the agents that ship.*
