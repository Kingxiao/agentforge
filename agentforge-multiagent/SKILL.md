---
name: agentforge-multiagent
description: AgentForge Phase 7 — Multi-agent coordination. 5 sub-agent spawn modes (sync/async/worktree/remote/adversarial-debate) + agent registry + communication protocols + anti-patterns. Triggered when the user says "multi-agent", "sub-agent", or "agent coordination".
triggers:
  - multi-agent
  - sub-agent
  - agent coordination
  - subagent spawn
  - agent orchestration
metadata:
  version: "2.1.0"
  last_updated: "2026-04-12"
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

### Hard Cost/Benefit Numbers (Anthropic Multi-Agent Research, 2025-06-13)

> Source: Anthropic "How we built our multi-agent research system" — https://www.anthropic.com/engineering/multi-agent-research-system (verified 2026-04-12). These are **verbatim** production numbers, not estimates.

| Metric | Value | Implication |
|---|---|---|
| **Single agent token cost** | "agents typically use about **4× more tokens** than chat interactions" | Even a plain agent is 4× a single chat call |
| **Multi-agent token cost** | "multi-agent systems use about **15× more tokens** as chats" | ~4× above single agent; plan budget accordingly |
| **Performance uplift** | "Claude Opus 4 lead + Sonnet 4 subagents outperformed single-agent Claude Opus 4 by **90.2%** on internal research eval" | Multi-agent is not a tax — it's a capability unlock for heavy parallelization |
| **Variance decomposition** | On BrowseComp: "**token usage alone explains 80% of variance**"; token usage + tool calls + model choice explain **95%** of variance | Context engineering > model choice as the lever |

**Cost/benefit rule**: "Multi-agent systems require tasks where the value of the task is high enough to pay for the increased performance." In plain words — **if you can't justify 15× token spend for substantial quality gain, don't go multi-agent**.

**Best-fit domains (verbatim)**: "tasks that involve heavy parallelization, information that exceeds single context windows, and interfacing with numerous complex tools." Three clear "yes" signals. Missing all three → single agent is almost always the right answer.

### Decision Tree

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

### Documented Failure Mode: Runaway Delegation

> Source: Adaline Labs, 2026-04-11 (https://labs.adaline.ai/p/multi-agent-systems-product-control-plane)

**Anthropic's own research system** was documented to have "**spawned 50 subagents for simple queries**" and at times "scouring the web endlessly" without a delegation governance layer. This is the canonical failure mode: without explicit permission/handoff/visibility/recovery rules, a Lead agent will over-delegate and burn token budget in a runaway fan-out. **Treat 50-subagent episodes as a paging-severity incident**, not an amusing anecdote — at 15× token ratio, one such episode can exceed a month's budget for a single task.

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

### Mode 5: Adversarial Debate

```
Main Agent → spawn(prompt_A, stance="advocate") + spawn(prompt_B, stance="challenger")
              ↓                                      ↓
        Agent A argues FOR                    Agent B argues AGAINST
              ↓                                      ↓
              └──────── Both results ────────────────┘
                              ↓
                   Synthesizer Agent combines → Final output
```

**Applicable**: Decisions where confirmation bias is the primary risk — the quality of the decision improves when opposing viewpoints are forced to engage

**Examples across domains**:
- Research: hypothesis agent vs counter-hypothesis agent → synthesis
- Product design: user advocate vs engineering feasibility → balanced feature spec
- Risk assessment: optimistic projection vs pessimistic projection → calibrated estimate
- Content review: "publish" advocate vs "revise" advocate → editorial decision

**Key design constraints**:
- The advocate and challenger MUST receive the same input data — asymmetric information defeats the purpose
- The synthesizer MUST NOT be either advocate — it's a separate agent with a distinct prompt ("weigh both arguments, identify which claims have stronger evidence")
- Debate rounds: 1 round is usually sufficient. Multiple rounds risk agents entrenching rather than converging — cap at 2 rounds with explicit "what new evidence would change your position?" prompt in round 2

**When NOT to use**: Tasks with objectively correct answers (code compilation, math). Debate adds latency and cost for zero quality gain when ground truth is mechanically verifiable.

**Cost**: 3x a single agent call (advocate + challenger + synthesizer). Only justified when the cost of a wrong decision exceeds the cost of 3x inference.

### Mode 5 Failure Modes (2025-2026 research)

Recent empirical research has identified serious failure modes in multi-agent debate. Understand these before choosing Mode 5:

| Failure mode | Description | Mitigation |
|--------------|-------------|------------|
| **Homogeneous bias amplification** | When advocate and challenger share the same base model, they share the same training biases. Debate amplifies rather than corrects these biases — the agents agree on wrong answers with higher confidence | Force heterogeneity: use different model providers or at least different model families for advocate vs challenger. A Claude-vs-Claude debate is weaker than Claude-vs-GPT debate |
| **Persuasion > accuracy** | A single eloquent but incorrect agent can lower system accuracy by 10-40% (Nature Sci Rep 2026). Agents often fail to revise their stance when confronted with correct counter-evidence, swayed instead by confident delivery | Add a "change condition" to round 2 prompt: "What specific evidence, not rhetoric, would change your position?" Reject positions that claim no evidence could change them |
| **Voting ≈ Debate** | ICLR 2025 research shows majority voting accounts for most performance gains attributed to Multi-Agent Debate. Simple N-way parallel sampling + vote may be cheaper and equally effective | Benchmark Mode 5 against simpler "N independent samples + majority vote" before committing. If voting performs within 5% of debate at 1/3 the cost, use voting |
| **Error entrenchment over rounds** | Additional debate rounds don't always improve outcomes — they can cement initial errors through repetition. More rounds ≠ better decisions | Cap at 2 rounds maximum. Extended rounds risk groupthink around incorrect consensus |

**Revised decision flow**:

```
Considering Mode 5 (Adversarial Debate)?
    │
    ├─ Do you have the budget for N-way parallel sampling + majority voting?
    │  Yes → Benchmark voting FIRST. It's often 80% as good at 33% the cost
    │
    ├─ If voting is insufficient, can you use heterogeneous models?
    │  No (only one provider available) → Mode 5 risks bias amplification — reconsider
    │  Yes → Proceed with Mode 5 but:
    │        - Use different model providers/families for advocate vs challenger
    │        - Cap debate at 2 rounds
    │        - Add evidence-based change conditions to round 2 prompts
    │        - The synthesizer must be a third model, not either debater
```

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

## Product Control Plane: The 4 Primitives (Adaline 2026)

> Source: Adaline Labs "Multi-Agent Systems Need a Product Control Plane" (2026-04-11, https://labs.adaline.ai/p/multi-agent-systems-product-control-plane). Derived from production deployment data, not theory.

Multi-agent systems **fail in production not because models aren't smart enough but because there's no governance layer above the models.** Adaline's empirical finding: "If your PRD does not define delegation boundaries and escalation conditions, it is not ready for a multi-agent workflow."

Four essential primitives must exist **before** launching any multi-agent system:

### 1. Permissions — What Each Agent Can Do

- **Least-privilege defaults at the sub-agent level** — default deny, explicit grant.
- **Semantic constraints, not just binary access** — e.g. "read-only access to specific rows" rather than "read access to DB".
- **Dynamic permissions based on trust metrics** — agents that demonstrate reliability earn broader scope; those that drift lose it.

### 2. Handoffs — Transfers of Work Between Agents

- **Safety classifiers at both ends of every sub-agent handoff** — one on the sender's output, one on the receiver's accepted input. Handoff is the highest-risk boundary in a multi-agent system.
- **Log handoffs with source/destination agents and context transferred** — enables incident replay.
- **Treat incomplete context transfers as failure events** — if the handoff payload is missing fields the receiver needs, fail loud, don't silently degrade.

### 3. Visibility — Understanding System Operations

- **Traces at the agent-step level, not just the request level** — a single user query can spawn 10+ internal steps; per-request logs hide the interesting behavior.
- **Step-level visibility for users** — users should see what the agent is doing at each stage of a multi-agent task, not just the final answer.
- **Define user-visible stages explicitly** — which steps are surfaced, which are internal.

### 4. Recovery — Handling Failures

Every multi-agent system must implement **at least three explicit recovery options**:
1. **Retry with modified parameters** — same tool call, different inputs after error analysis.
2. **Fallback to simpler workflow** — degrade from multi-agent to single-agent or to a hardcoded workflow.
3. **Escalation to human review** — exit the autonomous loop entirely when the first two options are exhausted.

**Circuit breakers for runaway delegation chains** — agents delegating to sub-agents delegating further must have a hard stop (max depth, max fan-out, max total token budget), otherwise you get the "50 subagents for simple queries" failure mode.

### Autonomy Drift: Measured in Production

Adaline tracked Anthropic API usage from **October 2025 → January 2026**:
- 99.9th-percentile session length grew from **10 minutes → 40 minutes** (4×).
- Human interventions dropped from **5.4 → 3.3 per session**.

**Interpretation**: agents are running longer and with less human oversight — autonomy drift is real and measurable. The delayed-feedback safety pattern in `/agentforge-evolution` should be applied here too: observation window + shadow mode + reversible-only modifications + outcome attribution gate + human escalation thresholds.

### Industry Signals

- **Linux Foundation A2A Protocol** — crossed "150 supporting organizations in its first year" — inter-agent governance is being standardized at the ecosystem level, not just per-product.
- **Amazon finding** — "Quality issues in production often surface in ways that traditional monitoring misses" — you can't just bolt on APM; need agent-specific observability.
- **Gartner prediction** — "40% of enterprise applications will include task-specific agents by year's end, up from less than 5% in 2025" — demand is real, but the production bar is rising fast.

## CI as Universal Verifier

In multi-agent scenarios, CI is the only mechanism that can equally verify all agent outputs:

```
Agent A commits → CI runs → Pass/Fail
Agent B commits → CI runs → Pass/Fail
Human commits    → CI runs → Pass/Fail
```

**CI doesn't care who wrote the code.** This is the most impartial quality gate in multi-agent systems.

## Advanced Patterns (specialized — read on demand)

Four patterns below don't fit the standard decision flow and only apply when your build matches the trigger. All four are extracted to `references/advanced-patterns.md` to keep this skill focused:

| Pattern | Read when you are building… |
|---|---|
| **OpenClaw Plugin SDK / Skill-as-Agent** | A plugin marketplace or runtime-loaded skill system (instead of process-spawned sub-agents) |
| **Platform / OS Agent Architecture** | A platform that *manages* other agents' lifecycles (Agent OS), not one that *coordinates* them for a single task |
| **OpenHands Microagent 3 Types** | An instruction-injection system with distinct global / repo / task-scoped rules |
| **Streaming Pipeline Multi-Agent** | A real-time data pipeline (transcription → analysis → notification) where each agent runs continuously through shared queues |

If none of these match your system, the four spawn modes + Control Plane 4 primitives above cover your case.

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
Building Platform type → **`/agentforge-evolution`** (Phase 11: Self-Evolution)
Need deep Zig implementation → **`/selfevolving-agent-architecture`**
