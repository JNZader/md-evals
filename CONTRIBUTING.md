# Contributing to md-evals

Thank you for your interest in contributing to md-evals! We're excited to have you help improve this LLM evaluation framework.

This document provides guidelines and instructions for contributing code, documentation, and other improvements.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Linting and Code Style](#linting-and-code-style)
- [Git Workflow](#git-workflow)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Documentation](#documentation)
- [Community Expectations](#community-expectations)
- [Questions?](#questions)

## Code of Conduct

Please read and follow our [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). We are committed to providing a welcoming and inclusive environment for all contributors.

## Getting Started

### Prerequisites

- Python 3.12 or higher
- Git
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Fork and Clone

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/md-evals.git
   cd md-evals
   ```
3. **Add upstream** remote to track the main repository:
   ```bash
   git remote add upstream https://github.com/JNZader/md-evals.git
   ```

## Development Setup

### Using uv (Recommended)

```bash
# Install dependencies including dev tools
uv sync --extra dev

# Activate the virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Verify installation
md-evals --version
```

### Using pip

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Verify installation
md-evals --version
```

### Environment Variables (Optional)

For testing with LLM providers:

```bash
# GitHub Models (recommended for testing)
export GITHUB_TOKEN="github_pat_YOUR_TOKEN_HERE"

# Or other providers
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
```

See [docs/guide/github-models-setup.md](docs/guide/github-models-setup.md) for detailed setup instructions.

## Making Changes

### Create a Feature Branch

```bash
# Update local main
git fetch upstream
git checkout main
git reset --hard upstream/main

# Create your feature branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
# or
git checkout -b docs/your-documentation-update
```

### Branch Naming Conventions

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions/improvements
- `perf/` - Performance improvements

Use descriptive names:
- ✅ Good: `feature/github-models-provider`, `fix/token-counting-accuracy`
- ❌ Bad: `feature/new`, `fix/bug`, `my-changes`

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=md_evals --cov-report=html

# Run specific test file
pytest tests/test_evaluators.py

# Run specific test function
pytest tests/test_evaluators.py::test_regex_evaluator

# Run tests in parallel (faster)
pytest -n auto

# Run tests with verbose output
pytest -vv
```

### Writing Tests

- Place tests in the `tests/` directory
- Use descriptive test names: `test_feature_description()`
- Test both happy path and error cases
- Use fixtures for setup/teardown
- Mock external API calls
- Aim for >80% code coverage

Example test:

```python
import pytest
from md_evals.evaluators import RegexEvaluator

def test_regex_evaluator_matches_pattern():
    """Test that regex evaluator correctly matches patterns."""
    evaluator = RegexEvaluator(
        name="has_greeting",
        pattern=r"Hello|Hi"
    )
    
    result = evaluator.evaluate("Hello, World!")
    assert result.passed is True
    assert result.score == 1.0

def test_regex_evaluator_handles_no_match():
    """Test that regex evaluator handles non-matching text."""
    evaluator = RegexEvaluator(
        name="has_greeting",
        pattern=r"Hello|Hi"
    )
    
    result = evaluator.evaluate("Goodbye")
    assert result.passed is False
    assert result.score == 0.0
```

## Linting and Code Style

### Code Style

We use [Ruff](https://github.com/astral-sh/ruff) for linting and code formatting.

```bash
# Check code style
ruff check .

# Auto-fix style issues
ruff check --fix .

# Format code
ruff format .

# Format and check
ruff check --fix && ruff format .
```

### Style Guide

- **Line length**: Maximum 100 characters
- **Imports**: Organize as stdlib, third-party, local
- **Type hints**: Use for function signatures
- **Docstrings**: Use Google-style docstrings
- **Comments**: Explain "why", not "what"

Example properly formatted code:

```python
"""Module for handling LLM evaluations."""

from typing import Optional
from pydantic import BaseModel
from md_evals.models import EvaluationResult


class SkillEvaluator(BaseModel):
    """Evaluator for AI skills based on SKILL.md files.
    
    Attributes:
        name: Evaluator name
        description: What this evaluator tests
    """
    
    name: str
    description: Optional[str] = None
    
    def evaluate(
        self,
        response: str,
        expected: Optional[str] = None,
    ) -> EvaluationResult:
        """Evaluate LLM response against criteria.
        
        Args:
            response: The LLM's response text
            expected: Expected output (optional)
            
        Returns:
            EvaluationResult with pass/fail and score
            
        Raises:
            ValueError: If response is empty
        """
        if not response:
            raise ValueError("Response cannot be empty")
            
        # Implement evaluation logic
        return EvaluationResult(passed=True, score=1.0)
```

### Pre-commit Checks

Before committing, run:

```bash
# Full check
ruff check --fix . && ruff format . && pytest
```

## Git Workflow

### Standard Workflow

1. **Update your branch** with latest upstream changes:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Make your changes** on your feature branch

3. **Commit** with clear messages (see [Commit Messages](#commit-messages))

4. **Push** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request** on GitHub

### Handling Merge Conflicts

```bash
# If conflicts occur during rebase
git fetch upstream
git rebase upstream/main

# Resolve conflicts in your editor
# Then continue rebase
git add .
git rebase --continue

# Or abort if needed
git rebase --abort
```

## Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/) format.

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style changes (formatting, linting)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Test additions/changes
- `chore`: Build, dependencies, etc.

### Examples

✅ **Good commits:**

```
feat(github-models): add support for Claude 3.5 Sonnet

Integrate GitHub Models API for free LLM evaluation.
Add provider detection and model listing capability.

Closes #42
```

```
fix(token-counting): improve accuracy within ±12% target

Refine token estimation algorithm for streaming responses.
Add comprehensive test cases for edge cases.

Fixes #15
```

```
docs: update GitHub Models setup guide

Add step-by-step authentication instructions.
Include rate limit information and troubleshooting section.
```

❌ **Poor commits:**

```
fix bug
```

```
update code
```

```
WIP: stuff
```

### Guidelines

- **Subject** (first line):
  - Imperative mood ("add" not "added")
  - Don't capitalize first letter
  - No period at end
  - Maximum 50 characters
  
- **Body**:
  - Explain what and why, not how
  - Wrap at 72 characters
  - Separate from subject with blank line
  - Use bullet points if helpful
  
- **Footer**:
  - Reference issues: `Closes #123`, `Fixes #456`
  - Break changes: `BREAKING CHANGE: description`

## Pull Request Process

### Before Submitting

1. **Update main branch**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run tests locally**:
   ```bash
   pytest --cov=md_evals
   ```

3. **Check code style**:
   ```bash
   ruff check --fix . && ruff format .
   ```

4. **Update documentation** if needed

5. **Sign commits** (if configured):
   ```bash
   git commit -S -m "your message"
   ```

### Creating a PR

1. Push your branch to your fork
2. Click "Compare & pull request" on GitHub
3. Use the [pull request template](.github/pull_request_template.md)
4. Fill in all required sections
5. Link any related issues with `Closes #123`

### PR Title Format

Follow the same [Conventional Commits](#commit-messages) format:

```
feat(github-models): add DeepSeek-R1 support
fix(cli): resolve argument parsing issue
docs: improve quickstart guide
```

### What Happens Next

1. **Automated Checks**:
   - Tests must pass
   - Code coverage must not decrease
   - Linting must pass
   
2. **Code Review**:
   - Maintainers will review your changes
   - Suggest improvements or changes
   - Approve when ready
   
3. **Merge**:
   - Squash and merge (for clean history)
   - Delete your branch

### During Review

- **Respond to feedback** promptly
- **Make requested changes** as new commits
- **Ask questions** if feedback is unclear
- **Don't take criticism personally** - we're all learning!

### If Your PR Gets Stale

If upstream main has moved ahead:

```bash
git fetch upstream
git rebase upstream/main
git push --force-with-lease origin feature/your-feature
```

## Documentation

### Updating Docs

Documentation uses [Docsify](https://docsify.js.org/):

```
docs/
├── README.md                 # Homepage
├── guide/                    # User guides
│   ├── getting-started.md
│   ├── configuration.md
│   └── ...
├── reference/                # API reference
│   ├── cli-commands.md
│   ├── yaml-schema.md
│   └── ...
├── examples/                 # Example evaluations
│   ├── basic-evaluation.md
│   └── ...
└── _sidebar.md              # Navigation
```

### Writing Good Documentation

- Use clear, concise language
- Include code examples
- Add screenshots where helpful
- Explain the "why" not just "how"
- Keep examples up-to-date with code

Example documentation section:

```markdown
## Using GitHub Models

GitHub Models provides free/low-cost access to state-of-the-art LLMs.

### Setup

1. Create a GitHub token:
   - Visit https://github.com/settings/tokens
   - Create token with `repo` scope
   - Copy your token

2. Set environment variable:
   ```bash
   export GITHUB_TOKEN="github_pat_YOUR_TOKEN"
   ```

### Usage

```bash
md-evals run eval.yaml \
  --provider github-models \
  --model claude-3.5-sonnet
```

### Available Models

| Model | Cost | Speed | Best For |
|-------|------|-------|----------|
| claude-3.5-sonnet | Free | Fast | Reasoning, coding |
| gpt-4o | Free | Fast | General purpose |
| deepseek-r1 | Free | Fastest | Quick evals |

See [GitHub Models Guide](guide/github-models-setup.md) for details.
```

## Community Expectations

### Be Respectful

- Treat all community members with respect
- Welcome diverse perspectives and backgrounds
- Listen actively to feedback
- Disagree respectfully

### Be Helpful

- Answer questions with patience
- Help review others' PRs
- Share knowledge and resources
- Mentor newer contributors

### Be Collaborative

- Work together to solve problems
- Communicate clearly and often
- Ask questions if something is unclear
- Give credit to collaborators

### Be Professional

- Keep discussions focused and productive
- Avoid off-topic or contentious subjects
- Report issues privately if needed (see [SECURITY.md](SECURITY.md))
- Follow the [Code of Conduct](CODE_OF_CONDUCT.md)

## Getting Help

### Resources

- 📚 **[Full Documentation](https://jnzader.github.io/md-evals/)**
- 🐛 **[Issue Tracker](https://github.com/JNZader/md-evals/issues)**
- 💬 **[Discussions](https://github.com/JNZader/md-evals/discussions)**

### Common Questions

**How do I set up my development environment?**
→ See [Development Setup](#development-setup)

**What's the test command?**
→ See [Testing](#testing)

**How do I format my code?**
→ See [Linting and Code Style](#linting-and-code-style)

**Where do I report security issues?**
→ See [SECURITY.md](SECURITY.md)

### Need More Help?

- Check [existing issues](https://github.com/JNZader/md-evals/issues) for similar problems
- Start a [discussion](https://github.com/JNZader/md-evals/discussions) for questions
- Review [documentation](https://jnzader.github.io/md-evals/)

## Recognition

We appreciate all contributions! Contributors are recognized in:
- The project README
- Release notes
- GitHub's contributor graph

Thank you for making md-evals better! 🎉
