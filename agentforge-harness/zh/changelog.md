# Harness Engineering Skill — Changelog

## 2026-03-26 — Initial creation
- **Created:** Complete skill with 13 tasks, 5 reference files, 1 script
- **Tested:** 6 rounds of testing, 22 bugs found and fixed
- **Key fixes:** Hook JSON format, pipe exit code bug, environment variable reliability, Plan mode shortcut, pytest marker accuracy

## 2026-04-15 — Evolution from ECC cross-harness analysis

Borrowed 4 patterns from ECC and extracted 2 from session failure observation. Net-new additions (verified absent from SKILL.md + all references before edit).

- **Changed `references/components.md`:**
  - Layer 2 — added "Iterative Retrieval for Subagent Context" (DISPATCH/EVALUATE/REFINE/LOOP with relevance-score protocol)
  - Layer 4 — added "Risk-Scored Constraints (Continuous, Not Binary)" (4-axis 0-1 scorer with graduated Allow/Review/Confirm/Block actions; complements Dry-Run Mode but doesn't replace it)
  - Layer 5 — added "Synchronous vs Asynchronous Back-Pressure" (daemon polling for multi-session drift and scheduled resource coordination; complements Long-Running Agent Harness pattern from SKILL.md)
- **Changed `references/hooks.md`:**
  - Added "Hook Gating: Profile and Disable Flags" — `HARNESS_HOOK_PROFILE` (minimal/standard/strict) + `HARNESS_DISABLED_HOOKS` env-var pattern with wrapper script
- **Changed `SKILL.md`:**
  - Anti-Patterns — added "Secondhand research as firsthand evidence"
  - Tasks — added "Adopt a Borrowed Component" (origin frontmatter, source quote with line number, 90-day re-verification horizon, adaptation notes)

- **Reason:**
  - Borrowed patterns source: ECC's `ecc2/src/observability/mod.rs:60-218` (risk scoring), `ecc2/src/session/daemon.rs:20-56` (polling), `skills/iterative-retrieval/SKILL.md` (context refinement), `scripts/lib/hook-flags.js` (gating). Each fills a concrete gap after grep-verifying absence across all agentforge-harness files.
  - Session-extracted patterns source: direct observation of this session's own failures. Assistant offloaded first-hand source reading to subagents three times, then presented the summaries as if primary. User caught the pattern each time and required a correction. The Anti-Pattern and the Borrowed Component task encode both halves of that failure.

- **Verified:** All added sections cite source file paths and line numbers inline. Grep confirmed concepts absent before edit. Changes are additive (no existing content removed). Cross-references to existing SKILL.md sections (Dry-Run Mode, Long-Running Agent Harness) noted to prevent conflict.

## How to use this changelog
Each entry records: what changed, why (which feedback entries drove it), and how the fix was verified. This is the Hashimoto Loop applied to the skill itself.
