# 记忆范式深度实现对比

> 三流派的工程细节。配合 SKILL.md 决策树使用。

## File Memory [CC]

### MEMORY.md 结构

```markdown
# Memory Index

## 用户偏好
- [编码风格偏好](user_coding_style.md) — Rust 优先，函数式风格，错误处理用 Result

## 项目
- [ProjectX 架构](project_x_architecture.md) — 微服务，gRPC，PostgreSQL
- [ProjectY 状态](project_y_status.md) — MVP 阶段，3/7 模块完成

## 反馈
- [调试习惯](feedback_debugging.md) — 用户不喜欢过度 log，偏好断点调试
```

### 约束参数

| 参数 | 值 | 来源 |
|------|-----|------|
| MEMORY.md 最大行数 | 200 行 | [CC] |
| MEMORY.md 最大字节 | 25,000 bytes | [CC] |
| 单个记忆文件最大字符 | 40,000 chars | [CC] |
| 记忆类型 | user / feedback / project / reference | [CC] |
| 加载时机 | 每次会话开始时注入 system prompt | [CC] |
| 优先级层级 | Layer 5（最高优先级）| [CC] |

### 自动提取实现 [CC]

```
触发条件：
  - 每 N 次工具调用（内部计数器）
  - 用户输入 /memory
  - compact 触发时

提取流程：
  1. fork 子进程（独立 context，不阻塞主循环）
  2. 子进程收到完整对话历史
  3. LLM 判断是否有新的值得记忆的信息
  4. 如有 → 判断类型（user/feedback/project/reference）
  5. 检查是否与现有记忆冲突 → 更新或新建
  6. 写入 MEMORY.md 索引 + 对应的 .md 文件
  7. 子进程退出
```

### 优势与局限

**优势**：
- 零外部依赖 — 只需文件系统
- Git 可追踪 — 记忆变更有完整历史
- 人类可审计 — 打开文件就能看到 Agent 记住了什么
- 跨 Agent 共享 — 任何能读 Markdown 的 Agent 都能用

**局限**：
- 无语义搜索 — 只能靠索引文件的标题匹配
- 容量上限 — 25KB 约等于 50-100 条结构化记忆
- 手动维护 — 记忆过多时需要人工修剪
- 无多租户 — 单用户设计

## Block Memory [LT]

### Block 类定义

```python
class Block:
    label: str          # 如 "persona", "human", "project"
    value: str          # 实际内容
    limit: int          # 字符数上限（默认 2000）
    read_only: bool     # 是否允许 Agent 修改
    
    # 系统会追踪 token 使用量
    # Core Memory Block 内容始终在 system prompt 中
```

### 三层记忆架构

**Core Memory（上下文窗口内）**：
```
始终在 system prompt 中，Agent 每轮都能看到。
存放高频使用的关键信息：
  - persona block: Agent 身份和能力描述
  - human block: 用户画像和偏好
  - 自定义 block: 项目状态、任务上下文等

修改方式：Agent 通过内置工具修改
  core_memory_append(label, content)
  core_memory_replace(label, old_text, new_text)
```

**Archival Memory（长期存储）**：
```
不在上下文窗口中，需要 Agent 主动检索。
支持语义搜索（embedding + 向量索引）。
无容量上限（受后端存储限制）。

操作工具：
  archival_memory_insert(content)          → 存入
  archival_memory_search(query, k=10)      → 语义检索 top-k
```

**Recall Memory（近期对话）**：
```
自动管理，Agent 无需显式操作。
最近 N 轮对话，按时间衰减权重。
用于"刚才说了什么"类型的短期回忆。
```

### Heartbeat 机制 [LT]

Letta 的独特设计：Agent 可以主动请求"再次被调用"。

```
Agent 返回：
{
  "tool_calls": [...],
  "request_heartbeat": true   ← 告诉系统"执行完工具后再调用我"
}

用途：
  - 连续多步操作（不需要用户输入触发）
  - 后台记忆整理
  - 自主探索归档记忆
```

### 持久化 [LT]

```
SQLAlchemy ORM
├── agents 表（Agent 配置 + Core Memory 快照）
├── blocks 表（所有 Block 内容）
├── passages 表（Archival Memory 条目 + embedding）
├── messages 表（对话历史 = Recall Memory）
└── tools 表（Agent 可用工具定义）

支持后端：SQLite（开发）/ PostgreSQL（生产）
```

### 优势与局限

**优势**：
- Agent 自主管理 — 不依赖外部脚本或 fork 进程
- 多租户原生 — 每个 Agent 实例有独立的 Block 集合
- 语义检索 — Archival Memory 支持向量搜索
- 可扩展 — 自定义 Block 类型和工具

**局限**：
- 不透明 — 用户不容易审计 Agent 记住了什么
- Core Memory 容量有限 — 每个 Block 默认 2000 字符
- 依赖 embedding 模型 — Archival Memory 需要向量化
- 冷启动问题 — 新 Agent 的 Core Memory 是空的

## Hierarchical Semantic Memory [MU]

### 文件系统隐喻

```
memory_store/
├── preferences/
│   ├── coding_style.json      # {"type": "preference", "content": "..."}
│   ├── communication.json
│   └── tools.json
├── relationships/
│   ├── colleague_alice.json
│   └── manager_bob.json
├── knowledge/
│   ├── rust_patterns.json
│   └── architecture_decisions.json
└── context/
    ├── current_project.json
    └── recent_decisions.json
```

### memorize() Pipeline [MU]

```
输入: 原始文本
    ↓
Step 1: preprocess
    - 清洗噪声（重复、无意义内容）
    - 标准化格式
    ↓
Step 2: type_extract（LLM 调用）
    - 判断记忆类型：preference / relationship / knowledge / context
    - 提取结构化字段
    ↓
Step 3: categorize（LLM 调用）
    - 判断归属目录
    - 检查是否与现有记忆冲突
    - 冲突 → merge 策略（覆盖 / 追加 / 版本化）
    ↓
Step 4: store
    - 写入对应目录
    - 更新索引
    - 生成 embedding（用于后续检索）
    - 返回 revision token（用于版本追踪）
```

### retrieve() Pipeline [MU]

```
输入: 查询文本
    ↓
Step 1: decompose（LLM 调用）
    - 将复杂查询分解为子查询
    - 例: "用户最近的 Rust 项目架构决策"
      → ["user Rust preferences", "recent architecture decisions", "project context"]
    ↓
Step 2: search（并行执行）
    - 对每个子查询，在所有相关目录中搜索
    - 向量相似度 + 关键词匹配混合
    ↓
Step 3: rerank（LLM 调用）
    - 对候选结果按相关性重排序
    - 考虑时间衰减（近期记忆权重更高）
    ↓
Step 4: return
    - 返回 top-k 结果
    - 附带来源目录和置信度分数
```

### Pipeline 版本控制 [MU]

```python
# 每次 memorize 返回 revision token
revision = memory.memorize("用户偏好 Rust over Go")
# → "rev_20260406_001"

# 可以回滚到特定版本
memory.rollback("rev_20260406_001")

# 用途：
# - A/B 测试不同记忆策略
# - 回滚错误的记忆提取
# - 审计记忆变更历史
```

### 可插拔后端 [MU]

```
MemoryBackend 接口:
  - InMemoryBackend    → 测试/开发
  - SQLiteBackend      → 单机生产
  - PostgresBackend    → 多机扩展

LLM Profile 路由:
  - embedding: 用轻量模型（如 text-embedding-3-small）
  - type_extract: 用中等模型（如 claude-haiku）
  - rerank: 用强模型（如 claude-sonnet）
  - 不同步骤用不同模型，平衡成本和质量
```

### 优势与局限

**优势**：
- 语义搜索 — 不只是关键词匹配
- 自动分类 — 减少人工维护
- Pipeline 可插拔 — 每个步骤可独立替换
- 版本控制 — 记忆变更可追溯和回滚

**局限**：
- 架构复杂 — memorize 一次可能触发 2-3 次 LLM 调用
- 成本高 — embedding + LLM 分类 + LLM 重排序
- 冷启动慢 — 需要积累足够记忆才能体现语义搜索价值
- 运维负担 — 需要管理 embedding 模型、向量索引、后端存储

## 三流派选型总结

| 维度 | File [CC] | Block [LT] | Hierarchical [MU] |
|------|-----------|-------------|---------------------|
| 复杂度 | 低 | 中 | 高 |
| 外部依赖 | 无 | SQLite/PG | SQLite/PG + Embedding |
| 语义搜索 | 无 | Archival 层有 | 全局有 |
| 容量上限 | ~25KB | Core 有限，Archival 无限 | 无限 |
| Agent 自主管理 | 否（fork 提取） | 是（内置工具） | 是（pipeline 自动） |
| 人类可审计 | 极好（Markdown） | 中等（需查 DB） | 差（分散 + embedding） |
| 多租户 | 否 | 原生支持 | 原生支持 |
| 适用规模 | 1 人 / 1 Agent | 多用户 / 多 Agent | 平台级 |
| 实现成本 | 1 天 | 1 周 | 2-4 周 |
