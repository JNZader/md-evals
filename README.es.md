# md-evals

Read this in: [English](README.md) · [Español](README.es.md)

Evaluación A/B científica para skills de IA, prompts y flujos de trabajo de agentes.

[![PyPI](https://img.shields.io/pypi/v/md-evals?color=blue&label=PyPI)](https://pypi.org/project/md-evals/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](tests/)
[![GitHub Models](https://img.shields.io/badge/GitHub%20Models-public%20preview-green.svg)](https://github.com/marketplace/models)

[Live Docs](https://evals.javierzader.com/) · [PyPI](https://pypi.org/project/md-evals/) · [Examples](docs/examples/) · [GitHub Models Guide](https://evals.javierzader.com/#/guide/github-models-setup)

`md-evals` es una CLI de Python para evaluar skills de IA (`SKILL.md`), variantes de prompts y agentes que producen archivos, contra una línea base real `CONTROL`. Compara un control contra uno o más tratamientos sobre una misma suite de tareas, usando tanto scoring con LLM-como-juez como graders determinísticos (archivos, comandos de shell, estado del workspace), y reporta los resultados a la terminal, JSON, Markdown o HTML estático.

Funciona sobre múltiples proveedores de LLM a través de LiteLLM y tiene soporte de primer nivel para **GitHub Models**, que es gratuito en public preview y te permite probar la herramienta sin gasto en APIs pagas.

El proyecto está inspirado en [LangChain skills-benchmarks](https://github.com/langchain-ai/skills-benchmarks) pero está diseñado como una CLI local independiente.

## Características

- Evaluación `CONTROL` vs tratamiento para variantes de `SKILL.md` y de prompts, con selección de tratamientos por comodines.
- Evaluadores por regex y con LLM-como-juez para la calidad de la salida.
- Graders determinísticos para archivos, ejecución de comandos de shell y diffs de estado del workspace.
- Corridas repetidas y workers en paralelo para comparaciones más confiables frente a la varianza del modelo.
- Grading basado en rúbrica, un pre-check determinístico sin LLM y un linter de `SKILL.md`.
- Evaluación en tres fases (`Structure` → `Analyze` → `Generate`) y contratos de salida A/B.
- Suites de evaluación con umbrales de nota, evaluación de plugins y suites de misión con seguimiento de regresiones.
- Store de analytics con tendencias, resúmenes de costo y un heatmap de skills × dimensiones, más un dashboard SQL-en-Markdown.
- Salida enriquecida en terminal más reportes en JSON, Markdown y HTML estático.
- UI web opcional (`apps/web`) y servidor de API (`apps/server`) — ver [Aplicación web y servidor](#aplicación-web-y-servidor).

Casos de uso típicos:

- Comparar dos variantes de prompt o skill contra la misma suite de tareas.
- Poner un gate a cambios de prompt/skill en CI con criterios repetibles de pass/fail y códigos de salida.
- Evaluar agentes de código o que producen archivos con graders determinísticos.
- Validar salidas estructuradas con chequeos multifase y contratos de salida.

## Instalación

Requisitos: Python `3.12+`.

### Desde PyPI

```bash
pip install md-evals
```

### Desde el código fuente con `uv`

```bash
git clone https://github.com/JNZader/md-evals.git
cd md-evals
uv sync
source .venv/bin/activate
```

Para dependencias de desarrollo:

```bash
uv sync --extra dev
source .venv/bin/activate
```

### Desde el código fuente con `pip` (modo editable)

```bash
git clone https://github.com/JNZader/md-evals.git
cd md-evals
pip install -e .
```

## Inicio rápido

### Generar el andamiaje de una evaluación nueva

```bash
md-evals init
```

Esto crea, en el directorio destino (por defecto `.`):

- `eval.yaml` — configuración (por defecto `provider: openai`, `model: gpt-4o`)
- `SKILL.md` — una plantilla de skill
- `rubric.yaml` — una copia de la rúbrica de grading incorporada
- `results/` — directorio de salida

### Flujo local mínimo

```bash
md-evals init
md-evals list --config eval.yaml
md-evals lint SKILL.md
md-evals run --config eval.yaml
```

### Inicio rápido con GitHub Models

```bash
export GITHUB_TOKEN="github_pat_..."
md-evals smoke --provider github-models --config eval.yaml
md-evals list-models --provider github-models
md-evals run --config eval.yaml --provider github-models --model claude-3.5-sonnet
```

### Flujos reales comunes

```bash
# Solo tratamientos específicos
md-evals run --config eval.yaml --treatment WITH_SKILL
md-evals run --config eval.yaml --treatment CONCISE_SKILL,DETAILED_SKILL

# Expansión por comodines
md-evals run --config eval.yaml --treatment "LCC_*"

# Repetición estadística + workers en paralelo
md-evals run --config eval.yaml --count 5 -n 4

# Override de proveedor/modelo
md-evals run --config eval.yaml --provider openai --model gpt-4o

# Exportar salida estructurada
md-evals run --config eval.yaml --output json      # escribe <results_dir>/results.json
md-evals run --config eval.yaml --output markdown  # escribe <results_dir>/results.md
```

## Configuración y flujo de autenticación de GitHub Models

GitHub Models es el camino de menor fricción para probar `md-evals` sin gasto en APIs pagas.

### Orden de resolución de autenticación

`md-evals` resuelve la autenticación de GitHub en este orden:

1. Variable de entorno `GITHUB_TOKEN`
2. `gh auth token` de un `gh auth login` previo

Flujo normal:

```bash
export GITHUB_TOKEN="github_pat_..."
md-evals smoke --provider github-models --config eval.yaml
```

Alternativa para usuarios ya autenticados con la CLI de GitHub:

```bash
gh auth login
md-evals smoke --provider github-models --config eval.yaml
```

### Preflight antes de las corridas completas

`md-evals smoke` corre chequeos de preflight locales **sin llamar a las APIs del proveedor**. Valida:

- registro del proveedor
- parseo de la configuración
- disponibilidad del token de autenticación de GitHub (para `github-models`)

```bash
md-evals smoke --provider github-models --config eval.yaml
```

Si falla, verificá ambas fuentes del token de forma explícita:

```bash
printenv GITHUB_TOKEN
gh auth token
```

### Listado de modelos

```bash
md-evals list-models --provider github-models
md-evals list-models --provider github-models --verbose
md-evals list-models   # todos los proveedores registrados
```

### Modelos de GitHub Models soportados

| Modelo | Ventana de contexto | Rango de temperatura | Notas |
|--------|---------------------|----------------------|-------|
| `claude-3.5-sonnet` | 200,000 | `0.0–2.0` | Recomendado para razonamiento y análisis complejos |
| `gpt-4o` | 128,000 | `0.0–2.0` | Capacidad general robusta |
| `deepseek-r1` | 64,000 | `0.0–1.0` | Menor costo, bueno para tareas de código |
| `grok-3` | 128,000 | `0.0–2.0` | Perfil de razonamiento alternativo |

Límite de tasa del tier gratuito informado por el proveedor: `15 req/min`.

Guía online: [GitHub Models setup](https://evals.javierzader.com/#/guide/github-models-setup)

## Configuración

`eval.yaml` maneja el ciclo de vida de la evaluación: valores por defecto, tratamientos, tests, reglas de lint, política de ejecución y salida.

### Ejemplo completo

```yaml
name: "Code Generation Skill Evaluation"
version: "1.0"
description: "Test whether a Python skill improves code quality"

defaults:
  model: "claude-3.5-sonnet"
  provider: "github-models"
  temperature: 0.7
  max_tokens: 2048
  timeout: 60
  retry_attempts: 3

treatments:
  CONTROL:
    description: "Baseline without injected skill"
    skill_path: null

  CONCISE_SKILL:
    description: "Short skill"
    skill_path: "./skills/concise.md"

  DETAILED_SKILL:
    description: "Detailed skill"
    skill_path: "./skills/detailed.md"

tests:
  - name: "python_function_generation"
    description: "Generate a valid Python function"
    prompt: "Write a function to {task}. Do not include markdown formatting."
    variables:
      task: "sort a list of integers"
    evaluators:
      - type: "regex"
        name: "has_def_keyword"
        pattern: "^def "
      - type: "llm"
        name: "is_correct"
        criteria: "Does the function solve the task correctly and clearly?"

lint:
  max_lines: 400
  fail_on_violation: true

execution:
  parallel_workers: 2
  repetitions: 3
  fail_fast: false

output:
  format: "table"
  save_results: true
  results_dir: "./results"
  verbose: false
```

### Referencia de secciones

| Sección | Qué controla |
|---------|--------------|
| `defaults` | modelo, proveedor, temperatura, límites de tokens, timeout, reintentos |
| `treatments` | línea base y variantes de skill, incluyendo `CONTROL` |
| `tests` | plantillas de prompt, variables, evaluadores |
| `lint` | longitud del skill y política de validación |
| `execution` | workers, repeticiones, comportamiento de fail-fast |
| `output` | salida table/json/markdown y resultados guardados |

### Notas prácticas

- `CONTROL` siempre debería tener `skill_path: null`. Si omitís `CONTROL` en `--treatment`, se agrega automáticamente.
- Usá `repetitions: 5` o `md-evals run --count 5` cuando necesites más señal frente a la varianza del modelo.
- Usá `parallel_workers` con cuidado en GitHub Models por los límites de tasa del public preview.
- Mantené `output.format: table` en local para loops rápidos y exportá JSON o Markdown en CI.

Esquema completo: [docs/reference/yaml-schema.md](docs/reference/yaml-schema.md)

## Comandos

Todos los comandos exponen `--help`.

### Principales

| Comando | Propósito |
|---------|-----------|
| `md-evals version` | imprime la versión instalada |
| `md-evals init [DIR]` | genera `eval.yaml`, `SKILL.md`, `rubric.yaml` y `results/` |
| `md-evals run` | corre evaluaciones `CONTROL` vs tratamiento |
| `md-evals lint [SKILL_PATH]` | valida un archivo de skill contra las restricciones |
| `md-evals check [SKILL_PATH]` | pre-check determinístico de un skill (sin LLM, sin costo) |
| `md-evals smoke` | preflight local: proveedor, config y auth de GitHub (sin llamadas a la API) |
| `md-evals list` | lista los tratamientos y tareas configurados |
| `md-evals list-models` | lista los modelos disponibles por proveedor |
| `md-evals export INPUT.json` | exporta un archivo de resultados JSON a HTML estático |

### Suites, plugins y pipelines

| Comando | Propósito |
|---------|-----------|
| `md-evals suite run` | corre una suite de evaluación y chequea umbrales de nota |
| `md-evals eval-plugin PLUGIN_DIR` | descubre y evalúa todos los `SKILL.md` de un directorio de plugin |
| `md-evals plugins list` | lista probes y detectors disponibles (incorporados y de plugin) |

### Analytics, misiones y dashboards

| Comando | Propósito |
|---------|-----------|
| `md-evals analytics trends` | tendencias de nota de un skill en el tiempo (o estadísticas resumen) |
| `md-evals analytics cost` | resumen de analytics de costo |
| `md-evals analytics heatmap` | heatmap de skills × dimensiones |
| `md-evals mission run MISSION.yaml` | corre una suite de misión en YAML y sigue las regresiones |
| `md-evals mission report MISSION.yaml` | genera un reporte en Markdown desde la última corrida de misión |
| `md-evals dashboard DASHBOARD.md` | renderiza un dashboard SQL-en-Markdown desde el store de analytics |

### Opciones de `run` que importan

| Opción | Por qué la usarías |
|--------|--------------------|
| `--treatment, -t` | tratamientos separados por coma o un comodín (ej. `"LCC_*"`) |
| `--count` / `-n` | repeticiones / workers en paralelo |
| `--provider, -p` / `--model, -m` | override de proveedor/modelo |
| `--output, -o` | `table`, `json` o `markdown` |
| `--no-lint` | saltear el linting del skill |
| `--no-pre-check` | omitir la fase de pre-check |
| `--force` | correr la eval con LLM aun con errores de pre-check |
| `--mode` | defaults de ejecución `smoke`, `reliable` o `regression` |
| `--pipeline` / `--no-pipeline` | forzar el modo pipeline on/off |
| `--probe` | nombres de probes separados por coma (ej. `dimension,edge-case`) |
| `--collect-usage-metrics` | incluir métricas extendidas de costo/contexto |
| `--debug` | logging de debug de la inicialización del proveedor |

Referencia completa de comandos: [docs/reference/cli-commands.md](docs/reference/cli-commands.md)

### Códigos de salida

`md-evals run` usa códigos de salida distintos para que puedas poner gates en CI:

| Código | Significado |
|--------|-------------|
| `0` | éxito (pass total o parcial) |
| `1` | error de configuración o de inicialización del proveedor |
| `2` | falla de pre-check o del linter |
| `3` | error de ejecución / de la API |
| `4` | todos los tests fallaron |
| `5` | regresiones detectadas (modo regression) |

Otros subcomandos (`suite`, `mission`, `eval-plugin`) documentan sus propios códigos en `--help`. Ver [docs/reference/exit-codes.md](docs/reference/exit-codes.md).

## Graders avanzados

Más allá del matching de texto, `md-evals` puede evaluar efectos secundarios dentro de un workspace aislado.

### Graders de archivos

```python
from md_evals.graders import FileExistsGrader, FileContentGrader, FileSizeGrader

graders = [
    FileExistsGrader(name="report_exists", path="results/report.md"),
    FileContentGrader(name="has_section", path="results/report.md", pattern=r"^## Summary"),
    FileSizeGrader(name="report_not_empty", path="results/report.md", min_bytes=200),
]
```

### `CommandGrader`

Corre un comando de shell real dentro del workspace y valida el código de salida y, opcionalmente, el stdout.

```python
from md_evals.graders import CommandGrader

grader = CommandGrader(
    name="tests_pass",
    command="python -m pytest tests/",
    expected_exit_code=0,
    expected_output="passed",
    timeout=30,
)
```

Usalo para chequeos de compilación, ejecución de tests, validación de scripts y para verificar que el código generado efectivamente corre.

### `StateGrader`

Toma un snapshot del estado del workspace antes de la ejecución y compara los archivos creados, borrados y modificados después de la corrida.

```python
from md_evals.graders import StateGrader

grader = StateGrader(
    name="workspace_changes",
    expected_created=["output.json"],
    expected_deleted=["temp.txt"],
    expected_modified=["config.yaml"],
)

# Llamá a grader.snapshot(workspace) antes de ejecutar la tarea.
# Luego llamá a grader.grade(workspace) después de ejecutar.
```

Esto importa cuando evaluás agentes que realizan operaciones de archivos en vez de devolver un único bloque de texto.

## Evaluación en tres fases y contratos

### `ThreePhaseEvaluator`

Estructura determinística antes del scoring subjetivo de calidad. Orden de ejecución: `Structure` → `Analyze` → `Generate`. Si una fase requerida falla, se saltean las fases posteriores. Cada fase se configura con una lista de graders, un peso de scoring y si es requerida.

```python
from md_evals.three_phase import ThreePhaseEvaluator, PhaseConfig
from md_evals.graders import (
    JSONValidGrader,
    RequiredFieldsGrader,
    KeywordCoverageGrader,
    OutputMatchGrader,
)

evaluator = ThreePhaseEvaluator(
    structure=PhaseConfig(
        graders=[
            JSONValidGrader(name="valid_json", path="output.json"),
            RequiredFieldsGrader(
                name="required_fields",
                path="output.json",
                required_fields=["name", "metadata.version"],
            ),
        ],
        weight=0.3,
        required=True,
    ),
    analyze=PhaseConfig(
        graders=[
            KeywordCoverageGrader(
                name="covers_topics",
                path="output.json",
                keywords=["architecture", "testing"],
                pass_threshold=0.8,
            )
        ],
        weight=0.4,
        required=True,
    ),
    generate=PhaseConfig(
        graders=[OutputMatchGrader(name="has_summary", path="output.json", patterns=[r"summary"])],
        weight=0.3,
        required=False,
    ),
)

result = evaluator.evaluate(workspace_path)
```

Graders representativos por fase:

| Fase | Graders típicos |
|------|-----------------|
| Structure | `JSONValidGrader`, `RequiredFieldsGrader`, `FieldTypeGrader` |
| Analyze | `KeywordCoverageGrader`, `SectionCoverageGrader`, `MinLengthGrader` |
| Generate | `OutputMatchGrader`, `ConstraintGrader` |

### `OutputContract` y `ABContractGrader`

Los contratos afirman estructura y política entre variantes sin depender únicamente de la opinión del modelo juez.

```python
from md_evals.graders import OutputContract, ContractAssertionGrader, ABContractGrader

contract = OutputContract(
    required_sections=[r"^## Purpose", r"^## Implementation"],
    format_rules=[r"```python"],
    forbidden_patterns=[r"TODO", r"FIXME"],
    min_words=50,
    max_words=2000,
)

single_output = ContractAssertionGrader(
    name="contract_check",
    contract=contract,
    path="output.md",
)

ab_output = ABContractGrader(
    name="ab_contract",
    contract=contract,
    variant_a="Control output...",
    variant_b="Treatment output...",
)
```

`ABContractGrader` verifica que ambas variantes satisfagan el mismo contrato y que las dos variantes no sean idénticas.

## Workspace Runner

`WorkspaceRunner` orquesta la ejecución aislada de tareas en directorios temporales.

Ciclo de vida: crear workspace temporal → escribir archivos de setup → tomar snapshot del estado para `StateGrader` → ejecutar el comando de la tarea → aplicar graders → limpiar.

```python
from md_evals.workspace import WorkspaceRunner, WorkspaceConfig, SetupFile
from md_evals.graders import FileExistsGrader, CommandGrader

config = WorkspaceConfig(
    name="test_code_generation",
    setup_files=[
        SetupFile(path="requirements.txt", content="pytest\n"),
        SetupFile(path="src/main.py", content="print('hello')"),
    ],
    task_command="python src/main.py",
    graders=[
        FileExistsGrader(name="main_exists", path="src/main.py"),
        CommandGrader(name="syntax_ok", command="python -m py_compile src/main.py"),
    ],
    task_timeout=60,
)

runner = WorkspaceRunner()
result = runner.run(config)
```

Este es el puente entre la evaluación de prompts y la evaluación real de tareas de agente.

## Aplicación web y servidor

El repositorio también contiene un frontend web y un servidor de API opcionales (no forman parte del paquete de PyPI):

- `apps/web` — una single-page app en React + Vite (`md-evals-web`) que usa TanStack Query, React Router y Recharts. Scripts: `npm run dev`, `npm run build`, `npm run preview`.
- `apps/server` — un servicio FastAPI respaldado por PostgreSQL (SQLAlchemy + Alembic) con login por GitHub OAuth, almacenamiento de claves de proveedor por usuario y rutas de eval/analytics.
- `docker-compose.yml` / `docker-compose.prod.yaml` — levantan los servicios `db` y `server`.

Estos dan soporte a la experiencia online y son independientes de la CLI. Usá solo la CLI si únicamente necesitás evaluación local.

## Desarrollo y testing

### Setup de desarrollo

```bash
uv sync --extra dev
source .venv/bin/activate
```

### Comandos de test principales

```bash
pytest
pytest -n 4
pytest -n auto
pytest -m unit
pytest -m integration
pytest -m e2e
pytest --cov=md_evals --cov-report=term-missing
pytest --cov=md_evals --cov-report=html
```

### Flujos de desarrollo comunes

```bash
# Correr un solo archivo
pytest tests/test_engine.py -v

# Correr una clase o un test
pytest tests/test_engine.py::TestExecutionEngine -v

# Enfocar el trabajo relacionado al proveedor
pytest -k "github_models" -v

# Loop local más rápido
pytest -m "unit and not slow"

# Reportes amigables para CI
pytest -n 4 \
  --cov=md_evals \
  --cov-report=html \
  --cov-report=xml \
  --cov-report=json
```

### Estado de los tests

Medido en este repositorio con `pytest -n 4` (cobertura habilitada vía `pytest.ini`):

| Métrica | Valor |
|---------|-------|
| Tests que pasan | `1788` |
| Tests salteados | `2` |
| Cobertura de `md_evals` | `86.94%` |

(Son un snapshot; corré `pytest` en local para los números actuales.)

### Documentación de testing

- [docs/TESTING.md](docs/TESTING.md)
- [docs/TEST_DEVELOPMENT_GUIDE.md](docs/TEST_DEVELOPMENT_GUIDE.md)
- [docs/TEST_ARCHITECTURE.md](docs/TEST_ARCHITECTURE.md)
- [docs/TEST_CI_INTEGRATION.md](docs/TEST_CI_INTEGRATION.md)
- [docs/TEST_QUICK_REFERENCE.md](docs/TEST_QUICK_REFERENCE.md)
- [docs/TEST_COVERAGE_ANALYSIS.md](docs/TEST_COVERAGE_ANALYSIS.md)

## Estructura del proyecto

```text
md_evals/            # Paquete de la CLI (publicado en PyPI)
├── cli.py           # Entrypoint de la CLI Typer y flujos de comandos
├── config.py        # Carga de eval.yaml y expansión de comodines
├── engine.py        # Lógica de ejecución y comparación A/B
├── evaluator.py     # Evaluadores regex / LLM-como-juez
├── llm.py           # Adaptador de LiteLLM + cadena de fallback de proveedores
├── linter.py        # Linter de SKILL.md
├── precheck.py      # Pre-check determinístico sin LLM
├── rubric.py        # Carga de rúbrica y grading
├── scoring.py       # Scoring de notas
├── three_phase.py   # Evaluación determinística multifase
├── workspace.py     # Ejecución aislada de tareas para grading de archivos/comandos/estado
├── analytics.py     # Store de analytics, tendencias, costo, heatmap
├── dashboard.py     # Renderizado de dashboard SQL-en-Markdown
├── export.py        # Exportación a HTML estático
├── suites.py        # Suites de evaluación con umbrales de nota
├── plugin_eval.py   # Evaluación de directorios de plugin
├── graders/         # Primitivas de grading determinístico
├── mission/         # Suites de misión + seguimiento de regresiones
├── pipeline/        # Modo pipeline: probes, detectors, stages
└── providers/       # Integraciones de proveedores (incl. GitHub Models)

apps/
├── web/             # Frontend React + Vite (md-evals-web)
└── server/          # Servidor de API FastAPI + PostgreSQL

tests/               # ~1.790 tests (unit, integration, e2e)
docs/                # docs online, guías, ejemplos, referencia
openspec/            # historial de cambios spec-driven
```

## Documentación y referencias

- Docs online: [evals.javierzader.com](https://evals.javierzader.com/)
- Guía de inicio rápido: [docs/guide/quick-start.md](docs/guide/quick-start.md)
- Guía de configuración: [docs/guide/configuration.md](docs/guide/configuration.md)
- Guía de evaluadores: [docs/guide/evaluators.md](docs/guide/evaluators.md)
- Guía de GitHub Models: [docs/guide/github-models-setup.md](docs/guide/github-models-setup.md)
- Variables de entorno: [docs/reference/environment.md](docs/reference/environment.md)
- Esquema YAML: [docs/reference/yaml-schema.md](docs/reference/yaml-schema.md)
- Códigos de salida: [docs/reference/exit-codes.md](docs/reference/exit-codes.md)
- Ejemplos: [docs/examples/](docs/examples/)
- Changelog: [CHANGELOG.md](CHANGELOG.md)
- Contribuir: [CONTRIBUTING.md](CONTRIBUTING.md)
- Seguridad: [SECURITY.md](SECURITY.md)
- Código de conducta: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

Licencia: [MIT](LICENSE)
