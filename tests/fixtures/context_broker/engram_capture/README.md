# Replay captured graph and memory together

This test fixture combines two observed RepoForge static imports with one synthetic
decision captured through actual Engram MCP save/search/get responses. It proves
offline capture handling, not live provider behavior or improved RAG quality.

## Run the focused replay

From the repository root, use the existing development environment:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
.venv/bin/python -m pytest --noconftest -p pytest_asyncio.plugin \
-p no:cacheprovider -o addopts= -o log_file=/dev/null --strict-markers -q \
tests/integration/test_context_broker_capture_union.py
```

Do not remove `--noconftest`: the repository-wide conftest preloads providers.
No network, subprocess, model, live database, or provider recapture is needed.
JSON Schema validation uses the already installed `jsonschema` dependency;
it is currently transitive rather than an explicit development dependency.

## What each source means

| Source | Binding and limitation |
| --- | --- |
| RepoForge | The [graph capture](../repoforge_capture/README.md) covers two static imports in three files, not generalized calls or service architecture. Its revision hashes the captured corpus, not a Git commit. |
| Engram | Response files retain original captured bytes and RPC IDs 5/6/7. The memory revision hashes raw `get-response.json` bytes, including whitespace, not a normalized payload or the graph corpus. |
| Applicability | `provenance.json` explicitly associates this synthetic decision with the graph target and edge. This is curated test data, not discovered service ownership or real team policy. |
| Namespace | `capture://engram/isolated-synthetic-GU44T1XB` is assigned capture identity. It is neither a code repository nor the provider project `context-broker-synthetic`. |
| Freshness | Captured lifecycle `active` and recorded review metadata describe the historical response. Current freshness and Git state remain `unknown`; replay does not contact Engram. |

`provenance.json` records the producer binary/build, protocol, original response
slices, rendering hash, and historical proof reference. A replay validates the
enrolled response files; it does not reproduce the original capture or verify an
unavailable full transcript. Dirty producer build metadata remains explicit.

## Trust and output contract

The test owns independent, fixed graph and memory manifest SHA-256 pins.
Changed files or manifests fail under those original pins. Separately named
`reenrolled_*` tests create new trust **in memory only** to reach inner validation;
they are not a self-enrollment or recovery path and never modify fixture files.

`ContextPack.capture.union.v1` preserves the base schema and separate source
identities, providers, revisions, citations, and deterministic traces. Modes are
`structure-only`, `memory-only`, and `combined`; unselected inputs are not inspected.
The desired named-export policy and observed import are distinct claims, not a
fabricated contradiction.

Budgeting keeps a deterministic prefix: graph quotes cost 8 + 10, memory costs
19, and all three cost 37 under the quote-byte estimate. This is **not complete
context size, model tokens, cost telemetry, or a quality benchmark**. Dropped IDs
are explicit and traces still bind the complete selected-source candidate set.

## Scope and next step

The suite covers exact identities, schema isolation, budget boundaries, immutable
inputs, deterministic replay, original-anchor tamper, and separately re-enrolled
RPC, lifecycle, rendering, and applicability failures. No production broker or
provider adapter is installed. The next product step is an independently designed
four-arm evaluation; no CodeGraph parity or Corbell replacement is established.
