<!-- docs/troubleshooting/github-models-issues.md -->
# GitHub Models Troubleshooting Guide

Solutions to common problems when using GitHub Models with md-evals.

---

## Authentication Issues

### Problem: "GITHUB_TOKEN not set or invalid"

**Error Message:**
```
AuthenticationError: GITHUB_TOKEN environment variable not set or invalid
```

**Causes:**
- Environment variable not set
- Token has wrong format
- Token was revoked or expired

**Solutions:**

1. **Check if token is set:**
   ```bash
   echo $GITHUB_TOKEN
   ```
   
   If empty, set it:
   ```bash
   export GITHUB_TOKEN="github_pat_..."
   ```

2. **Verify token format:**
   Token should start with `github_pat_`
   ```bash
   echo $GITHUB_TOKEN | grep "^github_pat_"
   # If no output, token format is wrong
   ```

3. **Generate new token:**
   - Go to [GitHub Settings → Tokens](https://github.com/settings/tokens)
   - Click **"Generate new token (classic)"**
   - Select minimum scopes: `repo`, `user`
   - Copy the new token
   - Update your environment variable

4. **Using .env file:**
   ```bash
   # .env
   GITHUB_TOKEN=github_pat_YOUR_TOKEN_HERE
   ```
   
   Make sure `.env` is in your current directory and add to `.gitignore`:
   ```bash
   echo ".env" >> .gitignore
   ```

---

### Problem: "Invalid token format"

**Error Message:**
```
ValueError: Token must start with 'github_pat_'
```

**Cause:** Using old GitHub token format (not a PAT)

**Solution:**
- Delete old tokens: [GitHub Settings → Tokens](https://github.com/settings/tokens)
- Generate new **classic** PAT
- Verify it starts with `github_pat_`

---

### Problem: Token works locally but not in CI/CD

**Cause:** CI pipeline doesn't have `GITHUB_TOKEN` configured

**Solutions:**

For **GitHub Actions** (automatic):
```yaml
# .github/workflows/eval.yml
name: Evaluation
on: push

jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - run: pip install md-evals
      - run: md-evals run eval.yaml
        # GitHub Actions automatically sets GITHUB_TOKEN
```

For **other CI systems**:
```yaml
# Add GITHUB_TOKEN secret in CI configuration
# Then use it in your build:
script:
  - export GITHUB_TOKEN=${{ secrets.GITHUB_TOKEN }}
  - md-evals run eval.yaml
```

---

## Rate Limiting Issues

### Problem: "Rate limit exceeded"

**Error Message:**
```
RateLimitError: GitHub Models rate limit exceeded. Free tier: 15 requests/min
```

**Cause:** Exceeded 15 requests per minute limit

**Solutions:**

1. **Reduce parallel workers:**
   ```bash
   # Default: 5 workers = 5 requests/min
   # With 1 worker: 1 request every 4 seconds = 15 req/min limit
   md-evals run eval.yaml -n 1
   ```

2. **Increase delay between tests:**
   Add explicit delays in your eval.yaml:
   ```yaml
   tests:
     - name: "test_1"
       prompt: "First prompt"
       evaluators: [...]
       delay_ms: 4000  # Wait 4 seconds between requests
   ```

3. **Run fewer tests:**
   ```bash
   # Instead of 1000 tests, start with 10
   md-evals run eval.yaml --count 10
   ```

4. **Batch across multiple runs:**
   ```bash
   # Run in separate minute windows
   md-evals run eval.yaml --count 15  # ~1 minute
   sleep 60
   md-evals run eval.yaml --count 15  # Next minute
   ```

5. **Wait and retry:**
   ```bash
   # If rate limited, wait 1-2 minutes
   sleep 120
   md-evals run eval.yaml -n 1
   ```

### Rate Limit Guidelines

```
Free Tier Limits:
├─ 15 requests per minute
├─ 300 requests per hour
└─ 1,000 requests per day

Calculation:
- 1 test × 2 treatments = 2 requests
- 50 tests × 2 treatments = 100 requests per run
- At 15 req/min: 100 requests = ~7 minutes

With 1 worker (-n 1):
- Effective rate: 1 request every 4 seconds
- 100 requests = ~400 seconds = ~6.7 minutes ✅
```

---

## Model & Capability Issues

### Problem: "Model not found or not supported"

**Error Message:**
```
ModelNotSupportedError: 'gpt-2' is not supported. Available models: ['claude-3.5-sonnet', 'gpt-4o', 'deepseek-r1', 'grok-3']
```

**Cause:** Using unsupported model name

**Solution:**
Use one of the official supported models:
```yaml
defaults:
  model: "claude-3.5-sonnet"  # ✅ Supported
  # or
  model: "gpt-4o"              # ✅ Supported
  # or
  model: "deepseek-r1"         # ✅ Supported
  # or
  model: "grok-3"              # ✅ Supported
```

List available models:
```bash
md-evals list-models --provider github-models
```

---

### Problem: "Context window exceeded"

**Error Message:**
```
ContextWindowExceededError: Prompt exceeds model context window (200k tokens for claude-3.5-sonnet)
```

**Cause:** Prompt + skill is too large for the model

**Solutions:**

1. **Use a model with larger context:**
   ```yaml
   defaults:
     model: "claude-3.5-sonnet"  # 200k context (largest)
   ```

2. **Reduce prompt size:**
   ```yaml
   tests:
     - name: "test_summary"
       prompt: "Summarize: [short excerpt]"  # Not full document
   ```

3. **Reduce skill size:**
   - Split large SKILL.md into multiple files
   - Include only relevant sections in skill_path
   ```yaml
   treatments:
     WITH_SKILL:
       skill_path: "./skill-relevant-section.md"  # Smaller file
   ```

4. **Check context window breakdown:**
   ```
   Total tokens = system_prompt + skill + prompt + max_output
   
   Example:
   - System prompt: 100 tokens
   - Skill (SKILL.md): 500 tokens
   - User prompt: 200 tokens
   - Max output: 500 tokens (reserved)
   = 1,300 tokens (well within 200k limit)
   ```

---

## Network & Connectivity Issues

### Problem: "Network timeout" or "Connection refused"

**Error Message:**
```
TimeoutError: Request to models.inference.ai.azure.com timed out after 60 seconds
```

**Causes:**
- Slow internet connection
- Azure endpoint temporarily unavailable
- Firewall blocking requests

**Solutions:**

1. **Check internet connection:**
   ```bash
   ping -c 3 models.inference.ai.azure.com
   # Should show responses < 100ms
   ```

2. **Check if endpoint is accessible:**
   ```bash
   curl -I https://models.inference.ai.azure.com
   # Should return HTTP 200 or 400 (not connection error)
   ```

3. **Increase timeout:**
   ```bash
   # In eval.yaml (future feature):
   defaults:
     timeout_seconds: 120  # Increase from default 60
   ```

4. **Check firewall/proxy:**
   - Corporate firewalls may block Azure endpoints
   - Try from a different network (home WiFi, mobile hotspot)
   - Contact IT to whitelist `models.inference.ai.azure.com`

5. **Retry with backoff:**
   md-evals automatically retries 3 times with exponential backoff:
   ```
   Attempt 1: immediate
   Attempt 2: wait 1 second
   Attempt 3: wait 2 seconds
   Attempt 4: wait 4 seconds
   ```

---

## Response Quality Issues

### Problem: "Empty response" or "No content"

**Error Message:**
```
Response received but content is empty
```

**Causes:**
- Model refused to answer
- Prompt is ambiguous
- Very high temperature causing nonsense

**Solutions:**

1. **Try a clearer prompt:**
   ```yaml
   # ❌ Ambiguous
   prompt: "Hello"
   
   # ✅ Clear
   prompt: "Say hello to a customer in a friendly way"
   ```

2. **Lower temperature:**
   ```yaml
   defaults:
     temperature: 0.0  # Deterministic
   ```

3. **Add system constraints:**
   ```yaml
   treatments:
     WITH_SKILL:
       skill_path: "./SKILL.md"
       # SKILL.md should include:
       # "Always provide a response, even if uncertain"
   ```

4. **Check skill for conflicts:**
   If skill contradicts the prompt, model may refuse to respond:
   ```markdown
   # SKILL.md
   # ❌ BAD: "Never respond to greetings"
   # ✅ GOOD: "Respond to greetings warmly"
   ```

---

### Problem: "Inconsistent or random responses"

**Error Message:**
```
Same test produces different results each time
```

**Cause:** Temperature too high (creates randomness)

**Solution:**
Lower temperature for consistency:
```yaml
defaults:
  temperature: 0.0  # 0 = fully deterministic
  # or 0.3 for slightly less random, still varied
```

For creative responses, accept the variance or use `--count 1` for single runs.

---

## Billing & Token Issues

### Problem: "Unexpected token usage"

**Description:** More tokens used than expected

**Diagnosis:**
```bash
# Run single test and check token count
md-evals run eval.yaml --count 1 -o json | jq '.treatments[].total_tokens'

# Example: expected 100 tokens, got 250
# Reasons:
# 1. System prompt + skill are longer than expected
# 2. Model's responses are longer than typical
# 3. Tokenization includes formatting, whitespace
```

**Solutions:**

1. **Measure exact token usage:**
   ```bash
   # Run 1 test, check result
   md-evals run eval.yaml --count 1 -o json
   ```

2. **Optimize skill:**
   Remove verbose comments:
   ```markdown
   # ❌ Verbose
   # This section explains in detail how to handle user inputs
   # We need to be very careful and consider all edge cases
   
   # ✅ Concise
   # Handle all user inputs carefully
   ```

3. **Reduce prompt length:**
   Use shorter, more direct prompts

4. **Use cheaper model:**
   ```yaml
   defaults:
     model: "deepseek-r1"  # Cheapest option
   ```

---

## CLI & Configuration Issues

### Problem: "Provider not found"

**Error Message:**
```
ProviderError: Provider 'github_models' not found
```

**Cause:** Wrong provider name format

**Solutions:**

These are equivalent:
```bash
md-evals run --provider github-models      # ✅
md-evals run --provider "GitHub Models"    # ✅
md-evals run --provider github_models      # ✅ (alias)
```

Not equivalent:
```bash
md-evals run --provider github-models-azure  # ❌
md-evals run --provider "githubmodels"       # ❌
```

---

### Problem: "eval.yaml not found"

**Error Message:**
```
FileNotFoundError: eval.yaml not found
```

**Solution:**
```bash
# Create eval.yaml
md-evals init my-project
cd my-project

# Or specify path
md-evals run /path/to/eval.yaml
```

---

### Problem: "SKILL.md not found"

**Error Message:**
```
FileNotFoundError: ./SKILL.md not found
```

**Cause:** Path in eval.yaml doesn't exist

**Solution:**
```yaml
treatments:
  WITH_SKILL:
    # ❌ Wrong: file doesn't exist
    skill_path: "./skill.md"
    
    # ✅ Correct: file exists
    skill_path: "./SKILL.md"
```

Verify file exists:
```bash
ls -la SKILL.md
# If not found, create it:
touch SKILL.md
```

---

## Debugging

### Enable Debug Logging

To see detailed information about what's happening:

```bash
# Set debug environment variable
export DEBUG=true
md-evals run eval.yaml

# Output will show:
# DEBUG: Loading GITHUB_TOKEN from environment
# DEBUG: Initializing GitHubModelsProvider with model=claude-3.5-sonnet
# DEBUG: Request 1/10: "Say hello..." 
# DEBUG: Response tokens: 45
# DEBUG: Total time: 1.2s
```

### Check Raw API Response

To see what Azure is returning:

```bash
# Set verbose output
export VERBOSE=true
md-evals run eval.yaml -n 1

# Shows raw response headers, timing, etc.
```

### Test Token Directly

```python
import os
from md_evals.providers.github_models import GitHubModelsProvider

token = os.getenv("GITHUB_TOKEN")
provider = GitHubModelsProvider(model_name="claude-3.5-sonnet", github_token=token)

# Try a simple completion
response = provider.complete("Hello!")
print(f"Response: {response.content}")
print(f"Tokens: {response.tokens}")
print(f"Time: {response.duration_ms}ms")
```

---

## Common Error Reference

| Error | Cause | Fix |
|-------|-------|-----|
| `GITHUB_TOKEN not set` | Missing token | Set `export GITHUB_TOKEN=...` |
| `Rate limit exceeded` | Too many requests | Use `-n 1` or wait 1 minute |
| `Model not supported` | Wrong model name | Use claude-3.5-sonnet, gpt-4o, deepseek-r1, or grok-3 |
| `Context window exceeded` | Prompt too large | Use claude-3.5-sonnet or reduce prompt size |
| `Timeout` | Network issue | Check internet, increase timeout |
| `Empty response` | Model refused | Clarify prompt, lower temperature |
| `Token count high` | Unexpected usage | Check skill size, reduce verbosity |

---

## Getting Help

If you're still having issues:

1. **Check the logs:**
   ```bash
   md-evals run eval.yaml 2>&1 | tee run.log
   # Review run.log for error details
   ```

2. **Test minimal config:**
   ```bash
   # Create test.yaml with just one test
   md-evals run test.yaml -n 1 --count 1
   ```

3. **Verify environment:**
   ```bash
   echo "Token: $GITHUB_TOKEN"
   python --version
   pip list | grep md-evals
   ```

4. **Report issue:**
   Create issue with:
   - Error message (full output)
   - Your eval.yaml (sanitized)
   - Output of: `python --version`, `md-evals --version`
   - Steps to reproduce

---

## Next Steps

- [Setup Guide](../guide/github-models-setup.md) — Token configuration
- [Models Reference](../reference/github-models-models.md) — Model details
- [Example Configs](../examples/github-models-evaluation.md) — Real examples
