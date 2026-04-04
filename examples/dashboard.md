# md-evals Analytics Dashboard

Run with:
```
md-evals dashboard examples/dashboard.md --store .md-evals/analytics.jsonl
```

---

## Top Skills by Average Score

```sql-eval
SELECT
    skill_path,
    ROUND(AVG(overall_score) * 100, 1) AS avg_pct,
    COUNT(*) AS runs,
    MAX(overall_grade) AS best_grade
FROM eval_records
GROUP BY skill_path
ORDER BY avg_pct DESC
LIMIT 10
```

---

## Cost by Model

```sql-eval
SELECT
    model,
    ROUND(SUM(cost_usd), 4) AS total_cost_usd,
    COUNT(*) AS runs,
    ROUND(AVG(cost_usd), 5) AS avg_cost_per_run
FROM eval_records
WHERE cost_usd IS NOT NULL
GROUP BY model
ORDER BY total_cost_usd DESC
```

---

## Grade Distribution

```sql-eval
SELECT
    overall_grade AS grade,
    COUNT(*) AS count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM eval_records), 1) AS pct
FROM eval_records
GROUP BY overall_grade
ORDER BY grade
```

---

## Recent Eval Runs (Last 20)

```sql-eval
SELECT
    substr(timestamp, 1, 19) AS run_at,
    skill_path,
    overall_grade AS grade,
    ROUND(overall_score * 100, 1) AS score_pct,
    model
FROM eval_records
ORDER BY timestamp DESC
LIMIT 20
```

---

## Token Usage by Provider

```sql-eval
SELECT
    provider,
    SUM(tokens_input) AS total_input_tokens,
    SUM(tokens_output) AS total_output_tokens,
    SUM(tokens_input + tokens_output) AS total_tokens,
    COUNT(*) AS runs
FROM eval_records
WHERE provider != ''
GROUP BY provider
ORDER BY total_tokens DESC
```

---

## Slowest Evaluations (by duration)

```sql-eval
SELECT
    skill_path,
    model,
    duration_ms,
    ROUND(overall_score * 100, 1) AS score_pct,
    substr(timestamp, 1, 19) AS run_at
FROM eval_records
WHERE duration_ms > 0
ORDER BY duration_ms DESC
LIMIT 10
```
