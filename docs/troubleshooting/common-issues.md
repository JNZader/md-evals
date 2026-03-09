<!-- docs/troubleshooting/common-issues.md -->
# Common Issues

## "API key not found"

Set your API key:
```bash
export OPENAI_API_KEY="sk-..."
```

## "Model not found"

Check the model name. Use the format:
- `provider/model` (e.g., `openai/gpt-4o`)

## "Config file not found"

Run from the correct directory:
```bash
cd my-evaluation
md-evals run
```

Or specify the path:
```bash
md-evals run --config path/to/eval.yaml
```

## "SKILL.md exceeds 400 lines"

Keep your SKILL.md concise. See [Linting](../guide/linting.md).

## "LLM API error"

- Check your API key
- Check your quota/credits
- Try a different model

## "Timeout"

Increase timeout in eval.yaml:
```yaml
defaults:
  timeout: 120
```
