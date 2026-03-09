<!-- docs/reference/yaml-schema.md -->
# YAML Schema Reference

Complete reference for `eval.yaml`.

## Top-Level

```yaml
name: string          # Required - Evaluation name
version: string       # Default: "1.0"
description: string  # Optional - Description
```

## defaults

```yaml
defaults:
  model: string       # Default: "gpt-4o"
  provider: string    # Default: "openai"
  temperature: float  # Default: 0.7
  max_tokens: int     # Default: 2048
  timeout: int        # Default: 60
  retry_attempts: int # Default: 3
```

## treatments

```yaml
treatments:
  TREATMENT_NAME:
    description: string      # Optional
    skill_path: string|null   # Path or null for CONTROL
    env:                     # Optional
      KEY: "value"
```

## tests

```yaml
tests:
  - name: string                    # Required
    description: string             # Optional
    prompt: string                  # Required - Template
    variables:                      # Optional
      key: "value"
    evaluators:                     # Required
      - type: "regex"               # See evaluators
        # ... evaluator config
```

## lint

```yaml
lint:
  max_lines: int          # Default: 400
  fail_on_violation: bool # Default: true
```

## output

```yaml
output:
  format: string     # table|json|markdown
  save_results: bool  # Default: true
  results_dir: string # Default: "./results"
  verbose: bool      # Default: false
```

## execution

```yaml
execution:
  parallel_workers: int  # Default: 1
  repetitions: int      # Default: 1
  fail_fast: bool       # Default: false
```
