---
name: agentforge-benchmark
description: AgentForge Phase 12 — Agent testing, acceptance, and benchmark evaluation. Test layering strategy + tool call mocking + industry benchmark index (SWE-bench/WebArena/AgentBench/τ-bench) + custom benchmark design + acceptance criteria framework. Triggered when user says "agent testing", "agent acceptance", "benchmark", "SWE-bench", or "how to test an agent".
triggers:
  - agent testing
  - agent acceptance
  - benchmark testing
  - SWE-bench
  - benchmark
  - agent evaluation
  - how to test an agent
metadata:
  version: "1.0.0"
  last_updated: "2026-04-07"
  category: "agent-engineering"
---

# AgentForge Phase 12: Testing, Acceptance & Benchmarking

> Previous step: `/agentforge-evolution` (Phase 10) | Series entry: `/agentforge`
> Observability companion: `/agent-observability`

## Core Understanding

> **The fundamental difficulty of Agent testing: outputs are non-deterministic. You're not testing for "exact output" — you're testing for "reasonable behavior."**

Regular function test: given input A, expect output B.
Agent test: given task T, expect Agent to complete it with a reasonable tool call sequence, within a reasonable number of turns, producing a quality result. "Reasonable" and "quality" need to be defined first.

**Three-layer testing maps to three types of uncertainty**:

```
Level 1: Unit tests — deterministic parts of tool functions
  Uncertainty source: none (pure functions)
  Can do: precise assertions on inputs/outputs/error paths
  Cannot test: whether LLM chose the right tool

Level 2: Integration tests — tool call orchestration
  Uncertainty source: LLM selection behavior (mock it out)
  Can do: verify tools trigger correctly given a specific LLM output
  Cannot test: LLM performance on real tasks

Level 3: End-to-end task tests
  Uncertainty source: LLM involved throughout
  Can do: verify Agent task completion rate on full tasks
  Cannot test: identical results every run (need statistical sampling)
```

---

## Decision 1: Agent Test Layering

### Level 1 — Tool Unit Tests

Tool functions are the most testable part of an Agent. Inputs/outputs are deterministic, side effects controllable.

**Testing focus**:
- Schema validation (correctly rejects illegal parameters)
- Edge cases (empty files, permission denied, network timeout)
- Error message quality (includes fix suggestions, see `/agentforge-tools` Layer 2)

```python
# Python example: tool unit test
def test_file_edit_tool_rejects_nonexistent_path():
    result = file_edit_tool(path="/nonexistent/file.txt", old="x", new="y")
    assert result.error_code == "FILE_NOT_FOUND"
    assert "Glob" in result.suggestion  # Error message guides user to use Glob

def test_bash_tool_schema_validation():
    with pytest.raises(ValidationError) as exc:
        bash_tool(command=None)  # Required field missing
    assert "command" in str(exc.value)
```

### Level 2 — Tool Call Orchestration Tests (Mock LLM)

Verify that when "LLM made decision X", the tool system responds correctly.

**Mock strategy selection**:

| Strategy | Use Case | Pros/Cons |
|---------|----------|-----------|
| **Record & Replay** | Regression testing | Record real trajectories, verify behavior consistency on replay; need re-recording when trajectories change |
| **Deterministic Mock** | Single-path testing | Given fixed LLM output sequence, verify correct tool is triggered |
| **Behavior Mock** | Edge/failure paths | Simulate tool failure, timeout, permission denied — verify Agent error handling |
| **Replay + Assertion** | Harness regression | Record full tool call trajectory, assert key tools were called with expected params |

```python
# Deterministic Mock example
def test_agent_reads_file_before_edit(mock_llm):
    # Given LLM outputs "read file" then "edit file" decision sequence
    mock_llm.responses = [
        ToolCallResponse(tool="FileRead", params={"path": "/src/main.py"}),
        ToolCallResponse(tool="FileEdit", params={"path": "/src/main.py", ...}),
        TextResponse("Done"),
    ]
    agent.run("Fix the bug in main.py")
    
    calls = mock_llm.recorded_tool_calls
    assert calls[0].tool == "FileRead"      # Read first
    assert calls[1].tool == "FileEdit"      # Then edit
    assert calls[1].params["path"] == "/src/main.py"
```

### Level 3 — End-to-End Task Tests

Real LLM, real tools, full tasks. **Don't pursue bit-for-bit identical results every run — pursue statistically stable task completion rates.**

**Implementation Key Points**:
1. **Multiple sampling** — Run each test task 5-10 times, take pass rate (not single pass/fail)
2. **Task difficulty tiers** — P0 (core functionality) / P1 (common scenarios) / P2 (edge cases)
3. **Turn budget** — Set max Agent turn limit per task; exceeding = failure
4. **Acceptance method** — See "Decision 5: Acceptance Criteria Framework"

---

## Decision 2: Regression Testing Strategy

**Problem**: After an Agent update (Harness adjustment, Prompt change, model upgrade), how do you prevent previously-fixed issues from regressing?

### Bug-Driven Regression Suite

Every time an Agent failure case is found → convert it into a regression test:

```json
// regression_cases.jsonl
{
  "id": "REG-042",
  "trigger": "2026-03-15",
  "description": "Agent tries to edit a file that doesn't exist, leading to 5 rounds of failure before giving up",
  "task": "Modify the login function in src/auth.py",
  "setup": {"files": {}},  // Intentionally don't create auth.py
  "pass_criteria": "Agent discovers file doesn't exist within 2 turns via Glob, then requests clarification or terminates",
  "fail_criteria": "Agent attempts FileEdit more than once"
}
```

### Before/After Harness Change Comparison

Before changing CLAUDE.md / Hook config / system prompt:
1. Run full Level 3 tests on baseline task set, record baseline pass rate
2. Execute Harness change
3. Re-run same task set, compare pass rates
4. Pass rate drops > 5% → rollback change, analyze root cause

---

## Decision 3: Industry Benchmark Index

> **Note: These numbers change extremely fast (quarterly). Must WebFetch latest rankings before use.** Table provides benchmark definitions and selection rationale only.

| Benchmark | What It Tests | Suitable Agent Type | Get Latest Data |
|-----------|--------------|---------------------|----------------|
| **SWE-bench** | Real GitHub Issue fix capability (300+ repos) | Coding Agent | `site:swebench.com` |
| **SWE-bench Verified** | Human-curated high-quality subset, more reliable results | Coding Agent | Same |
| **HumanEval / MBPP** | Function-level code generation accuracy | Coding Agent (lower bound) | `site:paperswithcode.com` |
| **Terminal Bench 2.0** | Real terminal tasks + Harness effect verification | Coding Agent with Harness | `github.com/kodu-ai/terminal-bench` |
| **WebArena** | Real website operation task completion (e-commerce/forums/code) | GUI/Browser Agent | `webarena.dev` |
| **VisualWebArena** | Web operations with image understanding | GUI Agent (visual-enhanced) | Same |
| **OSWorld** | Full desktop OS tasks (cross-application) | Computer-use Agent | `os-world.github.io` |
| **AgentBench** | Multi-environment comprehensive Agent benchmark (8 task types) | General-purpose Agent | `github.com/THUDM/AgentBench` |
| **τ-bench (tau-bench)** | Real Tool Use scenarios (retail/airline) | Tool-use Agent | `github.com/sierra-research/tau-bench` |
| **GAIA** | General AI assistant multi-step reasoning | Research / Reasoning Agent | `huggingface.co/datasets/gaia-benchmark` |
| **MTEB** | Embedding quality multi-task evaluation | For RAG/semantic cache Agents | `huggingface.co/spaces/mteb/leaderboard` |
| **RAGAS** | RAG system specialized evaluation: Faithfulness / Answer Relevancy / Context Precision / Context Recall | RAG / Knowledge / Q&A Agent | `docs.ragas.io` |
| **DeepEval** | 14+ LLM metrics incl. G-Eval, RAG specialization (Contextual Precision/Recall) + CI integration | RAG / Knowledge Agent needing CI gates | `docs.confident-ai.com` |
| **RAGBench** | Large-scale RAG benchmark 100k+ samples, TRACe framework (strong explainability) | RAG Agent large-scale evaluation | `arxiv.org/abs/2407.11005` |

### How to Use Benchmarks to Guide Agent Development

```
What's your Agent type?
│
├─ Coding Agent → SWE-bench is the gold standard
│   ├─ Entry calibration: HumanEval (function-level, fast to run)
│   ├─ Harness effect: Terminal Bench 2.0 (before/after comparison)
│   └─ Production target: SWE-bench Verified > 30% (mid-2026 baseline)
│
├─ GUI / Browser Agent → WebArena family
│   ├─ Pure web: WebArena
│   ├─ With screenshot understanding: VisualWebArena
│   └─ Desktop GUI: OSWorld
│
├─ Tool-use Agent → τ-bench is closest to production
│   └─ Feature: real user intent noise, high tool call failure rate
│
├─ Research / General Agent → GAIA
│   └─ Feature: multi-step reasoning + tool combinations, high difficulty
│
└─ RAG / Knowledge / Q&A Agent → RAGAS is the gold standard
    ├─ Core metrics: Faithfulness (does answer match retrieved results)
    │                Answer Relevancy (does answer address the question)
    │                Context Precision (retrieval precision)
    │                Context Recall (retrieval completeness)
    ├─ Tool selection: RAGAS (lightweight, fast) / DeepEval (needs CI integration) / RAGBench (large-scale comparison)
    ├─ Note: Retrieval quality (Context Precision/Recall) and generation quality (Faithfulness) are two independent failure sources
    │         Debug by isolation: run pure retrieval evaluation first, then end-to-end
    └─ WebFetch latest scores: `docs.ragas.io` + `docs.confident-ai.com/benchmarks`
```

---

## Decision 4: Custom Benchmark Design

Build your own when industry benchmarks don't cover your scenario.

### Gold Standard Dataset Construction

```
Step 1: Collect real tasks
  → Extract from user logs, support tickets, your own actual usage
  → 50-200 tasks (representative enough, don't over-collect)

Step 2: Establish labels via human acceptance
  → For each task: execute it manually, record "expected behavior" and "acceptance criteria"
  → Don't just record "correct answer" — record "what counts as passing"

Step 3: Define metrics
  → Task completion rate (passed / total)
  → Turn efficiency (average Agent turns to complete)
  → Tool call precision (proportion of invalid tool calls)
  → Error recovery rate (proportion recovering successfully after failure)

Step 4: Automate evaluation
  → Use LLM-as-Judge or rule-based checker for auto-scoring
  → Calibrate scorer accuracy on gold standard (requiring ≥ 90% agreement with human)
```

### 0→1 Cold Start Strategy (how to build first gold samples with no historical data)

New Agent has no user logs, no historical bug records — how to build a credible benchmark dataset from scratch?

```
Three-step cold start:

Step 1: Run your Agent on real tasks yourself (seed task method)
  → List 20-30 core tasks you expect the Agent to handle
  → Execute each task using the Agent yourself, record full trajectory
  → Judge manually: pass / fail / partial pass + reasoning
  → These 20-30 human-labeled samples become gold dataset v0

Step 2: Cover edge cases (proactively inject failures)
  → Don't only collect success cases — failure cases are worth 5x more
  → Deliberately construct failure-prone scenarios:
    - File doesn't exist
    - Permission denied
    - API returns error
    - Ambiguous task description
  → Record "correct behavior": how should the Agent handle these (request clarification? graceful termination?)

Step 3: Convert bugs immediately when first discovered
  → First time you notice Agent behavior doesn't match expectations, immediately:
    1. Save the complete input that triggered the bug
    2. Record expected vs. actual behavior
    3. Add to regression test suite
  → Never "remember to add it later" — each bug is a non-reproducible gold sample
```

**Cold start minimum viable set** (minimum number to start evaluating):
- Level 1 (tool units): Cover 3 edge cases per tool = tool_count × 3
- Level 2 (orchestration integration): 5-10 typical tool call sequences
- Level 3 (end-to-end): 10-15 core scenarios + 5 intentional failure scenarios

**When to upgrade**:
- Gold samples < 20 → can only make qualitative judgments, no statistical comparison
- Gold samples 20-50 → can do simple pass rate comparison
- Gold samples > 50 → LLM-as-Judge can be trusted (calibrate agreement rate at this scale for statistical meaning)

### Metric Design Principles

**Metrics to avoid**:
- Single-run pass/fail (variance too high)
- LLM output "subjective scores" (uncalibrated)

**Metrics to use**:
- Task completion rate over N samples (statistically stable)
- Turn efficiency (prevents Agent taking circuitous route but still passing)
- Tool call Precision/Recall (which were called correctly, which were missed)

---

## Decision 5: Acceptance Criteria Framework

### Automated Acceptance vs. Manual Acceptance

| Dimension | Automated Acceptance (LLM-as-Judge) | Manual Acceptance |
|-----------|-------------------------------------|-----------------|
| Cost | Low (API call cost) | High (human-hours) |
| Speed | Fast (minutes) | Slow (hours/days) |
| Suitable for | Tasks with clear judgment criteria | Subjective / novel scenarios |
| Risk | Judge LLM's own bias | Human fatigue / criteria drift |
| Use case | Every CI run | Building gold standards, periodic spot checks |

### LLM-as-Judge Implementation

```python
JUDGE_PROMPT = """
You are a strict Agent quality evaluator.

Task: {task_description}
Success criteria: {acceptance_criteria}
Agent execution trace: {agent_trace}
Agent final output: {agent_output}

Evaluation rules:
1. Only judge whether "success criteria" is met, do not add subjective commentary
2. If a dimension isn't explicitly covered by success criteria, mark it "not applicable"
3. Output PASS / FAIL / PARTIAL + one-sentence reason

Output JSON: {"verdict": "PASS|FAIL|PARTIAL", "reason": "..."}
"""
```

**Calibration requirement**: Verify Judge accuracy ≥ 90% agreement with human on 100 human-labeled samples — otherwise the Judge is not trustworthy.

### Acceptance Criteria Template (write into Agent Spec)

```markdown
## Acceptance Criteria

### Core scenarios (all must pass)
- [ ] Scenario A: [description] → Pass criteria: [specific verifiable conditions]
- [ ] Scenario B: [description] → Pass criteria: [specific verifiable conditions]

### Performance metrics (with statistical definitions)
- Task completion rate ≥ ___% (N=___ samples)
- Average completion turns ≤ ___
- Error recovery rate ≥ ___%

### Regression protection (no degradation allowed)
- Historical bug regression suite: 100% pass
- Before/after Harness change: completion rate change < 5%
```

---

## Current State (April 2026)

1. **SWE-bench has split into three versions** — SWE-bench Lite (nearly saturated, OpenAI found training data contamination, stopped reporting), SWE-bench Verified (current mainstream, Claude Opus 4.5 tops at 80.9%), SWE-bench Pro (launched 2026, harder, Augment Code Auggie leads on this version ~15-17 points ahead of commercial products). When selecting Coding Agent benchmarks, **prefer SWE-bench Verified or Pro — do not use SWE-bench Lite**
2. **LLM-as-Judge going mainstream** — Anthropic and DeepMind both published LLM judge consistency research; on structured tasks, LLM Judge agrees with humans 85-92%, but still cannot replace humans on open-ended tasks
3. **τ-bench fills the tool-use Agent gap** — Existing benchmarks mostly test "single-turn Function Calling"; τ-bench introduces real noise (unclear user intent, mid-task tool failures) closer to production, becoming the standard acceptance platform for tool-use Agents
4. **Custom benchmarks have more commercial value than industry benchmarks** — Industry benchmarks test "general capability"; your Agent faces specific scenarios. Custom benchmark scores are the real product quality metric. Recommendation: use industry benchmarks for model selection / Harness comparison; use custom benchmarks for product acceptance

## Known Pitfalls

1. **Running once and calling pass/fail** — LLM output has randomness; single result confidence is low. Fix: Level 3 tests must sample multiple times (≥5), use pass rate not single-run result.
2. **Using stale industry benchmark numbers** — Training data cutoff means remembered benchmark scores are 6-12 months behind. Fix: WebFetch latest rankings before use; don't use numbers from memory.
3. **LLM-as-Judge uncalibrated** — Judge LLM's bias hasn't been validated against humans; evaluation results unreliable. Fix: Verify agreement rate on human-labeled gold samples, < 90% = not trustworthy.
4. **Only testing happy paths** — Regression suite only contains success cases, no edge/failure scenarios. Fix: Every time an Agent failure is found → immediately convert to regression test case, **failure cases are worth 5x more than success cases**.
5. **Putting Level 3 tests in CI** — End-to-end tests are expensive (real LLM calls), slow, and non-deterministic — not suitable for per-commit triggers. Fix: Level 1/2 → CI (every commit); Level 3 → daily scheduled runs + manual trigger before releases.

## Further Reading

| Topic | Resource |
|-------|---------|
| Harness failure diagnosis | `/agentforge-harness` |
| Observability (logs/metrics/traces) | `/agent-observability` |
| Self-evolution security test gates | `/agentforge-evolution` |
| SWE-bench official | WebFetch `swebench.com` |
| Terminal Bench 2.0 | WebFetch `github.com/kodu-ai/terminal-bench` |
| τ-bench | WebFetch `github.com/sierra-research/tau-bench` |
| MTEB Embedding leaderboard | WebFetch `huggingface.co/spaces/mteb/leaderboard` |

## Testing & Acceptance Checklist

- [ ] Tool functions have unit tests (Level 1)
- [ ] Agent orchestration logic has Mock LLM integration tests (Level 2)
- [ ] End-to-end task set + acceptance criteria defined (Level 3)
- [ ] Historical bugs converted to regression cases
- [ ] Industry benchmark reference specified (SWE-bench / τ-bench / WebArena etc., per Agent type)
- [ ] LLM-as-Judge calibrated on gold samples at ≥ 90% agreement (if using automated acceptance)
- [ ] Level 3 tests NOT triggered per CI commit (cost control)
- [ ] "Acceptance criteria" field filled in Agent Spec (see `/agentforge-spec`)
- [ ] **Research / Q&A Agent special**: acceptance includes hallucination rate spot checks (randomly sample ≥20 outputs, manually verify citation source accuracy); target <20% hallucination rate, otherwise not production-ready (2026 data: mainstream Research Agent citation hallucination rate 26-37%, Agentic RAG without external verification hooks especially high-risk)

## Reverse Audit (Diagnose Mode)

> Called by `/agentforge-diagnose` — performs D9 benchmark testing dimension static audit on existing code.

| # | Check Item | How to Check | Pass Criteria |
|---|-----------|-------------|---------------|
| B1 | Test suite exists | `find . -path "*/test*" -name "*.py" -o -path "*/test*" -name "*.ts" \| wc -l` | tests/ directory has substantial test files (>3) |
| B2 | Core tasks have e2e tests | Read test files, determine if main Agent use cases are covered | Not just unit tests — has Agent behavior-level e2e tests |
| B3 | Known failures have regression tests | `git log --since="90 days ago" --grep="fix\|bug" \| head -20` + compare test file changes | Each fix has corresponding regression test |
| B4 | Evaluation metrics quantified | `grep -rn "assert\|expect\|threshold\|success_rate" tests/` | Has explicit numeric metrics (success rate/latency/cost), not subjective judgment |
| B5 | Cost tracking | `grep -rn "usage\|token_count\|cost" src/` | Has token usage or API cost recording mechanism |

**High-probability issues**: No e2e tests (P1 cannot verify overall Agent behavior), evaluation based on subjective feel (P2 cannot quantify improvements), no cost tracking (P2 surprise bills after going live)

## Next Steps

Phase 12 complete → Agent passes acceptance → Can enter `/agentforge-autoplan` for full pipeline retrospective, or enter `/agentforge-evolution` to add self-evolution capabilities.
