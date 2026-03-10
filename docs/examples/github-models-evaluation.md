<!-- docs/examples/github-models-evaluation.md -->
# GitHub Models Evaluation Examples

Real-world examples of using GitHub Models with md-evals for skill evaluation.

## Example 1: Basic Skill Evaluation

Evaluate a simple skill with GitHub Models as the backbone.

### SKILL.md

```markdown
# Example Skill

This skill helps format user messages clearly.

## Instructions

1. Keep responses concise (under 100 words)
2. Use markdown formatting
3. Always include at least one example
```

### eval.yaml

```yaml
name: "GitHub Models Skill Evaluation"
version: "1.0"

defaults:
  provider: "github-models"
  model: "claude-3.5-sonnet"
  temperature: 0.7

treatments:
  CONTROL:
    description: "Without skill"
    skill_path: null
  
  WITH_SKILL:
    description: "With formatting skill"
    skill_path: "./SKILL.md"

tests:
  - name: "test_greeting"
    prompt: "Say hello to a new user"
    evaluators:
      - type: "regex"
        name: "has_greeting"
        pattern: "hello|hi|welcome"

  - name: "test_format"
    prompt: "List three benefits of AI"
    evaluators:
      - type: "regex"
        name: "has_list"
        pattern: "[-*•]|\\d\\."  # Looks for bullet or numbered list

  - name: "test_example"
    prompt: "Explain machine learning"
    evaluators:
      - type: "regex"
        name: "has_example"
        pattern: "example|for instance"
```

### Run the Evaluation

```bash
# Set your token
export GITHUB_TOKEN="github_pat_..."

# Run evaluation
md-evals run eval.yaml

# Results:
# ┌─────────────────────────────────────┐
# │ Test Summary                        │
# ├─────────────────────────────────────┤
# │ test_greeting      CONTROL: 85%     │
# │                    WITH_SKILL: 95%  │
# │ test_format        CONTROL: 60%     │
# │                    WITH_SKILL: 95%  │
# │ test_example       CONTROL: 70%     │
# │                    WITH_SKILL: 90%  │
# └─────────────────────────────────────┘
```

---

## Example 2: Multi-Model Comparison

Compare how different models respond to the same skill.

### eval.yaml

```yaml
name: "Multi-Model Comparison"
version: "1.0"

defaults:
  provider: "github-models"
  temperature: 0.7

treatments:
  # Test with Claude (best for reasoning)
  CLAUDE_CONTROL:
    model: "claude-3.5-sonnet"
    skill_path: null
  
  CLAUDE_WITH_SKILL:
    model: "claude-3.5-sonnet"
    skill_path: "./SKILL.md"
  
  # Test with GPT-4 (balanced)
  GPT_CONTROL:
    model: "gpt-4o"
    skill_path: null
  
  GPT_WITH_SKILL:
    model: "gpt-4o"
    skill_path: "./SKILL.md"
  
  # Test with DeepSeek (fastest/cheapest)
  DEEPSEEK_CONTROL:
    model: "deepseek-r1"
    skill_path: null
  
  DEEPSEEK_WITH_SKILL:
    model: "deepseek-r1"
    skill_path: "./SKILL.md"

tests:
  - name: "test_code_quality"
    prompt: "Write a Python function to check if a string is a palindrome"
    variables: {}
    evaluators:
      - type: "regex"
        name: "has_function"
        pattern: "def "
      
      - type: "regex"
        name: "has_docstring"
        pattern: '""".*"""'
      
      - type: "regex"
        name: "has_test"
        pattern: "assert|test|Test"

  - name: "test_explanation"
    prompt: "Explain the concept of recursion in simple terms"
    evaluators:
      - type: "regex"
        name: "has_example"
        pattern: "example|factorial|tree"

  - name: "test_format"
    prompt: "Create a summary of AI ethics"
    evaluators:
      - type: "regex"
        name: "is_structured"
        pattern: "[\\n#-]"  # Has sections or lists
```

### Run with Analysis

```bash
# Run all treatments
md-evals run eval.yaml --count 5 -n 1

# Output to JSON for analysis
md-evals run eval.yaml --count 5 -o json > results.json

# Analyze with jq:
# Compare pass rates by treatment
jq '.treatments | keys[] as $k | "\($k): \(.[$k].pass_rate)"' results.json

# Compare average tokens used per model
jq '.treatments | to_entries[] | {model: (.key | split("_")[0]), tokens: .value.total_tokens}' results.json
```

---

## Example 3: Cost-Optimized Large Batch

Run high-volume evaluation with the cheapest model.

### eval.yaml

```yaml
name: "Large Batch Evaluation"
version: "1.0"

defaults:
  provider: "github-models"
  model: "deepseek-r1"  # Fastest + lowest cost
  temperature: 0.5     # Lower = more deterministic

treatments:
  CONTROL:
    skill_path: null
  
  WITH_SKILL:
    skill_path: "./SKILL.md"

tests:
  # Generate 100 test cases for comprehensive evaluation
  - name: "test_simple_prompt_{{ i }}"
    prompt: "Respond to: Hello, how are you?"
    evaluators:
      - type: "regex"
        name: "is_responsive"
        pattern: ".+"  # At least some response
```

### Cost Analysis

```bash
# Estimate before running full batch
# ~100 tests × 2 treatments × 50 input tokens × $0.0014/1k = ~$0.14

# Run just 10 to verify first
md-evals run eval.yaml --count 10 -n 5

# Track tokens:
md-evals run eval.yaml --count 100 -n 5 -o json | jq '.summary.total_tokens'
# Example output: 15234 tokens
# Cost: (15234 / 1000) × $0.0014 = ~$0.02 per run
```

---

## Example 4: LLM-as-Judge Evaluation

Use another GitHub Model to evaluate responses (meta-evaluation).

### eval.yaml

```yaml
name: "LLM-as-Judge with GitHub Models"
version: "1.0"

defaults:
  provider: "github-models"
  temperature: 0.7

treatments:
  CONTROL:
    model: "claude-3.5-sonnet"  # Test model
    skill_path: null
  
  WITH_SKILL:
    model: "claude-3.5-sonnet"  # Test model
    skill_path: "./SKILL.md"

tests:
  - name: "test_helpfulness"
    prompt: "What is the best way to learn Python?"
    evaluators:
      # First: regex for quick checks
      - type: "regex"
        name: "mentions_resources"
        pattern: "book|course|practice|project"
      
      # Second: Use GPT-4o as judge for deeper evaluation
      - type: "llm"
        name: "judge_helpfulness"
        model: "gpt-4o"  # Judge model
        prompt: |
          Rate this response's helpfulness on a scale of 1-5.
          Consider: clarity, actionability, completeness.
          
          Response: {response}
          
          Respond with ONLY a number 1-5.
        success_condition: "[4-5]"  # Pass if score 4 or 5

  - name: "test_accuracy"
    prompt: "What is 2+2?"
    evaluators:
      - type: "llm"
        name: "judge_accuracy"
        model: "deepseek-r1"  # Cheap judge
        prompt: "Is this answer mathematically correct? Response: {response}. Answer yes/no."
        success_condition: "yes"
```

### Run

```bash
md-evals run eval.yaml

# Note: This uses tokens from:
# 1. claude-3.5-sonnet for initial responses (CONTROL + WITH_SKILL)
# 2. gpt-4o for judge evaluation (extra tokens)
# Total token cost is approximately 2-3x single-model evaluation
```

---

## Example 5: Configuration per Environment

Use different models based on development stage.

### eval.yaml

```yaml
name: "Environment-Aware Evaluation"
version: "1.0"

defaults:
  provider: "github-models"

# These values override based on environment
# Set via CLI: md-evals run --model gpt-4o
treatments:
  CONTROL:
    model: "{{ MODEL | default('deepseek-r1') }}"
    skill_path: null
  
  WITH_SKILL:
    model: "{{ MODEL | default('deepseek-r1') }}"
    skill_path: "./SKILL.md"

tests:
  - name: "test_prompt_quality"
    prompt: "What is quantum computing?"
    evaluators:
      - type: "regex"
        name: "has_content"
        pattern: ".{100,}"  # Minimum 100 chars
```

### Usage

```bash
# Development: Use fast + cheap DeepSeek (default)
md-evals run eval.yaml

# Staging: Use balanced GPT-4o
md-evals run eval.yaml --model gpt-4o

# Production: Use best Claude
md-evals run eval.yaml --model claude-3.5-sonnet
```

---

## Example 6: Temperature Tuning

Test how temperature affects skill effectiveness.

### eval.yaml

```yaml
name: "Temperature Sensitivity Analysis"
version: "1.0"

defaults:
  provider: "github-models"
  model: "gpt-4o"

treatments:
  # Deterministic: temp = 0
  COLD_CONTROL:
    temperature: 0.0
    skill_path: null
  
  COLD_WITH_SKILL:
    temperature: 0.0
    skill_path: "./SKILL.md"
  
  # Balanced: temp = 1
  WARM_CONTROL:
    temperature: 1.0
    skill_path: null
  
  WARM_WITH_SKILL:
    temperature: 1.0
    skill_path: "./SKILL.md"
  
  # Creative: temp = 2
  HOT_CONTROL:
    temperature: 2.0
    skill_path: null
  
  HOT_WITH_SKILL:
    temperature: 2.0
    skill_path: "./SKILL.md"

tests:
  - name: "test_consistency"
    prompt: "Write a haiku about AI"
    evaluators:
      - type: "regex"
        name: "is_creative"
        pattern: "poetry|haiku"

  - name: "test_variability"
    prompt: "List three AI applications"
    evaluators:
      - type: "regex"
        name: "has_list"
        pattern: "[1-3]\\.|[-*]"
```

### Analysis

```bash
# Run with repetitions to measure variance
md-evals run eval.yaml --count 10

# Lower temperature (0.0) = more consistent results
# Higher temperature (2.0) = more variable results
# Analyze consistency per treatment
```

---

## Example 7: Skill Variant Testing

Test multiple versions of a skill with the same evaluation.

### Project Structure

```
project/
├── eval.yaml
├── skills/
│   ├── v1-basic.md
│   ├── v2-enhanced.md
│   ├── v3-experimental.md
│   └── baseline.md
```

### eval.yaml

```yaml
name: "Skill Variant Comparison"
version: "1.0"

defaults:
  provider: "github-models"
  model: "claude-3.5-sonnet"
  temperature: 0.7

treatments:
  BASELINE:
    description: "No skill (baseline)"
    skill_path: null
  
  SKILL_V1:
    description: "Basic skill"
    skill_path: "./skills/v1-basic.md"
  
  SKILL_V2:
    description: "Enhanced skill"
    skill_path: "./skills/v2-enhanced.md"
  
  SKILL_V3:
    description: "Experimental skill"
    skill_path: "./skills/v3-experimental.md"

tests:
  - name: "test_accuracy"
    prompt: "Answer: What is 2+2?"
    evaluators:
      - type: "regex"
        name: "correct_answer"
        pattern: "4"

  - name: "test_clarity"
    prompt: "Explain recursion"
    evaluators:
      - type: "regex"
        name: "has_example"
        pattern: "example"

  - name: "test_tone"
    prompt: "Greet a customer"
    evaluators:
      - type: "regex"
        name: "is_friendly"
        pattern: "hi|hello|welcome"
```

### Run

```bash
# Run all skill variants
md-evals run eval.yaml -n 3

# Compare results
md-evals run eval.yaml -o markdown > results.md

# Identify best performing variant
```

---

## Example 8: Minimal Configuration

Simplest possible evaluation with GitHub Models.

### eval.yaml

```yaml
# Minimal config - uses all defaults
name: "Quick Test"

defaults:
  provider: "github-models"
  model: "claude-3.5-sonnet"

treatments:
  CONTROL:
  WITH_SKILL:
    skill_path: "./SKILL.md"

tests:
  - name: "test_basic"
    prompt: "Hello"
    evaluators:
      - type: "regex"
        pattern: "."  # Non-empty response
```

### Run

```bash
md-evals run eval.yaml
```

---

## Quick Reference: Common Patterns

### Use Claude for complex reasoning
```yaml
defaults:
  model: "claude-3.5-sonnet"
```

### Use DeepSeek for speed + cost
```yaml
defaults:
  model: "deepseek-r1"
```

### Use GPT-4o for balance
```yaml
defaults:
  model: "gpt-4o"
```

### Use Grok-3 for current events
```yaml
defaults:
  model: "grok-3"
```

### Low temperature for consistency
```yaml
defaults:
  temperature: 0.0
```

### High temperature for creativity
```yaml
defaults:
  temperature: 2.0
```

---

## Troubleshooting Examples

### Example: Rate Limit Hit During Batch

```bash
# Original (failed):
md-evals run eval.yaml -n 10 --count 50
# ERROR: Rate limit exceeded

# Solution: Use 1 worker
md-evals run eval.yaml -n 1 --count 50  # ✅ 15 req/min = 1 req every 4 seconds
```

### Example: Token Counting Unexpected

```bash
# Check actual token usage:
md-evals run eval.yaml --count 1 -o json | jq '.treatments.CONTROL.total_tokens'

# Token counts are approximate:
# - Claude: might be slightly different from API's internal count
# - Varies by language/encoding
# - ±10% variance is expected
```

### Example: Empty Responses from Model

```yaml
# If models are returning empty responses:
defaults:
  temperature: 0.5  # Try mid-range temperature
  
# And check skill:
# - Is skill overriding system prompt incorrectly?
# - Is prompt too vague?
```

---

## Next Steps

- [Models Reference](../reference/github-models-models.md) — Detailed model comparison
- [Setup Guide](../guide/github-models-setup.md) — Token configuration
- [Troubleshooting](../troubleshooting/github-models-issues.md) — Common issues
