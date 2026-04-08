# Prompt Variants: Multi-Model System Prompt Adaptation

Different model families have varying comprehension能力和偏好 for system prompts. Feeding the same system prompt to all models produces wildly different results.

## Cline's Modular Prompt System [CL]

```
11 model families × 13 SystemPromptSection components

Model families: Claude / GPT / Gemini / DeepSeek / Mistral / Llama / Qwen / ...
Components: TOOL_USE / EDITING / BROWSER / PLANNING / MCP / ...

PromptRegistry (singleton)
    ├─ Register variant: matcher function + component override table
    ├─ Selection process: iterate matchers → hit → return variant
    └─ Component override: variant can override any subset of shared component templates
```

**Key insight**: Different models need different system prompts, not just different parameters. Some models need more explicit tool-call format instructions; some understand XML tags better than Markdown.

## Implementation Pattern

```python
from dataclasses import dataclass, field
from typing import Callable

@dataclass
class PromptVariant:
    name: str
    matcher: Callable[[str], bool]  # Receives model_id, returns whether it matches
    overrides: dict[str, str]        # section_name → replacement content

class PromptRegistry:
    _variants: list[PromptVariant] = []
    _default: dict[str, str] = {}   # Shared component defaults

    @classmethod
    def register(cls, variant: PromptVariant):
        cls._variants.append(variant)

    @classmethod
    def build(cls, model_id: str) -> dict[str, str]:
        # Start from shared defaults
        prompt = dict(cls._default)
        # Apply overrides from matching variant
        for variant in cls._variants:
            if variant.matcher(model_id):
                prompt.update(variant.overrides)
                break
        return prompt

# Registration example
PromptRegistry.register(PromptVariant(
    name="deepseek-variant",
    matcher=lambda m: "deepseek" in m.lower(),
    overrides={
        "TOOL_USE": "Use <tool_call> XML tags for all tool invocations.",
        "PLANNING": "Always output a numbered step plan before executing.",
    }
))

PromptRegistry.register(PromptVariant(
    name="gemini-variant",
    matcher=lambda m: "gemini" in m.lower(),
    overrides={
        "TOOL_USE": "Use function_declarations format. Do not use XML tags.",
    }
))
```

## Design Principles

- **Matcher-based selection**: Match by model ID pattern; new models only need a new matcher registered
- **Component-level overrides**: No need to rewrite entire prompts — override only the differing parts
- **Shared components as defaults**: Reduces duplication and ensures consistency

## Anti-Explosion Principles

Maintaining an independent prompt variant for each model family creates exponential maintenance costs as the number of models grows.

Strategies to prevent explosion:
1. **Override only components with genuine differences**, rather than maintaining complete prompt copies per model
2. **Automated regression testing**: Each variant has corresponding behavioral tests (tool call format, output structure); tests run automatically when a variant is modified
3. **Model sunset cleanup**: When a model is deprecated, its variant must be deleted to prevent dead code accumulation
