<!-- docs/troubleshooting/faq.md -->
# FAQ

## What is md-evals?

md-evals is a CLI tool for evaluating AI skills (SKILL.md files) by comparing Control (no skill) vs Treatment (with skill) prompts.

## Why use md-evals?

- Lightweight and local-first
- Model-agnostic (works with any LLM)
- Easy to set up and use
- Inspired by LangChain skills-benchmarks

## Which models are supported?

Any model supported by LiteLLM, including:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Google Gemini
- Azure OpenAI
- Ollama (local)

## How does CONTROL work?

CONTROL runs the bare prompt without any skill injection, providing a baseline for comparison.

## What's the 400-line limit?

The linter enforces a max of 400 lines in SKILL.md to encourage concise, actionable skills.

## Can I use my own models?

Yes! Just set the model and provider in eval.yaml:
```yaml
defaults:
  model: "your-model"
  provider: "openai"  # or any other provider
```

## Is it free?

md-evals is open source (MIT license), but you'll need to pay for API calls to the LLM providers.
