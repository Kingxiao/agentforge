# Packaging Recipes by Language

> Sources: Actual release configurations from Claude Code (TS), Codex CLI (Rust), OpenCode (Go), Aider (Python)

## TypeScript CLI Packaging

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

### esbuild Configuration Key Points

```typescript
// build.mjs
import { build } from "esbuild";

await build({
  entryPoints: ["src/cli.ts"],
  bundle: true,
  platform: "node",
  target: "node18",
  outfile: "dist/cli.js",
  // Critical: externalize dependencies that cannot be bundled
  external: [
    "fsevents",          // Native modules
    "cpu-features",      // Native modules
  ],
  banner: {
    js: "#!/usr/bin/env node",  // CLI entry point
  },
  minify: true,
  sourcemap: true,
});
```

### TypeScript SDK Packaging (Dual Format)

```typescript
// tsup.config.ts
import { defineConfig } from "tsup";

export default defineConfig({
  entry: ["src/index.ts"],
  format: ["cjs", "esm"],
  dts: true,              // Generate .d.ts
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

## Rust CLI Packaging

### Cargo.toml Release Configuration

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
strip = true        # Strip debug symbols
codegen-units = 1   # Maximum optimization (slower compile)
panic = "abort"     # Reduce binary size
```

### Cross-Compilation (cross-rs)

```toml
# Cross.toml
[target.x86_64-unknown-linux-musl]
image = "ghcr.io/cross-rs/x86_64-unknown-linux-musl:main"

[target.aarch64-unknown-linux-musl]
image = "ghcr.io/cross-rs/aarch64-unknown-linux-musl:main"
```

```bash
# Build statically linked binaries
cross build --release --target x86_64-unknown-linux-musl
cross build --release --target aarch64-unknown-linux-musl
cross build --release --target x86_64-apple-darwin
cross build --release --target aarch64-apple-darwin
```

### cargo-dist Auto-Release

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

### Docker Multi-Stage Build (Rust Service)

```dockerfile
# Stage 1: Builder
FROM rust:1.82-slim AS builder
WORKDIR /app
COPY Cargo.toml Cargo.lock ./
COPY src/ src/
RUN cargo build --release --target x86_64-unknown-linux-musl

# Stage 2: Runtime (minimal image)
FROM scratch
COPY --from=builder /app/target/x86_64-unknown-linux-musl/release/agent /agent
ENTRYPOINT ["/agent"]
```

---

## Go CLI Packaging

### goreleaser Configuration

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

### Go Module Release (SDK)

```bash
# Go SDK doesn't need "publishing" — just tag it
git tag v0.1.0
git push origin v0.1.0

# User installation
go get github.com/your-org/agent-sdk@v0.1.0
```

### Docker Scratch Image (Go Service)

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

## Python CLI Packaging

### pyproject.toml (Modern Standard)

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

### Publishing to PyPI

```bash
# Using uv (recommended)
uv build
uv publish

# Or using twine
python -m build
twine upload dist/*
```

### Docker Packaging (Python Service)

```dockerfile
FROM python:3.12-slim
WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install dependencies first (leverage cache layer)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy source code
COPY src/ src/
ENTRYPOINT ["uv", "run", "agent"]
```

### PyInstaller Single-File Distribution (Not Recommended — Special Cases Only)

```bash
# Generate single executable (size: 50-200MB)
pyinstaller --onefile --name agent src/agent_cli/main.py
```

**Why not recommended**: Large size, slow startup, requires separate builds per platform. Only use if users cannot install Python.

---

## GitHub Actions Release Template (Universal)

```yaml
name: Release

on:
  push:
    tags: ["v*"]

permissions:
  contents: write  # Create Release

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
          # Replace with your language's build command
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

## Version Automation

### Conventional Commits + Auto CHANGELOG

```bash
# git-cliff (Rust ecosystem, cross-language usable)
cargo install git-cliff

# Generate CHANGELOG
git cliff --output CHANGELOG.md

# Configuration file cliff.toml
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

### release-please (GitHub Action)

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
          release-type: node  # or rust, python, go, etc.
```

Automatically creates Release PR → on merge, auto-tags → triggers build and publish.
