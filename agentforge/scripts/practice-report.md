# agentforge Practice Verification Report

> Wave 6 Output | Verification date: 2026-04-08
> Status: historical design walkthrough, not an effectiveness benchmark. Estimates and web-verified product facts below must not be treated as current evidence.

## Verification Methodology

**Single-scenario simulation**: Using a PR Review workflow as a sample, walking through the then-current phases and estimating:
1. User cognitive cost per Phase
2. Whether deliverables match expectations
3. Gap between skill guidance and actual operation

---

## Full Cycle Walkthrough Summary

### Phase 0 (Spec) — Applicability Decision
- **Deliverable**: PR Review Agent judged suitable for Event-Driven architecture; trigger word = PR opened; single context sufficient; no long session needed
- **Cognitive cost**: Low. Decision tree is clear; conclusion in 5 minutes

### Phase 1 (Architecture) — Architecture Selection
- **Deliverable**: Reactive Loop (no persistent state) + GitHub Action trigger; selected Claude Sonnet 4.6
- **Cognitive cost**: Medium. Main architecture was clear, but choosing between GitHub Action and Webhook Server took time (15 minutes)
- **Gap found**: Skill doesn't directly mention `anthropics/claude-code-action@v1` official Action available for direct use; users go down a rabbit hole building Webhooks

### Phase 2 (Tools) — Tool Design
- **Deliverable**: Toolset confirmed = read_file + post_comment + approve/request_changes; no write needed
- **Cognitive cost**: Low. Tool minimization principle directly applicable

### Phase 3 (Context) — Context Strategy
- **Deliverable**: Static zone = system prompt + review spec; dynamic zone = diff + PR metadata; cache_control enabled
- **Cognitive cost**: Medium. TTL selection for cache_control (5min vs 1h) requires extra judgment

### Phase 4 (Memory) — Memory Strategy
- **Deliverable**: PR Review Agent needs no persistent memory (stateless); skip this Phase
- **Cognitive cost**: Extremely low. Skill's judgment logic matches directly

### Phase 5 (Security) — Security Design
- **Deliverable**: Least privilege (contents:read + pull-requests:write); no code execution; limited injection surface
- **Cognitive cost**: Low. Permission matrix is clear
- **Gap found**: Prompt injection threat (malicious Markdown in PR) underestimated; defensive hooks need to be added

### Phase 6 (Harness) — Engineering Constraints
- **Deliverable**: Stop hook verifies CI passes; GitHub Action security: pin to commit hash
- **Cognitive cost**: Medium. Hash pinning step not directly explained in skill

### Phase 7 (MultiAgent) — Multi-Agent Orchestration
- **Deliverable**: Not needed; single Agent sufficient
- **Cognitive cost**: Extremely low

### Phase 8 (Ship) — Delivery
- **Deliverable**: `.github/workflows/pr-review.yml` + README configuration guide
- **Cognitive cost**: Low. Templates directly usable

### Phase 9 (Production) — Runtime Applicability
- **Deliverable**: Not applicable for a GitHub-hosted Action; GitHub owns job scheduling and worker lifecycle. Retry, permissions, logs, and failure notification remain explicit workflow concerns.
- **Cognitive cost**: Low

### Phase 10 (Autoplan) — Full-Process Orchestration
- **Deliverable**: Record feedback.jsonl for next iteration to improve review prompt
- **Cognitive cost**: Medium. Requires user to proactively establish feedback mechanism; skill's actionable guidance lacks concreteness

---

## User Cognitive Cost Analysis

| Phase | Time Estimate | Main Bottleneck |
|-------|---------|---------|
| 0 Spec | 5 min | None |
| 1 Architecture | 20 min | GitHub Action vs Webhook selection |
| 2 Tools | 10 min | None |
| 3 Context | 15 min | TTL selection, breakpoint count limits |
| 4 Memory | 2 min | None (directly skipped) |
| 5 Security | 10 min | Injection risk judgment |
| 6 Harness | 15 min | Hash pinning not intuitive |
| 7 MultiAgent | 2 min | None (directly skipped) |
| 8 Ship | 10 min | None |
| 10 Autoplan | 15 min | Feedback mechanism lacks actionable feel |
| **Total** | **~104 min estimated** | Single walkthrough; no repeated timing or baseline |

---

## Hashimoto Loop Feedback → Fixed

| # | Gap Found | Fixed Location | Fix Date |
|---|-----------|----------|---------|
| 1 | Phase 1 missing `anthropics/claude-code-action@v1` official shortcut | agentforge-architecture/SKILL.md | 2026-04-08 |
| 2 | Phase 3 cache_control `ttl` field not documented | agentforge-context/SKILL.md + references/prompt-cache-guide.md | 2026-04-08 |
| 3 | Phase 5 Prompt injection real-world case not mentioned; threat underestimated | agentforge-security/SKILL.md | 2026-04-08 |
| 4 | Phase 0 Research Agent hallucination rate not quantified | agentforge-spec/SKILL.md + agentforge-benchmark/SKILL.md | 2026-04-08 |
| 5 | Phase 0 customer service Agent expected data distorted (60-80% misleading) | agentforge-spec/SKILL.md | 2026-04-08 |
| 6 | Phase 4 RAG+FT hybrid architecture 2026 new standard not reflected | agentforge-memory/SKILL.md | 2026-04-08 |

---

## Historical Product-Fact Checks

The following table records what the 2026-04-08 walkthrough claimed to check. It lacks retained source excerpts and is stale under `EVIDENCE.md`; re-verify primary sources before use.

| Conclusion | Source | Verification Method | Status |
|------|------|---------|------|
| GPT-5.4 mini / GPT-5.4 is correct 2026 OpenAI model | OpenAI docs | Web search | ✅ Verified |
| Gemini 3 Flash replaces Gemini 2.5 Flash | Google docs | Web search | ✅ Verified |
| Claude Haiku 4.5 / Sonnet 4.6 / Opus 4.6 | Anthropic docs | Web search | ✅ Verified |
| Research Agent citation hallucination rate 26-37% | 2026 measured data | Web search | ✅ Verified |
| Customer service deflection rate industry baseline 35-65% | Industry report | Web search | ✅ Verified |
| cache_control `{"type": "ephemeral", "ttl": "1h"}` | Anthropic SDK changelog | Web search | ✅ Verified |
| `anthropics/claude-code-action@v1` official Action | GitHub Marketplace | Web search | ✅ Verified |
| Prompt injection 2026 real-world: GitHub Copilot secrets leak | Security report | Web search | ✅ Verified |

---

## Conclusion

This walkthrough found useful routing and several documentation gaps, but one simulated scenario cannot establish series effectiveness. The ~104 and ~75 minute values were estimates without repeated measurements, raw logs, or an independent baseline; the claimed 28% improvement is therefore withdrawn. Use `tests/eval-cases.json` plus repeated, versioned runs for before/after claims.
