# Supply Chain Security: AI Agent-Specific Threats

Traditional supply chain attacks (npm/PyPI package poisoning) have evolved into new variants targeting the AI Agent ecosystem:

| Threat Type | Example | Agent-Specific Risk |
|---------|------|--------------|
| LLM dependency package poisoning | LiteLLM (2026-03) PyPI implanted with credential theft + K8s lateral movement backdoor; 3.4M downloads/day | Agent typically runs with high privileges; poisoned package = direct RCE |
| Base package compromise | Axios npm (2026-03) North Korean APT implant RAT; 100M downloads/week | Agent's LLM client libraries mostly depend on axios |
| Skill-Inject / ToolTweak | Attackers inject malicious instructions into public Skill/Tool repositories; Agent defaults to trusting Skills for execution | Agent holds shell/filesystem permissions + defaults to trusting skills → direct RCE |

**Why AI Agent supply chain risk is higher**: Agents run with system-level privileges (file I/O, shell, network) and default-trust loaded Skills/Plugins. Normal app poisoned = data leak; Agent poisoned = attacker gains full Agent execution environment.

## Mandatory Mitigation Measures

1. **Version pinning** — Pin all AI-related dependencies (LiteLLM, LangChain, Anthropic SDK, etc.) to known secure versions + hash verification

```bash
# Python (pip)
pip install --require-hashes -r requirements.txt

# Rust (cargo)
cargo install --locked

# Node.js (npm/pnpm)
npm ci  # Use package-lock.json; prohibit install --no-package-lock
```

2. **Skill source verification** — Verify signature or source repo before loading external Skills

```python
TRUSTED_SKILL_SOURCES = {
    "github.com/your-org",
    "registry.openclaw.dev",
}

def load_skill(source_url: str) -> Skill:
    domain = extract_domain(source_url)
    if domain not in TRUSTED_SKILL_SOURCES:
        raise SkillSourceUntrusted(
            f"Skill from '{domain}' is not in trusted source list. "
            f"Trusted: {TRUSTED_SKILL_SOURCES}"
        )
    return _load(source_url)
```

3. **Pre-release dependency audit** — Mandatory in release CI:

```yaml
# CI security gate
- name: Audit dependencies
  run: |
    npm audit --audit-level=high    # Node.js
    cargo audit                     # Rust
    pip-audit                       # Python (need pip install pip-audit first)
```

4. **SBOM generation** — Software Bill of Materials, for downstream consumers to audit

```bash
# Node.js
npx @cyclonedx/cyclonedx-npm --output-file sbom.json

# Rust
cargo cyclonedx

# Python
pip-sbom --output sbom.json
```

## Runtime Skill Sandbox

For dynamically loaded Skills, run in a restricted sandbox (cannot directly use host process privileges):

```python
class SandboxedSkillRunner:
    def run(self, skill: Skill, input: dict) -> dict:
        # Run in restricted subprocess; doesn't share main process filesystem permissions
        result = subprocess.run(
            ["python", "-c", f"import skill_runner; skill_runner.run({skill.id!r}, {input!r})"],
            capture_output=True,
            timeout=30,
            # Restrict resources
            preexec_fn=lambda: resource.setrlimit(resource.RLIMIT_FSIZE, (10*1024*1024, 10*1024*1024))
        )
        if result.returncode != 0:
            raise SkillExecutionError(result.stderr.decode())
        return json.loads(result.stdout)
```

## Scanning Tools

- npm package supply chain scan → `/supply-chain-scan-npm`
- PyPI package supply chain scan → `/supply-chain-scan-pypi`
- cargo package supply chain scan → `/supply-chain-scan-cargo`
- Docker image supply chain scan → `/supply-chain-scan-docker`
- CI/CD supply chain scan → `/supply-chain-scan-cicd`
