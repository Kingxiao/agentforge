# Tool Interface Complete Reference

> Source: Full interface extracted from Claude Code src/Tool.ts (792 lines)

## Claude Code's Complete Tool Interface

Every method below addresses a real product need. Those marked `[required]` are needed from the MVP stage.

### Core Execution

| Method | Purpose | Stage |
|--------|---------|-------|
| `call(input, context)` | Tool execution entry, returns AsyncGenerator | [required] |
| `inputSchema` | Zod schema for input validation and API schema generation | [required] |
| `outputSchema` | Output schema (optional, for type safety) | Maturation |

### LLM Communication

| Method | Purpose | Stage |
|--------|---------|-------|
| `name` | Tool identifier (used by LLM to call the tool) | [required] |
| `description()` | Static description for the LLM | [required] |
| `prompt()` | Dynamic description for the LLM (can vary with context) | Maturation |

### Concurrency & Safety

| Method | Purpose | Stage |
|--------|---------|-------|
| `isConcurrencySafe()` | Whether safe to execute in parallel with other tools | [required] |
| `isReadOnly()` | Whether read-only (affects permission flexibility) | [required] |
| `isDestructive()` | Whether high-risk (requires extra confirmation) | Maturation |

### Permissions & Validation

| Method | Purpose | Stage |
|--------|---------|-------|
| `checkPermissions(input)` | Tool-level permission check | Maturation |
| `preparePermissionMatcher()` | Compile once, match many times (performance) | Optimization |
| `validateInput(input)` | Pre-execution validation (prevents invalid calls) | [required] |

### Context Management

| Method | Purpose | Stage |
|--------|---------|-------|
| `shouldDefer` | Whether to defer loading (reduces prompt tokens) | Maturation |
| `isEnabled(context)` | Dynamic enable/disable | Maturation |

### Rendering & Serialization

| Method | Purpose | Stage |
|--------|---------|-------|
| `renderToolUseMessage(input)` | User-facing input rendering | Maturation |
| `renderToolResultMessage(output)` | User-facing result rendering | Maturation |
| `mapToolResultToToolResultBlockParam(output)` | API result serialization | [required] |

## Builder Pattern Implementation

```typescript
function buildTool(config: {
  name: string;
  description: string;
  inputSchema: ZodSchema;
  call: (input, context) => AsyncGenerator;
  // All below have safe defaults
  isConcurrencySafe?: boolean;      // default: false
  isReadOnly?: boolean;             // default: false
  isDestructive?: boolean;          // default: false
  shouldDefer?: boolean;            // default: false
  validateInput?: (input) => void;  // default: schema validation
}) {
  return {
    ...defaults,
    ...config,
  };
}
```

## Tool Implementation Comparison Across Agents

### OpenCode (Go) — Minimal

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

### Codex CLI (Rust) — Trait System

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

### Cline (TypeScript) — Enum + Handler

```typescript
enum ClineDefaultTool {
    BASH, FILE_READ, FILE_EDIT, FILE_NEW, SEARCH,
    LIST_FILES, LIST_CODE_DEF, BROWSER, MCP_USE,
    APPLY_PATCH, WEB_FETCH, WEB_SEARCH,
    // ...36+ tools
}
// Each tool has an independent handler file
```

## MCP Tool Wrapping Pattern

```go
// OpenCode's MCP tool dynamic registration
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
