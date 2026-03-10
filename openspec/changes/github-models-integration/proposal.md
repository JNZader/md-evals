# Proposal: GitHub Models Integration for md-evals

## Intent

md-evals currently supports proprietary LLM providers (OpenAI, Anthropic) that require paid API keys. GitHub Models offers **free or low-cost access** to multiple state-of-the-art models (Claude 3.5 Sonnet, GPT-4o, DeepSeek-R1, Grok-3) via the Azure AI Inference SDK with GitHub authentication. Adding GitHub Models support removes cost barriers for users, democratizes evaluation access, and provides an ideal provider for community-driven testing workflows.

## Scope

### Phase 1: LLM Provider Integration (Core)
- [ ] Implement `GitHubModelsProvider` class integrating Azure AI Inference SDK
- [ ] Support core models: Claude 3.5 Sonnet, GPT-4o, DeepSeek-R1, Grok-3
- [ ] Implement streaming token counting (via response parsing)
- [ ] Add GitHub token authentication (`GITHUB_TOKEN` env var)
- [ ] Integrate with existing provider registry and model detection
- [ ] Write unit tests for provider initialization and basic inference

### Phase 2: Documentation & Examples (User Enablement)
- [ ] Create user guide: "Getting Started with GitHub Models"
- [ ] Document available models, pricing, token limits
- [ ] Add tutorial: Running evaluations with GitHub Models
- [ ] Create example config files (default provider, model selection)
- [ ] Update README with GitHub Models as recommended low-cost option
- [ ] Document authentication setup and troubleshooting

### Phase 3: CLI Improvements (Developer Experience)
- [ ] Add `--provider github-models` flag to CLI
- [ ] Implement automatic provider/model detection from config
- [ ] Add `--list-models` to show available models per provider
- [ ] Improve error messages for missing credentials/rate limits
- [ ] Add debug logging for provider initialization

## Approach

**Phase 1: Integration**
- Create new provider module: `md_evals/providers/github_models.py`
- Wrap Azure AI Inference SDK (`azure-ai-inference` package)
- Implement `AsyncLLMProvider` interface following existing patterns (OpenAI, Anthropic)
- Use environment variable-based auth (`GITHUB_TOKEN`)
- Leverage streaming API for token counting approximation
- Register provider in global registry for auto-discovery

**Phase 2: Documentation**
- Add markdown guides to `/docs` folder
- Embed runnable examples in docstrings
- Update CHANGELOG and feature matrix

**Phase 3: CLI**
- Extend existing argument parser with `--provider` and `--list-models` options
- Add config-based provider detection (`.md-evals.yml` or similar)
- Enhance help text and error messages

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `md_evals/providers/` | New | Add `github_models.py` provider module |
| `md_evals/provider_registry.py` | Modified | Auto-register GitHub Models provider |
| `md_evals/cli.py` | Modified | Add `--provider` and `--list-models` flags |
| `docs/` | New | Add user guides and examples |
| `pyproject.toml` / `requirements.txt` | Modified | Add `azure-ai-inference` dependency |
| `README.md` | Modified | Highlight GitHub Models as low-cost option |
| Tests | New | Provider unit tests, integration examples |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Azure SDK API changes or deprecation | Low | Pin `azure-ai-inference` version; monitor GitHub Models docs |
| GitHub token rate limiting (free tier) | Medium | Document rate limits; add clear error messages; suggest caching |
| Token counting accuracy (streaming-based) | Medium | Use response length approximation; document limitation; offer exact counting via mock |
| User confusion with provider selection | Medium | Provide clear CLI defaults and config examples; default to GitHub Models if available |
| Breaking changes to existing provider interface | Low | Implement interface contract tests; add compatibility layer if needed |

## Rollback Plan

- **Remove provider**: Delete `md_evals/providers/github_models.py`
- **Update registry**: Remove GitHub Models registration from `provider_registry.py`
- **Update CLI**: Remove `--provider` and `--list-models` flags (or stub them)
- **Clean dependencies**: Remove `azure-ai-inference` from `pyproject.toml`
- **Revert docs**: Remove GitHub Models guides and examples from `/docs`
- **Backwards compatible**: Existing OpenAI/Anthropic workflows unaffected

## Dependencies

- `azure-ai-inference` (new)
- Existing: `python >= 3.10`, `pydantic`, `pytest`
- External: GitHub Models service (free tier sufficient for testing)

## Success Criteria

- [ ] GitHub Models provider fully implements `AsyncLLMProvider` interface
- [ ] All Phase 1 models (Claude 3.5, GPT-4o, DeepSeek-R1, Grok-3) work end-to-end
- [ ] Unit tests cover initialization, authentication, and basic inference
- [ ] Token counting works for all models (within 10% accuracy vs. model estimates)
- [ ] CLI `--provider github-models` selects provider and runs evaluations
- [ ] Documentation is complete and includes working runnable examples
- [ ] No breaking changes to existing OpenAI/Anthropic provider workflows
- [ ] GitHub token auth works with `GITHUB_TOKEN` env var
- [ ] Rate limit errors have clear user-facing messages

---

**Status**: Ready for Specification & Design  
**Complexity**: Medium (new provider, familiar patterns)  
**Effort Estimate**: 3-4 weeks (Phase 1: 1 week, Phase 2: 1 week, Phase 3: 1-2 weeks)
