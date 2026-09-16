"""Offline captured union contracts; no provider execution or quality inference."""

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import pytest
from jsonschema import Draft202012Validator, ValidationError

from tests.context_broker_capture_union_support import compose_capture, union_schema
from tests.repoforge_capture_support import CaptureError

BASE = Path(__file__).parents[1] / "fixtures/context_broker"
GRAPH = BASE / "repoforge_capture"
MEMORY = BASE / "engram_capture"
GRAPH_ANCHOR = "45bf178c883014e1482661f210828622e221ad8f301e09b506a5af6d152842cf"
MEMORY_ANCHOR = "a27107b7e2f72c41657c4d394455f7b93d05b7c9761259ea89b186ef2a6611a2"
REVISION = "sha256:8310e290c2cec537b01450d720d4377fed2170c86e2888cb872abcd6cc31f519"
MEMORY_REVISION = "sha256:58083296eb0e3cd421cfaf51a208b303a8e09c5bda7df51113aa3279116945fa"
NAMESPACE = "capture://engram/isolated-synthetic-GU44T1XB"
GRAPH_INSTANCE = (
    "repoforge:40255f5f952795f98c207f6bf2e3006e0354f4ae:"
    "sha256:04484dc8fb1f36af77c3952fa00a1808f7e48dfacade1835075dbbc4cec18270"
)
TARGET = {
    "repository": "fixture://repoforge-file-graph",
    "revision": REVISION,
    "edge": {"source": "src/consumer.ts", "target": "src/base.ts"},
}
QUOTES = [
    'import { VALUE } from "./base";',
    'import { current } from "./consumer";',
    "**What**: Keep VALUE as a named export from src/base.ts for src/consumer.ts.",
]
IDENTITY_KEYS = ("kind", "repository", "revision", "producer_instance", "source_id", "path", "line")


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def hashed(value):
    return hashlib.sha256(encoded(value)).hexdigest()


@pytest.fixture
def captured():
    graph = (
        (GRAPH / "graph.json").read_bytes(),
        {
            name: (GRAPH / name).read_bytes()
            for name in ("src/base.ts", "src/consumer.ts", "src/entry.js")
        },
        (GRAPH / "provenance.json").read_bytes(),
    )
    files = {
        name: (MEMORY / name).read_bytes()
        for name in (
            "save-response.json",
            "search-response.json",
            "get-response.json",
            "observation-rendering.txt",
        )
    }
    return graph, files, (MEMORY / "provenance.json").read_bytes()


def compose(captured, **overrides):
    options = dict(
        target=deepcopy(TARGET),
        mode="combined",
        expected_graph_manifest_sha256=GRAPH_ANCHOR,
        expected_memory_manifest_sha256=MEMORY_ANCHOR,
    )
    options.update(overrides)
    return compose_capture(*captured, **options)


def expected_records(manifest):
    """Independent literal identities/claims; never call adapter identity helpers."""
    instance = "engram:" + hashed(
        {"namespace": NAMESPACE, "producer": manifest["producer"], "revision": MEMORY_REVISION}
    )
    records = []
    for index, (source, target) in enumerate(
        (("src/consumer.ts", "src/base.ts"), ("src/entry.js", "src/consumer.ts"))
    ):
        claim = f"imports:{source}:{target}"
        identity = dict(
            kind="structure",
            repository=TARGET["repository"],
            revision=REVISION,
            producer_instance=GRAPH_INSTANCE,
            source_id=claim,
            path=source,
            line=1,
        )
        records.append(
            dict(
                identity,
                id=hashed(identity),
                quote=QUOTES[index],
                claim=claim,
                value="present",
                freshness="unknown",
                git_state="unknown",
            )
        )
    identity = dict(
        kind="memory",
        repository=NAMESPACE,
        revision=MEMORY_REVISION,
        producer_instance=instance,
        source_id="observation:1:obs-41042f46a97da659",
        path="observation-rendering.txt",
        line=2,
    )
    records.append(
        dict(
            identity,
            id=hashed(identity),
            quote=QUOTES[2],
            claim="policy:named-export:src/base.ts:VALUE:src/consumer.ts",
            value="keep",
            freshness="unknown",
            git_state="unknown",
        )
    )
    return records


@pytest.mark.parametrize(
    "mode,indices", [("structure-only", [0, 1]), ("memory-only", [2]), ("combined", [0, 1, 2])]
)
def test_exact_records_providers_and_full_traces(captured, mode, indices):
    before = deepcopy(captured)
    # Guard the pure replay boundary, after file loading and before composition.
    with (
        patch("socket.socket.connect", side_effect=AssertionError("network forbidden")),
        patch("socket.create_connection", side_effect=AssertionError("network forbidden")),
        patch("subprocess.Popen", side_effect=AssertionError("process forbidden")),
        patch("os.system", side_effect=AssertionError("process forbidden")),
    ):
        pack = compose(captured, mode=mode)
        assert pack == compose(captured, mode=mode)
    assert captured == before
    manifest = json.loads(captured[2])
    expected = [expected_records(manifest)[index] for index in indices]
    assert pack["evidence"] == expected
    assert pack["repository"] == TARGET["repository"] and pack["revision"] == REVISION
    assert pack["freshness"] == pack["git_state"] == "unknown"
    assert pack["conflicts"] == []  # Desired policy is not the observed-import claim.
    providers, anchors = [], {}
    if mode != "memory-only":
        graph_manifest = json.loads(captured[0][2])
        detail = dict(
            producer=graph_manifest["producer"],
            capture=graph_manifest["capture"],
            manifest_sha256=GRAPH_ANCHOR,
            scope="curated static imports; proof reference only",
        )
        providers.append(
            dict(
                kind="structure",
                instance=GRAPH_INSTANCE,
                status="ok",
                detail=encoded(detail).decode(),
            )
        )
        for capability in ("symbols", "calls", "cross_service"):
            providers.append(
                dict(
                    kind="structure",
                    instance=f"{GRAPH_INSTANCE}:unsupported:{capability}",
                    status="unsupported",
                    detail=(
                        f"{capability} unsupported: file-dep imports only; not extracted"
                    ),
                )
            )
        anchors["structure"] = GRAPH_ANCHOR
    if mode != "structure-only":
        providers.append(
            dict(
                kind="memory",
                instance=expected[-1]["producer_instance"],
                status="ok",
                detail=encoded(manifest).decode(),
            )
        )
        anchors["memory"] = MEMORY_ANCHOR
    producer = dict(
        name="md-evals-capture-union",
        version="1",
        instance="sha256:" + hashed(dict(target=TARGET, anchors=anchors)),
    )
    assert pack["providers"] == providers and pack["producer"] == producer
    assert pack["trace"] == {
        "retrieval_digest": hashed(dict(providers=providers, records=expected)),
        "provenance_digest": hashed(
            dict(
                repository=TARGET["repository"],
                revision=REVISION,
                producer=producer,
                sources=[{key: r[key] for key in IDENTITY_KEYS} for r in expected],
            )
        ),
    }
    assert manifest["observation"]["project"] != expected_records(manifest)[2]["repository"]


@pytest.mark.parametrize("mode", ["structure-only", "memory-only"])
def test_unselected_payload_and_anchor_are_not_inspected(captured, mode):
    graph, files, manifest = captured
    if mode == "structure-only":
        altered = (graph, object(), object())
        overrides = {"expected_memory_manifest_sha256": object()}
    else:
        altered = (object(), files, manifest)
        overrides = {"expected_graph_manifest_sha256": object()}
    assert compose(altered, mode=mode, **overrides) == compose(captured, mode=mode)


@pytest.mark.parametrize(
    "mode,limit,kept,estimate",
    [
        ("combined", 0, [], 0),
        ("combined", 7, [], 0),
        ("combined", 8, [0], 8),
        ("combined", 17, [0], 8),
        ("combined", 18, [0, 1], 18),
        ("combined", 36, [0, 1], 18),
        ("combined", 37, [0, 1, 2], 37),
        ("memory-only", 18, [], 0),
        ("memory-only", 19, [2], 19),
    ],
)
def test_single_prefix_quote_budget_preserves_full_candidate_traces(
    captured, mode, limit, kept, estimate
):
    records = expected_records(json.loads(captured[2]))
    candidates = [2] if mode == "memory-only" else [0, 1, 2]
    pack = compose(captured, mode=mode, limit=limit)
    assert pack["evidence"] == [records[index] for index in kept]
    dropped = [records[index]["id"] for index in candidates if index not in kept]
    assert pack["budget"] == dict(
        limit=limit,
        estimated_tokens=estimate,
        measurement="estimate",
        algorithm="utf8_quote_bytes_div4_ceil_v0",
        scope="evidence_quotes",
        truncated=bool(dropped),
        dropped_ids=dropped,
    )
    assert pack["trace"] == compose(captured, mode=mode)["trace"]
    Draft202012Validator(
        union_schema(json.loads((BASE / "context-pack.schema.json").read_bytes()))
    ).validate(pack)


def test_schema_is_an_independent_strict_derivation(captured):
    base = json.loads((BASE / "context-pack.schema.json").read_bytes())
    original = deepcopy(base)
    expected = deepcopy(base)
    expected["$id"] = "urn:md-evals:context-pack:capture:union:v1"
    expected["properties"]["schema_version"]["const"] = "ContextPack.capture.union.v1"
    expected["properties"]["revision"]["pattern"] = "^sha256:[0-9a-f]{64}$"
    expected["$defs"]["evidence"]["properties"]["revision"]["pattern"] = "^sha256:[0-9a-f]{64}$"
    schema = union_schema(base)
    assert schema == expected and base == original
    Draft202012Validator.check_schema(schema)
    for mode in ("structure-only", "memory-only", "combined"):
        Draft202012Validator(schema).validate(compose(captured, mode=mode))
    pack = compose(captured)
    pack["extra"] = True
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(pack)
    schema["$defs"]["evidence"]["required"].clear()
    assert base == original


@pytest.mark.parametrize(
    "options",
    [
        {"mode": "none"},
        {"mode": None},
        {"limit": -1},
        {"limit": True},
        {"limit": 1.0},
        {"target": None},
        {"target": dict(TARGET, revision="a" * 40)},
        {"target": dict(TARGET, repository="")},
        {"target": dict(TARGET, edge={"source": "../escape", "target": "src/base.ts"})},
    ],
)
def test_invalid_caller_input_is_rejected(captured, options):
    with pytest.raises(CaptureError):
        compose(captured, **options)


@pytest.mark.parametrize("source", ["graph", "memory"])
@pytest.mark.parametrize("anchor", [None, "", "0" * 64])
def test_selected_source_requires_original_external_anchor(captured, source, anchor):
    with pytest.raises(CaptureError, match="anchor"):
        compose(captured, **{f"expected_{source}_manifest_sha256": anchor})


@pytest.mark.parametrize(
    "name",
    [
        "save-response.json",
        "search-response.json",
        "get-response.json",
        "observation-rendering.txt",
        "provenance.json",
        "graph.json",
        "graph-manifest",
    ],
)
def test_tamper_fails_under_unchanged_pins(captured, name):
    graph, files, manifest = deepcopy(captured)
    if name == "provenance.json":
        manifest += b" "
    elif name == "graph.json":
        graph = (graph[0] + b" ", graph[1], graph[2])
    elif name == "graph-manifest":
        graph = (graph[0], graph[1], graph[2] + b" ")
    else:
        files[name] += b" "
    with pytest.raises(CaptureError, match="anchor|hash"):
        compose((graph, files, manifest))


def reenrolled_memory(captured, manifest=None, files=None):
    """Explicit in-memory NEW trust only to reach inner checks; original pins stay fixed."""
    graph, original_files, raw_manifest = captured
    files = deepcopy(original_files if files is None else files)
    manifest = deepcopy(json.loads(raw_manifest) if manifest is None else manifest)
    manifest["files"] = {
        name: {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
        for name, raw in files.items()
    }
    raw = encoded(manifest)
    return (graph, files, raw), hashlib.sha256(raw).hexdigest()


def set_field(value, path, replacement):
    for key in path[:-1]:
        value = value[key]
    value[path[-1]] = replacement


@pytest.mark.parametrize(
    "path,value,reason",
    [
        (("profile",), "other", "profile"),
        (("target", "repository"), "fixture://other", "applicability"),
        (("producer", "binary_sha256"), "bad", "producer"),
        (("producer", "mcp", "version"), "other", "protocol"),
        (("producer", "build", "vcs_modified"), "true", "build"),
        (("source_namespace",), TARGET["repository"], "namespace"),
        (("observation", "id"), True, "observation ID"),
        (("observation", "sync_id"), "obs-bad", "sync ID"),
        (("observation", "state"), "needs_review", "lifecycle"),
        (("observation", "review_after"), None, "lifecycle"),
        (("observation", "scope"), "personal", "scope"),
        (("observation", "title"), "different", "search identity"),
        (("citation", "line"), True, "citation"),
        (("citation", "path"), "../escape", "citation"),
        (("citation", "quote"), "unrelated", "citation"),
        (("claim",), "imports:src/consumer.ts:src/base.ts", "claim"),
        (("value",), "present", "claim"),
    ],
)
def test_reenrolled_manifest_inner_validation(captured, path, value, reason):
    manifest = json.loads(captured[2])
    set_field(manifest, path, value)
    altered, anchor = reenrolled_memory(captured, manifest=manifest)
    with pytest.raises(CaptureError, match=reason):
        compose(altered, expected_memory_manifest_sha256=anchor)


@pytest.mark.parametrize(
    "name,layer,path,value,reason",
    [
        ("save-response.json", "outer", ("jsonrpc",), "1.0", "RPC error"),
        ("search-response.json", "outer", ("id",), True, "RPC identity"),
        ("get-response.json", "outer", ("id",), 6, "RPC identity"),
        ("get-response.json", "outer", ("error",), {}, "RPC error"),
        ("save-response.json", "outer", ("result", "isError"), True, "RPC error"),
        ("search-response.json", "outer", ("result", "content"), [], "RPC content"),
        ("get-response.json", "outer", ("result", "content", 0, "type"), "image", "RPC content"),
        ("get-response.json", "outer", ("result", "content", 0, "text"), "[]", "JSON object"),
        ("save-response.json", "payload", ("project",), "other", "project identity"),
        ("save-response.json", "payload", ("judgment_required",), True, "save judgment"),
        ("save-response.json", "payload", ("id",), 2, "observation identity"),
        (
            "save-response.json",
            "payload",
            ("sync_id",),
            "obs-0000000000000000",
            "observation identity",
        ),
        ("search-response.json", "payload", ("results",), [], "search inventory"),
        ("search-response.json", "payload", ("results", 0, "state"), "needs_review", "lifecycle"),
        (
            "search-response.json",
            "payload",
            ("results", 0, "review_after"),
            "other",
            "observation identity",
        ),
        ("search-response.json", "payload", ("results", 0, "project"), "other", "search identity"),
        ("get-response.json", "payload", ("result",), "other", "rendering bytes"),
    ],
)
def test_reenrolled_rpc_inner_validation(captured, name, layer, path, value, reason):
    files = deepcopy(captured[1])
    response = json.loads(files[name])
    payload = json.loads(response["result"]["content"][0]["text"])
    set_field(response if layer == "outer" else payload, path, value)
    if layer == "payload":
        response["result"]["content"][0]["text"] = encoded(payload).decode()
    files[name] = encoded(response)
    altered, anchor = reenrolled_memory(captured, files=files)
    with pytest.raises(CaptureError, match=reason):
        compose(altered, expected_memory_manifest_sha256=anchor)


@pytest.mark.parametrize(
    "replacement,reason",
    [
        (("#1 [decision]", "#2 [decision]"), "rendered identity"),
        (("Project: context-broker-synthetic", "Project: other"), "rendered identity"),
        (("Keep VALUE as a named export", "Remove VALUE as a named export"), "policy grounding"),
    ],
)
def test_reenrolled_consistent_rendering_still_requires_identity_and_policy(
    captured, replacement, reason
):
    files = deepcopy(captured[1])
    rendering = files["observation-rendering.txt"].decode().replace(*replacement)
    files["observation-rendering.txt"] = rendering.encode()
    response = json.loads(files["get-response.json"])
    payload = json.loads(response["result"]["content"][0]["text"])
    payload["result"] = rendering
    response["result"]["content"][0]["text"] = encoded(payload).decode()
    files["get-response.json"] = encoded(response)
    manifest = json.loads(captured[2])
    manifest["citation"]["quote"] = rendering.splitlines()[1]
    altered, anchor = reenrolled_memory(captured, manifest=manifest, files=files)
    with pytest.raises(CaptureError, match=reason):
        compose(altered, expected_memory_manifest_sha256=anchor)


@pytest.mark.parametrize("raw", [b"{", b"[]", b"\xff", b'{"jsonrpc":"2.0","id":7}'])
def test_reenrolled_malformed_rpc_is_normalized_to_capture_error(captured, raw):
    files = dict(captured[1], **{"get-response.json": raw})
    altered, anchor = reenrolled_memory(captured, files=files)
    with pytest.raises(CaptureError):
        compose(altered, expected_memory_manifest_sha256=anchor)


def test_get_revision_binds_raw_bytes_not_decoded_payload(captured):
    files = dict(captured[1], **{"get-response.json": captured[1]["get-response.json"] + b"\n"})
    altered, anchor = reenrolled_memory(captured, files=files)
    original = compose(captured)["evidence"][2]
    changed = compose(altered, expected_memory_manifest_sha256=anchor)["evidence"][2]
    assert changed["revision"] == "sha256:" + hashlib.sha256(files["get-response.json"]).hexdigest()
    assert changed["revision"] != MEMORY_REVISION
    assert (
        changed["id"] != original["id"]
        and changed["producer_instance"] != original["producer_instance"]
    )
    assert changed["quote"] == original["quote"]


def test_inventory_and_graph_applicability_remain_required(captured):
    files = dict(captured[1], extra=b"not enrolled")
    altered, anchor = reenrolled_memory(captured, files=files)
    with pytest.raises(CaptureError, match="inventory"):
        compose(altered, expected_memory_manifest_sha256=anchor)
    missing_edge = dict(TARGET, edge={"source": "src/entry.js", "target": "src/base.ts"})
    with pytest.raises(CaptureError, match="graph applicability edge"):
        compose(captured, mode="structure-only", target=missing_edge)
    with pytest.raises(CaptureError, match="graph target"):
        compose(captured, mode="structure-only", target=dict(TARGET, revision="sha256:" + "0" * 64))
