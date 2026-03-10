# Tasks: GitHub Models Integration

## Overview

**Total Tasks**: 18  
**Phases**: 3 (Core Integration, Documentation & Examples, CLI Improvements)

---

## Phase 1: LLM Provider Integration (Core)

Foundation tasks for implementing the GitHub Models provider with Azure SDK wrapper and model support.

- [ ] **1.1** Create provider package structure
  - **Description**: Create `md_evals/providers/` package directory with `__init__.py` if not exists
  - **Files affected**: `md_evals/providers/__init__.py`
  - **Dependencies**: None
  - **Type**: Feature (Setup)
  - **Effort**: Small

- [ ] **1.2** Implement `GitHubModelsProvider` class with Azure SDK wrapper
  - **Description**: Create `md_evals/providers/github_models.py` with `GitHubModelsProvider` class implementing async `complete()` method, wrapping Azure AI Inference SDK
  - **Files affected**: `md_evals/providers/github_models.py`
  - **Dependencies**: 1.1
  - **Type**: Feature
  - **Effort**: Medium

- [ ] **1.3** Implement token authentication and validation
  - **Description**: Add `_load_github_token()` method to validate `GITHUB_TOKEN` env var, support `.env` files, and raise `AuthenticationError` with clear guidance if missing/invalid
  - **Files affected**: `md_evals/providers/github_models.py`
  - **Dependencies**: 1.2
  - **Type**: Feature
  - **Effort**: Small

- [ ] **1.4** Implement streaming response handling and token counting
  - **Description**: Add `_handle_stream()` method to collect streaming chunks from Azure SDK, extract token metadata, and compute token counts with fallback estimation (len(content) / 4)
  - **Files affected**: `md_evals/providers/github_models.py`
  - **Dependencies**: 1.2
  - **Type**: Feature
  - **Effort**: Medium

- [ ] **1.5** Define custom exception hierarchy
  - **Description**: Create exception classes: `GitHubModelsError`, `AuthenticationError`, `ModelNotSupportedError`, `RateLimitError`, `ContextWindowError`, `StreamingError`, `APIError` with actionable error messages
  - **Files affected**: `md_evals/providers/github_models.py`
  - **Dependencies**: 1.2
  - **Type**: Feature
  - **Effort**: Small

- [ ] **1.6** Register supported models and metadata
  - **Description**: Implement `supported_models()` class method returning dict of 4 models (claude-3.5-sonnet, gpt-4o, deepseek-r1, grok-3) with metadata (context window, temperature range, rate limits, cost)
  - **Files affected**: `md_evals/providers/github_models.py`
  - **Dependencies**: 1.2
  - **Type**: Feature
  - **Effort**: Small

- [ ] **1.7** Create provider registry module
  - **Description**: Create `md_evals/provider_registry.py` with `ProviderRegistry` class (singleton pattern) supporting `register()`, `get()`, `list_providers()`, and `instantiate()` methods for provider discovery
  - **Files affected**: `md_evals/provider_registry.py`
  - **Dependencies**: None
  - **Type**: Feature
  - **Effort**: Medium

- [ ] **1.8** Register GitHub Models provider in registry
  - **Description**: Add auto-registration logic to `md_evals/providers/github_models.py` to register `GitHubModelsProvider` with registry on module import
  - **Files affected**: `md_evals/providers/github_models.py`, `md_evals/provider_registry.py`
  - **Dependencies**: 1.2, 1.7
  - **Type**: Feature
  - **Effort**: Small

- [ ] **1.9** Update dependencies in pyproject.toml
  - **Description**: Add `azure-ai-inference>=1.0.0` to dependencies; optionally add `python-dotenv>=1.0.0` as recommended optional dependency
  - **Files affected**: `pyproject.toml`
  - **Dependencies**: None
  - **Type**: Feature (Configuration)
  - **Effort**: Small

- [ ] **1.10** Unit test: Provider initialization with valid token
  - **Description**: Write test in `tests/test_github_models_provider.py` to verify `GitHubModelsProvider` initializes successfully with valid `GITHUB_TOKEN`
  - **Files affected**: `tests/test_github_models_provider.py`
  - **Dependencies**: 1.2, 1.3
  - **Type**: Test
  - **Effort**: Small

- [ ] **1.11** Unit test: Provider initialization without token (error case)
  - **Description**: Write test to verify `AuthenticationError` is raised with clear message when `GITHUB_TOKEN` is missing or invalid
  - **Files affected**: `tests/test_github_models_provider.py`
  - **Dependencies**: 1.2, 1.3
  - **Type**: Test
  - **Effort**: Small

- [ ] **1.12** Unit test: Supported models and metadata
  - **Description**: Write test to verify `supported_models()` returns all 4 models with correct metadata (context window, temperature range, rate limits)
  - **Files affected**: `tests/test_github_models_provider.py`
  - **Dependencies**: 1.6
  - **Type**: Test
  - **Effort**: Small

- [ ] **1.13** Unit test: Streaming token counting approximation
  - **Description**: Write test with mocked Azure SDK streaming response to verify token counting extracts metadata correctly and falls back to estimation when metadata unavailable
  - **Files affected**: `tests/test_github_models_provider.py`
  - **Dependencies**: 1.4, 1.5
  - **Type**: Test
  - **Effort**: Medium

- [ ] **1.14** Unit test: Error handling (rate limits, context window, API errors)
  - **Description**: Write tests to verify `RateLimitError`, `ContextWindowError`, `StreamingError`, and `APIError` are raised appropriately with actionable messages
  - **Files affected**: `tests/test_github_models_provider.py`
  - **Dependencies**: 1.5
  - **Type**: Test
  - **Effort**: Medium

- [ ] **1.15** Unit test: Provider registry auto-discovery
  - **Description**: Write test in `tests/test_provider_registry.py` to verify GitHub Models provider is automatically registered and retrievable from registry
  - **Files affected**: `tests/test_provider_registry.py`
  - **Dependencies**: 1.7, 1.8
  - **Type**: Test
  - **Effort**: Small

- [ ] **1.16** Integration test: Real API call with GitHub Models (optional, marked as @pytest.mark.integration)
  - **Description**: Write integration test that makes real API call to GitHub Models endpoint with valid token (if available), verifies response format and token counting accuracy
  - **Files affected**: `tests/integration_github_models.py`
  - **Dependencies**: 1.2, 1.4
  - **Type**: Test
  - **Effort**: Medium

---

## Phase 2: Documentation & Examples

User enablement and guidance for GitHub Models setup, authentication, and usage.

- [ ] **2.1** Create "Getting Started with GitHub Models" guide
  - **Description**: Create `docs/getting_started_github_models.md` with step-by-step setup: get GitHub token, set `GITHUB_TOKEN` env var, verify token, list available models
  - **Files affected**: `docs/getting_started_github_models.md`
  - **Dependencies**: 1.2, 1.6
  - **Type**: Documentation
  - **Effort**: Small

- [ ] **2.2** Create models reference table
  - **Description**: Create `docs/models_reference.md` with table of all 4 supported models, their capabilities (context window, temperature range), pricing (free tier), rate limits, and use case recommendations
  - **Files affected**: `docs/models_reference.md`
  - **Dependencies**: 1.6
  - **Type**: Documentation
  - **Effort**: Small

- [ ] **2.3** Add authentication troubleshooting section
  - **Description**: Add section to `docs/getting_started_github_models.md` covering common errors: missing token, invalid token format, rate limits, network connectivity, with resolution steps and links to generate new token
  - **Files affected**: `docs/getting_started_github_models.md`
  - **Dependencies**: 2.1, 1.5
  - **Type**: Documentation
  - **Effort**: Small

- [ ] **2.4** Create example evaluation config file
  - **Description**: Create `examples/eval_with_github_models.yaml` showing how to specify `defaults: { provider: "github-models", model: "claude-3.5-sonnet" }` and run a complete evaluation
  - **Files affected**: `examples/eval_with_github_models.yaml`
  - **Dependencies**: 1.6
  - **Type**: Documentation
  - **Effort**: Small

- [ ] **2.5** Update README with GitHub Models as low-cost option
  - **Description**: Add section to `README.md` highlighting GitHub Models as recommended free/low-cost alternative, with quick link to getting started guide and example
  - **Files affected**: `README.md`
  - **Dependencies**: 2.1, 2.2
  - **Type**: Documentation
  - **Effort**: Small

---

## Phase 3: CLI Improvements

Developer experience enhancements for provider selection and model discovery.

- [ ] **3.1** Add `--provider` flag to CLI `run` command
  - **Description**: Modify `md_evals/cli.py` to add `--provider github-models` argument to `run` command, allowing users to select provider at runtime
  - **Files affected**: `md_evals/cli.py`
  - **Dependencies**: 1.7, 1.8
  - **Type**: Feature
  - **Effort**: Small

- [ ] **3.2** Implement `--list-models` CLI command
  - **Description**: Add new CLI command `md-evals list-models [--provider github-models]` to display all available models for specified provider with metadata (context window, rate limits, cost)
  - **Files affected**: `md_evals/cli.py`
  - **Dependencies**: 1.7, 1.6
  - **Type**: Feature
  - **Effort**: Medium

- [ ] **3.3** Add provider selection via config file
  - **Description**: Modify config loader to recognize `defaults: { provider: "github-models", model: "..." }` in evaluation config and pass to provider registry
  - **Files affected**: `md_evals/config.py` (or equivalent)
  - **Dependencies**: 1.7
  - **Type**: Feature
  - **Effort**: Medium

- [ ] **3.4** Add provider name resolution (friendly name support)
  - **Description**: Implement name resolution in provider registry to accept variants: `"github-models"`, `"GitHub Models"`, `"github_models"` and resolve to correct provider
  - **Files affected**: `md_evals/provider_registry.py`
  - **Dependencies**: 1.7
  - **Type**: Feature
  - **Effort**: Small

- [ ] **3.5** Enhance error messages with actionable guidance
  - **Description**: Update CLI error handling to catch provider exceptions and display user-friendly messages with guidance (e.g., "Set `export GITHUB_TOKEN=github_pat_...` and check https://github.com/settings/tokens")
  - **Files affected**: `md_evals/cli.py`, exception handlers
  - **Dependencies**: 1.5, 3.1
  - **Type**: Feature
  - **Effort**: Small

- [ ] **3.6** Add debug logging for provider initialization
  - **Description**: Add structured logging (using `logging` module) to trace provider initialization, token loading, model selection, and first API call for debugging
  - **Files affected**: `md_evals/providers/github_models.py`, `md_evals/cli.py`
  - **Dependencies**: 1.2, 3.1
  - **Type**: Feature
  - **Effort**: Small

---

## Implementation Order & Dependencies

### Wave 1: Foundation (Days 1–2)
1. **1.1** → **1.7** → **1.8**: Establish provider package and registry
2. **1.2** → **1.3** → **1.4** → **1.5** → **1.6**: Build core GitHub Models provider
3. **1.9**: Add dependency

### Wave 2: Testing (Days 3–4)
4. **1.10** → **1.11** → **1.12** → **1.13** → **1.14**: Unit tests for provider
5. **1.15**: Registry tests
6. **1.16** (optional): Integration tests with real API

### Wave 3: CLI & Integration (Days 5–6)
7. **3.1** → **3.2** → **3.3** → **3.4** → **3.5** → **3.6**: CLI enhancements
8. End-to-end test: Run evaluation with `--provider github-models`

### Wave 4: Documentation (Days 7)
9. **2.1** → **2.2** → **2.3** → **2.4** → **2.5**: User guides and examples

### Critical Path
- **1.1** → **1.2** → **1.3** → **1.4** → **3.1** → E2E test

---

## Acceptance Criteria

### Phase 1 ✅
- [ ] `GitHubModelsProvider` implements async `complete()` interface
- [ ] All 4 models (claude-3.5-sonnet, gpt-4o, deepseek-r1, grok-3) initialize without error
- [ ] Token counting works for all models with ±15% accuracy
- [ ] Authentication via `GITHUB_TOKEN` env var successful
- [ ] Rate limit, context window, and API errors raise specific exceptions with clear messages
- [ ] Unit tests cover initialization, auth, inference, error cases (>80% coverage)
- [ ] No breaking changes to existing OpenAI/Anthropic workflows

### Phase 2 ✅
- [ ] "Getting Started with GitHub Models" guide complete with steps for token setup
- [ ] Models reference table includes all 4 models with capabilities and pricing
- [ ] Authentication troubleshooting section covers common errors
- [ ] Example config file runs without modification
- [ ] README highlights GitHub Models as low-cost option

### Phase 3 ✅
- [ ] `md-evals run eval.yaml --provider github-models` works
- [ ] `md-evals list-models --provider github-models` displays all 4 models with metadata
- [ ] Config file provider selection (YAML) respected
- [ ] Friendly provider names accepted (github-models, GitHub Models, github_models)
- [ ] Error messages guide users to documentation and token generation

---

## Verification Checklist

- [ ] All 18 tasks completed and tested
- [ ] Provider passes unit tests (>80% code coverage)
- [ ] Integration test succeeds with real API (or mark @pytest.mark.integration to skip in CI)
- [ ] E2E: Run sample evaluation with `--provider github-models --model claude-3.5-sonnet`
- [ ] CLI `list-models` command displays correct output
- [ ] Documentation is accessible and examples are runnable
- [ ] No regressions to OpenAI/Anthropic providers
- [ ] Ready for Phase verification (sdd-verify)
