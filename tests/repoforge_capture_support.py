"""Experimental replay of one curated three-file capture; no I/O or provider launches."""

import hashlib
import json
import re
from copy import deepcopy
from pathlib import PurePosixPath

PROFILE = "ContextPack.capture.v1"


class CaptureError(ValueError):
    """Capture integrity, grounding, or caller input is invalid."""


def require(condition, reason):
    if not condition:
        raise CaptureError(reason)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def identity(record):
    return {
        key: record[key]
        for key in (
            "kind",
            "repository",
            "revision",
            "producer_instance",
            "source_id",
            "path",
            "line",
        )
    }


def quote_estimate(records):
    return sum((len(item["quote"].encode("utf-8")) + 3) // 4 for item in records)


def capture_schema(base_schema):
    """Exactly three validation changes plus a distinct ID; v0 remains untouched."""
    schema = deepcopy(base_schema)
    schema["$id"] = "urn:md-evals:context-pack:capture:v1"
    schema["properties"]["schema_version"]["const"] = PROFILE
    schema["properties"]["revision"]["pattern"] = "^sha256:[0-9a-f]{64}$"
    schema["$defs"]["evidence"]["properties"]["revision"]["pattern"] = "^sha256:[0-9a-f]{64}$"
    return schema


def checked_path(value):
    require(isinstance(value, str) and value, "path")
    path = PurePosixPath(value)
    require(
        path.parts
        and not path.is_absolute()
        and path.as_posix() == value
        and ".." not in path.parts
        and "\\" not in value
        and ":" not in value,
        "path",
    )
    return path


def adapt_capture(graph_bytes, sources, manifest_bytes, *, expected_manifest_sha256, limit=4096):
    """The expected digest MUST come from caller trust, never the supplied manifest."""
    require(type(limit) is int and limit >= 0, "budget")
    require(
        isinstance(expected_manifest_sha256, str)
        and re.fullmatch(r"[0-9a-f]{64}", expected_manifest_sha256),
        "trust anchor",
    )
    require(type(manifest_bytes) is bytes, "manifest bytes")
    require(
        hashlib.sha256(manifest_bytes).hexdigest() == expected_manifest_sha256,
        "manifest trust anchor",
    )
    try:
        return _adapt(
            graph_bytes, sources, json.loads(manifest_bytes), expected_manifest_sha256, limit
        )
    except (KeyError, TypeError, UnicodeError, json.JSONDecodeError) as exc:
        raise CaptureError("malformed capture") from exc


def _adapt(graph_bytes, sources, manifest, anchor, limit):
    require(manifest["profile"] == "repoforge-static-import-capture.v1", "manifest profile")
    require(isinstance(manifest["repository"], str) and manifest["repository"], "repository")
    producer, capture = manifest["producer"], manifest["capture"]
    require(
        producer["name"] == "repoforge-ai"
        and isinstance(producer["version"], str)
        and producer["version"]
        and re.fullmatch(r"[0-9a-f]{40}", producer["commit"]),
        "producer",
    )
    checked_path(capture["proof_reference"])
    require(
        re.fullmatch(r"[0-9a-f]{64}", capture["proof_sha256"])
        and capture["recorded_status"] == "PASS"
        and type(capture["recorded_cli_exit_code"]) is int
        and capture["recorded_cli_exit_code"] == 0,
        "recorded proof",
    )
    require(
        type(graph_bytes) is bytes
        and len(graph_bytes) == capture["graph_bytes"]
        and hashlib.sha256(graph_bytes).hexdigest() == capture["graph_sha256"],
        "graph hash",
    )
    for path, content in sources.items():
        checked_path(path)
        require(type(content) is bytes, "source bytes")
    corpus = [
        {
            "path": path,
            "sha256": hashlib.sha256(sources[path]).hexdigest(),
            "bytes": len(sources[path]),
        }
        for path in sorted(sources)
    ]
    require(corpus == manifest["corpus_files"], "source manifest")
    # Original capture algorithm: sorted metadata list, ASCII JSON, no trailing newline.
    revision_hash = hashlib.sha256(
        json.dumps(corpus, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    require(revision_hash == manifest["corpus_identity_sha256"], "corpus identity")
    graph = json.loads(graph_bytes)
    require(set(graph) == {"nodes", "edges"}, "graph shape")
    require(type(graph["nodes"]) is list and type(graph["edges"]) is list, "graph shape")
    nodes = {}
    for node in graph["nodes"]:
        checked_path(node["id"])
        require(
            node["id"] == node["file_path"]
            and node["id"] not in nodes
            and node["type"] == "module"
            and type(node["exports"]) is list,
            "node",
        )
        nodes[node["id"]] = node
    require(set(nodes) == set(sources) and len(nodes) == 3, "node inventory")
    edges = []
    for edge in graph["edges"]:
        require(
            edge["source"] in nodes
            and edge["target"] in nodes
            and edge["source"] != edge["target"]
            and edge["type"] == "imports"
            and type(edge["weight"]) is int
            and edge["weight"] >= 1,
            "edge",
        )
        edges.append((edge["source"], edge["target"]))
    citations = manifest["citations"]
    pairs = [(item["source"], item["target"]) for item in citations]
    require(
        len(edges) == len(set(edges)) == len(pairs) == len(set(pairs)) == 2
        and set(pairs) == set(edges),
        "citation coverage",
    )

    def quote_at(path, line):
        require(path in sources and type(line) is int, "citation")
        lines = sources[path].decode("utf-8").splitlines()
        require(0 < line <= len(lines), "citation")
        return lines[line - 1]

    instance = f"repoforge:{producer['commit']}:sha256:{capture['graph_sha256']}"
    records = []
    for item in citations:
        source, target, symbol = item["source"], item["target"], item["symbol"]
        source_path, target_path = checked_path(source), checked_path(target)
        require(re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*", symbol), "citation symbol")
        expected_quote = f'import {{ {symbol} }} from "./{target_path.stem}";'
        require(
            source_path.parent == target_path.parent
            and item["quote"] == expected_quote
            and item["quote"] == quote_at(source, item["line"]),
            "citation",
        )
        target_quote = quote_at(target, item["target_line"])
        require(
            target_quote == item["target_quote"]
            and symbol in nodes[target]["exports"]
            and (
                target_quote.startswith(f"export const {symbol} ")
                or target_quote.startswith(f"export function {symbol}(")
            ),
            "target citation",
        )
        source_id = f"imports:{source}:{target}"
        record = {
            "kind": "structure",
            "repository": manifest["repository"],
            "revision": f"sha256:{revision_hash}",
            "producer_instance": instance,
            "source_id": source_id,
            "path": source,
            "line": item["line"],
            "quote": item["quote"],
            "claim": source_id,
            "value": "present",
            "freshness": "unknown",
            "git_state": "unknown",
        }
        records.append(dict(record, id=digest(identity(record))))
    providers = [
        {
            "kind": "structure",
            "instance": instance,
            "status": "ok",
            "detail": canonical(
                {
                    "producer": producer,
                    "capture": capture,
                    "manifest_sha256": anchor,
                    "scope": "curated static imports; proof reference only",
                }
            ),
        }
    ]
    adapter = {"name": "md-evals-capture-adapter", "version": "1", "instance": f"sha256:{anchor}"}
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
    return {
        "schema_version": PROFILE,
        "repository": manifest["repository"],
        "revision": f"sha256:{revision_hash}",
        "producer": adapter,
        "freshness": "unknown",
        "git_state": "unknown",
        "providers": providers,
        "evidence": kept,
        "conflicts": conflicts,
        "budget": {
            "limit": limit,
            "estimated_tokens": quote_estimate(kept),
            "measurement": "estimate",
            "algorithm": "utf8_quote_bytes_div4_ceil_v0",
            "scope": "evidence_quotes",
            "truncated": bool(dropped),
            "dropped_ids": [record["id"] for record in dropped],
        },
        "trace": {
            "retrieval_digest": digest({"providers": providers, "records": records}),
            "provenance_digest": digest(
                {
                    "repository": manifest["repository"],
                    "revision": f"sha256:{revision_hash}",
                    "producer": adapter,
                    "sources": [identity(record) for record in records],
                }
            ),
        },
    }
