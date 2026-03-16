# Proposal: md-evals

## Intent
Create `md-evals`, a lightweight, local, model-agnostic CLI tool built in Python using LiteLLM to evaluate the effectiveness of Markdown-based AI skills (`SKILL.md`). The tool aims to provide developers with a reliable way to test and iterate on their AI agent skills by comparing performance with and without the skill context, while enforcing best practices for skill design.

## Scope
- **CLI Application**: Build a Python-based command-line interface.
- **Model Agnostic**: Integrate LiteLLM to support multiple LLM providers (OpenAI, Anthropic, Gemini, local models, etc.).
- **A/B Testing Framework**: Evaluate prompts in "Control" (without skill) vs. "Skill" (with `SKILL.md` context) scenarios.
- **Hybrid Evaluation Engine**: 
  - Regex/deterministic assertions for precise checks.
  - LLM-as-a-judge for qualitative assessments.
- **Skill Health Check (Linter)**: Automatically validate `SKILL.md` files. Crucially, the tool will warn the user or fail the evaluation if the skill file exceeds 400 lines, enforcing concise "Encoded Preferences".

## Approach
- **Language/Framework**: Python with Click or Typer for the CLI interface.
- **LLM Integration**: Use `litellm` library for standardizing API calls across different providers.
- **Configuration**: Use YAML or JSON files to define evaluation suites (test cases, assertions, judge criteria).
- **Execution Flow**:
  1. Parse evaluation suite and load `SKILL.md`.
  2. Run the Health Check/Linter on `SKILL.md` (check < 400 lines constraint).
  3. Execute Control prompt (no skill).
  4. Execute Skill prompt (with skill injected).
  5. Run Hybrid Evaluation Engine (Regex + LLM Judge) on both outputs.
  6. Generate a comparison report (CLI output + optional JSON/Markdown report).

## Risks
- **LLM Judge Variability**: LLM-as-a-judge can be non-deterministic. *Mitigation*: Support multiple judge runs, use strong models for judging, and rely heavily on deterministic regex assertions where possible.
- **Provider API Changes/Errors**: Rate limits or API instability from LLM providers. *Mitigation*: Implement robust retry logic and error handling using LiteLLM's built-in features.
- **Performance**: Evaluating many cases sequentially might be slow. *Mitigation*: Implement concurrent evaluation execution using `asyncio`.

## Success Criteria
- The CLI can successfully execute an evaluation suite against at least two different LLM providers via LiteLLM.
- The A/B testing mechanism clearly outputs metrics comparing the Control vs. Skill performance.
- The Hybrid Evaluation Engine correctly processes both regex assertions and LLM judge criteria.
- **The Skill Health Check accurately identifies and flags `SKILL.md` files exceeding 400 lines**, providing clear feedback to the user.
- The tool can be easily installed and run locally with minimal dependencies.

## Extension: Comparative Context Window Analysis (Orchestrator vs Non-Orchestrator)

Esta extension agrega un segundo eje de evaluacion a md-evals: ademas de medir calidad de skills (A/B control vs skill), se analiza **costo y uso de context window** comparando dos modos de ejecucion:

- **`no-orq`** — flujo monolitico de una sola llamada LLM por caso.
- **`orq`** — flujo multi-etapa (planner → router → executor → synthesis).

El objetivo es responder: *¿cuanto contexto y tokens consume cada modo para lograr el mismo nivel de calidad?* Esto permite tomar decisiones informadas sobre cuando justifica el overhead de un orquestador.

La especificacion completa — incluyendo taxonomia de etapas, esquema de metricas, reglas de atribucion de tokens, diseno de reporte comparativo, plan de instrumentacion por fases, y mitigacion de sesgos — vive en el change dedicado:

> **📁 [`openspec/changes/split-cost-vs-context-metrics-orchestrator-comparison/`](openspec/changes/split-cost-vs-context-metrics-orchestrator-comparison/)**

Consultar la spec y el design de ese change para cualquier detalle de implementacion. Este proposal solo establece la intencion y el alcance general de la extension.
