<!-- docs/guide/quick-start.md -->
# Quick Start

This tutorial walks you through running your first evaluation in 5 minutes.

## Step 1: Initialize a Project

```bash
md-evals init my-first-evaluation
cd my-first-evaluation
```

This creates:
- `eval.yaml` - Your evaluation configuration
- `SKILL.md` - A sample skill file
- `results/` - Directory for results

## Step 2: Review the Configuration

Open `eval.yaml`:

```yaml
name: "My Evaluation"
version: "1.0"

defaults:
  model: "gpt-4o"
  provider: "openai"
  temperature: 0.7

treatments:
  CONTROL:
    description: "Baseline without skill"
    skill_path: null
  
  WITH_SKILL:
    description: "With skill injected"
    skill_path: "./SKILL.md"

tests:
  - name: "example_test"
    prompt: "Hello, {name}! How are you?"
    variables:
      name: "World"
    evaluators:
      - type: "regex"
        name: "has_greeting"
        pattern: "Hello"
```

## Step 3: Customize (Optional)

Edit `eval.yaml` to match your needs:

```yaml
defaults:
  model: "gemini-1.5-flash"  # Change model
  provider: "gemini"

treatments:
  CONTROL:
    skill_path: null
  CONCISE_SKILL:
    skill_path: "./skills/concise.md"
  DETAILED_SKILL:
    skill_path: "./skills/detailed.md"
```

## Step 4: Run the Evaluation

```bash
md-evals run
```

You'll see:

```
╔══════════════════════════════════════════════════════════════════╗
║                    md-evals Results                                ║
╠══════════════════════════════════════════════════════════════════╣
║ Treatment              │ Checks    │ Score  │ Time  │ Tokens    ║
╠══════════════════════════════════════════════════════════════════╣
║ CONTROL                │ 1/1 (100%)│ 1.0    │ 1.2s  │ 245       ║
║ WITH_SKILL             │ 1/1 (100%)│ 1.0    │ 1.4s  │ 312       ║
╚══════════════════════════════════════════════════════════════════╝
```

## Step 5: View Detailed Results

```bash
md-evals run -o json
```

This saves results to `results/results.json`.

## Common Commands

### Run specific treatments

```bash
md-evals run --treatment WITH_SKILL
```

### Run with repetitions

```bash
md-evals run --count 3
```

### Run in parallel

```bash
md-evals run -n 4
```

### Skip linting

```bash
md-evals run --no-lint
```

### Use different model

```bash
md-evals run --model claude-3-5-sonnet-20241022
```

## Next Steps

- [Configuration Guide](./configuration.md) - Deep dive into eval.yaml
- [Treatments](./treatments.md) - Learn about treatments
- [Examples](../examples/basic-evaluation.md) - More examples
