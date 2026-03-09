<!-- docs/guide/evaluators.md -->
# Evaluators

Evaluators determine whether an LLM response passes or fails a test.

## Regex Evaluator

Check if output contains a pattern:

```yaml
- type: "regex"
  name: "has_code"
  pattern: "def |class "
  pass_on_match: true  # Pass if pattern found
  fail_message: "Output should contain code"
```

## Exact Match Evaluator

Check for exact string match:

```yaml
- type: "exact-match"
  name: "exact_greeting"
  expected: "Hello, World!"
  case_sensitive: false
```

## LLM Judge Evaluator

Use another LLM to evaluate quality:

```yaml
- type: "llm-judge"
  name: "quality_score"
  judge_model: "gpt-4o"
  criteria: |
    Did the response correctly identify the core concepts?
    Rate from 1-5 with clear reasoning.
  output_schema:
    type: "object"
    properties:
      score:
        type: "integer"
        minimum: 1
        maximum: 5
      reasoning:
        type: "string"
    required: ["score", "reasoning"]
  pass_threshold: 0.8
```

The LLM Judge returns JSON with:
- `score`: 1-5 (normalized to 0-1)
- `reasoning`: Explanation of the score

## Multiple Evaluators

You can combine multiple evaluators:

```yaml
tests:
  - name: "code_test"
    prompt: "Write a function"
    evaluators:
      - type: "regex"
        name: "has_def"
        pattern: "def "
      - type: "regex"
        name: "has_return"
        pattern: "return "
      - type: "llm-judge"
        name: "quality"
        judge_model: "gpt-4o"
        criteria: "Is the code correct?"
        pass_threshold: 0.6
```

All evaluators must pass for the test to pass.
