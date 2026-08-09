---
name: agentforge-ship
disable-model-invocation: true
description: Internal AgentForge Phase 8 packaging guide. Load only when explicitly named or selected by the agentforge router; loading it never authorizes commit, push, release, deployment, or other external mutations.
triggers:
  - Agent release
  - Agent packaging
  - Agent deployment
  - ship agent
  - agent packaging
metadata:
  version: "3.0.0"
  last_updated: "2026-08-08"
  category: "agent-engineering"
---

# AgentForge Phase 8: Packaging & Release

> **Phase isolation:** This file is self-contained for its decision. References to other `/agentforge-*` skills are navigation only; do not load another phase in the same response unless the user explicitly requests a multi-phase comparison.

> Previous: `/agentforge-multiagent` | Next: `/agentforge-production` | Series entry: `/agentforge`
> Cloud deployment: `/cloud-deployment` | Rust deployment: `/deployment-rust` | Deployment verification: `/deploy-verifier`

## Core Concept

Agent built ≠ deliverable. Between "runs locally" and "user can use it" lies a chasm: packaging, distribution, version management, CI/CD.

**The Agent's release form determines the upper limit of user experience.** CLI tools and web services have completely different packaging strategies. Choosing the wrong form makes all subsequent work a waste.

## Decision 1: Release Form

```
Who is your Agent for?
│
├─ Developers, integrated into their toolchain
│  ├─ Needs local execution → CLI tool
│  ├─ Needs programmatic invocation → SDK library
│  └─ Needs IDE usage → IDE plugin
│
├─ Non-technical users
│  ├─ Needs interactive interface → Web service
│  └─ Needs continuous running → Background daemon
│
└─ Other systems/Agents
   └─ Needs API integration → HTTP API / gRPC service
```

### Form Comparison

| Form | Distribution Channel | User Barrier | Update Mechanism | Typical Examples |
|------|---------------------|--------------|------------------|-------------------|
| CLI Tool | npm/cargo/pip/go install | Medium | Manual upgrade by user | Claude Code, Codex CLI, Aider |
| SDK Library | Package manager | High (developers) | Dependency manager | Anthropic SDK, OpenAI SDK |
| Web Service | URL | Low | Server-side deployment | Claude.ai, ChatGPT |
| IDE Plugin | Plugin marketplace | Low-Medium | Auto-update | Cline, Continue |
| Background Daemon | System package/container | Medium | Package/container orchestration | OpenHands |
| HTTP API | Docs + SDK | High | Version-numbered routing | OpenAI API, Anthropic API |

## Decision 2: Language-Specific Packaging Strategy

### TypeScript/JavaScript Agent

```
Packaging decisions:
├─ CLI tool → esbuild single-file bundle → npm publish
├─ SDK library → tsup dual format (CJS + ESM) → npm publish
├─ Web service → Docker container → cloud platform deployment
└─ IDE plugin → vsce package (VS Code) / JetBrains plugin
```

**Key configurations**:
- `package.json` `bin` field (CLI) or `main`/`module`/`exports` fields (SDK)
- `tsconfig.json` strict mode + declaration file generation
- `.npmignore` or `files` whitelist (avoid publishing source/tests)

### Rust Agent

```
Packaging decisions:
├─ CLI tool → cargo build --release → single binary distribution
│  ├─ Cross-platform → cross-rs cross-compilation
│  └─ GitHub Release → cargo-dist / release-plz
├─ SDK library → cargo publish (crates.io)
└─ Service → Docker multi-stage build (builder + runtime)
```

**Rust's core advantage**: Single binary, no runtime dependencies. Codex CLI chose Rust precisely because distribution is simple.

**Key configurations**:
- `Cargo.toml` `[[bin]]` and `[profile.release]` (LTO, strip)
- Cross-compilation targets: `x86_64-unknown-linux-musl` (statically linked)

### Go Agent

```
Packaging decisions:
├─ CLI tool → go build → single binary
│  └─ Cross-platform → goreleaser (automatic multi-platform + changelog)
├─ SDK library → go module (no publishing needed, just tag)
└─ Service → Docker scratch image
```

**Go's core advantage**: Cross-compilation with zero configuration (`GOOS=linux GOARCH=amd64`). One reason OpenCode chose Go.

### Python Agent

```
Packaging decisions:
├─ CLI tool → uv/pip install → entry_points console_scripts
│  └─ Standalone distribution → PyInstaller / Nuitka (single file, but large)
├─ SDK library → uv publish / twine upload (PyPI)
└─ Service → Docker + uv pip install
```

**Python's challenge**: Dependency hell. Must lock dependency versions (`uv.lock` / `requirements.txt`). Aider's installation experience has consistently been a top user complaint.

**Key configurations**:
- `pyproject.toml` (modern standard, replaces setup.py)
- `[project.scripts]` defines CLI entry point
- Virtual environment isolation (never `sudo pip install`)

#### Python Agent Docker Image Best Practices

Python Agent Docker images face three unique challenges: **large image size, insecure API key injection, slow dependency installation**.

**Multi-stage build + uv (recommended)**:

```dockerfile
# Stage 1: Install dependencies (build layer only, not in final image)
FROM python:3.12-slim AS builder
RUN pip install uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
# --no-dev excludes dev dependencies; --frozen enforces lockfile (no auto-resolve)
RUN uv sync --no-dev --frozen

# Stage 2: Final runtime image (no build tools, runtime only)
FROM python:3.12-slim AS runtime
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY src/ ./src/
ENV PATH="/app/.venv/bin:$PATH"
# Run as non-root user (security best practice)
RUN useradd -m agent
USER agent
ENTRYPOINT ["python", "-m", "src.agent"]
```

**Image size selection**:
```
python:3.12          → ~900MB (includes docs, full pip toolchain — don't use)
python:3.12-slim     → ~100MB (recommended, good compatibility)
python:3.12-alpine   → ~50MB (extreme optimization, watch for C extension pitfalls)
```

**API Key Injection (security levels high to low)**:

```bash
# ✓ Method 1: Runtime environment variable (recommended — key not written to image layer)
docker run -e ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" agent:latest

# ✓ Method 2: Docker secrets (K8s/Swarm production)
docker run --secret id=api_key,env=ANTHROPIC_API_KEY agent:latest

# ✓ Method 3: .env file mount (local development)
docker run --env-file .env agent:latest

# ✗ Absolutely prohibited: ENV or ARG in Dockerfile写入 key
# ENV ANTHROPIC_API_KEY=sk-xxx ← baked into image layer, docker history visible
```

**Pre-release checks (prevent key leakage)**:
```bash
# Check all layers for sensitive variables
docker history --no-trunc agent:latest | grep -iE "key|secret|token|password"
# Check runtime environment
docker run --rm --entrypoint env agent:latest | grep -iE "key|secret"
```

Complete packaging configurations are inlined in the per-language sections above.

### Platform Bot Deployment (Slack / Discord / Telegram)

**Primary decision: Outgoing (Agent pushes) vs Incoming (Slack triggers)**

This is a more fundamental architectural fork than "HTTP vs Socket" — it directly affects integration approach:

```
Outgoing (Agent → Slack)
  Agent actively sends messages to Slack (notifications, reports, pushes)
  Implementation: Incoming Webhook URL or Web API chat.postMessage
  Use cases: Post-meeting summary推送, monitoring alert pushes
  Not needed: Bot Token read permissions, event listening

Incoming (Slack → Agent)
  User @mentions bot or sends commands in Slack, Agent responds
  Implementation: Slack Events API (Slack POSTs to your HTTPS endpoint)
  Use cases: Slack commands trigger Agent task execution
  Not needed: Webhook URL; needed: Bot Token + public HTTPS endpoint
```

**Common misconception**: Using Incoming Webhook for "need to respond to user commands" scenarios — Incoming Webhook is unidirectional (can only send, cannot receive), cannot be used for responding to user input. Responding to users = must use Events API.

| Scenario | Correct Solution |
|----------|-------------------|
| Scheduled push notifications | Incoming Webhook (simple, no Bot Token needed) |
| Respond to user commands | Events API + HTTP endpoint |
| Bidirectional dialogue | Events API + Web API (both read and write need Bot Token) |
| Notifications only (no interaction) | Incoming Webhook — don't over-engineer |

---

**Core decision: HTTP Mode vs Socket Mode**

```
Development/intranet (no public HTTPS)
    → Socket Mode (WebSocket long connection, Slack pushes messages proactively)
    → Advantage: No public port exposure needed
    → Trade-off: Requires a resident connection and reconnect handling; it can be production-appropriate when that operating model is intentional

Production (has public HTTPS endpoint)
    → HTTP Event API (Slack POSTs to your HTTPS endpoint)
    → Recommended: Stable, horizontally scalable, standard HTTP operations
    → Required: HTTPS (Slack doesn't accept HTTP)
```

**Platform freshness gate**: before release, verify current Slack authentication, event acknowledgement, rate limits, file-upload flow, scopes, and app-distribution rules in primary Slack documentation. Historical deadlines belong in migration notes, not permanent design guidance.

**Production deployment configuration (Slack Bolt TypeScript/Python)**:

```bash
# Environment variable configuration (must use env vars, hardcoding prohibited)
SLACK_BOT_TOKEN=xoxb-your-bot-token      # OAuth Bot Token
SLACK_SIGNING_SECRET=your-signing-secret  # Validates request origin
SLACK_APP_TOKEN=xapp-...                  # Socket Mode only (not needed for HTTP mode)
PORT=3000
```

```dockerfile
# Slack Bot Docker deployment
FROM node:20-slim AS runtime
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY package.json ./
RUN npm ci --only=production

# HTTP mode: listen for POST requests from Slack
ENV SLACK_SOCKET_MODE=false
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

**Slack App Manifest key configuration (HTTP mode)**:

```yaml
# manifest.yaml
settings:
  event_subscriptions:
    request_url: https://your-domain.com/slack/events  # HTTPS required
  socket_mode_enabled: false  # Disabled in production
features:
  bot_user:
    display_name: "Your Agent"
    always_online: true
```

**Local development → Production migration path**:

```
Local development: Socket Mode (no public URL needed)
    ↓ Near launch
Local + ngrok / Cloudflare Tunnel: test HTTP mode
    ngrok http 3000 → get temporary HTTPS URL → fill in Slack App config
    Cloudflare Tunnel: production-grade tunnel, free, low latency
    ↓ Launch
Production: HTTP mode +正式 HTTPS域名 (Nginx/Caddy reverse proxy + Let's Encrypt)
```

**Discord Bot differences (Python discord.py / TypeScript discord.js)**:

```
Discord has no HTTP Webhook mode — always uses WebSocket Gateway
→ Process must stay resident, must handle reconnection (discord.py has built-in exponential backoff)
→ Deployment: Docker + restart=always or systemd service
→ Multi-shard deployment (Bot must shard after 2500+ servers)
→ Intent permissions must be explicitly enabled in Discord developer portal (Message Content Intent disabled by default after 2022)
```

## Decision 3: CI/CD Strategy

### Minimum Viable CI Contract

A generated workflow is incomplete until it contains real build/test commands and reviewed immutable action references. At minimum:

1. Pull requests run lint/type checks, deterministic unit/integration tests, and the packaging build.
2. Release jobs depend on those checks, build only the operating systems actually supported, and verify artifact contents.
3. Third-party Actions are pinned to reviewed full commit SHAs; record the human-readable tag in a comment and use an authorized update process.
4. Publishing uses least-privilege short-lived credentials or platform trusted publishing where available.
5. The release job emits checksums/provenance as required and exercises installation plus a smoke test from the produced artifact.
6. Post-release verification and rollback ownership are explicit when deployment is in scope.

### CI/CD Tiering

| Tier | Trigger | Checks |
|------|---------|---------|
| L1: Fast checks | Every push | lint + typecheck + unit tests |
| L2: Full validation | PR merge | Integration tests + security scan + build |
| L3: Release | Tag push | Multi-platform build + publish to package manager + GitHub Release |
| L4: Post-deploy | Release complete | Canary checks + regression tests + monitoring alerts |

### Security Release Checklist

Must pass before release:
1. **Dependency audit** — `npm audit` / `cargo audit` / `pip audit`
2. **Leak scan** — Check for leaked API keys, passwords, etc. in package
3. **Signature verification** — npm provenance / disable `cargo publish --allow-dirty`
4. **SBOM generation** — Software Bill of Materials for downstream consumer auditing

## Decision 4: Version Management

### SemVer Semantic Versioning

```
MAJOR.MINOR.PATCH
  │      │      └─ Backward-compatible bug fixes
  │      └─ Backward-compatible feature additions
  └─ Backward-INCOMPATIBLE API changes
```

### CHANGELOG Strategy

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

**Automation solutions**:
- Conventional Commits → Auto-generate CHANGELOG
- `git cliff` (Rust) / `standard-version` (JS) / `release-please` (GitHub Action)

### Pre-release Versions

```
0.1.0-alpha.1  → Internal testing
0.1.0-beta.1   → External testing
0.1.0-rc.1     → Release candidate
0.1.0          → Official release
```

**Agent-specific version considerations**:
- LLM Provider API changes may break Agent behavior without code changes → annotate in CHANGELOG
- System prompt changes = behavior changes → treat as MINOR or MAJOR bump
- Tool definition changes → MAJOR bump if affects user calling patterns

## Release Form × Language Selection Matrix

| | TypeScript | Rust | Go | Python |
|---|---|---|---|---|
| **CLI** | esbuild + npm | cargo-dist | goreleaser | uv + entry_points |
| **SDK** | tsup + npm | cargo publish | go tag | uv publish |
| **Web** | Docker + Node | Docker + musl | Docker + scratch | Docker + uv |
| **IDE** | vsce | N/A | N/A | N/A |

## Historical Snapshot (April 2026; re-verify before use)

1. **CLI Agent becoming the dominant distribution form** — Claude Code, Codex CLI, OpenCode and other leading Agents all choose CLI as primary distribution. npm/cargo install provides better installation experience than Docker/Web deployment. CLI-first is becoming the de facto standard for Agent distribution.
2. **Single-binary distribution trend accelerating** — Rust (cargo-dist) and Go (goreleaser) zero-dependency single-binary distribution is replacing Python/Node dependency chain hell. Aider's installation complaint rate is 10x+ vs Claude Code's. Python Agent's distribution disadvantage is becoming increasingly apparent.
3. **Agent version management facing new challenges** — System prompt changes cause behavior changes without code changes. LLM Provider API changes cause feature regression despite passing local tests. Traditional SemVer cannot fully cover Agent behavior changes. Supplementary behavior version annotation mechanisms needed.
4. **Supply chain security becoming mandatory release gate** — npm provenance, `cargo publish --locked`, SBOM generation shifting from "optional" to "required." GitHub's Artifact Attestation and Sigstore signing becoming the trust foundation for open-source Agents.
5. **Remote Agent execution rising** — Anthropic Cloud Code, GitHub Codex remote sandbox execution models are changing the "packaging distribution" assumption. Some Agents may no longer need local installation — executing remotely via API.

## Known Pitfalls

1. **Python dependency hell** — Python Agent distributed via pip install fails frequently due to user environment Python version, system dependencies, and virtual environment configuration issues. Solution: Prefer uv for dependency management and generate lockfile. For severe cases, consider PyInstaller/Nuitka for single-file packaging, or distribute directly via Docker.
2. **Cross-platform build omissions** — Tested and released only on Linux; macOS/Windows users encounter errors immediately after install (path separators, shell differences, missing system libraries). Solution: CI matrix must cover three platforms — at minimum ubuntu-latest + macos-latest + windows-latest.
3. **Secrets/config leaked into distribution package** — .env files, test API keys, internal configurations accidentally packaged into npm/PyPI release. Solution: Must have leak scan step before release. Use whitelist patterns (.npmignore/MANIFEST.in) rather than blacklist.
4. **CHANGELOG diverges from actual changes** — Manually maintained CHANGELOG misses important changes or descriptions don't match reality. Users hit by breaking changes after upgrading. Solution: Mandate Conventional Commits + auto-generation tools (git cliff / release-please). Validate commit format on PR merge.

## Further Reading

| Topic | Resource |
|-------|----------|
| Packaging configurations (per language) | See "Per-Language Packaging Strategy" section above |
| Phase 5: Security audit & supply chain | `/agentforge-security` |
| Phase 6: Harness & CI validation gate | `/agentforge-harness` |
| Supply chain security orchestration | `/supply-chain-guard` |
| npm package supply chain scan | `/supply-chain-scan-npm` |
| cargo package supply chain scan | `/supply-chain-scan-cargo` |
| Docker image supply chain scan | `/supply-chain-scan-docker` |
| Post-deploy verification | `/deploy-verifier` |
| Rust service deployment | `/deployment-rust` |

## Release Checklist

- [ ] Release form determined (CLI / SDK / Web / IDE / API)
- [ ] Packaging strategy selected (matches language and form)
- [ ] CI/CD covers at least L1-L3 (fast checks + full validation + release)
- [ ] Version management uses SemVer
- [ ] CHANGELOG has auto-generation solution
- [ ] Pre-release security checks (dependency audit + leak scan)
- [ ] Cross-platform build configured (if needed)
- [ ] Post-release verification mechanism (canary / smoke test)

## Reverse Audit (Diagnose Mode)

> Invoked by `/agentforge-diagnose` — D8 delivery dimension static audit of existing code.

| # | Check Item | How to Check | Pass Criteria |
|---|-----------|-------------|--------------|
| SH1 | Deployment config complete | `ls Dockerfile docker-compose.yml k8s/ 2>/dev/null` | Deployable deployment solution exists |
| SH2 | Environment variable injection | `ls .env.example 2>/dev/null && cat .env.example` | Has `.env.example`, all values are `your_xxx_here` placeholders |
| SH3 | Health checks | `grep -rn "/health\|healthcheck\|health_check" src/` | Health check endpoint or probe exists |
| SH4 | Rollback strategy | `git tag \| head -5` — check for version tags; check README | Has version tags + rollback docs/scripts |
| SH5 | New person can reproduce | Clone→configure→start full flow using only README | No hidden dependencies, README can guide independently |

**High-probability problems**: No `.env.example` (P0 — new contributors can't configure), no health checks (P1 — deployment is a black box), README lacks startup steps (P1 — not reproducible)

## Next Steps

Release process ready → **`/agentforge-production`** (Phase 9) when the artifact is operated as a service; otherwise proceed to acceptance with `/agentforge-benchmark` or stop.
Need cloud deployment details → **`/cloud-deployment`**
Need post-deploy verification → **`/deploy-verifier`**
