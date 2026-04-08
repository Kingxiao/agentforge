# 编辑格式选型：Agent 如何修改代码

> 来源：研究报告 Chapter 9（L732-L789）
> 编辑格式是实际生产中最容易出错的环节之一。选错格式会导致 Agent 反复编辑失败。

## 5 种编辑格式对比

| 格式 | 代表 Agent | 原理 | 优势 | 劣势 |
|------|-----------|------|------|------|
| **Search/Replace Block** | Aider (EditBlock) | `<<<SEARCH`/`===`/`>>>REPLACE` 块 | 人可读，格式简单 | 搜索目标不唯一时出错 |
| **Unified Diff** | Aider (UDiff), Cline | 标准 unified diff 格式 | 业界标准，工具丰富 | LLM 生成的行号经常不准 |
| **Whole File** | Aider (WholeFile) | 输出整个文件内容 | 不会出格式错误 | Token 浪费严重 |
| **精确替换** | Claude Code (Edit) | `old_string` → `new_string` 精确匹配 | 精确、安全 | 要求 old_string 唯一 |
| **Apply Patch** | Codex CLI | Git patch 格式 | Git 原生支持 | 格式复杂，LLM 容易出错 |

## Claude Code 的精确替换策略

```typescript
Edit({
  file_path: "/absolute/path",
  old_string: "要替换的精确文本",
  new_string: "替换后的文本",
  replace_all: false  // 默认只替换第一个匹配
})
```

**关键约束**：
- `old_string` 必须在文件中**唯一匹配**，否则报错
- 强制使用**绝对路径**
- 编辑前必须先用 `Read` 工具读过文件（否则工具拒绝执行）
- 保留精确缩进（tab/space 敏感）

**为什么 Claude Code 选这个方案**：
- 比 diff 更不容易出行号错误（LLM 生成 diff 时行号是痛点）
- 比 whole-file 更省 token（只传变更部分）
- 唯一性约束保证编辑的确定性（不会误改同名代码）

## Aider 的多态编辑系统

Aider 最独特的设计——**同一个 Agent 可以运行时切换编辑格式**：

```python
# 编辑格式是 Coder 类的多态属性
class EditBlockCoder(Coder):   edit_format = "diff"
class UnifiedDiffCoder(Coder): edit_format = "udiff"
class PatchCoder(Coder):       edit_format = "patch"
class WholeFileCoder(Coder):   edit_format = "wholefile"
class ArchitectCoder(Coder):   edit_format = "architect"
```

### Architect 模式（两阶段分离）

1. **架构模型**做高层规划（"哪些文件需要改，怎么改"）
2. **编辑模型**执行具体修改（根据规划生成编辑块）

价值：贵的模型只做判断，便宜的模型做执行，成本优化。

### Fuzzy Matching

- 编辑块的搜索目标支持模糊匹配
- 处理 LLM 输出中的微小格式差异（多余空格、缩进偏移）
- 提高编辑成功率，降低"找不到匹配"的失败率

## 选型决策树

```
你的 Agent 如何修改代码？
│
├─ 只需要精确的小范围修改（大部分 coding agent 场景）
│  → 精确替换（Claude Code 方案）
│     优先：确定性高、token 效率好
│
├─ 需要支持多种编辑策略，按场景切换
│  → 多态编辑（Aider 方案）
│     优先：灵活性强，可按模型能力选策略
│
├─ 修改通常涉及整个文件重写（模板生成等）
│  → Whole File
│     优先：零格式错误，但仅限小文件
│
└─ 需要与 Git 工具链深度集成
   → Apply Patch（Codex 方案）
      注意：LLM 生成 patch 格式的出错率较高
```

## 各格式的 Token 效率对比

以修改一个 100 行文件中的 3 行为例：

| 格式 | 输出 token 数（估算） | 效率比 |
|------|---------------------|--------|
| 精确替换 | ~30 | 1x（基准） |
| Search/Replace Block | ~50 | 1.7x |
| Unified Diff | ~60 | 2x |
| Apply Patch | ~70 | 2.3x |
| Whole File | ~300 | 10x |

**结论**：精确替换的 token 效率最高，Whole File 最浪费。但 Whole File 的成功率最高（因为不存在格式解析问题）。
