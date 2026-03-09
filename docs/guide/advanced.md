<!-- docs/guide/advanced.md -->
# Advanced Features

## Parallel Execution

Run multiple treatments in parallel:

```bash
md-evals run -n 4
```

This runs 4 treatments simultaneously.

## Repetitions

Run tests multiple times for statistical significance:

```bash
md-evals run --count 3
```

Combines with parallel:

```bash
md-evals run -n 4 --count 3
```

## Custom Models

Override the default model:

```bash
md-evals run --model claude-3-5-sonnet-20241022
md-evals run --model gemini-1.5-pro
```

## Output Formats

### Table (default)

```bash
md-evals run -o table
```

### JSON

```bash
md-evals run -o json
```

Results saved to `results/results.json`.

### Markdown

```bash
md-evals run -o markdown
```

Results saved to `results/results.md`.

## Verbose Output

```bash
md-evals run -v
```

Shows detailed results for each test.

## Environment Variables in Treatments

```yaml
treatments:
  WITH_API:
    skill_path: "./skill.md"
    env:
      API_URL: "https://api.example.com"
      API_KEY: "secret"
```

## Fail Fast

Stop on first failure:

```yaml
execution:
  fail_fast: true
```
