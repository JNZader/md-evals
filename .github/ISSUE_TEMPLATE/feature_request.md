---
name: Feature Request
about: Suggest an improvement or new feature for md-evals
title: "[FEATURE] Brief description of requested feature"
labels: enhancement
assignees: []

---

## Description

**What feature or improvement would you like?**

A clear and concise description of the feature or enhancement you're requesting.

## Use Case

**What problem does this solve?**

Explain the problem or limitation you're trying to address:

- Current workflow: What's the current way of doing this?
- Pain point: What makes it difficult?
- Goal: What are you trying to achieve?

**Example scenario:**

```
When I'm doing X, I wish I could Y because Z.
```

## Proposed Solution

**How would you implement this?**

Describe your proposed solution in detail:

1. Feature overview
2. How it would work
3. Expected user experience
4. Any APIs or configuration needed

**Example usage:**

```bash
# How would users interact with this feature?
md-evals run eval.yaml --my-new-flag value
```

```yaml
# How would it look in configuration?
evaluators:
  - type: "my_new_evaluator"
    config:
      option: value
```

## Alternatives Considered

**What other approaches did you consider?**

- Alternative 1: Description and why you didn't choose it
- Alternative 2: Description and why you didn't choose it
- Current workaround: If there's a way to do this now, explain it

## Impact

**Who would benefit from this feature?**

- [ ] Users evaluating skills
- [ ] Developers extending md-evals
- [ ] Teams running large evaluations
- [ ] Integration with other tools
- [ ] Other: ___________

**How important is this?**

- [ ] Critical (blocking workflow)
- [ ] High (nice to have, would improve experience)
- [ ] Medium (interesting enhancement)
- [ ] Low (curious about possibility)

## Additional Context

**Any other context or information?**

- Related issues or discussions
- Similar features in other tools
- Reference implementations
- Performance considerations
- Backward compatibility concerns

---

## Checklist

- [ ] I've searched for existing feature requests (no duplicates)
- [ ] I've clearly described the use case
- [ ] I've provided examples of desired usage
- [ ] This is a feature request, not a bug report
- [ ] I've read the [documentation](https://jnzader.github.io/md-evals/)
- [ ] I understand this may not be implemented immediately
