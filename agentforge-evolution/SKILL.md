---
name: agentforge-evolution
description: AgentForge Phase 11 - Agent Self-Evolution Design. L0-L3b evolution level gradient + principles (DGM/Voyager/DSPy) + architectural patterns + safety boundaries + implementation code. Triggered when user says "self-evolving agent", "agent self-modification", "self-evolution architecture", "evolution agent".
triggers:
  - self-evolving agent
  - agent self-modification
  - self-evolution architecture
  - evolution agent
  - self-evolving
  - self-improvement agent
metadata:
  version: "1.1.0"
  last_updated: "2026-04-12"
  category: "agent-engineering"
---

# AgentForge Phase 11: Agent Self-Evolution Design

> Previous: `/agentforge-autoplan` (Phase 10) | Next: `/agentforge-benchmark` (Phase 12) | Series entry: `/agentforge`
> Deep Zig implementation: `/selfevolving-agent-architecture`

## Core Principles

> **Self-evolution is not "agent can modify code" — it is "agent can reliably, safely, and purposefully improve its own behavior."**

The gap between the two:
- **Can modify code** — any tool call can do this.
- **Reliable** — has tests to verify; behavior known before and after changes.
- **Safe** — has rollback, circuit breakers, blast-radius limits.
- **Purposeful** — modification aligns with system-wide goals (not local optimization causing global degradation).

Self-evolution is a **cross-cutting concern**: affects Phase 0 (declaring level) → Phase 1 (architecture supporting rollback) → Phase 5 (safety boundaries) → Phase 6 (Harness feedback loop) → Phase 7 (Platform mode).

## Self-Evolution Level Gradient (L0–L3b)

- **L0 — Static Agent**: behavior entirely determined by code/prompt; no runtime changes.
- **L1 — Monitoring Layer**: observe own behavior, record metrics, manual analysis. Output: diagnosis report, anomaly alerts.
- **L2 — Reactive Layer**: detects known problem → executes predefined fix path. Output: automatic retry, degradation, restart.
- **L3a — Suggestion Layer**: generates improvement plan → human approval → executes. Output: PR / diff / proposal.
- **L3b — Autonomous Layer**: passes safety check → automatically applies changes → verifies. Output: automatic merge / deploy (with constraints).

**Level selection principles**:
- L0–L1: starting point for all agents; no special design needed.
- L2: requires predefined "known problem → known solution" mapping table.
- L3a: requires LLM to generate plans + human approval UI/process.
- L3b: requires complete safety framework (Circuit Breaker + test gate + rollback). **Not recommended to jump directly to this level before system matures.**

## Academic & Engineering Principles

- **DGM (Darwin Gödel Machine)** — agent uses formal proofs to verify "the proposed modification will improve performance" before applying it. Passed the proof = safe to change itself. **Mapping to LLM Agent**: LLM doesn't do formal proofs, but can use test suites instead — passes the suite = safe. Test suite is the practical approximation.
- **Voyager (Minecraft Agent)** — don't directly modify agent code; build a reusable Skill library. Each execution, agent abstracts successful behavior sequences into new Skills stored in library; next time encountering similar tasks, reuse directly. **Mapping**: Skill accumulation in Memory = Voyager's Skill library.
- **DSPy (Automatic Prompt Optimization)** — treat Prompt as a learnable parameter, automatically optimize Prompt to maximize task metrics (rather than manual writing). **Mapping**: system prompts shouldn't be hand-written and locked; they should be optimizable variables. L3b path: auto-experiment with different prompt variants, keep the ones that work better.
- **Letta (MemGPT)** — agent can actively read/write its own Memory (not just passively accumulate). CRUD own core memories, enabling self-updates. **Mapping**: memory as an editable asset — the lightest self-evolution implementation.
- **MemU (Pipeline Versioning)** — each Pipeline change produces a version (revision); versions compared by metrics; can rollback to the previous better version. **Mapping**: self-evolution requires versioning. Each modification = one revision; compare metrics = KEEP/DISCARD; fail = git reset to previous tag.

## Architectural Pattern: Self-Evolution Diagnosis Loop

All L2–L3b implementations share this basic loop: **Monitor system metrics → trigger diagnosis (scheduled or threshold) → run diagnostic tool suite → classify results (True Finding / False Positive) → generate fix candidate plans → safety check (tests + blast radius) → (L3b) auto-apply OR (L3a) proposal to human for review → verify fix effect → record to Evolution Log → update circuit breaker state.**

## Safety Boundary Design (L3b Must Implement)

### Circuit Breaker

`EvolutionCircuitBreaker` tracks `consecutive_failures` with states `CLOSED` (normal) / `OPEN` (self-evolution halted). `record_result(success)` resets counter on success; otherwise increments — once `consecutive_failures >= failure_threshold` (default 3), state flips to `OPEN` and a human-intervention alert fires. `is_allowed()` returns `state == "CLOSED"`. Requires an external `success_reset` count to close the breaker again.

### Blast Radius Limit

Define two allowlist/blocklist sets as module constants:

- **`SAFE_EVOLUTION_ZONES`**: `config/prompts/**` (prompts can be auto-modified), `memory/**` (memory can be auto-modified).
- **`FORBIDDEN_ZONES`**: `src/auth/**` (auth code), `src/security/**` (security code), `.github/workflows/**` (CI/CD).

`check_blast_radius(patch)` walks `patch.modified_files` and returns False if any file matches a forbidden zone via `fnmatch` → human approval required.

### Test Gate (Before/After Comparison)

`safe_apply_patch(patch, test_suite)`:
1. Apply on an **isolated branch** (`create_isolation_branch()`).
2. Run the full test suite on the branch.
3. **Zero regression check** (stricter than delta check): no test that was `passed` before is `failed` after. Any regression → rollback.
4. **Overall metrics must improve** — `result.delta > 0` required. Otherwise rollback.
5. Only on all checks passing: merge.

## Self-Evolution Evolution Log Design

### Quick Start: Record Feedback with Shell Script

Lowest-cost starting approach — no Python, no framework:

```bash
cp /path/to/agentforge-evolution/scripts/record_feedback.sh ./scripts/
chmod +x ./scripts/record_feedback.sh

./scripts/record_feedback.sh prompt "PR review suggestions contain 'please' and other redundant words" ""
./scripts/record_feedback.sh harness "Stop hook triggers on npm install, infinite loop" "Add stop_hook_active detection"
./scripts/record_feedback.sh context "Response quality drops after 180K tokens" ""
```

Summarize by category via `jq`/`python3` one-liners to find highest-frequency issues. Script has no `jq` / Python dependency, just bash. `EVOLUTION_LOG` env var overrides output file path.

### Evolution Log Format

Audit trail + debug foundation for self-evolution. JSONL, one entry per run. Fields: `run_id`, `timestamp`, `trigger` (what caused this diagnosis cycle), `diagnosis` (`finding`, `confidence`, `evidence[]`), `patch` (`type`, `diff`, `blast_radius`), `test_result` (`before {pass, fail}`, `after {pass, fail}`, `regressions`), `decision` (`KEEP` / `DISCARD`), `circuit_breaker` (`CLOSED` / `OPEN`).

## Self-Evolution Level × agentforge Phase Cross-Impact

| Phase | L1 | L2 | L3a (Human Approval) | L3b (Auto-Execute) |
|-------|----|----|--------------|--------------|
| **0 Spec** | Declare target level | Predefined fix mapping table | Approval flow design | Safety framework needs |
| **1 Architecture** | No special needs | State persistence | Versioned storage | git worktree isolation |
| **4 Memory** | Record diagnosis history | Fix template library | Skill accumulation (Voyager) | Auto CRUD Memory |
| **5 Security** | Audit log | Circuit breaker | Approval UI | Circuit Breaker + Blast Radius |
| **6 Harness** | Monitoring hook | Auto-retry hook | PR approval hook | Test gate hook |
| **7 Multi-Agent** | — | — | — | Platform needs invariant rules to guard behavior bottom line |
| **8 Ship** | — | — | — | Auto PR + version number management |

## Production Trajectory Infrastructure (Hermes Pattern)

> Academic analogies (DGM/Voyager/DSPy) now implemented in production. Hermes (NousResearch, 40K+ stars) is the reference implementation.

### Trajectory Collection Architecture

**ShareGPT format + outcome split** is the minimal viable trajectory infrastructure. `save_trajectory(trajectory, model, completed)` appends to `trajectory_samples.jsonl` (positive examples, task completed) or `failed_trajectories.jsonl` (negative examples, task failed). Both files directly compatible with Axolotl / TRL / Unsloth fine-tuning pipelines. **Split from day one** — retrofitting the split after thousands of mixed trajectories is costly.

- `trajectory_samples.jsonl` → positive examples → supervised fine-tuning.
- `failed_trajectories.jsonl` → negative examples → DPO / RLHF preference training.

### Training Data Hygiene: `ephemeral_system_prompt`

When running batch trajectory collection (benchmarks, bootstrapping), inject persona/environment context via an `ephemeral_system_prompt` field that is **not saved to trajectories**. Without this, batch-generation context leaks into training data and teaches the model to expect personas it won't see in production. **Rule**: only production-identical system prompts should appear in saved trajectories.

### Reasoning Chain Normalization

Before saving reasoning-model trajectories, normalize reasoning tags: `<REASONING_SCRATCHPAD>…</REASONING_SCRATCHPAD>` → `<think>…</think>` (required for DeepSeek-R1 / reasoning model fine-tuning pipelines). **Guard**: never save truncated reasoning chains — if `<think>` is present but `</think>` is missing, discard.

### RL Training Toolset Pattern (Tinker-Atropos)

The agent can manage its own training runs from inside the agent loop via tools: `rl_list_environments`, `rl_select_environment`, `rl_get_current_config`, `rl_edit_config`, `rl_start_training`, `rl_check_status`, `rl_stop_training`, `rl_get_results`, `rl_list_runs`, `rl_test_inference`. Enables the full closed loop: collect trajectories → analyze failures → start training run → check status → get results → test inference → deploy if improved.

**When to implement**: L3b agents only. Requires training infrastructure already in place. The toolset is worthless without the backend.

### Automated Prompt Optimization (Behavioral Benchmark Pattern)

Rather than hand-tuning per-model behavioral guidance, generate it from behavioral benchmarks. Process: (1) run behavioral benchmark suite against model family; (2) identify systematic failure modes (e.g. "GPT tends to describe actions instead of taking them"); (3) generate corrective instructions targeting each failure mode; (4) benchmark again to verify correction; (5) commit generated constants (e.g. `OPENAI_MODEL_EXECUTION_GUIDANCE`, `GOOGLE_MODEL_OPERATIONAL_GUIDANCE`) to source with verification date.

This is DSPy's "prompt as learnable parameter" in production — the constants are code artifacts produced by an optimization process, not human intuition.

### Hindsight Pattern (Retrospective Analysis)

After-action analysis loop that converts completed trajectories into skill improvements:

```
Trajectory archived (completed=True)
    ↓
Hindsight analyzes: "What decision pattern led to success?"
    ↓
Extracts: reusable procedure, edge case handling, error recovery steps
    ↓
Creates or patches skill via skill_manage()
    ↓
Benchmark validates skill improves future performance
    ↓
Skill committed to skills library
```

The loop is: **experience → analysis → skill crystallization → faster future execution.** Without Hindsight, successful trajectories accumulate but don't compound. With it, every success raises the baseline.

### Automated Hashimoto Loop (L3b Target)

The manual Hashimoto Loop (Phase 6) has a fully automated variant: agent attempts task → trajectory saved (`completed=False` if failed) → Hindsight diagnoses "what capability/constraint was missing?" → `skill_manage()` patches relevant skill (auto-apply with security scan) → benchmark verifies recurrence prevented → repeat. Closes the loop without human involvement. **Prerequisites**: trajectory infrastructure, skills security scan, behavioral benchmark. Build in this order — don't attempt automated Hashimoto without all three.

## Known Limitations (Uncrossable Boundaries)

1. **Self-evolution cannot evolve its own evolution mechanism** (Gödel limitation, practical version) — L3b modifying the safety framework = bypassing safety checks = disaster. Solution: Circuit Breaker, test gate, Blast Radius itself listed in `FORBIDDEN_ZONES`; forbidden from auto-modification.
2. **LLM-generated fix plan credibility has an upper limit** — Even if tests pass, LLM-generated code may have hidden semantic errors (tests don't cover). Auto-apply forbidden on core paths (authentication, security, data integrity).
3. **Metrics Goodhart's Law** — Optimizing observable metrics causes agent to find "workarounds that game metrics without solving real problems" (e.g. deleting error logs to lower `error_rate`). Mitigation: multi-dimensional metrics + human regular spot-check of Evolution Log.
4. **Bitter Lesson applies** — As LLM capabilities improve, L2/L3a manual rule systems may be replaced by "just give a better base model." Self-evolution complexity should decrease as model capability increases, not solidify.

## Delayed-Feedback Evolution: A Different Safety Model

The L0–L3b framework, Circuit Breaker, and test-gate safety mechanisms all assume **fast feedback loops** — you can verify within seconds whether a modification worked (tests pass/fail, benchmark runs, syntax check). This assumption holds for coding agents but breaks for agents where true outcome takes days, weeks, or longer.

### The Fast-Feedback Assumption and Where It Breaks

- **Fast feedback (default)** — modification → immediate verification → keep/discard within seconds. Examples: coding agents (tests), translation agents (human rating), classification agents.
- **Delayed feedback (needs different safety model)** — modification → action taken → outcome observed after days/weeks. Any agent whose quality metric requires real-world downstream consequences over extended time.

### Why Standard Safety Mechanisms Fail

1. **Circuit Breaker needs immediate failure signal** — assumes you know a modification failed quickly. In delayed-feedback scenarios, by the time you detect failure, many more decisions have been made under the bad configuration.
2. **Test gates don't exist** — there's no unit test for "this decision was correct in hindsight."
3. **Benchmark-based evaluation is degenerate** — backtests or simulations don't faithfully represent future outcomes (past data can't test decisions about future states).
4. **Goodhart's Law hits harder** — without ground-truth feedback, any proxy metric gets gamed.

### The Delayed-Feedback Safety Pattern

When your agent operates in a delayed-feedback environment, apply these additional constraints beyond standard L2/L3b:

1. **Minimum observation window** — before any parameter update, require N complete decision→outcome cycles of real data. Never update from theoretical backtests alone. N must be large enough that noise averages out — "3 samples" is always too few.
2. **Shadow mode first** — new parameters run in "shadow mode": they compute what they would do, but the live agent still uses old parameters. Compare shadow decisions to live decisions over the full observation window before promoting shadow to live.
3. **Reversible-only modifications** — only allow self-evolution on parameters whose effects can be undone by reverting. Never self-evolve on parameters that trigger irreversible actions (capital allocation, resource commitment, external communications).
4. **Outcome attribution gate** — before accepting a modification's benefit, verify the improvement correlates with the modification, not with external conditions changing. Requires control groups or A/B tests — single-agent before/after is insufficient.
5. **Human-in-the-loop escalation** — any modification crossing a "significant impact" threshold (defined per-domain) requires human approval before promotion from shadow to live, regardless of metrics.

### When to Apply This Pattern

Apply delayed-feedback safety if **any** of these are true:
- The agent's quality metric requires observing future real-world outcomes (not simulations).
- The action-to-outcome lag exceeds modification frequency (you'd update parameters faster than you can evaluate the previous update).
- Actions have compounding effects — today's action changes what information tomorrow's decision sees.
- The environment is non-stationary — historical performance doesn't predict future performance.

### Relationship to Consequence Severity (Phase 0)

Delayed-feedback scenarios almost always overlap with HIGH consequence severity (see agentforge-spec six-layer feasibility check). The two safety layers compose: consequence severity forces human-in-the-loop at **decision** time; delayed-feedback safety forces it at **modification** time. Both gates must be passed.

### Empirical Evidence: Autonomy Drift Is Real

> Source: Adaline Labs, "Multi-Agent Systems Need a Product Control Plane" — https://labs.adaline.ai/p/multi-agent-systems-product-control-plane (verified 2026-04-12).

Adaline tracked Anthropic API usage between **October 2025 and January 2026** and documented measurable autonomy drift — agents running longer and with less human oversight, **not because developers consciously raised the autonomy slider, but because the system drifted there on its own**:

- 99.9th-percentile session length grew from **10 minutes → 40 minutes** (4× in 3 months).
- Human interventions dropped from **5.4 → 3.3 per session** (−39%).

This is exactly the failure mode the Delayed-Feedback Safety Pattern is designed to catch: even without any explicit "evolution" step, the **system state** evolves beyond the original design envelope. The observation-window requirement, attribution gate, and human-escalation threshold exist to make such drift **observable and reversible** before it compounds.

**Actionable rule**: track session length p99.9 and intervention rate as **first-class self-evolution metrics**. If either moves > 50% without an intentional rollout, treat it as an unplanned evolution event and trigger the attribution gate — even if the agent's apparent quality metric looks fine.

## Minimal Runnable Self-Evolution Implementation

Minimum L1 → L2 implementation suitable for PoC — `MinimalSelfEvolution(config_path, test_cmd)` with:

- **`diagnose()`** — reads config, fetches current metrics, returns `{issue, current}` if an anomaly threshold is crossed (e.g. `error_rate > 0.05`), else `None`.
- **`generate_patch(diagnosis)`** — LLM (or rule) generates a plan. Example: for `high_error_rate`, bump `max_retries` by 1 and return `{key, old, new}`.
- **`apply_and_verify(patch)`** — if circuit breaker is open, reject. Otherwise: back up config → apply patch → run test suite → on failure, rollback + increment circuit-breaker failure count + log `DISCARD`; on success, reset circuit breaker + log `KEEP`.
- **`_log(patch, decision, notes)`** — append JSONL entry `{timestamp, patch, decision, notes}` to `evolution_log.jsonl`.

This is intentionally 60 lines of code — it demonstrates the pattern without requiring LLM integration, and can be extended progressively toward L3a/L3b.

## Current Status (April 2026)

1. **L1–L2 have production-validated cases** — Multiple self-evolving Platform systems have completed 10+ diagnosis cycles in production; true positive rate ~60–65%; limited automatic merge implemented. L1/L2 maturity is sufficient for production Harness design.
2. **L3b still in research/experimental stage** — Fully autonomous code generation + automatic merge has very few real-world cases, mainly because LLM code-generation reliability cannot yet support zero supervision.
3. **DSPy automatic prompt optimization moving toward production** — "Prompt as a learnable parameter" has multiple open-source implementations; good entry point for L3a self-evolution via prompt optimization.
4. **Self-evolution safety framework gradually standardizing** — Circuit Breaker + Blast Radius + test gate combination has been independently discovered by multiple teams as the minimum safety set; trending toward standard pattern.

## Runtime Self-Evolution: Tool/Scaffold Hot-Swap Pattern [SWE]

A distinct variant — the agent modifies its **own tool interface or scaffold within a single session**, then continues using the updated interface. Unlike L3b (cross-session skill modification), this operates within the execution boundary of one task.

### How It Works (SWE-agent source pattern)

SWE-agent's tool system is loaded at session start from YAML config, then compiled into tool schemas. **Key insight**: tools are data, not code — the agent can generate a new tool definition, write it to a temp file, and reload it mid-session without restarting.

`DynamicToolSet.hot_swap_tool(tool_name, new_definition)`: (1) validate new definition (schema check only — no execution test); (2) replace the in-memory tool; (3) recompile schemas (injected into next LLM turn's system prompt); (4) append to session evolution log (not persisted across sessions). Each hot-swap carries a mandatory `evolution_reason` field.

### Key Design Constraints

| Constraint | Reason |
|-----------|--------|
| **In-session scope only** | Hot-swapped tools don't persist; each session starts from base scaffold |
| **Schema validation required** | Malformed tool definitions cause silent failures in next LLM turn |
| **`evolution_reason` field mandatory** | Auditability: why did the agent modify the tool? |
| **No execution test** | Unlike L3b, no test gate — agent assumes its own judgment is valid for the current task |
| **Rollback = session restart** | If hot-swap makes things worse, rollback requires aborting the session |

### When This Pattern Is Appropriate

Agent encounters tool-interface friction mid-task (output format doesn't match downstream, missing parameter needed for this task, tool description misleads LLM about capabilities):
- **Task well-scoped (single session, clear success criteria)?** → runtime tool hot-swap is appropriate.
- **Improvement general (will help all future sessions)?** → use L3b (Hermes) instead — trajectory → skill patch → benchmark → deploy. Runtime hot-swap wastes the learning; it only benefits the current session.

### Critical Difference from L3b (Hermes)

| Dimension | Runtime Hot-Swap [SWE] | L3b Automated Hashimoto [HR] |
|-----------|----------------------|------------------------------|
| Scope | Current session only | Persists across sessions |
| Validation gate | None (agent self-judgment) | Behavioral benchmark required |
| Tool modification | In-memory schema only | Writes to skill files on disk |
| Safety | Low risk (session-scoped) | High risk (circuit breaker mandatory) |
| Use case | Task-specific adaptation | Systematic capability improvement |

**Anti-pattern**: using runtime hot-swap to avoid building proper L3b infrastructure — the improvements are lost every session. If the agent hot-swaps the same tool 3+ times across different sessions, that tool needs a permanent fix via L2/L3b.

## Known Pitfalls

1. **L3b without Circuit Breaker** — Self-evolving agent enters a fix-failure loop; consecutive wrong modifications destroy the system. Circuit Breaker is the minimum requirement for L3b — without it, do not go live.
2. **Enabling self-evolution with low test coverage** — Test gate has no value: modifications in areas not covered by tests cannot be verified. Prerequisite: core-path test coverage > 80%.
3. **Evolution Log not designed** — When self-evolution-related bugs appear, you can't trace "which automatic modification introduced the problem." Establish Evolution Log starting from L2.
4. **Ignoring Goodhart's Law** — Directly optimizing `error_rate` causes the agent to delete logs, lower thresholds, and other avoidance behaviors. Multi-dimensional metrics + human review is the only defense.
5. **Self-evolution scope not bounded** — L3b without Blast Radius may modify authentication / security core code — once wrong, losses are huge. Start with `config/` and `memory/`; manually set core code as forbidden zones.

## Further Reading

| Topic | Resource |
|------|------|
| Deep Zig implementation (VTable / IR / JIT + evolution engine) | `/selfevolving-agent-architecture` |
| Prompt automatic optimization (DSPy methodology) | Search `DSPy Stanford` + `github.com/stanfordnlp/dspy` |
| Memory CRUD self-evolution (Letta mode) | `/agentforge-memory` |
| Pipeline versioning (MemU mode) | `/agentforge-harness` |
| Self-evolution Platform architecture | `/agentforge-multiagent` (Platform mode) |
| Evolution alignment & safety (game theory) | `/evolution-alignment` |
| Computational resource economics | `/computational-resource-economics` |
| Production trajectory infrastructure + RL toolset (Hermes source) | `借鉴/hermes-agent/agent/trajectory.py`, `tools/rl_training_tool.py` |
| Behavioral benchmark → auto-generated guidance | `借鉴/hermes-agent/agent/prompt_builder.py` |

## Self-Evolution Checklist

- [ ] Declared self-evolution target level in Phase 0 Spec (L0–L3b)
- [ ] L1+: monitoring system + Evolution Log design
- [ ] L2+: predefined "problem → fix" mapping + Blast Radius limit
- [ ] L3a+: LLM plan generation + human approval process
- [ ] L3b+: Circuit Breaker + test gate + core code in `FORBIDDEN_ZONES`
- [ ] Rollback mechanism (git or config backup)
- [ ] Evolution Log structured and queryable
- [ ] Avoiding Goodhart's Law (multi-dimensional metrics + human spot-check)

## Next Step

After self-evolution capability ready → **`/agentforge-benchmark`** (Phase 12: Testing, Acceptance & Benchmarking)
