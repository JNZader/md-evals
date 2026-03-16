# Proposal: md-evals

## Intent
Create `md-evals`, a lightweight, local, model-agnostic CLI tool built in Python using LiteLLM to evaluate the effectiveness of Markdown-based AI skills (`SKILL.md`). The tool aims to provide developers with a reliable way to test and iterate on their AI agent skills by comparing performance with and without the skill context, while enforcing best practices for skill design.

## Scope
- **CLI Application**: Build a Python-based command-line interface.
- **Model Agnostic**: Integrate LiteLLM to support multiple LLM providers (OpenAI, Anthropic, Gemini, local models, etc.).
- **A/B Testing Framework**: Evaluate prompts in "Control" (without skill) vs. "Skill" (with `SKILL.md` context) scenarios.
- **Hybrid Evaluation Engine**: 
  - Regex/deterministic assertions for precise checks.
  - LLM-as-a-judge for qualitative assessments.
- **Skill Health Check (Linter)**: Automatically validate `SKILL.md` files. Crucially, the tool will warn the user or fail the evaluation if the skill file exceeds 400 lines, enforcing concise "Encoded Preferences".

## Approach
- **Language/Framework**: Python with Click or Typer for the CLI interface.
- **LLM Integration**: Use `litellm` library for standardizing API calls across different providers.
- **Configuration**: Use YAML or JSON files to define evaluation suites (test cases, assertions, judge criteria).
- **Execution Flow**:
  1. Parse evaluation suite and load `SKILL.md`.
  2. Run the Health Check/Linter on `SKILL.md` (check < 400 lines constraint).
  3. Execute Control prompt (no skill).
  4. Execute Skill prompt (with skill injected).
  5. Run Hybrid Evaluation Engine (Regex + LLM Judge) on both outputs.
  6. Generate a comparison report (CLI output + optional JSON/Markdown report).

## Risks
- **LLM Judge Variability**: LLM-as-a-judge can be non-deterministic. *Mitigation*: Support multiple judge runs, use strong models for judging, and rely heavily on deterministic regex assertions where possible.
- **Provider API Changes/Errors**: Rate limits or API instability from LLM providers. *Mitigation*: Implement robust retry logic and error handling using LiteLLM's built-in features.
- **Performance**: Evaluating many cases sequentially might be slow. *Mitigation*: Implement concurrent evaluation execution using `asyncio`.

## Success Criteria
- The CLI can successfully execute an evaluation suite against at least two different LLM providers via LiteLLM.
- The A/B testing mechanism clearly outputs metrics comparing the Control vs. Skill performance.
- The Hybrid Evaluation Engine correctly processes both regex assertions and LLM judge criteria.
- **The Skill Health Check accurately identifies and flags `SKILL.md` files exceeding 400 lines**, providing clear feedback to the user.
- The tool can be easily installed and run locally with minimal dependencies.

## Extension: Comparative Context Window Analysis (Orchestrator vs Non-Orchestrator)

### 1) Definicion operativa de `orquestador`
- **Modo `no-orq`**: flujo monolitico de una sola llamada principal de generacion por test case/treatment, sin etapas explicitas de planificacion o ruteo.
- **Modo `orq`**: flujo multi-etapa con al menos dos fases semanticas separadas antes de la salida final (por ejemplo: `planner` -> `router` -> `executor/tool` -> `synthesis`).
- **Representacion cuando aun no existe un orquestador explicito**: usar una estructura logica de etapas en metadatos de ejecucion (`pipeline_mode` y `stage_type`) aunque internamente siga siendo un flujo simple. Esto permite comparar hoy y evolucionar despues sin romper el modelo de datos.

### 2) Esquema de metricas comparables entre modos (`no-orq` vs `orq`)
- **Metricas base por corrida**: `input_tokens`, `output_tokens`, `total_tokens`, `prompt_chars`, `latency_ms`, `success/failure`.
- **Metricas de contexto**:
  - `context_window_max_tokens` (capacidad del modelo),
  - `context_window_used_tokens` (estimado o reportado),
  - `context_window_utilization_pct = used / max`.
- **Metricas normalizadas para comparabilidad**:
  - `tokens_per_successful_case`,
  - `tokens_per_score_point` (si hay score de evaluador),
  - `latency_per_1k_tokens`.
- **Agregaciones por modo**: media, mediana, p90, desviacion estandar, tasa de overflow de contexto, tasa de error.
- **Comparativa directa**: `delta_abs` y `delta_pct` para cada metrica entre `orq` y `no-orq` sobre el mismo set de casos.

### 3) Aislamiento y atribucion de tokens por etapa
- **Taxonomia de etapas** (obligatoria en metadatos): `planner`, `router`, `tool_call`, `synthesis`, `single_pass`.
- **Regla de atribucion primaria**: cada llamada LLM se etiqueta con `stage_type`; sus tokens se acumulan solo en esa etapa.
- **Regla para tool calls**:
  - Tokens de argumentos/respuesta no LLM van a `tool_io_chars` (o `tool_io_tokens_est`) separado de tokens LLM.
  - Si una tool call dispara LLM interno, ese consumo se registra como `tool_call.llm_tokens`.
- **Regla de no mezcla**: metricas globales se calculan como suma de etapas homogeneas; nunca comparar `single_pass` contra `planner+router+synthesis` sin presentar composicion.
- **Fallback sin telemetria fina**: marcar `attribution_quality = low|medium|high` y separar resultados estimados vs medidos.

### 4) Diseno de reporte comparativo (tabla/JSON) con deltas
- **Tabla CLI/Markdown (por modo y global)**:
  - columnas minimas: `mode`, `cases`, `success_rate`, `avg_total_tokens`, `p90_total_tokens`, `avg_ctx_util_pct`, `overflow_rate`, `avg_latency_ms`, `delta_vs_baseline_pct`.
- **Tabla de breakdown por etapa** (solo `orq`): `stage_type`, `avg_tokens`, `share_pct`, `avg_latency_ms`.
- **JSON estable para automatizacion**:
  - `metadata`: modelo, provider, fecha, commit/config hash,
  - `modes`: bloque `no-orq` y `orq` con metricas agregadas,
  - `stage_breakdown`: arreglo por etapa,
  - `deltas`: `{metric: {abs, pct, better_mode}}`,
  - `quality_flags`: cobertura, calidad de atribucion, warnings de comparabilidad.

### 5) Plan de instrumentacion minima (sin romper compatibilidad)
- **Fase 1 (backward-compatible)**:
  - agregar campos opcionales en resultados (`pipeline_mode`, `stage_metrics`, `context_window_*`, `attribution_quality`),
  - default conservador: `pipeline_mode = no-orq`, `stage_type = single_pass`.
- **Fase 2**:
  - capturar tokens por llamada desde provider si esta disponible,
  - fallback a estimador existente cuando provider no retorna uso real.
- **Fase 3**:
  - reporter: vistas comparativas + JSON extendido con versionado de schema,
  - feature flag/config para habilitar comparativa orquestador sin afectar ejecuciones actuales.
- **Compatibilidad**:
  - no eliminar campos actuales,
  - no cambiar semantica de `total_tokens` existente,
  - versionar payload (`report_schema_version`) para consumidores externos.

### 6) Sesgos principales en benchmarks y mitigaciones
- **Sesgo de complejidad de tarea**: orquestador puede ayudar mas en tareas complejas.
  - *Mitigacion*: estratificar benchmark por complejidad y reportar por estrato.
- **Sesgo de longitud de prompt inicial**: prompts largos penalizan distinto a cada modo.
  - *Mitigacion*: controlar distribucion de longitud y usar metricas normalizadas.
- **Sesgo de no determinismo del modelo**: varianza de salida/consumo entre corridas.
  - *Mitigacion*: N repeticiones por caso, semillas/temperatura controladas, intervalos de confianza.
- **Sesgo de caching/warm-start**: segunda corrida puede ser mas barata o rapida.
  - *Mitigacion*: randomizar orden de ejecucion y alternar modos por lote.
- **Sesgo de herramientas externas**: tool latency/size puede inflar costos del modo `orq`.
  - *Mitigacion*: separar `llm_tokens` de `tool_io`, y reportar costo total + costo LLM puro.
- **Sesgo de comparacion injusta de calidad**: menor token no siempre es mejor.
  - *Mitigacion*: reportar eficiencia condicionada a calidad minima (score threshold) y no solo costo.
