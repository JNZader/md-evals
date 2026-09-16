"""Replay a pinned real capture offline; no provider execution or model-quality claim."""

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import pytest
from jsonschema import Draft202012Validator

from tests.repoforge_capture_support import CaptureError, adapt_capture, capture_schema

ROOT = Path(__file__).parents[2]
BASE = ROOT / "tests/fixtures/context_broker"
FIXTURE = BASE / "repoforge_capture"
TRUSTED_MANIFEST_SHA256 = "45bf178c883014e1482661f210828622e221ad8f301e09b506a5af6d152842cf"
REVISION = "sha256:8310e290c2cec537b01450d720d4377fed2170c86e2888cb872abcd6cc31f519"
GRAPH_SHA256 = "04484dc8fb1f36af77c3952fa00a1808f7e48dfacade1835075dbbc4cec18270"
COMMIT = "40255f5f952795f98c207f6bf2e3006e0354f4ae"
QUOTES = ['import { VALUE } from "./base";', 'import { current } from "./consumer";']


@pytest.fixture
def captured():
    manifest = (FIXTURE / "provenance.json").read_bytes()
    sources = {
        path: (FIXTURE / path).read_bytes()
        for path in ("src/base.ts", "src/consumer.ts", "src/entry.js")
    }
    return (FIXTURE / "graph.json").read_bytes(), sources, manifest


def adapt(captured, **kwargs):
    return adapt_capture(*captured, expected_manifest_sha256=TRUSTED_MANIFEST_SHA256, **kwargs)


def independent_digest(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()


def reenroll(graph, sources, manifest):
    """Explicit NEW trust for testing inner validation, never a production fallback."""
    original = (FIXTURE / "graph.json").read_bytes()
    raw = original if json.loads(original) == graph else json.dumps(graph).encode()
    manifest["capture"].update(graph_sha256=hashlib.sha256(raw).hexdigest(), graph_bytes=len(raw))
    manifest["corpus_files"] = [
        {"path": path, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        for path, data in sorted(sources.items())
    ]
    encoded_corpus = json.dumps(
        manifest["corpus_files"], sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode()
    manifest["corpus_identity_sha256"] = hashlib.sha256(encoded_corpus).hexdigest()
    encoded = json.dumps(manifest).encode()
    return adapt_capture(
        raw, sources, encoded, expected_manifest_sha256=hashlib.sha256(encoded).hexdigest()
    )


def test_captured_import_records_exist(captured):
    original = deepcopy(captured)
    with (
        patch("socket.socket.connect", side_effect=AssertionError("network forbidden")),
        patch("subprocess.Popen", side_effect=AssertionError("process forbidden")),
    ):
        pack = adapt(captured)
    assert captured == original
    assert [item["quote"] for item in pack["evidence"]] == QUOTES
    assert pack["revision"] == REVISION and pack["repository"] == "fixture://repoforge-file-graph"
    assert pack["freshness"] == pack["git_state"] == "unknown"
    assert pack["producer"] == {
        "name": "md-evals-capture-adapter",
        "version": "1",
        "instance": "sha256:" + TRUSTED_MANIFEST_SHA256,
    }
    assert pack["providers"][0]["instance"] == f"repoforge:{COMMIT}:sha256:{GRAPH_SHA256}"
    detail = json.loads(pack["providers"][0]["detail"])
    assert detail["producer"] == {"name": "repoforge-ai", "version": "0.6.0", "commit": COMMIT}
    assert detail["capture"]["proof_sha256"] == (
        "944aae3f5a91e925de329d5db1d6ce0d8d5d6b69da52ce8079bf1c8ed9a811d1"
    )
    assert [len(quote.encode("utf-8")) for quote in QUOTES] == [31, 37]
    assert pack["conflicts"] == [] and pack["budget"]["estimated_tokens"] == 18
    expected_sources = []
    for record, source, target, quote in zip(
        pack["evidence"],
        ("src/consumer.ts", "src/entry.js"),
        ("src/base.ts", "src/consumer.ts"),
        QUOTES,
    ):
        expected = {
            "kind": "structure",
            "repository": "fixture://repoforge-file-graph",
            "revision": REVISION,
            "producer_instance": f"repoforge:{COMMIT}:sha256:{GRAPH_SHA256}",
            "source_id": f"imports:{source}:{target}",
            "path": source,
            "line": 1,
        }
        expected_sources.append(expected)
        assert record == dict(
            expected,
            id=independent_digest(expected),
            quote=quote,
            claim=f"imports:{source}:{target}",
            value="present",
            freshness="unknown",
            git_state="unknown",
        )
    assert pack["trace"] == {
        "retrieval_digest": independent_digest(
            {"providers": pack["providers"], "records": pack["evidence"]}
        ),
        "provenance_digest": independent_digest(
            {
                "repository": pack["repository"],
                "revision": REVISION,
                "producer": pack["producer"],
                "sources": expected_sources,
            }
        ),
    }
    schema = capture_schema(json.loads((BASE / "context-pack.schema.json").read_bytes()))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(pack)


def test_file_dep_profile_lists_unsupported_symbols_calls_and_cross_service(captured):
    pack = adapt(captured)
    ok_structure = [
        provider
        for provider in pack["providers"]
        if provider["kind"] == "structure" and provider["status"] == "ok"
    ]
    unsupported = [
        provider for provider in pack["providers"] if provider["status"] == "unsupported"
    ]
    assert len(ok_structure) == 1
    assert [item["claim"] for item in pack["evidence"]] == [
        "imports:src/consumer.ts:src/base.ts",
        "imports:src/entry.js:src/consumer.ts",
    ]
    assert len(unsupported) == 3
    listed = []
    for capability in ("symbols", "calls", "cross_service"):
        matches = [provider for provider in unsupported if capability in provider["detail"]]
        assert len(matches) == 1
        assert matches[0]["status"] == "unsupported"
        assert matches[0]["detail"]
        assert "extracted" not in matches[0]["detail"] or "not extracted" in matches[0]["detail"]
        listed.append(capability)
    assert listed == ["symbols", "calls", "cross_service"]
    schema = capture_schema(json.loads((BASE / "context-pack.schema.json").read_bytes()))
    Draft202012Validator(schema).validate(pack)


def test_schema_changes_only_version_two_revision_patterns_and_id():
    base = json.loads((BASE / "context-pack.schema.json").read_bytes())
    original = deepcopy(base)
    expected = deepcopy(base)
    expected["$id"] = "urn:md-evals:context-pack:capture:v1"
    expected["properties"]["schema_version"]["const"] = "ContextPack.capture.v1"
    expected["properties"]["revision"]["pattern"] = "^sha256:[0-9a-f]{64}$"
    expected["$defs"]["evidence"]["properties"]["revision"]["pattern"] = "^sha256:[0-9a-f]{64}$"
    result = capture_schema(base)
    assert result == expected and base == original
    result["$defs"]["evidence"]["required"].clear()
    assert base == original


@pytest.mark.parametrize("which", ["graph", "source", "manifest", "replacement_manifest"])
def test_untrusted_mutations_are_rejected(captured, which):
    graph, sources, raw_manifest = captured
    manifest = json.loads(raw_manifest)
    if which in ("graph", "replacement_manifest"):
        graph += b" "
    if which == "source":
        sources["src/base.ts"] += b" "
    if which == "manifest":
        manifest["producer"]["version"] = "invented"
    if which == "replacement_manifest":
        manifest["capture"].update(
            graph_sha256=hashlib.sha256(graph).hexdigest(), graph_bytes=len(graph)
        )
    if which in ("manifest", "replacement_manifest"):
        raw_manifest = json.dumps(manifest).encode()
    with pytest.raises(CaptureError):
        adapt((graph, sources, raw_manifest))


def test_anchor_is_required(captured):
    with pytest.raises(TypeError, match="expected_manifest_sha256"):
        adapt_capture(*captured)


@pytest.mark.parametrize(
    "fault",
    [
        "missing_citation",
        "zero_line",
        "far_line",
        "wrong_quote",
        "target_line",
        "target_quote",
        "target_export",
        "missing_target",
        "duplicate_edge",
        "missing_node",
        "duplicate_node",
        "node_alias",
        "source_alias",
        "unknown_proof",
    ],
)
def test_curated_grounding_rejects_bad_inputs_even_with_explicit_new_trust(captured, fault):
    raw, sources, encoded = captured
    graph, manifest = json.loads(raw), json.loads(encoded)
    item = manifest["citations"][0]
    if fault == "missing_citation":
        manifest["citations"].pop()
    elif fault in ("zero_line", "far_line"):
        item["line"] = 0 if fault == "zero_line" else 99
    elif fault == "wrong_quote":
        item.update(line=2, quote="export const current = VALUE;")
    elif fault == "target_line":
        item["target_line"] = 99
    elif fault == "target_quote":
        item["target_quote"] = "export const VALUE = 999;"
    elif fault == "target_export":
        graph["nodes"][0]["exports"] = []
    elif fault == "missing_target":
        graph["edges"][0]["target"] = "src/missing.ts"
    elif fault == "duplicate_edge":
        graph["edges"].append(graph["edges"][0])
    elif fault == "missing_node":
        graph["nodes"].pop()
    elif fault == "duplicate_node":
        graph["nodes"].append(graph["nodes"][0])
    elif fault == "node_alias":
        graph["nodes"][0].update(id="src/./base.ts", file_path="src/./base.ts")
    elif fault == "source_alias":
        sources["src/./base.ts"] = sources.pop("src/base.ts")
    elif fault == "unknown_proof":
        manifest["capture"]["recorded_status"] = "unknown"
    with pytest.raises(CaptureError):
        reenroll(graph, sources, manifest)


@pytest.mark.parametrize(
    "limit,count,cost", [(0, 0, 0), (7, 0, 0), (8, 1, 8), (17, 1, 8), (18, 2, 18), (19, 2, 18)]
)
def test_exact_prefix_and_drop_accounting(captured, limit, count, cost):
    full, pack = adapt(captured), adapt(captured, limit=limit)
    assert pack["evidence"] == full["evidence"][:count]
    assert pack["budget"] == {
        "limit": limit,
        "estimated_tokens": cost,
        "measurement": "estimate",
        "algorithm": "utf8_quote_bytes_div4_ceil_v0",
        "scope": "evidence_quotes",
        "truncated": count < 2,
        "dropped_ids": [r["id"] for r in full["evidence"][count:]],
    }
    assert pack["trace"] == full["trace"]  # Traces bind candidates, not the selected prefix.


@pytest.mark.parametrize("limit", [-1, True, 1.5, "8", None])
def test_invalid_budget(captured, limit):
    with pytest.raises(CaptureError, match="budget"):
        adapt(captured, limit=limit)


@pytest.mark.parametrize("change", ["repository", "producer", "source"])
def test_ids_and_traces_bind_the_actual_revision_and_provider(captured, change):
    before = adapt(captured)
    raw, sources, encoded = captured
    graph, manifest = json.loads(raw), json.loads(encoded)
    if change == "repository":
        manifest["repository"] = "fixture://other-corpus"
    elif change == "producer":
        manifest["producer"]["commit"] = "a" * 40
    else:
        sources["src/base.ts"] += b"// another captured snapshot\n"
    after = reenroll(graph, sources, manifest)
    assert [r["id"] for r in before["evidence"]] != [r["id"] for r in after["evidence"]]
    assert all(before["trace"][key] != after["trace"][key] for key in before["trace"])
    if change != "producer":
        assert before["providers"][0]["instance"] == after["providers"][0]["instance"]
    if change == "source":
        assert (
            before["repository"] == after["repository"] and before["revision"] != after["revision"]
        )


@pytest.mark.parametrize(
    "path,expected",
    [
        (
            "tests/fixtures/context_broker/context-pack.schema.json",
            "78a270a28e32ae1065c98d533ff0af2039210998a589c9e33ae223b1a46136e0",
        ),
        (
            "tests/fixtures/context_broker/cases.json",
            "899897b325d4cb47acc2419c52cb28e344d090c8c2e99f5d597bd8f32510e334",
        ),
        (
            "tests/fixtures/context_broker/eval.yaml",
            "09fab346a4ea91e0efe8a43c9aed331f7955e29caf97d95932c103d2a24179eb",
        ),
        (
            "tests/integration/test_context_broker_offline.py",
            "c38cf32c0d112d1babcf5b6e41d3ff3f22b5e43894d2bf212eb8a1c3e4d687dd",
        ),
    ],
)
def test_original_approved_files_are_byte_identical(path, expected):
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected
