# Advanced Multi-Agent Patterns

> Specialized patterns extracted from `SKILL.md` on 2026-04-12 to keep the main skill under the 500-line limit. These patterns apply to platform builders, skill-based architectures, streaming data pipelines, and instruction-injection systems — most agent builds don't need them, so consult this file only when your design matches one of the triggers below.

## When to Read This File

| If you are building… | Read section |
|---|---|
| A **plugin marketplace** or runtime-loaded skill system | OpenClaw Plugin SDK + Skill-as-Agent |
| A **platform that manages other agents** (not just coordinates them for one task) | Platform / OS Agent Architecture Pattern |
| An **instruction injection system** with global / repo / task-scoped rules | OpenHands Microagent 3 Types |
| A **real-time data pipeline** (transcription → analysis → notification) | Streaming Pipeline Multi-Agent Pattern |

---

## OpenClaw Plugin SDK [OW]

OpenClaw's plugin system is essentially a Skill-as-Agent pattern — rather than spawning independent sub-processes, it loads domain skills to modify agent behavior.

### 5 Plugin Types

| Type | Responsibility | Examples |
|------|---------------|---------|
| Provider | LLM vendor adapter | OpenAI / Anthropic / Local |
| Channel | Input/output channel | Slack / Web / CLI |
| Tool | External capability binding | File system / API calls / Database |
| Skill | Domain behavior injection | Code review / Translation / Data analysis |
| Memory | Memory strategy | Vector storage / File memory / Redis |

### Hot-Loading Mechanism

- Uses **Jiti** for dynamic import, runtime load/unload plugins, no restart needed
- Each Skill is essentially a sub-agent: has independent system prompt and tool access
- Marketplace provides 100+ available Skills

### Core Insight: Skill-as-Agent Pattern

Traditional multi-agent approach spawns independent sub-agents to handle sub-tasks. OpenClaw's alternative: **load a domain skill to change the current agent's behavior**.

Comparison:

```
Traditional:  Main Agent → spawn(sub-agent) → sub-agent executes independently → returns result
OC:          Main Agent → load(Skill) → Main Agent gains new capability → executes directly
```

**Advantages**: Zero communication overhead, shared context, no result merging needed
**Disadvantages**: No isolation, skill conflict risk, single point of failure

Applicable when: Sub-tasks don't need file isolation, don't need parallelization, especially when deep context sharing is needed.

---

## Platform / OS Agent Architecture Pattern

> **"Use multi-agent to accomplish a task"** vs **"Build a platform that manages agents"** — these are two fundamentally different problems.
>
> OpenClaw is a prime example of the latter — rather than coordinating agents to complete a single task, it **maintains the health and evolution of an agent ecosystem**.

### When Are You Building a Platform

- Your system needs to run/manage other agents (not call them, but manage their lifecycles)
- You need to define "capability boundaries" for agents and dynamically expand them (Skill system, Plugin system)
- You need to monitor the health and evolution trajectory of the entire agent ecosystem
- Your agents can modify their own or other agents' behavioral rules

### Platform Architecture: Core Three Layers

```
Layer 1: Gateway / Channel (entry aggregation)
  ↓ Unified message format (CLI / Slack / Telegram / Web / API)
Layer 2: Agent Runtime (lifecycle management)
  ↓ Register, start, monitor, circuit break, destroy
  ├── Capability Store (Skill/Plugin repository)
  └── Evolution State (evolution history + circuit breaker)
Layer 3: Infrastructure (persistence + observability)
  ↓ Event stream / state storage / audit log
```

### Platform vs Coordinator Design Differences

| Dimension | Coordinator (task-oriented) | Platform (ecosystem-oriented) |
|-----------|---------------------------|------------------------------|
| Focus | Complete current task | Maintain system health |
| Agent relationship | Parent-child (task delegation) | Host-plugin (capability loading) |
| Failure handling | Retry/degrade | Circuit breaker + isolation |
| Evolution unit | Task prompt | Agent behavioral rules / capability library |
| State granularity | Task state | Agent ecosystem state |
| Representative implementation | Claude Code Agent SDK [CC] | OpenClaw [TS] (multi-channel Platform) |

### Key Platform Design Decisions

1. **Capability loading mechanism** — Static registration (compile-time determined) or dynamic loading (runtime JS module / .so)? Dynamic loading gains hot-update capability, at the cost of multiplied security audit complexity. Reference: OpenClaw uses Jiti dynamic import for hot loading
2. **Agent behavioral conventions** — Prompt conventions or compile-time invariants? Prompts are flexible but mutable, compile-time invariants are enforced but stable. Production platforms often combine both: invariants as floor, prompts for personalization
3. **Evolution safety boundary** — Platform must have Circuit Breaker (N consecutive failures → stop auto-evolution) and Blast Radius limit (auto-modifiable scope ≤ X%)
4. **Observability is a first-class citizen** — Platform debugging isn't about watching a single task, but about the evolution trajectory of the agent ecosystem. Must design Evolution Log from day one (reason + result for every agent behavior change)

> Principles and safety boundaries for self-evolving platforms → `/agentforge-evolution` (Phase 10)
> Deep Zig implementation → `/selfevolving-agent-architecture`

---

## OpenHands Microagent 3 Types [OH]

OpenHands refines "instruction injection" into three Microagent types, layered by trigger mode and scope:

| Type | Enum Value | Load Timing | Scope |
|------|-----------|-------------|-------|
| KNOWLEDGE | `value='knowledge'` | Always loaded | Global domain knowledge (language specs, API doc summaries) |
| REPO | `value='repo'` | Auto-loaded at repo level | Repo-specific instructions (`.openhands/` or `.cursorrules` files) |
| TASK | Dynamically triggered | When user message keywords match | On-demand injection of task-specific instructions |

**Design insights**:

- KNOWLEDGE is like the domain knowledge layer of system prompt — always in context, constant cost
- REPO corresponds to CLAUDE.md / AGENTS.md repo-level harness — auto-detected, no explicit loading needed
- TASK is the most interesting layer: **dynamically injects instructions based on keyword matching**, achieving "activate capability on demand" without spawning a new agent
- Three-layer separation makes context budget controllable: KNOWLEDGE takes fixed budget, REPO varies by repo, TASK loads on demand

---

## Streaming Pipeline Multi-Agent Pattern

> **Applicable scenarios**: Real-time data processing pipelines (transcription→analysis→push), where each agent's output is the next agent's input, and latency constraints differ at each stage.

Standard 4 modes (sync/async/worktree/remote) all assume "sub-task has a clear start and end." In streaming pipelines, each agent runs continuously, passing incremental data via shared queues — this is the 5th mode.

### Three-Stage Streaming Pipeline Diagram

```
TranscriptionAgent            AnalysisAgent              NotificationAgent
──────────────────            ─────────────              ─────────────────
Audio stream → Real-time transcription    Receives new segment every 30s   Push when trigger conditions met
    ↓                              ↓                              ↓
Write to transcript_queue →→→   Read transcript_queue          Read notification_queue
                            → LLM analysis                   → Write to notification queue
                            → Write to notification_queue →→→ → POST to Slack/Notion
```

**Key design**: Queues are the only communication medium between three agents, no direct calls — decouples processing speed at each stage.

### Implementation Points

```python
# Shared queue (asyncio.Queue intra-process, Redis Stream inter-process)
transcript_queue = asyncio.Queue(maxsize=10)
notification_queue = asyncio.Queue(maxsize=50)

async def run_pipeline():
    # Three agents run concurrently, non-blocking
    await asyncio.gather(
        TranscriptionAgent(output=transcript_queue).run(),
        AnalysisAgent(input=transcript_queue, output=notification_queue).run(),
        NotificationAgent(input=notification_queue).run(),
    )
```

### Comparison with Standard Multi-Agent Modes

| Dimension | Standard (sync/async spawn) | Streaming Pipeline |
|-----------|---------------------------|-------------------|
| Agent lifecycle | Start on demand, exit when task completes | Run continuously, no natural endpoint |
| Inter-agent communication | Spawn return value / Git commit | Shared queue (async, non-blocking) |
| Backpressure control | Not needed | Required (`maxsize` limits, prevent fast producer from overwhelming slow consumer) |
| Failure handling | Parent agent retries sub-agent | Single agent crash doesn't affect queue contents already in flight |
| Cost | Per-task billing | Continuous consumption (LLM billed per batch) |

**Backpressure is the key**: `maxsize` controls queue capacity, preventing TranscriptionAgent from writing at 10 items/sec while AnalysisAgent processes at 1 item/30s, which would cause memory explosion. Production environments use Redis Stream instead of `asyncio.Queue`, with persistence and consumer group functionality.
