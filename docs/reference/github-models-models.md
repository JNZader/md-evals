<!-- docs/reference/github-models-models.md -->
# GitHub Models Reference

Complete reference for all GitHub Models supported by md-evals, including capabilities, pricing, and recommendations.

## Overview

GitHub Models provides **free and low-cost access** to four premier language models through Azure AI Inference. All models are available at no cost to GitHub users during the public preview phase.

> ✅ **All models are currently free** during public preview. Check [GitHub Models availability](https://github.com/marketplace/models) for pricing updates.

---

## Model Comparison Matrix

### Quick Reference

| Model | Provider | Context | Temp Range | Speed | Quality | Best For | Cost |
|-------|----------|---------|------------|-------|---------|----------|------|
| **claude-3.5-sonnet** | Anthropic | 200k | 0.0–2.0 | Fast | Excellent | Complex reasoning, instruction following | Free |
| **gpt-4o** | OpenAI | 128k | 0.0–2.0 | Medium | Excellent | General purpose, balanced performance | Free |
| **deepseek-r1** | DeepSeek | 64k | 0.0–1.0 | Fast | Good | Code generation, cost-efficient | Free |
| **grok-3** | xAI | 128k | 0.0–2.0 | Medium | Very Good | Real-time reasoning, latest capabilities | Free |

---

## Detailed Model Profiles

### 🔵 Claude 3.5 Sonnet

**Model ID**: `claude-3.5-sonnet`  
**Provider**: Anthropic  
**Release**: October 2024

#### Capabilities

| Aspect | Value |
|--------|-------|
| **Context Window** | 200,000 tokens (~150k words) |
| **Max Output** | 4,096 tokens |
| **Temperature Range** | 0.0–2.0 |
| **Accuracy** | 99% on standard benchmarks |
| **Reasoning** | Excellent (multimodal reasoning) |

#### Use Cases

✅ **Ideal for:**
- Complex instruction following
- Detailed analysis and summarization
- Long-context document processing (e.g., code reviews)
- Multi-step reasoning tasks
- SKILL.md evaluation (detailed system prompts)

❌ **Not ideal for:**
- Ultra-fast, latency-critical tasks
- Simple classification (overkill for simple tasks)

#### Configuration

```yaml
defaults:
  model: "claude-3.5-sonnet"
  provider: "github-models"
  temperature: 0.7  # 0 = deterministic, 1 = balanced, 2 = creative
```

#### Example Prompt

```python
prompt = """
Analyze the following skill definition and provide:
1. Summary of what the skill does
2. Potential edge cases
3. Suggestions for improvement

SKILL.md content:
[... long content ...]
"""
```

#### Performance Metrics

- **Input Speed**: ~1500 tokens/sec
- **Output Speed**: ~80 tokens/sec
- **Avg Response Time**: 1.5–2.5 seconds
- **Free Tier Rate Limit**: 15 requests/min

---

### 🟠 GPT-4o

**Model ID**: `gpt-4o`  
**Provider**: OpenAI  
**Release**: May 2024

#### Capabilities

| Aspect | Value |
|--------|-------|
| **Context Window** | 128,000 tokens (~100k words) |
| **Max Output** | 4,096 tokens |
| **Temperature Range** | 0.0–2.0 |
| **Accuracy** | 98% on standard benchmarks |
| **Reasoning** | Very good (strong on math/logic) |

#### Use Cases

✅ **Ideal for:**
- General-purpose evaluations
- Balanced speed and quality
- Mathematical reasoning
- Code analysis
- When model diversity is needed (A/B testing providers)

❌ **Not ideal for:**
- Ultra-long context (>128k tokens)
- Open-ended creative writing

#### Configuration

```yaml
defaults:
  model: "gpt-4o"
  provider: "github-models"
  temperature: 1.0  # Balanced
```

#### Example Prompt

```python
prompt = """
Evaluate this code snippet for:
1. Correctness
2. Performance
3. Security issues

Code:
[... code ...]
"""
```

#### Performance Metrics

- **Input Speed**: ~2000 tokens/sec
- **Output Speed**: ~100 tokens/sec
- **Avg Response Time**: 1.0–2.0 seconds
- **Free Tier Rate Limit**: 15 requests/min

---

### 🔴 DeepSeek R1

**Model ID**: `deepseek-r1`  
**Provider**: DeepSeek  
**Release**: January 2025

#### Capabilities

| Aspect | Value |
|--------|-------|
| **Context Window** | 64,000 tokens (~50k words) |
| **Max Output** | 2,048 tokens |
| **Temperature Range** | 0.0–1.0 |
| **Accuracy** | 97% on standard benchmarks |
| **Reasoning** | Good (optimized for code) |

#### Use Cases

✅ **Ideal for:**
- Code generation and analysis
- Cost-optimized evaluations
- Programming task evaluation
- Quick feedback loops
- High-volume evaluation runs

❌ **Not ideal for:**
- Very large context requirements
- Long, open-ended creative writing

#### Configuration

```yaml
defaults:
  model: "deepseek-r1"
  provider: "github-models"
  temperature: 0.5  # Lower for code, more deterministic
```

#### Example Prompt

```python
prompt = """
Generate a Python function that:
- Accepts a list of numbers
- Returns the sum of even numbers
- Handles edge cases

Include tests.
"""
```

#### Performance Metrics

- **Input Speed**: ~2500 tokens/sec (fastest input)
- **Output Speed**: ~120 tokens/sec
- **Avg Response Time**: 0.8–1.5 seconds (fastest overall)
- **Free Tier Rate Limit**: 15 requests/min

---

### 🟡 Grok-3

**Model ID**: `grok-3`  
**Provider**: xAI  
**Release**: December 2024

#### Capabilities

| Aspect | Value |
|--------|-------|
| **Context Window** | 128,000 tokens (~100k words) |
| **Max Output** | 4,096 tokens |
| **Temperature Range** | 0.0–2.0 |
| **Accuracy** | 98% on standard benchmarks |
| **Reasoning** | Very good (real-time aware) |

#### Use Cases

✅ **Ideal for:**
- Current events/real-time reasoning
- Balanced speed and quality
- Testing provider diversity
- General-purpose tasks
- When you need latest reasoning capabilities

❌ **Not ideal for:**
- Ultra-long context (>128k)
- Extremely sensitive tasks (newer model)

#### Configuration

```yaml
defaults:
  model: "grok-3"
  provider: "github-models"
  temperature: 0.7
```

#### Example Prompt

```python
prompt = """
Explain the latest AI developments and their implications.
Current date: [system provides current date]
"""
```

#### Performance Metrics

- **Input Speed**: ~1800 tokens/sec
- **Output Speed**: ~90 tokens/sec
- **Avg Response Time**: 1.2–2.2 seconds
- **Free Tier Rate Limit**: 15 requests/min

---

## Feature Comparison Chart

### Input Capabilities

| Feature | Claude | GPT-4o | DeepSeek | Grok-3 |
|---------|--------|--------|----------|--------|
| Text Input | ✅ | ✅ | ✅ | ✅ |
| Long Context (200k) | ✅ | ❌ | ❌ | ❌ |
| System Prompts | ✅ | ✅ | ✅ | ✅ |
| Temperature Control | ✅ | ✅ | ✅ | ✅ |
| Max Tokens Limit | ✅ | ✅ | ✅ | ✅ |

### Output Quality

| Aspect | Claude | GPT-4o | DeepSeek | Grok-3 |
|--------|--------|--------|----------|--------|
| Instruction Following | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Code Generation | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Math Reasoning | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Creative Writing | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Consistency | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

---

## Rate Limits & Quotas

### Free Tier (Public Preview)

| Limit | Value |
|-------|-------|
| **Requests per minute** | 15 |
| **Requests per hour** | 300 |
| **Requests per day** | 1,000 |
| **Concurrent connections** | 3 |
| **Cost** | $0 (free during public preview) |

### Handling Rate Limits

If you exceed rate limits, md-evals automatically:
1. **Detects** the 429 HTTP error
2. **Raises** `RateLimitError` with retry-after info
3. **Suggests** caching or serial execution

**Workaround**: Run with fewer parallel workers

```bash
# Default: 5 parallel workers (uses 5 req/min)
md-evals run eval.yaml -n 1  # Use 1 worker (15 req/min available)
```

---

## Selecting the Right Model

### Decision Tree

```
START
  ↓
Need context > 128k tokens?
  ├─ YES → Use claude-3.5-sonnet (200k context)
  ├─ NO
    ↓
    Need fastest speed?
      ├─ YES → Use deepseek-r1
      ├─ NO
        ↓
        Need best code generation?
          ├─ YES → Use gpt-4o or deepseek-r1
          ├─ NO
            ↓
            Need real-time awareness?
              ├─ YES → Use grok-3
              ├─ NO → Use claude-3.5-sonnet (safest choice)
```

### Common Use Cases

**A/B Testing Multiple Models**

```yaml
# eval.yaml
defaults:
  provider: "github-models"
  temperature: 0.7

treatments:
  CONTROL_CLAUDE:
    model: "claude-3.5-sonnet"
    skill_path: null
  
  TREATMENT_CLAUDE:
    model: "claude-3.5-sonnet"
    skill_path: "./SKILL.md"
  
  CONTROL_GPT:
    model: "gpt-4o"
    skill_path: null
  
  TREATMENT_GPT:
    model: "gpt-4o"
    skill_path: "./SKILL.md"

tests:
  # ... your tests
```

Run with: `md-evals run eval.yaml`

**Cost-Optimized Evaluation**

```yaml
defaults:
  model: "deepseek-r1"  # Fastest, lowest latency
  provider: "github-models"
```

**Long Document Processing**

```yaml
defaults:
  model: "claude-3.5-sonnet"  # Only 200k context available
  provider: "github-models"
```

---

## Token Counting

GitHub Models provides token counts for billing and analysis. Counts are:

- **Approximate**: ±10% accuracy for typical responses
- **Per-model**: Different tokenizers for each model
- **Streamed**: Extracted from response metadata automatically

Example output:

```
Model: claude-3.5-sonnet
Prompt: "Explain AI in 100 words"
Response: "AI is... [50 words]"
Input tokens: 9
Output tokens: 51
Total tokens: 60
```

Token counts appear in results:

```bash
md-evals run eval.yaml -o markdown
# Shows: "Total tokens used: 1,234" in report
```

---

## Pricing & Cost Tracking

### Current Pricing (Public Preview)

**All models are free during public preview** on GitHub Models.

After preview ends, expected pricing:
- **Claude 3.5 Sonnet**: ~$0.003 input / $0.015 output (per 1k tokens)
- **GPT-4o**: ~$0.003 input / $0.012 output (per 1k tokens)
- **DeepSeek R1**: ~$0.0014 input / $0.0042 output (per 1k tokens)
- **Grok-3**: ~$0.002 input / $0.006 output (per 1k tokens)

### Estimating Evaluation Cost

```
Cost = (input_tokens * input_price + output_tokens * output_price) * model_count * test_count

Example:
- 100 input tokens per request
- 50 output tokens per response
- 1 model (claude-3.5-sonnet)
- 100 tests
- 2 treatments (control + with skill)

Cost ≈ (100 × $0.003 + 50 × $0.015) × 1 × 100 × 2 ≈ $2.10
```

Track token usage in results:

```bash
md-evals run eval.yaml -o json | jq '.summary.total_tokens'
```

---

## FAQ

**Q: Which model should I start with?**  
A: Start with `claude-3.5-sonnet`. It has the largest context window and best instruction-following. It's the safest choice for evaluating skills.

**Q: Can I switch models between runs?**  
A: Yes! Change the `model` field in `eval.yaml` or use `md-evals run --model gpt-4o`

**Q: Are token counts exact?**  
A: Approximate (±10%). Different models use different tokenizers. Exact counts require an extra API call, which we avoid for performance.

**Q: What's the difference between prompt and response tokens?**  
A: Input tokens = your prompt, Output tokens = model's response. You pay for both.

**Q: Can I use GitHub Models in my own application?**  
A: Yes! Azure AI Inference SDK is open. See [Design documentation](https://github.com/JNZader/md-evals/blob/main/openspec/changes/github-models-integration/design.md).

**Q: Where can I report issues with models?**  
A: Report to [GitHub Models Issues](https://github.com/marketplace/models/issues)

---

## Next Steps

- [Getting Started Guide](../guide/github-models-setup.md) — Set up your token
- [Example Configurations](../examples/github-models-evaluation.md) — Real eval configs
- [Troubleshooting](../troubleshooting/github-models-issues.md) — Common problems
