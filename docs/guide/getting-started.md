<!-- docs/guide/getting-started.md -->
# Getting Started

This guide will help you install and set up md-evals.

## Requirements

- **Python 3.12 or higher**
- **API Key** for your LLM provider (OpenAI, Anthropic, Gemini, etc.)

## Installation

### Using pip

```bash
pip install md-evals
```

### Using uv (recommended)

```bash
uv pip install md-evals
```

### From source

```bash
git clone https://github.com/JNZader/md-evals.git
cd md-evals
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Verify Installation

```bash
md-evals --version
# Output: md-evals 0.1.0
```

## API Keys Configuration

md-evals uses LiteLLM, which supports multiple providers. Configure your API keys as environment variables:

### OpenAI

```bash
export OPENAI_API_KEY="sk-..."
```

### Anthropic

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Google Gemini

```bash
export GOOGLE_API_KEY="AIza..."
```

### Azure OpenAI

```bash
export AZURE_API_KEY="your-azure-key"
export AZURE_API_BASE="https://your-resource.openai.azure.com"
```

### Multiple Providers

You can configure multiple providers at once:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="AIza..."
```

## Quick Verification

Test your setup by running:

```bash
md-evals init my-evaluation
cd my-evaluation
md-evals lint
```

This creates a demo project and validates the SKILL.md file.

## Next Steps

- [Quick Start](./quick-start.md) - Run your first evaluation
- [Configuration](./configuration.md) - Learn about eval.yaml
