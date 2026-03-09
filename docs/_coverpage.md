# md-evals

> Lightweight CLI tool for evaluating AI skills (SKILL.md) with Control vs Treatment testing

<span class="badge badge-primary">Python 3.12+</span>
<span class="badge badge-success">MIT License</span>
<span class="badge badge-primary">v0.1.0</span>

## Features

- **A/B Testing** - Compare Control (no skill) vs Treatment (with skill) prompts
- **Multiple Treatments** - Run wildcards like `LCC_*` to test multiple skill variations
- **Hybrid Evaluation** - Regex patterns + LLM-as-a-judge evaluation
- **Linter** - Enforce 400-line limit and best practices for SKILL.md
- **Rich Output** - Beautiful terminal tables with pass rates
- **Multi-Provider** - Works with OpenAI, Anthropic, Gemini, and more via LiteLLM

## Quick Links

- [Getting Started](./guide/getting-started.md) - Installation and setup
- [Quick Start](./guide/quick-start.md) - Run your first evaluation
- [Configuration](./guide/configuration.md) - Complete YAML reference
- [Examples](./examples/basic-evaluation.md) - Real-world use cases

## Why md-evals?

Inspired by [LangChain skills-benchmarks](https://github.com/langchain-ai/skills-benchmarks), md-evals provides a lightweight, local-first solution for evaluating AI skills.

## Sponsor

<a href="https://github.com/JNZader/md-evals" target="_blank">Star on GitHub</a>
