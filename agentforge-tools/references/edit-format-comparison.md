# Edit Format Selection: How Agents Modify Code

> Source: Research Report Chapter 9 (L732-L789)
> Edit formats are among the most error-prone aspects of production. Choosing the wrong format causes agents to fail repeatedly.

## Comparison of 5 Edit Formats

| Format | Representative Agent | Mechanism | Pros | Cons |
|--------|----------------------|-----------|------|------|
| **Search/Replace Block** | Aider (EditBlock) | `<<<SEARCH`/`===`/`>>>REPLACE` blocks | Human-readable, simple format | Breaks when search target is non-unique |
| **Unified Diff** | Aider (UDiff), Cline | Standard unified diff format | Industry standard, rich tooling | LLM-generated line numbers frequently inaccurate |
| **Whole File** | Aider (WholeFile) | Outputs entire file content | No format errors possible | Severe token waste |
| **Precise Replacement** | Claude Code (Edit) | `old_string` → `new_string` exact match | Precise, safe | Requires unique old_string |
| **Apply Patch** | Codex CLI | Git patch format | Native Git support | Complex format, error-prone for LLMs |

## Claude Code's Precise Replacement Strategy

```typescript
Edit({
  file_path: "/absolute/path",
  old_string: "exact text to replace",
  new_string: "replacement text",
  replace_all: false  // Only replaces first match by default
})
```

**Key constraints**:
- `old_string` must **uniquely match** in the file, otherwise throws error
- Must use **absolute paths**
- File must be read with `Read` tool before editing (tool refuses otherwise)
- Preserve exact indentation (tab/space sensitive)

**Why Claude Code chose this approach**:
- Less prone to line number errors than diffs (LLM-generated line numbers are a pain point)
- More token-efficient than whole-file (only sends the changed portion)
- Uniqueness constraint ensures deterministic edits (no accidental changes to similarly-named code)

## Aider's Polymorphic Edit System

Aider's most unique design — **the same agent can switch edit formats at runtime**:

```python
# Edit format is a polymorphic attribute of the Coder class
class EditBlockCoder(Coder):   edit_format = "diff"
class UnifiedDiffCoder(Coder): edit_format = "udiff"
class PatchCoder(Coder):       edit_format = "patch"
class WholeFileCoder(Coder):   edit_format = "wholefile"
class ArchitectCoder(Coder):   edit_format = "architect"
```

### Architect Mode (Two-Phase Separation)

1. **Architecture model** does high-level planning ("which files need changes, how")
2. **Edit model** executes the specific modifications (generates edit blocks based on plan)

Value: Expensive model only judges, cheap model executes — cost optimization.

### Fuzzy Matching

- Edit block search targets support fuzzy matching
- Handles minor format differences in LLM output (extra spaces, indentation shifts)
- Improves edit success rate, reduces "no match found" failures

## Selection Decision Tree

```
How does your agent modify code?
│
├─ Only need precise small-scope edits (most coding agent scenarios)
│  → Precise replacement (Claude Code approach)
│     Priority: high determinism, good token efficiency
│
├─ Need to support multiple edit strategies, switch by scenario
│  → Polymorphic editing (Aider approach)
│     Priority: high flexibility, can select strategy by model capability
│
├─ Changes typically involve rewriting entire files (template generation, etc.)
│  → Whole File
│     Priority: zero format errors, but only suitable for small files
│
└─ Need deep integration with Git tooling
   → Apply Patch (Codex approach)
      Note: LLM-generated patch format has high error rate
```

## Token Efficiency Comparison by Format

Modifying 3 lines in a 100-line file:

| Format | Output Tokens (estimated) | Efficiency Ratio |
|--------|--------------------------|------------------|
| Precise Replacement | ~30 | 1x (baseline) |
| Search/Replace Block | ~50 | 1.7x |
| Unified Diff | ~60 | 2x |
| Apply Patch | ~70 | 2.3x |
| Whole File | ~300 | 10x |

**Conclusion**: Precise replacement has highest token efficiency, Whole File is most wasteful. But Whole File has the highest success rate (no format parsing issues).
