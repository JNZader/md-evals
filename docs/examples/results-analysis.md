<!-- docs/examples/results-analysis.md -->
# Results Analysis

## JSON Output

```bash
md-evals run -o json
```

This creates `results/results.json`:

```json
{
  "experiment_id": "eval_20260217_143052",
  "timestamp": "2026-02-17T14:30:52Z",
  "summary": {
    "control_pass_rate": 0.5,
    "treatment_pass_rate": 1.0,
    "improvement": 0.5
  },
  "results": [
    {
      "treatment": "CONTROL",
      "test": "example_test",
      "passed": false,
      "duration_ms": 1234,
      "tokens": 245
    }
  ]
}
```

## Markdown Output

```bash
md-evals run -o markdown
```

Creates a formatted report with tables.

## Verbose Mode

```bash
md-evals run -v
```

Shows detailed evaluator results for each test.
