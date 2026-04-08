# Agent Suitability Matrix

## Scenario → Solution Mapping

| Scenario Characteristics | Recommended Approach | Rationale |
|---------------------------|---------------------|-----------|
| Single input → single output, stateless | LLM API call | Simplest, lowest cost |
| Multi-turn dialogue, no side effects | ChatBot (with history) | No tool system overhead needed |
| Fixed-step tool invocation | Function Calling pipeline | Deterministic, easy to debug |
| Dynamic multi-step reasoning + tool selection | **Agent** | Requires loop and decision-making |
| Long-term personalization + proactive triggers | **Agent + Memory** | Requires cross-session state |

## Counter-Signals (Scenarios That Should NOT Use Agents)

1. **Latency-sensitive**: Agent loops inherently introduce latency. If users need < 1s response, agents are unsuitable
2. **Cost-sensitive**: Each agent execution consumes 5-50x tokens (multi-turn + tool calls). Consider pipeline solutions if cost is critical
3. **High determinism requirements**: Agent execution paths are non-deterministic. Use traditional workflows if 100% predictable behavior is needed
4. **Simple CRUD**: If core operations are database CRUD, AI reasoning is unnecessary. Traditional APIs are more reliable
5. **Batch processing**: For large volumes of identical operations (e.g., processing 10,000 records), batch pipelines outperform agents

## Cost Estimation Reference

| Agent Type | Typical Tokens per Execution | Reference Cost (Claude Sonnet) |
|------------|------------------------------|--------------------------------|
| Simple Coding (edit one file) | 10K-30K | $0.03-0.10 |
| Complex Coding (multi-file refactor) | 50K-200K | $0.15-0.60 |
| Research (search + synthesis) | 20K-80K | $0.06-0.24 |
| Data Analysis | 15K-50K | $0.05-0.15 |
| Workflow Orchestration | 30K-100K | $0.09-0.30 |

Note: Sonnet-level estimates. Opus-level ~5x, Haiku-level ~0.2x.
