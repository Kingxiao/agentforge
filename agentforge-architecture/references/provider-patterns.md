# Provider Abstraction Layer Reference

> Source: Provider implementation comparison across 9 production-grade Agents

## Minimal Interface (OpenCode Pattern)

```go
type Provider interface {
    SendMessages(ctx, messages, tools) (*ProviderResponse, error)
    StreamResponse(ctx, messages, tools) <-chan ProviderEvent
    Model() models.Model
}
```

## Event Stream Types (Industry Convergence)

```go
type ProviderEventType int
const (
    EventContentStart   ProviderEventType = iota  // Text stream start
    EventContentDelta                              // Text delta
    EventContentStop                               // Text stream end
    EventThinkingDelta                             // Thinking process (extended thinking)
    EventToolUseStart                              // Tool call start
    EventToolUseDelta                              // Tool parameter delta
    EventToolUseStop                               // Tool call end
    EventComplete                                  // Turn complete
    EventError                                     // Error
    EventWarning                                   // Warning
)
```

## Token Usage Tracking

```go
type TokenUsage struct {
    InputTokens         int64
    OutputTokens        int64
    CacheCreationTokens int64  // Prompt Cache creation
    CacheReadTokens     int64  // Prompt Cache hits
}
```

## Multi-Provider Support Matrix

| Provider | OpenCode | Claude Code | Codex CLI | Aider |
|----------|----------|-------------|-----------|-------|
| Anthropic | yes | yes (native) | no | yes |
| OpenAI | yes | no | yes (native) | yes |
| Google Gemini | yes | no | no | yes |
| AWS Bedrock | yes | no | no | yes |
| Azure OpenAI | yes | no | no | yes |
| Groq | yes | no | no | yes |
| OpenRouter | yes | no | no | yes |
| X.AI | yes | no | no | no |
| GitHub Copilot | yes | no | no | no |
| Local (Ollama/LM Studio) | yes | no | yes | yes |

## Cost Calculation Formula

```
totalCost = (inputTokens * costPer1MInput / 1_000_000)
          + (outputTokens * costPer1MOutput / 1_000_000)
          + (cacheCreationTokens * cacheCreateCostPer1M / 1_000_000)
          + (cacheReadTokens * cacheReadCostPer1M / 1_000_000)
```

## Provider Initialization Patterns

### Factory Pattern [OC]

```go
func NewProvider(config ProviderConfig) (Provider, error) {
    switch config.Type {
    case "anthropic":
        return newAnthropicProvider(config)
    case "openai":
        return newOpenAIProvider(config)
    case "gemini":
        return newGeminiProvider(config)
    // ...
    }
}
```

### Builder Pattern [CX]

```rust
CodexClient::builder()
    .api_key(key)
    .model(model)
    .max_tokens(4096)
    .build()?
```
