# md-evals

Read this in: [English](README.md) · [Español](README.es.md)

Scientific A/B evaluation for AI skills, prompts, and agent workflows.

[![PyPI](https://img.shields.io/pypi/v/md-evals?color=blue&label=PyPI)](https://pypi.org/project/md-evals/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](tests/)
[![GitHub Models](https://img.shields.io/badge/GitHub%20Models-public%20preview-green.svg)](https://github.com/marketplace/models)

[Live Docs](https://evals.javierzader.com/) · [PyPI](https://pypi.org/project/md-evals/) · [Examples](docs/examples/) · [GitHub Models Guide](https://evals.javierzader.com/#/guide/github-models-setup)

`md-evals` is a Python CLI for evaluating AI skills (`SKILL.md`), prompt variants, and file-producing agents against a real `CONTROL` baseline. It compares a control against one or more treatments over a shared task suite, using both LLM-as-judge scoring and deterministic graders (files, shell commands, workspace state), and reports the results to the terminal, JSON, Markdown, or static HTML.

It runs on multiple LLM providers through LiteLLM and has first-class support for **GitHub Models**, which is free in public preview and lets you try the tool without paid API spend.

The project is inspired by [LangChain skills-benchmarks](https://github.com/langchain-ai/skills-benchmarks) but is designed as a standalone local CLI.

## Features

- `CONTROL` vs treatment evaluation for `SKILL.md` and prompt variants, with wildcard treatment selection.
- Regex and LLM-as-judge evaluators for output quality.
- Deterministic graders for files, shell command execution, and workspace state diffs.
- Repeated runs and parallel workers for more reliable comparisons under model variance.
- Rubric-based grading, a no-LLM deterministic pre-check, and a `SKILL.md` linter.
- Three-phase evaluation (`Structure` → `Analyze` → `Generate`) and A/B output contracts.
- Eval suites with grade thresholds, plugin evaluation, and mission suites with regression tracking.
- Analytics store with trends, cost summaries, and a skills × dimensions heatmap, plus a SQL-in-Markdown dashboard.
- Rich terminal output plus JSON, Markdown, and static HTML reporting.
- Optional web UI (`apps/web`) and API server (`apps/server`) — see [Web app and server](#web-app-and-server).

Typical use cases:

- Compare two prompt or skill variants against the same task suite.
- Gate prompt/skill changes in CI with repeatable pass/fail criteria and exit codes.
- Evaluate coding or file-producing agents with deterministic graders.
- Validate structured outputs with multi-phase checks and output contracts.

## Installation

Requirements: Python `3.12+`.

### From PyPI

```bash
pip install md-evals
```

### From source with `uv`

```bash
git clone https://github.com/JNZader/md-evals.git
cd md-evals
uv sync
source .venv/bin/activate
```

For development dependencies:

```bash
uv sync --extra dev
source .venv/bin/activate
```

### From source with `pip` (editable)

```bash
git clone https://github.com/JNZader/md-evals.git
cd md-evals
pip install -e .
```

## Quick Start

### Scaffold a new evaluation

```bash
md-evals init
```

This creates, in the target directory (default `.`):

- `eval.yaml` — configuration (defaults to `provider: openai`, `model: gpt-4o`)
- `SKILL.md` — a skill template
- `rubric.yaml` — a copy of the built-in grading rubric
- `results/` — output directory

### Minimum local flow

```bash
md-evals init
md-evals list --config eval.yaml
md-evals lint SKILL.md
md-evals run --config eval.yaml
```

### GitHub Models quick start

```bash
export GITHUB_TOKEN="github_pat_..."
md-evals smoke --provider github-models --config eval.yaml
md-evals list-models --provider github-models
md-evals run --config eval.yaml --provider github-models --model claude-3.5-sonnet
```

### Common real workflows

```bash
# Only specific treatments
md-evals run --config eval.yaml --treatment WITH_SKILL
md-evals run --config eval.yaml --treatment CONCISE_SKILL,DETAILED_SKILL

# Wildcard expansion
md-evals run --config eval.yaml --treatment "LCC_*"

# Statistical repetition + parallel workers
md-evals run --config eval.yaml --count 5 -n 4

# Different provider/model override
md-evals run --config eval.yaml --provider openai --model gpt-4o

# Export structured output
md-evals run --config eval.yaml --output json      # writes <results_dir>/results.json
md-evals run --config eval.yaml --output markdown  # writes <results_dir>/results.md
```

## GitHub Models Setup And Auth Flow

GitHub Models is the lowest-friction path for trying `md-evals` without paid API spend.

### Auth resolution order

`md-evals` resolves GitHub auth in this order:

1. `GITHUB_TOKEN` environment variable
2. `gh auth token` from a prior `gh auth login`

Normal flow:

```bash
export GITHUB_TOKEN="github_pat_..."
md-evals smoke --provider github-models --config eval.yaml
```

Fallback for users already authenticated with the GitHub CLI:

```bash
gh auth login
md-evals smoke --provider github-models --config eval.yaml
```

### Preflight before full runs

`md-evals smoke` runs local preflight checks **without calling provider APIs**. It validates:

- provider registration
- config parsing
- GitHub auth token availability (for `github-models`)

```bash
md-evals smoke --provider github-models --config eval.yaml
```

If it fails, verify both token sources explicitly:

```bash
printenv GITHUB_TOKEN
gh auth token
```

### Model listing

```bash
md-evals list-models --provider github-models
md-evals list-models --provider github-models --verbose
md-evals list-models   # every registered provider
```

### Supported GitHub Models

| Model | Context Window | Temperature Range | Notes |
|-------|----------------|-------------------|-------|
| `claude-3.5-sonnet` | 200,000 | `0.0–2.0` | Recommended for complex reasoning and analysis |
| `gpt-4o` | 128,000 | `0.0–2.0` | Strong general-purpose capability |
| `deepseek-r1` | 64,000 | `0.0–1.0` | Lower cost, good for coding tasks |
| `grok-3` | 128,000 | `0.0–2.0` | Alternative reasoning profile |

Free-tier rate limit reported by the provider: `15 req/min`.

Hosted guide: [GitHub Models setup](https://evals.javierzader.com/#/guide/github-models-setup)

## Configuration

`eval.yaml` drives the evaluation lifecycle: defaults, treatments, tests, lint rules, execution policy, and output.

### Complete example

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

### Section reference

| Section | What it controls |
|---------|------------------|
| `defaults` | model, provider, temperature, token limits, timeout, retries |
| `treatments` | baseline and skill variants, including `CONTROL` |
| `tests` | prompt templates, variables, evaluators |
| `lint` | skill length and validation policy |
| `execution` | workers, repetitions, fail-fast behavior |
| `output` | table/json/markdown output and saved results |

### Practical notes

- `CONTROL` should always have `skill_path: null`. If you omit `CONTROL` from `--treatment`, it is added automatically.
- Use `repetitions: 5` or `md-evals run --count 5` when you need stronger signal against model variance.
- Use `parallel_workers` carefully with GitHub Models because of public-preview rate limits.
- Keep `output.format: table` locally for fast loops and export JSON or Markdown in CI.

Full schema: [docs/reference/yaml-schema.md](docs/reference/yaml-schema.md)

## Commands

Every command exposes `--help`.

### Core

| Command | Purpose |
|---------|---------|
| `md-evals version` | print the installed version |
| `md-evals init [DIR]` | scaffold `eval.yaml`, `SKILL.md`, `rubric.yaml`, and `results/` |
| `md-evals run` | run `CONTROL` vs treatment evaluations |
| `md-evals lint [SKILL_PATH]` | validate a skill file against constraints |
| `md-evals check [SKILL_PATH]` | deterministic pre-check on a skill (no LLM, no cost) |
| `md-evals smoke` | local preflight: provider, config, and GitHub auth (no API calls) |
| `md-evals list` | list configured treatments and tasks |
| `md-evals list-models` | list available models by provider |
| `md-evals export INPUT.json` | export a JSON result file to static HTML |

### Suites, plugins, and pipelines

| Command | Purpose |
|---------|---------|
| `md-evals suite run` | run an eval suite and check grade thresholds |
| `md-evals eval-plugin PLUGIN_DIR` | discover and evaluate all `SKILL.md` files in a plugin directory |
| `md-evals plugins list` | list available probes and detectors (built-in and plugin) |

### Analytics, missions, and dashboards

| Command | Purpose |
|---------|---------|
| `md-evals analytics trends` | score trends for a skill over time (or summary stats) |
| `md-evals analytics cost` | cost analytics summary |
| `md-evals analytics heatmap` | skills × dimensions heatmap |
| `md-evals mission run MISSION.yaml` | run a YAML mission suite and track regressions |
| `md-evals mission report MISSION.yaml` | generate a Markdown report from the latest mission run |
| `md-evals dashboard DASHBOARD.md` | render a SQL-in-Markdown dashboard from the analytics store |

### `run` options that matter

| Option | Why you would use it |
|--------|----------------------|
| `--treatment, -t` | comma-separated treatments or a wildcard (e.g. `"LCC_*"`) |
| `--count` / `-n` | repetitions / parallel workers |
| `--provider, -p` / `--model, -m` | override provider/model |
| `--output, -o` | `table`, `json`, or `markdown` |
| `--no-lint` | skip skill linting |
| `--no-pre-check` | bypass the pre-check phase |
| `--force` | run LLM eval even on pre-check errors |
| `--mode` | `smoke`, `reliable`, or `regression` execution defaults |
| `--pipeline` / `--no-pipeline` | force pipeline mode on/off |
| `--probe` | comma-separated probe names (e.g. `dimension,edge-case`) |
| `--collect-usage-metrics` | include extended cost/context metrics |
| `--debug` | provider initialization debug logging |

Full command reference: [docs/reference/cli-commands.md](docs/reference/cli-commands.md)

### Exit codes

`md-evals run` uses distinct exit codes so you can gate CI:

| Code | Meaning |
|------|---------|
| `0` | success (all or partial pass) |
| `1` | configuration or provider-initialization error |
| `2` | pre-check or linter failure |
| `3` | execution / API error |
| `4` | all tests failed |
| `5` | regressions detected (regression mode) |

Other subcommands (`suite`, `mission`, `eval-plugin`) document their own codes in `--help`. See [docs/reference/exit-codes.md](docs/reference/exit-codes.md).

## Advanced Graders

Beyond text matching, `md-evals` can grade side effects inside an isolated workspace.

### File graders

```python
from md_evals.graders import FileExistsGrader, FileContentGrader, FileSizeGrader

graders = [
    FileExistsGrader(name="report_exists", path="results/report.md"),
    FileContentGrader(name="has_section", path="results/report.md", pattern=r"^## Summary"),
    FileSizeGrader(name="report_not_empty", path="results/report.md", min_bytes=200),
]
```

### `CommandGrader`

Runs a real shell command inside the workspace and asserts exit code and optional stdout.

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

Use it for compile checks, test execution, script validation, and verifying that generated code actually runs.

### `StateGrader`

Snapshots workspace state before execution and compares created, deleted, and modified files after the run.

```python
from md_evals.graders import StateGrader

grader = StateGrader(
    name="workspace_changes",
    expected_created=["output.json"],
    expected_deleted=["temp.txt"],
    expected_modified=["config.yaml"],
)

# Call grader.snapshot(workspace) before task execution.
# Then call grader.grade(workspace) after execution.
```

This matters when evaluating agents that perform file operations rather than returning a single text blob.

## Three-Phase Evaluation And Contracts

### `ThreePhaseEvaluator`

Deterministic structure before subjective quality scoring. Execution order: `Structure` → `Analyze` → `Generate`. If a required phase fails, later phases are skipped. Each phase is configured with a list of graders, a scoring weight, and whether it is required.

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

Representative graders by phase:

| Phase | Typical graders |
|-------|-----------------|
| Structure | `JSONValidGrader`, `RequiredFieldsGrader`, `FieldTypeGrader` |
| Analyze | `KeywordCoverageGrader`, `SectionCoverageGrader`, `MinLengthGrader` |
| Generate | `OutputMatchGrader`, `ConstraintGrader` |

### `OutputContract` and `ABContractGrader`

Contracts assert structure and policy across variants without depending only on judge-model opinions.

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

`ABContractGrader` verifies that both variants satisfy the same contract and that the two variants are not identical.

## Workspace Runner

`WorkspaceRunner` orchestrates isolated task execution in temporary directories.

Lifecycle: create temp workspace → write setup files → snapshot state for `StateGrader` → run the task command → apply graders → clean up.

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

This is the bridge between prompt evaluation and real agent-task evaluation.

## Web App And Server

The repository also contains an optional web frontend and API server (they are not part of the PyPI package):

- `apps/web` — a React + Vite single-page app (`md-evals-web`) using TanStack Query, React Router, and Recharts. Scripts: `npm run dev`, `npm run build`, `npm run preview`.
- `apps/server` — a FastAPI service backed by PostgreSQL (SQLAlchemy + Alembic) with GitHub OAuth login, per-user provider-key storage, and eval/analytics routes.
- `docker-compose.yml` / `docker-compose.prod.yaml` — bring up the `db` and `server` services.

These power the hosted experience and are independent of the CLI. Use the CLI alone if you only need local evaluation.

## Development And Testing

### Dev setup

```bash
uv sync --extra dev
source .venv/bin/activate
```

### Core test commands

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

### Common development workflows

```bash
# Run a single file
pytest tests/test_engine.py -v

# Run one class or test
pytest tests/test_engine.py::TestExecutionEngine -v

# Target provider-related work
pytest -k "github_models" -v

# Faster local loop
pytest -m "unit and not slow"

# CI-friendly reports
pytest -n 4 \
  --cov=md_evals \
  --cov-report=html \
  --cov-report=xml \
  --cov-report=json
```

### Test posture

Measured on this repository with `pytest -n 4` (coverage enabled via `pytest.ini`):

| Metric | Value |
|--------|-------|
| Tests passing | `1788` |
| Tests skipped | `2` |
| `md_evals` coverage | `86.94%` |

(These are a snapshot; run `pytest` locally for current numbers.)

### Testing documentation

- [docs/TESTING.md](docs/TESTING.md)
- [docs/TEST_DEVELOPMENT_GUIDE.md](docs/TEST_DEVELOPMENT_GUIDE.md)
- [docs/TEST_ARCHITECTURE.md](docs/TEST_ARCHITECTURE.md)
- [docs/TEST_CI_INTEGRATION.md](docs/TEST_CI_INTEGRATION.md)
- [docs/TEST_QUICK_REFERENCE.md](docs/TEST_QUICK_REFERENCE.md)
- [docs/TEST_COVERAGE_ANALYSIS.md](docs/TEST_COVERAGE_ANALYSIS.md)

## Project Structure

```text
md_evals/            # CLI package (published to PyPI)
├── cli.py           # Typer CLI entrypoint and command workflows
├── config.py        # eval.yaml loading and wildcard expansion
├── engine.py        # execution and A/B comparison logic
├── evaluator.py     # regex / LLM-as-judge evaluators
├── llm.py           # LiteLLM adapter + provider fallback chain
├── linter.py        # SKILL.md linter
├── precheck.py      # deterministic no-LLM pre-check
├── rubric.py        # rubric loading and grading
├── scoring.py       # grade scoring
├── three_phase.py   # multi-phase deterministic evaluation
├── workspace.py     # isolated task execution for file/command/state grading
├── analytics.py     # analytics store, trends, cost, heatmap
├── dashboard.py     # SQL-in-Markdown dashboard rendering
├── export.py        # static HTML export
├── suites.py        # eval suites with grade thresholds
├── plugin_eval.py   # plugin directory evaluation
├── graders/         # deterministic grading primitives
├── mission/         # mission suites + regression tracking
├── pipeline/        # pipeline mode: probes, detectors, stages
└── providers/       # provider integrations (incl. GitHub Models)

apps/
├── web/             # React + Vite frontend (md-evals-web)
└── server/          # FastAPI + PostgreSQL API server

tests/               # ~1,790 tests (unit, integration, e2e)
docs/                # hosted docs, guides, examples, reference
openspec/            # spec-driven change history
```

## Documentation And References

- Hosted docs: [evals.javierzader.com](https://evals.javierzader.com/)
- Quick start guide: [docs/guide/quick-start.md](docs/guide/quick-start.md)
- Configuration guide: [docs/guide/configuration.md](docs/guide/configuration.md)
- Evaluators guide: [docs/guide/evaluators.md](docs/guide/evaluators.md)
- GitHub Models guide: [docs/guide/github-models-setup.md](docs/guide/github-models-setup.md)
- Environment variables: [docs/reference/environment.md](docs/reference/environment.md)
- YAML schema: [docs/reference/yaml-schema.md](docs/reference/yaml-schema.md)
- Exit codes: [docs/reference/exit-codes.md](docs/reference/exit-codes.md)
- Examples: [docs/examples/](docs/examples/)
- Changelog: [CHANGELOG.md](CHANGELOG.md)
- Contributing: [CONTRIBUTING.md](CONTRIBUTING.md)
- Security: [SECURITY.md](SECURITY.md)
- Code of conduct: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

License: [MIT](LICENSE)
