# SecurityAnalyzer: Runtime Security Analysis Architecture

**Source**: OpenHands `openhands/security/base.py:213-223` (pluggable interface)

## Core Flow

```
Agent generates operation (Action)
    ↓
SecurityAnalyzer.analyze(action) → SecurityResult
    ↓
├── SAFE → Execute
├── WARN → Execute + record alert
└── BLOCK → Reject execution + notify user
```

## Design Points

- **Pluggable**: SecurityAnalyzer is an interface; multiple implementations can be registered (rule engine / LLM evaluation / static analysis)
- **Runtime evaluation**: Dynamically analyzed before each operation, not static configuration at startup
- **Difference from Layer 3**: Layer 3 (Policy Engine) is declarative rule matching (`rm -rf → forbidden`), SecurityAnalyzer is programmatic semantic understanding (same command has different risk in different contexts)

## Applicable Scenarios

1. **Sandbox escape detection** — Detect if Agent is attempting to bypass sandbox
2. **Operation chain attack detection** — Single operation is legal but sequence is dangerous (sliding window analysis)
3. **Pre-execution code scanning** — Static security scan after LLM generates code but before execution

## Implementation Reference

```python
class SecurityAnalyzer:
    def analyze(self, action: Action) -> SecurityResult:
        raise NotImplementedError

class InvariantAnalyzer(SecurityAnalyzer):
    """Rule engine implementation based on invariants"""
    def analyze(self, action):
        if self._violates_invariants(action):
            return SecurityResult.BLOCK
        return SecurityResult.SAFE

class LLMSecurityAnalyzer(SecurityAnalyzer):
    """Semantic security evaluation using LLM"""
    def analyze(self, action):
        risk_score = self.llm.evaluate_risk(action, self.context_window)
        return SecurityResult.BLOCK if risk_score > 0.8 else SecurityResult.SAFE
```

## Relationship with Guardian AI

| Mechanism | Trigger Timing | Evaluation Method | Source |
|------|---------|---------|------|
| Guardian AI [CX] | After user instruction → command generation | Another LLM evaluates intent alignment | Codex CLI |
| SecurityAnalyzer [OH] | Before each Action executes | Pluggable implementation (rule/LLM/static analysis) | OpenHands |

The two complement each other: Guardian AI handles "user intent vs executed command" alignment; SecurityAnalyzer handles "operation vs security policy" compliance.
