---
name: agentforge-spec
description: AgentForge Phase 0 - Agent requirements definition and feasibility judgment. Answer "should you build an Agent" and "what type of Agent to build" before writing any code. Triggered when user says "I want to build an Agent", "agent requirements", "agent spec", or "should I use an Agent".
triggers:
  - I want to build an Agent
  - Agent requirements
  - Agent positioning
  - should I use an Agent
  - agent spec
metadata:
  version: "2.0.0"
  last_updated: "2026-04-06"
  category: "agent-engineering"
---

# AgentForge Phase 0: Requirements Definition

> Series entry: `/agentforge` | Next: `/agentforge-architecture`
> Broader AI product judgment: `/ai-product-manager`

## 5 Questions the User Must Answer (Technical Selection Agent Auto-Decides)

> **The user only needs to answer these 5 questions.** All technical details (language, framework, model, architecture paradigm, memory system, security level, etc.) are automatically inferred by the Agent — no need to understand them.
>
> Exception: If you are in mainland China, or require only domestically accessible models, please note this when answering Question 4. The Agent will switch technical selections accordingly.

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
| **Exploration** | ¥50-200/month | Use cheap models (Gemini 3 Flash / Claude Haiku 4.5), core functionality works, occasional quality gaps on complex tasks |
| **Practical** | ¥200-1000/month | Use mainstream models (Claude Sonnet 4.6 / GPT-5.4 mini), stable quality, suitable for dozens of daily uses |
| **Production** | ¥1000+/month | Use flagship models (Claude Opus 4.6 / GPT-5.4), best quality for high-frequency or complex tasks |

> If in mainland China or requiring domestically accessible models, please specify. Selection switches to: DeepSeek / Alibaba Qwen / Baidu Qianfan, etc.

### Q5: What standard will you use to accept this Agent? (Final acceptance)

> No technical metrics needed. Describe in natural language what "success" looks like:
> - "Correctly handles 80% of our PRs, review quality on par with an intern"
> - "Saves me 2+ hours of repetitive work per week"
> - "I can recommend it to colleagues; they find it better than the old way"
>
> The Agent translates your description into measurable acceptance criteria.

---

## First Question: Should You Build an Agent?

Not every AI application needs an Agent. The core characteristic of an Agent is **autonomous looping** — perceive → reason → act → observe → reason again. If your scenario doesn't need this loop, a plain LLM API call is simpler and more controllable.

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
   → **Agent is needed**
```

### Five-Layer Feasibility Check

Agent-suitable ≠ Agent-feasible. After passing the suitability check, five more layers remain:

| Layer | Check Question | Failure Consequence |
|-------|---------------|-------------------|
| Technical | Can the LLM complete core reasoning? Are tool APIs available? | Cannot build |
| Cost | Is per-execution token cost acceptable? | Losing money |
| Supply Chain | Is the LLM/API provider stable? Is there a degradation plan? | Goes down at any moment |
| User Behavior | Can users accept Agent latency and uncertainty? | No one uses it |
| Business Model | Can Agent value cover operating costs? | Unsustainable |

## Second Question: What Type of Agent?

### Agent Type Matrix

| Type | Core Capability | Representatives | Key Challenges |
|------|----------------|-----------------|----------------|
| **Coding Agent** | Read/write code + execute commands + test verification | Claude Code, Codex, Cursor, Aider, OpenCode | Edit precision, security isolation |
| **Research Agent** | Search + read + cross-validate + synthesize | Perplexity, AutoResearch | Hallucination control (citation hallucination rate 26-37%, 2026 measured), source tracing, external validation hooks |
| **Data Agent** | Query + analyze + visualize + report | Various BI Agents | Data security, SQL injection |
| **Workflow Agent** | Orchestrate multi-step business processes | n8n AI, Zapier AI | Error recovery, idempotency |
| **Personal Agent** | Long-term memory + personalization + proactive triggers | Letta, MemU | Memory management, privacy |
| **Agent OS / Platform** | Multi-channel gateway + plugin system + Skill orchestration | OpenClaw, Goose | Multi-channel adaptation, plugin isolation |
| **GUI Agent** | Screenshot understanding + click/keyboard operations + visual feedback loop | Claude Computer Use, Browser-use, UI-TARS | Screenshot token cost (~1500/image), action precision, accidental trigger prevention |
| **Voice / Realtime Agent** | Real-time audio stream + <500ms response + bidirectional WebSocket | OpenAI Realtime API, Gemini Live | WebSocket long connection management, interruption handling, concurrent conversation isolation |

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
## ▌Technical Inference (Agent Auto-Fills, User Does Not Need to Decide)

> The following is automatically inferred by the Agent based on the user's 5 answers. If special constraints exist, note them in "User Information".

- **Agent Type**: [Agent auto-identifies: Coding / Research / Data / Workflow / Personal / GUI / Voice]
- **Interaction Pattern**: [Agent auto-selects: CLI / Web / API / Daemon / IDE Plugin / Realtime]
- **Architecture Paradigm**: [Agent auto-selects: First to Seventh Paradigm, with rationale]
- **Implementation Language**: [Agent auto-selects, with rationale]
- **LLM Model**: [Agent matches by budget tier, with estimated monthly cost]
- **Memory System**: [Agent auto-selects: file memory / chunk memory / semantic memory, with rationale]
- **Security Level**: [Agent auto-sets by usage scenario: Layer 1-6]
- **Tool Interface**: [Agent auto-designs: minimum viable / production-grade]
- **Multi-Agent**: [Agent auto-judges by task complexity: Yes / No, with rationale]
- **Capability Planes**: [Agent auto-declares: input / processing / output]
- **Cost Estimate**: [Agent auto-calculates: per-execution cost + monthly estimate, with high-consumption scenario warnings]
- **Quantified Acceptance**: [Agent translates user's natural language acceptance criteria into measurable indicators]

---
## ▌Technical Constraints (Only User-Declared Limitations)

> Only fill in items you know and actually have constraints for. Leave others blank.

- Deployment environment constraints: ___ (Example: can only deploy to company intranet, AWS only)
- Compliance requirements: ___ (Example: data must not leave country, HIPAA, SOC2)
- Mandatory language/tech stack constraints: ___ (Example: company standard is Go, cannot use Python)
```

## Current State (April 2026)

1. **Agent type boundaries are blurring** — Integration of Coding Agent and Research Agent capabilities is accelerating. Claude Code/Codex already have both code generation and deep research capabilities. Pure-type thinking is failing. Requirements should start from "capability combinations" rather than "type labels."
2. **MCP protocol becoming de facto standard** — Anthropic's Model Context Protocol adopted by OpenAI, Google, major IDEs. Tool feasibility assessment shifted from "does the API exist" to "does the MCP server exist," dramatically reducing tool-layer technical risk.
3. **Agent cost structure changing dramatically** — Mainstream model inference costs dropped 5-10x over the past 12 months (Gemini 3 Flash, Claude Haiku 4.5, etc.). High-frequency Agent scenarios previously infeasible due to cost (continuous code review, real-time data monitoring) are re-entering the feasible zone.
4. **"Agent vs Workflow" judgment remains the first question** — Anthropic's official documentation clearly distinguishes Agentic System = Agent + Workflow. Most scenarios are more reliable and cheaper with deterministic Workflow than autonomous Agent. Over-agentification is the most common requirements definition error.

## Known Pitfalls

1. **Over-agentification** — Packaging scenarios solvable via Function Calling pipeline as Agents, introducing unnecessary loop complexity and uncertainty. Solution: Strictly use the suitability decision tree. Only adopt Agent mode when "multi-step reasoning + mid-course decisions" conditions are met.
2. **Ignoring user error tolerance expectations** — Developers default to assuming users can tolerate Agent trial-and-error behavior, but enterprise users have far lower tolerance for "Agent mistakes" than expected. Solution: Explicitly label error tolerance tier in Spec stage. Move approval flow requirements forward to the requirements definition stage.
3. **Customer service / Q&A Agent acceptance expectations too high** — "AI can resolve 60-80% of tickets" is the best-case outcome for top performers, not an industry baseline. Actual data (2026): **mixed business scenarios average 35-50%**. Only high-quality knowledge base + structured questions reach 65-79%. Deflection rate is a function of "knowledge base quality," not model capability. Solution: Use specific scenarios in Q5 acceptance criteria (e.g., "correctly answers 90% of single-hop questions in product documentation") rather than percentages like "resolve 70% of tickets" that are easily misinterpreted.
3. **Cost estimation looks only at tokens, not loop** — Per-call token cost may be acceptable, but Agent loop averages 5-15 iterations — actual cost is 5-15x single-call cost. Solution: Cost estimates must use "per-task completion cost" not "per-API-call cost."
4. **Security requirements added later** — Security level not defined in Spec stage. Only discovered in Phase 5 that OS-level sandbox is needed, causing architecture refactoring. Solution: Force-fill sandbox requirements field in Agent Spec document. Lock security baseline in Phase 0.

## Further Reading

| Topic | Resource |
|-------|----------|
| Phase 1: Architecture Pattern Selection | `/agentforge-architecture` |
| Phase 5: Security Baseline & Sandbox Selection | `/agentforge-security` |
| Phase 9: Orchestrator & Task Planning | `/agentforge-autoplan` |
| AI Product Feasibility & PRD Output | `/ai-product-manager` |
| Agent Observability & Metrics Design | `/agent-observability` |
| Agent Tool System Design | `/agentforge-tools` |

## Spec Checklist

- [ ] Passed suitability decision tree (confirmed Agent needed vs. ChatBot/pipeline)
- [ ] Passed five-layer feasibility check
- [ ] Agent type determined (including GUI / Voice judgment)
- [ ] **Voice / Realtime Agent**: Confirmed "degraded path" (ASR→text→Async Generator Loop) vs "true realtime path" (WebSocket + Realtime API) — these are architecturally incompatible, Phase 1 re-selection cost is high
- [ ] Interaction pattern determined
- [ ] User profile defined
- [ ] Security requirement level clarified
- [ ] Capability planes declared (input / processing / output)
- [ ] Capability freshness check executed (WebFetch corresponding platform changelog — see `/agentforge-tools`)
- [ ] Agent Spec document output

## Next Step

Spec complete → **`/agentforge-architecture`** (Phase 1: Architecture Selection)
