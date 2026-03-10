# Design: GitHub Models Integration

## Technical Approach

Integrate GitHub Models via Azure AI Inference SDK as a new provider alongside existing OpenAI/Anthropic implementations. The `GitHubModelsProvider` will follow the established async provider pattern, using environment-based authentication and streaming responses for token counting. GitHub Models are accessed via Azure's endpoint but authenticated with GitHub PAT tokens, providing a seamless low-cost alternative for community users.

---

## Architecture Decisions

### Decision: Provider Architecture — Wrapped SDK vs. Custom Client

**Choice**: Wrap Azure AI Inference SDK in a provider class that implements md-evals' existing async interface.

**Alternatives considered**:
1. Direct litellm integration via custom model string routing
2. Custom HTTP client directly to GitHub Models endpoint
3. Lightweight wrapper with minimal abstraction

**Rationale**:
- Azure SDK is actively maintained and handles complex auth/retry/streaming
- Wrapping allows consistent provider interface across OpenAI/Anthropic/GitHub
- Provider registry pattern supports future provider additions (Claude.ai Direct, Ollama, etc.)
- Clear separation: SDK concerns (auth, retries) vs. md-evals concerns (skill injection, token tracking)

---

### Decision: Authentication — Environment Variable vs. Config File

**Choice**: Use `GITHUB_TOKEN` environment variable exclusively; optional `.env` file support.

**Alternatives considered**:
1. Config file at `~/.md-evals/config.yaml` with token
2. Keyring/secrets manager integration
3. Interactive CLI prompt for token

**Rationale**:
- GitHub users already set `GITHUB_TOKEN` in shells for git/gh CLI
- Environment variable is standard for CI/CD (GitHub Actions sets it automatically)
- Supports `.env` files via python-dotenv (common pattern)
- No need for additional infrastructure (keyring)
- Interactive prompt breaks CI workflows and is not production-friendly

---

### Decision: Token Counting — Streaming Metadata vs. Tiktoken

**Choice**: Extract token counts from Azure SDK streaming response metadata; fallback to approximation.

**Alternatives considered**:
1. Use tiktoken library (GPT models only, requires separate dependencies)
2. Exact counting via separate API call (doubles latency)
3. Pure estimation via regex/tokenizer library

**Rationale**:
- Azure SDK provides token counts in streaming messages automatically
- No extra dependency or API calls
- Handles model-specific tokenization (Claude uses different tokenizer than GPT)
- Fallback estimation is acceptable for ±15% accuracy within spec
- Streaming already parsed; metadata extraction is free

---

### Decision: Error Handling — Granular Exception Hierarchy

**Choice**: Define custom exception classes for each error category with actionable messages.

**Exceptions**:
```python
GitHubModelsError (base)
├── AuthenticationError       → GITHUB_TOKEN missing/invalid
├── ModelNotSupportedError    → Unsupported model name
├── RateLimitError           → API rate limit exceeded (with retry-after)
├── ContextWindowError       → Prompt exceeds model's context window
├── StreamingError           → Network disconnect during streaming
├── APIError                 → Generic API error (500, timeout, etc.)
```

**Rationale**:
- Client code (evaluator, CLI) can catch specific exceptions and provide tailored guidance
- Rate limit exceptions include retry-after info for intelligent backoff
- Context window errors guide users to longer-context models
- Clear separation of concerns: provider errors vs. infrastructure errors

---

### Decision: Integration Points — Minimal Changes to Existing Code

**Choice**: Create new provider module; register in global registry; minimal changes to CLI/config.

**Alternatives considered**:
1. Bake GitHub Models into existing LLMAdapter (violates single responsibility)
2. Refactor entire provider system (breaking change)
3. Plugin system with hot-loading (over-engineered for 4 providers)

**Rationale**:
- Existing LLMAdapter uses litellm (already supports many providers via string routing)
- New GitHubModelsProvider is optional; not loaded if unused
- Provider registry pattern allows init-time provider discovery
- CLI changes are additive (`--provider` flag, `--list-models` command)
- No breaking changes to existing OpenAI/Anthropic workflows

---

### Decision: Model Registry — Static Registration vs. Dynamic Discovery

**Choice**: Static registration of 4 supported models with hardcoded metadata.

**Alternatives considered**:
1. Query GitHub Models API for available models (adds startup latency)
2. Lazy registration on first access
3. Configuration-driven model list

**Rationale**:
- GitHub Models API is stable and unlikely to change frequently
- Static list is fast (no API call on startup)
- Clear documentation of supported models and limits
- Easy to test and debug
- Configuration file can override if needed (future enhancement)

---

## Data Flow

### Complete Request Flow

```
User Prompt
    ↓
CLI / Config (--provider github-models, --model claude-3.5-sonnet)
    ↓
Provider Registry (lookup GitHubModelsProvider)
    ↓
GitHubModelsProvider.complete()
    ├─ Load GITHUB_TOKEN from environment
    ├─ Validate token (auth call to Azure endpoint)
    ├─ Inject skill content as system prompt (if provided)
    ├─ Build message list [system, user]
    └─ Call Azure SDK with streaming=True
        ↓
    Azure AI Inference SDK
        ├─ Authenticate with GitHub token
        ├─ Route request to GitHub Models endpoint
        └─ Stream response chunks
            ↓
    GitHubModelsProvider._handle_stream()
        ├─ Collect streaming chunks
        ├─ Extract token metadata from final message
        ├─ Parse response content
        └─ Return LLMResponse(content, tokens, duration_ms, model, provider)
            ↓
Evaluator.evaluate()
    ├─ Compare responses (CONTROL vs. WITH_SKILL)
    ├─ Count tokens for billing/reporting
    └─ Record results
        ↓
Reporter.output()
    └─ Display results in table/JSON/markdown format
```

### Authentication Flow

```
GitHubModelsProvider.__init__(model_name)
    ↓
Load GITHUB_TOKEN from:
    1. Environment variable (os.getenv("GITHUB_TOKEN"))
    2. .env file (if python-dotenv installed)
    ↓
Validate token format (starts with "github_pat_")
    ↓
Initialize Azure ChatCompletionsClient(
    endpoint="https://models.inference.ai.azure.com",
    credential=AzureKeyCredential(token)
)
    ↓
Test endpoint connectivity (optional health check)
    ↓
Ready for requests
    
On first request → Azure endpoint validates token
    → If invalid → raise AuthenticationError with guidance
    → If valid → proceed with completion
```

---

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `md_evals/providers/__init__.py` | Create | New providers package (if not exists) |
| `md_evals/providers/github_models.py` | Create | GitHubModelsProvider implementation |
| `md_evals/provider_registry.py` | Create | Global provider registry and auto-discovery |
| `md_evals/llm.py` | Modify | Add provider parameter to LLMAdapter; route to appropriate provider |
| `md_evals/cli.py` | Modify | Add `--provider` flag to `run` command; add `list-models` command |
| `md_evals/models.py` | Modify | Add provider metadata (rate limits, context window, etc.) |
| `pyproject.toml` | Modify | Add `azure-ai-inference` dependency |
| `docs/getting_started_github_models.md` | Create | User guide for GitHub Models setup |
| `docs/models_reference.md` | Create | Reference table of all supported models |
| `tests/test_github_models_provider.py` | Create | Unit tests for provider |
| `tests/integration_github_models.py` | Create | Integration tests with real API calls (optional) |
| `README.md` | Modify | Add GitHub Models section with quick-start |

---

## Interfaces / Contracts

### GitHubModelsProvider Class

```python
class GitHubModelsProvider:
    """Wrapper for Azure AI Inference SDK (GitHub Models)."""
    
    def __init__(
        self,
        model_name: str,
        github_token: str | None = None,
        timeout_seconds: int = 60,
        max_retries: int = 3
    ):
        """Initialize provider.
        
        Args:
            model_name: One of 'claude-3.5-sonnet', 'gpt-4o', 'deepseek-r1', 'grok-3'
            github_token: GitHub PAT (defaults to GITHUB_TOKEN env var)
            timeout_seconds: Request timeout in seconds
            max_retries: Retry count on transient errors
            
        Raises:
            AuthenticationError: Token missing or invalid
            ModelNotSupportedError: Unknown model name
        """
        ...
    
    async def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Complete a prompt.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length (default: model-specific)
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        ...
    
    @staticmethod
    def supported_models() -> dict[str, ModelMetadata]:
        """Return dict of supported models with metadata."""
        return {
            "claude-3.5-sonnet": ModelMetadata(...),
            "gpt-4o": ModelMetadata(...),
            ...
        }
```

### LLMResponse (existing, unchanged)

```python
class LLMResponse(BaseModel):
    content: str                    # Response text
    model: str                      # Model name
    provider: str                   # "github-models"
    tokens: int                     # Estimated token count
    duration_ms: int                # Latency in milliseconds
    raw_response: dict[str, Any]    # Full API response metadata
```

### ModelMetadata (new)

```python
class ModelMetadata(BaseModel):
    name: str                       # Display name
    provider: str                   # Provider name
    context_window: int             # Max input + output tokens
    temperature_range: tuple[float, float]  # Min/max temperature
    rate_limit: str                 # e.g., "15 req/min (free tier)"
    cost: str                       # e.g., "free (free tier)"
    status: str                     # "supported" | "beta" | "deprecated"
    notes: str | None               # Additional info
```

### Provider Registry (new)

```python
class ProviderRegistry:
    """Global registry for LLM providers."""
    
    @staticmethod
    def register(name: str, provider_class) -> None:
        """Register a provider class."""
        ...
    
    @staticmethod
    def get(name: str) -> type:
        """Retrieve provider class by name."""
        ...
    
    @staticmethod
    def list_providers() -> dict[str, type]:
        """List all registered providers."""
        ...
    
    @staticmethod
    def instantiate(
        provider_name: str,
        model_name: str,
        **kwargs
    ) -> "AsyncLLMProvider":
        """Instantiate a provider."""
        ...
```

---

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| **Unit** | Provider initialization, error handling, message building | Mock Azure SDK; use pytest fixtures |
| **Unit** | Token counting from metadata; approximation fallback | Hardcoded streaming responses |
| **Unit** | Provider registry; auto-discovery | Import module and verify registration |
| **Integration** | Real API calls with valid token | Use pytest-asyncio; mark as `@pytest.mark.integration` (skip by default) |
| **Integration** | Rate limit handling; retry logic | Throttle test account or mock 429 responses |
| **E2E** | Full evaluation flow with GitHub Models | Run sample eval with CLI; verify results |

### Test Structure

```
tests/
├── test_github_models_provider.py
│   ├── test_init_with_valid_token()
│   ├── test_init_without_token_raises_error()
│   ├── test_supported_models_list()
│   ├── test_complete_happy_path()
│   ├── test_complete_with_system_prompt()
│   ├── test_rate_limit_error_handling()
│   ├── test_token_counting_approximation()
│   └── test_streaming_interruption()
├── test_provider_registry.py
│   ├── test_github_models_registered()
│   ├── test_instantiate_by_name()
│   └── test_list_providers_includes_github()
├── integration_github_models.py
│   └── @pytest.mark.integration
│       ├── test_real_api_call_claude()
│       ├── test_real_api_call_gpt4()
│       └── test_streaming_with_real_api()
└── cli_github_models.py
    ├── test_list_models_command()
    ├── test_run_with_provider_flag()
    └── test_config_provider_selection()
```

---

## Migration / Rollout

**No migration required.**

This is a **new provider** added alongside existing OpenAI/Anthropic support. Existing evaluations using OpenAI/Anthropic are completely unaffected. Users can adopt GitHub Models at their own pace by setting `GITHUB_TOKEN` and using `--provider github-models`.

### Rollout Plan

1. **Phase 1 (Week 1)**: Implement and test provider in isolation
2. **Phase 2 (Week 2)**: Integrate with CLI and config loading; test end-to-end
3. **Phase 3 (Week 3)**: Documentation and examples; collect user feedback
4. **Phase 4 (Week 4 optional)**: Optimize token counting; add advanced features

### Feature Flag (Optional)

If needed, add a feature flag to disable GitHub Models:
```yaml
# config.yaml
features:
  github_models_enabled: true  # default true
```

Useful if there are outages or issues discovered post-release.

---

## Key Design Patterns

### 1. Async Provider Interface
All providers implement `async def complete()` to enable concurrent evaluations.

### 2. Environment-First Configuration
Credentials and model selection come from environment/config, not CLI prompts. Better for automation.

### 3. Streaming Token Counting
Avoids extra API calls; metadata is free when streaming already enabled.

### 4. Custom Exception Hierarchy
Specific exceptions allow client code to handle different failure modes gracefully.

### 5. Provider Registry Pattern
Dynamic provider discovery supports future additions (Claude Direct, Ollama, etc.) without code changes.

---

## Open Questions

- [ ] Should token counting fallback use `len(content) / 4` or a more sophisticated estimator?
  - **Recommended**: Implement both; use simple formula for initial release, add tiktoken fallback in Phase 2
- [ ] Do we support custom Azure endpoints (for on-prem or sovereign cloud)?
  - **Recommended**: Not Phase 1; add as optional parameter in Phase 2
- [ ] Should `--list-models` show rate limits and pricing?
  - **Recommended**: Yes, include pricing tier (free/paid) and rate limits in output
- [ ] How to handle GitHub Models API outages?
  - **Recommended**: Document fallback to other providers; add health check endpoint in Phase 2

---

## Dependencies

**New**:
- `azure-ai-inference>=1.0.0` — Azure SDK for AI inference

**Existing**:
- `pydantic>=2.6.0` — Type validation
- `tenacity>=8.2.0` — Retry logic (already required)
- `httpx>=0.27.0` — HTTP client (already required)

**Optional**:
- `python-dotenv>=1.0.0` — Load .env files (recommended but not required)

---

## Deployment Considerations

### Environment Requirements
- Python ≥ 3.12
- Valid GitHub account with GitHub Models access (free tier available)
- Network access to `https://models.inference.ai.azure.com`

### CI/CD Integration
- GitHub Actions automatically sets `GITHUB_TOKEN` → no additional setup required
- Test accounts can use free tier (sufficient for CI testing)

### Backward Compatibility
- Zero breaking changes to existing provider interface
- Existing workflows using OpenAI/Anthropic unaffected
- New dependency (`azure-ai-inference`) only loaded when GitHub Models provider is instantiated

---

## Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| Provider init time | < 100ms | Minimal (just create client object) |
| First request latency | 1-2s | Azure endpoint routing overhead |
| Streaming latency | Model-dependent | 20-60ms per chunk |
| Token counting overhead | < 50ms | Metadata extraction only |
| Max concurrent requests | 15 (free tier) | Configurable per rate limit |

---

## Monitoring & Observability

### Logging Points
- Provider initialization (token loaded, model selected)
- Each request (prompt length, model, start/end time)
- Errors (auth failures, rate limits, streaming errors)
- Token counts (actual vs. estimated)

### Metrics to Track (Future)
- Provider usage (GitHub Models vs. OpenAI vs. Anthropic)
- Error rates by type (auth, rate limit, timeout)
- Average token count accuracy
- Request latency distribution
