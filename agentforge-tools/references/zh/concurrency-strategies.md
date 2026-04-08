# Tool Concurrency Strategies Reference

> Sources: Claude Code, Codex CLI, OpenCode, Cline concurrency implementations compared

## Strategy 1: Partitioned Concurrency [CC] (Recommended)

```
All tool calls arrive
    ↓
[Partition by isConcurrencySafe()]
    ├─ true:  FileRead, Glob, Grep, WebFetch, WebSearch, LSP
    │   → Promise.all() parallel execution
    │
    └─ false: FileWrite, FileEdit, Bash, Git, Agent
        → for...of serial execution
```

**Implementation要点**:
- Partitioning occurs across all tool_use blocks returned in a single LLM response
- Parallel group executes first, serial group follows
- Each tool's results collected independently with no interdependencies

## Strategy 2: Model-Driven Parallelism [CL]

Cline supports model-native parallel tool calls:
- If a model returns multiple tool_use blocks in one response, they can be executed in parallel
- Depends on whether the model supports parallel calling capability
- Loop detection prevents duplicate calls to the same tool

## Strategy 3: Fully Serial [CX, OC, AD]

Executes one tool call at a time:
- Safest approach, no race conditions
- Suitable for scenarios requiring approval of each operation (Codex's Starlark strategy checking)

## Concurrency Safety Annotation Guide

| Tool Type | Concurrency Safe? | Rationale |
|-----------|------------------|-----------|
| File Read | Yes | Read-only, no side effects |
| File Search (Glob/Grep) | Yes | Read-only |
| Web Requests | Yes | No local side effects |
| LSP Queries | Yes | Read-only queries |
| File Write | **No** | May write to the same file |
| File Edit | **No** | Depends on current file content |
| Shell Commands | **No** | May modify filesystem |
| Git Operations | **No** | Modifies repository state |
| Sub-Agent Spawning | **No** | May modify shared state |
| Plan Mode Switching | **No** | Modifies Agent state |

## Race Condition Protection

```typescript
// File state cache pattern [CC]
type FileStateCache = {
  [path: string]: {
    content: string,
    mtime: number,
    size: number
  }
}

// Check if file was modified by another tool before editing
function validateBeforeEdit(path, expectedContent) {
  const current = readFile(path);
  if (current !== expectedContent) {
    throw new Error(`File ${path} was modified since last read`);
  }
}
```
