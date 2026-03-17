# Phase 4: Ship & Scale — Proposal

## Intent

Deliver the final three features that make md-evals production-ready for CI pipelines, shareable reports, and plugin ecosystems.

## Scope

### Feature #6: Eval Suites + CI Integration
Named groups of skills with per-skill grade thresholds. YAML-driven suite configs that can run in CI with meaningful exit codes (0=pass, 1=config error, 2=threshold failures).

### Feature #7: Static HTML Export
Self-contained HTML reports with inline CSS and SVG radar charts. No JS dependencies. Dark-themed to match the web UI. Supports single-result and full-suite exports.

### Feature #8: Plugin Directory Support
Evaluate entire plugin packages following the agentskills.io structure (plugin.json + skills/ + commands/). Discovers all SKILL.md files, evaluates them, and produces aggregate results.

## Approach

- Pure Python implementations with no new dependencies
- All features get CLI subcommands via Typer
- Comprehensive test suites (40+ tests total)
- Grade comparison uses GRADE_ORDER from scoring.py

## Risks

- Suite runner depends on PipelineRunner which requires LLM — tests use mocking
- HTML export must be fully self-contained (no external CSS/JS)
- Plugin manifest format (plugin.json) needs clear schema

## Acceptance Criteria

- [x] `md-evals suite run --config suite.yaml` runs suites with threshold checks
- [x] `md-evals export result.json --format html` generates self-contained HTML
- [x] `md-evals eval-plugin ./path/` discovers and evaluates plugin skills
- [x] All features have unit tests with >90% coverage
- [x] Exit codes follow conventions (0=success, 1=config, 2=threshold/validation)
