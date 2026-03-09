<!-- docs/reference/environment.md -->
# Environment Variables

Configure API keys and settings via environment variables.

## Required API Keys

Set up at least one:

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
export AZURE_API_KEY="your-key"
export AZURE_API_BASE="https://your-resource.openai.azure.com"
export AZURE_API_VERSION="2024-02-01"
```

### Ollama (Local)
```bash
export OLLAMA_API_BASE="http://localhost:11434"
```

## LiteLLM Variables

```bash
# Optional LiteLLM settings
export LITELLM_DROP_PARAMS=true
export LITELLM_MAX_PARALLEL_REQUESTS=100
export LITELLM_REQUEST_TIMEOUT=60
```

## .env File

Create a `.env` file in your project:

```bash
# .env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

md-evals will automatically load from `.env` if present.
