---
name: agentforge-benchmark
description: AgentForge Phase 11 — Agent testing, acceptance, and benchmark evaluation. Test layering strategy + tool call mocking + industry benchmark index (SWE-bench/WebArena/AgentBench/τ-bench) + custom benchmark design + acceptance criteria framework. Triggered when user says "agent testing", "agent acceptance", "benchmark", "SWE-bench", or "how to test an agent".
triggers:
  - agent testing
  - agent acceptance
  - benchmark testing
  - SWE-bench
  - benchmark
  - agent evaluation
  - how to test an agent
metadata:
  version: "1.0.0"
  last_updated: "2026-04-07"
  category: "agent-engineering"
---

# AgentForge Phase 11: 测试、验收与基准评测

> 上一步：`/agentforge-evolution`（Phase 10） | 系列入口：`/agentforge`
> 可观测性配套：`/agent-observability`

## 核心认知

> **Agent 测试的本质困难：输出是非确定性的。你测试的不是"精确输出"，而是"行为合理性"。**

普通函数测试：给定输入 A，期望输出 B。
Agent 测试：给定任务 T，期望 Agent 以合理的工具调用序列、在合理轮次内、产出质量合格的结果。"合理"和"合格"需要你先定义。

**三层测试对应三类不确定性**：

```
Level 1: 单元测试 — 工具函数确定性部分
  不确定性来源：无（纯函数）
  可以：精确断言输入/输出/报错路径
  不能测：LLM 是否选了正确工具

Level 2: 集成测试 — 工具调用编排
  不确定性来源：LLM 选择行为（Mock 掉）
  可以：验证给定 LLM 输出时工具被正确触发
  不能测：LLM 在真实任务中的表现

Level 3: 端到端任务测试
  不确定性来源：LLM 全程参与
  可以：验证 Agent 对完整任务的完成率
  不能测：每次运行结果完全一致（需要统计采样）
```

---

## 决策一：Agent 测试分层

### Level 1 — 工具单元测试

工具函数是 Agent 中最容易测试的部分。输入/输出确定，副作用可控。

**测试重点**：
- Schema 验证（非法参数是否正确拒绝）
- 边界条件（空文件、权限拒绝、网络超时）
- 错误信息质量（是否包含修复建议，参见 `/agentforge-tools` Layer 2）

```python
# Python 示例：工具单元测试
def test_file_edit_tool_rejects_nonexistent_path():
    result = file_edit_tool(path="/nonexistent/file.txt", old="x", new="y")
    assert result.error_code == "FILE_NOT_FOUND"
    assert "Glob" in result.suggestion  # 错误信息引导使用 Glob 查找文件

def test_bash_tool_schema_validation():
    with pytest.raises(ValidationError) as exc:
        bash_tool(command=None)  # 必填字段缺失
    assert "command" in str(exc.value)
```

### Level 2 — 工具调用编排测试（Mock LLM）

验证 Agent 在"给定 LLM 做了某个决策时，工具系统是否正确响应"。

**Mock 策略选型**：

| 策略 | 适用场景 | 优劣 |
|------|---------|------|
| **Record & Replay** | 回归测试 | 录制真实轨迹，回放时验证行为一致性；轨迹变更后需重录 |
| **Deterministic Mock** | 单路径测试 | 给定固定 LLM 输出序列，验证工具调用是否正确触发 |
| **Behavior Mock** | 边界/失败路径 | 模拟工具失败、超时、权限拒绝，验证 Agent 的错误处理路径 |
| **Replay + Assertion** | Harness 回归 | 录制完整工具调用轨迹，断言关键工具被调用且参数符合预期 |

```python
# Deterministic Mock 示例
def test_agent_reads_file_before_edit(mock_llm):
    # 给定 LLM 先输出"读文件"再输出"编辑文件"的决策序列
    mock_llm.responses = [
        ToolCallResponse(tool="FileRead", params={"path": "/src/main.py"}),
        ToolCallResponse(tool="FileEdit", params={"path": "/src/main.py", ...}),
        TextResponse("Done"),
    ]
    agent.run("修复 main.py 中的 bug")
    
    calls = mock_llm.recorded_tool_calls
    assert calls[0].tool == "FileRead"      # 先读
    assert calls[1].tool == "FileEdit"      # 再改
    assert calls[1].params["path"] == "/src/main.py"
```

### Level 3 — 端到端任务测试

真实 LLM，真实工具，完整任务。**不追求每次结果完全一致，追求任务完成率在统计上稳定**。

**实施要点**：
1. **多次采样** — 每个测试任务运行 5-10 次，取通过率（非单次 pass/fail）
2. **任务难度分级** — P0（核心功能）/ P1（常见场景）/ P2（边缘案例）
3. **轮次预算** — 设定每个任务的最大 Agent 轮次上限，超出即判定失败
4. **验收方式** — 参见"决策五：验收标准体系"

---

## 决策二：回归测试策略

**问题**：Agent 更新（Harness 调整、Prompt 变更、模型升级）后，如何防止已解决的问题复发？

### Bug 驱动的回归集

每次发现 Agent 失败案例 → 将其转为回归测试用例：

```json
// regression_cases.jsonl
{
  "id": "REG-042",
  "trigger": "2026-03-15",
  "description": "Agent 在文件不存在时仍尝试编辑，导致 5 轮失败后放弃",
  "task": "修改 src/auth.py 中的 login 函数",
  "setup": {"files": {}},  // 刻意不创建 auth.py
  "pass_criteria": "Agent 在 2 轮内通过 Glob 发现文件不存在，并请求澄清或终止",
  "fail_criteria": "Agent 尝试 FileEdit 超过 1 次"
}
```

### Harness 变更前后对比

改 CLAUDE.md / Hook 配置 / 系统提示前：
1. 在基准任务集上跑完整 Level 3 测试，记录基线通过率
2. 执行 Harness 变更
3. 重新跑相同任务集，对比通过率
4. 通过率下降 > 5% → 回滚变更，分析原因

---

## 决策三：行业基准索引

> **注意：这些数字变化极快（季度级别）。使用前必须 WebFetch 最新排行。** 表格仅提供基准定义和选型依据。

| 基准 | 测什么 | 适用 Agent 类型 | 获取最新数据 |
|------|--------|----------------|------------|
| **SWE-bench** | GitHub Issue 真实修复能力（300+ 仓库） | Coding Agent | `site:swebench.com` |
| **SWE-bench Verified** | 人工筛选高质量子集，结果更可信 | Coding Agent | 同上 |
| **HumanEval / MBPP** | 函数级代码生成准确率 | Coding Agent（能力下限） | `site:paperswithcode.com` |
| **Terminal Bench 2.0** | 真实终端任务 + Harness 效果验证 | Coding Agent with Harness | `github.com/kodu-ai/terminal-bench` |
| **WebArena** | 真实网站操作任务完成率（电商/论坛/代码） | GUI/Browser Agent | `webarena.dev` |
| **VisualWebArena** | 含图像理解的网页操作 | GUI Agent（视觉增强） | 同上 |
| **OSWorld** | 桌面操作系统完整任务（跨应用） | Computer-use Agent | `os-world.github.io` |
| **AgentBench** | 多环境 Agent 综合基准（8 个任务类型） | 通用 Agent | `github.com/THUDM/AgentBench` |
| **τ-bench（tau-bench）** | 真实 Tool Use 场景（零售/航空） | 工具型 Agent | `github.com/sierra-research/tau-bench` |
| **GAIA** | 通用 AI 助手多步推理 | Research / Reasoning Agent | `huggingface.co/datasets/gaia-benchmark` |
| **MTEB** | Embedding 质量多任务评测 | 用于 RAG/语义缓存的 Agent | `huggingface.co/spaces/mteb/leaderboard` |
| **RAGAS** | RAG 系统专项评测：Faithfulness / Answer Relevancy / Context Precision / Context Recall | RAG / Knowledge / Q&A Agent | `docs.ragas.io` |
| **DeepEval** | 14+ LLM 指标含 G-Eval，含 RAG 专项（Contextual Precision/Recall）+ CI 集成 | RAG / Knowledge Agent，需要 CI 门禁 | `docs.confident-ai.com` |
| **RAGBench** | 10万+ 样本的大规模 RAG 基准，TRACe 框架（可解释性强）| RAG Agent 大规模评测 | `arxiv.org/abs/2407.11005` |

### 如何用基准指导你的 Agent 开发

```
你的 Agent 类型是？
│
├─ Coding Agent → SWE-bench 是黄金标准
│   ├─ 入门校准：HumanEval（函数级，快速跑）
│   ├─ Harness 效果：Terminal Bench 2.0（对比改前改后）
│   └─ 生产级目标：SWE-bench Verified > 30%（2026年中等水平）
│
├─ GUI / Browser Agent → WebArena 系
│   ├─ 纯网页：WebArena
│   ├─ 含截图理解：VisualWebArena
│   └─ 桌面 GUI：OSWorld
│
├─ 工具型 Agent → τ-bench 最贴近生产
│   └─ 特点：含真实用户意图噪声、工具调用失败率高
│
├─ Research / 通用 Agent → GAIA
│   └─ 特点：多步推理 + 工具组合，难度高
│
└─ RAG / Knowledge / Q&A Agent → RAGAS 是黄金标准
    ├─ 核心指标：Faithfulness（答案是否忠于检索结果）
    │             Answer Relevancy（答案是否回应了问题）
    │             Context Precision（检索结果精准度）
    │             Context Recall（检索结果完整度）
    ├─ 工具选型：RAGAS（轻量，快速上手）/ DeepEval（需要 CI 集成）/ RAGBench（大规模对比）
    ├─ 注意：检索质量（Context Precision/Recall）和生成质量（Faithfulness）是两个独立失败源
    │         调试时先隔离：先跑纯检索评测，再跑端到端评测
    └─ WebFetch 最新分数：`docs.ragas.io` + `docs.confident-ai.com/benchmarks`
```

---

## 决策四：自定义基准设计

行业基准不覆盖你的场景时，建自己的基准。

### 黄金标准数据集构建

```
Step 1：收集真实任务
  → 从用户日志、客服记录、你自己的实际使用中提取
  → 50-200 个任务（够代表性，不用多）

Step 2：人工验收建立标签
  → 对每个任务：人工执行一遍，记录"期望行为"和"验收标准"
  → 不要只记录"正确答案"，要记录"什么算通过"

Step 3：定义指标
  → 任务完成率（通过 / 总数）
  → 轮次效率（完成任务的平均 Agent 轮次）
  → 工具调用精准度（无效工具调用占比）
  → 错误恢复率（遇到失败后成功恢复的比例）

Step 4：自动化评测
  → 用 LLM-as-Judge 或规则检查器做自动评分
  → 在黄金标准上校准评分器的准确率（要求 ≥ 90% 与人工一致）
```

### 0→1 冷启动策略（没有历史数据时怎么建第一批黄金样本）

新 Agent 没有用户日志、没有历史 bug 记录——怎么从零建立可信的基准数据集？

```
冷启动三步法：

Step 1：用自己的 Agent 跑真实任务（种子任务法）
  → 列出你认为 Agent 应该能做的 20-30 个核心任务
  → 亲自用 Agent 执行每个任务，记录完整轨迹
  → 人工评判：通过 / 失败 / 部分通过 + 理由
  → 这 20-30 个人工标注的样本就是黄金数据集 v0

Step 2：覆盖边界场景（主动注入失败）
  → 不要只收集成功案例——失败案例的价值 5x
  → 故意构造会失败的场景：
    - 文件不存在
    - 权限被拒绝
    - API 返回错误
    - 任务描述模糊
  → 记录"正确行为"：Agent 应该怎么处理（请求澄清？优雅终止？）

Step 3：首个 Bug 出现后立刻转化
  → 第一次发现 Agent 行为不符合预期时，立刻：
    1. 保存触发该 bug 的完整输入
    2. 记录期望行为 vs 实际行为
    3. 将其加入回归测试集
  → 永远不要"记住了待会再加"——每个 bug 都是不可复制的黄金样本
```

**冷启动最小可行集**（足够开始评测的最小数量）：
- Level 1（工具单元）：覆盖每个工具的 3 个边界 case = 工具数 × 3
- Level 2（编排集成）：5-10 个典型工具调用序列
- Level 3（端到端）：10-15 个核心场景 + 5 个故意失败场景

**何时升级**：
- 黄金样本 < 20 → 只能做定性判断，不能做统计对比
- 黄金样本 20-50 → 可以做简单通过率对比
- 黄金样本 > 50 → 可以信任 LLM-as-Judge（在此数量上校准一致率才有统计意义）

### 指标设计原则

**不要的指标**：
- 单次运行 pass/fail（方差太大）
- LLM 输出的"主观评分"（未校准）

**要的指标**：
- N 次采样的任务完成率（统计稳定）
- 轮次效率（防止 Agent 绕远路但最终通过）
- 工具调用的 Precision/Recall（调对了哪些，漏了哪些）

---

## 决策五：验收标准体系

### 自动化验收 vs 人工验收

| 维度 | 自动化验收（LLM-as-Judge） | 人工验收 |
|------|--------------------------|---------|
| 成本 | 低（API 调用成本） | 高（人时成本） |
| 速度 | 快（分钟级） | 慢（小时/天级） |
| 适用 | 有明确判断标准的任务 | 主观性强/全新场景 |
| 风险 | 评判 LLM 自身偏差 | 人工疲劳/标准漂移 |
| 用途 | 每次 CI 运行 | 建立黄金标准、周期性抽检 |

### LLM-as-Judge 实现要点

```python
JUDGE_PROMPT = """
你是一个严格的 Agent 质量评判员。

任务：{task_description}
成功标准：{acceptance_criteria}
Agent 的执行轨迹：{agent_trace}
Agent 的最终输出：{agent_output}

评判规则：
1. 只判断是否满足了"成功标准"，不做主观评价
2. 如果成功标准未明确覆盖某个维度，标记为"不适用"
3. 给出 PASS / FAIL / PARTIAL + 一句理由

输出 JSON：{"verdict": "PASS|FAIL|PARTIAL", "reason": "..."}
"""
```

**校准要求**：在 100 个人工标注的样本上验证 Judge 准确率 ≥ 90%，否则 Judge 不可信。

### 验收标准模板（写入 Agent Spec）

```markdown
## 验收标准

### 核心场景（必须全部通过）
- [ ] 场景 A：[描述] → 通过标准：[具体可检查的条件]
- [ ] 场景 B：[描述] → 通过标准：[具体可检查的条件]

### 性能指标（统计口径）
- 任务完成率 ≥ ___% （N=___ 次采样）
- 平均完成轮次 ≤ ___
- 错误恢复率 ≥ ___%

### 回归保护（不得退化）
- 历史 bug 回归集：100% 通过
- Harness 变更前后：完成率变化 < 5%
```

---

## 当前状态 (2026年4月)

1. **SWE-bench 已分化为三个版本** — SWE-bench Lite（已近饱和，OpenAI 发现训练数据污染，已停止报告）、SWE-bench Verified（当前主流，顶级模型 Claude Opus 4.5 达 80.9%）、SWE-bench Pro（2026 年推出，更难，Augment Code Auggie 在此版本领先商业产品，差距约 15-17 问题）。选 Coding Agent 基准时**优先 SWE-bench Verified 或 Pro，不再使用 SWE-bench Lite**
2. **LLM-as-Judge 走向主流** — Anthropic、DeepMind 均发布了 LLM 评判一致性研究，在结构化任务上 LLM Judge 与人工一致率可达 85-92%，但在开放性任务上仍不可替代人工
3. **τ-bench 填补工具型 Agent 空白** — 现有基准多测"单轮 Function Calling"，τ-bench 引入真实噪声（用户意图不清、工具中途失败）更贴近生产场景，正成为工具型 Agent 的标准验收平台
4. **自定义基准比行业基准更有商业价值** — 行业基准测"通用能力"，你的 Agent 面对的是特定场景，自定义基准分数才是真实的产品质量指标。建议：行业基准用于选模型/比较 Harness，自定义基准用于验收产品

## Known Pitfalls

1. **只跑一次就判 pass/fail** — LLM 输出有随机性，单次结果置信度低。解决：Level 3 测试必须多次采样（≥5 次），用通过率而非单次结果。
2. **行业基准数字已过期** — 训练数据截止导致记忆的基准分数落后 6-12 个月。解决：使用前必须 WebFetch 最新排行，不使用记忆中的数字。
3. **LLM-as-Judge 未校准** — Judge LLM 的判断偏差没有经过人工验证，评测结果不可信。解决：在人工标注的黄金样本上验证一致率，< 90% 不可信。
4. **只测 happy path** — 回归集只包含成功案例，没有边界/失败场景。解决：每次发现 Agent 失败 → 立刻转化为回归测试用例，**失败案例的价值比成功案例高 5x**。
5. **把 Level 3 测试放在 CI 里** — 端到端测试成本高（真实 LLM 调用）、速度慢、有随机性，不适合每次 commit 触发。解决：Level 1/2 → CI（每次提交）；Level 3 → 每日定时跑 + 版本发布前手动触发。

## 延伸阅读

| 主题 | 资源 |
|------|------|
| Harness 失败诊断 | `/agentforge-harness` |
| 可观测性（日志/指标/追踪） | `/agent-observability` |
| 自进化的安全测试门禁 | `/agentforge-evolution` |
| SWE-bench 官方 | WebFetch `swebench.com` |
| Terminal Bench 2.0 | WebFetch `github.com/kodu-ai/terminal-bench` |
| τ-bench | WebFetch `github.com/sierra-research/tau-bench` |
| MTEB Embedding 排行 | WebFetch `huggingface.co/spaces/mteb/leaderboard` |

## 测试与验收检查清单

- [ ] 工具函数有单元测试（Level 1）
- [ ] Agent 编排逻辑有 Mock LLM 集成测试（Level 2）
- [ ] 定义了端到端任务集 + 验收标准（Level 3）
- [ ] 历史 bug 已转化为回归用例
- [ ] 指定了行业基准参照（SWE-bench / τ-bench / WebArena 等，按 Agent 类型）
- [ ] LLM-as-Judge 在黄金样本上校准一致率 ≥ 90%（若使用自动化验收）
- [ ] Level 3 测试不在每次 CI 提交触发（成本控制）
- [ ] Agent Spec 中已填写"验收标准"字段（参见 `/agentforge-spec`）
- [ ] **Research / Q&A Agent 专项**：验收包含幻觉率抽样测试（随机抽取 ≥20 个输出，人工核查引用来源准确率）；目标 <20% 幻觉率，否则不视为生产就绪（2026 数据：主流 Research Agent 引用幻觉率 26-37%，未加外部验证钩子的 Agentic RAG 尤其高危）

## 逆向审计（Diagnose Mode）

> 由 `/agentforge-diagnose` 调用——对已有代码进行 D9 基准测试维度静态审计。

| # | 检查项 | 检查方式 | 通过标准 |
|---|--------|---------|---------|
| B1 | 测试套件存在 | `find . -path "*/test*" -name "*.py" -o -path "*/test*" -name "*.ts" \| wc -l` | tests/ 目录有实质测试文件（>3 个） |
| B2 | 核心任务有端到端测试 | 读测试文件，判断是否覆盖 Agent 主要用例 | 不只是单元测试，有 Agent 行为级 e2e 测试 |
| B3 | 已知失败有回归测试 | `git log --since="90 days ago" --grep="fix\|bug" \| head -20` + 对比测试文件变更 | 每次修复后有对应回归测试 |
| B4 | 评估指标量化 | `grep -rn "assert\|expect\|threshold\|success_rate" tests/` | 有明确数值指标（成功率/延迟/成本），非感官判断 |
| B5 | 成本追踪 | `grep -rn "usage\|token_count\|cost" src/` | 有 token 用量或 API 成本记录机制 |

**高概率问题**：无端到端测试（P1 无法验证 Agent 整体行为）、评估靠主观感觉（P2 无法量化改进）、无成本追踪（P2 上线后账单震惊）

## 下一步

Phase 11 完成 → Agent 通过验收 → 可进入 `/agentforge-autoplan` 触发全流程复盘，或进入 `/agentforge-evolution` 添加自进化能力。
