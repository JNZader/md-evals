<!-- docs/guide/linting.md -->
# Linting

md-evals includes a built-in linter to enforce best practices for SKILL.md files.

## Running the Linter

```bash
# Lint default SKILL.md
md-evals lint specific file
md

# Lint-evals lint path/to/skill.md
```

## Rules

### Max Lines (400)

SKILL.md files should be concise. The linter warns if the file exceeds 400 lines:

```
✗ skill.md has violations:
  [ERROR] Skill file has 450 lines, exceeds limit of 400
```

### Required Sections

Recommended sections:
- Description
- Rules
- Examples

### No Empty Files

The linter ensures SKILL.md is not empty.

### Line Length

Lines over 200 characters generate warnings.

## Configuration

```yaml
lint:
  max_lines: 400
  fail_on_violation: true  # Exit with error if violated
```

## Skip Linting

```bash
md-evals run --no-lint
```

## Best Practices

1. Keep SKILL.md under 400 lines
2. Include Description, Rules, Examples
3. Use short, actionable rules
4. Include concrete examples
