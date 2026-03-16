# Specification: split-cost-vs-context-metrics-orchestrator-comparison

**Version**: 1.0  
**Status**: Draft  
**Última actualización**: 2026-03-15  

---

## 1. Propósito

Separar las métricas de ejecución en dos dominios independientes — `cost_metrics` (consumo de tokens para cálculo de costo USD) y `context_metrics` (uso de context window para evaluar riesgo técnico) — con comparativa side-by-side entre modo orquestador (multi-etapa) y no-orquestador (single-pass), manteniendo backward compatibility estricta mediante feature flags desactivados por defecto.

---

## 2. Definiciones

| Término | Definición |
|---------|-----------|
| **cost_metrics** | Domain de métricas orientado a cuántos tokens se enviaron/recibieron y cuánto cuesta en USD. |
| **context_metrics** | Domain de métricas orientado a cuánto del context window se consumió y qué riesgo técnico hay de overflow/truncamiento. |
| **orchestrator** (orq) | Flujo multi-etapa con ≥2 llamadas LLM semánticamente distintas (planner → router → tool_call → synthesis). |
| **non_orchestrator** (no-orq) | Flujo single-pass con una sola llamada LLM principal por test case/treatment. |
| **stage_type** | Etiqueta semántica de cada llamada LLM: `planner`, `router`, `tool_call`, `synthesis`, `single_pass`. |
| **variant** | Uno de los dos modos de ejecución: `orchestrator` o `non_orchestrator`. |
| **headroom** | Tokens disponibles restantes antes de alcanzar el límite del context window. |
| **safe_headroom** | Headroom que además descuenta los `max_tokens` configurados para la respuesta. |
| **overflow** | Condición donde `prompt_tokens_used > context_window_max_tokens`. |
| **truncation_risk** | Nivel de riesgo de que el modelo trunque o falle por falta de contexto: `low`, `medium`, `high`, `unknown`. |

---

## 3. Tabla de Métricas por Domain

### 3.1 `cost_metrics`

Métricas orientadas a calcular el costo económico de ejecución.

| Campo | Tipo | Fuente | Descripción |
|-------|------|--------|-------------|
| `prompt_tokens` | `int` | Provider telemetry (`response.usage.prompt_tokens`) | Tokens enviados al modelo (input). |
| `completion_tokens` | `int` | Provider telemetry (`response.usage.completion_tokens`) | Tokens generados por el modelo (output). |
| `total_tokens` | `int` | Derivado: `prompt_tokens + completion_tokens` | Total de tokens facturables. |
| `estimated_cost_usd` | `float \| null` | Derivado: `(prompt_tokens × input_rate + completion_tokens × output_rate) / 1_000_000` | Costo estimado en USD. `null` si no hay rate configurado. |
| `latency_ms` | `int` | Medido: `time.monotonic()` delta | Latencia total de la llamada en milisegundos. |
| `data_quality` | `enum` | Inferido | `measured` si provider retorna usage, `estimated` si se usó fallback, `unavailable` si no hay datos. |

### 3.2 `context_metrics`

Métricas orientadas a evaluar riesgo técnico de overflow del context window.

| Campo | Tipo | Fuente | Descripción |
|-------|------|--------|-------------|
| `prompt_tokens_used` | `int` | Provider telemetry (`response.usage.prompt_tokens`) | Tokens del prompt enviados al modelo. Mismo valor físico que `cost_metrics.prompt_tokens` pero con semántica de "ocupación del contexto". |
| `context_window_max_tokens` | `int \| null` | Config YAML (model registry) o provider metadata | Capacidad máxima del modelo en tokens. `null` si desconocido. |
| `context_utilization_pct` | `float \| null` | Derivado: `(prompt_tokens_used / context_window_max_tokens) × 100` | Porcentaje de contexto utilizado. `null` si `context_window_max_tokens` es `null` o `0`. |
| `headroom_tokens` | `int \| null` | Derivado: `max(context_window_max_tokens - prompt_tokens_used, 0)` | Tokens restantes antes del límite. `null` si window desconocido. |
| `safe_headroom_tokens` | `int \| null` | Derivado: `max(context_window_max_tokens - prompt_tokens_used - max_tokens_request, 0)` | Headroom descontando el espacio reservado para la respuesta (`defaults.max_tokens`). `null` si window desconocido. |
| `max_tokens_request` | `int` | Config: `defaults.max_tokens` | El valor de `max_tokens` usado en la request. Necesario para calcular `safe_headroom_tokens`. |
| `overflow` | `bool` | Derivado: `prompt_tokens_used > context_window_max_tokens` | `true` si el prompt excede la ventana. `false` en caso normal. `false` por defecto si window desconocido. |
| `overflow_tokens` | `int` | Derivado: `max(prompt_tokens_used - context_window_max_tokens, 0)` | Cantidad de tokens que exceden la ventana. `0` si no hay overflow o window desconocido. |
| `truncation_risk` | `enum` | Derivado por umbrales sobre `context_utilization_pct` | Nivel de riesgo: `low`, `medium`, `high`, `unknown`. |
| `data_quality` | `enum` | Inferido | `measured`, `estimated`, `unavailable`. |

#### Umbrales de `truncation_risk`

| `context_utilization_pct` | `truncation_risk` |
|---------------------------|-------------------|
| `null` (window desconocido) | `unknown` |
| `< 70%` | `low` |
| `≥ 70%` y `< 90%` | `medium` |
| `≥ 90%` | `high` |

Estos umbrales son los defaults. El sistema PUEDE permitir override vía configuración en futuras versiones, pero esta spec no lo requiere.

---

## 4. Requirements

### REQ-01: Separación de Domains

**MUST**: El sistema DEBE emitir dos objetos independientes y no solapados: `cost_metrics` y `context_metrics`.

**MUST**: Métricas de costo (tokens facturables, USD, latencia) DEBEN aparecer exclusivamente en `cost_metrics`.

**MUST**: Métricas de contexto (utilización de ventana, headroom, overflow, truncation risk) DEBEN aparecer exclusivamente en `context_metrics`.

**MUST**: `prompt_tokens` PUEDE compartir el mismo valor numérico entre ambos domains (es el mismo dato físico), pero cada domain lo nombra según su semántica: `prompt_tokens` en cost, `prompt_tokens_used` en context.

#### Scenario: REQ-01-S1 — Dominios separados en JSON
```
GIVEN  una ejecución completada con feature flags habilitados
WHEN   se genera el reporte JSON
THEN   el payload DEBE incluir los objetos `cost_metrics` y `context_metrics` como keys de primer nivel en cada variant
  AND  `cost_metrics` NO DEBE contener campos definidos exclusivamente en la tabla 3.2
  AND  `context_metrics` NO DEBE contener campos definidos exclusivamente en la tabla 3.1
```

#### Scenario: REQ-01-S2 — Dominios separados en CLI
```
GIVEN  una ejecución completada con feature flags habilitados
WHEN   se renderiza la salida CLI (tabla Rich)
THEN   DEBE haber secciones visuales separadas tituladas "Cost Metrics" y "Context Metrics"
  AND  cada sección DEBE contener solo los campos de su domain
```

---

### REQ-02: Métricas Absolutas y Derivadas

**MUST**: Cada domain DEBE proporcionar valores absolutos (medidos o de config) como métricas primarias.

**MUST**: Los valores derivados DEBEN calcularse con las fórmulas exactas especificadas en la Sección 3.

**MUST**: Si un valor de entrada para una fórmula es `null` o `0` (donde causaría division by zero), el valor derivado DEBE ser `null`.

#### Scenario: REQ-02-S1 — Cálculo de métricas derivadas con datos completos
```
GIVEN  prompt_tokens = 5000
  AND  completion_tokens = 1500
  AND  context_window_max_tokens = 128000
  AND  max_tokens_request = 2048
  AND  input_rate = 2.50 (USD por millón de tokens)
  AND  output_rate = 10.00 (USD por millón de tokens)
WHEN   se calculan las métricas
THEN   cost_metrics.total_tokens = 6500
  AND  cost_metrics.estimated_cost_usd = (5000 × 2.50 + 1500 × 10.00) / 1_000_000 = 0.0275
  AND  context_metrics.context_utilization_pct = (5000 / 128000) × 100 = 3.90625
  AND  context_metrics.headroom_tokens = 128000 - 5000 = 123000
  AND  context_metrics.safe_headroom_tokens = 128000 - 5000 - 2048 = 120952
  AND  context_metrics.overflow = false
  AND  context_metrics.overflow_tokens = 0
  AND  context_metrics.truncation_risk = "low"
```

#### Scenario: REQ-02-S2 — Context window desconocido
```
GIVEN  prompt_tokens_used = 5000
  AND  context_window_max_tokens = null
WHEN   se calculan context_metrics
THEN   context_utilization_pct = null
  AND  headroom_tokens = null
  AND  safe_headroom_tokens = null
  AND  overflow = false
  AND  overflow_tokens = 0
  AND  truncation_risk = "unknown"
```

#### Scenario: REQ-02-S3 — Division by zero en context window = 0
```
GIVEN  prompt_tokens_used = 5000
  AND  context_window_max_tokens = 0
WHEN   se calcula context_utilization_pct
THEN   context_utilization_pct = null
  AND  headroom_tokens = 0
  AND  safe_headroom_tokens = 0
  AND  overflow = true
  AND  overflow_tokens = 5000
  AND  truncation_risk = "unknown"
```

---

### REQ-03: Costo USD Configurable

**MUST**: El sistema DEBE calcular `estimated_cost_usd` a partir de tokens × rate configurable.

**MUST**: Los rates DEBEN ser configurables en `eval.yaml` bajo una sección `cost_map`, indexada por modelo.

**MUST**: Si no hay rate configurado para un modelo, `estimated_cost_usd` DEBE ser `null` (no `0`, no omitido).

**MUST NOT**: El sistema NO DEBE fallar si falta el cost_map o el modelo no está mapeado.

#### Formato de configuración en `eval.yaml`

```yaml
cost_map:
  "gpt-4o":
    input_rate_per_million: 2.50
    output_rate_per_million: 10.00
  "claude-sonnet-4-20250514":
    input_rate_per_million: 3.00
    output_rate_per_million: 15.00
  # Modelo sin entry → estimated_cost_usd será null
```

#### Scenario: REQ-03-S1 — Cálculo de costo con rate disponible
```
GIVEN  modelo = "gpt-4o"
  AND  cost_map contiene "gpt-4o" con input_rate=2.50, output_rate=10.00
  AND  prompt_tokens = 10000
  AND  completion_tokens = 2000
WHEN   se calcula estimated_cost_usd
THEN   estimated_cost_usd = (10000 × 2.50 + 2000 × 10.00) / 1_000_000 = 0.045
```

#### Scenario: REQ-03-S2 — Rate no disponible
```
GIVEN  modelo = "llama-3.1-70b"
  AND  cost_map NO contiene "llama-3.1-70b"
WHEN   se calcula estimated_cost_usd
THEN   estimated_cost_usd = null
  AND  cost_metrics.data_quality = "measured" (tokens sí existen, solo falta rate)
```

#### Scenario: REQ-03-S3 — cost_map ausente de config
```
GIVEN  eval.yaml NO contiene sección cost_map
WHEN   se calcula estimated_cost_usd para cualquier modelo
THEN   estimated_cost_usd = null para todos los modelos
  AND  el sistema NO DEBE emitir error ni warning por ausencia de cost_map
```

---

### REQ-04: Feature Flags (Opt-in, Default Off)

**MUST**: Las métricas extendidas DEBEN estar desactivadas por defecto.

**MUST**: Activación vía CLI flag `--collect-usage-metrics` o config YAML `output.include_usage_metrics: true`.

**MUST**: El flag CLI DEBE tener precedencia sobre el YAML config.

**MUST**: Si ambos flags están off, el output JSON y CLI DEBE ser idéntico al formato legacy actual (backward compat estricta — cero campos nuevos en el payload).

**MUST NOT**: Cuando los flags están off, NO DEBE haber recolección de métricas extendidas (ni overhead de procesamiento adicional).

#### Mecanismos de activación

| Mecanismo | Sintaxis | Default |
|-----------|---------|---------|
| CLI flag ON | `--collect-usage-metrics` | — |
| CLI flag OFF | `--no-collect-usage-metrics` | Este es el default implícito |
| YAML config | `output.include_usage_metrics: true` | `false` |

#### Precedencia

```
CLI flag explícito > YAML config > default (false)
```

#### Scenario: REQ-04-S1 — Flags off: output idéntico a legacy
```
GIVEN  --collect-usage-metrics NO fue pasado
  AND  output.include_usage_metrics = false (o ausente) en eval.yaml
WHEN   se ejecuta una evaluación
THEN   el JSON de resultado DEBE ser idéntico byte-a-byte en estructura al formato legacy
  AND  NO DEBE existir `cost_metrics`, `context_metrics`, ni `usage_metrics` en el payload
  AND  los campos legacy (tokens, duration_ms) DEBEN seguir presentes
```

#### Scenario: REQ-04-S2 — Flag habilitado via CLI
```
GIVEN  --collect-usage-metrics fue pasado en CLI
  AND  output.include_usage_metrics = false en eval.yaml
WHEN   se ejecuta una evaluación
THEN   el output DEBE incluir cost_metrics y context_metrics
  AND  CLI flag tiene precedencia sobre YAML
```

#### Scenario: REQ-04-S3 — Flag habilitado via YAML
```
GIVEN  --collect-usage-metrics NO fue pasado en CLI (ni --no-collect-usage-metrics)
  AND  output.include_usage_metrics = true en eval.yaml
WHEN   se ejecuta una evaluación
THEN   el output DEBE incluir cost_metrics y context_metrics
```

#### Scenario: REQ-04-S4 — CLI override explícito desactiva YAML
```
GIVEN  --no-collect-usage-metrics fue pasado en CLI
  AND  output.include_usage_metrics = true en eval.yaml
WHEN   se ejecuta una evaluación
THEN   el output NO DEBE incluir cost_metrics ni context_metrics
  AND  el output DEBE ser formato legacy
```

---

### REQ-05: Stage Breakdown para Modo Orquestador

**MUST**: En modo orquestador, cada llamada LLM DEBE estar etiquetada con un `stage_type`.

**MUST**: Valores válidos de `stage_type`: `planner`, `router`, `tool_call`, `synthesis`, `single_pass`.

**MUST**: El reporte DEBE incluir un array `stage_breakdown` con métricas acumuladas por etapa.

**MUST**: Los tokens de tool I/O (argumentos/respuesta no-LLM) DEBEN separarse de tokens LLM en un campo `tool_io_tokens`.

**MUST**: Cada stage entry DEBE incluir `attribution_quality`: `high` (medido directo del provider), `medium` (estimado con heurística razonable), `low` (fallback sin telemetría).

**MUST**: En modo `non_orchestrator`, DEBE haber un único stage con `stage_type = "single_pass"`.

#### Estructura por stage

```json
{
  "stage_type": "planner",
  "prompt_tokens": 2000,
  "completion_tokens": 500,
  "total_tokens": 2500,
  "tool_io_tokens": 0,
  "latency_ms": 450,
  "attribution_quality": "high"
}
```

#### Scenario: REQ-05-S1 — Stage breakdown en modo orquestador
```
GIVEN  una ejecución en modo orchestrator con 3 llamadas LLM:
       - planner: prompt=2000, completion=500
       - tool_call: prompt=1500, completion=800, tool_io=340
       - synthesis: prompt=3000, completion=1200
WHEN   se genera el reporte con feature flags habilitados
THEN   stage_breakdown DEBE tener 3 entries
  AND  stage_breakdown[0].stage_type = "planner"
  AND  stage_breakdown[0].total_tokens = 2500
  AND  stage_breakdown[1].stage_type = "tool_call"
  AND  stage_breakdown[1].tool_io_tokens = 340
  AND  la suma de total_tokens de todos los stages DEBE igualar el total_tokens del variant
```

#### Scenario: REQ-05-S2 — Non-orchestrator tiene un solo stage
```
GIVEN  una ejecución en modo non_orchestrator
WHEN   se genera el reporte con feature flags habilitados
THEN   stage_breakdown DEBE tener exactamente 1 entry
  AND  stage_breakdown[0].stage_type = "single_pass"
```

#### Scenario: REQ-05-S3 — Attribution quality con telemetría parcial
```
GIVEN  una etapa "tool_call" donde el provider NO retornó usage.prompt_tokens
WHEN   se genera la stage entry
THEN   prompt_tokens DEBE contener un valor estimado (best-effort)
  AND  attribution_quality = "low"
```

---

### REQ-06: Comparativa Orquestador vs No-Orquestador

**MUST**: El reporte DEBE incluir un bloque `comparison` con deltas side-by-side para ambos domains.

**MUST**: Los deltas DEBEN calcularse como:
- `delta_abs = orchestrator.value - non_orchestrator.value`
- `delta_pct = (delta_abs / non_orchestrator.value) × 100` (con protección division-by-zero)

**MUST**: Si un variant falta (no se ejecutó o no tiene datos), sus valores DEBEN ser `null` con un campo `reason` explicativo.

**MAY**: El reporte PUEDE incluir métricas normalizadas opcionales:
- `tokens_per_successful_case`: `total_tokens / successful_cases`
- `tokens_per_score_point`: `total_tokens / aggregate_score`

#### Scenario: REQ-06-S1 — Comparativa completa con ambos variants
```
GIVEN  orchestrator.cost_metrics.total_tokens = 8500
  AND  non_orchestrator.cost_metrics.total_tokens = 5000
WHEN   se calculan los deltas
THEN   comparison.cost_metrics.total_tokens.delta_abs = 3500
  AND  comparison.cost_metrics.total_tokens.delta_pct = 70.0
```

#### Scenario: REQ-06-S2 — Variant faltante
```
GIVEN  solo se ejecutó non_orchestrator
  AND  orchestrator NO fue ejecutado
WHEN   se genera el bloque comparison
THEN   comparison DEBE existir
  AND  orchestrator values DEBEN ser null
  AND  cada métrica con null DEBE incluir reason = "variant_not_executed"
  AND  delta_abs = null
  AND  delta_pct = null
```

#### Scenario: REQ-06-S3 — Division by zero en delta_pct
```
GIVEN  non_orchestrator.cost_metrics.total_tokens = 0
  AND  orchestrator.cost_metrics.total_tokens = 5000
WHEN   se calcula delta_pct
THEN   delta_pct = null
  AND  delta_pct_reason = "baseline_zero"
  AND  delta_abs = 5000
```

#### Scenario: REQ-06-S4 — Métricas normalizadas
```
GIVEN  orchestrator.cost_metrics.total_tokens = 8500
  AND  orchestrator tuvo 10 cases exitosos
  AND  orchestrator aggregate_score = 85.0
WHEN   se calculan métricas normalizadas
THEN   tokens_per_successful_case = 850
  AND  tokens_per_score_point = 100.0
```

---

### REQ-07: Backward Compatibility

**MUST**: Los campos legacy existentes en `ExecutionResult` y el JSON de salida DEBEN permanecer con nombres, tipos y semántica idénticos.

**MUST**: El campo legacy `tokens` en `LLMResponse` DEBE seguir conteniendo `completion_tokens` (comportamiento actual).

**MUST**: El campo legacy `duration_ms` DEBE seguir presente.

**MUST**: Los nuevos campos son estrictamente aditivos — nunca remueven ni renombran campos existentes.

**MUST**: Un consumer que parsea el JSON legacy DEBE poder seguir haciéndolo sin modificar su código, independientemente del estado de los feature flags.

#### Scenario: REQ-07-S1 — Consumer legacy con flags off
```
GIVEN  un script que lee results.json y accede a result.tokens y result.duration_ms
  AND  --collect-usage-metrics NO está habilitado
WHEN   se ejecuta con la versión actualizada de md-evals
THEN   el script DEBE funcionar sin cambios
  AND  el JSON DEBE tener estructura idéntica a la versión anterior
```

#### Scenario: REQ-07-S2 — Consumer legacy con flags on
```
GIVEN  un script que lee results.json y accede SOLO a result.tokens y result.duration_ms
  AND  --collect-usage-metrics está habilitado
WHEN   se ejecuta con la versión actualizada de md-evals
THEN   result.tokens y result.duration_ms DEBEN seguir presentes con mismos valores
  AND  los campos nuevos (cost_metrics, context_metrics) son keys adicionales que el script puede ignorar
```

---

### REQ-08: Definición de Overflow

**MUST**: `overflow` es un booleano: `prompt_tokens_used > context_window_max_tokens`.

**MUST**: `overflow_tokens = max(prompt_tokens_used - context_window_max_tokens, 0)`.

**MUST**: Si `context_window_max_tokens` es `null`, `overflow = false` y `overflow_tokens = 0` (no se puede determinar overflow sin conocer la ventana).

**MUST**: Si `context_window_max_tokens = 0`, `overflow = true` si `prompt_tokens_used > 0`, `overflow_tokens = prompt_tokens_used`.

#### Scenario: REQ-08-S1 — Overflow detectado
```
GIVEN  prompt_tokens_used = 140000
  AND  context_window_max_tokens = 128000
WHEN   se calculan context_metrics
THEN   overflow = true
  AND  overflow_tokens = 12000
  AND  headroom_tokens = 0
  AND  truncation_risk = "high"
```

#### Scenario: REQ-08-S2 — Sin overflow
```
GIVEN  prompt_tokens_used = 5000
  AND  context_window_max_tokens = 128000
WHEN   se calculan context_metrics
THEN   overflow = false
  AND  overflow_tokens = 0
  AND  headroom_tokens = 123000
```

#### Scenario: REQ-08-S3 — Window desconocido
```
GIVEN  prompt_tokens_used = 5000
  AND  context_window_max_tokens = null
WHEN   se calculan context_metrics
THEN   overflow = false
  AND  overflow_tokens = 0
  AND  truncation_risk = "unknown"
```

---

## 5. Ejemplo JSON Canónico

Ejemplo completo mostrando ambos domains, ambos variants, stage breakdown, comparison y quality flags.

```json
{
  "experiment_id": "eval_20260315_143022",
  "timestamp": "2026-03-15T14:30:22Z",
  "config": {
    "name": "skill-evaluation",
    "version": "1.0"
  },
  "report_schema_version": "2.0",
  "feature_flags": {
    "include_usage_metrics": true
  },

  "results": [
    {
      "treatment": "WITH_SKILL",
      "test": "react_component_test",
      "prompt": "Create a React component...",
      "response": "Here is the component...",
      "passed": true,
      "evaluators": [
        {
          "name": "has_jsx",
          "passed": true,
          "score": 1.0,
          "reason": null
        }
      ],
      "tokens": 1200,
      "duration_ms": 2340,
      "timestamp": "2026-03-15T14:30:25Z"
    }
  ],

  "summary": {
    "CONTROL": { "total": 5, "passed": 3, "pass_rate": 0.6 },
    "WITH_SKILL": { "total": 5, "passed": 4, "pass_rate": 0.8 }
  },

  "usage_metrics": {
    "model": "gpt-4o",
    "provider": "openai",
    "context_window_max_tokens": 128000,
    "max_tokens_request": 2048,

    "variants": {
      "non_orchestrator": {
        "pipeline_mode": "non_orchestrator",

        "cost_metrics": {
          "prompt_tokens": 25000,
          "completion_tokens": 6000,
          "total_tokens": 31000,
          "estimated_cost_usd": 0.1225,
          "latency_ms": 11500,
          "data_quality": "measured"
        },

        "context_metrics": {
          "prompt_tokens_used": 25000,
          "context_window_max_tokens": 128000,
          "context_utilization_pct": 19.53,
          "headroom_tokens": 103000,
          "safe_headroom_tokens": 100952,
          "max_tokens_request": 2048,
          "overflow": false,
          "overflow_tokens": 0,
          "truncation_risk": "low",
          "data_quality": "measured"
        },

        "stage_breakdown": [
          {
            "stage_type": "single_pass",
            "prompt_tokens": 25000,
            "completion_tokens": 6000,
            "total_tokens": 31000,
            "tool_io_tokens": 0,
            "latency_ms": 11500,
            "attribution_quality": "high"
          }
        ]
      },

      "orchestrator": {
        "pipeline_mode": "orchestrator",

        "cost_metrics": {
          "prompt_tokens": 32000,
          "completion_tokens": 8500,
          "total_tokens": 40500,
          "estimated_cost_usd": 0.165,
          "latency_ms": 15200,
          "data_quality": "measured"
        },

        "context_metrics": {
          "prompt_tokens_used": 32000,
          "context_window_max_tokens": 128000,
          "context_utilization_pct": 25.0,
          "headroom_tokens": 96000,
          "safe_headroom_tokens": 93952,
          "max_tokens_request": 2048,
          "overflow": false,
          "overflow_tokens": 0,
          "truncation_risk": "low",
          "data_quality": "measured"
        },

        "stage_breakdown": [
          {
            "stage_type": "planner",
            "prompt_tokens": 8000,
            "completion_tokens": 2000,
            "total_tokens": 10000,
            "tool_io_tokens": 0,
            "latency_ms": 3200,
            "attribution_quality": "high"
          },
          {
            "stage_type": "router",
            "prompt_tokens": 4000,
            "completion_tokens": 500,
            "total_tokens": 4500,
            "tool_io_tokens": 0,
            "latency_ms": 1800,
            "attribution_quality": "high"
          },
          {
            "stage_type": "tool_call",
            "prompt_tokens": 6000,
            "completion_tokens": 3000,
            "total_tokens": 9000,
            "tool_io_tokens": 1200,
            "latency_ms": 5400,
            "attribution_quality": "medium"
          },
          {
            "stage_type": "synthesis",
            "prompt_tokens": 14000,
            "completion_tokens": 3000,
            "total_tokens": 17000,
            "tool_io_tokens": 0,
            "latency_ms": 4800,
            "attribution_quality": "high"
          }
        ]
      }
    },

    "comparison": {
      "cost_metrics": {
        "prompt_tokens": {
          "orchestrator": 32000,
          "non_orchestrator": 25000,
          "delta_abs": 7000,
          "delta_pct": 28.0
        },
        "completion_tokens": {
          "orchestrator": 8500,
          "non_orchestrator": 6000,
          "delta_abs": 2500,
          "delta_pct": 41.67
        },
        "total_tokens": {
          "orchestrator": 40500,
          "non_orchestrator": 31000,
          "delta_abs": 9500,
          "delta_pct": 30.65
        },
        "estimated_cost_usd": {
          "orchestrator": 0.165,
          "non_orchestrator": 0.1225,
          "delta_abs": 0.0425,
          "delta_pct": 34.69
        },
        "latency_ms": {
          "orchestrator": 15200,
          "non_orchestrator": 11500,
          "delta_abs": 3700,
          "delta_pct": 32.17
        }
      },
      "context_metrics": {
        "prompt_tokens_used": {
          "orchestrator": 32000,
          "non_orchestrator": 25000,
          "delta_abs": 7000,
          "delta_pct": 28.0
        },
        "context_utilization_pct": {
          "orchestrator": 25.0,
          "non_orchestrator": 19.53,
          "delta_abs": 5.47,
          "delta_pct": 28.01
        },
        "headroom_tokens": {
          "orchestrator": 96000,
          "non_orchestrator": 103000,
          "delta_abs": -7000,
          "delta_pct": -6.80
        },
        "safe_headroom_tokens": {
          "orchestrator": 93952,
          "non_orchestrator": 100952,
          "delta_abs": -7000,
          "delta_pct": -6.93
        },
        "overflow": {
          "orchestrator": false,
          "non_orchestrator": false,
          "delta_abs": null,
          "delta_pct": null,
          "delta_pct_reason": "boolean_metric"
        }
      },
      "normalized": {
        "tokens_per_successful_case": {
          "orchestrator": 10125.0,
          "non_orchestrator": 10333.33,
          "delta_abs": -208.33,
          "delta_pct": -2.02
        },
        "tokens_per_score_point": {
          "orchestrator": 506.25,
          "non_orchestrator": 516.67,
          "delta_abs": -10.42,
          "delta_pct": -2.02
        }
      }
    },

    "quality_flags": {
      "attribution_coverage": "full",
      "provider_telemetry": "complete",
      "cost_map_available": true,
      "warnings": []
    }
  }
}
```

**Notas del ejemplo**:
- Los campos `results`, `summary` son **legacy** — siempre presentes, nunca cambian estructura.
- El bloque `usage_metrics` es **nuevo** — solo aparece si feature flags están habilitados.
- `report_schema_version` y `feature_flags` son metadata de versión.
- La suma de `total_tokens` en `stage_breakdown` del orchestrator (10000 + 4500 + 9000 + 17000 = 40500) iguala el `total_tokens` del variant.

---

## 6. Edge Cases

### EC-01: Division by zero en `context_utilization_pct`
```
GIVEN  context_window_max_tokens = 0
WHEN   se calcula context_utilization_pct
THEN   context_utilization_pct = null
  AND  truncation_risk = "unknown"
```

### EC-02: Division by zero en `delta_pct`
```
GIVEN  non_orchestrator.total_tokens = 0
WHEN   se calcula delta_pct
THEN   delta_pct = null
  AND  delta_pct_reason = "baseline_zero"
  AND  delta_abs = orchestrator.total_tokens (valor absoluto, no null)
```

### EC-03: Overflow con prompt_tokens negativos (inválido)
```
GIVEN  prompt_tokens_used = -100 (dato corrupto del provider)
WHEN   se calculan context_metrics
THEN   prompt_tokens_used DEBE clampearse a 0
  AND  data_quality = "estimated"
  AND  overflow = false
  AND  overflow_tokens = 0
```

### EC-04: Telemetría parcial del provider
```
GIVEN  provider retorna usage.completion_tokens pero NO usage.prompt_tokens
WHEN   se construyen cost_metrics y context_metrics
THEN   completion_tokens = valor del provider
  AND  prompt_tokens = null (o estimado si hay heurística)
  AND  data_quality = "estimated" si se estimó, "unavailable" si no se pudo
  AND  todas las métricas derivadas que dependen de prompt_tokens = null
```

### EC-05: Variant faltante (solo uno ejecutado)
```
GIVEN  solo se ejecutó non_orchestrator
WHEN   se genera comparison
THEN   comparison DEBE existir
  AND  todos los campos orchestrator = null
  AND  todos los delta_abs = null
  AND  todos los delta_pct = null
  AND  reason = "variant_not_executed" en cada métrica
```

### EC-06: Rate map faltante para el modelo
```
GIVEN  cost_map no incluye el modelo usado
WHEN   se calcula estimated_cost_usd
THEN   estimated_cost_usd = null
  AND  todos los demás campos de cost_metrics con tokens DEBEN estar presentes normalmente
  AND  quality_flags.cost_map_available = false
```

### EC-07: Context window desconocido
```
GIVEN  model registry no tiene context_window_max_tokens para el modelo
WHEN   se calculan context_metrics
THEN   context_window_max_tokens = null
  AND  context_utilization_pct = null
  AND  headroom_tokens = null
  AND  safe_headroom_tokens = null
  AND  overflow = false
  AND  overflow_tokens = 0
  AND  truncation_risk = "unknown"
```

### EC-08: Feature flags off — cero regresión
```
GIVEN  include_usage_metrics = false (default)
WHEN   se ejecuta cualquier evaluación
THEN   el JSON de salida DEBE tener exactamente las mismas keys que la versión anterior
  AND  NO DEBE existir la key "usage_metrics"
  AND  NO DEBE existir la key "report_schema_version"
  AND  NO DEBE existir la key "feature_flags"
```

### EC-09: Stage breakdown con sumas inconsistentes
```
GIVEN  stage_breakdown entries suman total_tokens = 40000
  AND  el variant reporta total_tokens = 40500
WHEN   se genera el reporte
THEN   quality_flags DEBE incluir warning "stage_sum_mismatch"
  AND  attribution_coverage = "partial"
```

### EC-10: Boolean metric en comparison delta
```
GIVEN  orchestrator.overflow = true
  AND  non_orchestrator.overflow = false
WHEN   se calcula delta para overflow
THEN   delta_abs = null (no aplica a booleanos)
  AND  delta_pct = null
  AND  delta_pct_reason = "boolean_metric"
```

---

## 7. Impacto en Código Existente

Referencia del estado actual relevante para la implementación:

| Archivo | Estado Actual | Cambio Requerido |
|---------|---------------|------------------|
| `md_evals/models.py` | `LLMResponse.tokens: int` = solo `completion_tokens` | Agregar `prompt_tokens`, `completion_tokens` (nombrados), mantener `tokens` legacy |
| `md_evals/models.py` | `OutputConfig` sin `include_usage_metrics` | Agregar campo `include_usage_metrics: bool = False` |
| `md_evals/models.py` | `EvalConfig` sin `cost_map` | Agregar campo `cost_map: dict[str, CostRate] = {}` |
| `md_evals/llm.py` | Solo extrae `completion_tokens` del provider | Extraer también `prompt_tokens`, `total_tokens` de `response.usage` |
| `md_evals/cli.py` | Sin flag `--collect-usage-metrics` | Agregar flag al comando `run` con precedencia sobre YAML |
| `md_evals/reporter.py` | `_build_output_data()` retorna formato plano | Condicional: si flag on → agregar bloque `usage_metrics` |
| `md_evals/reporter.py` | `report_terminal()` sin secciones de métricas | Condicional: si flag on → renderizar secciones Cost/Context |

---

## 8. Acceptance Criteria

Checklist verificable. Cada item es un test que DEBE pasar.

- [ ] **AC-01**: JSON con flags on contiene `cost_metrics` y `context_metrics` como objetos separados sin campos mezclados.
- [ ] **AC-02**: JSON con flags off es structurally idéntico al formato legacy (no keys nuevas).
- [ ] **AC-03**: `estimated_cost_usd` se calcula correctamente con rates de `cost_map` y es `null` sin rate.
- [ ] **AC-04**: `context_utilization_pct` = `(prompt_tokens_used / context_window_max_tokens) × 100`, `null` si denominador es 0 o null.
- [ ] **AC-05**: `headroom_tokens` = `max(window - used, 0)`, `null` si window desconocido.
- [ ] **AC-06**: `safe_headroom_tokens` = `max(window - used - max_tokens_request, 0)`, `null` si window desconocido.
- [ ] **AC-07**: `overflow` = `true` sii `prompt_tokens_used > context_window_max_tokens` (y window conocido).
- [ ] **AC-08**: `overflow_tokens` = `max(used - window, 0)`, `0` si window desconocido.
- [ ] **AC-09**: `truncation_risk` asignado por umbrales: <70%→low, 70-90%→medium, ≥90%→high, desconocido→unknown.
- [ ] **AC-10**: Stage breakdown presente en ambos variants: single stage para no-orq, múltiples para orq.
- [ ] **AC-11**: Suma de `total_tokens` en stage_breakdown = variant `total_tokens` (o warning si mismatch).
- [ ] **AC-12**: `attribution_quality` presente en cada stage entry.
- [ ] **AC-13**: Comparison block tiene deltas para ambos domains con `delta_abs` y `delta_pct`.
- [ ] **AC-14**: Variant faltante → nulls con `reason` en comparison.
- [ ] **AC-15**: Division by zero → `null` con `reason` (nunca crash, nunca `Infinity`, nunca `NaN`).
- [ ] **AC-16**: CLI flag `--collect-usage-metrics` / `--no-collect-usage-metrics` funciona con precedencia sobre YAML.
- [ ] **AC-17**: Legacy fields (`tokens`, `duration_ms`) presentes e invariados independientemente de feature flags.
- [ ] **AC-18**: `data_quality` flag presente en ambos domains indicando `measured`/`estimated`/`unavailable`.
- [ ] **AC-19**: `cost_map` ausente o modelo no mapeado → `estimated_cost_usd = null`, sin error.
- [ ] **AC-20**: `context_window_max_tokens` desconocido → todos los derivados de contexto son `null`/default seguro.

---

## 9. Fuera de Scope

Los siguientes items están explícitamente excluidos de esta spec:

- Umbrales configurables de `truncation_risk` (hardcoded en esta versión).
- Agregaciones estadísticas (media, mediana, p90, desviación estándar) — se definirán en spec aparte.
- Persistencia de métricas en base de datos.
- Dashboard o visualización web.
- Integración con proveedores de billing reales (solo estimación local).
- Orquestador real (esta spec define el modelo de datos; la implementación del orquestador es spec aparte).
- Soporte para múltiples modelos en una misma ejecución (se asume un modelo por run).
