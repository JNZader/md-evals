"""Test-owned union of two pinned captures; no I/O, provider calls, or quality claim."""

import hashlib
import json
import re

from tests.repoforge_capture_support import (
    CaptureError,
    adapt_capture,
    canonical,
    capture_schema,
    checked_path,
    digest,
    identity,
    quote_estimate,
    require,
)

PROFILE = "ContextPack.capture.union.v1"
RPC_FILES = {"save-response.json": 5, "search-response.json": 6, "get-response.json": 7}


def union_schema(base_schema):
    """Declare heterogeneous source origins/revisions without relaxing validation."""
    schema = capture_schema(base_schema)
    schema["$id"] = "urn:md-evals:context-pack:capture:union:v1"
    schema["properties"]["schema_version"]["const"] = PROFILE
    return schema


def raw_hash(raw):
    require(type(raw) is bytes, "capture bytes")
    return hashlib.sha256(raw).hexdigest()


def object_json(raw):
    result = json.loads(raw)
    require(type(result) is dict, "JSON object")
    return result


def rpc_payload(raw, rpc_id):
    response = object_json(raw)
    require(response.get("jsonrpc") == "2.0" and "error" not in response, "RPC error")
    require(type(response.get("id")) is int and response["id"] == rpc_id, "RPC identity")
    result = response["result"]
    require(type(result) is dict and result.get("isError", False) is False, "RPC error")
    content = result["content"]
    require(type(content) is list and len(content) == 1, "RPC content")
    require(content[0]["type"] == "text" and type(content[0]["text"]) is str, "RPC content")
    return object_json(content[0]["text"])


def memory_record(files, raw_manifest, anchor, target):
    require(type(anchor) is str and re.fullmatch(r"[0-9a-f]{64}", anchor), "memory anchor")
    require(raw_hash(raw_manifest) == anchor, "memory trust anchor")
    manifest = object_json(raw_manifest)
    require(manifest["profile"] == "engram-isolated-synthetic-capture.v1", "memory profile")
    require(manifest["target"] == target, "memory applicability")
    names = set(RPC_FILES) | {"observation-rendering.txt"}
    require(set(files) == set(manifest["files"]) == names, "memory inventory")
    for name in names:
        expected = manifest["files"][name]
        require(
            raw_hash(files[name]) == expected["sha256"]
            and type(expected["bytes"]) is int
            and len(files[name]) == expected["bytes"],
            "memory file hash",
        )
    producer, observation = manifest["producer"], manifest["observation"]
    require(re.fullmatch(r"[0-9a-f]{64}", producer["binary_sha256"]), "memory producer")
    require(
        producer["mcp"] == {"name": "engram", "version": "0.1.0"}
        and producer["protocol_version"] == "2024-11-05",
        "memory protocol",
    )
    build = producer["build"]
    require(
        type(build["version"]) is str
        and build["version"]
        and type(build["vcs_modified"]) is bool
        and re.fullmatch(r"[0-9a-f]{40}", build["vcs_revision"]),
        "memory build",
    )
    namespace = manifest["source_namespace"]
    require(
        type(namespace) is str
        and namespace.startswith("capture://engram/")
        and namespace != target["repository"],
        "memory namespace",
    )
    require(type(observation["id"]) is int and observation["id"] > 0, "observation ID")
    require(re.fullmatch(r"obs-[0-9a-f]{16}", observation["sync_id"]), "sync ID")
    require(observation.get("state") == "active", "lifecycle: captured active required")
    require(
        type(observation["review_after"]) is str
        and re.fullmatch(
            r"[0-9]{4}(-[0-9]{2}){2} [0-9]{2}(:[0-9]{2}){2}", observation["review_after"]
        ),
        "lifecycle: review metadata",
    )
    require(
        observation["project_path"] == ""
        and observation["project_source"] == "process_override"
        and observation["scope"] == "project"
        and observation["type"] == "decision",
        "observation scope",
    )
    payloads = {name: rpc_payload(files[name], rpc_id) for name, rpc_id in RPC_FILES.items()}
    for payload in payloads.values():
        require(
            all(
                payload[key] == observation[key]
                for key in ("project", "project_path", "project_source")
            ),
            "project identity",
        )
    saved, searched, fetched = (payloads[name] for name in RPC_FILES)
    require(saved["judgment_required"] is False, "save judgment")
    require(type(searched["results"]) is list and len(searched["results"]) == 1, "search inventory")
    found = searched["results"][0]
    for actual in (saved, found):
        require(actual.get("state") == "active", "lifecycle: captured active required")
        require(
            type(actual["id"]) is int
            and all(
                actual[key] == observation[key]
                for key in ("id", "sync_id", "state", "review_after")
            ),
            "observation identity",
        )
    require(
        all(found[key] == observation[key] for key in ("project", "scope", "type", "title")),
        "search identity",
    )
    rendering = fetched["result"]
    require(
        type(rendering) is str and rendering.encode("utf-8") == files["observation-rendering.txt"],
        "rendering bytes",
    )
    lines = rendering.splitlines()
    require(
        lines[0] == f"#{observation['id']} [decision] {observation['title']}"
        and lines.count(f"Project: {observation['project']}") == 1
        and lines.count("Scope: project") == 1,
        "rendered identity",
    )
    citation = manifest["citation"]
    require(
        citation["path"] == "observation-rendering.txt"
        and type(citation["line"]) is int
        and citation["line"] == 2
        and len(lines) >= 2
        and lines[1] == citation["quote"],
        "memory citation",
    )
    edge = target["edge"]
    require(
        citation["quote"]
        == f"**What**: Keep VALUE as a named export from {edge['target']} for {edge['source']}.",
        "policy grounding",
    )
    require(
        manifest["claim"] == f"policy:named-export:{edge['target']}:VALUE:{edge['source']}"
        and manifest["value"] == "keep",
        "policy claim",
    )
    revision = "sha256:" + raw_hash(files["get-response.json"])
    binding = dict(namespace=namespace, producer=producer, revision=revision)
    instance = "engram:" + digest(binding)
    record = dict(
        kind="memory",
        repository=namespace,
        revision=revision,
        producer_instance=instance,
        source_id=f"observation:{observation['id']}:{observation['sync_id']}",
        path=citation["path"],
        line=citation["line"],
        quote=citation["quote"],
        claim=manifest["claim"],
        value=manifest["value"],
        freshness="unknown",
        git_state="unknown",
    )
    record["id"] = digest(identity(record))
    provider = dict(kind="memory", instance=instance, status="ok", detail=canonical(manifest))
    return provider, record


def compose_capture(
    graph_capture,
    memory_files,
    memory_manifest,
    *,
    target,
    mode,
    expected_graph_manifest_sha256,
    expected_memory_manifest_sha256,
    limit=4096,
):
    """Trust anchors are mandatory; unselected capture payloads are never inspected."""
    require(type(mode) is str and mode in ("structure-only", "memory-only", "combined"), "mode")
    require(type(limit) is int and limit >= 0, "budget")
    try:
        return _compose(
            graph_capture,
            memory_files,
            memory_manifest,
            target,
            mode,
            expected_graph_manifest_sha256,
            expected_memory_manifest_sha256,
            limit,
        )
    except CaptureError:
        raise
    except (
        KeyError,
        IndexError,
        TypeError,
        AttributeError,
        UnicodeError,
        json.JSONDecodeError,
    ) as exc:
        raise CaptureError("malformed union capture") from exc


def _compose(graph, memory, manifest, target, mode, graph_anchor, memory_anchor, limit):
    require(set(target) == {"repository", "revision", "edge"}, "target")
    require(type(target["repository"]) is str and target["repository"], "target repository")
    require(re.fullmatch(r"sha256:[0-9a-f]{64}", target["revision"]), "target revision")
    require(set(target["edge"]) == {"source", "target"}, "target edge")
    for path in target["edge"].values():
        checked_path(path)
    providers, records, anchors = [], [], {}
    if mode != "memory-only":
        # Source-byte bound plus explicit nontruncation check avoids upstream budget loss.
        source_bound = sum(len(content) for content in graph[1].values())
        pack = adapt_capture(*graph, expected_manifest_sha256=graph_anchor, limit=source_bound)
        require(not pack["budget"]["truncated"], "upstream truncation")
        require(
            pack["repository"] == target["repository"] and pack["revision"] == target["revision"],
            "graph target",
        )
        edge = target["edge"]
        claim = f"imports:{edge['source']}:{edge['target']}"
        require(
            any(
                record["claim"] == claim and record["value"] == "present"
                for record in pack["evidence"]
            ),
            "graph applicability edge",
        )
        providers.extend(pack["providers"])
        records.extend(pack["evidence"])
        anchors["structure"] = graph_anchor
    if mode != "structure-only":
        provider, record = memory_record(memory, manifest, memory_anchor, target)
        providers.append(provider)
        records.append(record)
        anchors["memory"] = memory_anchor
    producer = dict(
        name="md-evals-capture-union",
        version="1",
        instance="sha256:" + digest(dict(target=target, anchors=anchors)),
    )
    kept = []
    for record in records:
        if quote_estimate(kept + [record]) > limit:
            break
        kept.append(record)
    dropped = records[len(kept) :]
    conflicts = [
        [left["id"], right["id"]]
        for index, left in enumerate(kept)
        for right in kept[index + 1 :]
        if left["claim"] == right["claim"] and left["value"] != right["value"]
    ]
    return dict(
        schema_version=PROFILE,
        repository=target["repository"],
        revision=target["revision"],
        producer=producer,
        freshness="unknown",
        git_state="unknown",
        providers=providers,
        evidence=kept,
        conflicts=conflicts,
        budget=dict(
            limit=limit,
            estimated_tokens=quote_estimate(kept),
            measurement="estimate",
            algorithm="utf8_quote_bytes_div4_ceil_v0",
            scope="evidence_quotes",
            truncated=bool(dropped),
            dropped_ids=[record["id"] for record in dropped],
        ),
        trace=dict(
            retrieval_digest=digest(dict(providers=providers, records=records)),
            provenance_digest=digest(
                dict(
                    repository=target["repository"],
                    revision=target["revision"],
                    producer=producer,
                    sources=[identity(record) for record in records],
                )
            ),
        ),
    )
