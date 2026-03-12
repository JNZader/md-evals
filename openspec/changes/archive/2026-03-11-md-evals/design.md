# md-evals Technical Design

## Architecture Modules
- **CLI Parser**: Entry point parsing commands (`init`, `run`, `lint`) using Typer.
- **Config Loader**: Reads `eval.yaml` and enforces strict schema validation using Pydantic.
- **Execution Engine**: Orchestrates asynchronous requests for Control and Test groups, managing concurrency limits.
- **LLM Adapter**: Unified interface wrapping LiteLLM for cross-provider completions.
- **Evaluator Engine**: Executes regex rules or LLM judge prompts (parsing JSON schema for score and reasoning).
- **Reporter**: Consolidates results into a structured terminal view via Rich.

## Technology Stack
- **Language**: Python 3.12+ (latest stable)
- **CLI Framework**: Typer (latest)
- **Terminal UI**: Rich (latest)
- **LLM Integration**: LiteLLM (latest)
- **Schema Validation**: Pydantic v2.x (latest)

## Data Flow
1. **Config Loader** parses `eval.yaml` and sets up the execution plan.
2. **Execution Engine** dispatches prompts to the **LLM Adapter**:
   - *Control*: Bare prompt.
   - *Test*: Prompt + `SKILL.md` injected context.
3. Outputs are forwarded to the **Evaluator Engine**.
4. Regex rules or the LLM Judge evaluate the output.
5. **Reporter** formats the comparative results into a structured terminal view.
