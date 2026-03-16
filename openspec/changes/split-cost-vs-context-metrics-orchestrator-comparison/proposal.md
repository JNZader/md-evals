# Proposal: split-cost-vs-context-metrics-orchestrator-comparison

## Intent

Separar las métricas de ejecución de md-evals en **dos ejes independientes** para comparativa orquestador vs no-orquestador:

- **`cost_metrics`**: tokens consumidos → costo USD estimado + latencia (cuánto cuesta ejecutar).
- **`context_metrics`**: uso de context window → riesgo técnico de overflow/truncamiento (cuánto contexto queda).

Hoy ambos conceptos están mezclados o ausentes. Esta separación permite responder preguntas distintas sin confundir "más caro" con "más riesgoso en contexto".

## Scope

### `cost_metrics` (consumo económico)
- `prompt_tokens`, `completion_tokens`, `total_tokens` del provider.
- `estimated_cost_usd` calculado con rates configurables por modelo (`cost_map` en `eval.yaml`). `null` si no hay rate — nunca error.
- `latency_ms` medido por llamada.
- `data_quality` flag: `measured` / `estimated` / `unavailable`.

### `context_metrics` (riesgo técnico)
- `prompt_tokens_used`, `context_window_max_tokens`, `context_utilization_pct`.
- `headroom_tokens`, `safe_headroom_tokens` (descuenta `max_tokens` de respuesta).
- `overflow` (bool), `overflow_tokens`, `truncation_risk` (low/medium/high/unknown por umbrales).
- `data_quality` flag independiente del de cost.

### Stage breakdown (orquestador)
- Cada llamada LLM etiquetada con `stage_type`: `planner`, `router`, `tool_call`, `synthesis`, `single_pass`.
- `tool_io_tokens` separado de tokens LLM.
- `attribution_quality` por stage: `high` / `medium` / `low`.
- Non-orchestrator: un solo stage `single_pass`.

### Comparativa side-by-side
- Bloque `comparison` con `delta_abs` y `delta_pct` por domain, protección division-by-zero.
- Métricas normalizadas opcionales: `tokens_per_successful_case`, `tokens_per_score_point`.
- Variant faltante → nulls con `reason`, nunca crash.

### Feature flags
- **Off por defecto** (`--collect-usage-metrics` CLI o `output.include_usage_metrics: true` en YAML).
- CLI tiene precedencia sobre YAML.
- Flags off → output idéntico al legacy actual (cero campos nuevos, cero overhead).

### Backward compatibility
- Campos legacy (`tokens`, `duration_ms`) invariados siempre.
- Nuevos campos son estrictamente aditivos.

## Approach

1. Definir modelos de datos para ambos domains y stage breakdown (ver spec §3).
2. Extraer `prompt_tokens` del provider telemetry (hoy solo se captura `completion_tokens`).
3. Agregar `cost_map` a config y lógica de cálculo USD.
4. Implementar recolección condicional detrás de feature flag.
5. Agregar bloque `usage_metrics` al reporter (JSON + CLI Rich tables).
6. Comparison con deltas por domain.

No se modifica la lógica de evaluación — solo instrumentación y reporting.

## Risks

| Riesgo | Mitigación |
|--------|------------|
| **Telemetría parcial del provider** — algunos no exponen `prompt_tokens`. | `data_quality` flag + `attribution_quality` por stage. Métricas derivadas → `null` si falta input. |
| **Cost map desactualizado** — rates cambian frecuentemente. | `estimated_cost_usd = null` si no hay rate. Sin error, sin default inventado. Responsabilidad del usuario mantener rates. |
| **Confusión cost vs context** — mejor utilización de contexto ≠ menor costo. | Domains separados con deltas independientes. Sin score blended. |
| **Feature flag regression** — flags off debe ser idéntico a legacy. | Test explícito: JSON con flags off es byte-identical en estructura al formato previo. |

## Success Criteria

→ Ver spec §8 para los 20 acceptance criteria detallados. Resumen:

- [ ] Dos domains separados en JSON y CLI sin campos mezclados.
- [ ] Flags off → output legacy idéntico (AC-02).
- [ ] `estimated_cost_usd` correcto con rate, `null` sin rate (AC-03, AC-19).
- [ ] Context metrics: utilization, headroom, safe_headroom, overflow, truncation_risk con null-safety (AC-04 a AC-09, AC-20).
- [ ] Stage breakdown con attribution_quality, sumas consistentes (AC-10 a AC-12).
- [ ] Comparison con deltas por domain, division-by-zero safe (AC-13 a AC-15).
- [ ] CLI flag con precedencia sobre YAML (AC-16).
- [ ] Legacy fields invariados (AC-17).
- [ ] `data_quality` en ambos domains (AC-18).

## References

- **Spec completa**: [`spec.md`](./spec.md) — definiciones, tablas de campos, fórmulas, scenarios, edge cases, JSON canónico.
