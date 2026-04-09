---
name: agentforge-multiagent
description: AgentForge Phase 7 — Multi-agent coordination. 4 sub-agent spawn modes + agent registry + communication protocols + anti-patterns. Triggered when the user says "multi-agent", "sub-agent", "agent coordination", or "multi-agent".
triggers:
  - multi-agent
  - sub-agent
  - agent coordination
  - multi-agent
  - agent coordination
metadata:
  version: "2.0.0"
  last_updated: "2026-04-06"
  category: "agent-engineering"
---

# AgentForge Phase 7: Multi-Agent Coordination

> Previous: `/agentforge-harness` | Next: `/agentforge-ship` | Series entry: `/agentforge`
> Orchestrating existing agents: `/dev-orchestrator`
> Deep theory: `/multiagent-topology`, `/stigmergy-coordination`, `/collective-intelligence-design`

## Opening Warning: The Most Important Anti-Pattern

> **"Frontend Engineer Agent" + "Backend Engineer Agent" does not work.**
>
> Use Sub-agents for **context isolation**, not **role specialization**. An LLM doesn't write better frontend code just because you call it a "frontend engineer." The real value: let sub-tasks execute in a clean context, un polluted by the main loop's history.

## First Decision: Do You Even Need Multi-Agent?

```
Does your scenario need multi-agent?
│
├─ All tasks execute serially, no parallelization needed
│  → No, single agent suffices
│
├─ Has independent sub-tasks but no file isolation needed
│  → Async background agent (lightest weight)
│
├─ Sub-tasks modify different files, potential conflicts
│  → Isolated Worktree Agent
│
└─ Need large-scale parallelization (10+ concurrent tasks)
   → Remote Agent or containerized
```

## 4 Sub-Agent Modes [CC] — 3-Tier Isolation System

Claude Code has the most refined multi-agent isolation architecture in production, with three progressive tiers:

| Tier | Isolation Method | Mechanism | Applicable Scenario |
|------|-----------------|-----------|-------------------|
| L1 | Worktree isolation | `git worktree` creates independent working tree, file-level isolation | Sub-tasks modify files, need conflict avoidance |
| L2 | CCR / Remote isolation | Cloud compute environment, full sandbox (isolated filesystem + network) | Large-scale parallelization, untrusted code execution |
| L3 | Background async | Same workspace, async notification mechanism | Independent read-only tasks, don't block main flow |

This is currently the most mature isolation tiering in production-grade agent systems — most competitors only have "same-process" or "container" two modes, lacking an intermediate state.

### Mode 1: Synchronous Blocking

```
Main Agent → spawn(prompt) → Wait for completion → Get result → Continue
```

**Applicable**: Research, code analysis, search — results directly affect next decision
**Implementation**: `Agent(description, prompt)` returns result, main loop continues
**Constraint**: Blocks main loop, user must wait

### Mode 2: Async Background

```
Main Agent → spawn(prompt, background=true) → Continue working
                                           ↓ (notify on completion)
                                        Get result
```

**Applicable**: Independent coding tasks, test runs, doc generation — doesn't block main flow
**Implementation**: `Agent(description, prompt, run_in_background: true)` returns agentId
**Constraint**: Results return async, need notification mechanism

### Mode 3: Isolated Worktree

```
Main Agent → spawn(prompt, isolation="worktree")
              ↓
        Create Git worktree → Independent branch → Execute task
              ↓
        Complete → If changes, return branch name → Main Agent merges
        No changes → Auto-cleanup worktree
```

**Applicable**: Sub-tasks modify files, need isolation from main workspace
**Implementation**: Temporary git worktree + independent branch
**Constraint**: Needs Git repo, merging may have conflicts

### Mode 4: Remote

```
Main Agent → spawn(prompt, isolation="remote")
              ↓
        Execute in remote environment → Return session ID
              ↓
        Poll status → Get result
```

**Applicable**: Large-scale parallelization, need different hardware environments
**Constraint**: Network latency, high cost

## Sub-Agent Tool Restrictions

Sub-agents should not have the exact same toolset as the parent agent. Restriction principles [CC]:

| Disabled Tool | Reason |
|---------------|--------|
| EnterPlanMode / ExitPlanMode | Prevent nested plan mode |
| Agent (respawn) | Prevent recursive agents (infinite nesting, non-Ant-enterprise user) |
| AskUserQuestion | Sub-agent should not directly question user |
| TaskOutput / TaskStop | Sub-agent should not manipulate parent task |

**Design principle**: Sub-agent capabilities should be a **subset** of parent agent's.

## Inter-Agent Communication

### Git as Shared State [CC, CX]

The simplest and most reliable inter-agent communication:

```
Agent A completes work → git commit → git push
Agent B starts work → git pull → Read Agent A's changes
```

**Commit message is the communication protocol**. Descriptive commit messages let other agents understand what happened.

### Message Passing [CX]

Codex CLI's `Op::InterAgentCommunication`:
- Parent agent sends messages to sub-agent
- Sub-agent returns results to parent agent
- Via channel, not shared memory

### PubSub Events [OC]

OpenCode's pattern: Session inheritance + PubSub notification
- Sub-agent creates child Session (`ParentSessionID` points to parent)
- On completion, publishes event via PubSub
- Cost auto-aggregates to parent Session

### Delegation Lineage Tracking [HR]

Hermes stores full delegation chains in SQLite, enabling session history search to correctly deduplicate and attribute subagent work:

```sql
-- sessions table
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    parent_session_id TEXT,          -- NULL for root sessions
    source TEXT,                     -- "user", "tool", "api"
    created_at TIMESTAMP,
    ...
);

-- Walk the chain to find root
def _resolve_to_parent(session_id) -> str:
    while True:
        parent = db.get_parent(session_id)
        if parent is None:
            return session_id
        session_id = parent
```

**Three sources tagged at creation**:
- `source="user"` — Human-initiated sessions (visible in history)
- `source="tool"` — Subagent sessions spawned by tool calls (hidden from user history)
- `source="api"` — Third-party integrations (hidden)

**Context compression creates child sessions**: when the context is compressed, a new child session continues the work. The lineage chain is preserved.

**Memory provider gets notified on delegation**: the `on_delegation(task, result, child_session_id)` hook lets memory providers record what was delegated and what came back, without parsing the full transcript.

**When to implement**: any agent that spawns subagents and needs searchable session history. Without lineage tracking, cross-session search returns duplicates (parent + child both match the same query); with it, results are deduplicated at the root and child work is attributed correctly.

## Agent Registry and Lifecycle

### Codex's ThreadManager [CX]

```rust
struct AgentRegistry {
    agents: HashMap<ThreadId, AgentHandle>,
    parent: Weak<ThreadManager>,  // Weak ref to prevent cycles
}

// Lifecycle
spawn_agent(config, initial_op) → ThreadId
    ↓ executing
monitor(thread_id) → AgentStatus
    ↓ complete
cleanup(thread_id) → release resources
```

### Claude Code's Agent Lifecycle [CC]

```
registerAsyncAgent(agentId, {description, prompt, model})
    ↓
updateAgentProgress(agentId, progress)  // Streaming updates
    ↓
completeAgentTask(agentId, result)      // Complete
    ↓
enqueueAgentNotification()              // Notify main loop
    ↓
removeAgent(agentId)                   // Cleanup
```

## Division of Labor Strategy

### By Scope (Recommended)

```
Agent A → Handle all files under src/api/
Agent B → Handle all files under src/ui/
Agent C → Run tests + report results
```

**Principle**: Different agents operate on different file scopes. If two agents need to edit the same file, merge into one agent.

### By Phase

```
Agent A → Research + Analysis (read-only tools)
    ↓ output analysis report
Agent B → Implementation (read-write tools)
    ↓ output code
Agent C → Review (read-only + diff tools)
```

### Forbidden: By Role

```
❌ "Frontend Engineer" Agent
❌ "Backend Engineer" Agent  
❌ "Test Engineer" Agent
❌ "DevOps Engineer" Agent
```

These role divisions are meaningless to LLMs. They just add unnecessary communication overhead.

## CI as Universal Verifier

In multi-agent scenarios, CI is the only mechanism that can equally verify all agent outputs:

```
Agent A commits → CI runs → Pass/Fail
Agent B commits → CI runs → Pass/Fail
Human commits    → CI runs → Pass/Fail
```

**CI doesn't care who wrote the code.** This is the most impartial quality gate in multi-agent systems.

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

## Current State (April 2026)

1. **Worktree Isolation Becomes Mainstream** — Claude Code's git worktree mode is validated as the optimal solution for multi-agent file conflicts; Codex CLI and OpenCode have both implemented similar mechanisms; "multi-agent in same workspace" pattern is being phased out
2. **Agent-to-Agent Protocol Converging** — Google A2A protocol and Anthropic's Agent SDK drive standardization of inter-agent communication, but Git commit as shared state remains the most reliable cross-agent communication in production
3. **Sub-agent Recursive Spawn Restricted** — Multiple platforms now prohibit sub-agents from spawning sub-agents (preventing recursive explosion); Claude Code enforces single-level nesting for non-Ant-enterprise users, becoming industry consensus
4. **Scope-Based Division Trumps Role-Based Division** — Empirical data continues to confirm "divide agents by file scope" has 2-3× higher success rate than "divide by role"; role division's communication overhead far exceeds its benefits
5. **Skill-as-Agent Pattern Rising** — OpenClaw's plugin-style capability injection (load Skill to change agent behavior rather than spawn new agent) demonstrates zero-communication-overhead advantages in scenarios not needing file isolation

## Known Pitfalls

1. **Worktree Merge Conflict Accumulation** — Multiple worktree agents parallel-modifying then merging causes conflict count to grow super-linearly with agent count. Solution: strictly divide agent responsibilities by file scope, no overlap; pre-check conflicts with `git diff --stat` before merging
2. **Sub-agent Context Inheritance Bloat** — Parent agent passes full context to sub-agent, causing sub-agent context polluted by irrelevant information, degrading decision quality. Solution: pass only minimum context needed for sub-task (prompt + relevant file paths), don't pass conversation history
3. **Async Agent Result Loss** — Background agent completes but main agent has already entered a different execution branch, async result goes unconsumed. Solution: async agent writes results to persistent storage (file or Git commit), don't rely on in-memory notification mechanism
4. **Multi-Agent Cost Explosion** — Each sub-agent consumes independent LLM tokens; 10 parallel agents cost 10×+ of single agent (due to system prompt repetition). Solution: strictly evaluate parallel necessity; prioritize Skill-as-Agent pattern for scenarios not needing file isolation
5. **Inter-Agent Deadlock** — Agent A waits for Agent B's output, Agent B waits for Agent A's output. Solution: prohibit circular dependencies; all inter-agent communication must be a directed acyclic graph (DAG)

## Further Reading

| Topic | Resource |
|-------|---------|
| Sub-agent spawn mode detailed implementation | [`references/spawn-modes-detail.md`](references/spawn-modes-detail.md) |
| Agent registry and lifecycle patterns | [`references/agent-registry-patterns.md`](references/agent-registry-patterns.md) |
| Sub-agent permissions and tool restrictions | `/agentforge-security` |
| Worktree and Git isolation configuration | `/agentforge-harness` |
| Multi-agent topology design principles | `/multiagent-topology` |
| Collective intelligence and pheromone coordination | `/stigmergy-coordination`, `/collective-intelligence-design` |
| Self-evolving agent clusters | `/selfevolving-agent-architecture` |

## Multi-Agent Checklist

- [ ] Confirmed need for multi-agent (clear reason single agent won't suffice)
- [ ] Clarified mode: Coordinator (task-focused) or Platform (ecosystem-focused)
- [ ] Selected spawn mode (sync/async/worktree/remote)
- [ ] Sub-agent toolset is a subset of parent agent's
- [ ] Different agents operate on different file scopes (no conflicts)
- [ ] Has inter-agent communication mechanism (Git commit or message passing)
- [ ] CI as universal verifier
- [ ] Not using role division mode
- [ ] Platform type: designed Circuit Breaker + Evolution Log + Capability Store

## Reverse Audit (Diagnose Mode)

> Called by `/agentforge-diagnose` — static audit of existing code across D7 Multi-Agent dimensions.

| # | Check Item | How | Pass Criteria |
|---|-----------|-----|---------------|
| MA1 | Spawn mode identifiable | Search for spawn/create_agent/subagent calls | Can determine Parallel/Sequential/Hierarchical/Mesh type |
| MA2 | No circular dependency risk | Draw call graph (A→B→?) check for cycles | Call chain has no cycles, or has `max_depth` limit |
| MA3 | Sub-agent context isolated | Check how sub-agent is created: does it inherit main context | Sub-agent uses fresh context, doesn't inherit main agent's full history |
| MA4 | Sub-agent results verified | Check how main agent uses sub-agent return values | Has integrity checks (not blind trust), critical conclusions have source verification |
| MA5 | Partial failure has degradation | `grep -rn "try\|except\|catch\|fallback" src/ \| grep -i agent` | Single sub-agent failure doesn't crash entire workflow |

**High-probability issues**: No cycle depth limit (P0 deadlock risk), sub-agents share main context (P1 context pollution), blind trust of sub-agent output (P1 error propagation)

## Next Steps

Multi-agent design complete → **`/agentforge-ship`** (Phase 8: Release & Deployment)
Building Platform type → **`/agentforge-evolution`** (Phase 10: Self-Evolution)
Need deep Zig implementation → **`/selfevolving-agent-architecture`**
