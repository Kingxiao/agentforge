# Provider 抽象层参考

> 来源：9 个生产级 Agent 的 Provider 实现对比

## 最简接口（OpenCode 模式）

```go
type Provider interface {
    SendMessages(ctx, messages, tools) (*ProviderResponse, error)
    StreamResponse(ctx, messages, tools) <-chan ProviderEvent
    Model() models.Model
}
```

## 事件流类型（全行业趋同）

```go
type ProviderEventType int
const (
    EventContentStart   ProviderEventType = iota  // 文本流开始
    EventContentDelta                              // 文本增量
    EventContentStop                               // 文本流结束
    EventThinkingDelta                             // 思考过程（extended thinking）
    EventToolUseStart                              // 工具调用开始
    EventToolUseDelta                              // 工具参数增量
    EventToolUseStop                               // 工具调用结束
    EventComplete                                  // 本轮完成
    EventError                                     // 错误
    EventWarning                                   // 警告
)
```

## Token 用量追踪

```go
type TokenUsage struct {
    InputTokens         int64
    OutputTokens        int64
    CacheCreationTokens int64  // Prompt Cache 创建
    CacheReadTokens     int64  // Prompt Cache 命中
}
```

## 多 Provider 支持矩阵

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

## 成本计算公式

```
totalCost = (inputTokens * costPer1MInput / 1_000_000)
          + (outputTokens * costPer1MOutput / 1_000_000)
          + (cacheCreationTokens * cacheCreateCostPer1M / 1_000_000)
          + (cacheReadTokens * cacheReadCostPer1M / 1_000_000)
```

## Provider 初始化模式

### 工厂模式 [OC]

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

### Builder 模式 [CX]

```rust
CodexClient::builder()
    .api_key(key)
    .model(model)
    .max_tokens(4096)
    .build()?
```
