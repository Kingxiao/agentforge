---
name: agentforge-evolution
description: AgentForge Phase 10 - Agent Self-Evolution Design. L0-L3b evolution level gradient + principles (DGM/Voyager/DSPy) + architectural patterns + safety boundaries + implementation code. Triggered when user says "self-evolving agent", "agent self-modification", "self-evolution architecture", "evolution agent".
triggers:
  - 自进化 Agent
  - Agent 自我修改
  - 自进化架构
  - evolution agent
  - self-evolving
  - self-improvement agent
metadata:
  version: "1.0.0"
  last_updated: "2026-04-07"
  category: "agent-engineering"
---

# AgentForge Phase 10: Agent Self-Evolution Design

> Previous: `/agentforge-autoplan` (Phase 9) | Series entry: `/agentforge`
> Deep Zig implementation: `/selfevolving-agent-architecture`

## Core Principles

> **Self-evolution is not "agent can modify code" — it is "agent can reliably, safely, and purposefully improve its own behavior."**

The gap between the two:
- Can modify code → Any tool call can do this
- Reliable → Has tests to verify, behavior known before and after changes
- Safe → Has rollback, has circuit breakers, has blast radius limits
- Purposeful → Modification direction aligns with system-wide goals (not local optimization causing global degradation)

Self-evolution is a **cross-cutting concern**: It affects Phase 0 (Spec declaring level) → Phase 1 (architecture supporting rollback) → Phase 5 (safety boundaries) → Phase 6 (Harness feedback loop) → Phase 7 (Platform mode).

---

## Self-Evolution Level Gradient (L0-L3b)

```
L0: Static Agent
    ↓ Behavior entirely determined by code/prompt, no runtime changes
L1: Monitoring Layer
    ↓ Observe own behavior, record metrics, manual analysis
    → Output: diagnosis report, anomaly alerts
L2: Reactive Layer
    ↓ Detects known problem → executes predefined fix path
    → Output: automatic retry, degradation, restart
L3a: Suggestion Layer
    ↓ Generates improvement plan → human approval → executes
    → Output: PR / diff / improvement proposal
L3b: Autonomous Layer
    ↓ Passes safety check → automatically applies changes → verifies
    → Output: automatic merge, automatic deployment (with constraints)
```

**Level selection principles**:
- L0-L1: Starting point for all agents, no special design needed
- L2: Requires predefined "known problem → known solution" mapping table
- L3a: Requires LLM to generate plans + human approval UI/process
- L3b: Requires complete safety framework (Circuit Breaker + test gate + rollback mechanism), **not recommended to jump directly to this level before system matures**

---

## Academic & Engineering Principles

### DGM (Darwin Gödel Machine)
**Core idea**: Agent uses formal proofs to verify "the proposed modification will improve performance" before applying it. Passed the proof = safe to change itself.
**Mapping to LLM Agent**: LLM doesn't do formal proofs, but can use test suites instead — passes the test suite = safe to change. Test suite is the practical approximation of DGM's idea.

### Voyager (Minecraft Agent)
**Core idea**: Don't directly modify agent code; instead build a reusable Skill library. Each execution, agent abstracts successful behavior sequences into new Skills stored in the library; next time encountering similar tasks, directly reuse.
**Mapping to LLM Agent**: Skill accumulation in Memory = Voyager's Skill library. Each time successfully completing a task type, extract Skill → inject into Memory → faster next time.

### DSPy (Automatic Prompt Optimization)
**Core idea**: Treat Prompt as a learnable parameter, automatically optimize Prompt to maximize task metrics (rather than manual writing).
**Mapping to LLM Agent**: System prompts shouldn't be hand-written and locked; they should be optimizable variables. One implementation path for L3b: Agent automatically experiments with different prompt variants, keeps the ones that work better.

### Letta (MemGPT)
**Core idea**: Agent can actively read and write its own Memory (not just passively accumulating). Agent can CRUD its own core memories,实现自我更新.
**Mapping to LLM Agent**: Memory as an editable asset — agent can delete stale memories, organize contradictory information, write new rules. This is the lightest self-evolution implementation.

### MemU (Pipeline Versioning)
**Core idea**: Each Pipeline change produces a version (revision); versions can be compared by metrics; can rollback to the previous better version.
**Mapping to LLM Agent**: Self-evolution requires versioning. Each modification = one revision, compare metrics = KEEP/DISCARD decision, fail = git reset to previous tag.

---

## Architectural Pattern: Self-Evolution Diagnosis Loop

All L2-L3b implementations share this basic loop:

```
┌─────────────────────────────────────────────┐
│           Self-Evolution Diagnosis Loop      │
│                                             │
│  Monitor system metrics                     │
│       ↓                                     │
│  Trigger diagnosis (scheduled or threshold) │
│       ↓                                     │
│  Run diagnostic tool suite                  │
│       ↓                                     │
│  Classify results (True Finding / False Positive) │
│       ↓                                     │
│  Generate fix candidate plans                │
│       ↓                                     │
│  Safety check (tests + blast radius)         │
│       ↓                                     │
│  ┌───────────────┐   ┌──────────────────┐   │
│  │ L3b: Pass →  │   │ L3a: Proposal to │   │
│  │ Auto-apply   │   │ human for review │   │
│  └───────────────┘   └──────────────────┘   │
│       ↓                                     │
│  Verify fix effect → Record to Evolution Log │
│       ↓                                     │
│  Update circuit breaker state               │
└─────────────────────────────────────────────┘
```

---

## Safety Boundary Design (L3b Must Implement)

### Circuit Breaker

```python
class EvolutionCircuitBreaker:
    def __init__(self, failure_threshold=3, success_reset=5):
        self.consecutive_failures = 0
        self.state = "CLOSED"  # CLOSED=normal OPEN=stop self-evolution
        self.failure_threshold = failure_threshold

    def record_result(self, success: bool):
        if success:
            self.consecutive_failures = 0
        else:
            self.consecutive_failures += 1
            if self.consecutive_failures >= self.failure_threshold:
                self.state = "OPEN"
                # Notify human intervention
                alert("Circuit breaker tripped: self-evolution halted")

    def is_allowed(self) -> bool:
        return self.state == "CLOSED"
```

### Blast Radius Limit

```python
SAFE_EVOLUTION_ZONES = [
    "config/prompts/**",     # Prompts can be auto-modified
    "memory/**",             # Memory can be auto-modified
]

FORBIDDEN_ZONES = [
    "src/auth/**",           # Auth code forbidden from auto-modification
    "src/security/**",       # Security code forbidden from auto-modification
    ".github/workflows/**",  # CI/CD forbidden from auto-modification
]

def check_blast_radius(patch: Patch) -> bool:
    for file in patch.modified_files:
        if any(fnmatch(file, zone) for zone in FORBIDDEN_ZONES):
            return False  # Touched forbidden zone → human approval required
    return True
```

### Test Gate (Before/After Comparison)

```python
def safe_apply_patch(patch: Patch, test_suite: TestSuite) -> bool:
    # 1. Apply on isolated branch
    branch = create_isolation_branch()
    apply(patch, branch)

    # 2. Run tests
    result = test_suite.run(branch)

    # 3. Zero regression check (stricter than delta check)
    regressions = [t for t in result.before if t.passed
                   and not result.after_map[t.id].passed]
    if regressions:
        rollback(branch)
        return False

    # 4. Overall metrics must improve
    if result.delta <= 0:
        rollback(branch)
        return False

    # 5. Commit
    merge(branch)
    return True
```

---

## Self-Evolution Evolution Log Design

### Quick Start: Record Feedback with Shell Script

Lowest-cost starting approach — no Python, no framework needed:

```bash
# Install (copy script to project scripts/ directory)
cp /path/to/agentforge-evolution/scripts/record_feedback.sh ./scripts/
chmod +x ./scripts/record_feedback.sh

# Usage: Record immediately after discovering agent behavior issue
./scripts/record_feedback.sh prompt "PR review suggestions contain 'please' and other redundant words, user must clean twice" ""
./scripts/record_feedback.sh harness "Stop hook triggers on npm install, infinite loop" "Add stop_hook_active detection"
./scripts/record_feedback.sh context "Response quality noticeably drops after 180K tokens, need earlier compression trigger" ""

# View records
cat evolution_log.jsonl | python3 -c "import sys,json; [print(json.dumps(json.loads(l), ensure_ascii=False)) for l in sys.stdin]"

# Summarize by category (find highest frequency issues)
cat evolution_log.jsonl | python3 -c "
import sys, json, collections
entries = [json.loads(l) for l in sys.stdin]
c = collections.Counter(e['category'] for e in entries)
for cat, count in c.most_common():
    print(f'{count:3d}  {cat}')
"
```

> Script: `agentforge-evolution/scripts/record_feedback.sh`
> No jq dependency, no Python dependency, just bash. `EVOLUTION_LOG` env var can override output file path.

### Evolution Log Format

Evolution Log is the audit trail and debugging foundation for self-evolution systems:

```json
{
  "run_id": 42,
  "timestamp": "2026-04-07T10:30:00Z",
  "trigger": "error_rate_threshold_exceeded",
  "diagnosis": {
    "finding": "context_compression_too_aggressive",
    "confidence": 0.78,
    "evidence": ["avg_response_quality: -15%", "user_corrections: +30%"]
  },
  "patch": {
    "type": "config_change",
    "diff": "compression_threshold: 80000 -> 100000",
    "blast_radius": "config/context.yaml"
  },
  "test_result": {
    "before": {"pass": 145, "fail": 5},
    "after": {"pass": 148, "fail": 2},
    "regressions": 0
  },
  "decision": "KEEP",
  "circuit_breaker": "CLOSED"
}
```

---

## Self-Evolution Level & agentforge Phase Cross-Impact

> Level description (see gradient definition above): L1 = Monitoring, L2 = Reactive, L3a = Suggestion (human approval), L3b = Autonomous (auto-apply)

| Phase | L1 | L2 | L3a (Human Approval) | L3b (Auto-Execute) |
|-------|----|----|--------------|--------------|
| **0 Spec** | Declare target level | Predefined fix mapping table | Approval flow design needs | Safety framework needs |
| **1 Architecture** | No special needs | State persistence | Versioned storage | git worktree isolation |
| **4 Memory** | Record diagnosis history | Fix template library | Skill accumulation (Voyager mode) | Auto CRUD Memory |
| **5 Security** | Audit log | Circuit breaker mechanism | Approval UI | Circuit Breaker + Blast Radius |
| **6 Harness** | Monitoring hook | Auto-retry hook | PR approval hook | Test gate hook |
| **7 Multi-Agent** | — | — | — | Platform type needs invariant rules to guard behavior bottom line, prevent self-evolution from losing control |
| **8 Ship** | — | — | — | Auto PR + version number management |

---

## Known Limitations (Uncrossable Boundaries)

1. **Self-evolution cannot evolve its own evolution mechanism** (Gödel limitation practical version) — L3b modifies safety framework = bypassing safety checks = disaster. Solution: Circuit Breaker, test gate, Blast Radius itself listed in FORBIDDEN_ZONES, forbidden from auto-modification.

2. **LLM-generated fix plan credibility has an upper limit** — Even if tests pass, LLM-generated code may have hidden semantic errors (tests don't cover). Auto-apply forbidden on core paths (authentication, security, data integrity).

3. **Metrics Goodhart's Law** — Optimizing observable metrics causes agent to find "workarounds that game metrics without solving real problems" (e.g., deleting error logs to lower error_rate). Mitigation: Multi-dimensional metrics + human regular spot-check of Evolution Log.

4. **Bitter Lesson applies** — As LLM capabilities improve, L2/L3a manual rule systems may be replaced by "just give a better base model." Self-evolution complexity should decrease as model capability increases, not solidify.

---

## Minimal Runnable Self-Evolution Implementation (Python / Any Language Generic)

Minimum implementation from L1 → L2, suitable for Proof of Concept:

```python
import json, subprocess, datetime
from pathlib import Path

class MinimalSelfEvolution:
    def __init__(self, config_path: str, test_cmd: str):
        self.config_path = Path(config_path)
        self.test_cmd = test_cmd
        self.evo_log = Path("evolution_log.jsonl")
        self.circuit_failures = 0
        self.FAILURE_THRESHOLD = 3

    def diagnose(self) -> dict | None:
        """Run diagnosis, return discovered problem (or None)"""
        # Simple example: check thresholds in config
        config = json.loads(self.config_path.read_text())
        metrics = self._get_current_metrics()
        if metrics["error_rate"] > 0.05:
            return {"issue": "high_error_rate", "current": metrics["error_rate"]}
        return None

    def generate_patch(self, diagnosis: dict) -> dict | None:
        """Generate fix plan based on diagnosis (LLM can be plugged in here)"""
        if diagnosis["issue"] == "high_error_rate":
            config = json.loads(self.config_path.read_text())
            new_val = config.get("max_retries", 3) + 1
            return {"key": "max_retries", "old": config.get("max_retries", 3), "new": new_val}
        return None

    def apply_and_verify(self, patch: dict) -> bool:
        if self.circuit_failures >= self.FAILURE_THRESHOLD:
            return False  # Circuit breaker open

        # Backup
        backup = self.config_path.read_text()

        # Apply modification
        config = json.loads(backup)
        config[patch["key"]] = patch["new"]
        self.config_path.write_text(json.dumps(config, indent=2))

        # Run tests
        result = subprocess.run(self.test_cmd.split(), capture_output=True)

        if result.returncode != 0:
            # Rollback
            self.config_path.write_text(backup)
            self.circuit_failures += 1
            self._log(patch, "DISCARD", result.stderr.decode())
            return False

        self.circuit_failures = 0
        self._log(patch, "KEEP", "tests passed")
        return True

    def _log(self, patch, decision, notes):
        entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "patch": patch, "decision": decision, "notes": notes
        }
        with self.evo_log.open("a") as f:
            f.write(json.dumps(entry) + "\n")
```

---

## Current Status (April 2026)

1. **L1-L2 have production-validated cases** — Multiple self-evolving Platform systems have completed 10+ diagnosis cycles in production, true positive rate ~60-65%, implemented limited automatic merge. L1/L2 maturity is sufficient for production Harness design.
2. **L3b still in research/experimental stage** — Fully autonomous code generation + automatic merge has very few real-world agent cases, mainly because LLM code generation reliability cannot yet support zero supervision.
3. **DSPy automatic prompt optimization moving toward production** — The idea of treating Prompt as a learnable parameter has multiple open-source implementations, suitable for starting L3a self-evolution from prompt optimization.
4. **Self-evolution safety framework gradually standardizing** — Circuit Breaker + Blast Radius + test gate combination independently discovered by multiple teams as the minimum safety set, trending toward becoming a standard pattern.

## Known Pitfalls

1. **L3b without Circuit Breaker** — Self-evolving agent enters fix failure loop, consecutive wrong modifications destroy system. Circuit Breaker is the minimum requirement for L3b — without it, cannot go live.
2. **Enabling self-evolution with low test coverage** — Test gate has no value: modifications in areas not covered by tests cannot be verified. Self-evolution prerequisite: core path test coverage > 80%.
3. **Evolution Log not designed** — When self-evolution-related bugs appear, cannot trace "which automatic modification introduced the problem". Evolution Log must be established starting from L2.
4. **Ignoring Goodhart's Law** — Directly optimizing error_rate causes agent to delete logs, lower thresholds and other avoidance behaviors. Multi-dimensional metrics + human review is the only defense.
5. **Self-evolution scope not bounded** — L3b without Blast Radius limit may modify authentication, security and other core code — once wrong, losses are huge. Start with config/ and memory/, manually set core code as forbidden zones.

## Further Reading

| Topic | Resource |
|------|------|
| Deep Zig implementation (VTable/IR/JIT + evolution engine) | `/selfevolving-agent-architecture` |
| Prompt automatic optimization (DSPy methodology) | Search `DSPy Stanford` + `site:github.com/stanfordnlp/dspy` |
| Memory CRUD self-evolution (Letta mode) | `/agentforge-memory` |
| Pipeline versioning (MemU mode) | `/agentforge-harness` |
| Self-evolution Platform architecture | `/agentforge-multiagent` (Platform mode) |
| Evolution alignment & safety (game theory perspective) | `/evolution-alignment` |
| Computational resource economics (evolution under cost constraints) | `/computational-resource-economics` |

## Self-Evolution Checklist

- [ ] Declared self-evolution target level in Phase 0 Spec (L0-L3b)
- [ ] L1+: Has monitoring system + Evolution Log design
- [ ] L2+: Has predefined "problem→fix" mapping, has Blast Radius limit
- [ ] L3a+: Has LLM plan generation + human approval process
- [ ] L3b+: Circuit Breaker implemented + test gate implemented + core code in FORBIDDEN_ZONES
- [ ] Has rollback mechanism (git or config backup)
- [ ] Evolution Log structured and queryable
- [ ] Avoiding Goodhart's Law (multi-dimensional metrics + human spot-check)

## Next Step

After self-evolution capability ready → **`/agentforge-benchmark`** (Phase 11: Testing, Acceptance & Benchmarking)
