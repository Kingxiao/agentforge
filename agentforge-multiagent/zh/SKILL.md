---
name: agentforge-multiagent
description: AgentForge Phase 7 - 多 Agent 协调。Sub-agent 4 种模式 + Agent 注册表 + 通信协议 + 反模式。当用户说「多 Agent」「sub-agent」「Agent 协调」「multi-agent」时触发。
triggers:
  - 多 Agent
  - sub-agent
  - Agent 协调
  - multi-agent
  - agent coordination
metadata:
  version: "2.0.0"
  last_updated: "2026-04-06"
  category: "agent-engineering"
---

# AgentForge Phase 7: 多 Agent 协调

> 上一步：`/agentforge-harness` | 下一步：`/agentforge-ship` | 系列入口：`/agentforge`
> 编排已有 Agent：`/dev-orchestrator`
> 深度理论：`/multiagent-topology`、`/stigmergy-coordination`、`/collective-intelligence-design`

## 开篇警告：最重要的反模式

> **"前端工程师 Agent" + "后端工程师 Agent" 不 work。**
> 
> 用 Sub-agent 做**上下文隔离**，不是**角色分工**。LLM 不因为你叫它"前端工程师"就写更好的前端代码。真正的价值在于：让子任务在干净的上下文中执行，不被主循环的历史信息污染。

## 第一个决策：需不需要多 Agent？

```
你的场景需要多 Agent 吗？
│
├─ 所有任务串行执行，无并行需求
│  → 不需要，单 Agent 足够
│
├─ 有独立子任务但不需要文件隔离
│  → 异步后台 Agent（最轻量）
│
├─ 子任务需要修改不同文件，可能冲突
│  → 隔离 Worktree Agent
│
└─ 需要大规模并行（10+ 任务同时）
   → 远程 Agent 或容器化
```

## 4 种 Sub-Agent 模式 [CC] — 3 层隔离体系

Claude Code 拥有生产环境中最精细的多 Agent 隔离架构，三层递进：

| 层级 | 隔离方式 | 机制 | 适用场景 |
|------|---------|------|---------|
| L1 | Worktree 隔离 | `git worktree` 创建独立工作树，文件级隔离 | 子任务会修改文件，需避免冲突 |
| L2 | CCR / Remote 隔离 | 云端计算环境，完整沙箱（独立文件系统+网络） | 大规模并行、不可信代码执行 |
| L3 | Background 异步 | 同工作区，异步通知机制 | 独立只读任务、不阻塞主流程 |

这是目前生产级 Agent 系统中最成熟的隔离分层——大多数竞品只有"同进程"或"容器"两档，缺乏中间态。

### 模式一：同步阻塞

```
主 Agent → spawn(prompt) → 等待完成 → 获取结果 → 继续
```

**适用**：研究、代码分析、搜索——结果直接影响下一步决策
**实现**：`Agent(description, prompt)` 返回结果后主循环继续
**约束**：阻塞主循环，用户需等待

### 模式二：异步后台

```
主 Agent → spawn(prompt, background=true) → 继续工作
                                           ↓ （完成时通知）
                                        获取结果
```

**适用**：独立编码任务、测试运行、文档生成——不阻塞主流程
**实现**：`Agent(description, prompt, run_in_background: true)` 返回 agentId
**约束**：结果异步返回，需要通知机制

### 模式三：隔离 Worktree

```
主 Agent → spawn(prompt, isolation="worktree")
              ↓
        创建 Git worktree → 独立分支 → 执行任务
              ↓
        完成 → 如有修改返回分支名 → 主 Agent 合并
        无修改 → 自动清理 worktree
```

**适用**：子任务会修改文件，需要与主工作区隔离
**实现**：临时 git worktree + 独立分支
**约束**：需要 Git 仓库，合并可能有冲突

### 模式四：远程

```
主 Agent → spawn(prompt, isolation="remote")
              ↓
        远程环境执行 → 返回 session ID
              ↓
        轮询状态 → 获取结果
```

**适用**：大规模并行、需要不同硬件环境
**约束**：网络延迟、成本高

## Sub-Agent 的工具限制

子 Agent 不应该拥有和父 Agent 完全相同的工具集。限制原则 [CC]：

| 禁用工具 | 理由 |
|----------|------|
| EnterPlanMode / ExitPlanMode | 防止嵌套计划模式 |
| Agent（再 spawn） | 防止递归 Agent（无限嵌套，非 ant 用户） |
| AskUserQuestion | 子 Agent 不应直接向用户提问 |
| TaskOutput / TaskStop | 子 Agent 不应操作父级任务 |

**设计原则**：子 Agent 的能力应该是父 Agent 的**子集**。

## Agent 间通信

### Git 作为共享状态 [CC, CX]

最简单且最可靠的 Agent 间通信方式：

```
Agent A 完成工作 → git commit → git push
Agent B 开始工作 → git pull → 读取 Agent A 的修改
```

**commit message 是通信协议**。描述性的 commit message 让其他 Agent 理解发生了什么。

### 消息传递 [CX]

Codex CLI 的 `Op::InterAgentCommunication`：
- 父 Agent 向子 Agent 发消息
- 子 Agent 向父 Agent 返回结果
- 通过 channel 实现，非共享内存

### PubSub 事件 [OC]

OpenCode 的模式：Session 继承 + PubSub 通知
- 子 Agent 创建子 Session（`ParentSessionID` 指向父）
- 完成后通过 PubSub 发布事件
- 成本自动汇总到父 Session

## Agent 注册与生命周期

### Codex 的 ThreadManager [CX]

```rust
struct AgentRegistry {
    agents: HashMap<ThreadId, AgentHandle>,
    parent: Weak<ThreadManager>,  // 弱引用防循环
}

// 生命周期
spawn_agent(config, initial_op) → ThreadId
    ↓ 执行中
monitor(thread_id) → AgentStatus
    ↓ 完成
cleanup(thread_id) → 释放资源
```

### Claude Code 的 Agent 生命周期 [CC]

```
registerAsyncAgent(agentId, {description, prompt, model})
    ↓
updateAgentProgress(agentId, progress)  // 流式更新
    ↓
completeAgentTask(agentId, result)      // 完成
    ↓
enqueueAgentNotification()              // 通知主循环
    ↓
removeAgent(agentId)                    // 清理
```

## 分工策略

### 按范围分（推荐）

```
Agent A → 处理 src/api/ 下的所有文件
Agent B → 处理 src/ui/ 下的所有文件
Agent C → 运行测试 + 报告结果
```

**原则**：不同 Agent 操作不同的文件范围。如果两个 Agent 需要编辑同一个文件，合并为一个 Agent。

### 按阶段分

```
Agent A → 研究 + 分析（只读工具）
    ↓ 输出分析报告
Agent B → 实现（读写工具）
    ↓ 输出代码
Agent C → 审查（只读 + diff 工具）
```

### 禁止：按角色分

```
❌ "前端工程师" Agent
❌ "后端工程师" Agent  
❌ "测试工程师" Agent
❌ "DevOps 工程师" Agent
```

这些角色划分对 LLM 没有意义。只是增加了不必要的通信开销。

## CI 作为通用验证器

多 Agent 场景中，CI 是唯一能同等验证所有 Agent 输出的机制：

```
Agent A 提交 → CI 运行 → 通过/失败
Agent B 提交 → CI 运行 → 通过/失败
人类提交    → CI 运行 → 通过/失败
```

**CI 不 care 谁写的代码。** 这是多 Agent 系统中最公正的质量门禁。

## OpenClaw Plugin SDK [OW]

OpenClaw 的插件系统本质上是一种 Skill-as-Agent 模式——不是 spawn 独立子进程，而是加载领域技能来修改 Agent 行为。

### 5 种插件类型

| 类型 | 职责 | 示例 |
|------|------|------|
| Provider | LLM 供应商适配 | OpenAI / Anthropic / Local |
| Channel | 输入/输出通道 | Slack / Web / CLI |
| Tool | 外部能力绑定 | 文件系统 / API 调用 / 数据库 |
| Skill | 领域行为注入 | 代码审查 / 翻译 / 数据分析 |
| Memory | 记忆策略 | 向量存储 / 文件记忆 / Redis |

### 热加载机制

- 使用 **Jiti** 动态 import，运行时加载/卸载插件，无需重启
- 每个 Skill 本质上是一个 sub-agent：拥有独立的 system prompt 和 tool access
- Marketplace 提供 100+ 可用 Skills

### 核心洞察：Skill-as-Agent 模式

传统多 Agent 思路是 spawn 独立 sub-agent 来处理子任务。OpenClaw 的替代方案：**加载一个 domain skill 来改变当前 Agent 的行为**。

对比：

```
传统：  主 Agent → spawn(子 Agent) → 子 Agent 独立执行 → 返回结果
OC：    主 Agent → load(Skill) → 主 Agent 获得新能力 → 直接执行
```

**优势**：零通信开销、共享上下文、无需合并结果
**劣势**：无隔离、Skill 冲突风险、单点故障

适用于：子任务不需要文件隔离、不需要并行、更需要深度上下文共享的场景。

## Platform / OS Agent 架构模式

> **"用多 Agent 完成任务"** vs **"构建管理 Agent 的平台"** — 这是两个根本不同的问题。
>
> OpenClaw 是典型的后者——不是协调 Agent 完成一个任务，而是**维持一个 Agent 生态系统的健康和演进**。

### 什么时候你在构建 Platform

- 你的系统需要运行/管理其他 Agent（不是调用，是管理生命周期）
- 你需要为 Agent 定义"能力边界"并动态扩展（Skill 系统、Plugin 系统）
- 你需要监控整个 Agent 生态的健康、演进方向
- 你的 Agent 能修改自身或其他 Agent 的行为规则

### Platform 架构的核心三层

```
Layer 1: Gateway / Channel（入口聚合）
  ↓ 统一消息格式（CLI / Slack / Telegram / Web / API）
Layer 2: Agent 运行时（生命周期管理）
  ↓ 注册、启动、监控、熔断、销毁
  ├── Capability Store（Skill/Plugin 仓库）
  └── Evolution State（进化历史 + 断路器）
Layer 3: 基础设施（持久化 + 可观测性）
  ↓ 事件流 / 状态存储 / 审计日志
```

### Platform 与 Coordinator 的设计差异

| 维度 | Coordinator（任务型） | Platform（生态型） |
|------|---------------------|-----------------|
| 关注点 | 完成当前任务 | 维持系统健康 |
| Agent 关系 | 父子（任务委派） | 宿主-插件（能力加载） |
| 失败处理 | 重试/降级 | 断路器 + 隔离 |
| 演进单元 | 任务 Prompt | Agent 行为规则/能力库 |
| 状态粒度 | 任务状态 | Agent 生态系统状态 |
| 代表实现 | Claude Code Agent SDK [CC] | OpenClaw [TS]（多通道 Platform） |

### Platform 的关键设计决策

1. **能力加载机制** — 静态注册（编译期确定）还是动态加载（运行时 JS module / .so）？动态加载获得热更新能力，代价是安全审计复杂度倍增。参考：OpenClaw 用 Jiti 动态 import 热加载
2. **Agent 行为规范** — 用 Prompt 约定还是编译期不变量？Prompt 灵活但可变，编译期不变量强制但稳定。生产级 Platform 往往两者结合：不变量守底线，Prompt 做个性化
3. **演进安全边界** — Platform 必须有 Circuit Breaker（连续失败 N 次 → 停止自动演进）和 Blast Radius 限制（自动修改的范围 ≤ X%）
4. **可观测性是一等公民** — Platform 的调试不是看单次任务，而是看 Agent 生态的演进轨迹。必须从第一天设计 Evolution Log（每次 Agent 行为变更的原因 + 结果）

> 自进化 Platform 的原理和安全边界 → `/agentforge-evolution`（Phase 10）
> 深度 Zig 实现 → `/selfevolving-agent-architecture`

## OpenHands Microagent 3 类型 [OH]

OpenHands 将"指令注入"细分为三种 Microagent，按触发方式和作用域分层：

| 类型 | 枚举值 | 加载时机 | 作用域 |
|------|--------|---------|--------|
| KNOWLEDGE | `value='knowledge'` | 始终加载 | 全局领域知识（如语言规范、API 文档摘要） |
| REPO | `value='repo'` | 仓库级自动加载 | 仓库特定指令（`.openhands/` 或 `.cursorrules` 文件） |
| TASK | 动态触发 | 用户消息中关键词匹配时 | 按需注入的任务特定指令 |

**设计启示**：

- KNOWLEDGE 类似 system prompt 的领域知识层——始终在 context 中，成本恒定
- REPO 对应 CLAUDE.md / AGENTS.md 的仓库级 harness——自动检测、无需显式加载
- TASK 是最有趣的一层：**基于关键词匹配动态注入指令**，实现了"按需激活能力"而无需 spawn 新 Agent
- 三层分离让 context budget 可控：KNOWLEDGE 占固定预算，REPO 按仓库变化，TASK 按需加载

## 流式处理 Pipeline 多 Agent 模式

> **适用场景**：实时数据处理流水线（转录→分析→推送），每个 Agent 的输出是下一个 Agent 的输入，且每步的延迟约束不同。

标准 4 种模式（同步/异步/worktree/remote）都假设"子任务有明确的开始和结束"。流式 Pipeline 中每个 Agent 持续运行，通过共享队列传递增量数据——这是第 5 种模式。

### 三阶段流式 Pipeline 示意

```
TranscriptionAgent            AnalysisAgent              NotificationAgent
──────────────────            ─────────────              ─────────────────
音频流 → 实时转录          每 30 秒接收新段落         触发条件满足时推送
    ↓                              ↓                              ↓
写入 transcript_queue →→→   读取 transcript_queue      读取 notification_queue
                            → LLM 分析                   → 写入通知队列
                            → 写入 notification_queue →→→ → POST to Slack/Notion
```

**关键设计**：队列是三个 Agent 之间的唯一通信媒介，没有直接调用——解耦了每个阶段的处理速度。

### 实现要点

```python
# 共享队列（进程内用 asyncio.Queue，进程间用 Redis Stream）
transcript_queue = asyncio.Queue(maxsize=10)
notification_queue = asyncio.Queue(maxsize=50)

async def run_pipeline():
    # 三个 Agent 并发运行，互不阻塞
    await asyncio.gather(
        TranscriptionAgent(output=transcript_queue).run(),
        AnalysisAgent(input=transcript_queue, output=notification_queue).run(),
        NotificationAgent(input=notification_queue).run(),
    )
```

### 与标准多 Agent 模式的对比

| 维度 | 标准（同步/异步 spawn） | 流式 Pipeline |
|------|---------------------|-------------|
| Agent 生命周期 | 按需启动，任务完成后退出 | 持续运行，无自然结束点 |
| Agent 间通信 | spawn 返回值 / Git commit | 共享队列（异步、非阻塞）|
| 背压控制 | 不需要 | 必须（`maxsize` 限制，防止快速生产者淹没慢速消费者）|
| 失败处理 | 父 Agent 重试子 Agent | 单个 Agent 崩溃不影响队列已有内容 |
| 成本 | 按任务计 | 持续消耗（LLM 按批次调用）|

**背压（Backpressure）是关键**：`maxsize` 控制队列容量，防止 TranscriptionAgent 以 10 条/秒的速度写入，而 AnalysisAgent 只能 1 条/30s 处理，导致内存爆炸。生产环境用 Redis Stream 替代 `asyncio.Queue`，具备持久化和消费组功能。

## 当前状态 (2026年4月)

1. **Worktree 隔离成为主流** — Claude Code 的 git worktree 模式被验证为多 Agent 文件冲突的最优解，Codex CLI 和 OpenCode 均已跟进实现类似机制，"同工作区多 Agent"模式正在被淘汰
2. **Agent-to-Agent 协议收敛** — Google A2A 协议和 Anthropic 的 Agent SDK 推动了 Agent 间通信标准化，但生产环境中 Git commit 作为共享状态仍然是最可靠的跨 Agent 通信方式
3. **Sub-agent 递归产卵被限制** — 多个平台已禁止 sub-agent 再 spawn sub-agent（防止递归爆炸），Claude Code 对非 Ant 用户强制单层嵌套，这成为行业共识
4. **按范围分工压倒按角色分工** — 实证数据持续确认"按文件范围分 Agent"比"按角色分 Agent"的成功率高 2-3 倍，角色分工模式的通信开销远超收益
5. **Skill-as-Agent 模式兴起** — OpenClaw 的插件式能力注入（加载 Skill 改变 Agent 行为而非 spawn 新 Agent）在无需文件隔离的场景下展现出零通信开销优势

## Known Pitfalls

1. **Worktree 合并冲突累积** — 多个 worktree Agent 并行修改后合并，冲突数量随 Agent 数量超线性增长。解决方案：严格按文件范围划分 Agent 职责，确保无交叉；合并前用 `git diff --stat` 预检冲突
2. **Sub-agent 上下文继承过多** — 父 Agent 将完整上下文传递给子 Agent，导致子 Agent 上下文被无关信息污染，决策质量下降。解决方案：只传递子任务所需的最小上下文（prompt + 相关文件路径），不传历史对话
3. **异步 Agent 结果丢失** — 后台 Agent 完成后主 Agent 已进入不同的执行分支，异步结果无人消费。解决方案：异步 Agent 将结果写入持久化存储（文件或 Git commit），而非依赖内存通知机制
4. **多 Agent 成本失控** — 每个 sub-agent 都消耗独立的 LLM token，10 个并行 Agent 的成本是单 Agent 的 10 倍以上（因 system prompt 重复）。解决方案：严格评估并行必要性，优先用 Skill-as-Agent 模式替代不需要文件隔离的场景
5. **Agent 间死锁** — Agent A 等待 Agent B 的输出，Agent B 等待 Agent A 的输出。解决方案：禁止循环依赖，所有 Agent 间通信必须是有向无环图（DAG）

## 延伸阅读

| 主题 | 资源 |
|------|------|
| Sub-agent spawn 模式详细实现 | [`references/spawn-modes-detail.md`](references/spawn-modes-detail.md) |
| Agent 注册表与生命周期模式 | [`references/agent-registry-patterns.md`](references/agent-registry-patterns.md) |
| Sub-agent 权限与工具限制 | `/agentforge-security` |
| Worktree 与 Git 隔离配置 | `/agentforge-harness` |
| 多 Agent 拓扑设计原理 | `/multiagent-topology` |
| 集体智能与信息素协调 | `/stigmergy-coordination`、`/collective-intelligence-design` |
| 自进化 Agent 集群 | `/selfevolving-agent-architecture` |

## 多 Agent 检查清单

- [ ] 确认需要多 Agent（单 Agent 不够用的明确理由）
- [ ] 明确模式：协调型（完成任务）还是 Platform 型（管理生态）
- [ ] 选定了 spawn 模式（同步/异步/worktree/远程）
- [ ] 子 Agent 工具集是父 Agent 的子集
- [ ] 不同 Agent 操作不同的文件范围（无冲突）
- [ ] 有 Agent 间通信机制（Git commit 或消息传递）
- [ ] CI 作为通用验证器
- [ ] 没有使用角色分工模式
- [ ] Platform 型：设计了 Circuit Breaker + Evolution Log + Capability Store

## 逆向审计（Diagnose Mode）

> 由 `/agentforge-diagnose` 调用——对已有代码进行 D7 多 Agent 维度静态审计。

| # | 检查项 | 检查方式 | 通过标准 |
|---|--------|---------|---------|
| MA1 | Spawn 模式可识别 | 搜索 spawn/create_agent/subagent 等调用 | 能判断是 Parallel/Sequential/Hierarchical/Mesh 哪种 |
| MA2 | 无循环依赖风险 | 绘制调用图（A→B→？）检查是否有环 | 调用链无环，或有 `max_depth` 限制 |
| MA3 | 子 Agent context 隔离 | 看子 Agent 如何创建：是否传入主 context | 子 Agent 用 fresh context，不继承主 Agent 全量历史 |
| MA4 | 子 Agent 结果有验证 | 看主 Agent 如何使用子 Agent 返回值 | 有完整性检查（非盲信），关键结论有来源验证 |
| MA5 | 局部失败有降级 | `grep -rn "try\|except\|catch\|fallback" src/ \| grep -i agent` | 单个子 Agent 失败不会崩掉整个 workflow |

**高概率问题**：无循环深度限制（P0 死循环风险）、子 Agent 共享主 context（P1 上下文污染）、盲信子 Agent 输出无验证（P1 错误传播）

## 下一步

多 Agent 设计完成后 → **`/agentforge-ship`**（Phase 8：发布部署）
构建 Platform 型 → **`/agentforge-evolution`**（Phase 10：自进化）
需要深度 Zig 实现 → **`/selfevolving-agent-architecture`**
