<!-- docs/README.md -->
# md-evals

> Lightweight CLI tool for evaluating AI skills (SKILL.md) with Control vs Treatment testing

## Features

- **A/B Testing** - Compare Control (no skill) vs Treatment (with skill) prompts
- **Multiple Treatments** - Run wildcards like `LCC_*`
- **Hybrid Evaluation** - Regex + LLM-as-a-judge
- **Linter** - Enforce 400-line limit for SKILL.md
- **Rich Output** - Beautiful terminal tables

## Quick Links

- [Getting Started](./guide/getting-started.md)
- [Quick Start](./guide/quick-start.md)
- [Configuration](./guide/configuration.md)
- [Examples](./examples/basic-evaluation.md)

## Installation

```bash
pip install md-evals
```

## Quick Start

```bash
md-evals init my-evaluation
cd my-evaluation
md-evals run
```

## Sponsor

[Star on GitHub](https://github.com/JNZader/md-evals)
