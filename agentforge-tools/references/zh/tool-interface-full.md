# 工具接口完整参考

> 来源：Claude Code src/Tool.ts (792 行) 的完整接口提炼

## Claude Code 的完整 Tool 接口

以下每个方法都对应一个真实的产品需求。标注 `[必须]` 的在 MVP 阶段就需要。

### 核心执行

| 方法 | 用途 | 阶段 |
|------|------|------|
| `call(input, context)` | 工具执行入口，返回 AsyncGenerator | [必须] |
| `inputSchema` | Zod schema，用于输入验证和 API schema 生成 | [必须] |
| `outputSchema` | 输出 schema（可选，用于类型安全） | 成熟期 |

### LLM 通信

| 方法 | 用途 | 阶段 |
|------|------|------|
| `name` | 工具标识符（LLM 用来调用） | [必须] |
| `description()` | 给 LLM 的静态说明 | [必须] |
| `prompt()` | 给 LLM 的动态说明（可随上下文变化） | 成熟期 |

### 并发与安全

| 方法 | 用途 | 阶段 |
|------|------|------|
| `isConcurrencySafe()` | 是否可与其他工具并行执行 | [必须] |
| `isReadOnly()` | 是否只读（影响权限宽松度） | [必须] |
| `isDestructive()` | 是否高危（需要额外确认） | 成熟期 |

### 权限与验证

| 方法 | 用途 | 阶段 |
|------|------|------|
| `checkPermissions(input)` | 工具级权限检查 | 成熟期 |
| `preparePermissionMatcher()` | 编译一次匹配多次（性能） | 优化期 |
| `validateInput(input)` | 执行前校验（防无效调用） | [必须] |

### 上下文管理

| 方法 | 用途 | 阶段 |
|------|------|------|
| `shouldDefer` | 是否延迟加载（减少 prompt token） | 成熟期 |
| `isEnabled(context)` | 动态启用/禁用 | 成熟期 |

### 渲染与序列化

| 方法 | 用途 | 阶段 |
|------|------|------|
| `renderToolUseMessage(input)` | 给用户看的输入渲染 | 成熟期 |
| `renderToolResultMessage(output)` | 给用户看的结果渲染 | 成熟期 |
| `mapToolResultToToolResultBlockParam(output)` | 给 API 的结果序列化 | [必须] |

## Builder Pattern 实现

```typescript
function buildTool(config: {
  name: string;
  description: string;
  inputSchema: ZodSchema;
  call: (input, context) => AsyncGenerator;
  // 以下全部有 safe defaults
  isConcurrencySafe?: boolean;      // default: false
  isReadOnly?: boolean;             // default: false
  isDestructive?: boolean;          // default: false
  shouldDefer?: boolean;            // default: false
  validateInput?: (input) => void;  // default: schema 验证
}) {
  return {
    ...defaults,
    ...config,
  };
}
```

## 各 Agent 的工具实现对比

### OpenCode (Go) — 极简

```go
type BaseTool interface {
    Info() ToolInfo
    Run(ctx context.Context, call ToolCall) (ToolResponse, error)
}

type ToolInfo struct {
    Name        string
    Description string
    Parameters  map[string]interface{} // JSON Schema
}

type ToolResponse struct {
    Type    string // "text" | "image"
    Content string
    IsError bool
}
```

### Codex CLI (Rust) — trait 系统

```rust
#[async_trait]
trait ToolHandler {
    type Output;
    async fn handle(&self, invocation: ToolInvocation) -> Result<Self::Output, FunctionCallError>;
    async fn is_mutating(&self, invocation: &ToolInvocation) -> bool;
    fn pre_tool_use_payload(&self) -> Option<HookPayload>;
    fn post_tool_use_payload(&self) -> Option<HookPayload>;
}
```

### Cline (TypeScript) — 枚举 + Handler

```typescript
enum ClineDefaultTool {
    BASH, FILE_READ, FILE_EDIT, FILE_NEW, SEARCH, 
    LIST_FILES, LIST_CODE_DEF, BROWSER, MCP_USE,
    APPLY_PATCH, WEB_FETCH, WEB_SEARCH,
    // ...36+ 工具
}
// 每个工具有独立的 handler 文件
```

## MCP 工具包装模式

```go
// OpenCode 的 MCP 工具动态注册
type mcpTool struct {
    server       MCPServer
    originalName string
    schema       json.RawMessage
}

func (t *mcpTool) Info() ToolInfo {
    return ToolInfo{
        Name:        fmt.Sprintf("%s_%s", t.server.Name, t.originalName),
        Description: t.schema.Description,
        Parameters:  t.schema.InputSchema,
    }
}

func (t *mcpTool) Run(ctx, call) (ToolResponse, error) {
    return t.server.CallTool(ctx, t.originalName, call.Input)
}
```
