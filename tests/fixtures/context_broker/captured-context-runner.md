# Execute a captured four-arm batch without grading

`await run_captured_arms(config, adapter, packs_by_task)` returns raw
`CapturedRunRow` records using the existing `ExecutionEngine.run_single`.
Supply an explicit adapter exposing `model`, `provider`, `defaults: Defaults`,
and async `complete(prompt, system_prompt=None) -> LLMResponse`.
No provider is constructed and no skill file is written or read.

## Admission and ordering

Validate full ContextPack schema, integrity, provenance, and applicability before
calling. This executor adds whole-batch shape, arm, target/budget and binding
checks; it is not a replacement validator or retrieval broker.
Provide exactly one entry per nonempty unique configured task, containing
`CONTROL: None`, `B_STRUCTURE`, `C_MEMORY`, and `D_UNION` captured union packs.
All tasks and arms are snapshotted and rendered before the first completion.
Order is repetition (zero-based), configured task, then the four arms above.

Use one matching model/provider/defaults, positive repetitions, one worker, and
`fail_fast=False`. Skill paths, environment overrides, evaluators, models lists,
pipelines, and metric overrides are rejected. Set `output.save_results=False`;
other output and lint settings must remain default because this unit does not
persist results or lint skills. Configuration descriptions remain inert metadata.

Related packs must share target and budget contract, consistent provider bindings,
and identical contents for any reused selected-record ID. Memory revisions remain
independent. Empty/truncated selection may omit a kind, including both union kinds.
Only selected-evidence rendering reaches the adapter; manifests, traces, and
dropped-ID audit data do not. This does not sanitize instruction-like quotations.

## Rows and failures

Rows carry arm/task/repetition, actual engine-resolved prompt, rendered-context
SHA-256 (or `None`), ordered selected IDs, status, unchanged response, and timestamp.
`completed` means execution finished, **not** answer correctness. Engine-normalized
`LLMError` rows retain their synthetic response and the matrix continues; unexpected
exceptions and cancellation propagate immediately without runner retries.
Missing optional usage stays `None`; legacy `tokens=0` and synthetic error
`duration_ms=0` are not measured zero consumption or latency.
Adapter settings are checked at admission and before each completion.

## Offline verification

Run this module alone: `PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
PYTEST_ADDOPTS= PYTEST_PLUGINS= .venv/bin/python -B -m pytest --noconftest
-p pytest_asyncio.plugin -p no:cacheprovider -o addopts= -o log_file=/dev/null
--strict-markers -q tests/integration/test_captured_context_runner.py`.
Its pre-import outbound guard and recording adapter prove wiring, not provider
conformance or model quality. Run earlier suites separately: unexpected preloading
fails closed. Strict grading, comparisons, persistence, and paid runs remain later.
