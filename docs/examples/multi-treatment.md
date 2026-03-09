<!-- docs/examples/multi-treatment.md -->
# Multi-Treatment Evaluation

Compare multiple skill variations.

```yaml
treatments:
  CONTROL:
    skill_path: null
  
  CONCISE_SKILL:
    description: "Short skill"
    skill_path: "./skills/concise.md"
  
  DETAILED_SKILL:
    description: "Detailed skill"
    skill_path: "./skills/detailed.md"
  
  PROMPT_ENGINEERED:
    description: "Prompt engineered"
    skill_path: "./skills/prompt.md"
```

Run all:

```bash
md-evals run
```

Run specific:

```bash
md-evals run --treatment CONCISE_SKILL,DETAILED_SKILL
```

The tool automatically adds CONTROL if not specified.
