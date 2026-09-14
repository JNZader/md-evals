"""Pure projection of a caller-validated captured union into selected evidence."""

import json
import re
from copy import deepcopy

_PROFILE = "ContextPack.capture.union.v1"
_PAIRED_PROFILE = "ContextPack.capture.paired.v1"
_FORMAT = "ContextPack.selected-evidence.v1"
_CONTAINERS = {
    "producer": dict,
    "providers": list,
    "evidence": list,
    "conflicts": list,
    "budget": dict,
    "trace": dict,
}
_ROOT_TEXT = {"schema_version", "repository", "revision", "freshness", "git_state"}
_EVIDENCE_TEXT = {
    "id",
    "kind",
    "repository",
    "revision",
    "producer_instance",
    "source_id",
    "path",
    "quote",
    "claim",
    "value",
    "freshness",
    "git_state",
}


class ContextRenderError(ValueError):
    """The supported envelope or selected evidence has an invalid shape."""


def _validate_paired_slot(pack: object, kind: str) -> dict[str, object]:
    _require(type(pack) is dict, f"{kind} slot must be a pack")
    _require(pack.get("schema_version") == _PROFILE, "paired slots require union packs")
    render_selected_evidence(pack)
    _require(
        all(record["kind"] == kind for record in pack["evidence"]),
        f"{kind} slot contains another evidence kind",
    )
    return deepcopy(pack)


def compose_paired_context(
    structure: dict[str, object], memory: dict[str, object]
) -> dict[str, object]:
    """Build an exact two-slot pair without projecting or combining either pack."""
    return {
        "schema_version": _PAIRED_PROFILE,
        "structure": _validate_paired_slot(structure, "structure"),
        "memory": _validate_paired_slot(memory, "memory"),
    }


def render_paired_context(pair: dict[str, object]) -> str:
    """Render a paired capture as compact canonical ASCII JSON."""
    _require(type(pair) is dict, "expected paired context object")
    _require(set(pair) == {"schema_version", "structure", "memory"}, "invalid paired envelope")
    _require(pair["schema_version"] == _PAIRED_PROFILE, "unsupported paired profile")
    normalized = compose_paired_context(pair["structure"], pair["memory"])
    try:
        return json.dumps(
            normalized,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError, RecursionError) as exc:
        raise ContextRenderError("paired context is not JSON-renderable") from exc


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise ContextRenderError(reason)


def _text_fields(value: dict[str, object], names: set[str]) -> None:
    for name in names:
        _require(type(value[name]) is str and bool(value[name]), f"invalid {name}")


def _origin_fields(value: dict[str, object]) -> None:
    _require(bool(re.fullmatch(r"sha256:[0-9a-f]{64}", value["revision"])), "invalid revision")
    _require(value["freshness"] in ("fresh", "stale", "unknown"), "invalid freshness")
    _require(value["git_state"] in ("clean", "dirty", "unknown"), "invalid git_state")


def render_selected_evidence(pack: dict[str, object] | None) -> str | None:
    """Render only selected records; callers own full schema and provenance checks."""
    if pack is None:
        return None
    _require(type(pack) is dict, "expected pack object")
    _require(set(pack) == _ROOT_TEXT | set(_CONTAINERS), "invalid envelope fields")
    _text_fields(pack, _ROOT_TEXT)
    _require(pack["schema_version"] == _PROFILE, "unsupported profile")
    _origin_fields(pack)
    for name, container in _CONTAINERS.items():
        _require(type(pack[name]) is container, f"invalid {name} container")

    records = pack["evidence"]
    for record in records:
        _require(type(record) is dict, "expected evidence object")
        _require(set(record) == _EVIDENCE_TEXT | {"line"}, "invalid evidence fields")
        _text_fields(record, _EVIDENCE_TEXT)
        _origin_fields(record)
        _require(bool(re.fullmatch(r"[0-9a-f]{64}", record["id"])), "invalid id")
        _require(record["kind"] in ("structure", "memory"), "invalid kind")
        _require(type(record["line"]) is int and record["line"] > 0, "invalid line")
    if not records:
        return None

    # Out-of-band metadata is deliberately never passed to the serializer.
    try:
        return json.dumps(
            {"format": _FORMAT, "evidence": records},
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ContextRenderError("selected evidence is not JSON-renderable") from exc
