# Tasks: md-evals

## Phase 1: Project Setup

- [ ] **1.1** Initialize project using `uv` with Python 3.12+ as the base requirement.
  - Create `pyproject.toml` with: name, version, description, requires-python = ">=3.12"
  - Use `uv sync` for dependency management
  
- [ ] **1.2** Add and lock latest versions of dependencies:
  ```toml
  dependencies = [
      "typer[all]>=0.12.0",
      "rich>=13.7.0",
      "litellm>=1.40.0",
      "pydantic>=2.6.0",
      "pyyaml>=6.0.0",
      "pytest>=8.0.0",
      "pytest-asyncio>=0.23.0",
      "pytest-xdist>=3.5.0",  # For parallel execution (-n)
      "httpx>=0.27.0",        # For async HTTP
      "tenacity>=8.2.0",     # For retry logic
  ]
  ```
  
- [ ] **1.3** Setup basic project structure:
  ```
  md_evals/
  ├── __init__.py
  ├── __main__.py           # Entry point: python -m md_evals
  ├── cli.py                 # Typer CLI commands
  ├── config.py              # ConfigLoader
  ├── models.py              # Pydantic schemas
  ├── engine.py              # ExecutionEngine
  ├── llm.py                 # LLMAdapter
  ├── evaluator.py           # EvaluatorEngine
  ├── reporter.py            # Reporter
  ├── linter.py              # Skill linter
  └── utils.py               # Helpers
  tests/
  ├── __init__.py
  ├── test_config.py
  ├── test_engine.py
  ├── test_evaluator.py
  ├── test_linter.py
  └── fixtures/
      ├── eval.yaml
      ├── skill_short.md     # < 400 lines
      └── skill_long.md      # > 400 lines
  ```

---

## Phase 2: Core Models & Config

- [ ] **2.1** Create Pydantic V2 schemas in `md_evals/models.py`:

  ```python
  # Core config
  class Defaults(BaseModel):
      model: str = "gpt-4o"
      provider: str = "openai"
      temperature: float = 0.7
      max_tokens: int = 2048
      timeout: int = 60
      retry_attempts: int = 3
      retry_delay: float = 1.0

  # Treatment definition
  class Treatment(BaseModel):
      description: str | None = None
      skill_path: str | None = None  # None = CONTROL
      env: dict[str, str] = {}

  # Evaluator definitions
  class RegexEvaluator(BaseModel):
      type: Literal["regex"] = "regex"
      name: str
      pattern: str
      pass_on_match: bool = True
      fail_message: str | None = None

  class ExactMatchEvaluator(BaseModel):
      type: Literal["exact-match"] = "exact-match"
      name: str
      expected: str
      case_sensitive: bool = False

  class LLMJudgeEvaluator(BaseModel):
      type: Literal["llm-judge"] = "llm-judge"
      name: str
      judge_model: str
      criteria: str
      output_schema: dict  # JSON schema
      pass_threshold: float = 0.8

  Evaluator = RegexEvaluator | ExactMatchEvaluator | LLMJudgeEvaluator

  # Task definition
  class Task(BaseModel):
      name: str
      description: str | None = None
      prompt: str  # Template with {variables}
      variables: dict[str, str] = {}
      evaluators: list[Evaluator]

  # Model definition
  class ModelConfig(BaseModel):
      name: str
      provider: str
      api_base: str | None = None

  # Linter config
  class LinterConfig(BaseModel):
      max_lines: int = 400
      fail_on_violation: bool = True
      rules: list[dict] = []

  # Output config
  class OutputConfig(BaseModel):
      format: Literal["table", "json", "markdown"] = "table"
      save_results: bool = True
      results_dir: str = "./results"
      verbose: bool = False

  # Execution config
  class ExecutionConfig(BaseModel):
      parallel_workers: int = 1
      repetitions: int = 1
      fail_fast: bool = False

  # Top-level EvalConfig
  class EvalConfig(BaseModel):
      name: str
      version: str = "1.0"
      description: str | None = None
      defaults: Defaults = Defaults()
      treatments: dict[str, Treatment] = {}
      models: list[ModelConfig] = []
      lint: LinterConfig = LinterConfig()
      tests: list[Task] = []
      output: OutputConfig = OutputConfig()
      execution: ExecutionConfig = ExecutionConfig()
  ```

- [ ] **2.2** Implement `ConfigLoader` in `md_evals/config.py`:
  - `load(path: str) -> EvalConfig` - Load and validate YAML
  - `validate(config: EvalConfig)` - Strict validation
  - `expand_wildcards(treatments: list[str]) -> list[str]` - Expand patterns like `LCC_*`

- [ ] **2.3** Write unit tests for configuration parsing:
  - Valid YAML parsing
  - Invalid YAML error handling
  - Missing required fields
  - Default values
  - Treatment validation

---

## Phase 3: The Linter

- [ ] **3.1** Implement linter rules in `md_evals/linter.py`:

  ```python
  class LinterRule(Protocol):
      def check(self, skill_path: str) -> LinterResult: ...

  class MaxLinesRule:
      limit: int = 400
      def check(self, skill_path: str) -> LinterResult: ...

  class RequiredSectionsRule:
      sections: list[str] = ["Description", "Rules", "Examples"]
      def check(self, skill_path: str) -> LinterResult: ...

  class LinterEngine:
      rules: list[LinterRule]
      def run(self, skill_path: str) -> LinterReport: ...
  ```

- [ ] **3.2** Implement CLI lint command:
  ```python
  @app.command()
  def lint(
      skill_path: str = "SKILL.md",
      fail_on_violation: bool = True,
      verbose: bool = False
  ) -> int:  # Exit code
  ```

- [ ] **3.3** Write tests for linter:
  - File < 400 lines → PASS
  - File > 400 lines → FAIL with clear message
  - Missing required sections → WARN
  - Non-existent file → ERROR

- [ ] **3.4** Add linting to `run` command (auto-run before evaluation)

---

## Phase 4: Execution Engine

- [ ] **4.1** Implement `LLMAdapter` in `md_evals/llm.py`:

  ```python
  class LLMResponse(BaseModel):
      content: str
      model: str
      provider: str
      tokens: int
      duration_ms: int
      raw_response: dict

  class LLMAdapter:
      def __init__(self, config: ModelConfig, defaults: Defaults): ...
      
      async def complete(
          self,
          prompt: str,
          system_prompt: str | None = None,
          temperature: float | None = None,
          max_tokens: int | None = None,
      ) -> LLMResponse: ...
      
      # Support for:
      # - Streaming responses
      # - Retry logic (exponential backoff)
      # - Timeout handling
      # - Error transformation
  ```

- [ ] **4.2** Implement skill injection logic:

  ```python
  def inject_skill(prompt: str, skill_path: str | None) -> tuple[str, str | None]:
      """
      Returns (final_prompt, system_prompt).
      
      If skill_path is None → CONTROL (no injection)
      If skill_path exists → inject skill into system prompt
      """
      if skill_path is None:
          return prompt, None
      
      skill_content = read_file(skill_path)
      system_prompt = f"{skill_content}\n\n---\n\nYou are a helpful AI assistant."
      return prompt, system_prompt
  ```

- [ ] **4.3** Implement `ExecutionEngine` in `md_evals/engine.py`:

  ```python
  class ExecutionResult(BaseModel):
      treatment: str
      test: str
      prompt: str
      response: LLMResponse
      passed: bool
      evaluator_results: list[EvaluatorResult]
      timestamp: datetime

  class ExecutionEngine:
      def __init__(
          self,
          config: EvalConfig,
          llm_adapter: LLMAdapter,
          evaluator_engine: "EvaluatorEngine",
      ): ...
      
      async def run_single(
          self,
          treatment: Treatment,
          task: Task,
      ) -> ExecutionResult: ...
      
      async def run_all(
          self,
          treatments: list[str],  # Expanded from wildcards
          progress: bool = True,
      ) -> list[ExecutionResult]: ...
      
      # Handle:
      # - Concurrency limits (semaphore)
      # - Retry on API errors
      # - Progress reporting (Rich)
  ```

- [ ] **4.4** Implement concurrency control:
  ```python
  # Use asyncio.Semaphore for parallel workers
  semaphore = asyncio.Semaphore(config.execution.parallel_workers)
  
  # Use tenacity for retry logic
  @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
  async def complete_with_retry(...): ...
  ```

- [ ] **4.5** Write tests:
  - Mock LLM responses
  - Test skill injection
  - Test retry logic
  - Test concurrency

---

## Phase 5: Evaluator Engine

- [ ] **5.1** Implement `RegexEvaluator`:

  ```python
  class EvaluatorResult(BaseModel):
      evaluator_name: str
      passed: bool
      score: float  # 0.0 - 1.0
      reason: str | None = None
      details: dict | None = None

  class RegexEvaluator:
      def evaluate(
          self,
          output: str,
          pattern: str,
          pass_on_match: bool = True,
      ) -> EvaluatorResult: ...
  ```

- [ ] **5.2** Implement `ExactMatchEvaluator`:

  ```python
  class ExactMatchEvaluator:
      def evaluate(
          self,
          output: str,
          expected: str,
          case_sensitive: bool = False,
      ) -> EvaluatorResult: ...
  ```

- [ ] **5.3** Implement `LLMJudgeEvaluator`:

  ```python
  class LLMJudgeEvaluator:
      def __init__(self, llm_adapter: LLMAdapter): ...
      
      async def evaluate(
          self,
          output: str,
          criteria: str,
          judge_model: str,
          output_schema: dict,
          pass_threshold: float = 0.8,
      ) -> EvaluatorResult:
          """
          1. Build judge prompt with criteria + output
          2. Call LLM with output_schema in response_format
          3. Parse JSON response
          4. Return EvaluatorResult with score + reasoning
          """
  ```

  Example judge prompt:
  ```python
  JUDGE_PROMPT = """You are an expert evaluator. 

  Output to evaluate:
  ---
  {output}
  ---

  Evaluation criteria:
  {criteria}

  Provide your evaluation as JSON matching this schema:
  {schema}

  Output:"""
  ```

- [ ] **5.4** Implement `EvaluatorEngine`:

  ```python
  class EvaluatorEngine:
      def __init__(self, llm_adapter: LLMAdapter | None = None): ...
      
      async def evaluate(
          self,
          output: str,
          evaluators: list[Evaluator],
      ) -> list[EvaluatorResult]: ...
  ```

- [ ] **5.5** Write unit tests:
  - Regex matching / not matching
  - Exact match case sensitivity
  - LLM Judge with mocked response
  - JSON parsing edge cases

---

## Phase 6: CLI & Reporting

- [ ] **6.1** Implement Typer CLI in `md_evals/cli.py`:

  ```python
  import typer
  from typing import Annotated
  
  app = typer.Typer(
      name="md-evals",
      help="Evaluate AI skills with Control vs Treatment testing"
  )

  @app.command()
  def init(
      directory: Annotated[str, typer.Argument(".")] = ".",
      force: bool = False,
  ):
      """Scaffold eval.yaml and SKILL.md template."""
      # Creates:
      # - eval.yaml with example config
      # - SKILL.md template
      # - results/ directory
  

  @app.command()
  def run(
      config: Annotated[str, typer.Option("--config", "-c")] = "eval.yaml",
      treatment: Annotated[str | None, typer.Option("--treatment", "-t")] = None,
      model: Annotated[str | None, typer.Option("--model", "-m")] = None,
      count: Annotated[int, typer.Option("--count")] = 1,
      workers: Annotated[int, typer.Option("-n")] = 1,
      output: Annotated[str, typer.Option("--output", "-o")] = "table",
      verbose: bool = False,
  ):
      """Run evaluations."""
  

  @app.command()
  def lint(
      skill_path: Annotated[str, typer.Argument("SKILL.md")] = "SKILL.md",
      fail: bool = True,
      verbose: bool = False,
  ):
      """Validate SKILL.md against constraints."""
  

  @app.command()
  def list(
      config: Annotated[str, typer.Option("--config", "-c")] = "eval.yaml",
      treatments: bool = False,
      tasks: bool = False,
  ):
      """List available tasks and treatments."""
  ```

- [ ] **6.2** Implement `Reporter` in `md_evals/reporter.py`:

  ```python
  class Reporter:
      def __init__(self, config: EvalConfig): ...
      
      def report_terminal(
          self,
          results: list[ExecutionResult],
          verbose: bool = False,
      ) -> None:
          """Print Rich table to terminal."""
      
      def report_json(
          self,
          results: list[ExecutionResult],
          output_path: str,
      ) -> None:
          """Save JSON report."""
      
      def report_markdown(
          self,
          results: list[ExecutionResult],
          output_path: str,
      ) -> None:
          """Save Markdown report."""
      
      def calculate_summary(
          self,
          results: list[ExecutionResult],
      ) -> dict:
          """Calculate aggregate statistics."""
  ```

- [ ] **6.3** Wire up CLI to all components:

  ```python
  # In cli.py run command:
  config = ConfigLoader().load(config_path)
  
  # Expand treatment wildcards
  if treatment:
      treatments = ConfigLoader.expand_wildcards(treatment, config.treatments)
  else:
      treatments = list(config.treatments.keys())
  
  # Run linter first (optional skip with --no-lint)
  if not no_lint:
      linter = LinterEngine(config.lint)
      report = linter.run(config.defaults.skill_path)
      if report.has_violations and config.lint.fail_on_violation:
          raise typer.Exit(code=1)
  
  # Execute
  llm_adapter = LLMAdapter(model_config, config.defaults)
  evaluator_engine = EvaluatorEngine(llm_adapter)
  engine = ExecutionEngine(config, llm_adapter, evaluator_engine)
  
  results = await engine.run_all(treatments)
  
  # Report
  reporter = Reporter(config)
  reporter.report_terminal(results, verbose)
  if config.output.save_results:
      reporter.report_json(results, f"{config.output.results_dir}/results.json")
  ```

- [ ] **6.4** Implement results directory structure:

  ```
  results/
  └── eval_20260217_143052/
      ├── summary.md              # Rich table + summary
      ├── metadata.json            # Config used, timestamp, etc.
      ├── events/
      │   ├── control_task1_001.json
      │   └── treatment_task1_001.json
      └── raw/
          └── llm_outputs.jsonl    # Raw LLM responses
  ```

- [ ] **6.5** Write end-to-end tests:

  ```python
  def test_init_scaffolds_files(tmp_path):
      """Test init command creates expected files."""
  
  def test_run_with_mocked_llm():
      """Test run with mocked LLM responses."""
  
  def test_lint_fails_on_long_skill(tmp_path):
      """Test lint fails when skill > 400 lines."""
  
  def test_wildcard_expansion():
      """Test LCC_* expands correctly."""
  
  def test_reporter_formats():
      """Test terminal, JSON, and Markdown output."""
  ```

---

## Phase 7: Polish & Documentation (Optional)

- [ ] **7.1** Add shell completion for Typer
- [ ] **7.2** Add `--version` flag
- [ ] **7.3** Create `README.md` with installation and usage
- [ ] **7.4** Add `--help` examples
- [ ] **7.5** Add integration with LangSmith (optional future)

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Invalid configuration / file not found |
| 2 | Linter violation (if fail_on_violation=true) |
| 3 | LLM API error (after retries exhausted) |
| 4 | Evaluation failures (if fail_fast=true) |

---

## Dependencies Summary

| Package | Purpose |
|---------|---------|
| typer | CLI framework |
| rich | Terminal output |
| litellm | Multi-provider LLM |
| pydantic | Schema validation |
| pyyaml | YAML parsing |
| pytest | Testing |
| pytest-asyncio | Async tests |
| pytest-xdist | Parallel tests |
| httpx | Async HTTP (litellm dep) |
| tenacity | Retry logic |

---

## File-by-File Breakdown

| File | Lines (est.) | Purpose |
|------|-------------|---------|
| `__init__.py` | 5 | Package init |
| `__main__.py` | 10 | Entry point |
| `cli.py` | 150 | All CLI commands |
| `config.py` | 100 | Config loading |
| `models.py` | 200 | Pydantic schemas |
| `llm.py` | 150 | LLM adapter |
| `engine.py` | 200 | Execution engine |
| `evaluator.py` | 150 | Evaluators |
| `reporter.py` | 100 | Output formatting |
| `linter.py` | 100 | Skill linter |
| `utils.py` | 50 | Helpers |
| **Total** | **~1,215** | Core implementation |
