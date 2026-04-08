---
name: agentforge-autoplan
description: AgentForge Phase 9 — full-pipeline orchestrator. Serial execution of Phase 0→8, auto-handling mechanical decisions, deferring only judgment calls to humans. Triggers when user says "build an Agent", "agentforge autoplan", "one-shot build", or "full pipeline". When the user provides repo code or an existing Agent, automatically switches to diagnosis mode and invokes agentforge-diagnose.
triggers:
  - build an agent
  - agentforge autoplan
  - one-shot build
  - agent full pipeline
  - agent autoplan
  - diagnose agent
  - audit agent code
  - review this agent
metadata:
  version: "2.1.0"
  last_updated: "2026-04-08"
  category: "agent-engineering"
---

# AgentForge Phase 9: 全流程编排

> 系列入口：`/agentforge` | 覆盖 Phase 0→8 全部阶段
> 参考：`/gstack-autoplan`（Web 产品的等价编排器）

## 模式检测（编排器入口）

**编排器启动的第一步是判断处于哪种模式**，然后路由到对应流程。

```
用户输入
    ↓
检测关键词/上下文
    ↓
┌─────────────────────────────────────────────────────┐
│ 包含以下任一信号 → 诊断模式（→ /agentforge-diagnose）│
│  • 提供了 repo 路径 / 代码文件                       │
│  • "已有 Agent" / "现有代码" / "帮我看看"           │
│  • "诊断" / "审计" / "哪里有问题" / "为什么不行"    │
│  • "优化" + 缺少"新建"/"构建"意图                  │
├─────────────────────────────────────────────────────┤
│ 包含以下信号 → 构建模式（继续本 skill 的流水线）     │
│  • "构建" / "做一个" / "新建" / "从零"              │
│  • 提供了 Agent 创意描述（但无现有代码）             │
│  • "autoplan" 无附加代码上下文                      │
└─────────────────────────────────────────────────────┘
    ↓
不确定时：直接问"你是要新建 Agent，还是诊断已有的？"
```

**诊断模式激活后**：
1. 切换到 `/agentforge-diagnose`，按其协议执行
2. 诊断完成后，如用户要修复，回到本 skill 对应 Phase 执行修复
3. 本 skill 的"构建流水线"不在诊断模式下运行

---

## 核心认知

构建 Agent 是一个 9 阶段流水线。每个阶段都有明确的输入输出。编排器的工作是：**自动处理机械决策，只把真正需要判断的问题留给人。**

不是每个 Agent 都需要走完全部 9 个阶段。编排器会根据场景自动跳过不适用的阶段。

## 编排流水线

```
Phase 0 (spec)        → Agent 定位与可行性
    ↓ 输出：Agent Spec 文档
Phase 1 (architecture) → 架构选型
    ↓ 输出：5 种 Loop 范式选型 + 语言 + Provider 方案
Phase 2 (tools)        → 工具系统设计
    ↓ 输出：工具接口 + 并发策略 + MCP 集成方案
Phase 3 (context)      → 上下文工程
    ↓ 输出：Prompt 分层 + Cache 策略 + Compact 方案
Phase 4 (memory)       → 记忆系统选型
    ↓ 输出：记忆范式 + 进度文件 + 会话持久化方案
Phase 5 (security)     → 安全/沙箱/权限
    ↓ 输出：安全层级 + 审批流 + 沙箱方案
Phase 6 (harness)      → Harness 工程
    ↓ 输出：CLAUDE.md + Hook 配置 + 验证循环
Phase 7 (multiagent)   → 多 Agent 协调（可选）
    ↓ 输出：Spawn 模式 + 通信协议
Phase 8 (ship)         → 打包与发布
    ↓ 输出：打包配置 + CI/CD + 版本管理
```

## 决策分工原则

### 用户只决策 5 件事

编排器启动时，先从用户已提供的信息中提取这 5 项。缺哪个就问哪个，问完不再追问其他：

| # | 用户决策 | 问法 |
|---|---------|------|
| 1 | **Agent 创意**：做什么 | "用 1-3 句话描述你的 Agent 要完成什么任务？" |
| 2 | **定位**：给谁用、在哪用 | "谁会用它？大概多高频？在什么环境下运行？" |
| 3 | **初始效果预期** | "第一版你期望的效果档位：能用就行 / 稳定可用 / 生产级？" |
| 4 | **预算档位** | "月度 API 成本接受范围（见下方档位表）？是否需要仅限国内可用模型？" |
| 5 | **验收标准** | "什么情况下你会觉得这个 Agent 做成了？用自然语言描述就行。" |

### 技术选型全部自动决策

以下内容**编排器自主决定，不询问用户**：

| 技术决策 | 自动决策依据 |
|---------|------------|
| 编程语言 | 根据部署场景、性能需求、交付速度自动选 |
| 架构范式（7 种 Loop） | 根据交互模式和触发方式自动选 |
| LLM 模型 | 根据预算档位 + 是否中国约束自动匹配 |
| 框架/库选型 | 根据语言 + 场景自动选，优先最简 |
| 记忆系统 | 根据用户数量和记忆重要性自动选 |
| 安全层级 | 根据使用场景（个人/团队/对外）自动设定 |
| 工具接口复杂度 | 根据原型/生产阶段自动决定 |
| 并发策略 | 根据工具类型自动推断 |
| Multi-Agent | 根据任务可并行性自动判断 |
| 打包方式 | 根据分发对象自动选 |

**中国约束例外**：用户提及"国内""中国大陆""不能用 OpenAI/Claude"时，自动切换为国内可用方案（DeepSeek / 阿里千问 / 百度千帆），无需询问具体模型名称。

### 必须问用户时：用体感差异，不用技术参数

当技术选型确实需要用户判断（极少情况），**不呈现技术选项，呈现体感差异**：

```
❌ 错误问法："用 claude-sonnet-4-6 还是 claude-haiku-4-5？"
❌ 错误问法："要不要用 Block Memory 还是 File Memory？"

✅ 正确问法：
"这个任务有两个方向，效果差距比较明显，需要你选一下：
  方向 A（月费约 ¥80）：能完成 85% 的任务，遇到复杂情况偶尔出错，需要你偶尔检查下
  方向 B（月费约 ¥350）：复杂任务也能稳定处理，几乎不需要盯着
  你更倾向哪个？"
```

### 6 条自动决策原则

### 1. 完整性优先
覆盖全部边缘情况，不留"以后再补"的缺口。

**应用**：工具接口设计时，宁可多定义 `isReadOnly()`、`isExpensive()` 等方法，不要"先简单实现再说"。

### 2. 务实选择
等效方案选更简洁的。技术上能实现 ≠ 应该这样做。

**应用**：记忆系统选型时，如果文件记忆能满足需求，不选块记忆。

### 3. DRY（拒绝重复）
同一信息只在一处定义。配置、常量、类型定义都适用。

**应用**：Provider endpoint 只在配置文件中定义一次，代码中引用配置。

### 4. 显式优于隐式
每个决策都有可追溯的理由。"默认"不是理由。

**应用**：选择 Async Generator 范式时（7 种可选），记录"因为需要流式输出 + TypeScript 生态"。

### 5. 行动偏好
默认推进而非等待。信息不足时，列出判断 → 提出方案 → 标注不确定性。

**应用**：不因为"还不确定 Provider 方案"就阻塞整个 Phase 1，先用最可能的方案继续。

### 6. 安全保守
权限/沙箱相关决策选更严格的选项。可以后续放松，但安全漏洞难以回收。

**应用**：不确定子 Agent 是否需要文件写入权限时，默认禁止。

边界案例原则：技术可行性有争议时，Agent 先完成草案再由人工评估；安全相关争议，直接升级到人工决策。

## 决策分类

| 类型 | 定义 | 处理方式 | 示例 |
|------|------|---------|------|
| **机械决策** | 有明确最优解 | 自动处理 | 文件格式、import 风格、并发策略 |
| **品味决策** | 多个等效方案 | 自动处理 + 记录理由 | 命名风格、目录结构、框架选择 |
| **技术选型** | 语言/模型/架构等技术判断 | **自动处理**（见技术选型决策表）| 语言选 Python/Go、模型按预算匹配 |
| **产品挑战** | 影响产品方向的 5 个用户问题 | 必须人工决定 | 创意、定位、效果预期、预算、验收 |
| **前提假设** | 假设可能错误 | 必须人工确认 | "假设目标用户是开发者" |

**铁律**：编排器只向用户问"产品挑战"和"前提假设"，绝不因技术选型阻塞用户。

## Phase 跳过逻辑

不是每个 Agent 都需要所有 Phase：

```
你的 Agent 需要多 Agent 协调吗？
├─ 否 → 跳过 Phase 7 (multiagent)
└─ 是 → 执行 Phase 7

你的 Agent 需要跨会话记忆吗？
├─ 否 → 跳过 Phase 4 (memory)
└─ 是 → 执行 Phase 4

你的 Agent 面向终端用户吗？
├─ 否（内部工具）→ Phase 5 (security) 简化为最小权限
└─ 是 → Phase 5 完整执行

你的 Agent 需要分发给他人吗？
├─ 否（自用）→ 跳过 Phase 8 (ship)
└─ 是 → 执行 Phase 8
```

**不可跳过的阶段**：Phase 0 (spec)、Phase 1 (architecture)、Phase 2 (tools)、Phase 6 (harness)。这 4 个阶段是任何 Agent 的最小必需。

## 编排执行协议

### 启动

```
用户调用 /agentforge-autoplan
    ↓
读取用户已有的 Agent 描述/需求
    ↓
判断从哪个 Phase 开始：
  ├─ 从零开始 → Phase 0
  ├─ 已有 Spec → Phase 1
  ├─ 已有架构 → Phase 2
  └─ 中途恢复 → 读取进度文件，从上次断点继续
```

### 每个 Phase 的执行流程

```
1. 调用对应的 /agentforge-{phase} skill
2. 收集 skill 输出的决策点
3. 按决策分类自动处理或向用户提问
4. 记录所有决策到进度文件
5. 验证 Phase 检查清单全部通过
6. 输出 Phase 总结 → 进入下一个 Phase
```

### 进度文件格式

```json
{
  "agent_name": "my-coding-agent",
  "started_at": "2026-04-06T10:00:00Z",
  "current_phase": 2,
  "phases": {
    "0": {
      "status": "completed",
      "decisions": [
        {"type": "user_challenge", "question": "Agent 类型？", "answer": "Coding Agent"},
        {"type": "mechanical", "question": "交互模式？", "answer": "CLI", "auto": true}
      ],
      "output": "spec.md"
    },
    "1": {
      "status": "completed",
      "decisions": [...],
      "output": "architecture.md"
    },
    "2": {
      "status": "in_progress",
      "decisions": [],
      "output": null
    }
  },
  "skipped_phases": [7],
  "skip_reasons": {"7": "单 Agent，不需要多 Agent 协调"}
}
```

### Phase 间上下文交接模板

**问题根源**：每个 agentforge-* skill 调用时都是 fresh context（尤其在多会话或 subagent 执行时），不自动继承前一阶段的决策。如果没有结构化的交接机制，Phase 3 可能用与 Phase 1 不一致的架构假设，Phase 5 不知道 Phase 2 已选了哪些外部 API（导致安全审计遗漏）。

**解决方案**：每个 Phase 完成时，除了写进度文件，还要输出一份简洁的"交接摘要"，供下一个 Phase 消费时注入到 skill 调用的 context 中。

**各 Phase 的交接契约**：

| Phase | 必须输出的关键决策 | 下一 Phase 的消费方 |
|-------|-----------------|-----------------|
| 0 Spec | Agent 类型、部署形态、目标用户、处理平面、关键约束、SLA 要求 | Phase 1（架构选型依据） |
| 1 Architecture | Loop 范式（5选1）、语言、Provider、是否多通道 | Phase 2/3/5/6（工具/上下文/安全/harness 都依赖） |
| 2 Tools | 工具列表（含外部 API 调用清单）、并发策略、MCP 工具 | Phase 3（上下文预算）、Phase 5（安全审计范围）|
| 3 Context | 上下文窗口大小、Prompt Cache 边界、压缩策略 | Phase 4（记忆 vs 压缩边界）|
| 4 Memory | 记忆范式、持久化方案、是否多租户 | Phase 5（RLS 要求）、Phase 7（共享记忆设计）|
| 5 Security | 沙箱级别、审批流要求、工具级权限列表 | Phase 6（harness hook 配置）、Phase 8（CI/CD 门禁）|
| 6 Harness | CLAUDE.md 规则摘要、Hook 配置、验证命令 | Phase 8（CI 集成）|
| 7 MultiAgent | spawn 模式、通信协议、Agent 数量 | Phase 8（打包为单进程 vs 多进程）|

**交接摘要格式**（每个 Phase 完成时写入进度文件的 `handoff_summary` 字段）：

```json
{
  "phases": {
    "0": {
      "status": "completed",
      "handoff_summary": {
        "agent_type": "RAG Q&A Bot",
        "deployment_form": "Slack Bot (HTTP mode)",
        "language": "TypeScript",
        "loop_paradigm": null,
        "external_apis": ["Confluence API", "Slack Events API"],
        "data_sources": ["Confluence", "内部 Wiki"],
        "privacy_level": "internal-only",
        "sla": {"p95_latency_ms": 3000, "availability": "99.5%"},
        "key_constraints": ["数据不可发往第三方 API", "仅限企业内网用户"]
      }
    },
    "1": {
      "status": "completed",
      "handoff_summary": {
        "loop_paradigm": "Async Generator",
        "language": "TypeScript",
        "provider": "Anthropic claude-sonnet-4-6",
        "multi_channel": false,
        "vector_db": "pgvector",
        "embedding_model": "text-embedding-3-small"
      }
    }
  }
}
```

> **模型 ID 时效性**：示例中 `claude-sonnet-4-6`（verified: 2026-04-08）、`text-embedding-3-small`（verified: 2026-04-08）仅供格式参考。实际值由 Phase 1 架构阶段自动推断写入，超过 90 天须重新 WebFetch 确认。

**调用下一 Phase skill 时的 context 注入协议**：

```
调用 /agentforge-{next_phase} 时，必须在提示词开头附加：

"Previous phase decisions:
- Agent type: RAG Q&A Bot (Slack Bot, HTTP mode)
- Architecture: Async Generator, TypeScript, Anthropic
- External APIs: Confluence API, Slack Events API
- Privacy: data must not leave internal network
[...其余 handoff_summary 内容...]

Now proceeding with Phase {N}."
```

没有这段注入，skill 会从零开始推导，可能做出与前序 Phase 矛盾的决策（如 Phase 5 选了需要联网的沙箱，但 Phase 0 要求数据不出内网）。

### 完成协议

每个 Phase 完成后，编排器输出三种状态之一：

| 状态 | 含义 | 后续行动 |
|------|------|---------|
| `DONE` | Phase 完成，无遗留问题 | 自动进入下一 Phase |
| `DONE_WITH_CONCERNS` | Phase 完成，但有风险标注 | 记录风险，继续 |
| `BLOCKED` | Phase 无法完成 | 暂停，向用户报告阻塞原因 |

全部 Phase 完成后，输出最终报告：
- 所有决策的完整记录
- 所有自动决策的理由
- 所有风险标注
- 下一步行动建议

## 与其他编排器的关系

| 编排器 | 领域 | 共同点 |
|--------|------|--------|
| `/gstack-autoplan` | Web 产品全流程 | 6 条决策原则、决策分类、完成协议 |
| `/skill-orchestrator` | 咨询技能链 | 串行编排、进度跟踪 |
| `/dev-orchestrator` | 多 Agent 开发 | Sub-agent 协调、Git 工作流 |

`agentforge-autoplan` 专注于**Agent 构建流程**，不覆盖部署运维（用 `/cloud-deployment`）和业务流程（用 `/skill-orchestrator`）。

## 当前状态 (2026年4月)

1. **Agent 构建工具链碎片化严重** — 从 Spec 到发布没有统一标准，团队在 LangGraph/CrewAI/Autogen/Vercel AI SDK 之间反复切换，每次切换导致 30-50% 的架构返工。编排器的价值在于锁定决策链路，减少中途换道。
2. **"一键生成 Agent"产品涌现但质量堪忧** — Wordware、Dify、Coze 等 no-code Agent 平台吸引了大量非技术用户，但生成的 Agent 在错误恢复、安全隔离、上下文管理方面普遍不达标。全流程编排器的定位是面向专业开发者的工程级方案。
3. **Phase 跳过逻辑的重要性上升** — 实践表明 70%+ 的 Agent 项目不需要 Phase 7（多 Agent），40%+ 不需要 Phase 8（发布），但几乎所有项目都低估了 Phase 5（安全）的工作量。编排器需要更积极地引导安全投入。
4. **进度持久化从"可选"变为"必需"** — Agent 构建周期从"一天搞定"延长到"多天迭代"，跨会话恢复能力直接决定编排器的实际可用性。

## Known Pitfalls

1. **过度自动化判断题** — 编排器为了"流畅体验"将本应由用户决策的"前提假设"类问题自动处理，导致 Agent 方向偏离。解决方案：严格执行四类决策分类，永远不自动处理"用户挑战"和"前提假设"，宁可多问一次也不替用户做方向决策。
2. **Phase 间依赖丢失** — Phase 3（上下文）的决策依赖 Phase 1（架构）的输出，但进度文件只记录了最终结果没记录推导过程，导致中途恢复后决策脱节。解决方案：进度文件必须记录每个决策的完整推导链，包括输入依据和备选方案。
3. **跳过 Phase 不等于零成本** — 标记"跳过 Phase 7"后直接进入 Phase 8，但 Phase 8 的打包策略实际依赖"是否有 sub-agent"这个信息。解决方案：跳过的 Phase 仍需输出最小声明（如"无 sub-agent"），供下游 Phase 消费。
4. **编排器本身成为瓶颈** — 串行执行 9 个 Phase 时，单个 Phase 的阻塞会冻结整条流水线。解决方案：识别可并行的 Phase 对（如 Phase 4 记忆和 Phase 5 安全在某些场景下可并行），在进度文件中标注并行窗口。
5. **决策疲劳导致用户放弃** — 连续提出 5+ 个"用户挑战"类问题时，用户倾向于随意回答或直接退出。解决方案：将多个相关决策合并为一次结构化提问，附带推荐选项和理由。

## 延伸阅读

| 主题 | 资源 |
|------|------|
| Phase 0: 需求定位与 Spec | `/agentforge-spec` |
| Phase 1: 架构选型 | `/agentforge-architecture` |
| Phase 2: 工具系统设计 | `/agentforge-tools` |
| Phase 3: 上下文工程 | `/agentforge-context` |
| Phase 4: 记忆系统 | `/agentforge-memory` |
| Phase 5: 安全与权限 | `/agentforge-security` |
| Phase 6: Harness 工程 | `/agentforge-harness` |
| Phase 7: 多 Agent 协调 | `/agentforge-multiagent` |
| Phase 8: 打包与发布 | `/agentforge-ship` |
| Phase 10: 自进化 | `/agentforge-evolution` |
| Phase 11: 测试、验收与基准 | `/agentforge-benchmark` |
| 云部署运维 | `/cloud-deployment` |

## 编排检查清单

- [ ] 确认了起始 Phase（从零 / 从中间 / 恢复）
- [ ] 确认了跳过的 Phase 及理由
- [ ] 每个 Phase 的检查清单全部通过
- [ ] 所有"用户挑战"类决策已获用户确认
- [ ] 所有"前提假设"类决策已获用户确认
- [ ] 进度文件持续更新
- [ ] 最终报告包含完整决策记录

## 全自主 vs 引导模式的调用协议

### 两种调用模式

| 模式 | 触发词 | 编排行为 |
|------|--------|---------|
| **引导模式**（默认）| "帮我设计一个 Agent" | 每个决策点都问用户，用户全程参与 |
| **全自主模式** | "全自主执行 agentforge 全流程" | 机械决策 + 品味决策自动处理，仅"用户挑战"类和"前提假设"类才暂停问用户 |

### 全自主模式的执行协议

当用户指定全自主模式时，编排器按以下方式驱动 Phase 间的自动跳转：

**1. Phase 完成后的自动跳转逻辑**

```
当前 Phase 输出 DONE
    ↓
从进度文件读取 handoff_summary（本 Phase 的输出）
    ↓
构建下一 Phase 的注入 prompt：
  "Previous phase decisions:
   [handoff_summary 内容]
   Now proceeding with Phase N."
    ↓
调用 /agentforge-{next_phase}，将注入 prompt 作为 context 前缀
    ↓
继续执行，直到遇到"用户挑战"或"前提假设"类决策 → 暂停询问用户
```

**2. 真正需要暂停的判断标准**

编排器应该中断并询问用户当且仅当：
- 发现了"前提假设"类问题（如"假设目标用户是开发者"——这个假设可能错误）
- 发现了"用户挑战"类决策（如"Agent 类型选 RAG 还是 Code Agent？"）
- Phase 状态变为 `BLOCKED`（缺少必要输入无法继续）

**3. 不应暂停的情况**（编排器常见过度谨慎）

```
❌ 错误：每步都问"我接下来要做 X，可以吗？"
❌ 错误：品味决策（命名风格、目录结构）也要用户确认
✓ 正确：自动处理机械决策，记录理由，在最终报告中汇报
```

### 快速启动

**引导模式**：
```
我要构建一个 [描述你的 Agent]。
```

**全自主模式**：
```
全自主执行 agentforge 全流程。Agent 描述：[描述]。
机械决策和品味决策自动处理，只在"用户挑战"和"前提假设"时询问。
```

编排器会从 Phase 0 开始，根据模式决定是否自动跳转到下一 Phase。
