---
name: agentforge-diagnose
disable-model-invocation: true
description: >
  Internal AgentForge diagnosis phase. Load only when explicitly named or
  selected by the agentforge router; do not auto-trigger from generic debugging,
  audit, optimization, repository review, or live testing requests.
series: agentforge
phase: diagnose
version: 2.0
---

# agentforge-diagnose — Agent Diagnosis & Optimization

> **Positioning**: This is agentforge series' "reverse entry point." New agents start from `/agentforge-spec`; existing agents start here.
>
> Other series skills: `/agentforge` (overview)

---

## Applicable Scenarios

- Taking over an agent someone else wrote, need to quickly assess quality
- Your own agent has problems after going live, don't know the root cause
- Doing agent code review, need structured audit dimensions
- Preparing to refactor an agent, need current state assessment

---

## Four Input Modes

### Mode A: Repository Code Static Audit (Most Common)

**Trigger words**: User provides repo path / "Help me look at this agent's code" / "Audit this repository"

**Data sources**: Source code + directory structure + config files + CI/CD + dependency list + git log

**Execution protocol** (in order):
```
1. ls -la {repo_root}                          # Directory structure overview
2. Identify tech stack (package.json / Cargo.toml / go.mod / pyproject.toml)
3. Find entry file (main.py / index.ts / cmd/main.go / app.py)
4. Read entry file completely
5. Grep key patterns (see "Static audit grep list" below)
6. Read 3-5 core files (loop implementation, tool definitions, prompt files)
7. Check key config files (.env.example / CLAUDE.md / Dockerfile / .github/workflows/)
8. git log --since="90 days ago" --stat | head -50  # Recent evolution direction
9. Score each item against 9-dimension checklist
10. Output diagnosis report
```

### Mode B: Online Agent + Symptoms (Combined Static+Dynamic)

**Trigger words**: User describes "agent fails in scenario X" + optional code path

**Execution protocol**:
```
1. Collect symptoms (use "Symptom → Root Cause mapping table" for quick candidate dimension location)
2. If code path provided → Execute Mode A static audit (focus on candidate dimensions)
3. If no code → Execute Mode C
4. Output targeted diagnosis report (not full 9-dimension run, focus on high-probability root causes)
```

### Mode C: Pure Symptom Hypothesis Diagnosis (No Code Access)

**Trigger words**: User only describes symptoms, no code provided

**Execution protocol**:
```
1. Use symptom → root cause mapping table, list 2-3 candidate dimensions
2. Provide "verification steps" for each candidate (tell user what to check)
3. Provide hypothetical fix suggestions
4. Clearly label: This is hypothetical diagnosis, needs code confirmation
```

### Mode D: Live Testing (Run Agent + Probe Testing)

**Trigger words**: User says "run tests" / "diagnose after actual run" / "help me stress test this agent" / "benchmark this agent"

**Prerequisites**: Agent can start locally (has start command), or is already running (has endpoint)

**Execution protocol** (7 steps, complete flow ~30-60 minutes):

```
Step 1  Interaction type detection (~2 minutes)
        → Read README / Dockerfile / main entry, identify protocol type
        → Fill detection result into "Interaction adapter" for subsequent steps

Step 2  Environment setup + Agent startup (~5 minutes)
        → Install dependencies (pip install / npm install / cargo build)
        → Configure .env (generate test config from .env.example)
        → Start agent, wait for ready signal (port listening / process stable)
        → Record startup time + memory baseline

Step 3  L1: Existing test suite (~5 minutes)
        → Run pytest / npm test / go test
        → Record: pass rate, failed cases, coverage (if available)

Step 4  L2: Behavior probes — general capabilities (~10 minutes)
        → Select corresponding probe set by agent type (see references/probes.md)
        → Record for each probe: input, output, success, latency
        → Probes P1-P6 (see references/probes.md for details)

Step 5  L3: Stress probes — boundary behavior (~15 minutes)
        → Select directional probes by "known high-risk dimensions"
        → Probes S1-S6 (Prompt Injection / extremely long context / long session decay / tool chain depth / concurrency / error recovery)
        → Each probe: input, expected, actual output, whether triggered problem

Step 6  Collect runtime metrics (ongoing)
        → First token latency (P50/P95)
        → L2 probe success rates
        → Token usage + estimated cost/per call
        → Memory growth curve (important: detect D4 memory leak)
        → Tool call success rate (if tools available)

Step 7  Static/dynamic merged analysis
        → Static audit scores (D1-D9 baseline)
        → Use runtime evidence to adjust scores:
            · Static-found issues → Did runtime actually trigger? (confirmed vs. false positive)
            · New issues found at runtime → What did static miss? (supplementary)
        → Output merged diagnosis report (including measured data tables)
```

**Recommended combination strategy**:

| Scenario | Recommended Mode | Reason |
|------|---------|------|
| First contact with unfamiliar repo | A → D | Static assessment first, then probe verification |
| Known specific problem | B → Targeted D (L3 focus) | Use probes to verify symptom root cause |
| Pre-launch quality gate | A + D full | Complete coverage, produce baseline report |
| Daily monitoring | D L2 only | Quick health check (10 minutes) |
| No local environment | A + C | Degrade to static + hypothesis |

---

## Interaction Adapters: Select Probe Delivery Method by Agent Type

> Step 1 detection result → Select corresponding adapter

### CLI Agent (stdin/stdout)

```bash
# Detection signal: main.py / main.go reads stdin, no HTTP server
# Single turn interaction
echo "Your probe input" | python main.py

# Multi-turn interaction (use pexpect or heredoc)
python main.py << 'EOF'
turn 1 input
EOF

# With timeout
timeout 30 python main.py < probe_input.txt
```

### HTTP Agent (REST API)

```bash
# Detection signal: app.py / server.ts listens on port, has /chat or /complete route
# Startup
python app.py &  # or npm start &
sleep 3  # Wait for ready

# Single turn
curl -s -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Probe input", "session_id": "test-001"}' \
  -w "\nTime: %{time_total}s\n"

# Multi-turn (keep session_id consistent)
for turn in 1 2 3; do
  curl -s -X POST http://localhost:8080/chat \
    -d "{\"message\": \"Turn ${turn} input\", \"session_id\": \"probe-session\"}"
done
```

### SDK-based Agent (direct import)

```python
# Detection signal: No main entry, core is class/functions in agent.py
# Write probe script
import time
from agent import Agent  # or run / create_agent

agent = Agent(config={...})
start = time.time()
result = agent.run("Probe input")
latency = time.time() - start
print(f"Output: {result}\nLatency: {latency:.2f}s")
```

### MCP Server (JSON-RPC over stdio)

```bash
# Detection signal: server.py / index.ts has @mcp.tool or mcp.server import
# Startup + list tools
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python server.py

# Call tool
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"tool name","arguments":{"arg":"value"}}}' \
  | python server.py
```

### Interactive REPL (multi-turn stdin, need terminal simulation)

```python
# Detection signal: while True reads input(), interactive CLI
import pexpect
child = pexpect.spawn('python agent.py')
child.expect('>')  # Wait for prompt
child.sendline('Probe input turn 1')
output1 = child.before.decode()
child.sendline('Probe input turn 2')
output2 = child.before.decode()
child.terminate()
```

---

## Static Audit Grep List

```bash
# Tool count (tool registration count)
grep -rn "def |async def |function |tool(" src/ | grep -i "tool\|skill\|action" | wc -l

# System prompt location (whether externalized)
find . -name "*.txt" -o -name "*.md" -o -name "*.yaml" | xargs grep -l "system\|你是\|You are" 2>/dev/null
grep -rn "system_prompt\|systemPrompt\|SYSTEM_PROMPT" src/ | head -10

# Hardcoded API key / model ID
grep -rn "sk-\|api_key\s*=\s*['\"]" src/ | grep -v ".env\|example\|test"
grep -rn "gpt-4\|claude-\|gemini-" src/ | grep -v "# verified\|config\|env"

# Tool concurrency (whether Promise.all / asyncio.gather / goroutine pattern exists)
grep -rn "Promise.all\|asyncio.gather\|go func\|concurrent" src/

# Large text truncation
grep -rn "truncat\|max_token\|[:截断]" src/ | head -10

# Memory/persistence
grep -rn "sqlite\|redis\|json.dump\|pickle\|persist\|save_state" src/ | head -10

# Security-related
grep -rn "subprocess\|exec\|eval\|shell=True\|os.system" src/ | head -20
grep -rn "approval\|confirm\|human_in_loop\|require_approval" src/ | head -10

# Test coverage
find . -path "*/test*" -name "*.py" -o -path "*/test*" -name "*.ts" | wc -l
```

---

## 9-Dimension Audit Checklist

> Each dimension max 3 points, 0=severe problem, 1=obvious defect, 2=minor deficiency, 3=pass

### D1. Architecture

Reference: `/agentforge-architecture` §Reverse Audit

| # | Check | Pass Standard | Deduct If |
|---|--------|---------|---------|
| A1 | Loop paradigm identifiable | Can determine which Loop paradigm from code | Cannot determine how agent operates |
| A2 | Paradigm matches scenario | Webhook doesn't use blocking Loop; CLI Agent doesn't use Event-Driven | Paradigm selection clearly mismatched |
| A3 | No God File | All files < 500 lines | Single file > 500 lines exists |
| A4 | Single module responsibility | Loop / tools / prompt / memory each in separate files | Responsibilities mixed in same file |
| A5 | No hardcoded config | model/endpoint/key all via env vars or config files | Hardcoded API key or model ID exists |

### D2. Tools

Reference: `/agentforge-tools` §Reverse Audit

| # | Check | Pass Standard | Deduct If |
|---|--------|---------|---------|
| T1 | Tool count reasonable | ≤ 10 tools (complex agent ≤ 15) | > 15 (severe warning) |
| T2 | Tool descriptions clear | Each tool has docstring/description explaining purpose | Tool has no description or vague description |
| T3 | Supports concurrent execution | Promise.all / gather pattern exists | All tools serial, no concurrency |
| T4 | Large data not passed directly | Binary/images/large files via file reference, not stuffed into LLM | Binary stuffed directly into messages |
| T5 | Tool results have limits | Tool return results have truncation or max_length control | Tool may return unlimited-length results |

### D3. Context

Reference: `/agentforge-context` §Reverse Audit

| # | Check | Pass Standard | Deduct If |
|---|--------|---------|---------|
| C1 | Prompt externalized | System prompt in separate file, not hardcoded in source | Prompt string inline in code |
| C2 | Large text truncation strategy | Truncation logic exists for PR diff / logs / scraped results | No truncation whatsoever, fed as-is |
| C3 | Static/dynamic separation | Static instructions separated from dynamic data (cache-friendly) | Each request concatenates brand new string |
| C4 | Untrusted content isolation | External content wrapped in XML tags, placed in user message | External content mixed into system prompt |
| C5 | Inform LLM when truncating | After truncation, note "content truncated, N items total" in prompt | Silent truncation, LLM not informed |

### D4. Memory

Reference: `/agentforge-memory` §Reverse Audit

| # | Check | Pass Standard | Deduct If |
|---|--------|---------|---------|
| M1 | Memory paradigm identifiable | Can determine File/Block/Semantic approach | Cannot determine how agent persists state |
| M2 | Cross-session persistence | File/DB writes exist, state not lost after restart | All state in memory, lost on restart |
| M3 | Memory capacity bounded | Memory file/DB has max_entries or TTL | Unlimited growth, no eviction mechanism |
| M4 | Contamination protection | Deduplication/conflict checking when updating memory | Duplicate/contradictory info can be written to memory |
| M5 | Deletion supported | Can delete specific memories (right to be forgotten / error correction) | Write-only, deletion not supported |

### D5. Security

Reference: `/agentforge-security` §Reverse Audit

| # | Check | Pass Standard | Deduct If |
|---|--------|---------|---------|
| S1 | Prompt Injection protection | External input isolated via XML tags, not in system prompt | External content directly concatenated into system prompt |
| S2 | Dangerous operations require approval | rm/delete/deploy/send etc. have human approval gate | Dangerous operations fully automated, no human confirmation |
| S3 | No secret leakage | .env.example has only placeholders, no real keys | Real API keys in code or git history |
| S4 | Command injection protection | subprocess calls use list args, not string concatenation | `shell=True` + user input = injection vulnerability |
| S5 | Least privilege | Tool permissions requested as needed, no "universal root" tool | Single tool can perform arbitrary operations |

### D6. Harness

Reference: `/agentforge-harness` §Reverse Audit

| # | Check | Pass Standard | Deduct If |
|---|--------|---------|---------|
| H1 | CLAUDE.md/AGENTS.md exists | Agent instruction file in root directory | No agent context config at all |
| H2 | Test pre-commit gate | pre-commit hook or CI runs tests before commit | Destructive code can be committed |
| H3 | Progress tracking mechanism | Multi-session projects have progress.json or equivalent | Long tasks cannot recover across sessions |
| H4 | Build verification | CI runs build + lint, failures block merge | No CI or CI is just for show |
| H5 | Rules traceable | Each rule in CLAUDE.md can trace to a real failure | Rules are imaginary, no real events driving them |

### D7. Multi-Agent

Reference: `/agentforge-multiagent` §Reverse Audit

| # | Check | Pass Standard | Deduct If |
|---|--------|---------|---------|
| MA1 | Spawn pattern identifiable | Can determine which multi-agent pattern | Cannot determine how agents collaborate |
| MA2 | No circular dependencies | A→B call chain has no cycles, or has depth limit | A→B→A possible infinite loop |
| MA3 | Sub-agent context isolation | Sub-agents use fresh context, don't pollute main agent | Sub-agents share main context, mutual pollution |
| MA4 | Sub-agent result verification | Main agent does integrity check on sub-agent returns | Blindly trusts sub-agent conclusions |
| MA5 | Local failure doesn't crash global | Single sub-agent failure has degradation path | Any sub-agent failure → entire flow interrupted |

### D8. Ship

Reference: `/agentforge-ship` §Reverse Audit

| # | Check | Pass Standard | Deduct If |
|---|--------|---------|---------|
| SH1 | Deployment config complete | Dockerfile/compose or equivalent deployment solution exists | No deployment config, only runs locally |
| SH2 | Env var injection | All secrets/config via env vars, has .env.example | Config hardcoded or .env.example missing |
| SH3 | Health check | HTTP /health or equivalent check exists | No health check, deployment is a black box |
| SH4 | Rollback strategy | Version tags + rollback docs/scripts exist | Cannot quickly rollback to previous version |
| SH5 | New member reproducible | Can complete clone→configure→start purely from README | Hidden dependencies or missing key docs |

### D9. Benchmark

Reference: `/agentforge-benchmark` §Reverse Audit

| # | Check | Pass Standard | Deduct If |
|---|--------|---------|---------|
| B1 | Test suite exists | tests/ directory has substantial content | No tests, or only hello world |
| B2 | Core tasks have tests | Agent's main use cases have end-to-end tests | Only tests tool functions, not agent behavior |
| B3 | Known failures have regression tests | Regression test added after each bug fix | Same bug may appear again |
| B4 | Evaluation metrics quantified | Success rate/latency/cost have numerical baselines | Evaluation depends on "feels good/bad" |
| B5 | Cost tracking | Token usage or API cost recorded | Don't know how much each run costs |

---

## Symptom → Root Cause Mapping Table

Quick candidate dimension location, for Mode B/C.

| Symptom | Primary Dimension | Alternate Dimension | Verification Direction |
|------|---------|---------|---------|
| Long session quality degrades / late responses go wrong | D3 Context | D4 Memory | Check for truncation strategy; check if memory contaminated |
| Tool call success rate low (<80%) | D2 Tools | D3 Context | Check tool count; check tool description quality |
| Cross-session state loss | D4 Memory | D6 Harness | Check for persistence writes; check progress mechanism |
| Agent manipulated by external content | D5 Security | D3 Context | Check Prompt Injection protection |
| Same bug appears repeatedly | D6 Harness | D9 Benchmark | Check for regression tests; check if CLAUDE.md rules in place |
| Crashes immediately on launch | D8 Ship | D1 Architecture | Check deployment config; check env var injection |
| Sub-agent infinite loop | D7 Multi-Agent | D1 Architecture | Check circular dependencies; check depth limit |
| Architecture increasingly hard to maintain | D1 Architecture | D6 Harness | Check God File; check module boundaries |
| Running cost too high | D2 Tools | D3 Context | Check tool concurrency; check Prompt Cache config |
| Dangerous operations executed automatically | D5 Security | D6 Harness | Check approval gates; check permission boundaries |
| Model response quality poor | D3 Context | D1 Architecture | Check prompt structure; check if wrong model selected |
| All tests pass but fails on launch | D9 Benchmark | D8 Ship | Check for e2e tests; check deployment environment differences |

---

## Priority Calculation

```
Priority = Impact (H/M/L) × Fix Cost (1=low/2=medium/3=high)

P0 = Impact H + Fix Cost low (high-value quick win, fix immediately)
P1 = Impact H + Fix Cost medium/high (important but needs planning)
P2 = Impact M + any cost (optimization improvement)
P3 = Impact L (tech debt, schedule when possible)
```

---

## Diagnosis Report Template

```markdown
# Agent Diagnosis Report
**Report date**: {YYYY-MM-DD}
**Diagnosis mode**: Static audit (A) / Combined Static+Dynamic (B) / Hypothesis diagnosis (C) / Live Testing (D)
**Interaction type**: {CLI / HTTP / SDK / MCP / REPL} (fill when Mode D)
**Agent type**: {CLI Agent / Event-Driven HTTP / Loop-Based / ...}
**Tech stack**: {Language + Framework}

## Executive Summary
{3 sentences summarizing: biggest problem, highest risk, recommended first step}

## Runtime Metrics (Mode D only, skip for other modes)

| Metric | Value | Baseline Reference | Rating |
|------|------|---------|------|
| L1 test suite pass rate | x% | Target >95% | PASS/FAIL |
| L2 behavior probe success rate | x/6 probes | Target 6/6 | PASS/FAIL |
| L3 stress probe triggered issues | x probes | Target 0 | List triggered items |
| First token latency P50 | xms | Target <2000ms | PASS/FAIL |
| First token latency P95 | xms | Target <5000ms | PASS/FAIL |
| Token usage per call | x tokens | Baseline record | - |
| Estimated cost/per call | ¥x | Budget tier | - |
| Memory growth (after 20 turns) | +x MB | Target <50MB | PASS/WARN |
| Tool call success rate | x% | Target >90% | PASS/FAIL |

### L3 Stress Probe Details (Triggered Issue List)
| Probe | Input Summary | Expected | Actual | Triggered Issue |
|------|---------|------|------|------------|
| S1 Prompt Injection | ... | Refuse to execute | ... | ✓/✗ |
| S2 Long context | 50K tokens | Normal truncation | ... | ✓/✗ |
| S3 Session decay | 20 turns | Stable quality | ... | ✓/✗ |
| S4 Tool chain depth | Requires 3+ tools | Complete task | ... | ✓/✗ |
| S5 Concurrent requests | 5 concurrent | All respond | ... | ✓/✗ |
| S6 Error recovery | Bad input | Graceful degradation | ... | ✓/✗ |

## Dimension Scores

| Dimension | Score | Main Findings |
|------|------|---------|
| D1 Architecture | x/3 | ... |
| D2 Tools | x/3 | ... |
| D3 Context | x/3 | ... |
| D4 Memory | x/3 | ... |
| D5 Security | x/3 | ... |
| D6 Harness | x/3 | ... |
| D7 Multi-Agent | x/3 | ... |
| D8 Ship | x/3 | ... |
| D9 Benchmark | x/3 | ... |
| **Total** | **x/27** | |

## Prioritized Fix List

### P0 (Fix Immediately)
- [ ] **{Problem summary}**
  - Evidence: {Code location / grep result}
  - Risk: {Consequence of not fixing}
  - Fix direction: → See `/agentforge-{phase}` §{Specific section}
  - Estimated effort: {small/medium/large}

### P1 (This Week's Plan)
...

### P2 (Next Iteration)
...

## Items Outside This Diagnosis Scope
{List skipped check items and reasons (e.g., no code access / not currently applicable)}
```

---

## Collaboration with Other Phase Skills

After diagnosis completes, call corresponding Phase skill for fixes by priority:

```
D1 Architecture issues   → /agentforge-architecture
D2 Tool issues   → /agentforge-tools
D3 Context issues → /agentforge-context
D4 Memory issues   → /agentforge-memory
D5 Security issues   → /agentforge-security
D6 Harness    → /agentforge-harness
D7 Multi-Agent   → /agentforge-multiagent
D8 Ship issues   → /agentforge-ship
D9 Benchmark   → /agentforge-benchmark
```

After fixes complete, rerun corresponding dimension checklist to verify score improvement.

---

## Self-Evolution: Diagnosis Skill Evolution

When a new symptom-to-root-cause mapping is discovered in actual diagnosis, or when a checklist item proves to have high/low value in practice:

1. Update "Symptom → Root Cause mapping table"
2. Update corresponding checklist item (adjust weight or replace)
3. Record change and rationale in `references/changelog.md`

Follow Hashimoto Loop: New findings from each diagnosis → improve checklist → next diagnosis more accurate.
