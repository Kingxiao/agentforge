# Tool-Level Network Permissions: Detailed Implementation

> OS Sandbox's `network_allowed: bool` is an Agent-level global switch; cannot distinguish between tools within the same sandboxed process. This document provides three implementation approaches with finer granularity.

## Approach A: Tool-Isolated Processes (Strongest Isolation)

Each tool class runs in an independent container, each with different network policies:

```yaml
# docker-compose.yml
services:
  web-search-runner:
    image: agent-tool-runner:latest
    networks: [external-net]
    environment:
      ALLOWED_DOMAINS: "*.google.com,*.bing.com,*.wikipedia.org"

  code-runner:
    image: agent-tool-runner:latest
    networks: [internal-net]
    environment:
      ALLOWED_HOSTS: "api.internal,db.internal"
      BLOCKED_HOSTS: "*"

  file-editor:
    image: agent-tool-runner:latest
    network_mode: "none"   # Completely disconnected

networks:
  external-net:
    driver: bridge
  internal-net:
    driver: bridge
    internal: true          # No routing to host external
```

**Applicable**: SaaS multi-tenant products needing strongest tool-level isolation.

## Approach B: Application-Layer Proxy (Medium Isolation)

Tools forward network requests through a middleware proxy, which enforces tool-level policies:

```python
from fnmatch import fnmatch

class NetworkProxy:
    # Maintained in tool configuration file; not hardcoded
    TOOL_POLICIES: dict[str, dict] = {
        "WebSearch": {"allow": ["*"], "deny": []},
        "WebFetch":  {"allow": ["*"], "deny": ["*.internal", "169.254.*", "10.*", "192.168.*"]},
        "CodeRunner": {"allow": ["api.internal"], "deny": ["*"]},
        "FileEdit":  {"allow": [], "deny": ["*"]},   # Completely disconnected
    }

    def check(self, tool_name: str, url: str) -> bool:
        policy = self.TOOL_POLICIES.get(tool_name, {"allow": [], "deny": ["*"]})
        # Deny takes precedence
        if any(fnmatch(url, d) for d in policy["deny"]):
            return False
        return any(fnmatch(url, a) for a in policy["allow"])

    def proxy_request(self, tool_name: str, url: str, **kwargs):
        if not self.check(tool_name, url):
            raise NetworkPolicyViolation(
                f"Tool '{tool_name}' is not allowed to access '{url}'. "
                f"Policy: {self.TOOL_POLICIES.get(tool_name)}"
            )
        return requests.request(url=url, **kwargs)
```

**Applicable**: Self-hosted single-node service; medium security requirements; simple operations.

## Approach C: Tool Declarative Metadata (Lightest)

Tools declare network requirements in the interface; tool dispatcher performs policy checks:

```python
from dataclasses import dataclass

@dataclass
class NetworkPolicy:
    allowed_schemes: list[str] = ("https",)
    allowed_domains: list[str] = ()
    blocked_domains: list[str] = ("*.internal", "localhost", "169.254.*")

class WebSearchTool(BaseTool):
    def network_policy(self) -> NetworkPolicy:
        return NetworkPolicy(allowed_domains=["*"])  # Allow any external HTTPS

class CodeRunnerTool(BaseTool):
    def network_policy(self) -> NetworkPolicy:
        return NetworkPolicy(
            allowed_domains=["api.internal"],
            blocked_domains=["*"],  # Default deny all; only allow declared whitelist
        )

class FileEditTool(BaseTool):
    def network_policy(self) -> NetworkPolicy:
        return NetworkPolicy(allowed_domains=[])  # Completely disconnected

# Dispatcher check (called before tool execution)
class ToolDispatcher:
    def validate_network_call(self, tool: BaseTool, url: str):
        policy = tool.network_policy()
        if not self._is_allowed(url, policy):
            raise NetworkPolicyViolation(
                f"{tool.name} is requesting network access to {url} but has not declared this permission. "
                f"If needed, declare it in tool.network_policy()."
            )
```

**Applicable**: CLI tool development / Spec document declaring network requirements; used with Layer 5 OS Sandbox.

## Selection Guide

| Scenario | Recommended Approach |
|------|---------|
| SaaS multi-tenant; strong isolation needs | A (container isolation)|
| Self-hosted; medium security requirements | B (proxy layer) |
| CLI tools / rapid prototyping / Spec phase | C (declarative) |
| Finance / healthcare high-security scenarios | A + B combined |

## Declaration Template in Agent Spec

Fill in Phase 0 Spec "Security Requirements" field (decide earlier; affects architecture selection):

```
## Security Requirements
- WebSearch tool: Allow external HTTPS (any domain)
- CodeRunner tool: Only allow api.internal + db.internal
- FileEdit / FileRead tools: Completely disconnected
- Network control implementation: Approach B (application-layer proxy)
```
