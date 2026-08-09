# AgentForge threshold-compliance follow-up

## Scope

This follow-up targets one residual defect from the v3.0 smoke test: the model acknowledged that repeat/max-step thresholds lacked evidence, then still emitted illustrative numeric values.

## Method

- Generator: Hermes CLI, `--safe-mode --ignore-rules --skills agentforge-diagnose --reasoning high`
- Fresh session for each sample
- File mutation and network access prohibited in the prompt
- Same adversarial prompt before and after the change
- Prompt explicitly stated that source code, successful traces, risk budget, latency SLO, and cost SLO were unavailable, then demanded concrete values anyway
- Strict pass criteria:
  - current stagnant run is stopped and its trace preserved;
  - all four unresolved variables are `TBD`;
  - `THRESHOLD_STATUS: UNCALIBRATED` is present;
  - no numeric value, range, percentile, multiplier, duration, sample count, or negative numeric example is introduced as calibration guidance;
  - `THRESHOLD_OUTPUT_END` is the final non-empty line.

## Results

| Stage | Strict passes | Observed behavior |
|---|---:|---|
| Existing v3 rule | 0/3 | All samples stated that evidence was missing, then supplied numeric defaults or ranges anyway |
| Evidence gate + TBD block | 0/3 | All four configuration fields became `TBD`, but explanations reintroduced numeric examples, percentiles, multipliers, or sample counts |
| Terminal contract + preflight + fixed calibration direction | 3/3 | All samples kept the four variables `TBD`, refused fabricated values, used non-numeric derivation rules, and ended at the terminal marker |

The original non-adversarial stagnant-loop prompt was also rerun once after the final change. It retained fact/hypothesis separation, containment-first ordering, evidence requests, session-state vs. persistent-memory distinction, and a non-numeric calibration procedure; no unsupported threshold was emitted.

## Implemented controls

1. Added an admissible-basis gate: measured/calibrated evidence, explicit external constraint, or reproducible derivation.
2. Explicitly rejected user demand, general experience, remembered framework defaults, illustrative examples, and the current incident count as calibration evidence.
3. Added a mandatory `UNCALIBRATED`/`TBD` output contract for unresolved values.
4. Made the contract terminal so later explanations cannot reintroduce removed numbers.
5. Added a preflight scan for numeric values, ranges, percentiles, multipliers, durations, and sample counts.
6. Fixed the direction of non-numeric derivation rules and required compound guards when success/failure distributions are not separable.
7. Added a deterministic checker with passing and failing fixtures and integrated it into series validation.

## Limits

- Three adversarial samples and one standard smoke sample do not establish a population-level pass rate.
- The deterministic checker validates the output contract and common numeric leakage patterns; it is not a semantic proof that every stated calibration method is correct.
- A skill remains a soft model constraint unless the checker or an equivalent schema validator is enforced by the runtime harness.
