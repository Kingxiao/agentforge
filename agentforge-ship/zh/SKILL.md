---
name: agentforge-ship
description: AgentForge Phase 8 - Agent 打包与发布。发布形态选型 + 按语言打包配方 + CI/CD + 版本管理。当用户说「Agent 发布」「Agent 打包」「Agent 部署」「ship agent」时触发。
triggers:
  - Agent 发布
  - Agent 打包
  - Agent 部署
  - ship agent
  - agent packaging
metadata:
  version: "2.0.0"
  last_updated: "2026-04-06"
  category: "agent-engineering"
---

# AgentForge Phase 8: 打包与发布

> 上一步：`/agentforge-multiagent` | 下一步：`/agentforge-autoplan` | 系列入口：`/agentforge`
> 云部署：`/cloud-deployment` | Rust 部署：`/deployment-rust` | 部署验证：`/deploy-verifier`

## 核心认知

Agent 构建完成 ≠ 可交付。从"本地能跑"到"用户能用"之间有一条鸿沟：打包、分发、版本管理、CI/CD。

**Agent 的发布形态决定了用户体验的上限。** CLI 工具和 Web 服务的打包策略完全不同。选错形态，后面所有工作都是浪费。

## 第一个决策：发布形态

```
你的 Agent 给谁用？
│
├─ 开发者，集成到他们的工具链
│  ├─ 需要本地执行 → CLI 工具
│  ├─ 需要编程调用 → SDK 库
│  └─ 需要 IDE 内使用 → IDE 插件
│
├─ 非技术用户
│  ├─ 需要交互界面 → Web 服务
│  └─ 需要持续运行 → 后台 Daemon
│
└─ 其他系统/Agent
   └─ 需要 API 集成 → HTTP API / gRPC 服务
```

### 形态对比

| 形态 | 分发渠道 | 用户门槛 | 更新机制 | 典型案例 |
|------|---------|---------|---------|---------|
| CLI 工具 | npm/cargo/pip/go install | 中 | 用户手动升级 | Claude Code, Codex CLI, Aider |
| SDK 库 | 包管理器 | 高（开发者） | 依赖管理器 | Anthropic SDK, OpenAI SDK |
| Web 服务 | URL | 低 | 服务端部署 | Claude.ai, ChatGPT |
| IDE 插件 | 插件市场 | 低-中 | 自动更新 | Cline, Continue |
| 后台 Daemon | 系统包/容器 | 中 | 包管理/容器编排 | OpenHands |
| HTTP API | 文档 + SDK | 高 | 版本号路由 | OpenAI API, Anthropic API |

## 第二个决策：按语言选择打包策略

### TypeScript/JavaScript Agent

```
打包决策：
├─ CLI 工具 → esbuild 单文件 bundle → npm publish
├─ SDK 库 → tsup 双格式 (CJS + ESM) → npm publish
├─ Web 服务 → Docker 容器 → 云平台部署
└─ IDE 插件 → vsce package (VS Code) / JetBrains plugin
```

**关键配置**：
- `package.json` 的 `bin` 字段（CLI）或 `main`/`module`/`exports` 字段（SDK）
- `tsconfig.json` 严格模式 + 声明文件生成
- `.npmignore` 或 `files` 白名单（避免发布源码/测试）

### Rust Agent

```
打包决策：
├─ CLI 工具 → cargo build --release → 单二进制分发
│  ├─ 跨平台 → cross-rs 交叉编译
│  └─ GitHub Release → cargo-dist / release-plz
├─ SDK 库 → cargo publish (crates.io)
└─ 服务 → Docker 多阶段构建（builder + runtime）
```

**Rust 的核心优势**：单二进制、无运行时依赖。Codex CLI 选 Rust 正是因为分发简单。

**关键配置**：
- `Cargo.toml` 的 `[[bin]]` 和 `[profile.release]`（LTO、strip）
- 交叉编译目标：`x86_64-unknown-linux-musl`（静态链接）

### Go Agent

```
打包决策：
├─ CLI 工具 → go build → 单二进制
│  └─ 跨平台 → goreleaser（自动多平台 + 变更日志）
├─ SDK 库 → go module (无需发布，tag 即可)
└─ 服务 → Docker scratch 镜像
```

**Go 的核心优势**：交叉编译零配置（`GOOS=linux GOARCH=amd64`）。OpenCode 选 Go 的原因之一。

### Python Agent

```
打包决策：
├─ CLI 工具 → uv/pip install → entry_points console_scripts
│  └─ 独立分发 → PyInstaller / Nuitka（单文件，但体积大）
├─ SDK 库 → uv publish / twine upload (PyPI)
└─ 服务 → Docker + uv pip install
```

**Python 的挑战**：依赖地狱。必须锁定依赖版本（`uv.lock` / `requirements.txt`）。Aider 的安装体验一直是用户投诉的重灾区。

**关键配置**：
- `pyproject.toml`（现代标准，替代 setup.py）
- `[project.scripts]` 定义 CLI 入口
- 虚拟环境隔离（永远不 `sudo pip install`）

#### Python Agent Docker 镜像最佳实践

Python Agent 的 Docker 镜像有三个特有挑战：**镜像体积大、API Key 注入不安全、依赖安装慢**。

**多阶段构建 + uv（推荐）**：

```dockerfile
# Stage 1: 安装依赖（仅构建层，不进入最终镜像）
FROM python:3.12-slim AS builder
RUN pip install uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
# --no-dev 排除开发依赖；--frozen 强制锁文件（禁止自动 resolve）
RUN uv sync --no-dev --frozen

# Stage 2: 最终运行镜像（不含构建工具，只含运行时）
FROM python:3.12-slim AS runtime
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY src/ ./src/
ENV PATH="/app/.venv/bin:$PATH"
# 非 root 用户运行（安全最佳实践）
RUN useradd -m agent
USER agent
ENTRYPOINT ["python", "-m", "src.agent"]
```

**镜像体积选型**：
```
python:3.12          → ~900MB（含文档、pip 完整工具链，不要用）
python:3.12-slim     → ~100MB（推荐，兼容性好）
python:3.12-alpine   → ~50MB（极限优化，C 扩展依赖有坑，谨慎用）
```

**API Key 注入（安全等级从高到低）**：

```bash
# ✓ 方式 1：运行时环境变量（推荐，key 不写入镜像 layer）
docker run -e ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" agent:latest

# ✓ 方式 2：Docker secrets（K8s/Swarm 生产环境）
docker run --secret id=api_key,env=ANTHROPIC_API_KEY agent:latest

# ✓ 方式 3：.env 文件挂载（本地开发）
docker run --env-file .env agent:latest

# ✗ 绝对禁止：Dockerfile 内 ENV 或 ARG 写入 key
# ENV ANTHROPIC_API_KEY=sk-xxx  ← 固化进镜像 layer，docker history 可见
```

**发布前必查（防 key 泄漏）**：
```bash
# 检查所有 layer 是否含敏感变量
docker history --no-trunc agent:latest | grep -iE "key|secret|token|password"
# 检查运行时环境
docker run --rm --entrypoint env agent:latest | grep -iE "key|secret"
```

完整打包配置已内联在上方各语言章节中。

### 平台 Bot 部署（Slack / Discord / Telegram）

**首要决策：Outgoing（Agent 推送）vs Incoming（Slack 触发）**

这是比"HTTP vs Socket"更基础的架构分叉，直接影响集成方式：

```
Outgoing（Agent → Slack）
  Agent 主动向 Slack 发消息（通知、报告、推送）
  实现：Incoming Webhook URL 或 Web API chat.postMessage
  使用场景：会议结束后推送摘要、监控告警推送
  不需要：Bot Token 的 read 权限，不需要监听事件

Incoming（Slack → Agent）
  用户在 Slack 中 @ 机器人或发指令，Agent 响应
  实现：Slack Events API（Slack 向你的 HTTPS endpoint POST）
  使用场景：Slack 命令触发 Agent 执行任务
  不需要：Webhook URL，需要：Bot Token + 公网 HTTPS 端点
```

**常见误区**：把"需要响应用户指令"的场景用 Incoming Webhook 实现——Incoming Webhook 是单向的（只能发消息，无法接收），不能用于响应用户输入。响应用户 = 必须走 Events API。

| 场景 | 正确方案 |
|------|---------|
| 定时推送通知 | Incoming Webhook（简单，无需 Bot Token）|
| 响应用户指令 | Events API + HTTP Endpoint |
| 双向对话 | Events API + Web API（读写均需 Bot Token）|
| 纯通知（无交互）| Incoming Webhook 即可，不要过度设计 |

---

**核心决策：HTTP 模式 vs Socket 模式**

```
开发/内网环境（无公网 HTTPS）
    → Socket Mode（WebSocket 长连接，Slack 主动推消息）
    → 优点：无需暴露公网端口
    → 缺点：连接不稳定，不适合生产

生产环境（有公网 HTTPS 端点）
    → HTTP Event API（Slack 向你的 HTTPS endpoint 发送 POST 请求）
    → 推荐：稳定、可水平扩展、标准 HTTP 运维
    → 必须：HTTPS（Slack 不接受 HTTP）
```

**2025 Slack API 重大变更（发布前必查）**：

| 变更 | 截止日期 | 影响 |
|------|---------|------|
| Legacy Bot Token 弃用 | 2025-03-31 | 所有 `xoxb-` 旧格式 token 失效，必须迁移到 OAuth App |
| `files.upload` API 弃用 | 2025-11-12 | 改用 `files.getUploadURLExternal` + `files.completeUploadExternal` |
| 非 Marketplace App 限速收紧 | 2025 全年 | 小 App 并发请求限制降低，批量发消息需加 retry 逻辑 |

**生产部署配置（Slack Bolt TypeScript/Python）**：

```bash
# 环境变量配置（必须通过环境变量，禁止硬编码）
SLACK_BOT_TOKEN=xoxb-your-bot-token      # OAuth Bot Token
SLACK_SIGNING_SECRET=your-signing-secret  # 验证请求来源
SLACK_APP_TOKEN=xapp-...                  # Socket Mode 专用（HTTP 模式不需要）
PORT=3000
```

```dockerfile
# Slack Bot Docker 部署
FROM node:20-slim AS runtime
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY package.json ./
RUN npm ci --only=production

# HTTP 模式：监听 Slack 发来的 POST 请求
ENV SLACK_SOCKET_MODE=false
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

**Slack App Manifest 关键配置（HTTP 模式）**：

```yaml
# manifest.yaml
settings:
  event_subscriptions:
    request_url: https://your-domain.com/slack/events  # 必须 HTTPS
  socket_mode_enabled: false  # 生产环境关闭 Socket Mode
features:
  bot_user:
    display_name: "Your Agent"
    always_online: true
```

**本地开发 → 生产迁移路径**：

```
本地开发：Socket Mode（无需公网）
    ↓ 接近上线时
本地 + ngrok / Cloudflare Tunnel：测试 HTTP 模式
    ngrok http 3000 → 获得临时 HTTPS URL → 填入 Slack App 配置
    Cloudflare Tunnel：生产级隧道，免费，延迟低
    ↓ 上线
生产：HTTP 模式 + 正式 HTTPS 域名（Nginx/Caddy 反代 + Let's Encrypt）
```

**Discord Bot 差异（Python discord.py / TypeScript discord.js）**：

```
Discord 无 HTTP Webhook 模式，始终使用 WebSocket Gateway
→ 进程常驻，必须处理断线重连（discord.py 内置指数退避）
→ 部署：Docker + restart=always 或 systemd service
→ 多 shard 部署（Bot 超 2500 服务器后必须 sharding）
→ Intent 权限必须在 Discord 开发者后台显式开启（Message Content Intent 2022 后默认关）
```

## 第三个决策：CI/CD 策略

### 最小可用 CI（GitHub Actions）

```yaml
# .github/workflows/release.yml
name: Release
on:
  push:
    tags: ["v*"]

jobs:
  build:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - name: Build
        run: # 语言特定的构建命令
      - name: Upload artifacts
        uses: actions/upload-artifact@v4

  publish:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Download artifacts
        uses: actions/download-artifact@v4
      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          files: artifacts/*
```

### CI/CD 分层

| 层 | 触发时机 | 检查内容 |
|----|---------|---------|
| L1: 快速检查 | 每次 push | lint + typecheck + 单元测试 |
| L2: 完整验证 | PR 合并 | 集成测试 + 安全扫描 + 构建 |
| L3: 发布 | tag 推送 | 多平台构建 + 发布到包管理器 + GitHub Release |
| L4: 部署后 | 发布完成 | 金丝雀检查 + 回归测试 + 监控告警 |

### 安全发布检查

发布前必须通过：
1. **依赖审计** — `npm audit` / `cargo audit` / `pip audit`
2. **泄漏扫描** — 检查是否有 API key、密码等泄漏到包中
3. **签名验证** — npm provenance / cargo publish --allow-dirty 禁用
4. **SBOM 生成** — 软件物料清单，供下游用户审计

## 第四个决策：版本管理

### SemVer 语义化版本

```
MAJOR.MINOR.PATCH
  │      │      └─ 向后兼容的 bug 修复
  │      └─ 向后兼容的功能新增
  └─ 不兼容的 API 变更
```

### CHANGELOG 策略

```markdown
# Changelog

## [0.3.0] - 2026-04-06
### Added
- Multi-agent coordination support
### Changed
- Tool interface now requires `description` field
### Fixed
- Context compaction memory leak

## [0.2.0] - 2026-03-15
...
```

**自动化方案**：
- Conventional Commits → 自动生成 CHANGELOG
- `git cliff`（Rust）/ `standard-version`（JS）/ `release-please`（GitHub Action）

### 预发布版本

```
0.1.0-alpha.1  → 内部测试
0.1.0-beta.1   → 外部测试
0.1.0-rc.1     → 发布候选
0.1.0          → 正式发布
```

**Agent 特有的版本考量**：
- LLM Provider API 变更可能破坏 Agent 行为但不改变代码 → 在 CHANGELOG 中标注
- 系统提示词变更 = 行为变更 → 视为 MINOR 或 MAJOR bump
- 工具定义变更 → 如果影响用户调用方式，MAJOR bump

## 发布形态 × 语言 选型矩阵

| | TypeScript | Rust | Go | Python |
|---|---|---|---|---|
| **CLI** | esbuild + npm | cargo-dist | goreleaser | uv + entry_points |
| **SDK** | tsup + npm | cargo publish | go tag | uv publish |
| **Web** | Docker + Node | Docker + musl | Docker + scratch | Docker + uv |
| **IDE** | vsce | N/A | N/A | N/A |

## 当前状态 (2026年4月)

1. **CLI Agent 成为主流分发形态** — Claude Code、Codex CLI、OpenCode 等头部 Agent 全部选择 CLI 作为主分发形态，npm/cargo install 的安装体验优于 Docker/Web 部署。CLI-first 正在成为 Agent 分发的事实标准。
2. **单二进制分发趋势加速** — Rust (cargo-dist) 和 Go (goreleaser) 的零依赖单二进制分发正在取代 Python/Node 的依赖链地狱。Aider 的安装投诉率是 Claude Code 的 10x+，Python Agent 的分发劣势越来越明显。
3. **Agent 版本管理面临新挑战** — 系统提示词变更导致行为变化但代码不变、LLM Provider API 变更导致功能退化但本地测试通过。传统 SemVer 无法完全覆盖 Agent 的行为变更，需要补充行为版本标注机制。
4. **供应链安全成为发布门禁标配** — npm provenance、cargo publish --locked、SBOM 生成从"可选"变为"必需"。GitHub 的 Artifact Attestation 和 Sigstore 签名正在成为开源 Agent 的信任基线。
5. **远程 Agent 执行兴起** — Anthropic Cloud Code、GitHub Codex 的远程沙箱执行模式正在改变"打包分发"的假设。部分 Agent 可能不再需要本地安装，而是通过 API 远程执行。

## Known Pitfalls

1. **Python 依赖地狱** — Python Agent 用 pip install 分发时，用户环境的 Python 版本、系统依赖、虚拟环境配置导致大量安装失败。解决方案：优先用 uv 管理依赖并生成 lockfile，严重场景考虑用 PyInstaller/Nuitka 打单文件，或直接用 Docker 分发。
2. **跨平台构建遗漏** — 只在 Linux 上测试就发布，macOS/Windows 用户安装后立刻报错（路径分隔符、shell 差异、缺失系统库）。解决方案：CI 矩阵必须覆盖三平台，至少包含 ubuntu-latest + macos-latest + windows-latest。
3. **密钥/配置泄漏到发布包** — .env 文件、测试用的 API key、内部配置被意外打包到 npm/PyPI 发布包中。解决方案：发布前必须有泄漏扫描步骤，.npmignore/MANIFEST.in 使用白名单模式而非黑名单模式。
4. **CHANGELOG 与实际变更脱节** — 手动维护 CHANGELOG 导致遗漏重要变更或描述与实际不符，用户升级后被 breaking change 打盲。解决方案：强制使用 Conventional Commits + 自动生成工具（git cliff / release-please），PR 合并时校验 commit 格式。

## 延伸阅读

| 主题 | 资源 |
|------|------|
| 打包配置（各语言） | 见上方"按语言选择打包策略"章节 |
| Phase 5: 安全审计与供应链 | `/agentforge-security` |
| Phase 6: Harness 与 CI 验证门禁 | `/agentforge-harness` |
| 供应链安全编排 | `/supply-chain-guard` |
| npm 包供应链扫描 | `/supply-chain-scan-npm` |
| cargo 包供应链扫描 | `/supply-chain-scan-cargo` |
| Docker 镜像供应链扫描 | `/supply-chain-scan-docker` |
| 部署后验证 | `/deploy-verifier` |
| Rust 服务部署 | `/deployment-rust` |

## 发布检查清单

- [ ] 确定了发布形态（CLI / SDK / Web / IDE / API）
- [ ] 选定了打包策略（匹配语言和形态）
- [ ] CI/CD 至少覆盖 L1-L3（快速检查 + 完整验证 + 发布）
- [ ] 版本管理使用 SemVer
- [ ] CHANGELOG 有自动化生成方案
- [ ] 发布前有安全检查（依赖审计 + 泄漏扫描）
- [ ] 跨平台构建已配置（如需要）
- [ ] 发布后有验证机制（金丝雀 / smoke test）

## 逆向审计（Diagnose Mode）

> 由 `/agentforge-diagnose` 调用——对已有代码进行 D8 交付维度静态审计。

| # | 检查项 | 检查方式 | 通过标准 |
|---|--------|---------|---------|
| SH1 | 部署配置完整 | `ls Dockerfile docker-compose.yml k8s/ 2>/dev/null` | 存在可执行的部署方案 |
| SH2 | 环境变量注入 | `ls .env.example 2>/dev/null && cat .env.example` | 有 `.env.example`，值全为 `your_xxx_here` 占位符 |
| SH3 | 健康检查 | `grep -rn "/health\|healthcheck\|health_check" src/` | 存在 health check endpoint 或 probe |
| SH4 | 回滚策略 | `git tag \| head -5`，看是否有版本 tag；查 README | 有版本 tag + 回滚文档/脚本 |
| SH5 | 新人可复现 | 仅凭 README 模拟 clone→配置→启动全流程 | 无隐性依赖，README 可独立引导完成部署 |

**高概率问题**：无 `.env.example`（P0 新人无法配置）、无健康检查（P1 部署黑盒）、README 缺少启动步骤（P1 不可复现）

## 下一步

发布流程就绪后 → **`/agentforge-autoplan`**（Phase 9：自动编排全流程）
需要云部署细节 → **`/cloud-deployment`**
需要部署后验证 → **`/deploy-verifier`**
