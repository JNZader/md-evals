# md-evals

[![GitHub License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-69%2B-brightgreen.svg)](tests/)
[![GitHub Models](https://img.shields.io/badge/GitHub%20Models-Free-green.svg)](https://github.com/models)

> **Evaluate AI skills with scientific rigor.** Compare prompts with and without injected context using A/B testing, multiple LLM providers, and production-grade evaluation techniques.

**Lightweight CLI tool for evaluating AI skills (SKILL.md) with Control vs Treatment testing using LiteLLM.**

Inspired by [LangChain skills-benchmarks](https://github.com/langchain-ai/skills-benchmarks).

**📚 [Full Documentation](https://jnzader.github.io/md-evals/)** | [Quick Start](#quick-start) | [GitHub Models Guide](#-github-models-freelow-cost-llm-evaluation) | [Examples](docs/examples/)

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

**Requirements:** Python 3.9+

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

# 2. Run with GitHub Models (free!)
export GITHUB_TOKEN="github_pat_..."
md-evals run --provider github-models --model claude-3.5-sonnet

# 3. View results
# → Beautiful table with Control vs Treatment comparison
# → Pass rates and statistics
```

## 🎉 GitHub Models: Free LLM Evaluation

Evaluate your skills **completely free** using GitHub's Models API (public preview):

### Setup (One-time)

```bash
# Create a GitHub personal access token
# https://github.com/settings/tokens → New token → "repo" scope

# Set your token (save in .env for persistence)
export GITHUB_TOKEN="github_pat_..."
```

### Run Evaluation with Free Models

```bash
# Use Claude 3.5 Sonnet (200k context, free!)
md-evals run eval.yaml --provider github-models --model claude-3.5-sonnet

# Or use GPT-4o
md-evals run eval.yaml --provider github-models --model gpt-4o

# Or use DeepSeek R1 (fastest)
md-evals run eval.yaml --provider github-models --model deepseek-r1
```

### Available Models

| Model | Context | Best For | Cost |
|-------|---------|----------|------|
| `claude-3.5-sonnet` | 200k | Reasoning, complex tasks | 🟢 Free |
| `gpt-4o` | 128k | General-purpose, balanced | 🟢 Free |
| `deepseek-r1` | 64k | Speed, cost efficiency | 🟢 Free |
| `grok-3` | 128k | Latest, edge cases | 🟢 Free |

**Rate Limits:** 15 requests/min (public preview) · [Full Guide →](https://jnzader.github.io/md-evals/#/guide/github-models-setup)

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
| `md-evals run [treatment]` | 🎯 Run specific treatment |
| `md-evals lint` | ✅ Validate SKILL.md (400-line limit, best practices) |
| `md-evals list` | 📋 List available treatments and tests |
| `md-evals list-models` | 🤖 List available models per provider |

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

## Development

### Setup

```bash
# Install with dev dependencies
uv sync --extra dev

# Activate virtual environment
source .venv/bin/activate
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=md_evals --cov-report=html

# Run specific test file
pytest tests/test_github_models_provider.py -v

# Run with debug output
pytest --debug
```

### Project Structure

```
md_evals/
├── cli.py                    # Command-line interface
├── engine.py                 # Evaluation engine (A/B testing)
├── llm.py                    # LLM provider interface
├── providers/                # LLM provider implementations
│   ├── github_models.py     # GitHub Models (free!)
│   ├── openai_provider.py
│   ├── anthropic_provider.py
│   └── litellm_provider.py
├── evaluators/               # Evaluation strategies
│   ├── regex_evaluator.py
│   └── llm_evaluator.py
└── config.py                 # YAML config parsing

tests/
├── test_engine.py
├── test_github_models_provider.py  # 43 tests
├── test_provider_registry.py       # 11 tests
└── ...
```

## Community & Support

### 📖 Documentation
- **[Full Guide](https://jnzader.github.io/md-evals/)** - Installation, tutorials, API reference
- **[GitHub Models Setup](https://jnzader.github.io/md-evals/#/guide/github-models-setup)** - Free LLM evaluation guide
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
