<div align="center">

# md-evals

### Evaluate AI Skills with Scientific Rigor

**A/B testing framework for AI prompts and SKILL.md files — Control vs Treatment, statistical validation, zero-cost evaluation.**

<!-- TODO: Add hero image here — a polished screenshot of the CLI comparison output or a banner graphic -->
![Hero banner placeholder](https://placehold.co/900x300/1a1a2e/e94535?text=md-evals+%E2%86%92+Scientific+AI+Skill+Evaluation)

[![PyPI](https://img.shields.io/pypi/v/md-evals?color=blue&label=PyPI%20Package)](https://pypi.org/project/md-evals/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![GitHub License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-321%2B-brightgreen.svg)](tests/)
[![GitHub Models](https://img.shields.io/badge/GitHub%20Models-Free-green.svg)](https://github.com/models)

[🌐 **Live Demo**](https://evals.javierzader.com) · [📦 PyPI](https://pypi.org/project/md-evals/) · [📖 Full Docs](https://evals.javierzader.com/) · [🤝 Contributing](CONTRIBUTING.md)

</div>

---

## 🎯 Why md-evals?

Building AI applications that work **reliably** requires scientific validation — not guesswork. md-evals gives you the tools to prove your prompts and skills actually improve outputs.

| Challenge | Solution |
|-----------|----------|
| 🤔 "Does my skill actually help?" | A/B test Control vs Treatment automatically |
| 💰 "Can't afford expensive APIs?" | Use **free** GitHub Models (Claude, GPT-4, DeepSeek) |
| 📊 "Are my results statistically significant?" | Hybrid regex + LLM-as-judge evaluation |
| 🔄 "100+ test cases manually?" | Parallel workers, Rich terminal output, JSON/Markdown export |
| ✅ "Prevent bad skills from merging?" | Built-in linter (400-line limit, best practices) |
| 🏗️ "Integrate with CI/CD?" | Simple YAML config, exit codes, structured output |

---

## ✨ Features

| Category | Feature | Description |
|----------|---------|-------------|
| 🧪 **A/B Testing** | Control vs Treatment | Compare prompts with/without injected context side-by-side |
| | Multiple Treatments | Run wildcards like `LCC_*` to test skill variations in one go |
| 🧠 **Evaluation** | Hybrid Grading | Combine regex pattern matching + LLM-as-judge |
| | Deterministic Graders | File, command, and state graders for side-effect evaluation |
| | Three-Phase Pipeline | Structure → Analyze → Generate sequential evaluation |
| | Contract Assertions | Define output contracts and validate A/B variants |
| 🚀 **Providers** | GitHub Models | **Free** LLM access (Claude 3.5, GPT-4o, DeepSeek, Grok) |
| | Multi-Provider | OpenAI, Anthropic, LiteLLM, and more via unified interface |
| 📊 **Output** | Rich Terminal | Beautiful tables with pass rates, comparisons, and statistics |
| | Export | JSON, Markdown, or table format for reporting |
| ⚡ **Performance** | Parallel Execution | Run multiple tests concurrently for faster feedback |
| 🏗️ **Infrastructure** | Workspace Runner | Isolated temp workspaces for reproducible evaluation |
| 📋 **Quality** | Linter | Enforce 400-line limit, quality checks, and best practices |

<!-- TODO: Add screenshot here — CLI evaluation output showing Rich tables -->
![CLI output placeholder](https://placehold.co/800x400/1a1a2e/e94535?text=CLI+Evaluation+Output+%28terminal+screenshots%29)

---

## 🛠️ Tech Stack

| Category | Technology | Purpose |
|----------|-----------|---------|
| CLI | [Typer](https://typer.tiangolo.com/) | Command-line interface framework |
| Terminal UI | [Rich](https://rich.readthedocs.io/) | Beautiful tables, progress bars, formatted output |
| LLM Integration | [LiteLLM](https://github.com/BerriAI/litellm) | Multi-provider LLM abstraction (OpenAI, Anthropic, etc.) |
| LLM Integration | [Azure AI Inference](https://learn.microsoft.com/en-us/python/api/overview/azure/ai-inference) | GitHub Models provider |
| Validation | [Pydantic](https://docs.pydantic.dev/) | Config and result validation |
| HTTP | [httpx](https://www.python-httpx.org/) | Async HTTP client for API calls |
| Language | Python 3.12+ | Modern Python with type hints |

---

## 🚀 Quick Start

```bash
# Install
pip install md-evals

# Or from source
git clone https://github.com/JNZader/md-evals.git && cd md-evals
uv sync && source .venv/bin/activate

# Initialize, authenticate, and run
md-evals init
md-evals smoke --provider github-models   # preflight auth check
md-evals run --provider github-models --model claude-3.5-sonnet
```

<!-- TODO: Add screenshot here — comparison results showing Control vs Treatment -->
![Comparison results placeholder](https://placehold.co/800x400/1a1a2e/e94535?text=Control+vs+Treatment+Comparison+Results)

---

## 🎉 GitHub Models: Free LLM Evaluation

Evaluate your skills **completely free** using GitHub's Models API (public preview):

```bash
export GITHUB_TOKEN="github_pat_..."
md-evals run --provider github-models --model claude-3.5-sonnet   # 200k context, free!
md-evals run --provider github-models --model gpt-4o             # 128k context, free!
md-evals run --provider github-models --model deepseek-r1       # 64k context, fastest!
```

| Model | Context | Best For | Cost |
|-------|---------|----------|------|
| `claude-3.5-sonnet` | 200k | Reasoning, complex tasks | 🟢 Free |
| `gpt-4o` | 128k | General-purpose, balanced | 🟢 Free |
| `deepseek-r1` | 64k | Speed, cost efficiency | 🟢 Free |
| `grok-3` | 128k | Latest, edge cases | 🟢 Free |

**Rate Limits:** 15 requests/min (public preview) · [Full Setup Guide →](https://evals.javierzader.com/#/guide/github-models-setup)

---

## ⚙️ Configuration

<details>
<summary><strong>eval.yaml example</strong></summary>

```yaml
name: "My AI Skill Evaluation"
version: "1.0"
description: "Evaluate skill effectiveness with Control vs Treatment"

defaults:
  model: "claude-3.5-sonnet"
  provider: "github-models"
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
```

</details>

**Key sections:** `defaults` (LLM config) · `treatments` (A/B variants) · `tests` (prompts + evaluators)

**Evaluator types:** `regex` (pattern matching, fast) · `llm` (LLM-as-judge, flexible)

---

## 📋 Commands

| Command | Purpose |
|---------|---------|
| `md-evals init` | 🚀 Scaffold `eval.yaml` and `SKILL.md` templates |
| `md-evals run` | ▶️ Run evaluations (Control vs Treatment) |
| `md-evals run --treatment WITH_SKILL` | 🎯 Run specific treatment |
| `md-evals lint` | ✅ Validate SKILL.md (400-line limit, best practices) |
| `md-evals list` | 📋 List available treatments and tests |
| `md-evals list-models` | 🤖 List available models per provider |
| `md-evals smoke --provider github-models` | 🧪 Preflight auth check |

### Common Options

```bash
md-evals run -n 4                                              # 4 parallel workers
md-evals run --count 5                                         # Repeat 5× for statistical significance
md-evals run --output json > results.json                      # JSON export
md-evals run --output markdown > report.md                     # Markdown export
md-evals run --provider openai --model gpt-4o                  # Different provider
md-evals run -t WITH_SKILL                                      # Single treatment
```

<details>
<summary><strong>Full Options Reference</strong></summary>

#### `run`
- `-c, --config FILE` — Config file (default: `eval.yaml`)
- `-t, --treatment TREATMENT` — Run specific treatment(s)
- `-m, --model MODEL` — Override model
- `-p, --provider PROVIDER` — Provider: `github-models`, `openai`, `anthropic`, etc.
- `-n WORKERS` — Parallel workers (default: 1)
- `--count N` — Repeat tests N times for statistical validation
- `-o, --output FORMAT` — Output format: `table` (default), `json`, `markdown`
- `--no-lint` — Skip SKILL.md linting
- `--debug` — Enable debug logging

#### `list-models`
- `-p, --provider PROVIDER` — Filter by provider
- `-v, --verbose` — Show metadata (temperature ranges, costs, rate limits)

</details>

---

## 🔬 Advanced: Deterministic Graders

Beyond regex and LLM-as-judge, md-evals includes **deterministic graders** that check side effects (files, commands, workspace state) rather than LLM output text.

| Grader | Purpose |
|--------|---------|
| `FileExistsGrader` | Assert file exists (or doesn't) |
| `FileContentGrader` | Assert content matches regex/exact string |
| `FileSizeGrader` | Assert size within min/max byte range |
| `CommandGrader` | Run shell command, assert exit code + stdout |
| `StateGrader` | Compare workspace state before/after task |

<details>
<summary><strong>Three-Phase Pipeline, Contracts & Workspace Runner</strong></summary>

**Three-Phase Evaluation** (`ThreePhaseEvaluator`): Structure → Analyze → Generate with fail-fast. Graders: `JSONValidGrader`, `RequiredFieldsGrader`, `FieldTypeGrader`, `KeywordCoverageGrader`, `SectionCoverageGrader`, `MinLengthGrader`, `OutputMatchGrader`, `ConstraintGrader`.

**Contract Assertions** (`OutputContract`, `ContractAssertionGrader`, `ABContractGrader`): Define structural contracts (sections, format rules, forbidden patterns, word limits) and validate A/B variants.

**Workspace Runner** (`WorkspaceRunner`): Isolated temp directories for reproducible eval. Setup files → snapshot state → execute task → grade results → cleanup.

See [Full Docs](https://evals.javierzader.com/) for complete API reference.

</details>

---

## 🌐 Live Demo

<!-- TODO: Add screenshot here — Dashboard view of evaluation results -->
![Dashboard placeholder](https://placehold.co/800x400/1a1a2e/e94535?text=Dashboard+View+%28screenshot+or+GIF%29)

Experience md-evals interactively: **[evals.javierzader.com](https://evals.javierzader.com)**

---

---

**Key modules:** `engine.py` (A/B testing core) · `cli.py` (Typer) · `three_phase.py` (pipeline) · `workspace.py` (isolated eval) · `graders/` (deterministic) · `providers/` (multi-LLM)

---

## 🧪 Development

```bash
uv sync --extra dev && source .venv/bin/activate
pytest                          # Run all tests (321 passing, 94.95% coverage)
pytest -n 4                     # Parallel execution (73% faster)
pytest -m unit                   # Unit tests only
pytest --cov=md_evals           # Coverage report
```

| Metric | Value |
|--------|-------|
| Test count | 321+ |
| Code coverage | 94.95% |
| Serial execution | 22.09s |
| Parallel (4 workers) | 6.63s (73% faster) |

See **[TESTING.md](docs/TESTING.md)** for the full testing guide.

---

## 📖 Documentation & Community

- **[Full Guide](https://evals.javierzader.com/)** — Installation, tutorials, API reference
- **[GitHub Models Setup](https://evals.javierzader.com/#/guide/github-models-setup)** — Free LLM evaluation guide
- **[Examples](docs/examples/)** — Real-world usage examples
- **[CONTRIBUTING.md](CONTRIBUTING.md)** — Fork → Branch → PR workflow, code style, testing requirements
- **[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)** · **[SECURITY.md](SECURITY.md)**

---

<div align="center">

**[📦 PyPI](https://pypi.org/project/md-evals/)** · **[🌐 Live Demo](https://evals.javierzader.com)** · **[📖 Docs](https://evals.javierzader.com/)** · **[🐛 Issues](https://github.com/JNZader/md-evals/issues)** · **[💬 Discussions](https://github.com/JNZader/md-evals/discussions)**

Licensed under [MIT](LICENSE) · Inspired by [LangChain skills-benchmarks](https://github.com/langchain-ai/skills-benchmarks)

</div>