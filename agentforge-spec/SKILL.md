---
name: agentforge-spec
disable-model-invocation: true
description: Internal AgentForge Phase 0 specification workshop. Load only when explicitly named or selected by the agentforge router; do not force this questionnaire on ordinary Agent requests.
triggers:
  - I want to build an Agent
  - Agent requirements
  - Agent positioning
  - should I use an Agent
  - agent spec
metadata:
  version: "3.0.0"
  last_updated: "2026-08-08"
  category: "agent-engineering"
---

# AgentForge Phase 0: Requirements Definition

> **Phase isolation:** This file is self-contained for its decision. References to other `/agentforge-*` skills are navigation only; do not load another phase in the same response unless the user explicitly requests a multi-phase comparison.

> Series entry: `/agentforge` | Next: `/agentforge-architecture`
> Broader AI product judgment: `/ai-product-manager`

## 5 Questions the User Must Answer (Technical Selection Agent Auto-Decides)

> Start from these five product questions, but do not hide technical choices that materially change cost, data handling, vendor commitment, deployment ownership, permissions, or user-visible behavior. Propose those choices with evidence and confirm them at the appropriate impact gate.
>
> If regional access or data residency matters, record it as a constraint and verify current compatible providers before proposing a selection.

### Q1: What will your Agent do? (Creative vision / core functionality, 1-3 sentences)

> No technical description needed. "Automatically reply to GitHub Issues", "Every morning, read competitor updates and post them to Feishu" are both valid answers.
>
> If you have multiple ideas, pick the one you most want to build first.

### Q2: Who uses it, in what scenario? (Positioning)

> Example answers:
> - "Just for myself, runs locally, average 2-3 times per day"
> - "Team of 5 engineers sharing, embedded in daily development workflow"
> - "For customers, non-technical users, accessed via web interface"
>
> This answer determines security requirements, interaction patterns, and reliability standards — the Agent infers these automatically.

### Q3: What outcome do you expect from the first version? (Initial effect expectation)

Pick the closest to your expectation:

| Tier | User Experience | Suitable For |
|------|----------------|--------------|
| **Usable** | Completes main functionality, occasional errors requiring manual handling is acceptable | Personal tools, proof-of-concept, MVP |
| **Stable** | Covers 90%+ of scenarios, edge cases have graceful degradation, no need to monitor daily | Internal team tools, stable operations |
| **Production** | Near-zero manual intervention, has monitoring, alerting, auto-recovery | External services, customer-facing, critical business processes |

### Q4: Budget tier (monthly API + infrastructure total cost range)

| Tier | Reference Amount | User Experience |
|------|----------------|-----------------|
| **Exploration** | ¥50-200/month | Optimize for learning and a narrow task set; evaluate a current low-cost model against the acceptance cases |
| **Practical** | ¥200-1000/month | Balance measured quality, latency, and cost for expected task volume |
| **Production** | ¥1000+/month | Budget for evaluation, observability, recovery, and review as well as model inference |

> These are conversation bands, not price guarantees. Calculate the actual plan from current primary pricing, task volume, retries, tools, hosting, and review cost.

### Q5: What standard will you use to accept this Agent? (Final acceptance)

> No technical metrics needed. Describe in natural language what "success" looks like:
> - "Correctly handles 80% of our PRs, review quality on par with an intern"
> - "Saves me 2+ hours of repetitive work per week"
> - "I can recommend it to colleagues; they find it better than the old way"
>
> The Agent translates your description into measurable acceptance criteria.

---

## Production Reality Check (Before Any Technical Discussion)

Agent projects often fail from unclear value, weak acceptance criteria, excessive autonomy, missing operational ownership, or costs that were measured per call rather than per completed task. Industry anecdotes and forecasts are useful warnings but do not establish a 90% prior for an individual project.

**Implication for Phase 0**: require a measurable user outcome, a simpler baseline, an explicit failure budget, per-task cost, and an owner for operation and review. If a fixed workflow meets the criteria, ship that workflow instead of introducing an Agent loop.

## Gate 0: Workflow or Agent?

> Source: Anthropic "Building Effective Agents" by Erik Schluntz & Barry Zhang (2024-12-19, https://www.anthropic.com/research/building-effective-agents). This is the **front gate** Anthropic itself recommends before any agent architecture decision.

**Definitions (verbatim from Anthropic)**:
- **Workflow** — "systems where LLMs and tools are orchestrated through predefined code paths"
- **Agent** — "systems where LLMs dynamically direct their own processes and tool usage, maintaining control over how they accomplish tasks"

**Default answer: not an agent.** Anthropic's explicit guidance: "for many applications, optimizing single LLM calls with retrieval and in-context examples is usually enough." Agentic systems "trade latency and cost for better task performance, and you should consider when this tradeoff makes sense." The autonomous nature brings "higher costs, and the potential for compounding errors."

### Augmented LLM (the atomic building block)

Before workflow or agent, the atomic unit is an **Augmented LLM**: "an LLM enhanced with augmentations such as retrieval, tools, and memory" that can generate search queries, select tools, and determine what to retain. Most production systems are composed of **one or more Augmented LLMs**, not of agents.

### Five Workflow Patterns (use before reaching for an agent)

If a plain Augmented LLM call is not enough, try these **workflow patterns** (predefined code paths) in order of simplicity — **all are simpler and more reliable than a full agent**:

1. **Prompt chaining** — fixed sequence of LLM calls, each step processes the previous output.
2. **Routing** — classify input → dispatch to one specialized sub-prompt/model.
3. **Parallelization** — run multiple LLM calls simultaneously (sectioning for independent subtasks, voting for majority-vote quality).
4. **Orchestrator–workers** — central LLM breaks down dynamic tasks and delegates to worker LLMs.
5. **Evaluator–optimizer** — one LLM generates, another critiques, loop until acceptance.

**Decision order**:
```
Single Augmented LLM call → Can solve? → Yes: stop here
      ↓ No
Prompt chaining / Routing / Parallelization → Can solve? → Yes: stop here
      ↓ No
Orchestrator–workers / Evaluator–optimizer → Can solve? → Yes: stop here
      ↓ No
Agent (autonomous loop) — proceed to First Question below
```

**Anthropic's three implementation principles** (apply whether workflow or agent):
1. **Simplicity** — maintain it in agent design; every added component must earn its keep.
2. **Transparency** — explicitly show the planning steps so humans can audit.
3. **Agent-computer interface (ACI)** — craft through thorough tool documentation and testing. (Phase 2 agentforge-tools elaborates.)

**Iron rule**: if Gate 0 can be satisfied by a workflow or an Augmented LLM, **do not build an agent**. The cheapest, most reliable agent is the one you didn't build.

## First Question: Should You Build an Agent?

Not every AI application needs an Agent. The core characteristic of an Agent is **autonomous looping** — perceive → reason → act → observe → reason again. If Gate 0 above already gave you a workflow solution, this section doesn't apply. Only proceed here when workflow patterns have been ruled out.

### Agent Suitability Decision Tree

```
What does your scenario need?
│
├─ Single input → output (translation, summarization, classification)
│  → No Agent needed, direct API call
│
├─ Multi-turn dialogue but no side effects (customer service, Q&A)
│  → No Agent needed, use ChatBot
│
├─ External tool calls but fixed steps (check weather → format → return)
│  → No Agent needed, use Function Calling pipeline
│
└─ Needs any of the following:
   ├─ Multi-step reasoning + mid-course decisions ("search code first, then analyze, then modify")
   ├─ Side-effect execution (modify files, run commands, call APIs)
   ├─ Cross-session state persistence (remembers what was done before)
   └─ Dynamic tool selection (decides which tool to use based on situation)
   → **Agent is needed** — but first, check if someone already built it ↓
```

### Existing Solution Scan (Before Building)

> Users who pass the suitability check may still jump into custom architecture before evaluating existing products, APIs, or deterministic automation. Compare those options against the same acceptance criteria; do not assume a universal coverage percentage.

Before designing a custom Agent, search for existing solutions:

```
Does an off-the-shelf product/action already do this?
│
├─ GitHub PR review → anthropics/claude-code-action (free, API cost only)
├─ Slack/Discord bot → OpenClaw built-in Channel plugins
├─ Code generation in IDE → Cursor / Cline / Claude Code (already exist)
├─ Web scraping + analysis → browser-use / Playwright + LLM
├─ Data analysis pipeline → smolagents CodeAgent + pandas
│
└─ Search strategy:
   1. Search "[your use case] AI agent" or "[your use case] GitHub Action"
   2. Check MCP server registry (modelcontextprotocol.io) for existing tool integrations
   3. Check if your target platform (GitHub/Slack/Notion) has an official AI integration
```

**Decision**: score existing solutions against weighted acceptance criteria and test the highest-coverage option first. Build custom only when an unmet requirement is material enough to justify ownership cost; do not use a universal coverage cutoff.

### Five-Layer Feasibility Check

Agent-suitable ≠ Agent-feasible. After passing the suitability check, five more layers remain:

| Layer | Check Question | Failure Consequence |
|-------|---------------|-------------------|
| Technical | Can the LLM complete core reasoning? Are tool APIs available? | Cannot build |
| Cost | Is per-execution token cost acceptable? (include non-LLM costs — see cost formula below) | Losing money |
| Supply Chain | Is the LLM/API provider stable? Is there a degradation plan? | Goes down at any moment |
| User Behavior | Can users accept Agent latency and uncertainty? | No one uses it |
| Business Model | Can Agent value cover operating costs? | Unsustainable |
| **Consequence Severity** | If the Agent's output is wrong, what happens? | Ranges from "minor inconvenience" to "irreversible real-world harm" |

**Consequence Severity tiers** (determines required human-in-the-loop level):

| Tier | If Agent is wrong... | Required safeguard |
|------|---------------------|-------------------|
| **Low** | User wastes time, redoes task (code review, summarization) | Standard approval flow |
| **Medium** | Incorrect information published, reputation damage (content agent, research agent) | Human review before external output |
| **High** | Financial loss, legal liability, safety risk (trading, medical, legal agents) | Human approval on every consequential action + domain expert review of acceptance criteria |

This is not a domain-specific check — it's a **universal consequence assessment**. The Agent itself doesn't need to know about finance or medicine; it needs to know "my output triggers irreversible real-world actions" and escalate accordingly.

## Second Question: What Type of Agent?

### Agent Type Matrix

| Type | Core Capability | Representatives | Key Challenges |
|------|----------------|-----------------|----------------|
| **Coding Agent** | Read/write code + execute commands + test verification | Claude Code, Codex, Cursor, Aider, OpenCode | Edit precision, security isolation |
| **Research Agent** | Search + read + cross-validate + synthesize | Perplexity, AutoResearch | Citation entailment, source tracing, freshness, disagreement handling, and domain-specific verification |
| **Data Agent** | Query + analyze + visualize + report | Various BI Agents | Data security, SQL injection |
| **Workflow Agent** | Orchestrate multi-step business processes | n8n AI, Zapier AI | Error recovery, idempotency |
| **Personal Agent** | Long-term memory + personalization + proactive triggers | Letta, MemU | Memory management, privacy |
| **Agent OS / Platform** | Multi-channel gateway + plugin system + Skill orchestration | OpenClaw, Goose | Multi-channel adaptation, plugin isolation |
| **GUI Agent** | DOM/AX tree or screenshot observation + action execution + event-driven verification | browser-use, computer-use APIs, UI-TARS | DOM/AX paths reduce image usage but may miss visual state; screenshot paths add vision cost and coordinate uncertainty. Measure task-level reliability and verify the current provider's image accounting before budgeting. |
| **Voice / Realtime Agent** | Real-time audio stream + low-latency response + bidirectional WebSocket | Current realtime-capable providers | Long-connection management, interruption handling, concurrent isolation, latency budget, and current provider pricing; verify before selection |
| **Learning Agent** | Trajectory capture + skill synthesis + self-benchmark + closed learning loop | Hermes (NousResearch) | Validation gate design (no gate = error amplification), ephemeral context hygiene in training data, RL infrastructure coupling |

### Research Agent Search Strategy Design Points

Research Agents must define search strategy combinations in the Spec stage — otherwise later-stage hallucination control is just plugging holes:

| Strategy | Description | Tool Dependencies |
|----------|-------------|------------------|
| **Multi-source cross-validation** | ≥3 independent sources support core conclusions; single sources not trusted | WebSearch × N |
| **Site-limited search** | `site:arxiv.org`, `site:github.com`, `site:docs.xxx` | WebSearch with site: parameter |
| **Recency filtering** | Limit by publication date (last 6/12 months), filter stale info | WebSearch with time parameters |
| **Citation chain tracing** | Trace conclusions back to original sources; reject unverified secondhand summaries | WebFetch for original documents |
| **Grey literature** | HN, Reddit, tech blogs (supplements academic/official document blind spots) | WebSearch + WebFetch |

**Decision point in Spec stage**: Wrong strategy combination makes Agent output confidence fundamentally uncontrollable. Different combinations demand different architectures — multi-source validation needs concurrent WebSearch; citation tracing needs WebFetch deep-reading capability; grey literature needs Agent capable of judging source credibility.

### Interaction Pattern Selection

| Pattern | Suitable Scenarios | Technical Constraints |
|---------|-------------------|----------------------|
| **CLI** | Developer tools, automation scripts | Needs TUI framework |
| **IDE Plugin** | Coding assistance, code review | Needs Bridge API |
| **Web Service** | Multi-user, remote access | Needs auth, concurrency control |
| **API/SDK** | Integrated by other systems | Needs documentation, version management |
| **Multi-channel Gateway** | Same Agent serves Telegram/Slack/Web/CLI, etc. | Needs Channel adapter layer [OW] |
| **Background Daemon** | Continuous monitoring, auto-trigger | Needs process management, logging |

## Third Question: Who Is It For?

### User Profile Definition

Answer these questions:

1. **Technical level**: Developer? Operations? End user?
   - Developers → Can expose low-level details (logs, tool calls)
   - Non-technical users → Must hide complexity (results only)

2. **Usage environment**: Local? Cloud? Restricted network?
   - Local → Can use filesystem, shell
   - Cloud → Needs sandbox, resource limits

3. **Error tolerance expectations**: How much error is acceptable?
   - High fault tolerance (exploratory tasks) → Loose constraints
   - Zero fault tolerance (production operations) → Strict approval + sandbox

### Latent Requirements Discovery Layer (Reduces Communication Round-Trips)

What users say they want is often not their true need. The Agent Spec stage must preset a "latent requirements discovery" mechanism — otherwise the Agent spends large numbers of rounds on clarification and confirmation:

| Discovery Strategy | Implementation | Applicable Scenarios |
|-------------------|---------------|---------------------|
| **Context inference** | Analyze user's historical operations (file structure, recent commits, existing config) to infer intent | Coding Agent (read code to guess task) |
| **Proactive clarification question tree** | Generate minimum necessary question set (2-3), rather than asking at each step | Complex task Agent |
| **Implicit memory accumulation** | Extract user preferences from past conversations (language, style, conventions) into memory | Personal Agent / long-term usage |
| **Intent before literal** | Before executing, output "My understanding of your intent is X" for user confirmation — do not execute literal instructions | High-risk operations (delete/publish) |

**Decision point in Spec stage**: Which discovery strategy does your Agent need? Different strategies map to different architectures (context inference needs tool access, memory accumulation needs persistence, intent confirmation needs flow-interrupting UI). Lock this in Phase 0 to avoid later refactoring.

## Output: Agent Spec

After completing the 5 required questions, output the following document. **[User]** fields are answered by the user; **[Agent]** fields are automatically inferred by the Agent — user does not need to fill these.

```markdown
# Agent Spec: [Agent Name]

---
## ▌User Information (User Fills, 5 Questions)

### Creative Vision & Core Functionality [User]
[Describe what the Agent does in 1-3 sentences, no technical description needed]

### Target Users & Scenarios [User]
[Who uses it, where, how frequently]

### Initial Effect Expectation [User]
[ ] Usable (occasional errors acceptable, MVP / proof-of-concept stage)
[ ] Stable (90%+ scenario coverage, team daily tool)
[ ] Production (near-zero manual intervention, critical business / external service)

### Budget Tier [User]
[ ] Exploration (¥50-200/month, high cost-performance model, core functionality sufficient)
[ ] Practical (¥200-1000/month, mainstream model, stable quality)
[ ] Production (¥1000+/month, flagship model, strongest quality for complex tasks)
[ ] Domestic-only models required (DeepSeek / Qwen / Qianfan, etc. — specify)

### Acceptance Criteria [User]
[Describe in natural language what "success" looks like]

---
## ▌Product Definition (Optional for User, Agent Can Infer from Creative Vision)

### Core Capabilities
1. ___ (Agent extracts from creative vision, user can supplement or modify)
2. ___
3. ___

### Out of Scope (Boundaries)
1. ___ (Agent infers, user confirms)
2. ___

### Data Sources (Only Needed for RAG / Knowledge Base Agents)
- Data source: ___ (Confluence / Notion / Feishu / self-built DB / ...)
- Data privacy: [ ] Can send to public internet API  [ ] Internal only (cannot send to third parties)

### Key Assumptions (Project is meaningless if assumption is wrong)
1. ___ (Example: user is willing to give Agent GitHub read access)
2. ___

---
## ▌Technical Proposal (Agent Drafts, Impact Gates Still Apply)

> Draft the following from known requirements. Confirm choices that materially affect cost, data handling, deployment ownership, vendor commitment, permissions, or user-visible behavior.

- **Agent Type**: [Agent auto-identifies: Coding / Research / Data / Workflow / Personal / GUI / Voice]
- **Interaction Pattern**: [Agent auto-selects: CLI / Web / API / Daemon / IDE Plugin / Realtime]
- **Architecture Paradigm**: [fixed workflow/no Agent loop, or one of Paradigms 1–8, with rationale]
- **Implementation Language**: [Agent auto-selects, with rationale]
- **LLM Model**: [Agent matches by budget tier, with estimated monthly cost]
- **Memory System**: [Agent auto-selects: file memory / chunk memory / semantic memory, with rationale]
- **Security Level**: [Agent auto-sets by usage scenario: Layer 1-6]
- **Tool Interface**: [Agent auto-designs: minimum viable / production-grade]
- **Multi-Agent**: [Agent auto-judges by task complexity: Yes / No, with rationale]
- **Capability Planes**: [Agent auto-declares: input / processing / output]
- **Cost Estimate**: [Agent auto-calculates using the formula below, not just per-call cost]

#### Cost Estimation Formula (mandatory — per-call cost is misleading)

```
Monthly cost = per_call_token_cost × avg_loop_iterations × daily_calls × 30
             × (1 + cache_miss_rate × cache_penalty_multiplier)

Where:
  per_call_token_cost = (input_tokens × input_price + output_tokens × output_price) / 1M
  avg_loop_iterations = 5-15 for typical Agent tasks (NOT 1)
  cache_miss_rate = 0.1-0.4 depending on prompt stability
  cache_penalty_multiplier = current_uncached_rate / current_cached_rate - 1
```

**Worked calculation template**:

- Per-call model cost = `input units × current input rate + output units × current output rate + cache/media charges`.
- Per-attempt cost = model calls + paid tools + compute/runtime.
- Per-accepted-task cost = `(all attempt costs + human review cost) / accepted tasks`.
- Monthly cost = per-accepted-task cost × expected accepted-task volume + fixed infrastructure and observability.

Use measured iteration and retry distributions. Without current pricing or network authorization, leave rates as variables and label the estimate provisional rather than naming a current model.

**Warning threshold**: reserve an explicit uncertainty/headroom margin for retries, traffic variance, cache misses, paid tools, and review. Set the margin from risk and observed variance rather than a fixed percentage.

**Non-LLM cost check** (mandatory): LLM tokens are often the minority of total Agent operating cost. After computing the LLM cost above, ask:
- Does this Agent consume paid external data APIs? (market data, geospatial, medical databases, legal corpora) → Add their monthly cost
- Does this Agent require specialized infrastructure? (GPU for local models, real-time data feeds, dedicated servers) → Add infrastructure cost
- Total system cost = LLM cost + external data cost + infrastructure cost. If total exceeds budget tier, flag before proceeding to Phase 1
- **Quantified Acceptance**: [Agent translates user's natural language acceptance criteria into measurable indicators]
- **Domain expertise flag**: [If acceptance criteria involve specialized domains (finance, medicine, law, safety-critical systems), flag: "These acceptance criteria require domain expert review — the Agent can translate them into measurable indicators but cannot assess whether they are sufficient for this domain"]

---
## ▌Technical Constraints (Only User-Declared Limitations)

> Only fill in items you know and actually have constraints for. Leave others blank.

- Deployment environment constraints: ___ (Example: can only deploy to company intranet, AWS only)
- Compliance requirements: ___ (Example: data must not leave country, HIPAA, SOC2)
- Mandatory language/tech stack constraints: ___ (Example: company standard is Go, cannot use Python)
```

## Historical Snapshot (April 2026; re-verify before use)

1. **Agent type boundaries are blurring** — Integration of Coding Agent and Research Agent capabilities is accelerating. Claude Code/Codex already have both code generation and deep research capabilities. Pure-type thinking is failing. Requirements should start from "capability combinations" rather than "type labels."
2. **MCP protocol becoming de facto standard** — Anthropic's Model Context Protocol adopted by OpenAI, Google, major IDEs. Tool feasibility assessment shifted from "does the API exist" to "does the MCP server exist," dramatically reducing tool-layer technical risk.
3. **Agent economics change quickly** — model, cache, tool, and hosted-runtime prices evolve independently. Recalculate per-completed-task cost from current primary pricing when cost affects feasibility.
4. **"Agent vs Workflow" judgment remains the first question** — Anthropic's official documentation clearly distinguishes Agentic System = Agent + Workflow. Most scenarios are more reliable and cheaper with deterministic Workflow than autonomous Agent. Over-agentification is the most common requirements definition error.

## Known Pitfalls

1. **Over-agentification** — Packaging scenarios solvable via Function Calling pipeline as Agents, introducing unnecessary loop complexity and uncertainty. Solution: Strictly use the suitability decision tree. Only adopt Agent mode when "multi-step reasoning + mid-course decisions" conditions are met.
2. **Ignoring user error tolerance expectations** — Developers default to assuming users can tolerate Agent trial-and-error behavior, but enterprise users have far lower tolerance for "Agent mistakes" than expected. Solution: Explicitly label error tolerance tier in Spec stage. Move approval flow requirements forward to the requirements definition stage.
3. **Using industry deflection percentages as acceptance criteria** — averages do not represent a specific knowledge base or ticket mix. Solution: define a representative scenario set, escalation behavior, false-answer cost, and measured target for that set.
4. **Cost estimation looks only at tokens, not loop** — per-call cost hides retries, tool calls, failed runs, and review. Solution: estimate and measure cost per accepted task.
5. **Security requirements added later** — permissions, data sensitivity, and approval points discovered after architecture selection cause rework. Solution: declare the initial risk boundary in Phase 0 and refine it in Phase 5.

## Further Reading

| Topic | Resource |
|-------|----------|
| Phase 1: Architecture Pattern Selection | `/agentforge-architecture` |
| Phase 5: Security Baseline & Sandbox Selection | `/agentforge-security` |
| Phase 10: Full-Process Orchestration | `/agentforge-autoplan` |
| AI Product Feasibility & PRD Output | `/ai-product-manager` |
| Agent Observability & Metrics Design | `/agent-observability` |
| Agent Tool System Design | `/agentforge-tools` |

## Spec Checklist

- [ ] Passed suitability decision tree (confirmed Agent needed vs. ChatBot/pipeline)
- [ ] Existing-solution scan completed against weighted acceptance criteria; material unmet requirements documented
- [ ] Passed five-layer feasibility check
- [ ] Agent type determined (including GUI / Voice judgment)
- [ ] **Voice / Realtime Agent**: Confirmed "degraded path" (ASR→text→Async Generator Loop) vs "true realtime path" (WebSocket + Realtime API) — these are architecturally incompatible, Phase 1 re-selection cost is high
- [ ] **GUI / Browser Agent**: Confirmed "web-native path" (CDP AX tree, browser-use pattern) vs "screenshot path" (Computer Use) — web-native eliminates ~1500 tokens/image cost; screenshot path required for native desktop/non-web targets. Decision is architecturally incompatible, lock down in Phase 0
- [ ] Interaction pattern determined
- [ ] User profile defined
- [ ] Security requirement level clarified
- [ ] Capability planes declared (input / processing / output)
- [ ] Capability freshness check executed (WebFetch corresponding platform changelog — see `/agentforge-tools`)
- [ ] Agent Spec document output

## Next Step

Spec complete → **`/agentforge-architecture`** (Phase 1: Architecture Selection)
