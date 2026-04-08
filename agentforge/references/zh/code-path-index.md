# 关键代码路径索引 + 术语表

> 来源：v1 研究 + Wave 2 深度逆向（2026-04-06）
> 去源码学习的导航图。每个模块标注了文件路径和大致规模。

## Claude Code (TypeScript)

| 模块 | 路径 | 备注 |
|------|------|------|
| 主循环 | `src/query.ts` | 1729 行，无限 while 循环，6 个 continue 站点 |
| 查询引擎 | `src/QueryEngine.ts` | 1295 行 |
| 工具定义 | `src/Tool.ts` | 792 行，30+ 方法接口 |
| 工具注册 | `src/tools.ts` | 400+ 行，feature gate 条件注册 |
| 工具调度 | `src/services/tools/toolOrchestration.ts` | 只读并发/非只读串行 |
| CLAUDE.md 加载 | `src/utils/claudemd.ts` | 400+ 行，循环引用检测 |
| Hook 事件定义 | `src/entrypoints/sdk/coreTypes.ts:25-53` | 27 个事件 |
| Hook 执行 | `src/utils/hooks.ts` | 5022 行，电路断路器 |
| Hook Schema | `src/entrypoints/sdk/coreSchemas.ts` | Zod 验证 |
| Auto-compact | `src/services/compact/autoCompact.ts` | 351 行 |
| 微压缩 | `src/services/compact/compact.ts` | 61K+ |
| 权限 | `src/utils/permissions/permissions.ts` | 5 层决策 |
| Sub-agent | `src/tools/AgentTool/runAgent.ts` | Worktree/CCR/本地后台 3 层隔离 |
| 并行 Agent | `src/tools/shared/spawnMultiAgent.ts` | parallelism 参数 |
| 记忆系统 | `src/memdir/memdir.ts` | 508 行，Auto/Team/KAIROS 3 模式 |
| 记忆类型 | `src/memdir/memoryTypes.ts` | user/feedback/project/reference |
| Prompt cache | `src/services/api/claude.ts` | 静态/动态分离 |
| Bridge API | `src/bridge/bridgeMain.ts` | IDE 集成 |

## Codex CLI (Rust)

| 模块 | 路径 | 备注 |
|------|------|------|
| 主循环 | `codex-rs/core/src/codex.rs` | 294KB |
| 工具注册 | `codex-rs/core/src/tools/registry.rs` | |
| 工具 Handler | `codex-rs/core/src/tools/handlers/` | |
| 策略引擎 | `codex-rs/execpolicy/src/` | Starlark DSL |
| 沙箱 | `codex-rs/sandboxing/src/` | Seatbelt/Landlock |
| 协议定义 | `codex-rs/protocol/src/protocol.rs` | Op 枚举 |
| HTTP API | `codex-rs/app-server-protocol/src/protocol/v2.rs` | |
| Agent 控制 | `codex-rs/core/src/agent/control.rs` | 42KB |
| Hook 系统 | `codex-rs/hooks/src/` | |

## OpenCode (Go)

| 模块 | 路径 | 备注 |
|------|------|------|
| 主循环 | `internal/llm/agent/agent.go` | |
| 工具注册 | `internal/llm/agent/tools.go` | |
| 工具接口 | `internal/llm/tools/tools.go` | 2 方法接口 |
| Provider | `internal/llm/provider/` | |
| 配置 | `internal/config/config.go` | |
| TUI | `internal/tui/tui.go` | Bubble Tea |
| LSP | `internal/lsp/` | 深度集成 |
| 会话 | `internal/session/session.go` | SQLite |
| 消息 | `internal/message/message.go` | |
| PubSub | `internal/pubsub/` | 泛型 Broker |

## Aider (Python)

| 模块 | 路径 | 备注 |
|------|------|------|
| 主循环 | `aider/coders/base_coder.py` | 反射循环 |
| 编辑格式 | `aider/coders/editblock_coder.py` | 6 种多态(diff/whole/udiff/architect/ask/patch) |
| Fuzzy Matching | `aider/coders/editblock_coder.py:146-329` | 4 级优先级(精确→空格→省略号→编辑距离[禁用]) |
| 反射链 | `aider/coders/base_coder.py:930-938` | max 3 次，4 触发源 |
| Repo Map | `aider/repomap.py` | tree-sitter AST |
| Git 集成 | `aider/repo.py` | |
| 模型管理 | `aider/models.py` | |
| 命令系统 | `aider/commands.py` | |

## Cline (TypeScript)

| 模块 | 路径 | 备注 |
|------|------|------|
| 主循环 | `src/core/task/index.ts` | Task 类，Mutex 状态保护 |
| 工具枚举 | `src/shared/tools.ts:8-36` | 27 个 ClineDefaultTool |
| 工具执行 | `src/core/task/ToolExecutor.ts` | |
| Variant 注册表 | `src/core/prompts/system-prompt/registry/PromptRegistry.ts` | 单例，matcher 遍历 |
| Variant 类型 | `src/core/prompts/system-prompt/types.ts:27-46` | PromptVariant 接口 |
| 组件定义 | `src/core/prompts/system-prompt/components/` | 13 种 SystemPromptSection |
| 工具变体 | `src/core/prompts/system-prompt/tools/` | 每工具多变体 + Fallback |
| 工具注册 | `src/core/prompts/system-prompt/tools/init.ts` | registerClineToolSets() |
| 模板引擎 | `src/core/prompts/system-prompt/templates/TemplateEngine.ts` | {{占位符}} 解析 |
| Native 工具转换 | `src/core/prompts/system-prompt/tools/ClineToolSet.ts:151-192` | 按 provider 选转换器 |
| Proto 定义 | `proto/cline/` | task/ui/models/state/common |
| 循环检测 | `src/core/task/loop-detection.ts` | 签名比较，3/5 双阈值 |
| 上下文管理 | `src/core/context/context-management/ContextManager.ts` | |

## OpenClaw (TypeScript, Cline Fork → Agent OS)

| 模块 | 路径 | 备注 |
|------|------|------|
| 入口 | `src/entry.ts` | CLI 层，环境标准化 |
| 插件加载 | `src/plugins/loader.ts` | 5 种插件类型，Jiti 动态导入 |
| 技能系统 | `src/agents/skills.ts` | Lazy loading + 环境感知过滤 |
| 系统提示 | `src/agents/system-prompt.ts` | 确定性排序 + 缓存边界 |
| 循环检测 | `src/agents/tool-loop-detection.ts` | 4 种检测器 + 全局断路器 |
| Agent 命令 | `src/agents/agent-command.ts` | 会话解析 + 执行循环 |
| 网关协议 | `src/gateway/protocol/schema.ts` | TypeScript Zod schema |

## OpenHands (Python)

| 模块 | 路径 | 备注 |
|------|------|------|
| CodeAct Agent | `openhands/agenthub/codeact_agent/codeact_agent.py:57` | VERSION 2.2，step() + pending_actions 队列 |
| Runtime 基类 | `openhands/runtime/base.py:106-244` | 抽象基类，cmd 重试(3次指数退避) |
| Docker Runtime | `openhands/runtime/impl/docker/docker_runtime.py` | Action Execution Server |
| Runtime 工厂 | `openhands/runtime/impl/__init__.py` | get_runtime_cls() 动态加载 |
| 事件基类 | `openhands/events/event.py:25-122` | id/timestamp/source/cause 因果链 |
| 事件存储 | `openhands/storage/conversation/conversation_store.py` | JSON 序列化，增量保存 |
| Microagent 类型 | `openhands/microagent/types.py:11` | KNOWLEDGE/REPO('repo')/TASK |
| Microagent 加载 | `openhands/microagent/microagent.py:51-171` | frontmatter 解析，第三方兼容(.cursorrules) |
| 安全分析器 | `openhands/runtime/base.py:213-223` | 可插拔 SecurityAnalyzer |

## Letta (Python)

| 模块 | 路径 | 备注 |
|------|------|------|
| Agent 核心 | `letta/agent.py` | 2000+ 行 |
| 记忆 Schema | `letta/schemas/memory.py` | Block 定义 |
| 核心工具 | `letta/functions/function_sets/base.py` | 自修改记忆 |
| LLM 客户端 | `letta/llm_api/` | |
| 服务层 | `letta/services/` | |

## MemU (Rust + Python)

| 模块 | 路径 | 备注 |
|------|------|------|
| 服务入口 | `src/memu/app/service.py` | |
| 记忆工作流 | `src/memu/app/memorize.py` | |
| 检索工作流 | `src/memu/app/retrieve.py` | |
| Pipeline | `src/memu/workflow/pipeline.py` | 版本化 |
| 数据库抽象 | `src/memu/database/` | |

## Goose (Rust)

| 模块 | 路径 | 备注 |
|------|------|------|
| Agent 核心 | `crates/goose/src/agent.rs` | 2500+ 行，reply() → reply_internal() |
| ACP 服务器 | `crates/goose-acp/src/server.rs` | 99K 行 |
| CLI 入口 | `crates/goose-cli/` | |
| 后台服务 | `crates/goose-server/` | goosed 二进制 |
| 内置 MCP 扩展 | `crates/goose-mcp/` | 4 个：autovisualiser/computercontroller/memory/tutorial |
| Rust SDK | `crates/goose-sdk/` | ACP 客户端 SDK |
| 测试工具 | `crates/goose-test/` | |

---

## 核心概念术语表

| 术语 | 含义 |
|------|------|
| **Agent Loop** | LLM 调用 → 工具执行 → 结果反馈的核心循环 |
| **Tool Use / Function Calling** | LLM 输出结构化工具调用请求的能力 |
| **Context Window** | 单次 API 调用能处理的最大 token 数 |
| **System Prompt** | 每次 API 调用的固定指令前缀 |
| **Prompt Cache** | API 对重复前缀的缓存，降低 90% 输入成本 |
| **Auto-Compact** | 上下文超限时自动摘要压缩 |
| **Progressive Disclosure** | 按需分层提供信息，而非一次全给 |
| **Repo Map** | 代码库的 AST 级结构摘要 |
| **Hook** | 在 Agent 生命周期事件上触发的回调脚本 |
| **Harness** | 让 Agent 可靠运行的系统级约束和工具集 |
| **Hashimoto Loop** | 观察失败 → 诊断原因 → 系统级修复的迭代方法论 |
| **MCP** | Model Context Protocol，工具/资源的标准化连接协议 |
| **Sub-Agent** | 在隔离上下文中执行子任务的独立 Agent 实例 |
| **Worktree** | Git worktree，用于 Agent 的文件系统隔离 |
| **Guardian AI** | 用 LLM 评估操作风险等级的安全机制 |
| **Starlark** | Python-like 配置语言，Codex 用于定义执行策略 |
| **Heartbeat** | Letta 中 Agent 请求继续执行的信号机制 |
| **Bitter Lesson** | Rich Sutton 的原则：通用计算方法最终胜过专用知识 |
| **Prompt Variant** | 针对不同模型家族的系统提示变体配置（Cline 首创） |
| **Component Override** | 变体覆盖共享组件模板的机制 |
| **Circuit Breaker** | 电路断路器：连续失败 N 次后停止重试的保护机制 |
| **Loop Detection** | 检测 Agent 死循环的机制（签名比较/ping-pong/全局断路器） |
| **Event Sourcing** | 所有状态变更记录为不可变事件序列的架构模式（OpenHands） |
| **Condenser** | 历史事件压缩器，View(保留)/Condensation(请求压缩)双模式 |
| **Microagent** | OpenHands 的模块化知识单元，按触发器/类型激活 |
| **Plugin SDK** | OpenClaw 的插件开发套件，5 种类型（Provider/Channel/Tool/Skill/Memory） |
| **KAIROS** | Claude Code 的追加式记忆模式，日志格式，夜间 /dream 处理 |
| **Agent OS** | OpenClaw 的定位：多通道网关 + 可扩展插件系统，超越 IDE 扩展 |
