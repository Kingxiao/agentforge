# 11 Agents Cross-Comparison Matrix

> Source: v1 research report + Wave 2 deep reverse engineering (2026-04-06)
> 11 production-grade Agents, 14-dimensional comparison + each Agent's killer innovation
> Note: Cursor data sourced from behavioral observation, not source code verification

## Core Architecture Comparison

| Dimension | Claude Code | Codex CLI | OpenCode | Aider | Cline | OpenClaw | OpenHands | Goose | Letta | MemU | Cursor† |
|------|------------|-----------|----------|-------|-------|----------|-----------|-------|-------|------|--------|
| **Language** | TypeScript | Rust + TS | Go | Python | TypeScript | TypeScript | Python | Rust | Python | Rust + Python | TypeScript (Electron) |
| **UI** | Terminal (Ink) | Terminal (ratatui) | Terminal (Bubble Tea) | Terminal (Rich) | VS Code Webview | Web + Mobile native | Web + SDK | Terminal | REST API | Library | IDE (VS Code fork) |
| **Positioning** | CLI Agent | CLI Agent | CLI Agent | CLI Agent | IDE Extension | Agent OS (multi-channel gateway) | Research-grade Agent SDK | CLI Agent | Agent Framework | Agent Framework | IDE Agent Orchestrator |
| **Agent Loop** | Async Generator | Submission-Handler | PubSub Event | Reflection Chain | Event + Proto | Plugin Gateway | Event Sourcing | Rust Agent loop | Step + Heartbeat | Workflow Pipeline | Sketch+Apply Two-Stage |
| **Tool Count** | 35+ | 15+ | 15+ | Commands only | 27 | 100+ Skill plugins | ~8 dynamically generated | MCP-based | Function set | None (steps) | ~15 built-in + MCP |
| **Edit Format** | Exact replacement | Git Patch | Exact replacement | Polymorphic (5 types) | Unified Patch | Inherited from Cline | Semantic Action | Unspecified | N/A | N/A | Sketch+Apply (self-developed MoE integrated diff) |
| **Sandbox** | Permission rules + Hook | OS-level (Seatbelt/Landlock) | Permission dialog | None | Auto-approve rules | Plugin isolation | Docker/K8s/Local/Remote/CLI/E2B | None | Tool sandbox | None | Kernel-level (Seatbelt/Landlock/seccomp) |
| **Memory** | MEMORY.md + KAIROS | Event log | SQLite + SummaryMessageID | Git history | Disk persistence | Plugin Memory | Event Store | None explicit | Block memory (core) | Hierarchical memory (core) | No native cross-session memory (Notepads manual) |
| **Multi-Agent** | 3-tier isolation (Worktree/remote/background) | Registry + messaging | Session inheritance | None | Sub-agent tool | Plugin SDK | 3 Microagent types (Knowledge/Repo/Task) | None | Multi-agent tools | None | Agent tree (recursive spawn) + /best-of-n cross-model competition, up to 8 local parallel + unlimited Cloud |
| **Context Compression** | auto-compact + micro-compact + context-collapse + snip | Op::Compact | Summarize (truncate to post-summary) | On model switch | Condense tool | Prompt Cache stable ordering | Condenser (View/Condensation) | None explicit | Summarize + archive | None | Merkle tree incremental indexing + AST splitting |
| **Loop Detection** | Compaction circuit breaker (3x) | None explicit | None explicit | None explicit | Signature comparison (3/5 threshold) | 4 detectors + global circuit breaker (30x) | None explicit | None explicit | None explicit | None explicit | None explicit |
| **MCP** | Native support | Native support | Native support | None | Native support | Native support | Native support | Native support | Native support | None | Native support (output file optimization) |
| **Prompt Cache** | Yes (static/dynamic separation) | None explicit | None | Optional | None | Yes (deterministic ordering + cache boundary) | None | None | None | None | Yes (Merkle tree incremental) |
| **Prompt Variants** | None (single system prompt) | None | None | None | 11 model families × 13 components | Dynamic selection by Provider | None | None | None | None | None explicit |

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

> † All Cursor data sourced from behavioral observation, not source code verification
