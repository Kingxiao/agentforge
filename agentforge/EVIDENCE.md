# AgentForge Series — External Source Evidence Log

> Single source of truth for every external claim cited by the `agentforge-*` skills.
> Any statistic, benchmark, or specific quote in any skill file must trace back to an entry here.
> Purpose: prevent cross-session hallucination of "verified" numbers. If it's not here, it's not verified.

## How This File Works

- **One row per external source** — not per citation. A single source may be cited in multiple skills.
- **`verified` date** is the date a human or an agent actually WebFetched the URL and confirmed the claim matches the source verbatim.
- **`claims_used`** lists the specific numbers/phrases extracted, so we can re-verify quickly when re-fetching.
- **Re-verification policy**: any source older than **90 days** must be re-fetched before being cited in new skill content. Stale verification ≠ current truth.
- **Commit-guard note (2026-04-12)**: push-guard.sh now allowlists `agentforge-*` and `ai-skills/` paths for AI vendor names in commit messages — commits legitimately discussing Anthropic / OpenAI / Claude as the *subject* are passed through, while AI attribution markers (`Co-Authored-By`, `AI-generated`, etc.) remain blocked unconditionally.

## Sources

### 1. Anthropic — "Building Effective Agents"

- **URL**: https://www.anthropic.com/research/building-effective-agents
- **Authors**: Erik Schluntz, Barry Zhang
- **Published**: 2024-12-19
- **Verified**: 2026-04-12
- **Cited in**: `agentforge-spec` (Gate 0)
- **Claims used**:
  - Workflow vs Agent definitions (verbatim).
  - Five workflow patterns: Prompt chaining / Routing / Parallelization / Orchestrator-workers / Evaluator-optimizer.
  - "Augmented LLM" building block: "an LLM enhanced with augmentations such as retrieval, tools, and memory."
  - Default advice: "for many applications, optimizing single LLM calls with retrieval and in-context examples is usually enough."
  - Three implementation principles: Simplicity / Transparency / ACI.

### 2. Anthropic — "How we built our multi-agent research system"

- **URL**: https://www.anthropic.com/engineering/multi-agent-research-system
- **Published**: 2025-06-13
- **Verified**: 2026-04-12
- **Cited in**: `agentforge-multiagent` (First Decision), `agentforge-context` (Core Principles empirical anchor)
- **Claims used**:
  - "Agents typically use about 4× more tokens than chat interactions, and multi-agent systems use about 15× more tokens as chats."
  - "Multi-agent system with Claude Opus 4 as the lead agent and Claude Sonnet 4 subagents outperformed single-agent Claude Opus 4 by 90.2% on our internal research eval."
  - BrowseComp variance decomposition: "Three factors explained 95% of the performance variance" — "token usage by itself explains 80% of the variance."
  - Best-fit domains: "tasks that involve heavy parallelization, information that exceeds single context windows, and interfacing with numerous complex tools."

### 3. Anthropic — "Scaling Managed Agents: Decoupling the brain from the hands"

- **URL**: https://www.anthropic.com/engineering/managed-agents
- **Published**: 2026-04-10 (public beta launch)
- **Verified**: 2026-04-12
- **Cited in**: `agentforge-production` (Decision 1 + Current State), `agentforge-context` (Decision 13), `agentforge-security` (Credential Unreachability), `agentforge-harness` (Meta-Harness)
- **Claims used**:
  - Brain / Hands / Session three-component decoupling (verbatim).
  - Interface shape: `execute(name, input) → string`, `wake(sessionId)`, `getSession(id)`, `emitEvent(id, event)`.
  - "p50 TTFT dropped roughly 60%."
  - "p95 dropped over 90%."
  - Lazy sandbox provisioning: containers "provisioned by the brain via a tool call only if they are needed."
  - Sandbox-as-cattle: execution containers as stateless, not precious.

### 4. LangChain — "Improving Deep Agents with harness engineering"

- **URL**: https://blog.langchain.com/improving-deep-agents-with-harness-engineering/
- **Published**: 2026-03
- **Verified**: 2026-04-12
- **Cited in**: `agentforge-harness` (First Principles evidence)
- **Claims used**:
  - deepagents-cli improved from **52.8 → 66.5** on Terminal Bench 2.0 by changing only the harness.
  - Top 30 → Top 5 ranking jump.
  - Components used: LocalContextMiddleware + reasoning sandwich + test-awareness prompting.

### 5. Vercel — "We removed 80% of our agent's tools"

- **URL**: https://vercel.com/blog/we-removed-80-percent-of-our-agents-tools
- **Published**: 2025-12
- **Verified**: 2026-04-12
- **Cited in**: `agentforge-harness` (Anti-Patterns / evidence), `agentforge-tools` (Core Principle)
- **Claims used**:
  - d0 text-to-SQL agent: 16 specialized tools → 1 bash capability + sandbox.
  - Success rate: **80% → 100%**.
  - **40% fewer tokens**, **40% fewer steps**.
  - **3.5× faster** (274 s → 77 s avg response time).

### 6. Adaline Labs — "Multi-Agent Systems Need a Product Control Plane"

- **URL**: https://labs.adaline.ai/p/multi-agent-systems-product-control-plane
- **Published**: 2026-04-11
- **Verified**: 2026-04-12
- **Cited in**: `agentforge-spec` (Production Reality Check), `agentforge-multiagent` (Product Control Plane section), `agentforge-evolution` (Delayed-Feedback empirical evidence)
- **Claims used**:
  - "Only 1 in 10 agentic AI use cases reached production in the past year."
  - Four primitives: **Permissions / Handoffs / Visibility / Recovery**.
  - Autonomy drift (Oct 2025 → Jan 2026 Anthropic API analysis): 99.9th-percentile session length 10 min → 40 min; human interventions per session 5.4 → 3.3.
  - Anthropic's research system "spawned 50 subagents for simple queries" — canonical runaway delegation failure.
  - Safety classifiers at both ends of every subagent handoff.
  - Three mandatory recovery paths: retry with modified parameters / fallback to simpler workflow / escalation to human review.
  - Gartner: "40% of enterprise applications will include task-specific agents by year's end."
  - METR research: "AI task duration doubling every seven months."
  - Linux Foundation A2A Protocol: 150+ supporting organizations in first year.

### 7. Adaline Labs — "The AI Research Landscape in 2026"

- **URL**: https://labs.adaline.ai/p/the-ai-research-landscape-in-2026
- **Verified**: 2026-04-12
- **Cited in**: (background context only, not yet cited verbatim)
- **Claims used**:
  - Gartner: "40% of agentic AI projects will be canceled by 2027 due to escalating costs and unclear ROI."
  - METR: "AI task duration doubling every seven months."
  - Seven technical transitions framework (agent optimization, continual learning, world models, reasoning distillation, infrastructure constraints, beyond transformers, production reliability).

### 8. Adaline Labs — "The 5 Levels of Agentic AI in 2026"

- **URL**: https://labs.adaline.ai/p/the-5-levels-of-agentic-ai
- **Published**: 2025-06-23 (updated 2026-01-29)
- **Verified**: 2026-04-12
- **Cited in**: (reference only, not directly integrated — Karpathy autonomy slider used instead as primary framing)
- **Claims used**:
  - Five levels: Basic Responder / Router+Copilot / Partial Autonomy with LLM Planning / High Automation with Self-Improvement / Fully Autonomous AGI.
  - Level 3 examples: Claude Code, Codex, AutoGPT, BabyAGI.
  - Level 4 examples: MetaGPT, ChatDev, OpenAI Operator.

### 9. OWASP — "LLM01:2025 Prompt Injection"

- **URL**: https://genai.owasp.org/llmrisk/llm01-prompt-injection/
- **Published**: 2024-04-10 (originally); **updated 2025-04-17**
- **Verified**: 2026-04-12 (via WebSearch of OWASP page content — direct WebFetch returned skeleton only due to page JS rendering)
- **Cited in**: `agentforge-security` (Layer 1 / Prompt Injection defenses)
- **Claims used**:
  - Definition: "Prompt Injection vulnerabilities exist in how models process prompts, and how input may force the model to incorrectly pass prompt data to other parts of the model, potentially causing them to violate guidelines, generate harmful content, enable unauthorized access, or influence critical decisions."
  - Direct: "Direct prompt injections occur when a user's prompt input directly alters the behavior of the model in unintended or unexpected ways."
  - Indirect: "Indirect prompt injections occur when an LLM accepts input from external sources, such as websites or files. The content may have in the external content data that when interpreted by the model, alters the behavior of the model in unintended or unexpected ways."
  - Honest limit: "given the stochastic influence at the heart of the way models work, it is unclear if there are fool-proof methods of prevention for prompt injection."

### 10. OpenAI — "gpt-realtime and Realtime API pricing"

- **URL**: https://openai.com/api/pricing/ (direct fetch blocked 403; cross-verified via OpenAI community + openai.com/index/introducing-gpt-realtime)
- **Verified**: 2026-04-12
- **Cited in**: `agentforge-architecture` (voice agent cost anchor)
- **Claims used**:
  - gpt-realtime audio: **$32 / 1M input tokens**, **$64 / 1M output tokens**, **$0.40 / 1M cached input tokens**.
  - Cached input discount: ~90% off standard input.
  - Billing model: dual-meter (audio minutes + text tokens) for text-based context/instructions.
- **Note**: The previous claim `$0.06/min audio input, $0.24/min audio output` in agentforge-architecture is a **per-minute approximation** — OpenAI's canonical pricing is per-million-tokens. Rewrite cites to use per-million-token figures with a `$/min` rule-of-thumb in parentheses.

### 11. Liu et al. — "Lost in the Middle: How Language Models Use Long Contexts"

- **URL**: https://arxiv.org/abs/2307.03172
- **Authors**: Nelson F. Liu, Kevin Lin, John Hewitt, Ashwin Paranjape, Michele Bevilacqua, Fabio Petroni, Percy Liang
- **Published**: 2023-07 (arXiv:2307.03172)
- **Verified**: 2026-04-12
- **Cited in**: `agentforge-context` (Decision 7 — hierarchy placement rationale)
- **Claims used**:
  - Verbatim abstract: "performance can degrade significantly when changing the position of relevant information, indicating that current language models do not robustly make use of information in long input contexts."
  - U-shaped finding: "performance is often highest when relevant information occurs at the beginning or end of the input context, and significantly degrades when models must access relevant information in the middle of long contexts, even for explicitly long-context models."
  - Tasks studied: multi-document QA + key-value retrieval.

### 12. Pedro et al. — "From Prompt Injections to SQL Injection Attacks (P2SQL)"

- **URL**: https://arxiv.org/abs/2308.01990
- **Authors**: Rodrigo Pedro, Daniel Castro, Paulo Carreira, Nuno Santos
- **Published**: 2023-08 (latest revision 2025-01-27; accepted ICSE 2025)
- **Verified**: 2026-04-12
- **Cited in**: `agentforge-security` (P2SQL section), `agentforge-tools` (trust-boundary)
- **Claims used**:
  - Verbatim: "LLM-integrated applications based on Langchain are highly susceptible to P2SQL injection attacks."
  - Attack mechanism: unsanitized user prompts routed through LangChain generate malicious SQL queries.
  - Defense: "four effective defense techniques that can be integrated as extensions to the Langchain framework."
  - Venue: 47th IEEE/ACM International Conference on Software Engineering (ICSE 2025).

### 13. OpenHands — Runtime backend enumeration

- **URL**: https://github.com/All-Hands-AI/OpenHands/tree/main/openhands/runtime/impl
- **Verified**: 2026-04-12
- **Cited in**: `agentforge-security` (Layer 6 sandbox matrix)
- **Claims used**:
  - Main-branch `openhands/runtime/impl/` contains **6 subdirectories**: `action_execution`, `cli`, `docker`, `kubernetes`, `local`, `remote`.
  - **Important evolution**: Third-party runtimes (daytona, modal, e2b, runloop) were **removed from main codebase** (commit b319bea, around 2025-06) and are now maintained out-of-tree.
  - True standalone runtime backends as of 2026-04: **docker / local / remote / kubernetes** (4); `action_execution` and `cli` are supporting infrastructure, not independent sandboxes.
- **Correction needed**: Previous claim "6 runtime backends" was accurate for v0.x era (docker/local/remote + daytona/modal/e2b/runloop). For post-refactor main branch, update to "4 first-party runtime backends (docker/local/remote/kubernetes) with third-party runtimes maintained out-of-tree."

### 14. Andrej Karpathy — "2025 LLM Year in Review" + related 2025–2026 talks

- **URL**: https://karpathy.bearblog.dev/year-in-review-2025/ (primary); additional context from [ViSight: "The Decade of the Agent"](https://visight.tech/2025/06/23/the-decade-of-the-agent-andrej-karpathy-on-building-in-the-new-era-of-software/)
- **Verified**: 2026-04-12
- **Cited in**: `agentforge` (entry — Autonomy Slider framing)
- **Claims used**:
  - "When I see things like 'oh 2025 is the year of agents' I get very concerned… this is the decade of agents."
  - "An autonomy slider that lets the human decide how much control to cede to the AI."
  - Tesla analogy: basic assistance → lane keeping → navigate on autopilot → FSD supervised; each level delivers value and becomes foundation for next.
  - LLM-as-OS framing: "LLM is the CPU … context window is the RAM."
  - Phased timeline: 2025–2026 code/ops copilots + early robust UI-control; 2027–2029 memory adapters + autonomy sliders at 70–90% on scoped workflows; 2030–2035 enterprise agent platforms with measurable SLAs.

## Not Yet Verified (Claims Flagged for Future Re-check)

These appear in agentforge skill files but have NOT been independently WebFetched to their primary source. Re-verify before relying on them:

- **"5 malicious documents can manipulate output 90% of the time"** — agentforge-security RAG section. Not found in the public OWASP LLM01:2025 page content. May be from a separate research paper incorrectly attributed to OWASP. **Action**: locate primary source or demote claim to "illustrative example only."
- **"Four-layer combined defense: 73.2% → 8.7% attack success, 94.3% benign task perf"** — agentforge-security. Searched 2026-04-12; the closest match is a four-layer governance framework (Perception / Decision / Memory / Execution) in a Clausius Press paper, but it does not supply those exact percentages. **Action**: demote to "architectural pattern, stats unverified" or replace with P2SQL defense numbers (which are primary-sourced).

## Applied Corrections (2026-04-12, commit e38fc1a + follow-up)

All four corrections from the prior round have been backfilled into the skill source files:

1. ✅ **agentforge-architecture** (`SKILL.md:287-296`) — rewrote gpt-realtime pricing to per-million-token canonical form; version bumped 2.0.0 → 2.1.0. **Additional fix this round**: also discovered the `$0.06/$0.24 per minute` rule-of-thumb was stale — those values are for the deprecated **gpt-4o-realtime-preview** ($100/$200 per 1M tokens), not current gpt-realtime ($32/$64 per 1M). Recomputed correct per-minute values: **$0.019/min input + $0.077/min output** (derived from OpenAI's published 10 tok/sec user + 20 tok/sec assistant rates). Monthly example math also corrected (original had an internal inconsistency between "100 calls/day" and the claimed `$180/month` result; true answer at 10 calls/day × 2 min × 30 days × new pricing ≈ $58/month).
2. ✅ **agentforge-security** Layer 6 (`SKILL.md:173`, `zh/SKILL.md:380`) — updated to "4 first-party backends (docker/local/remote/kubernetes) in main codebase; third-party runtimes moved out-of-tree mid-2025"; version 2.0.0 → 2.1.0.
3. ✅ **agentforge-security** RAG section (`SKILL.md:198`, `zh/SKILL.md:417`, `references/rag-prompt-injection.md:3`) — removed unverified "5 docs / 90%" claim; replaced with OWASP's verbatim direct/indirect definitions and OWASP's honest "no fool-proof prevention" limit.
4. ✅ **agentforge-security** 4-layer defense stats — removed unverified "73.2% → 8.7% / 94.3%" numbers from the same section; reframed the four layers as defense-in-depth pattern (structural content preserved, unsourced stats demoted).

**Lesson**: Rule-of-thumb numbers often fossilize past model-generation prices. When bumping a model reference, always recompute derived figures from first principles (tokens/sec × price/token), don't blindly copy the old `$/min` value.

## Verification Protocol (for future agents updating this file)

1. Before adding a new claim to any `agentforge-*/SKILL.md`, check if the source already exists here. If yes, verify the `verified` date is < 90 days old.
2. If source is not here, or is stale, **WebFetch the source** and extract the exact quote.
3. Add a row to this file with: URL, publication date, verification date, claims_used (verbatim quotes), and which skill cites it.
4. In the skill file itself, cite as: `Source: <description> — <url> (verified YYYY-MM-DD)`.
5. When a source is older than 90 days **and** you're editing the skill that cites it, re-fetch the URL and either update the `verified` date (if content still matches) or correct the skill (if content has changed).

**Iron rule**: No claim in `agentforge-*` skill files without a corresponding row here. If you find one, it's an audit debt — add it to "Not Yet Verified" above and schedule a fetch.
