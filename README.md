# md-evals

Scientific A/B evaluation for AI skills, prompts, and agent workflows.

[![PyPI](https://img.shields.io/pypi/v/md-evals?color=blue&label=PyPI)](https://pypi.org/project/md-evals/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-321%20passing-brightgreen.svg)](tests/)
[![GitHub Models](https://img.shields.io/badge/GitHub%20Models-public%20preview-green.svg)](https://github.com/marketplace/models)

[Live Docs](https://evals.javierzader.com/) · [PyPI](https://pypi.org/project/md-evals/) · [Examples](docs/examples/) · [GitHub Models Guide](https://evals.javierzader.com/#/guide/github-models-setup)

Visuals coming soon.

## Quick Portfolio Snapshot

- CLI-first evaluation framework for comparing `CONTROL` vs treatment prompts and `SKILL.md` variants.
- Built for real model iteration: parallel runs, repeated trials, structured reports, and deterministic graders.
- Supports free GitHub Models in public preview plus multi-provider execution through LiteLLM.
- Includes linter, pre-check phase, YAML configuration, pipeline mode, and a documented test suite with 321 passing tests and 94.95% coverage.

## Why It Matters

- Teams shipping prompts or agent skills need proof, not vibes. `md-evals` gives you reproducible A/B workflows.
- It covers both response quality and side effects. You can grade output text, generated files, command execution, and workspace state.
- It keeps local dev practical. You can start with `smoke`, `lint`, and free GitHub Models before spending on paid providers.

Typical use cases:

- Compare two prompt or skill variants against the same task suite.
- Gate prompt changes in CI with repeatable pass/fail criteria.
- Evaluate coding or file-producing agents with deterministic graders.
- Test structured outputs with multi-phase validation and output contracts.

## Quick Start

### Install

```bash
git clone https://github.com/JNZader/md-evals.git
cd md-evals
uv sync
source .venv/bin/activate
```

Or install from PyPI:

```bash
pip install md-evals
```

### First Workflow

```bash
md-evals init
md-evals smoke --provider github-models --config eval.yaml
md-evals list --config eval.yaml
md-evals run --provider github-models --model claude-3.5-sonnet --config eval.yaml
md-evals lint SKILL.md
```

## Jump To Technical Docs

- Full technical README: [Technical README](#technical-readme)
- Hosted documentation: [evals.javierzader.com](https://evals.javierzader.com/)
- GitHub Models setup: [guide/github-models-setup](https://evals.javierzader.com/#/guide/github-models-setup)

---

## Technical README

### Table Of Contents

1. [What md-evals does](#what-md-evals-does)
2. [Installation](#installation)
3. [Quick start workflows](#quick-start-workflows)
4. [GitHub Models setup and auth flow](#github-models-setup-and-auth-flow)
5. [Configuration](#configuration)
6. [Commands and real workflows](#commands-and-real-workflows)
7. [Advanced graders](#advanced-graders)
8. [Three-phase evaluation and contracts](#three-phase-evaluation-and-contracts)
9. [Workspace runner](#workspace-runner)
10. [Development and testing](#development-and-testing)
11. [Project structure](#project-structure)
12. [Performance notes](#performance-notes)
13. [Documentation and references](#documentation-and-references)

## What md-evals does

`md-evals` is a Python CLI for evaluating AI skills and prompt variants with a real baseline.

Core capabilities:

- `CONTROL` vs treatment evaluation for `SKILL.md` or prompt variants.
- Regex and LLM-as-judge evaluators for output quality.
- Deterministic graders for files, commands, and workspace state.
- Repeated runs and parallel workers for more reliable comparisons.
- Rich terminal output plus JSON and Markdown reporting.
- Free GitHub Models support in public preview.
- Skill linting, pre-checks, pipeline mode, and test coverage strong enough to maintain the tool with confidence.

The project is inspired by [LangChain skills-benchmarks](https://github.com/langchain-ai/skills-benchmarks), but it is designed as a standalone local CLI with pragmatic workflows for prompt and agent evaluation.

## Installation

### Using `uv` from source

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

### Using `pip`

Install the published package:

```bash
pip install md-evals
```

Install from source in editable mode:

```bash
git clone https://github.com/JNZader/md-evals.git
cd md-evals
pip install -e .
```

Requirements:

- Python `3.12+`

## Quick Start Workflows

### Scaffold a new evaluation

```bash
md-evals init
```

This creates:

- `eval.yaml`
- `SKILL.md`
- `results/`

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
md-evals run --config eval.yaml --treatment WITH_SKILL
md-evals run --config eval.yaml --treatment "CONCISE_*,DETAILED_*"
md-evals run --config eval.yaml --count 5 -n 4
md-evals run --config eval.yaml --output json > results.json
md-evals run --config eval.yaml --output markdown > report.md
md-evals run --config eval.yaml --provider openai --model gpt-4o
md-evals smoke --provider github-models --config examples/eval_with_github_models.yaml
```

## GitHub Models Setup And Auth Flow

GitHub Models is the best low-friction path for trying `md-evals` without paid API spend.

### Auth resolution order

`md-evals` checks GitHub auth in this order:

1. `GITHUB_TOKEN`
2. `gh auth token` from a prior `gh auth login`

That means the normal flow is:

```bash
export GITHUB_TOKEN="github_pat_..."
md-evals smoke --provider github-models --config eval.yaml
```

Fallback flow for users already authenticated with GitHub CLI:

```bash
gh auth login
md-evals smoke --provider github-models --config eval.yaml
```

### Preflight auth before full runs

Use `smoke` first. It validates:

- provider registration
- config parsing
- GitHub auth availability

```bash
md-evals smoke --provider github-models --config eval.yaml
```

If it fails, verify both sources explicitly:

```bash
printenv GITHUB_TOKEN
gh auth token
```

### Model listing patterns

List only GitHub Models:

```bash
md-evals list-models --provider github-models
md-evals list-models --provider github-models --verbose
```

List every registered provider:

```bash
md-evals list-models
```

### Supported GitHub Models

| Model | Context Window | Temperature Range | Best For |
|-------|----------------|-------------------|----------|
| `claude-3.5-sonnet` | 200,000 | `0.0–2.0` | long context, instruction following, skill evaluation |
| `gpt-4o` | 128,000 | `0.0–2.0` | balanced general use |
| `deepseek-r1` | 64,000 | `0.0–1.0` | code-heavy and fast loops |
| `grok-3` | 128,000 | `0.0–2.0` | alternative reasoning profile |

Rate limit in public preview: `15 req/min`.

Hosted guide: [GitHub Models setup](https://evals.javierzader.com/#/guide/github-models-setup)

## Configuration

`eval.yaml` drives the whole evaluation lifecycle: defaults, treatments, tests, lint rules, execution policy, and output.

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

- `CONTROL` should always have `skill_path: null`.
- Use `repetitions: 5` or `md-evals run --count 5` when you need stronger signal against model variance.
- Use `parallel_workers` carefully with GitHub Models because of public-preview rate limits.
- If you want faster debugging loops, keep `output.format: table` locally and export JSON or Markdown in CI.

Full schema: [docs/reference/yaml-schema.md](docs/reference/yaml-schema.md)

## Commands And Real Workflows

### Core commands

| Command | Purpose |
|---------|---------|
| `md-evals init` | scaffold `eval.yaml` and `SKILL.md` |
| `md-evals run` | run Control vs treatment evaluations |
| `md-evals lint [SKILL_PATH]` | validate a skill file |
| `md-evals smoke` | preflight provider, config, and GitHub auth |
| `md-evals list` | list configured treatments and tasks |
| `md-evals list-models` | list available models by provider |

### Common evaluation flows

```bash
# Baseline run from local config
md-evals run --config eval.yaml

# Specific treatment only
md-evals run --config eval.yaml --treatment WITH_SKILL

# Multiple explicit treatments
md-evals run --config eval.yaml --treatment CONCISE_SKILL,DETAILED_SKILL

# Wildcard expansion
md-evals run --config eval.yaml --treatment "LCC_*"

# Statistical repetition + parallel workers
md-evals run --config eval.yaml --count 5 -n 4

# Different provider/model override
md-evals run --config eval.yaml --provider github-models --model gpt-4o

# Export structured output
md-evals run --config eval.yaml --output json > results.json
md-evals run --config eval.yaml --output markdown > report.md
```

### Operational flags that matter

| Option | Why you would use it |
|--------|----------------------|
| `--no-lint` | skip skill linting in a controlled experiment |
| `--no-pre-check` | bypass pre-check phase |
| `--force` | continue after pre-check errors |
| `--mode smoke|reliable|regression` | switch execution defaults by intent |
| `--pipeline` | force pipeline mode |
| `--probe` | select pipeline probes |
| `--collect-usage-metrics` | include extended cost/context metrics |
| `--debug` | provider initialization debugging |

### Inspection commands

```bash
md-evals list --config eval.yaml
md-evals list --config eval.yaml --treatments
md-evals list --config eval.yaml --tasks
md-evals list-models
md-evals list-models --provider github-models --verbose
```

Full command reference: [docs/reference/cli-commands.md](docs/reference/cli-commands.md)

## Advanced Graders

Beyond text matching, `md-evals` can grade side effects inside an isolated workspace.

### File graders

Use file-based graders when the task is supposed to create or modify artifacts.

- `FileExistsGrader`
- `FileContentGrader`
- `FileSizeGrader`

```python
from md_evals.graders import FileExistsGrader, FileContentGrader, FileSizeGrader

graders = [
    FileExistsGrader(name="report_exists", path="results/report.md"),
    FileContentGrader(name="has_section", path="results/report.md", pattern=r"^## Summary"),
    FileSizeGrader(name="report_not_empty", path="results/report.md", min_bytes=200),
]
```

### `CommandGrader`

`CommandGrader` runs a real shell command inside the workspace and asserts exit code and optional stdout.

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

Use it for:

- compile checks
- test execution
- script validation
- verifying generated code actually runs

### `StateGrader`

`StateGrader` snapshots workspace state before execution and compares created, deleted, and modified files after the run.

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

This matters when you are evaluating agents that do file operations rather than returning a single text blob.

## Three-Phase Evaluation And Contracts

### `ThreePhaseEvaluator`

The three-phase pipeline gives you deterministic structure before subjective quality scoring.

Execution order:

1. `Structure`
2. `Analyze`
3. `Generate`

If a required phase fails, later phases are skipped.

### `PhaseConfig`

Each phase is configured with:

- a list of graders
- a scoring weight
- whether the phase is required

### Example

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

Contracts let you assert structure and policy across variants without depending only on judge-model opinions.

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

`ABContractGrader` verifies:

- both variants satisfy the same contract
- the two variants are not identical

That is exactly the kind of check you want in real A/B prompt experiments.

## Workspace Runner

`WorkspaceRunner` orchestrates isolated task execution in temporary directories.

Lifecycle:

1. create temp workspace
2. write setup files
3. snapshot state for `StateGrader`
4. run the task command
5. apply graders
6. clean up

### Example

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
pytest tests/test_engine.py::TestExecutionEngine::test_run_basic -vvv --pdb

# Target provider-related work
pytest -k "github_models" -v

# Faster local loop
pytest -m "unit and not slow"

# Generate CI-friendly reports
pytest -n 4 \
  --cov=md_evals \
  --cov-report=html \
  --cov-report=xml \
  --cov-report=json \
  --junit-xml=test-results.xml
```

### Current test posture

| Metric | Value |
|--------|-------|
| Coverage | `94.95%` |
| Passing tests | `321` |
| Skipped tests | `2` |
| Serial runtime | `22.09s` |
| Parallel runtime (`-n 4`) | `6.63s` |

### Testing documentation

- [docs/TESTING.md](docs/TESTING.md)
- [docs/TEST_DEVELOPMENT_GUIDE.md](docs/TEST_DEVELOPMENT_GUIDE.md)
- [docs/TEST_ARCHITECTURE.md](docs/TEST_ARCHITECTURE.md)
- [docs/TEST_CI_INTEGRATION.md](docs/TEST_CI_INTEGRATION.md)
- [docs/TEST_QUICK_REFERENCE.md](docs/TEST_QUICK_REFERENCE.md)
- [docs/TEST_COVERAGE_ANALYSIS.md](docs/TEST_COVERAGE_ANALYSIS.md)

## Project Structure

```text
md_evals/
├── cli.py
├── config.py
├── engine.py
├── llm.py
├── linter.py
├── workspace.py
├── three_phase.py
├── evaluators/
├── graders/
├── mission/
├── pipeline/
└── providers/

tests/
├── conftest.py
├── fixtures/
├── test_cli.py
├── test_config.py
├── test_e2e_workflow.py
├── test_engine.py
├── test_evaluator.py
├── test_github_models_provider.py
├── test_linter.py
├── test_llm.py
├── test_performance.py
├── test_provider_registry.py
└── test_reporter.py
```

Key modules worth knowing:

- `md_evals/cli.py`: Typer CLI entrypoint and command workflows.
- `md_evals/engine.py`: execution and A/B comparison logic.
- `md_evals/three_phase.py`: multi-phase deterministic evaluation.
- `md_evals/workspace.py`: isolated task execution for file/command/state grading.
- `md_evals/graders/`: deterministic grading primitives.
- `md_evals/providers/`: provider integrations including GitHub Models.

## Performance Notes

- Parallel pytest runs cut suite time from `22.09s` to `6.63s` with `-n 4`.
- Repeated eval runs are essential for noisy model behavior, but they amplify rate-limit pressure on GitHub Models.
- `deepseek-r1` is the fastest GitHub Models option for code-heavy feedback loops.
- `claude-3.5-sonnet` is usually the best default when context size and reasoning quality matter more than raw speed.
- Deterministic graders are cheaper and more stable than judge-model scoring for filesystem and command outcomes. Use them whenever you can.

## Documentation And References

- Hosted docs: [evals.javierzader.com](https://evals.javierzader.com/)
- Quick start guide: [docs/guide/quick-start.md](docs/guide/quick-start.md)
- Configuration guide: [docs/guide/configuration.md](docs/guide/configuration.md)
- Evaluators guide: [docs/guide/evaluators.md](docs/guide/evaluators.md)
- GitHub Models guide: [docs/guide/github-models-setup.md](docs/guide/github-models-setup.md)
- Environment variables: [docs/reference/environment.md](docs/reference/environment.md)
- YAML schema: [docs/reference/yaml-schema.md](docs/reference/yaml-schema.md)
- Examples: [docs/examples/](docs/examples/)
- Contributing: [CONTRIBUTING.md](CONTRIBUTING.md)
- Security: [SECURITY.md](SECURITY.md)
- Code of conduct: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

License: [MIT](LICENSE)
