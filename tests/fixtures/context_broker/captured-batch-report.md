# Captured batch report export

`build_captured_report` turns rows that were already captured into a JSON-ready,
privacy-minimized summary. It does not run a model, write a file, or contact a provider.

## Quick path

```python
from md_evals.captured_batch_report import render_captured_report_json

report_json = render_captured_report_json(
    captured_rows, expected_by_task=expected_by_task, repetitions=2
)
```

The `arms`, `cohorts`, and `paired_comparisons` arrays retain the comparator's fixed order.
Each arm has allowlisted `quality` and `usage` objects. The six usage token counters are
decimal strings or `null`; `token_count_encoding` is `decimal-string`. Counts and quality
rates remain JSON numbers. A quality-incomplete batch can still have a complete usage total
for an individual arm.

## Limits

- The export excludes task names, prompts, responses, expected gold, context IDs/digests,
  metadata, timestamps, provider/model identity, and raw telemetry.
- Captured-batch results are not statistical utility or Gate1 evidence, billing, provider
  identity, measured token savings, global pooled totals, or authorization for live execution.
