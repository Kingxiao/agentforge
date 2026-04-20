---
name: agentforge-production
description: AgentForge Phase 9 - Agent production runtime. Brain/Hands/Session decoupling, lazy provisioning, container resilience, credential isolation, observability, scaling patterns. Triggered when user says "agent production", "agent runtime", "agent operations", "agent as a service".
triggers:
  - agent production
  - agent runtime
  - agent operations
  - agent as a service
  - agent infrastructure
metadata:
  version: "1.1.0"
  last_updated: "2026-04-12"
  category: "agent-engineering"
---

# AgentForge Phase 9: Production Runtime

> Previous: `/agentforge-ship` | Next: `/agentforge-autoplan` | Series entry: `/agentforge`
> Source: Anthropic Managed Agents architecture — https://www.anthropic.com/engineering/managed-agents (verified 2026-04-11, published 2026-04-10), validated against first principles
> Security foundations: `/agentforge-security` | Packaging: `/agentforge-ship`

## Core Distinction: Ship vs. Production

| Dimension | Ship (Phase 8) | Production (Phase 9) |
|-----------|---------------|---------------------|
| Question answered | "How to deliver Agent to users" | "How to keep Agent alive and reliable" |
| Time horizon | Ends at release | Starts at release |
| Concerns | Packaging, CI/CD, versioning | Process management, fault recovery, scaling, observability |
| Applies when | Always (every Agent ships somehow) | Only when Agent runs as a service (not CLI-only tools) |

**Skip this Phase if**: Your Agent is a local CLI tool (Claude Code, Aider style) that users install and run themselves. CLI tools don't need production runtime — Phase 8 (Ship) is sufficient.

**This Phase is mandatory if**: Your Agent runs as a service — HTTP API, background daemon, multi-user web service, or managed platform.

## Decision 1: Component Decoupling (Brain / Hands / Session)

> Principle: Separation of Concerns (Dijkstra, 1972), applied to Agent runtime.

An Agent in production has three concerns that fail independently and should be managed independently:

```
Brain   = LLM inference + harness logic (stateless, horizontally scalable)
Hands   = Execution environments: containers, sandboxes, browsers, any tool runtime
Session = Append-only event log: durable record of everything that happened
```

**Why decouple?**

| Coupled failure mode | Decoupled behavior |
|---------------------|-------------------|
| Container crash loses all session state | Session persists in event log; new brain reads log and resumes |
| LLM API timeout blocks sandbox | Brain retries independently; sandbox stays alive |
| Scaling inference requires scaling sandboxes | Brain scales horizontally; sandboxes provisioned on demand |

### Minimal Interface Set

```
execute(name, input) → string    # Call any tool / sandbox
provision({resources})           # Initialize new execution environment
wake(sessionId)                  # Recover from brain crash
getSession(id)                   # Read event log
emitEvent(id, event)             # Persist event to log
```

**Key constraint**: Brain is stateless. All state lives in the Session (event log). If a brain process crashes, `wake(sessionId)` reads the log and resumes from the last event.

### When to Decouple

```
Is your Agent a single-user local tool?
    Yes → Skip decoupling; in-process architecture is fine
    No → Does your Agent need crash recovery or horizontal scaling?
        Yes → Full Brain/Hands/Session decoupling
        No → Partial decoupling: separate Session (event log) from Brain+Hands
             (cheapest insurance — crash recovery without full architectural split)
```

## Decision 2: Lazy Provisioning

> Principle: Don't pay for resources until you need them.

**Problem**: Eagerly provisioning execution environments (Docker containers, sandboxes) at session start adds latency to every session — including sessions that never use tools.

**Solution**: Brain starts inference immediately. Sandboxes are provisioned only when the first tool call requires one.

```
Session start
    ├─ Brain starts inference immediately (no waiting)
    ├─ LLM generates text response → no sandbox needed → fast response
    └─ LLM generates tool call → provision sandbox on-demand → execute
        └─ Subsequent tool calls reuse the warm sandbox
```

**Impact**: Anthropic measured p50 TTFT (time to first token) drop of ~60%, p95 drop of ~90%, by eliminating eager provisioning.

**Applicability**: This pattern matters when sandbox cold-start is measured in seconds (cloud containers, VMs). For local Docker (< 1s start), the benefit is negligible.

## Decision 3: Execution Environment Resilience

> Principle: Treat execution environments as cattle, not pets.

**Problem**: If the Agent treats its sandbox as a stateful pet (relies on files, processes, state within it), sandbox failure = session failure.

**Solution**: Sandbox failures surface as tool errors. The brain catches them, reports to the LLM, and provisions a fresh sandbox from a standard recipe.

```python
async def execute_tool(name: str, input: dict) -> str:
    try:
        return await sandbox.execute(name, input)
    except SandboxError as e:
        # Don't crash the session — report as tool error
        new_sandbox = await provision(standard_recipe)
        return f"Tool execution failed: {e}. New environment provisioned. Retry if needed."
```

**Standard recipe**: A reproducible environment spec (Dockerfile, nix config, or similar) that can rebuild the sandbox from scratch. The brain loses in-sandbox state but can re-derive it from the session event log.

**Anti-pattern**: "Nursing containers back to health" — SSHing into a stuck container, manually restarting processes, patching state. This doesn't scale and creates implicit state dependencies.

## Decision 4: Credential Isolation at Runtime

> Full principle: `/agentforge-security` (Credential Unreachability section)
> This section covers production deployment patterns specifically.

Security is covered in Phase 5. At production deployment time, the key decision is:

```
Does your Agent execute LLM-generated code?
    Yes → Credentials MUST NOT be in the execution environment
          Deploy vault + proxy (see Phase 5 for architecture)
    No → Standard .env + secrets manager is sufficient
         But: ensure Agent process and tool execution run with different permission sets
```

### Production Credential Topology

```
                        ┌─ Secrets Manager (AWS SM / Vault / GCP SM) ─┐
                        │  OAuth tokens, API keys                     │
                        └──────────────┬──────────────────────────────┘
                                       │ (fetch at call time)
┌─ Agent Brain ─┐      ┌─ MCP Proxy ──┤
│ No credentials │──────│ Routes tool  │──→ External APIs (GitHub, Slack, etc.)
│ in memory      │      │ calls        │
└────────────────┘      └──────────────┘
        │
        │ execute(name, input) → string
        ▼
┌─ Sandbox ─────────────────────┐
│ No .env mounted               │
│ No secrets in environment     │
│ LLM-generated code runs here  │
└───────────────────────────────┘
```

## Decision 5: Observability

> Principle: You cannot improve what you cannot measure.

Three layers of observability for production Agents:

| Layer | What to capture | Tool |
|-------|----------------|------|
| **Session events** | Every LLM turn, tool call, result (the event log from D1) | JSONL / SQLite — your own |
| **Infrastructure metrics** | Container CPU/memory, LLM API latency p50/p95/p99, error rates | Prometheus + Grafana / Datadog |
| **Business metrics** | Task completion rate, user satisfaction, cost per task | Custom dashboards |

**Minimum viable observability** (before anything else):

```bash
# 1. Session event log (already have from D1)
# 2. LLM API cost tracking (tokens in/out per session)
# 3. Error rate by error type (LLM timeout / tool failure / sandbox crash / user error)
# 4. Health check endpoint
```

**Anti-pattern**: Observability as afterthought. If you can't answer "what went wrong in session X?" from logs alone, your observability is insufficient. Add structured logging from day one.

## Decision 6: Scaling Patterns

### Horizontal Scaling Decision Tree

```
How many concurrent Agent sessions do you need?
    1-5 → Single process, no scaling architecture needed
    5-50 → Process pool (PM2 / gunicorn workers / goroutine pool)
    50-500 → Container orchestration (K8s / Fly.io / ECS)
    500+ → Full Brain/Hands/Session decoupling + auto-scaling groups
```

### Stateless Brain Scaling

Because brains are stateless (all state in session event log), scaling is straightforward:

```
Load Balancer
    ├─ Brain instance 1 ──→ Session Store (shared)
    ├─ Brain instance 2 ──→ Session Store (shared)
    └─ Brain instance N ──→ Session Store (shared)
```

Any brain can serve any session — just `getSession(id)` and continue.

### Cost-Aware Scaling

Agent sessions are expensive (LLM API calls). Scaling patterns must account for:

| Concern | Mitigation |
|---------|-----------|
| Runaway sessions (infinite loops) | IterationBudget cap (see `/agentforge-tools`) |
| Concurrent LLM calls overwhelming API rate limits | Queue + rate limiter between brain pool and LLM API |
| Sandbox sprawl (orphaned containers) | TTL on sandboxes + garbage collection sweep |
| Cost per session unknown | Track tokens + sandbox compute per session; alert on outliers |

## Current State (April 2026)

1. **Managed Agent platforms emerging** — Anthropic (Managed Agents), OpenAI (Codex cloud), Google (Gemini agents) all launched hosted Agent platforms in Q1-Q2 2026. The "build vs. buy" decision for production runtime is now real.
2. **Brain/Hands/Session pattern validated at scale** — Anthropic's Managed Agents architecture blog (published 2026-04-10, https://www.anthropic.com/engineering/managed-agents) documented verbatim: "p50 TTFT dropped roughly 60%" and "p95 dropped over 90%" from decoupling brain from containers + lazy sandbox provisioning. The pattern is production-proven, not theoretical.
3. **Container-as-cattle becoming standard** — Kubernetes-native Agent deployments treat sandbox containers as ephemeral workloads. State lives in event logs, not containers.
4. **Credential isolation moving from best practice to requirement** — Multiple Agent-related credential theft incidents in Q1 2026 (prompt injection → .env exfiltration) pushed vault-backed proxy from "nice to have" to "mandatory for any Agent handling third-party tokens."

## Decision 7: External Dependency Operational Risk Enumeration

> Principle: Every external dependency has operational constraints that are not in its API documentation. Enumerate them before production, not after the first outage.

Agent systems in production are only as reliable as their weakest external dependency. Health checks verify "the service responds"; they rarely catch the subtler operational traps: rate limits hit under load, 2FA requirements that break unattended operation, quota resets at inconvenient times, silent data staleness, authentication token lifetime mismatches.

**This is not a dependency selection check** (that belongs in Phase 2 Tools). This is a **pre-production risk enumeration** — you've already chosen the dependency, now list what will go wrong.

### The Enumeration Protocol

For every external dependency (LLM API, data source, storage, auth provider, third-party SDK, broker, hardware integration), answer these five questions and commit the answers to a `DEPENDENCIES.md` file in the repo:

```
1. Known rate limits — What's the documented rate limit? What happens when hit?
   (pacing errors, silent drops, 429 with retry-after, quota reset timing?)

2. Authentication lifetime — How long do tokens/sessions last? What's the renewal mechanism?
   (does it require human action? 2FA? hardware key? is renewal API-based or UI-only?)

3. Unattended operation blockers — Are there any requirements that break headless/cron execution?
   (2FA prompts, captchas, session reconnection requiring UI, email confirmation, IP whitelist drift)

4. Silent failure modes — What failure types return success-looking responses?
   (stale data served as fresh, empty results that should be errors, default values substituted for missing data)

5. Cost/quota surprises — What actions consume quota unexpectedly?
   (retries counted against quota, background prefetch, debug modes leaving high-cost logging on)
```

### Why This Works

These questions are domain-agnostic but catch domain-specific traps:
- A dependency's documentation never admits "this breaks unattended operation" — you must discover it through Q3
- Silent failures (Q4) are the hardest class of bugs because they don't trigger alerts
- Q5 catches the "I thought API calls were cheap" mistake that only shows up on the next month's bill

### When to Enumerate

- **First pass**: Phase 8 Ship — before first deployment
- **Update trigger**: Every incident where an external dependency caused or contributed to a failure
- **Source material**: Read the dependency's GitHub issues (filter by "production", "rate limit", "unattended", "headless"), Stack Overflow, and the project's changelog for operational fixes

### Anti-pattern: Trusting Health Checks Alone

A health check that verifies "API returns 200" tells you nothing about whether Q4 (silent failures) or Q5 (quota surprises) are happening. Health checks are necessary but insufficient. The DEPENDENCIES.md enumeration is the documentation layer; health checks are the runtime verification layer. You need both.

---

## Known Pitfalls

1. **Premature decoupling** — Building Brain/Hands/Session split for a 1-user prototype. Over-engineering kills delivery speed. Start coupled; decouple when you hit the first scaling pain point.
2. **Event log without size management** — Append-only logs grow unbounded. A 1000-turn session generates megabytes of events. Solution: implement event log retention policy (compress old events, archive to cold storage after session ends).
3. **Observability without action** — Dashboards exist but no one looks at them. Solution: set alerts on 3 metrics only: error rate > threshold, cost per session > budget, p95 latency > SLA. Add more only when these are stable.
4. **Sandbox TTL too long** — Orphaned sandboxes from crashed sessions consume resources indefinitely. Solution: sandboxes must have a TTL (max 1 hour without activity); garbage collector sweeps for orphans every 10 minutes.

## Further Reading

| Topic | Resource |
|-------|----------|
| Security foundations (6-layer model + vault) | `/agentforge-security` |
| Packaging & CI/CD (pre-production) | `/agentforge-ship` |
| Context reconstruction from event log | `/agentforge-context` (Decision 13) |
| Harness assumption decay | `/agentforge-harness` (Meta-Harness section) |
| Agent observability deep dive | `/agent-observability` |
| Cloud deployment recipes | `/cloud-deployment` |
| Anthropic Managed Agents architecture | `https://www.anthropic.com/engineering/managed-agents` |

## Production Checklist

- [ ] Determined if Phase 9 applies (Agent runs as service, not CLI-only)
- [ ] Component decoupling level decided (full / partial / none)
- [ ] Session persistence mechanism chosen (JSONL / SQLite / cloud store)
- [ ] Crash recovery tested (kill brain process → restart → verify session continues)
- [ ] Credential isolation verified (sandbox cannot read secrets)
- [ ] Health check endpoint exists and monitored
- [ ] LLM API cost tracked per session
- [ ] Error rate alerting configured
- [ ] Sandbox TTL and garbage collection configured
- [ ] Scaling tier determined (single process / process pool / container orchestration)

## Reverse Audit (Diagnose Mode)

> Called by `/agentforge-diagnose` — D9 production runtime audit.

| # | Check Item | How to Check | Pass Criteria |
|---|-----------|-------------|---------------|
| PR1 | Session durability | Kill agent process mid-task, restart | Session resumes from event log without data loss |
| PR2 | Credential isolation | `docker exec <sandbox> env \| grep -i key` | No API keys / tokens in sandbox environment |
| PR3 | Health check | `curl /health` | Returns 200 with status info |
| PR4 | Cost tracking | Check logs/dashboard for token usage per session | Per-session cost is visible and within budget |
| PR5 | Sandbox cleanup | List running containers after session end | No orphaned sandboxes from completed/failed sessions |

## Next Steps

Production runtime operational → **`/agentforge-autoplan`** (Phase 10: Full-Pipeline Orchestrator)
