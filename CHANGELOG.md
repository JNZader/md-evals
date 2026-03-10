# Changelog

All notable changes to md-evals will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub Models provider integration (free/low-cost LLM support)
- CLI `--provider` flag for model provider selection
- `list-models` command to show available models per provider
- Support for Claude 3.5 Sonnet, GPT-4o, DeepSeek-R1, and Grok-3 models
- Comprehensive GitHub Models documentation and examples

### Changed
- Enhanced error messages with actionable guidance
- Updated CLI help text with GitHub Models usage
- Improved token counting accuracy in streaming responses

### Fixed
- Token counting accuracy within ±12% target

---

## [1.0.0] - 2026-03-10

### Added
- Initial public release
- A/B testing framework (Control vs Treatment evaluation)
- Multiple treatment support with wildcards (LCC_*, etc.)
- Hybrid evaluation: regex patterns + LLM-as-judge
- Rich terminal output with comparison tables
- JSON/Markdown export for results analysis
- Linter for SKILL.md files (400-line limit enforcement)
- Support for OpenAI and Anthropic LLM providers
- Comprehensive documentation website (Docsify-based)
- Docker support for reproducible evaluations
- Example skills and evaluation configurations

### Documentation
- Getting Started guide
- API reference and CLI commands
- Architecture decisions document (ADR)
- Integration guide for custom evaluators
- Troubleshooting guide
- FAQ section

### Testing
- Unit tests for core functionality
- Integration tests for LLM providers
- Edge case coverage for mutations and error handling
- Mutation testing suite (58-64% kill rate)

### Infrastructure
- GitHub Actions CI/CD pipeline
- Automated documentation deployment
- Code coverage tracking
- Test automation on pull requests

---

## Archives

Detailed implementation reports and design documents are archived in:
- `openspec/archive/` - SDD (Spec-Driven Development) artifacts
- `openspec/archive/mutations/` - Mutation testing analysis
- `openspec/archive/documentation-sdd/` - Documentation SDD cycle
- `openspec/archive/github-models-integration/` - GitHub Models integration reports

---

## Contributing

See [CONTRIBUTING.md](https://github.com/JNZader/md-evals/blob/main/CONTRIBUTING.md) for guidelines.

---

## License

MIT License - See LICENSE file for details
