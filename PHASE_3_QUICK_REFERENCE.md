# Phase 3 Quick Reference: CLI Commands & Flags

## New Commands

### `list-models` - Show Available Models

```bash
# Show all providers and models
md-evals list-models

# Filter to GitHub Models
md-evals list-models --provider github-models

# Show detailed information
md-evals list-models --provider github-models --verbose
```

## New Flags

### `--provider` - Select Provider

```bash
# Run with GitHub Models
md-evals run eval.yaml --provider github-models

# Run with specific model override
md-evals run eval.yaml --provider github-models --model claude-3.5-sonnet

# Run with different provider
md-evals run eval.yaml --provider openai --model gpt-4o
```

**Provider Name Formats (all equivalent):**
- `github-models`
- `github_models`
- `GitHub Models`

### `--debug` - Enable Debug Logging

```bash
# Show provider initialization details
md-evals run eval.yaml --debug

# Combined with other flags
md-evals run eval.yaml --provider github-models --debug
```

## Config File Provider Setting

### In `eval.yaml`

```yaml
name: "My Evaluation"

defaults:
  provider: "github-models"          # ← Set provider here
  model: "claude-3.5-sonnet"         # ← Set model
  temperature: 0.7

treatments:
  CONTROL:
    skill_path: null
  WITH_SKILL:
    skill_path: "./SKILL.md"

tests:
  - name: "test_example"
    prompt: "Example prompt"
```

## Supported GitHub Models

From `md-evals list-models --provider github-models`:

| Model | Provider | Context | Status |
|-------|----------|---------|--------|
| `claude-3.5-sonnet` | Anthropic | 200k | ✅ Supported |
| `gpt-4o` | OpenAI | 128k | ✅ Supported |
| `deepseek-r1` | DeepSeek | 64k | ✅ Supported |
| `grok-3` | xAI | 128k | ✅ Supported |

## Precedence (CLI beats Config)

```bash
# Config has: provider: "github-models", model: "claude-3.5-sonnet"
# CLI command:
md-evals run eval.yaml --provider openai --model gpt-4o

# Result: Uses OpenAI + GPT-4o (CLI overrides config)
```

## Error Handling

### Missing GITHUB_TOKEN

```
[red]Authentication Error: GITHUB_TOKEN environment variable not set or invalid[/red]

[yellow]GitHub Models Troubleshooting:[/yellow]
1. Set your GitHub token: export GITHUB_TOKEN=github_pat_...
2. Generate a token at: https://github.com/settings/tokens
3. Check your .env file for GITHUB_TOKEN
```

**Solution:**
```bash
export GITHUB_TOKEN="github_pat_..." 
md-evals run eval.yaml --provider github-models
```

### Invalid Provider

```
Error: Provider 'invalid' not found. 
Available providers:
  - github-models
```

**Solution:**
```bash
md-evals list-models  # See what providers are available
```

## Common Tasks

### Run evaluation with free GitHub Models
```bash
export GITHUB_TOKEN="github_pat_..."
md-evals run eval.yaml --provider github-models
```

### Compare models
```bash
# Run with Claude
md-evals run eval.yaml --provider github-models --model claude-3.5-sonnet

# Run with GPT-4o
md-evals run eval.yaml --provider github-models --model gpt-4o

# Compare results
```

### Debug provider issues
```bash
md-evals run eval.yaml --provider github-models --debug
```

### Check model capabilities before running
```bash
md-evals list-models --provider github-models --verbose
```

## Full Command Examples

```bash
# Setup (once)
export GITHUB_TOKEN="github_pat_..."

# List all available models
md-evals list-models

# List GitHub Models with details
md-evals list-models --provider github-models --verbose

# Run evaluation with default config
md-evals run

# Run with provider override
md-evals run eval.yaml --provider github-models --model gpt-4o

# Run with debug logging
md-evals run eval.yaml --provider github-models --debug --verbose

# Run specific treatments
md-evals run eval.yaml --treatment CONTROL,WITH_SKILL --provider github-models

# Run with multiple workers
md-evals run eval.yaml --provider github-models -n 4

# Multiple repetitions
md-evals run eval.yaml --provider github-models --count 3
```

## All CLI Options

### `run` Command
```
--config, -c TEXT      Config file path (default: eval.yaml)
--treatment, -t TEXT   Treatment(s) to run
--model, -m TEXT       Override model
--provider, -p TEXT    Override provider
--count INTEGER        Number of repetitions
-n INTEGER             Parallel workers
--output, -o TEXT      Output format (table/json/markdown)
--no-lint              Skip linting
--verbose, -v          Verbose output
--debug                Enable debug logging
```

### `list-models` Command
```
--provider, -p TEXT    Filter by provider
--verbose, -v          Show detailed metadata
```

## Example Config File

See: `examples/eval_with_github_models.yaml`

```bash
# Copy example to your project
cp examples/eval_with_github_models.yaml my_eval.yaml

# Edit and run
md-evals run my_eval.yaml
```
