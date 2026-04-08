# Key Code Path Index + Glossary

> Sources: v1 research + Wave 2 deep reverse engineering (2026-04-06)
> Source code learning navigation map. Each module annotated with file path and approximate scale.

## Claude Code (TypeScript)

| Module | Path | Notes |
|-------|------|-------|
| Main loop | `src/query.ts` | 1729 lines, infinite while loop, 6 continue checkpoints |
| Query engine | `src/QueryEngine.ts` | 1295 lines |
| Tool definitions | `src/Tool.ts` | 792 lines, 30+ method interfaces |
| Tool registration | `src/tools.ts` | 400+ lines, feature gate conditional registration |
| Tool orchestration | `src/services/tools/toolOrchestration.ts` | Read-only concurrent / non-read-only serial |
| CLAUDE.md loading | `src/utils/claudemd.ts` | 400+ lines, circular reference detection |
| Hook event definitions | `src/entrypoints/sdk/coreTypes.ts:25-53` | 27 events |
| Hook execution | `src/utils/hooks.ts` | 5022 lines, circuit breaker |
| Hook schema | `src/entrypoints/sdk/coreSchemas.ts` | Zod validation |
| Auto-compact | `src/services/compact/autoCompact.ts` | 351 lines |
| Micro-compact | `src/services/compact/compact.ts` | 61K+ |
| Permissions | `src/utils/permissions/permissions.ts` | 5-layer decision |
| Sub-agent | `src/tools/AgentTool/runAgent.ts` | 3-tier isolation (Worktree/CCR/local background) |
| Parallel agents | `src/tools/shared/spawnMultiAgent.ts` | parallelism parameter |
| Memory system | `src/memdir/memdir.ts` | 508 lines, Auto/Team/KAIROS 3 modes |
| Memory types | `src/memdir/memoryTypes.ts` | user/feedback/project/reference |
| Prompt cache | `src/services/api/claude.ts` | Static/dynamic separation |
| Bridge API | `src/bridge/bridgeMain.ts` | IDE integration |

## Codex CLI (Rust)

| Module | Path | Notes |
|-------|------|-------|
| Main loop | `codex-rs/core/src/codex.rs` | 294KB |
| Tool registry | `codex-rs/core/src/tools/registry.rs` | |
| Tool handlers | `codex-rs/core/src/tools/handlers/` | |
| Policy engine | `codex-rs/execpolicy/src/` | Starlark DSL |
| Sandbox | `codex-rs/sandboxing/src/` | Seatbelt/Landlock |
| Protocol definitions | `codex-rs/protocol/src/protocol.rs` | Op enum |
| HTTP API | `codex-rs/app-server-protocol/src/protocol/v2.rs` | |
| Agent control | `codex-rs/core/src/agent/control.rs` | 42KB |
| Hook system | `codex-rs/hooks/src/` | |

## OpenCode (Go)

| Module | Path | Notes |
|-------|------|-------|
| Main loop | `internal/llm/agent/agent.go` | |
| Tool registry | `internal/llm/agent/tools.go` | |
| Tool interface | `internal/llm/tools/tools.go` | 2-method interface |
| Provider | `internal/llm/provider/` | |
| Configuration | `internal/config/config.go` | |
| TUI | `internal/tui/tui.go` | Bubble Tea |
| LSP | `internal/lsp/` | Deep integration |
| Session | `internal/session/session.go` | SQLite |
| Messages | `internal/message/message.go` | |
| PubSub | `internal/pubsub/` | Generic Broker |

## Aider (Python)

| Module | Path | Notes |
|-------|------|-------|
| Main loop | `aider/coders/base_coder.py` | Reflection loop |
| Edit formats | `aider/coders/editblock_coder.py` | 6 polymorphic types (diff/whole/udiff/architect/ask/patch) |
| Fuzzy matching | `aider/coders/editblock_coder.py:146-329` | 4-level priority (exact→whitespace→ellipsis→edit distance [disabled]) |
| Reflection chain | `aider/coders/base_coder.py:930-938` | Max 3x, 4 triggers |
| Repo Map | `aider/repomap.py` | tree-sitter AST |
| Git integration | `aider/repo.py` | |
| Model management | `aider/models.py` | |
| Command system | `aider/commands.py` | |

## Cline (TypeScript)

| Module | Path | Notes |
|-------|------|-------|
| Main loop | `src/core/task/index.ts` | Task class, Mutex state protection |
| Tool enumeration | `src/shared/tools.ts:8-36` | 27 ClineDefaultTool entries |
| Tool execution | `src/core/task/ToolExecutor.ts` | |
| Variant registry | `src/core/prompts/system-prompt/registry/PromptRegistry.ts` | Singleton, matcher traversal |
| Variant types | `src/core/prompts/system-prompt/types.ts:27-46` | PromptVariant interface |
| Component definitions | `src/core/prompts/system-prompt/components/` | 13 SystemPromptSection types |
| Tool variants | `src/core/prompts/system-prompt/tools/` | Per-tool multi-variants + fallback |
| Tool registration | `src/core/prompts/system-prompt/tools/init.ts` | registerClineToolSets() |
| Template engine | `src/core/prompts/system-prompt/templates/TemplateEngine.ts` | {{placeholder}} parsing |
| Native tool conversion | `src/core/prompts/system-prompt/tools/ClineToolSet.ts:151-192` | Converter selection by provider |
| Proto definitions | `proto/cline/` | task/ui/models/state/common |
| Loop detection | `src/core/task/loop-detection.ts` | Signature comparison, 3/5 dual threshold |
| Context management | `src/core/context/context-management/ContextManager.ts` | |

## OpenClaw (TypeScript, Cline Fork → Agent OS)

| Module | Path | Notes |
|-------|------|-------|
| Entry point | `src/entry.ts` | CLI layer, environment normalization |
| Plugin loading | `src/plugins/loader.ts` | 5 plugin types, Jiti dynamic import |
| Skill system | `src/agents/skills.ts` | Lazy loading + environment-aware filtering |
| System prompt | `src/agents/system-prompt.ts` | Deterministic ordering + cache boundary |
| Loop detection | `src/agents/tool-loop-detection.ts` | 4 detectors + global circuit breaker |
| Agent commands | `src/agents/agent-command.ts` | Session parsing + execution loop |
| Gateway protocol | `src/gateway/protocol/schema.ts` | TypeScript Zod schema |

## OpenHands (Python)

| Module | Path | Notes |
|-------|------|-------|
| CodeAct Agent | `openhands/agenthub/codeact_agent/codeact_agent.py:57` | VERSION 2.2, step() + pending_actions queue |
| Runtime base class | `openhands/runtime/base.py:106-244` | Abstract base, cmd retry (3x exponential backoff) |
| Docker Runtime | `openhands/runtime/impl/docker/docker_runtime.py` | Action Execution Server |
| Runtime factory | `openhands/runtime/impl/__init__.py` | get_runtime_cls() dynamic loading |
| Event base class | `openhands/events/event.py:25-122` | id/timestamp/source/cause causal chain |
| Event store | `openhands/storage/conversation/conversation_store.py` | JSON serialization, incremental save |
| Microagent types | `openhands/microagent/types.py:11` | KNOWLEDGE/REPO('repo')/TASK |
| Microagent loading | `openhands/microagent/microagent.py:51-171` | Frontmatter parsing, third-party compatible (.cursorrules) |
| Security analyzer | `openhands/runtime/base.py:213-223` | Pluggable SecurityAnalyzer |

## Letta (Python)

| Module | Path | Notes |
|-------|------|-------|
| Agent core | `letta/agent.py` | 2000+ lines |
| Memory schema | `letta/schemas/memory.py` | Block definitions |
| Core tools | `letta/functions/function_sets/base.py` | Self-modifying memory |
| LLM client | `letta/llm_api/` | |
| Service layer | `letta/services/` | |

## MemU (Rust + Python)

| Module | Path | Notes |
|-------|------|-------|
| Service entry | `src/memu/app/service.py` | |
| Memorize workflow | `src/memu/app/memorize.py` | |
| Retrieve workflow | `src/memu/app/retrieve.py` | |
| Pipeline | `src/memu/workflow/pipeline.py` | Versioned |
| Database abstraction | `src/memu/database/` | |

## Goose (Rust)

| Module | Path | Notes |
|-------|------|-------|
| Agent core | `crates/goose/src/agent.rs` | 2500+ lines, reply() → reply_internal() |
| ACP server | `crates/goose-acp/src/server.rs` | 99K lines |
| CLI entry | `crates/goose-cli/` | |
| Background service | `crates/goose-server/` | goosed binary |
| Built-in MCP extensions | `crates/goose-mcp/` | 4: autosvisualiser/computercontroller/memory/tutorial |
| Rust SDK | `crates/goose-sdk/` | ACP client SDK |
| Test utilities | `crates/goose-test/` | |

---

## Core Concept Glossary

| Term | Meaning |
|------|---------|
| **Agent Loop** | Core loop: LLM call → tool execution → result feedback |
| **Tool Use / Function Calling** | LLM's ability to output structured tool invocation requests |
| **Context Window** | Maximum token count a single API call can process |
| **System Prompt** | Fixed instruction prefix for each API call |
| **Prompt Cache** | API caching of repeated prefixes, reducing input costs by 90% |
| **Auto-Compact** | Automatic summarization and compression when context exceeds limits |
| **Progressive Disclosure** | Providing information in layers on demand, rather than all at once |
| **Repo Map** | AST-level structural summary of a codebase |
| **Hook** | Callback scripts triggered on Agent lifecycle events |
| **Harness** | System-level constraints and toolset for reliable Agent execution |
| **Hashimoto Loop** | Iterative methodology: observe failure → diagnose cause → system-level fix |
| **MCP** | Model Context Protocol, standardized connection protocol for tools/resources |
| **Sub-Agent** | Independent Agent instance executing subtasks in an isolated context |
| **Worktree** | Git worktree, used for Agent filesystem isolation |
| **Guardian AI** | Security mechanism using LLM to assess operation risk level |
| **Starlark** | Python-like configuration language used by Codex for execution policy definition |
| **Heartbeat** | Signal mechanism in Letta where Agent requests to continue execution |
| **Bitter Lesson** | Rich Sutton's principle: general-purpose computation methods ultimately outperform specialized knowledge |
| **Prompt Variant** | System prompt variant configuration tailored for different model families (pioneered by Cline) |
| **Component Override** | Mechanism where variants override shared component templates |
| **Circuit Breaker** | Protection mechanism that stops retrying after N consecutive failures |
| **Loop Detection** | Mechanism to detect Agent infinite loops (signature comparison / ping-pong / global circuit breaker) |
| **Event Sourcing** | Architectural pattern where all state changes are recorded as immutable event sequences (OpenHands) |
| **Condenser** | Historical event compressor with dual modes: View (preservation) / Condensation (request compression) |
| **Microagent** | OpenHands' modular knowledge unit, activated by triggers/types |
| **Plugin SDK** | OpenClaw's plugin development kit, 5 types (Provider/Channel/Tool/Skill/Memory) |
| **KAIROS** | Claude Code's append-style memory mode, log format, nightly /dream processing |
| **Agent OS** | OpenClaw's positioning: multi-channel gateway + extensible plugin system, transcending IDE extensions |
