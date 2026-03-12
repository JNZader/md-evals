# md-evals Specification

## Core Requirements

### CLI Commands

| Command | Description |
|---------|-------------|
| `md-evals init` | Scaffolds `eval.yaml` and a dummy `SKILL.md` in the current directory. |
| `md-evals run` | Executes Control vs. Test evaluations using LLM endpoints defined in config. Supports `--treatment` wildcards, `--count` for repetitions, and `-n` for parallel workers. |
| `md-evals lint` | Validates `SKILL.md` against constraints. Fails/warns if file exceeds 400-line "Red Flag" limit. |
| `md-evals list` | Lists available tasks and treatments from config. |

### Concepts (inspired by skills-benchmarks)

- **Control**: Bare prompt without any skill context (baseline).
- **Treatment**: A skill configuration to test (e.g., "ALL_MAIN_SKILLS", "langchain-fundamentals").
- **Task**: A test case with prompt + evaluators.
- **Treatment Wildcards**: Support patterns like `LCC_*` to run multiple treatments matching prefix.

## Scenarios

### 1. Happy Path
User runs `md-evals run`. The tool compares outputs of a bare prompt (Control) versus the prompt with `SKILL.md` (Treatment), quantifying the impact of skill injection.

### 2. Linter Constraint Failure
User runs `md-evals lint`. The engine scans `SKILL.md` and detects over 400 lines, throwing a validation error. This enforces concise, actionable AI skills.

### 3. Hybrid Evaluation
`eval.yaml` defines a mix of deterministic (regex/exact match) and heuristic (LLM-as-a-judge) evaluators. The LLM judge returns structured JSON with score and reasoning.

### 4. Multiple Treatments
User runs `md-evals run --treatment=CONTROL,ALL_SKILLS,CONCISE_SKILL`. The tool executes all specified treatments and generates comparative results.

### 5. Repetitions & Parallelization
User runs `md-evals run --count=3 -n 4`. The tool runs each treatment 3 times with 4 parallel workers for statistical significance.

### 6. Treatment Wildcards
User runs `md-evals run --treatment=LCC_*`. The tool automatically expands to all treatments matching the pattern.

## YAML Configuration Schema (`eval.yaml`)

```yaml
name: "Skill Evaluation"
version: "1.0"

# Default settings
defaults:
  model: "gpt-4o"
  temperature: 0.7
  max_tokens: 2048
  timeout: 60

# Treatments define skill configurations
treatments:
  CONTROL:
    description: "No skill context (baseline)"
    skill_path: null
  
  ALL_MAIN_SKILLS:
    description: "All production skills"
    skill_path: "./skills/main/SKILL.md"
  
  CONCISE_SKILL:
    description: "Concise version of skill"
    skill_path: "./skills/concise/SKILL.md"

# Models to test
models:
  - name: "gpt-4o"
    provider: "openai"
  - name: "claude-3-5-sonnet-20241022"
    provider: "anthropic"

# Test tasks
tests:
  - name: "Format compliance"
    description: "Check if response follows expected format"
    prompt: "Generate a summary of the following: {input}"
    variables:
      input: "artificial intelligence"
    evaluators:
      - type: "regex"
        name: "has_summary_header"
        pattern: "^Summary:"
        pass_on_match: true
      - type: "regex"
        name: "has_bullet_points"
        pattern: "^[•\\-]"
        pass_on_match: true
      
  - name: "Reasoning Depth"
    description: "Evaluate reasoning quality"
    prompt: "Analyze the architecture of: {topic}"
    variables:
      topic: "microservices"
    evaluators:
      - type: "llm-judge"
        name: "depth_score"
        judge_model: "gpt-4o"
        criteria: |
          Did the response correctly identify at least 3 core layers?
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

  - name: "Code Quality"
    description: "Check code output quality"
    prompt: "Write a function to {task}"
    variables:
      task: "sort a list"
    evaluators:
      - type: "exact-match"
        name: "has_function"
        expected: "def"
```

### Complete YAML Schema Fields

```yaml
# Top-level
name: string                    # Evaluation name
version: string                # Config version
description: string            # Optional description

# Defaults (optional)
defaults:
  model: string                 # Default model name
  provider: string              # Default provider (openai, anthropic, etc.)
  temperature: float            # Default temperature (0.0-2.0)
  max_tokens: integer           # Max tokens in response
  timeout: integer              # Request timeout in seconds
  retry_attempts: integer      # Number of retry attempts
  retry_delay: float            # Delay between retries

# Treatments
treatments:
  <treatment_name>:
    description: string         # Human-readable description
    skill_path: string|null     # Path to SKILL.md file
    env:                        # Environment variables (optional)
      KEY: "value"

# Models (optional, overrides defaults)
models:
  - name: string                # Model name as recognized by litellm
    provider: string             # Provider name
    api_base: string            # Custom API base URL (optional)
    api_key: string             # API key (or use env var)

# Linter config (optional)
lint:
  max_lines: integer            # Max lines in SKILL.md (default: 400)
  fail_on_violation: boolean    # Fail run if violation found
  rules:
    - type: "max-lines"
      limit: 400
    - type: "required-sections"
      sections: ["Description", "Rules", "Examples"]

# Tasks
tests:
  - name: string                # Unique test name
    description: string         # Human-readable description
    prompt: string              # Prompt template with {variables}
    variables:                  # Variables for prompt template
      key: "value"
    evaluators:                 # List of evaluators
      # Regex evaluator
      - type: "regex"
        name: string
        pattern: string
        pass_on_match: boolean  # Pass if pattern matches (default: true)
        fail_message: string     # Message on failure
      
      # Exact match evaluator
      - type: "exact-match"
        name: string
        expected: string
        case_sensitive: boolean
        
      # LLM Judge evaluator
      - type: "llm-judge"
        name: string
        judge_model: string      # Model to use as judge
        criteria: string         # Evaluation criteria
        output_schema: object    # Expected JSON schema
        pass_threshold: float    # Minimum score to pass (0.0-1.0)

# Output config (optional)
output:
  format: "table" | "json" | "markdown"
  save_results: boolean
  results_dir: string           # Directory for results (default: ./results)
  verbose: boolean              # Show detailed output

# Execution config (optional)
execution:
  parallel_workers: integer      # Number of parallel workers (default: 1)
  repetitions: integer          # Number of times to run each test
  fail_fast: boolean            # Stop on first failure
```

## Output Formats

### Terminal Output (Rich)
```
╔══════════════════════════════════════════════════════════════════╗
║                    md-evals Results                                ║
╠══════════════════════════════════════════════════════════════════╣
║ Treatment              │ Checks    │ Score  │ Time  │ Tokens    ║
╠══════════════════════════════════════════════════════════════════╣
║ CONTROL                │ 2/4 (50%) │ 2.5    │ 1.2s  │ 245       ║
║ ALL_MAIN_SKILLS        │ 4/4 (100%)│ 4.8    │ 1.4s  │ 312       ║
║ CONCISE_SKILL          │ 3/4 (75%) │ 3.9    │ 1.3s  │ 289       ║
╚══════════════════════════════════════════════════════════════════╝

Improvement: +50% (CONTROL → ALL_MAIN_SKILLS)
```

### JSON Output
```json
{
  "experiment_id": "eval_20260217_143052",
  "timestamp": "2026-02-17T14:30:52Z",
  "config": {
    "name": "Skill Evaluation",
    "models": ["gpt-4o"]
  },
  "results": [
    {
      "treatment": "CONTROL",
      "test": "Format compliance",
      "checks": [
        {"name": "has_summary_header", "passed": false, "reason": "Pattern not found"}
      ],
      "score": 0.5,
      "duration_ms": 1234,
      "tokens": 245
    }
  ],
  "summary": {
    "control_pass_rate": 0.5,
    "treatment_pass_rate": 1.0,
    "improvement": 0.5
  }
}
```

### Results Directory Structure
```
results/
└── eval_20260217_143052/
    ├── summary.md              # Human-readable summary
    ├── metadata.json           # Experiment configuration
    ├── events/                 # Parsed events per run
    │   ├── control_001.json
    │   └── treatment_001.json
    └── raw/
        └── llm_outputs.jsonl   # Raw LLM responses
```

## Edge Cases

1. **Empty SKILL.md**: Warn but allow execution
2. **Invalid YAML syntax**: Fail with clear error message
3. **LLM API timeout**: Retry with exponential backoff, then mark as error
4. **Invalid JSON from LLM Judge**: Fall back to regex parsing or mark as error
5. **Model not found**: Clear error suggesting correct model name
6. **Missing environment variables**: Prompt user with instructions
7. **File not found for skill path**: Fail with clear error
8. **Concurrent execution conflicts**: Use proper async/thread safety
9. **Very long prompts**: Warn if prompt + skill > context window
10. **Rate limiting**: Implement backoff and queueing

## API Keys & Configuration

Environment variables (following LiteLLM conventions):
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GOOGLE_API_KEY`
- `AZURE_API_KEY`
- Or use custom `MODEL_API_KEY` with `MODEL_API_BASE`

## Error Handling

| Error Type | Behavior |
|------------|----------|
| Invalid YAML | Exit with code 1, show parse error |
| LLM API Error | Retry 3x, then log error, continue to next |
| Validation Failure | Mark test as failed, continue |
| Linter Violation | Exit with code 1 (if fail_on_violation=true) |
| File Not Found | Exit with code 1, clear message |

## Success Criteria

1. ✅ CLI executes `init`, `run`, `lint`, `list` commands
2. ✅ Supports multiple treatments with wildcard expansion
3. ✅ A/B testing shows clear Control vs Treatment comparison
4. ✅ Regex and LLM Judge evaluators work correctly
5. ✅ Linter enforces 400-line limit with clear feedback
6. ✅ Results saved to local files (JSON + Markdown)
7. ✅ Repetitions (`--count`) and parallelization (`-n`) work
8. ✅ Handles API errors gracefully with retry logic
9. ✅ Exit codes indicate success/failure correctly
10. ✅ Works with at least 2 different LLM providers via LiteLLM
