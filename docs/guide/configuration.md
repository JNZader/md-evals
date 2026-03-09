<!-- docs/guide/configuration.md -->
# Configuration Guide

This guide explains the complete `eval.yaml` configuration.

## Full Example

```yaml
name: "My Skill Evaluation"
version: "1.0"
description: "Evaluating code generation skills"

defaults:
  model: "gpt-4o"
  provider: "openai"
  temperature: 0.7
  max_tokens: 2048
  timeout: 60
  retry_attempts: 3

treatments:
  CONTROL:
    description: "No skill context"
    skill_path: null
  
  CONCISE_SKILL:
    description: "Concise skill"
    skill_path: "./skills/concise.md"
  
  DETAILED_SKILL:
    description: "Detailed skill"
    skill_path: "./skills/detailed.md"

tests:
  - name: "code_quality"
    description: "Check code quality"
    prompt: "Write a function to {task}"
    variables:
      task: "sort a list"
    evaluators:
      - type: "regex"
        name: "has_def"
        pattern: "def "
        pass_on_match: true
      - type: "regex"
        name: "has_return"
        pattern: "return "

lint:
  max_lines: 400
  fail_on_violation: true

output:
  format: "table"
  save_results: true
  results_dir: "./results"
  verbose: false

execution:
  parallel_workers: 1
  repetitions: 1
  fail_fast: false
```

## Sections

### defaults

Default values used for all API calls:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `model` | string | `"gpt-4o"` | Model name |
| `provider` | string | `"openai"` | Provider name |
| `temperature` | float | `0.7` | Sampling temperature |
| `max_tokens` | int | `2048` | Max tokens to generate |
| `timeout` | int | `60` | Request timeout (seconds) |
| `retry_attempts` | int | `3` | Number of retries |

### treatments

Define skill configurations to test:

| Field | Type | Description |
|-------|------|-------------|
| `description` | string | Human-readable description |
| `skill_path` | string/null | Path to SKILL.md file |
| `env` | object | Environment variables |

### tests

Define test cases:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Unique test name |
| `description` | string | Test description |
| `prompt` | string | Prompt template with `{variables}` |
| `variables` | object | Variables to substitute |
| `evaluators` | array | List of evaluators |

## Validators

See [Evaluators Guide](./evaluators.md) for details.
