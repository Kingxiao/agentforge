# 各语言打包配方

> 来源：Claude Code (TS)、Codex CLI (Rust)、OpenCode (Go)、Aider (Python) 的实际发布配置

## TypeScript CLI 打包

### package.json

```json
{
  "name": "@your-org/agent-cli",
  "version": "0.1.0",
  "bin": {
    "agent": "./dist/cli.js"
  },
  "files": ["dist/", "README.md", "LICENSE"],
  "engines": {
    "node": ">=18"
  },
  "scripts": {
    "build": "esbuild src/cli.ts --bundle --platform=node --target=node18 --outfile=dist/cli.js",
    "prepublishOnly": "npm run build && npm test"
  }
}
```

### esbuild 配置要点

```typescript
// build.mjs
import { build } from "esbuild";

await build({
  entryPoints: ["src/cli.ts"],
  bundle: true,
  platform: "node",
  target: "node18",
  outfile: "dist/cli.js",
  // 关键：外部化不能 bundle 的依赖
  external: [
    "fsevents",          // 原生模块
    "cpu-features",      // 原生模块
  ],
  banner: {
    js: "#!/usr/bin/env node",  // CLI 入口
  },
  minify: true,
  sourcemap: true,
});
```

### TypeScript SDK 打包（双格式）

```typescript
// tsup.config.ts
import { defineConfig } from "tsup";

export default defineConfig({
  entry: ["src/index.ts"],
  format: ["cjs", "esm"],
  dts: true,              // 生成 .d.ts
  splitting: false,
  sourcemap: true,
  clean: true,
});
```

```json
// package.json exports
{
  "exports": {
    ".": {
      "import": "./dist/index.mjs",
      "require": "./dist/index.cjs",
      "types": "./dist/index.d.ts"
    }
  }
}
```

---

## Rust CLI 打包

### Cargo.toml 发布配置

```toml
[package]
name = "agent-cli"
version = "0.1.0"
edition = "2021"
license = "MIT"
description = "An AI coding agent"
repository = "https://github.com/your-org/agent-cli"

[[bin]]
name = "agent"
path = "src/main.rs"

[profile.release]
lto = true          # Link-Time Optimization
strip = true        # 去除调试符号
codegen-units = 1   # 最大优化（牺牲编译速度）
panic = "abort"     # 减小二进制体积
```

### 交叉编译（cross-rs）

```toml
# Cross.toml
[target.x86_64-unknown-linux-musl]
image = "ghcr.io/cross-rs/x86_64-unknown-linux-musl:main"

[target.aarch64-unknown-linux-musl]
image = "ghcr.io/cross-rs/aarch64-unknown-linux-musl:main"
```

```bash
# 构建静态链接二进制
cross build --release --target x86_64-unknown-linux-musl
cross build --release --target aarch64-unknown-linux-musl
cross build --release --target x86_64-apple-darwin
cross build --release --target aarch64-apple-darwin
```

### cargo-dist 自动发布

```toml
# Cargo.toml
[workspace.metadata.dist]
cargo-dist-version = "0.27.0"
ci = "github"
installers = ["shell", "powershell", "homebrew"]
targets = [
  "x86_64-unknown-linux-gnu",
  "aarch64-unknown-linux-gnu",
  "x86_64-apple-darwin",
  "aarch64-apple-darwin",
  "x86_64-pc-windows-msvc",
]
```

### Docker 多阶段构建（Rust 服务）

```dockerfile
# Stage 1: Builder
FROM rust:1.82-slim AS builder
WORKDIR /app
COPY Cargo.toml Cargo.lock ./
COPY src/ src/
RUN cargo build --release --target x86_64-unknown-linux-musl

# Stage 2: Runtime（最小镜像）
FROM scratch
COPY --from=builder /app/target/x86_64-unknown-linux-musl/release/agent /agent
ENTRYPOINT ["/agent"]
```

---

## Go CLI 打包

### goreleaser 配置

```yaml
# .goreleaser.yml
version: 2
builds:
  - env:
      - CGO_ENABLED=0
    goos:
      - linux
      - darwin
      - windows
    goarch:
      - amd64
      - arm64
    ldflags:
      - -s -w
      - -X main.version={{.Version}}
      - -X main.commit={{.ShortCommit}}

archives:
  - format: tar.gz
    name_template: "{{ .ProjectName }}_{{ .Os }}_{{ .Arch }}"
    format_overrides:
      - goos: windows
        format: zip

brews:
  - repository:
      owner: your-org
      name: homebrew-tap
    homepage: "https://github.com/your-org/agent"
    description: "An AI coding agent"

changelog:
  sort: asc
  filters:
    exclude:
      - "^docs:"
      - "^test:"
```

### Go module 发布（SDK）

```bash
# Go SDK 不需要"发布"，只需打 tag
git tag v0.1.0
git push origin v0.1.0

# 用户安装
go get github.com/your-org/agent-sdk@v0.1.0
```

### Docker scratch 镜像（Go 服务）

```dockerfile
FROM golang:1.23-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -ldflags="-s -w" -o /agent ./cmd/agent

FROM scratch
COPY --from=builder /agent /agent
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
ENTRYPOINT ["/agent"]
```

---

## Python CLI 打包

### pyproject.toml（现代标准）

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "agent-cli"
version = "0.1.0"
description = "An AI coding agent"
requires-python = ">=3.10"
license = "MIT"
dependencies = [
    "anthropic>=0.40.0",
    "click>=8.0",
    "rich>=13.0",
]

[project.scripts]
agent = "agent_cli.main:cli"

[project.optional-dependencies]
dev = ["pytest", "ruff", "mypy"]
```

### 发布到 PyPI

```bash
# 使用 uv（推荐）
uv build
uv publish

# 或使用 twine
python -m build
twine upload dist/*
```

### Docker 打包（Python 服务）

```dockerfile
FROM python:3.12-slim
WORKDIR /app

# 安装 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 先安装依赖（利用缓存层）
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# 复制源码
COPY src/ src/
ENTRYPOINT ["uv", "run", "agent"]
```

### PyInstaller 单文件分发（非推荐，仅特殊场景）

```bash
# 生成单个可执行文件（体积 50-200MB）
pyinstaller --onefile --name agent src/agent_cli/main.py
```

**不推荐原因**：体积大、启动慢、跨平台需分别构建。除非用户环境无法安装 Python。

---

## GitHub Actions 发布模板（通用）

```yaml
name: Release

on:
  push:
    tags: ["v*"]

permissions:
  contents: write  # 创建 Release

jobs:
  build:
    strategy:
      matrix:
        include:
          - os: ubuntu-latest
            target: x86_64-unknown-linux-musl
          - os: macos-latest
            target: aarch64-apple-darwin
          - os: windows-latest
            target: x86_64-pc-windows-msvc
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      
      - name: Build
        run: |
          # 替换为你的语言的构建命令
          echo "Build for ${{ matrix.target }}"
      
      - uses: actions/upload-artifact@v4
        with:
          name: binary-${{ matrix.target }}
          path: target/release/agent*

  release:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v4
      
      - name: Create Release
        uses: softprops/action-gh-release@v2
        with:
          generate_release_notes: true
          files: |
            binary-*/agent*
```

---

## 版本自动化

### Conventional Commits + 自动 CHANGELOG

```bash
# git-cliff（Rust 生态，跨语言可用）
cargo install git-cliff

# 生成 CHANGELOG
git cliff --output CHANGELOG.md

# 配置文件 cliff.toml
[changelog]
header = "# Changelog\n"
body = """
{% for group, commits in commits | group_by(attribute="group") %}
### {{ group | upper_first }}
{% for commit in commits %}
- {{ commit.message | upper_first }}
{% endfor %}
{% endfor %}
"""

[git]
conventional_commits = true
commit_parsers = [
    { message = "^feat", group = "Added" },
    { message = "^fix", group = "Fixed" },
    { message = "^refactor", group = "Changed" },
    { message = "^doc", group = "Documentation" },
]
```

### release-please（GitHub Action）

```yaml
# .github/workflows/release-please.yml
name: release-please
on:
  push:
    branches: [main]

jobs:
  release-please:
    runs-on: ubuntu-latest
    steps:
      - uses: googleapis/release-please-action@v4
        with:
          release-type: node  # 或 rust, python, go 等
```

自动创建 Release PR → 合并后自动打 tag → 触发构建和发布。
