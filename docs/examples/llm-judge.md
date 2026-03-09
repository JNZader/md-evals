<!-- docs/examples/llm-judge.md -->
# LLM Judge Example

Use an LLM to evaluate subjective quality.

```yaml
tests:
  - name: "response_quality"
    prompt: "Explain {topic}"
    variables:
      topic: "quantum computing"
    evaluators:
      - type: "llm-judge"
        name: "accuracy_score"
        judge_model: "gpt-4o"
        criteria: |
          Did the response correctly explain the core concepts?
          Rate accuracy from 1-5.
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

The judge returns JSON with score and reasoning.
