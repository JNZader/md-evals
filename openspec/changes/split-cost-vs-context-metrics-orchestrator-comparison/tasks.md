# Tasks: split-cost-vs-context-metrics-orchestrator-comparison

**Spec**: [`spec.md`](./spec.md)  
**Design**: [`design.md`](./design.md)  
**Estimación total**: ~2-3 días  
**Total**: 6 fases, 19 tareas

---

## Fase 1: Modelo de Datos (dataclasses, enums en metrics.py)

Fundación sin efecto observable. Todo detrás de flag off. Cero impacto en el pipeline actual.

### T-01: Crear `md_evals/metrics.py` con enums

- [ ] **Crear enums `DataQuality`, `TruncationRisk`, `AttributionQuality`**
- **Archivos**: `md_evals/metrics.py` (NUEVO)
- **Qué hace**: Crear el archivo `metrics.py` con los 3 enums (`str, Enum`) definidos en design §2.1. `DataQuality` = measured/estimated/unavailable. `TruncationRisk` = low/medium/high/unknown. `AttributionQuality` = high/medium/low.
- **Dependencias**: Ninguna (es la primera tarea)
- **Criterio de done**: `from md_evals.metrics import DataQuality, TruncationRisk, AttributionQuality` funciona sin error. Cada enum hereda de `str, Enum` para serialización JSON directa.
- **Esfuerzo**: S

### T-02: Crear dataclasses de métricas en `metrics.py`

- [ ] **Agregar `TokenUsage`, `CostMetrics`, `ContextMetrics`, `StageMetrics`, `VariantMetrics`, `MetricDelta`, `CostRate`**
- **Archivos**: `md_evals/metrics.py`
- **Qué hace**: Definir las 7 dataclasses del design §2.1 con todos los campos, tipos y defaults. `TokenUsage` y `CostRate` son `frozen=True`. `VariantMetrics` usa `field(default_factory=...)` para los contenedores mutables.
- **Dependencias**: T-01 (necesita los enums)
- **Criterio de done**: Todas las dataclasses se instancian con defaults sin argumentos (`CostMetrics()`, `ContextMetrics()`, etc.). Los tipos coinciden exactamente con la tabla de campos de spec §3.1 y §3.2. `dataclasses.asdict(CostMetrics())` produce un dict serializable a JSON.
- **Esfuerzo**: M

### T-03: Extender modelos existentes en `models.py`

- [ ] **Agregar campos nuevos a `LLMResponse`, `OutputConfig`, `EvalConfig`**
- **Archivos**: `md_evals/models.py`
- **Qué hace**: 
  - `LLMResponse`: agregar `prompt_tokens: int | None = None`, `completion_tokens_detail: int | None = None`, `total_tokens: int | None = None`, `stage_type: str = "single_pass"`.
  - `OutputConfig`: agregar `include_usage_metrics: bool = False`.
  - `EvalConfig`: agregar `cost_map: dict[str, dict[str, float]] = Field(default_factory=dict)`, `context_window_overrides: dict[str, int] = Field(default_factory=dict)`.
- **Dependencias**: Ninguna (no depende de metrics.py)
- **Criterio de done**: 
  - `LLMResponse(content="x", model="m", provider="p").stage_type == "single_pass"` y `.prompt_tokens is None`.
  - `OutputConfig().include_usage_metrics == False`.
  - `EvalConfig(name="test").cost_map == {}`.
  - Tests existentes de models siguen pasando (campos nuevos son opcionales con defaults).
- **Esfuerzo**: S

---

## Fase 2: Captura de Tokens (LLMAdapter + resolución context_window)

Los datos empiezan a fluir en `LLMResponse`, pero aún no se reportan (flag off por defecto).

### T-04: Modificar `LLMAdapter.complete()` para capturar prompt_tokens

- [ ] **Extraer `prompt_tokens`, `completion_tokens`, `total_tokens` de `response.usage`**
- **Archivos**: `md_evals/llm.py`
- **Qué hace**: En el método `complete()` (líneas ~99-111), extraer `response.usage.prompt_tokens` y `response.usage.completion_tokens` con `getattr()` seguro. Calcular `total_tokens = prompt + completion` si ambos disponibles. Clampear negativos a 0 (EC-03 de spec). Determinar `data_quality` (measured/estimated/unavailable). El campo legacy `tokens` sigue siendo `completion_tokens or 0` — intacto. Agregar parámetro `stage_type: str = "single_pass"` al método `complete()`.
- **Dependencias**: T-03 (LLMResponse tiene los campos nuevos)
- **Criterio de done**: 
  - Una llamada a `complete()` con un response de litellm que tiene `usage.prompt_tokens=100` retorna `LLMResponse` con `prompt_tokens=100`.
  - El campo `tokens` (legacy) sigue siendo `completion_tokens`.
  - Con `prompt_tokens=-50` del provider → se clampea a `0`.
  - Tests existentes en `tests/test_llm.py` siguen pasando.
- **Esfuerzo**: S

### T-05: Modificar `GitHubModelsProvider` para capturar prompt_tokens

- [ ] **Extraer `prompt_tokens` de `response.usage` en el provider de GitHub Models**
- **Archivos**: `md_evals/providers/github_models.py`
- **Qué hace**: En el método que construye `LLMResponse` (buscar donde se setea `tokens=...`), poblar también `prompt_tokens`, `completion_tokens_detail`, `total_tokens` desde la respuesta del provider. Misma lógica de clamp y data_quality que T-04.
- **Dependencias**: T-03 (LLMResponse extendido), T-04 (patrón de captura a seguir)
- **Criterio de done**: Un mock de respuesta de GitHub Models con `usage.prompt_tokens` produce un `LLMResponse` con campos nuevos poblados. Tests existentes en `tests/test_github_models_provider.py` siguen pasando.
- **Esfuerzo**: S

### T-06: Implementar `resolve_context_window()`

- [ ] **Crear la función de resolución de context window con cadena de fallback**
- **Archivos**: `md_evals/metrics.py`
- **Qué hace**: Implementar `resolve_context_window(model, provider, config) -> int | None` con la cadena de fallback del ADR-02: (1) `config.context_window_overrides[model]`, (2) provider metadata via `ProviderRegistry`, (3) `litellm.get_model_info()`, (4) `None`. Cada fallback envuelto en try/except para que nunca falle.
- **Dependencias**: T-01, T-02 (módulo metrics.py existe), T-03 (EvalConfig tiene `context_window_overrides`)
- **Criterio de done**: 
  - Con override en config → retorna el override.
  - Sin override pero con litellm registry → retorna de litellm.
  - Sin nada → retorna `None`.
  - Nunca lanza excepción bajo ninguna circunstancia.
- **Esfuerzo**: M

---

## Fase 3: Cálculo de Métricas Derivadas (cost, context, overflow, truncation_risk, deltas)

Funciones puras que toman datos y producen dataclasses. Testeables en aislamiento.

### T-07: Implementar `compute_cost_metrics()`

- [ ] **Calcular métricas de costo agregadas a partir de resultados de ejecución**
- **Archivos**: `md_evals/metrics.py`
- **Qué hace**: Implementar la función del design §3.4. Suma `prompt_tokens`, `completion_tokens`, `latency_ms` de todos los `ExecutionResult`. Calcula `estimated_cost_usd` usando `cost_map` (si hay rate para el modelo) con la fórmula `(prompt × input_rate + completion × output_rate) / 1_000_000`. Sin rate → `null`. Determina `data_quality` como `measured` si al menos un result tiene `prompt_tokens`.
- **Dependencias**: T-02 (dataclass `CostMetrics`), T-03 (modelos extendidos)
- **Criterio de done**: Test con scenario REQ-02-S1 de spec (prompt=5000, completion=1500, rates=2.50/10.00 → cost=0.0275). Test con REQ-03-S2 (sin rate → `null`). Test con REQ-03-S3 (sin cost_map → `null` para todos).
- **Esfuerzo**: M

### T-08: Implementar `compute_context_metrics()`

- [ ] **Calcular métricas de contexto (utilización, headroom, overflow, truncation_risk)**
- **Archivos**: `md_evals/metrics.py`
- **Qué hace**: Implementar la función del design §3.4. Usa MAX de `prompt_tokens` entre todos los results (worst-case). Calcula todas las métricas derivadas: `context_utilization_pct`, `headroom_tokens`, `safe_headroom_tokens`, `overflow`, `overflow_tokens`, `truncation_risk`. Maneja los 3 paths: (a) window conocido y >0, (b) window=0, (c) window=None. Umbrales hardcoded: <70%→low, 70-90%→medium, ≥90%→high.
- **Dependencias**: T-02 (dataclass `ContextMetrics`)
- **Criterio de done**: Tests con los 3 scenarios de REQ-02 (datos completos, window null, window=0). Test de EC-01 (division by zero). Test de EC-07 (window desconocido). Test de cada threshold de truncation_risk (69.99%→low, 70%→medium, 89.99%→medium, 90%→high).
- **Esfuerzo**: M

### T-09: Implementar `compute_delta()` y `build_comparison()`

- [ ] **Calcular deltas de comparación entre variants con protección div-by-zero**
- **Archivos**: `md_evals/metrics.py`
- **Qué hace**: Implementar `compute_delta()` (design §3.5) y una función `build_comparison()` que aplica `compute_delta()` a todos los campos comparables de ambos domains. Manejar: (a) ambos valores presentes → calcular delta_abs y delta_pct, (b) baseline=0 → `delta_pct=null, reason="baseline_zero"`, (c) variant faltante → todo null con `reason="variant_not_executed"`, (d) booleanos → `reason="boolean_metric"`.
- **Dependencias**: T-02 (dataclass `MetricDelta`), T-07, T-08 (CostMetrics/ContextMetrics calculadas)
- **Criterio de done**: Tests con REQ-06-S1 (delta completo), REQ-06-S2 (variant faltante), REQ-06-S3 (div-by-zero), EC-02, EC-05, EC-10 (boolean metric).
- **Esfuerzo**: M

### T-10: Implementar `build_stage_breakdown()`

- [ ] **Construir el array de stage breakdown a partir de results agrupados**
- **Archivos**: `md_evals/metrics.py`
- **Qué hace**: Agrupar `ExecutionResult`s por `stage_type` del `LLMResponse`. Para cada grupo, sumar tokens y latency. Asignar `attribution_quality` basado en la disponibilidad de datos. Para V1 (sin orquestador real), todo será un solo stage `single_pass`. Verificar consistencia: si la suma de `total_tokens` de stages ≠ total del variant → emitir un flag de warning.
- **Dependencias**: T-02 (dataclass `StageMetrics`), T-04 (stage_type en LLMResponse)
- **Criterio de done**: Test con single_pass → array de 1 entry. Test con múltiples stage_types → entries agrupadas. Test de EC-09 (sumas inconsistentes → warning). Test con telemetría parcial → `attribution_quality="low"`.
- **Esfuerzo**: S

---

## Fase 4: Feature Flags y Configuración (CLI flags + YAML schema + cost_map)

El interruptor que enciende todo. Hasta que esta fase esté completa, las métricas se capturan pero no se reportan.

### T-11: Agregar `--collect-usage-metrics` a `cli.py`

- [ ] **Registrar flag CLI con precedencia sobre YAML**
- **Archivos**: `md_evals/cli.py`
- **Qué hace**: Agregar parámetro `collect_usage_metrics: Annotated[Optional[bool], typer.Option("--collect-usage-metrics/--no-collect-usage-metrics", ...)] = None` al comando `run()`. Después de cargar config, resolver precedencia: si CLI no es None → usa CLI; si None → mantiene valor de YAML (default False). Setear `config.output.include_usage_metrics` con el valor resuelto.
- **Dependencias**: T-03 (OutputConfig tiene `include_usage_metrics`)
- **Criterio de done**: 
  - `md-evals run --collect-usage-metrics` → `config.output.include_usage_metrics == True`.
  - `md-evals run --no-collect-usage-metrics` con YAML true → `False` (CLI gana).
  - `md-evals run` sin flag con YAML true → `True`.
  - `md-evals run` sin flag sin YAML → `False`.
  - `md-evals run --help` muestra la opción.
- **Esfuerzo**: S

### T-12: Validar parseo de `cost_map` y `context_window_overrides` desde YAML

- [ ] **Verificar que Pydantic parsea los nuevos campos de EvalConfig sin errores**
- **Archivos**: `md_evals/models.py`, `tests/test_config.py`
- **Qué hace**: Asegurar que un `eval.yaml` con secciones `cost_map` y `context_window_overrides` se carga correctamente en `EvalConfig`. Verificar que la ausencia de estas secciones no produce error (defaults vacíos). Agregar tests en `test_config.py` que validen el parseo con y sin estos campos.
- **Dependencias**: T-03 (campos en EvalConfig)
- **Criterio de done**: Test con YAML que incluye `cost_map` → parsea rates correctamente. Test con YAML sin `cost_map` → `config.cost_map == {}`. Test con `context_window_overrides` → parsea ints correctamente.
- **Esfuerzo**: S

---

## Fase 5: Agregación y Reporte (reporter CLI + JSON export)

Donde todo se une. El reporter consume los datos capturados y los renderiza.

### T-13: Implementar `_build_usage_metrics()` en reporter

- [ ] **Construir el bloque `usage_metrics` completo para el JSON output**
- **Archivos**: `md_evals/reporter.py`, `md_evals/metrics.py`
- **Qué hace**: Agregar método `_build_usage_metrics(results) -> dict | None` al reporter. Si `include_usage_metrics == False` → retorna `None`. Si True: agrupa results por treatment, resuelve context_window, llama a `compute_cost_metrics()`, `compute_context_metrics()`, `build_stage_breakdown()` por variant, llama a `build_comparison()` si hay 2+ variants, serializa todo a dict con `dataclasses.asdict()`. Implementar también `serialize_usage_metrics()` en metrics.py si es necesario para dar estructura al dict final.
- **Dependencias**: T-06 a T-10 (todas las funciones de cálculo), T-11 (flag resuelto)
- **Criterio de done**: Con flag on y results mock → retorna dict con estructura del JSON canónico (spec §5). Con flag off → retorna `None`.
- **Esfuerzo**: M

### T-14: Modificar `_build_output_data()` para inclusión condicional

- [ ] **Incluir `usage_metrics`, `report_schema_version`, `feature_flags` solo si flag on**
- **Archivos**: `md_evals/reporter.py`
- **Qué hace**: En `_build_output_data()`, llamar a `_build_usage_metrics()`. Si retorna non-None, agregar al output dict: `report_schema_version: "2.0"`, `feature_flags: {"include_usage_metrics": true}`, y el bloque `usage_metrics`. Si retorna None → no agregar nada (output legacy idéntico).
- **Dependencias**: T-13 (`_build_usage_metrics()` existe)
- **Criterio de done**: 
  - **AC-02**: JSON con flag off NO tiene keys `report_schema_version`, `feature_flags`, ni `usage_metrics`.
  - **AC-01**: JSON con flag on tiene `cost_metrics` y `context_metrics` dentro de `usage_metrics.variants`.
  - **AC-17**: `results[].tokens` y `results[].duration_ms` presentes en ambos casos.
- **Esfuerzo**: S

### T-15: Implementar tablas CLI de métricas (Rich tables)

- [ ] **Renderizar secciones Cost Metrics, Context Metrics, Comparison en terminal**
- **Archivos**: `md_evals/reporter.py`
- **Qué hace**: Agregar 3 métodos: `_print_cost_metrics_table()`, `_print_context_metrics_table()`, `_print_comparison_table()`. Usar `rich.table.Table` (ya importado). Modificar `report_terminal()` para llamar a estos métodos condicionalmente si `include_usage_metrics == True`, después de la tabla principal existente. Columnas numéricas con `justify="right"`. Colores: verde para mejoras (delta negativo en cost), rojo para degradaciones.
- **Dependencias**: T-13 (datos de usage_metrics disponibles), T-14 (integración en reporter)
- **Criterio de done**: `md-evals run --collect-usage-metrics` muestra las 3 tablas adicionales en terminal. Sin el flag → terminal idéntica a la actual (cero secciones nuevas). Números formateados con separadores de miles.
- **Esfuerzo**: M

---

## Fase 6: Tests, Validación y Backward Compat

Cierre: tests exhaustivos, edge cases, y verificación de que nada se rompe.

### T-16: Tests unitarios de funciones puras en `metrics.py`

- [ ] **Cubrir todos los scenarios y edge cases de spec con tests unitarios**
- **Archivos**: `tests/test_metrics.py` (NUEVO)
- **Qué hace**: Tests paramétricos para:
  - `compute_cost_metrics()`: REQ-02-S1 (datos completos), REQ-03-S1/S2/S3 (rate sí/no/ausente).
  - `compute_context_metrics()`: REQ-02-S1/S2/S3 (datos completos, window null, window=0). Cada threshold de truncation_risk. EC-01 (div-by-zero), EC-03 (negativos), EC-07 (window desconocido).
  - `compute_delta()`: REQ-06-S1/S2/S3 (delta normal, variant faltante, div-by-zero). EC-02, EC-05, EC-10.
  - `resolve_context_window()`: cada nivel del fallback chain.
  - `build_stage_breakdown()`: single_pass, multi-stage, EC-09 (sumas inconsistentes).
- **Dependencias**: T-06 a T-10 (funciones implementadas)
- **Criterio de done**: `pytest tests/test_metrics.py -v` → todos pasan. Coverage ≥ 95% del módulo `metrics.py`. Cada edge case EC-01 a EC-10 tiene al menos un test.
- **Esfuerzo**: M

### T-17: Tests de integración de reporter con flag on/off

- [ ] **Verificar output JSON y CLI con ambos estados del flag**
- **Archivos**: `tests/test_reporter_usage.py` (NUEVO)
- **Qué hace**: Tests que crean `ExecutionResult`s mock, los pasan al reporter con flag on y off, y verifican:
  - **AC-02**: Flag off → JSON no tiene keys nuevas (comparar keys contra snapshot legacy).
  - **AC-01**: Flag on → `usage_metrics.variants.*.cost_metrics` y `.context_metrics` existen y son objetos separados.
  - **AC-17**: `results[].tokens` y `results[].duration_ms` presentes independientemente del flag.
  - **AC-18**: `data_quality` presente en ambos domains.
  - **AC-11**: Suma de stage_breakdown tokens = total del variant.
- **Dependencias**: T-13, T-14 (reporter con usage_metrics implementado)
- **Criterio de done**: `pytest tests/test_reporter_usage.py -v` → todos pasan. Al menos 1 test por cada AC validado.
- **Esfuerzo**: M

### T-18: Tests de precedencia de CLI flags

- [ ] **Verificar las 4 combinaciones de CLI × YAML para feature flag**
- **Archivos**: `tests/test_cli_flags.py` (NUEVO) o extensión de `tests/test_cli.py`
- **Qué hace**: Tests de las 4 combinaciones del flag (spec §REQ-04-S1 a S4):
  - CLI no pasado + YAML false/ausente → off.
  - CLI `--collect-usage-metrics` + YAML false → on (CLI gana).
  - CLI no pasado + YAML true → on.
  - CLI `--no-collect-usage-metrics` + YAML true → off (CLI gana).
- **Dependencias**: T-11 (flag CLI implementado)
- **Criterio de done**: `pytest tests/test_cli.py -k usage_metrics -v` (o `test_cli_flags.py`) → 4 tests pasan, uno por cada scenario.
- **Esfuerzo**: S

### T-19: Test E2E completo y verificación de ACs

- [ ] **Smoke test de flujo completo con eval.yaml configurado**
- **Archivos**: `tests/test_e2e_workflow.py` (extensión)
- **Qué hace**: Agregar un test E2E que:
  1. Usa un `eval.yaml` de fixture con `cost_map`, `context_window_overrides`, y `output.include_usage_metrics: true`.
  2. Ejecuta una evaluación mock (con LLM mockeado que retorna usage completa).
  3. Verifica que el JSON output tiene la estructura completa del spec §5.
  4. Ejecuta la misma evaluación con flag off y verifica que el JSON es legacy-compatible.
  5. Valida todos los AC que no estén cubiertos por tests unitarios (AC-01 a AC-20).
- **Dependencias**: Todas las tareas anteriores (T-01 a T-18)
- **Criterio de done**: Test E2E pasa. Checklist de AC-01 a AC-20 verificado (se puede usar comentarios en el test marcando cada AC).
- **Esfuerzo**: L

---

## Validación Global

Comandos a ejecutar antes de considerar el feature completo:

```bash
# 1. Lint — cero errores
ruff check md_evals/ tests/

# 2. Type check (si aplica)
# mypy md_evals/ --ignore-missing-imports

# 3. Tests completos — todos pasan, incluyendo nuevos
pytest tests/ -v --tb=short

# 4. Coverage — no baja del baseline actual
pytest tests/ --cov=md_evals --cov-report=term-missing

# 5. Build — paquete se construye sin error
python -m build

# 6. Smoke test con flag ON
md-evals run --collect-usage-metrics -c examples/eval.yaml

# 7. Smoke test con flag OFF (backward compat)
md-evals run -c examples/eval.yaml
# Verificar: output no tiene keys nuevas (usage_metrics, report_schema_version, feature_flags)

# 8. Smoke test con flag ON pero sin cost_map (graceful null)
md-evals run --collect-usage-metrics -c examples/eval-no-costs.yaml
# Verificar: estimated_cost_usd = null, sin error

# 9. Comparar output legacy (diff)
# Guardar output antes de la feature, comparar con output después con flag off
diff results/before.json results/after-flag-off.json  # Debe ser idéntico en estructura
```

---

## Notas de Implementación

### Gotchas del design que el implementador debe tener en cuenta

1. **`tokens` (legacy) vs `completion_tokens_detail` (nuevo)**: El campo `LLMResponse.tokens` DEBE seguir siendo `completion_tokens or 0`. No renombrar, no cambiar su semántica. El nuevo campo se llama `completion_tokens_detail` para evitar confusión con el legacy. En `cost_metrics`, el campo se llama `completion_tokens` (sin suffix).

2. **Clamp de negativos (EC-03)**: Si el provider retorna `prompt_tokens < 0`, clampear a `0` Y cambiar `data_quality` a `"estimated"`. Esto se hace en `LLMAdapter.complete()`, no en las funciones de cálculo.

3. **`context_window_max_tokens = 0` vs `null`**: Son casos distintos. `0` → overflow es true si hay tokens, headroom=0. `null` → todo derivado es null/default seguro, overflow=false. Implementar ambos paths explícitamente.

4. **Division by zero en `delta_pct`**: Nunca retornar `Infinity`, `NaN`, ni crashear. Si baseline=0 → `delta_pct=null` con `reason="baseline_zero"`. Si ambos son null → `reason="variant_not_executed"`.

5. **Boolean metrics en comparison**: `overflow` es booleano — no tiene sentido calcular delta numérico. Usar `reason="boolean_metric"` con delta_abs y delta_pct ambos null.

6. **`litellm.get_model_info()` puede fallar**: La función existe en litellm pero puede lanzar excepciones con modelos desconocidos. Envolver SIEMPRE en try/except. Si litellm no está importado o la función no existe → silently skip.

7. **`dataclasses.asdict()` con enums**: Los `str, Enum` se serializan como sus valores string automáticamente con `asdict()`. No se necesita custom encoder.

8. **Serialización condicional en reporter**: El bloque `usage_metrics` se agrega al dict DESPUÉS de las keys legacy. Si `_build_usage_metrics()` retorna `None`, NO agregar ninguna key nueva al output — ni `report_schema_version`, ni `feature_flags`. Esto garantiza AC-02.

9. **`max_tokens_request`**: Viene de `config.defaults.max_tokens`. Si no está configurado, usar el default del modelo o 0. Este valor se necesita para `safe_headroom_tokens`.

10. **Stage breakdown en V1**: En esta versión no hay orquestador real — toda llamada es `single_pass`. El code path de múltiples stages existe en la lógica pero no se activará hasta que se implemente el orquestador (spec separada). Aun así, los tests deben cubrir el multi-stage path con datos mockeados.

### Mapping de ACs a tareas

| AC | Descripción breve | Tarea que lo cubre |
|----|-------------------|--------------------|
| AC-01 | Domains separados en JSON | T-14, T-17 |
| AC-02 | Flag off = legacy idéntico | T-14, T-17, T-19 |
| AC-03 | Cost USD correcto / null sin rate | T-07, T-16 |
| AC-04 | context_utilization_pct formula | T-08, T-16 |
| AC-05 | headroom_tokens formula | T-08, T-16 |
| AC-06 | safe_headroom_tokens formula | T-08, T-16 |
| AC-07 | overflow = true sii used > max | T-08, T-16 |
| AC-08 | overflow_tokens formula | T-08, T-16 |
| AC-09 | truncation_risk thresholds | T-08, T-16 |
| AC-10 | Stage breakdown ambos variants | T-10, T-16 |
| AC-11 | Suma stages = total variant | T-10, T-17 |
| AC-12 | attribution_quality en stages | T-10, T-16 |
| AC-13 | Comparison deltas ambos domains | T-09, T-16 |
| AC-14 | Variant faltante → nulls + reason | T-09, T-16 |
| AC-15 | Div-by-zero → null + reason | T-09, T-16 |
| AC-16 | CLI flag precedencia | T-11, T-18 |
| AC-17 | Legacy fields invariados | T-14, T-17 |
| AC-18 | data_quality en ambos domains | T-07, T-08, T-17 |
| AC-19 | cost_map ausente → null sin error | T-07, T-12, T-16 |
| AC-20 | Window desconocido → null/default | T-08, T-16 |
