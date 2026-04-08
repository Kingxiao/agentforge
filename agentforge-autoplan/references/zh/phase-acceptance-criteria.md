# 阶段验收标准 + 工时估算 + 技术选型速查

> 来源：研究报告 Chapter 13（L942-L097）
> "怎样才算做完"的定义 + 每阶段的具体目录结构蓝图

## 6 阶段验收标准

| 阶段 | 工时估算 | 验收标准 |
|------|---------|---------|
| **Phase 1: 最小可行 Agent** | 1-2 天 | Agent 能独立完成简单 bug fix（读代码→定位→修改→验证） |
| **Phase 2: 上下文工程** | 3-5 天 | 长会话（50+ 轮）后仍能正确引用早期上下文 |
| **Phase 3: 安全与权限** | 3-5 天 | 无法通过 prompt injection 让 Agent 执行危险命令 |
| **Phase 4: 工具生态扩展** | 5-7 天 | 通过 MCP 连接外部服务（数据库、API）并正确使用 |
| **Phase 5: 多 Agent 与记忆** | 5-7 天 | 新会话自动恢复上次未完成的任务进度 |
| **Phase 6: UI 与产品化** | 5-7 天 | 非技术用户能在 3 分钟内完成首次使用 |

**总计**：20-33 天（1 人全职）

## 各阶段目录结构蓝图

### Phase 1: 最小可行 Agent
```
├── agent_loop.rs/go/ts    # 主循环（LLM → Tool → LLM）
├── provider.rs/go/ts      # LLM API 客户端
├── tools/
│   ├── bash.rs            # Shell 执行
│   ├── read.rs            # 文件读取
│   └── write.rs           # 文件写入
└── main.rs                # 入口
```

### Phase 2: 上下文工程
```
新增：
├── context/
│   ├── system_prompt.rs   # 分层系统提示
│   ├── claude_md.rs       # CLAUDE.md 加载器
│   └── compact.rs         # 上下文压缩
├── config/
│   └── config.rs          # 配置系统
└── tools/
    ├── glob.rs            # 文件搜索
    └── grep.rs            # 内容搜索
```

### Phase 3: 安全与权限
```
新增：
├── permissions/
│   ├── rules.rs           # 权限规则引擎
│   ├── approval.rs        # 审批流程
│   └── deny_tracking.rs   # 拒绝记录
├── sandbox/
│   └── policy.rs          # 执行策略
└── hooks/
    ├── pre_tool.rs        # 工具执行前 hook
    └── post_tool.rs       # 工具执行后 hook
```

### Phase 4: 工具生态扩展
```
新增：
├── tools/
│   ├── edit.rs            # 精确替换编辑
│   ├── web_fetch.rs       # Web 获取
│   ├── web_search.rs      # Web 搜索
│   ├── lsp.rs             # LSP 集成
│   └── agent.rs           # Sub-agent 工具
├── mcp/
│   ├── client.rs          # MCP 客户端
│   └── registry.rs        # MCP 工具注册
└── tools/
    └── orchestrator.rs    # 工具并发调度
```

### Phase 5: 多 Agent 与记忆
```
新增：
├── agents/
│   ├── spawner.rs         # Agent 生成器
│   ├── registry.rs        # Agent 注册表
│   └── communication.rs   # Agent 间通信
├── memory/
│   ├── auto_memory.rs     # 自动记忆提取
│   ├── memory_file.rs     # 记忆文件管理
│   └── index.rs           # 记忆索引
└── session/
    ├── session.rs         # 会话管理
    ├── history.rs         # 历史持久化
    └── progress.rs        # 进度追踪
```

### Phase 6: UI 与产品化
```
新增：
├── tui/
│   ├── app.rs             # TUI 框架
│   ├── chat.rs            # 聊天界面
│   ├── permissions.rs     # 权限对话框
│   └── status.rs          # 状态栏
├── cli/
│   ├── commands.rs        # 斜杠命令
│   └── streaming.rs       # 流式输出
└── bridge/
    └── api.rs             # IDE 集成 API
```

## 技术选型速查表

| 决策点 | 推荐方案 | 理由 |
|-------|---------|------|
| **语言** | Rust 或 Go | 性能 + 类型安全 + 并发；TS 也可但运行时开销大 |
| **LLM SDK** | 直接 HTTP 调用 | SDK 版本更新太快，直接调用更可控 |
| **TUI 框架** | ratatui (Rust) / Bubble Tea (Go) / Ink (TS) | 各生态的最优选 |
| **数据库** | SQLite (WAL 模式) | 嵌入式、零配置、足够快 |
| **配置格式** | TOML | 人可读、层级清晰、注释友好 |
| **工具 Schema** | JSON Schema | 业界标准，所有 LLM API 支持 |
| **IPC** | JSON-RPC over stdio | 简单、跨平台、无依赖 |

## 关键决策备注

- **LLM SDK 直接 HTTP 调用**：9 个 Agent 中 Codex CLI 和 OpenCode 都选择了直接实现 HTTP 客户端而非使用官方 SDK。原因：SDK 的版本更新周期（每周）远快于 Agent 的发布周期（每月），频繁的 breaking changes 是维护噩梦。
- **SQLite WAL 模式**：OpenCode 选择 SQLite 做会话持久化（三表结构），Claude Code 选择 JSON 文件。SQLite 在需要查询历史会话时更有优势。
- **TOML > YAML > JSON**：Codex CLI 用 TOML 配置，理由是支持注释且不像 YAML 有缩进敏感问题。
