<!-- docs/examples/wildcards.md -->
# Wildcards

Use wildcards to run multiple treatments.

## Define Treatments

```yaml
treatments:
  CONTROL:
    skill_path: null
  
  LCC_SHORT:
    skill_path: "./skills/short.md"
  
  LCC_LONG:
    skill_path: "./skills/long.md"
  
  LCC_DETAILED:
    skill_path: "./skills/detailed.md"
  
  OTHER_SKILL:
    skill_path: "./skills/other.md"
```

## Run with Wildcards

```bash
# Run all LCC_ treatments
md-evals run --treatment LCC_*

# Run all treatments
md-evals run --treatment "*"
```

The wildcard expands to matching treatment names.
