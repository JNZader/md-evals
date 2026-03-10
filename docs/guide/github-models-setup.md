<!-- docs/guide/github-models-setup.md -->
# Getting Started with GitHub Models

GitHub Models provides **free and low-cost LLM access** directly from your GitHub account. This guide will walk you through setting up and using GitHub Models with md-evals.

> 💡 **Why GitHub Models?** Get free API access to powerful models like Claude 3.5 Sonnet, GPT-4, DeepSeek R1, and Grok 3 with no credit card required.

## What You'll Need

- A **GitHub account** (free or paid)
- A **GitHub Personal Access Token** (PAT)
- md-evals installed (`pip install md-evals`)

## Step 1: Create a GitHub Personal Access Token

GitHub Models are accessed through the Azure AI Inference API, authenticated with your GitHub account.

### Generate Your Token

1. Go to [GitHub Settings → Tokens](https://github.com/settings/tokens)
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. Give it a descriptive name like `"md-evals-github-models"`
4. Select scopes (minimum required):
   - ☑️ **repo** (Full control of private repositories)
   - ☑️ **user** (Read user profile data)
5. Click **"Generate token"**
6. **Copy the token immediately** — you won't see it again!

*[See GitHub Settings → Tokens page](https://github.com/settings/tokens)*

### Token Format

Your token will look like:
```
github_pat_11A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q7R8S9T0U1V2W3X4Y5Z6A7B8C
```

## Step 2: Set Your GITHUB_TOKEN

Once you have your token, add it to your environment.

### Option A: Using Shell Profile (Persistent)

Add this line to your `~/.bash_profile`, `~/.zshrc`, or `~/.bashrc`:

```bash
export GITHUB_TOKEN="github_pat_11A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q7R8S9T0U1V2W3X4Y5Z6A7B8C"
```

Then reload your shell:

```bash
source ~/.bash_profile  # or ~/.zshrc
```

### Option B: Using .env File (Project-Local)

Create a `.env` file in your project root:

```bash
# .env
GITHUB_TOKEN=github_pat_11A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q7R8S9T0U1V2W3X4Y5Z6A7B8C
```

md-evals automatically loads `.env` files using `python-dotenv`.

### Option C: Command-Line Export (Temporary)

```bash
export GITHUB_TOKEN="github_pat_..."
md-evals run eval.yaml --provider github-models
```

> ⚠️ **Security Warning**: Never commit your token to git! Add `.env` to `.gitignore`.

## Step 3: Verify Your Token

Test your token without running a full evaluation:

```bash
python3 << 'EOF'
import os

token = os.getenv("GITHUB_TOKEN")
if token:
    if token.startswith("github_pat_"):
        print("✅ Token format valid")
    else:
        print("❌ Token does not start with 'github_pat_'")
else:
    print("❌ GITHUB_TOKEN not set")
EOF
```

## Step 4: List Available Models

See all supported models and their capabilities:

```bash
md-evals list-models --provider github-models
```

Output:
```
Provider: github-models
────────────────────────────────────────────────────────
Model               Context    Temperature    Rate Limit
────────────────────────────────────────────────────────
claude-3.5-sonnet   200,000    0.0–2.0       15 req/min
gpt-4o              128,000    0.0–2.0       15 req/min
deepseek-r1         64,000     0.0–1.0       15 req/min
grok-3              128,000    0.0–2.0       15 req/min
────────────────────────────────────────────────────────
```

## Step 5: Run Your First Evaluation

Create an `eval.yaml` file:

```yaml
name: "GitHub Models Test"
version: "1.0"

defaults:
  model: "claude-3.5-sonnet"
  provider: "github-models"
  temperature: 0.7

treatments:
  CONTROL:
    description: "Baseline"
    skill_path: null
  
  WITH_SKILL:
    description: "With skill"
    skill_path: "./SKILL.md"

tests:
  - name: "test_greeting"
    prompt: "Say hello!"
    evaluators:
      - type: "regex"
        name: "has_hello"
        pattern: "hello|hi"
```

Run the evaluation:

```bash
md-evals run eval.yaml
```

Success! 🎉 You're now using GitHub Models with md-evals.

---

## Troubleshooting

### "GITHUB_TOKEN not set"

**Problem**: Error message says `GITHUB_TOKEN` not configured

**Solution**:
1. Verify token is set: `echo $GITHUB_TOKEN`
2. If empty, set it: `export GITHUB_TOKEN="github_pat_..."`
3. If using `.env` file, ensure it's in your current directory
4. Restart your terminal or IDE

### "Invalid token format"

**Problem**: Token doesn't start with `github_pat_`

**Solution**:
1. Generate a new token at [GitHub Settings → Tokens](https://github.com/settings/tokens)
2. Use the new token starting with `github_pat_`
3. Classic PATs (old format) may be deprecated

### "Rate limit exceeded"

**Problem**: `RateLimitError: GitHub Models rate limit exceeded. Free tier: 15 requests/min`

**Solutions**:
- **Wait**: GitHub Models uses a rolling 1-minute window. Wait 1–2 minutes before retrying.
- **Batch requests**: Reduce parallel workers with `-n 1`
- **Cache responses**: Use shorter evaluation runs during development
- **Upgrade**: GitHub Pro or Enterprise plan provides higher limits

Example:
```bash
# Run with 1 worker instead of default 5
md-evals run eval.yaml --provider github-models -n 1
```

### "Model not supported"

**Problem**: Model like `gpt-4` is not available

**Solution**:
Use one of the officially supported models:
- `claude-3.5-sonnet`
- `gpt-4o`
- `deepseek-r1`
- `grok-3`

See: [Models Reference](../reference/github-models-models.md)

### "Network timeout"

**Problem**: Request takes too long and times out

**Solutions**:
1. **Check your internet**: Ensure stable connection to `models.inference.ai.azure.com`
2. **Retry**: GitHub Models automatically retries up to 3 times with backoff
3. **Longer timeout**: Check your network connection; Azure endpoint should respond within 60 seconds
4. **Reduce prompt size**: Very large prompts may take longer

### "Empty response"

**Problem**: Model returns blank response

**Solution**:
- Try a simpler prompt
- Check model temperature (values closer to 0 are more deterministic)
- Verify your skill doesn't override system instructions incorrectly

## Next Steps

- [Models Reference](../reference/github-models-models.md) — Detailed comparison of all models
- [Example Configurations](../examples/github-models-evaluation.md) — Real-world eval configs
- [Advanced Configuration](./advanced.md) — Custom providers and skill injection
