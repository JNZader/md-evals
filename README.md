# md-evals

[![GitHub License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-69%2B-brightgreen.svg)](tests/)
[![GitHub Models](https://img.shields.io/badge/GitHub%20Models-Free-green.svg)](https://github.com/models)

> **Evaluate AI skills with scientific rigor.** Compare prompts with and without injected context using A/B testing, multiple LLM providers, and production-grade evaluation techniques.

**Lightweight CLI tool for evaluating AI skills (SKILL.md) with Control vs Treatment testing using LiteLLM.**

Inspired by [LangChain skills-benchmarks](https://github.com/langchain-ai/skills-benchmarks).

**📚 [Full Documentation](https://evals.javierzader.com/)** | [Quick Start](#quick-start) | [GitHub Models Guide](#-github-models-freelow-cost-llm-evaluation) | [Examples](docs/examples/)

## Why md-evals?

Building AI applications that work reliably requires **scientific validation**. md-evals makes it easy:

| Challenge | Solution |
|-----------|----------|
| 🤔 "Does my skill actually help?" | A/B test Control vs Treatment automatically |
| 💰 "Can't afford to evaluate with expensive APIs?" | Use free GitHub Models (Claude, GPT-4, DeepSeek) |
| 📊 "How do I know if my results are real?" | Hybrid regex + LLM-as-judge evaluation |
| 🔄 "Evaluating 100+ test cases manually is tedious" | Parallel workers, beautiful terminal output, JSON/Markdown export |
| ✅ "How do I prevent bad skills from merging?" | Built-in linter (400-line limit, best practices) |
| 🏗️ "Will this integrate with my CI/CD?" | Simple YAML config, exit codes for automation |

## Features

- ✨ **A/B Testing**: Compare Control (no skill) vs Treatment (with skill) prompts side-by-side
- 🎯 **Multiple Treatments**: Run wildcards like `LCC_*` to test different skill variations in one go
- 🧠 **Hybrid Evaluation**: Combine regex pattern matching + LLM-as-a-judge for flexible validation
- 🚀 **Multiple LLM Providers**: GitHub Models (free!), OpenAI, Anthropic, LiteLLM, and more
- 📋 **Linter**: Enforce 400-line limit, quality checks, and best practices for SKILL.md
- 📊 **Rich Output**: Beautiful terminal tables with pass rates, comparisons, and statistics
- 💾 **Export**: JSON, Markdown, or table format for reporting and analysis
- ⚡ **Parallel Execution**: Run multiple tests concurrently for faster feedback
- 🎉 **GitHub Models Support**: Use free/low-cost models (Claude 3.5, GPT-4, DeepSeek, Grok)
- 🔬 **Deterministic Graders**: File, command, and state graders for side-effect evaluation
- 🔄 **Three-Phase Pipeline**: Structure → Analyze → Generate sequential evaluation
- 📜 **Contract Assertions**: Define output contracts and validate A/B variants against them
- 🏗️ **Workspace Runner**: Isolated temp workspaces for reproducible task evaluation

## Installation

### Using `uv` (Recommended)

```bash
# Clone the repository
git clone https://github.com/JNZader/md-evals.git
cd md-evals

# Install with uv (fastest)
uv sync

# Activate virtual environment
source .venv/bin/activate
```

### Using `pip`

```bash
git clone https://github.com/JNZader/md-evals.git
cd md-evals

# Install dependencies
pip install -e .
```

**Requirements:** Python 3.12+

## Quick Start

### 1. Initialize your evaluation

```bash
md-evals init
```

This creates:
- `eval.yaml` - Your evaluation config
- `SKILL.md` - Template for your AI skill

### 2. Run evaluation

```bash
md-evals run
```

### 3. Check your skill

```bash
md-evals lint        # Validate SKILL.md
md-evals list        # List treatments and tests
```

### ⏱️ Complete example in 2 minutes

```bash
# 1. Create evaluation
md-evals init

# 2. Preflight auth (env var first, gh login fallback)
md-evals smoke --provider github-models

# 3. Run with GitHub Models (free!)
export GITHUB_TOKEN="github_pat_..."
md-evals run --provider github-models --model claude-3.5-sonnet --config eval.yaml

# 4. View results
# → Beautiful table with Control vs Treatment comparison
# → Pass rates and statistics
```

## 🎉 GitHub Models: Free LLM Evaluation

Evaluate your skills **completely free** using GitHub's Models API (public preview):

### Setup (One-time)

```bash
# Preferred: set GITHUB_TOKEN directly
export GITHUB_TOKEN="github_pat_..."

# Fallback for users already logged in with GitHub CLI
gh auth login

# Verify auth preflight before first run
md-evals smoke --provider github-models --config examples/eval_with_github_models.yaml
```

### Run Evaluation with Free Models

```bash
# Use Claude 3.5 Sonnet (200k context, free!)
md-evals run --config eval.yaml --provider github-models --model claude-3.5-sonnet

# Or use GPT-4o
md-evals run --config eval.yaml --provider github-models --model gpt-4o

# Or use DeepSeek R1 (fastest)
md-evals run --config eval.yaml --provider github-models --model deepseek-r1
```

### Available Models

| Model | Context | Best For | Cost |
|-------|---------|----------|------|
| `claude-3.5-sonnet` | 200k | Reasoning, complex tasks | 🟢 Free |
| `gpt-4o` | 128k | General-purpose, balanced | 🟢 Free |
| `deepseek-r1` | 64k | Speed, cost efficiency | 🟢 Free |
| `grok-3` | 128k | Latest, edge cases | 🟢 Free |

**Rate Limits:** 15 requests/min (public preview) · [Full Guide →](https://evals.javierzader.com/#/guide/github-models-setup)

## Configuration

Create `eval.yaml` to define your evaluation. Here's a complete example:

```yaml
name: "My AI Skill Evaluation"
version: "1.0"
description: "Evaluate skill effectiveness with Control vs Treatment"

defaults:
  model: "claude-3.5-sonnet"
  provider: "github-models"  # Free! (or: openai, anthropic, etc.)
  temperature: 0.7
  max_tokens: 500

treatments:
  CONTROL:
    description: "Baseline: No skill injected"
    skill_path: null
  
  WITH_SKILL:
    description: "Treatment: With skill injected"
    skill_path: "./SKILL.md"
  
  WITH_SKILL_V2:
    description: "Alternative skill variant"
    skill_path: "./SKILL_V2.md"

tests:
  - name: "test_basic_greeting"
    prompt: "Greet {name} and ask how they're doing."
    variables:
      name: "Alice"
    evaluators:
      - type: "regex"
        name: "has_greeting"
        pattern: "(hello|hi|greetings)"
      - type: "llm"
        name: "is_friendly"
        criteria: "Does the response feel warm and friendly?"
  
  - name: "test_complex_reasoning"
    prompt: "Explain {concept} to a {audience}."
    variables:
      concept: "quantum computing"
      audience: "5-year-old child"
    evaluators:
      - type: "llm"
        name: "is_age_appropriate"
        criteria: "Is the explanation suitable for a 5-year-old?"
```

### Key Sections

| Section | Purpose |
|---------|---------|
| `defaults` | LLM model, provider, temperature, token limits |
| `treatments` | Different skill configurations to compare |
| `tests` | Test cases with prompts, variables, and evaluators |

### Evaluators

- **`type: regex`** - Pattern matching (fast, deterministic)
- **`type: llm`** - LLM-as-judge (flexible, intelligent)

## Commands

| Command | Purpose |
|---------|---------|
| `md-evals init` | 🚀 Scaffold `eval.yaml` and `SKILL.md` templates |
| `md-evals run` | ▶️ Run evaluations (Control vs Treatment) |
| `md-evals run --treatment WITH_SKILL` | 🎯 Run specific treatment |
| `md-evals lint` | ✅ Validate SKILL.md (400-line limit, best practices) |
| `md-evals list` | 📋 List available treatments and tests |
| `md-evals list-models` | 🤖 List available models per provider |
| `md-evals smoke --provider github-models --config eval.yaml` | 🧪 Local preflight (provider, config, auth) |

### Common Workflows

```bash
# Evaluate with default provider
md-evals run

# Use specific provider and model
md-evals run --provider github-models --model claude-3.5-sonnet

# Run only specific treatment
md-evals run --treatment WITH_SKILL

# Export results as JSON
md-evals run --output json > results.json

# Run with 4 parallel workers
md-evals run -n 4

# Repeat each test 5 times (for statistical significance)
md-evals run --count 5

# Export to Markdown report
md-evals run --output markdown > report.md

# Validate before running
md-evals lint
```

### Full Options Reference

#### `run`
- `-c, --config FILE` - Config file (default: `eval.yaml`)
- `-t, --treatment TREATMENT` - Run specific treatment(s)
- `-m, --model MODEL` - Override model
- `-p, --provider PROVIDER` - Provider: `github-models`, `openai`, `anthropic`, etc.
- `-n WORKERS` - Parallel workers (default: 1)
- `--count N` - Repeat tests N times for statistical validation
- `-o, --output FORMAT` - Output format: `table` (default), `json`, `markdown`
- `--no-lint` - Skip SKILL.md linting
- `--debug` - Enable debug logging

#### `list-models`
- `-p, --provider PROVIDER` - Filter by provider
- `-v, --verbose` - Show metadata (temperature ranges, costs, rate limits)

## Deterministic Graders

Beyond regex and LLM-as-judge evaluators, md-evals includes **deterministic graders** that check side effects of agent task execution (files created, commands run, workspace state) rather than LLM output text.

All graders implement the `Grader` protocol (`md_evals.graders.base`) and return `EvaluatorResult`, so they integrate seamlessly with the existing reporter and pipeline infrastructure.

### File Graders

| Grader | Purpose |
|--------|---------|
| `FileExistsGrader` | Assert a file exists (or does not exist) in the workspace |
| `FileContentGrader` | Assert file content matches a regex pattern or exact string |
| `FileSizeGrader` | Assert file size is within a min/max byte range |

### Command Grader

`CommandGrader` runs a shell command inside the workspace and asserts on exit code and optionally stdout content. Useful for verifying that generated code compiles, tests pass, or scripts produce expected output.

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

### State Grader

`StateGrader` compares workspace file-system state before and after task execution. It tracks created, deleted, and modified files using modification time snapshots.

```python
from md_evals.graders import StateGrader

grader = StateGrader(
    name="check_state",
    expected_created=["output.json"],
    expected_deleted=["temp.txt"],
    expected_modified=["config.yaml"],
)
# Call grader.snapshot(workspace) before task, grader.grade(workspace) after
```

## Three-Phase Evaluation Pipeline

The `ThreePhaseEvaluator` (`md_evals.three_phase`) orchestrates evaluation in three sequential phases with fail-fast behavior:

1. **Structure** — Validate input/output format (JSON valid? fields present? types correct?)
2. **Analyze** — Evaluate quality of analysis (keyword coverage, section coverage, minimum length)
3. **Generate** — Evaluate final output quality (pattern matching, constraint checking)

If a required phase fails, subsequent phases are skipped. Each phase has configurable weight for scoring.

### Phase Graders

| Phase | Grader | Purpose |
|-------|--------|---------|
| Structure | `JSONValidGrader` | Validate JSON format (file or string mode) |
| Structure | `RequiredFieldsGrader` | Check required fields exist (dot-notation for nesting) |
| Structure | `FieldTypeGrader` | Validate field types (str, int, float, bool, list, dict) |
| Analyze | `KeywordCoverageGrader` | Check keyword/concept coverage with configurable threshold |
| Analyze | `SectionCoverageGrader` | Check for expected sections/headings via regex patterns |
| Analyze | `MinLengthGrader` | Enforce minimum word count and/or character count |
| Generate | `OutputMatchGrader` | Match regex patterns (AND logic, with negate option) |
| Generate | `ConstraintGrader` | Enforce max words, max chars, and forbidden patterns |

### Example

```python
from md_evals.three_phase import ThreePhaseEvaluator, PhaseConfig
from md_evals.graders import JSONValidGrader, RequiredFieldsGrader, KeywordCoverageGrader

evaluator = ThreePhaseEvaluator(
    structure=PhaseConfig(
        graders=[
            JSONValidGrader(name="valid_json", path="output.json"),
            RequiredFieldsGrader(name="has_fields", path="output.json",
                                 required_fields=["name", "metadata.version"]),
        ],
        weight=0.3,
        required=True,
    ),
    analyze=PhaseConfig(
        graders=[KeywordCoverageGrader(name="covers_topics",
                                        path="output.json",
                                        keywords=["architecture", "testing"],
                                        pass_threshold=0.8)],
        weight=0.4,
    ),
    generate=PhaseConfig(graders=[], weight=0.3),
)
result = evaluator.evaluate(workspace_path)
# result.passed, result.overall_score, result.failed_phase
```

## Contract-Based Assertions

Define structural contracts for outputs and validate them deterministically using `ContractAssertionGrader`. The `ABContractGrader` extends this for A/B testing — both variants must satisfy the same contract while producing different content.

### OutputContract

```python
from md_evals.graders import OutputContract, ContractAssertionGrader, ABContractGrader

contract = OutputContract(
    required_sections=[r"^## Purpose", r"^## Implementation"],
    format_rules=[r"```python"],
    forbidden_patterns=[r"TODO", r"FIXME"],
    min_words=50,
    max_words=2000,
)

# Single output validation
grader = ContractAssertionGrader(
    name="contract_check",
    contract=contract,
    path="output.md",        # file mode
    # content="...",         # or content mode
)

# A/B contract validation
ab_grader = ABContractGrader(
    name="ab_contract",
    contract=contract,
    variant_a="Control output...",
    variant_b="Treatment output...",
)
```

## Workspace Runner

`WorkspaceRunner` (`md_evals.workspace`) manages the full lifecycle for deterministic evaluation in isolated temporary directories:

1. Create temporary workspace
2. Set up files (`SetupFile` with path and content)
3. Snapshot state (for `StateGrader` baselines)
4. Execute the task command (with timeout)
5. Apply all graders
6. Cleanup

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
    task_command="python src/main.py > output.txt",
    graders=[
        FileExistsGrader(name="output_created", path="output.txt"),
        CommandGrader(name="syntax_ok", command="python -m py_compile src/main.py"),
    ],
    task_timeout=60,
)

runner = WorkspaceRunner()
result = runner.run(config)
# result.passed, result.grader_results, result.task_exit_code
```

## Development

### Setup

```bash
# Install with dev dependencies
uv sync --extra dev

# Activate virtual environment
source .venv/bin/activate
```

### Testing

md-evals has a comprehensive test suite with **94.95% code coverage** and **321 passing tests**.

#### Quick Start

```bash
# Run all tests
pytest

# Run tests in parallel (73% faster)
pytest -n 4

# View coverage report
pytest --cov=md_evals --cov-report=html
open htmlcov/index.html
```

#### Test Documentation

Complete testing guides for different audiences:

| Guide | Audience | Purpose |
|-------|----------|---------|
| **[TESTING.md](docs/TESTING.md)** | Everyone | How to run tests, markers, parallel execution |
| **[TEST_DEVELOPMENT_GUIDE.md](docs/TEST_DEVELOPMENT_GUIDE.md)** | Developers | Writing new tests, fixtures, mocking strategies |
| **[TEST_ARCHITECTURE.md](docs/TEST_ARCHITECTURE.md)** | Tech Leads | Test organization, fixture hierarchy, isolation patterns |
| **[TEST_CI_INTEGRATION.md](docs/TEST_CI_INTEGRATION.md)** | DevOps/CI Engineers | CI/CD setup, Docker, reporting, multiple platforms |
| **[TEST_QUICK_REFERENCE.md](docs/TEST_QUICK_REFERENCE.md)** | All | Command cheat sheet, one-liners, common patterns |
| **[TEST_COVERAGE_ANALYSIS.md](docs/TEST_COVERAGE_ANALYSIS.md)** | Maintainers | Coverage gaps, improvement roadmap, module analysis |

#### Common Testing Tasks

```bash
# Run only unit tests (fast feedback)
pytest -m unit

# Run only integration tests
pytest -m integration

# Run specific test file
pytest tests/test_github_models_provider.py -v

# Debug a specific test
pytest tests/test_engine.py::TestExecutionEngine::test_run_basic -vvv --pdb

# Run tests that match pattern
pytest -k "github_models"

# Skip slow tests (faster local development)
pytest -m "not slow"

# Generate all reports
pytest -n 4 \
  --cov=md_evals \
  --cov-report=html \
  --cov-report=xml \
  --cov-report=json \
  --junit-xml=test-results.xml
```

#### Test Coverage

- **Overall**: 94.95% (production standard: 90%)
- **Critical modules**: >95% (engine, evaluators, config)
- **Test count**: 321 tests (unit, integration, E2E, performance)
- **Execution time**: 6.63s parallel / 22.09s serial

#### Test Structure

```
tests/
├── conftest.py                    # Shared fixtures and config
├── test_cli.py                    # CLI command tests (100+ tests)
├── test_engine.py                 # Core evaluation engine
├── test_evaluator.py              # Regex & LLM evaluators
├── test_github_models_provider.py # Provider tests (43 tests)
├── test_e2e_workflow.py          # End-to-end workflow tests
├── test_linter.py                 # SKILL.md validation
├── test_reporter.py               # Report generation
└── ... (10+ test files total)
```

#### Performance

| Configuration | Time | Speedup |
|---------------|------|---------|
| Serial | 22.09s | — |
| Parallel (4 workers) | 6.63s | 73% |
| Unit tests only | ~5s | 78% |
| Fast tests (no slow) | ~10s | 55% |

For more details, see **[TESTING.md](docs/TESTING.md)**.

### Project Structure

```
md_evals/
├── cli.py                    # Command-line interface
├── engine.py                 # Evaluation engine (A/B testing)
├── llm.py                    # LLM provider interface
├── config.py                 # YAML config parsing
├── three_phase.py            # Three-phase evaluation pipeline
├── workspace.py              # WorkspaceRunner for isolated evaluation
├── providers/                # LLM provider implementations
│   ├── github_models.py     # GitHub Models (free!)
│   ├── openai_provider.py
│   ├── anthropic_provider.py
│   └── litellm_provider.py
├── evaluators/               # Evaluation strategies
│   ├── regex_evaluator.py
│   └── llm_evaluator.py
├── graders/                  # Deterministic graders
│   ├── base.py              # Grader protocol
│   ├── file_graders.py      # FileExists, FileContent, FileSize
│   ├── command_grader.py    # CommandGrader (shell commands)
│   ├── state_grader.py      # StateGrader (file-system diffs)
│   ├── structure_grader.py  # JSONValid, RequiredFields, FieldType
│   ├── analysis_grader.py   # KeywordCoverage, SectionCoverage, MinLength
│   ├── generation_grader.py # OutputMatch, ConstraintGrader
│   └── contract_grader.py   # OutputContract, ContractAssertion, ABContract
└── pipeline/                 # Plugin evaluation pipeline
    ├── pipeline.py
    ├── runner.py
    └── ...

tests/
├── test_engine.py
├── test_github_models_provider.py  # 43 tests
├── test_provider_registry.py       # 11 tests
└── ...
```

## Community & Support

### 📖 Documentation
- **[Full Guide](https://evals.javierzader.com/)** - Installation, tutorials, API reference
- **[GitHub Models Setup](https://evals.javierzader.com/#/guide/github-models-setup)** - Free LLM evaluation guide
- **[Examples](docs/examples/)** - Real-world usage examples

### 🤝 Contributing
We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Fork → Branch → Pull Request workflow
- Code style guidelines (Ruff, 100 char lines)
- Testing requirements (>80% coverage)
- Conventional Commits format

### 📋 Community
- **[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)** - Our community standards
- **[SECURITY.md](SECURITY.md)** - Vulnerability disclosure process
- **[Issues](https://github.com/JNZader/md-evals/issues)** - Report bugs or request features
- **[Discussions](https://github.com/JNZader/md-evals/discussions)** - Ask questions and share ideas

### 📝 License

MIT
