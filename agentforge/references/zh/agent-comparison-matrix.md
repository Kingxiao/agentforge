# 15 Agents Cross-Comparison Matrix

> Source: v1 research report + Wave 2 deep reverse engineering (2026-04-06) + Wave 7 Hermes research (2026-04-09) + Wave 8 browser-use/smolagents/SWE-agent research (2026-04-09)
> 15 production-grade Agents, 14-dimensional comparison + each Agent's killer innovation
> Note: Cursor data sourced from behavioral observation, not source code verification

## Core Architecture Comparison

| Dimension | Claude Code | Codex CLI | OpenCode | Aider | Cline | OpenClaw | OpenHands | Goose | Letta | MemU | Cursor† | Hermes | browser-use | smolagents | SWE-agent |
|------|------------|-----------|----------|-------|-------|----------|-----------|-------|-------|------|--------|--------|------------|-----------|-----------|
| **Language** | TypeScript | Rust + TS | Go | Python | TypeScript | TypeScript | Python | Rust | Python | Rust + Python | TypeScript (Electron) | Python | Python 3.11+ | Python | Python |
| **UI** | Terminal (Ink) | Terminal (ratatui) | Terminal (Bubble Tea) | Terminal (Rich) | VS Code Webview | Web + Mobile native | Web + SDK | Terminal | REST API | Library | IDE (VS Code fork) | Terminal + Gateway (iMessage/Discord/Slack) | Headless/CDP browser (multi-tab) | Terminal / Jupyter | Terminal |
| **Positioning** | CLI Agent | CLI Agent | CLI Agent | CLI Agent | IDE Extension | Agent OS (multi-channel gateway) | Research-grade Agent SDK | CLI Agent | Agent Framework | Agent Framework | IDE Agent Orchestrator | Self-improving Agent + RL training platform | Browser automation agent (web-native) | Minimal agent framework (CodeAgent paradigm) | Research coding agent (ACI principles) |
| **Agent Loop** | Async Generator | Submission-Handler | PubSub Event | Reflection Chain | Event + Proto | Plugin Gateway | Event Sourcing | Rust Agent loop | Step + Heartbeat | Workflow Pipeline | Sketch+Apply Two-Stage | AIAgent single-class (~3000 lines) + IterationBudget | 3-phase async (init/step/finalize) + IterationBudget via max_steps | CodeAgent (code-gen loop) or ToolCallingAgent (JSON loop) | Bash + tools loop with ACI constraints |
| **Tool Count** | 35+ | 15+ | 15+ | Commands only | 27 | 100+ Skill plugins | ~8 dynamically generated | MCP-based | Function set | None (steps) | ~15 built-in + MCP | Dynamic (toolset-gated, condition-filtered) | 12 core + extensible | Configurable (any Python callables) | 7 purpose-built (ACI-constrained) |
| **Edit Format** | Exact replacement | Git Patch | Exact replacement | Polymorphic (5 types) | Unified Patch | Inherited from Cline | Semantic Action | Unspecified | N/A | N/A | Sketch+Apply (self-developed MoE integrated diff) | Fuzzy patch (SequenceMatcher) | N/A (browser actions: click/type/navigate) | Code generation (Python snippets) | Exact-match str_replace + linter validation |
| **Sandbox** | Permission rules + Hook | OS-level (Seatbelt/Landlock) | Permission dialog | None | Auto-approve rules | Plugin isolation | Docker/K8s/Local/Remote/CLI/E2B | None | Tool sandbox | None | Kernel-level (Seatbelt/Landlock/seccomp) | Security scan on every skill write | CDP isolation + action param validation + training-data leak scanner | 6 tiers: Local/E2B/Docker/Modal/Blaxel/Wasm | None (process-level bash timeout) |
| **Memory** | MEMORY.md + KAIROS | Event log | SQLite + SummaryMessageID | Git history | Disk persistence | Plugin Memory | Event Store | None explicit | Block memory (core) | Hierarchical memory (core) | No native cross-session memory (Notepads manual) | MEMORY.md (semantic) + session_search FTS5 (episodic) + provider lifecycle hooks | Compacted history with <compacted_memory> boundary markers | Persistent PythonExecutor state dict (cross-step variables) | State files (/root/state.json) |
| **Multi-Agent** | 3-tier isolation (Worktree/remote/background) | Registry + messaging | Session inheritance | None | Sub-agent tool | Plugin SDK | 3 Microagent types (Knowledge/Repo/Task) | None | Multi-agent tools | None | Agent tree (recursive spawn) + /best-of-n cross-model competition, up to 8 local parallel + unlimited Cloud | Delegation lineage (parent_session_id chain) + on_delegation hook | None explicit | None explicit | None explicit |
| **Context Compression** | auto-compact + micro-compact + context-collapse + snip | Op::Compact | Summarize (truncate to post-summary) | On model switch | Condense tool | Prompt Cache stable ordering | Condenser (View/Condensation) | None explicit | Summarize + archive | None | Merkle tree incremental indexing + AST splitting | on_pre_compress hook (memory providers inject summaries) | LLM-powered step summarization, char+step threshold triggers | None (state persists in executor, not context) | Observation truncation (100K chars hard cap) |
| **Loop Detection** | Compaction circuit breaker (3x) | None explicit | None explicit | None explicit | Signature comparison (3/5 threshold) | 4 detectors + global circuit breaker (30x) | None explicit | None explicit | None explicit | None explicit | None explicit | IterationBudget (90 parent / 50 subagent cap) | consecutive_failures counter | max_steps cap | max_steps + consecutive timeout (3x) |
| **MCP** | Native support | Native support | Native support | None | Native support | Native support | Native support | Native support | Native support | None | Native support (output file optimization) | None explicit | Yes (MCP server mode) | None explicit | None explicit |
| **Prompt Cache** | Yes (static/dynamic separation) | None explicit | None | Optional | None | Yes (deterministic ordering + cache boundary) | None | None | None | None | Yes (Merkle tree incremental) | Two-layer skills cache (in-process LRU + disk mtime snapshot) | None explicit | None explicit | None explicit |
| **Prompt Variants** | None (single system prompt) | None | None | None | 11 model families × 13 components | Dynamic selection by Provider | None | None | None | None | None explicit | Per-model behavioral guidance constants (GPT/Gemini/Gemma/Grok/Codex) generated by automated benchmarks | None explicit | Structured output mode (JSON schema for thought+code) | None (single template) |

## Killer Innovations by Agent

| Agent | Killer Innovation |
|-------|------------------|
| **Claude Code** | 27 Hook events full lifecycle + 3-tier Agent isolation (Worktree/CCR/background) + multi-layer compression (4 strategies) + KAIROS append-style memory |
| **Codex CLI** | OS-level sandbox + Starlark policy engine + Guardian AI review + 27 Rust crate modular architecture |
| **OpenCode** | Go PubSub architecture (channels provide natural backpressure) + LSP deep integration (crash self-healing) + streaming delta immediate persistence |
| **Aider** | Repo Map (PageRank + binary search) + 6 edit formats (including Patch) + reflection chain (4 triggers × 3x) + 4-level Fuzzy Matching |
| **Cline** | Modular Prompt Variants (11 families × 13 components) + tool fallback chain + Proto IPC (cross-IDE) + Native/XML dual tool modes |
| **OpenClaw** | Agent OS multi-channel gateway (10+ channels) + Plugin SDK (5 types) + 4 loop detectors + Prompt Cache stable ordering |
| **OpenHands** | 6 Runtime backends + 3 Microagent types (Knowledge/Repo/Task) + Event Sourcing + Condenser dynamic compression + Security analyzer |
| **Goose** | Full-stack Rust framework + MCP first-class citizen (Extension Manager + cached versions) + ACP server + 20+ providers + 31 environment variable security blacklist |
| **Letta** | Block memory 6 CRUD types (append/replace/insert/rethink/patch) + deep copy isolation + Read-Only protection + Heartbeat chain execution + 3 rendering modes |
| **MemU** | Pipeline immutable versioning (4 atomic operations) + 3-tier memory (Category→Item→Resource) + 7-step RAG sufficiency check + 5 capability declarations + dual interceptors |
| **Cursor†** | Sketch+Apply two-stage editing (self-developed MoE 250tok/s) + Agent tree recursive spawn + /best-of-n cross-model competition + Automations event-driven always-on Agent + Merkle tree incremental indexing |
| **Hermes** | Closed learning loop (trajectory→RL toolset→benchmark→updated guidance→Hindsight) + IterationBudget with execute_code refund + skill conditions (toolset-aware show/hide) + policy-as-schema + semantic/episodic memory explicit split + session lineage tracking |
| **browser-use** | 5-step DOM serialization pipeline (CDP→AX tree fusion→paint-order→bbox→index) + event-driven watchdog pattern (15+ watchdogs, no polling) + action registry signature normalization (special params never in LLM schema) + boundary-marked compaction |
| **smolagents** | CodeAgent paradigm (Python code as action language) + persistent AST-walking executor (state dict survives across steps) + 6-tier executor abstraction (Local/E2B/Docker/Modal/Blaxel/Wasm) + Tool-to-Python-signature conversion |
| **SWE-agent** | ACI principle (interface design > model choice) + exact-match str_replace with linter feedback + constrained view windows (100 lines/16K chars) + succinct search output + blocklists as ACI decisions |

## How to Use This Matrix

1. **Selection reference**: Scan through before building an Agent; find the closest reference implementation for your needs
2. **Differentiation analysis**: What makes your Agent different from existing ones? Which dimension will you innovate on?
3. **Learning path**: Every dimension has a best-practice Agent to deeply study its source code
4. **Loop detection**: OpenClaw (4 detectors) has the most complete implementation, followed by Cline (signature + dual threshold)
5. **Prompt engineering**: Cline's Variants system is the most granular model adaptation solution

## Repository Location Index

| Agent | Local Path |
|-------|-----------|
| Claude Code | `reference-material/sanbuphy-claude-code` |
| Codex CLI | `reference-material/codex-cli` |
| OpenCode | `reference-material/opencode` |
| Aider | `reference-material/aider` |
| Cline | `reference-material/cline` |
| OpenClaw | `reference-material/openclaw-src` |
| OpenHands | `reference-material/openhands` |
| Goose | `reference-material/goose` |
| Letta | `reference-material/letta` |
| MemU | `reference-material/memu` |
| Cursor† | Closed source (behavioral observation, not source-verified) |
| Hermes | `借鉴/hermes-agent` (NousResearch, cloned 2026-04-09) |
| browser-use | `借鉴/browser-use` |
| smolagents | `借鉴/smolagents` |
| SWE-agent | `借鉴/SWE-agent` |

> † All Cursor data sourced from behavioral observation, not source code verification
> ‡ Hermes deep research report: `领域知识/multi-agents/agent-architecture-research/hermes-deep-study.md`
> 15 Agents total: Claude Code, Codex CLI, OpenCode, Aider, Cline, OpenClaw, OpenHands, Goose, Letta, MemU, Cursor†, Hermes, browser-use, smolagents, SWE-agent
