<!-- docs/guide/treatments.md -->
# Treatments

Treatments are skill configurations that define how the LLM should behave during evaluation.

## CONTROL Treatment

The CONTROL treatment is special - it has no skill context:

```yaml
treatments:
  CONTROL:
    description: "Baseline without any skill"
    skill_path: null  # This is required for CONTROL
```

The CONTROL treatment runs the bare prompt without any skill injection, providing a baseline for comparison.

## Custom Treatments

```yaml
treatments:
  CONCISE_SKILL:
    description: "Short, focused skill"
    skill_path: "./skills/concise.md"
  
  DETAILED_SKILL:
    description: "Comprehensive skill"
    skill_path: "./skills/detailed.md"
  
  WITH_ENV:
    description: "Skill with custom env"
    skill_path: "./skills/custom.md"
    env:
      CUSTOM_VAR: "value"
```

## Wildcards

You can use wildcards to run multiple treatments:

```bash
# Run all treatments matching LCC_*
md-evals run --treatment LCC_*

# Run treatments starting with TEST_
md-evals run --treatment TEST_*
```

## How It Works

1. **CONTROL**: Bare prompt → LLM
2. **With Skill**: Prompt + SKILL.md content injected as system prompt → LLM

The skill content is prepended to a system message, guiding the LLM's behavior.
