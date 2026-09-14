# Captured Pipeline Smoke Test

`test_captured_context_runner.py` adds a deterministic offline integration path:
`compose_capture` prepares copied synthetic fixtures, the renderer supplies selected
evidence to the real `ExecutionEngine.run_single` path, and
`compare_captured_batch` applies the strict JSON grader afterwards.

The three fixture questions cover a named `VALUE` import in `src/consumer.ts`, the
synthetic captured named-export policy value `keep`, and an uncaptured current Git
commit that must abstain. The memory record has a content digest revision; it is not a
Git commit assertion.

The scripted recorder makes 24 adapter calls: three tasks × two repetitions × four
arms. It records one LLM error, one malformed JSON response, context-hidden citation
failures, and valid but wrong answer envelopes. The complete declared grid has six
cells per arm. `D_UNION` passes 3, structure and memory arms pass 4 each, and control
passes 2. Both fixed comparisons count 1 win, 2 losses, 2 mutual passes, 1 mutual
non-pass, and a delta of -1/6.

Run the focused module without project conftest or provider plugins:

```sh
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTEST_ADDOPTS= PYTEST_PLUGINS= /home/javier/programacion/md-evals/.venv/bin/python -B -m pytest --noconftest -p pytest_asyncio.plugin -p no:cacheprovider -o addopts= -o log_file=/dev/null --strict-markers -q tests/integration/test_captured_context_runner.py
```

This is an offline contract test. It makes no provider call and does not make a
benchmark, quality, cost, or live-runtime claim. Live benchmark work remains separate.

## Generate wire contract

The offline bridge decoder consumes the response `text` field, including an empty
string; it deliberately rejects missing, null, non-string, and content-only payloads.
`text` is the public shape emitted by
`buildGenerateResponseFromInternal` in
`/home/javier/programacion/mcp-llm-bridge/src/core/router-shaping.ts:164-199`
(SHA-256 `6a42d79e47ee3443609335ee01214a9cef3fc5323ec45771d10b836b83475b64`).
The HTTP execution service returns the router's generated result unchanged at
`/home/javier/programacion/mcp-llm-bridge/src/server/execution/generate-service.ts:56`
(SHA-256 `c92bb51ddf62ce09d251815f72835952b9c96002254b3a2a59589002ca262cc7`).

The fixtures simulate this source-backed shape only. They do not execute the
bridge producer, make a live call, or establish runtime compatibility.

`test_frozen_twelve_call_pilot_decodes_usage_and_renders_private_report` is a second,
offline seam: three fixture-derived tasks × one repetition × four arms make 12 serialized
POSTs through the real `BridgeCompletionAdapter`, its `httpx.AsyncClient`, the frozen plan,
the bridge decoder, and the private JSON report. Its factory supplies a fresh in-memory
`httpx.MockTransport` for every call; the assertions cover the public wire payload,
provider pin, selected context, transport closure, and cookie isolation. The companion
HTTP 429 scenario proves one normalized runner error row without treating the synthetic
protocol failure as quality evidence.

No real network, bridge server, provider, or model is contacted. These in-memory transport
proofs leave live-execution blockers unchanged; they do not add a CLI or start a live pilot.
Run the focused module command above to exercise both seams.
