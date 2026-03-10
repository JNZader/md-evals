# Specification: GitHub Models Integration

## Purpose

Define functional and non-functional requirements for adding GitHub Models support to md-evals, enabling free/low-cost LLM evaluation via Azure AI Inference SDK.

---

## Functional Requirements

### Requirement: GitHub Models Provider Implementation

The system **MUST** implement a `GitHubModelsProvider` that wraps the Azure AI Inference SDK and provides LLM completions compatible with md-evals' existing provider interface.

#### Scenario: Initialize GitHub Models provider with valid token

- GIVEN a valid `GITHUB_TOKEN` environment variable is set
- WHEN a `GitHubModelsProvider` is instantiated with a supported model name (e.g., "claude-3.5-sonnet")
- THEN the provider **MUST** initialize successfully and be ready to accept completion requests

#### Scenario: Initialize provider without valid token

- GIVEN `GITHUB_TOKEN` is missing or invalid
- WHEN a `GitHubModelsProvider` is instantiated
- THEN the provider **MUST** raise an `AuthenticationError` with a clear message: "GITHUB_TOKEN environment variable not set or invalid"

#### Scenario: Attempt to use unsupported model

- GIVEN a provider is initialized with an unsupported model name (e.g., "gpt-2")
- WHEN the provider's `complete()` method is called
- THEN it **MUST** raise a `ModelNotSupportedError` with a message listing available models

---

### Requirement: Model Support

The system **MUST** support the four primary GitHub Models:
1. **claude-3.5-sonnet** — Anthropic Claude 3.5 Sonnet
2. **gpt-4o** — OpenAI GPT-4 Optimized
3. **deepseek-r1** — DeepSeek R1
4. **grok-3** — xAI Grok-3

Each model **MUST** be registered in the global provider registry with metadata (max tokens, default temperature, rate limit tier).

#### Scenario: List available models

- GIVEN the CLI command `md-evals list-models --provider github-models` is invoked
- WHEN the provider registry is queried
- THEN the output **MUST** display all four supported models with their metadata (context window, rate limits)

#### Scenario: Select model from CLI

- GIVEN a user runs `md-evals run eval.yaml --provider github-models --model claude-3.5-sonnet`
- WHEN the evaluation engine initializes
- THEN the Claude model **MUST** be used for all completions in the evaluation

---

### Requirement: Streaming Completions with Token Counting

The system **MUST** support streaming responses from GitHub Models and approximate token counts from the streamed response.

#### Scenario: Complete prompt and extract token count

- GIVEN a prompt "Tell me a joke about Python"
- WHEN `provider.complete(prompt)` is called
- THEN the response **MUST** contain:
  - `content`: The complete response text
  - `tokens`: An estimated token count (within ±15% accuracy for the response)
  - `duration_ms`: Elapsed time in milliseconds
  - `model`: The model name used
  - `provider`: "github-models"

#### Scenario: Handle streaming timeout

- GIVEN a long-running streaming request
- WHEN a network timeout occurs after 60 seconds (default)
- THEN the provider **MUST** raise a `TimeoutError` with clear error message and allow retry

#### Scenario: Graceful handling of partial responses

- GIVEN streaming is interrupted mid-response
- WHEN the connection drops
- THEN the provider **MUST** return the partial content received with an accurate token count for that partial response (not estimated for full response)

---

### Requirement: Authentication via GitHub Token

The system **MUST** authenticate using `GITHUB_TOKEN` environment variable.

#### Scenario: Load token from environment

- GIVEN `GITHUB_TOKEN` is set in the environment
- WHEN the provider is initialized
- THEN the token **MUST** be loaded and used for all API requests

#### Scenario: Token validation on initialization

- GIVEN a malformed or expired token
- WHEN the provider attempts its first API call
- THEN it **MUST** raise `AuthenticationError` with guidance: "Check your GITHUB_TOKEN in ~/.bash_profile or .env file"

---

### Requirement: Error Handling and Rate Limits

The system **MUST** gracefully handle rate limits and provide clear user feedback.

#### Scenario: Rate limit exceeded (free tier)

- GIVEN the free tier rate limit is exceeded (e.g., 15 requests/min)
- WHEN `provider.complete()` is called
- THEN it **MUST** raise `RateLimitError` with:
  - Message: "GitHub Models rate limit exceeded. Free tier: 15 requests/min"
  - Retry-After value (if provided by API)
  - Suggestion: "Consider caching responses or upgrading to paid tier"

#### Scenario: Automatic retry on transient error

- GIVEN a transient HTTP 503 (Service Unavailable) error
- WHEN `provider.complete()` is called
- THEN it **MUST** retry up to 3 times with exponential backoff (1s, 2s, 4s) before failing

#### Scenario: Clear error for misconfigured provider

- GIVEN a user runs evaluation without setting `GITHUB_TOKEN`
- WHEN the provider is initialized
- THEN error message **MUST** include:
  - What went wrong: "GITHUB_TOKEN not configured"
  - How to fix: "Set `export GITHUB_TOKEN=github_pat_...` or update .env"
  - Where to get token: "Generate at https://github.com/settings/tokens"

---

### Requirement: Integration with Provider Registry

The system **MUST** automatically register `GitHubModelsProvider` and allow selection via CLI and config.

#### Scenario: Auto-discover provider from registry

- GIVEN the provider module is installed
- WHEN the application starts
- THEN `GitHubModelsProvider` **MUST** be automatically registered in the global provider registry

#### Scenario: Select provider via CLI flag

- GIVEN a user runs `md-evals run eval.yaml --provider github-models`
- WHEN the evaluator is initialized
- THEN the GitHub Models provider **MUST** be selected and instantiated

#### Scenario: Select provider via config file

- GIVEN `eval.yaml` contains `defaults: { provider: "github-models", model: "claude-3.5-sonnet" }`
- WHEN the config is loaded
- THEN GitHub Models **MUST** be used by default

#### Scenario: Provider name resolution

- GIVEN various provider name formats are used:
  - `"github-models"` (short name)
  - `"GitHub Models"` (friendly name)
  - `"github_models"` (snake_case)
- WHEN any format is used in CLI or config
- THEN the provider **MUST** be correctly resolved to `GitHubModelsProvider`

---

### Requirement: Skill Injection Support

The system **MUST** support injecting skill content (from SKILL.md) as system prompts when using GitHub Models.

#### Scenario: Complete with skill injection

- GIVEN a skill file `/path/to/SKILL.md` exists with custom guidelines
- WHEN evaluation runs with `--skill-path /path/to/SKILL.md` and `--provider github-models`
- THEN skill content **MUST** be injected into system prompt (via `inject_skill()` function)
- AND the GitHub Models provider **MUST** handle system prompts correctly

---

## Non-Functional Requirements

### Requirement: Performance

Token counting approximation **MUST** complete within 50ms of response completion (i.e., not add significant overhead).

#### Scenario: Token count latency

- GIVEN a response of 500 tokens
- WHEN token counting is performed via response parsing
- THEN the additional latency **MUST** be < 50ms

---

### Requirement: Reliability

The provider **MUST** maintain 99% success rate for successful requests over a 24-hour period (excepting rate limits and network outages).

#### Scenario: Consistent inference across retries

- GIVEN a valid request that initially fails with transient error
- WHEN retried automatically
- THEN the retry **MUST** succeed and produce valid response without duplicating content

---

### Requirement: Documentation Clarity

All authentication, model availability, and rate limit information **MUST** be documented with examples.

#### Scenario: User reads documentation

- GIVEN a user reads docs about GitHub Models
- THEN they **MUST** be able to:
  - Understand how to get a GitHub token
  - Know which models are available and their capabilities
  - Understand free tier rate limits and costs
  - See a complete working example

---

### Requirement: Dependency Management

The system **MUST** explicitly declare `azure-ai-inference` as a dependency with pinned version.

#### Scenario: Install with dependencies

- GIVEN `pip install md-evals[github-models]` is run
- WHEN installation completes
- THEN `azure-ai-inference` **MUST** be installed at specified version

---

## Edge Cases & Error Scenarios

### Edge Case: Empty response from API

- GIVEN the API returns an empty completion
- WHEN `provider.complete()` processes the response
- THEN it **MUST** return a response with empty `content` string and `tokens=0`

### Edge Case: Extremely long prompt

- GIVEN a prompt exceeds the model's context window (e.g., > 200k tokens for claude-3.5)
- WHEN the prompt is sent to the API
- THEN the API **MUST** return an error (handled by Azure SDK)
- AND the provider **MUST** raise `ContextWindowExceededError` with suggestion to use a longer-context model

### Edge Case: Unicode and special characters in prompts

- GIVEN a prompt contains emoji, CJK characters, or other Unicode
- WHEN sent through the provider
- THEN the complete flow (tokenization, transmission, response) **MUST** preserve all characters correctly

### Edge Case: Network connectivity loss during streaming

- GIVEN the network disconnects mid-stream
- WHEN the provider is processing a response
- THEN it **MUST** raise `StreamingError` and NOT partially return incomplete tokens

---

## Token Counting Strategy

### Approach: Streaming-Based Approximation

Since GitHub Models API returns token counts in streaming metadata, the provider **MUST**:

1. **Collect streaming chunks** from the API response
2. **Parse token metadata** from the final stream message
3. **Return token count** from API metadata if available
4. **Fallback to estimation** (len(content) / 4 for English text) if metadata unavailable

### Accuracy Target

- Token counts **MUST** be within ±10% of model's internal count for typical responses
- Edge cases (unusual Unicode, code) may have ±15% variance

### Limitation Documentation

If exact token counting is unavailable via streaming, **MUST** document:
- "Token counts are approximated from streamed response metadata"
- "For exact counts, enable debug mode to see raw API response"

---

## Supported Models & Characteristics

| Model | Provider | Context Window | Temperature Range | Status | Notes |
|-------|----------|-----------------|-------------------|--------|-------|
| `claude-3.5-sonnet` | Anthropic | 200k | 0.0–2.0 | Supported | Recommended for complex reasoning |
| `gpt-4o` | OpenAI | 128k | 0.0–2.0 | Supported | Strong general-purpose capability |
| `deepseek-r1` | DeepSeek | 64k | 0.0–1.0 | Supported | Lower cost, good for coding |
| `grok-3` | xAI | 128k | 0.0–2.0 | Supported | Latest reasoning model |

---

## Acceptance Criteria

✅ **Phase 1 (Core Integration)**
- [ ] `GitHubModelsProvider` class implements `AsyncLLMProvider` interface
- [ ] All 4 models initialize and complete basic prompts successfully
- [ ] Token counting works for all models with ±15% accuracy
- [ ] Authentication via `GITHUB_TOKEN` env var works
- [ ] Rate limit errors are clear and actionable
- [ ] Unit tests cover initialization, auth, inference, and error cases
- [ ] No breaking changes to existing OpenAI/Anthropic workflows

✅ **Phase 2 (Documentation)**
- [ ] User guide: "Getting Started with GitHub Models"
- [ ] Model matrix with pricing and limits
- [ ] Complete example config file
- [ ] Authentication troubleshooting section
- [ ] README mentions GitHub Models as low-cost option

✅ **Phase 3 (CLI)**
- [ ] `--provider github-models` flag works
- [ ] `--list-models` shows GitHub Models with metadata
- [ ] CLI defaults to GitHub Models if `GITHUB_TOKEN` is set
- [ ] Error messages guide users to documentation
