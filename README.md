# md-evals

Lightweight CLI tool for evaluating AI skills (SKILL.md) with Control vs Treatment testing using LiteLLM.

Inspired by [LangChain skills-benchmarks](https://github.com/langchain-ai/skills-benchmarks).

## Features

- **A/B Testing**: Compare Control (no skill) vs Treatment (with skill) prompts
- **Multiple Treatments**: Run wildcards like `LCC_*` to test multiple skill variations
- **Hybrid Evaluation**: Regex patterns + LLM-as-a-judge evaluation
- **Linter**: Enforce 400-line limit and other best practices
- **Rich Output**: Beautiful terminal tables with pass rates and comparisons
- **JSON/Markdown Export**: Save results for analysis

## Installation

```bash
# Clone the repository
git clone https://github.com/JNZader/md-evals.git
cd md-evals

# Install dependencies
uv sync

# Or with pip
pip install -e .
```

## Quick Start

```bash
# Initialize a new evaluation project
md-evals init

# Run evaluation
md-evals run

# Lint your SKILL.md
md-evals lint

# List available treatments and tasks
md-evals list
```

## Configuration

Create an `eval.yaml` file:

```yaml
name: "My Evaluation"
version: "1.0"

defaults:
  model: "gpt-4o"
  provider: "openai"
  temperature: 0.7

treatments:
  CONTROL:
    description: "Baseline without skill"
    skill_path: null
  
  WITH_SKILL:
    description: "With skill injected"
    skill_path: "./SKILL.md"

tests:
  - name: "example_test"
    prompt: "Hello, {name}!"
    variables:
      name: "World"
    evaluators:
      - type: "regex"
        name: "has_greeting"
        pattern: "Hello"
```

## Commands

| Command | Description |
|---------|-------------|
| `md-evals init` | Scaffold eval.yaml and SKILL.md |
| `md-evals run` | Run evaluations |
| `md-evals lint` | Validate SKILL.md |
| `md-evals list` | List treatments and tasks |

## Options

### run
- `-c, --config`: Config file (default: eval.yaml)
- `-t, --treatment`: Treatment(s) to run
- `-m, --model`: Override model
- `-n`: Parallel workers
- `--count`: Repetitions
- `-o, --output`: Output format (table/json/markdown)
- `--no-lint`: Skip linting

### lint
- `SKILL.md`: File to lint (default: SKILL.md)
- `-f, --fail`: Exit with error on violations

## Development

```bash
# Install dev dependencies
uv sync --extra dev

# Run tests
pytest

# Run with coverage
pytest --cov=md_evals
```

## License

MIT
