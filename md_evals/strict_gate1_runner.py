"""Offline Gate 1 artifact generation and strict execution admission.

The generator is deliberately non-authorizing.  The runner has a separate,
explicit authorization argument and accepts only an injected execution
boundary, so tests cannot accidentally reach a provider or gateway.
"""

from __future__ import annotations

import ctypes
import errno
import inspect
import hashlib
import argparse
import json
import os
import re
import secrets
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, Mapping

from md_evals.captured_answer_grader import validate_answer_envelope
from md_evals.captured_pilot_plan import CapturedPilotPlan, prepare_captured_pilot
from md_evals.strict_authorization_prompt import (
    StrictAuthorizationRequest,
    build_strict_authorization_request,
    parse_strict_authorization_request,
)
from md_evals.strict_run_assembly import (
    StrictRunAssembly,
    build_strict_run_assembly,
    parse_strict_run_assembly,
)
from md_evals.strict_run_packet import (
    StrictRunPacket,
    build_strict_run_packet,
    validate_strict_run_packet_binding,
)


class StrictGate1Error(ValueError):
    """A strict Gate 1 artifact or admission precondition is invalid."""


def _publish_new_directory(stage_name: str, output_name: str, parent_fd: int) -> None:
    """Atomically publish a previously absent directory without replacing a race winner."""
    try:
        renameat2 = ctypes.CDLL(None, use_errno=True).renameat2
    except (AttributeError, OSError) as exc:
        raise StrictGate1Error(
            "strict Gate 1 no-clobber directory publication is unsupported"
        ) from exc
    renameat2.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    ]
    renameat2.restype = ctypes.c_int
    result = renameat2(
        parent_fd,
        os.fsencode(stage_name),
        parent_fd,
        os.fsencode(output_name),
        1,  # RENAME_NOREPLACE
    )
    if result == 0:
        return
    error_number = ctypes.get_errno()
    if error_number == errno.EEXIST:
        raise StrictGate1Error("strict Gate 1 artifact target appeared before publication")
    raise OSError(error_number, os.strerror(error_number))


_STRICT_GATE1_INPUT_KEYS = frozenset(
    {
        "cases",
        "provider",
        "model",
        "backend_config_sha256",
        "limits",
        "gold_reference",
        "reviewer_metadata",
        "billing_scaffold",
        "repository_state",
        "cleanup_declaration",
        "checklist",
        "generated_at",
    }
)
_LEGACY_STRICT_GATE1_INPUT_KEYS = (_STRICT_GATE1_INPUT_KEYS - {"billing_scaffold"}) | {
    "billing_attestation"
}


def load_strict_gate1_input(path: str | Path) -> dict[str, Any]:
    """Load one explicit, frozen, offline Gate 1 input bundle."""
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise StrictGate1Error("strict Gate 1 input is not valid JSON") from exc
    if type(payload) is not dict:
        raise StrictGate1Error("strict Gate 1 input must be a JSON object")
    keys = set(payload)
    allowed = _STRICT_GATE1_INPUT_KEYS
    if keys == _LEGACY_STRICT_GATE1_INPUT_KEYS:
        allowed = _LEGACY_STRICT_GATE1_INPUT_KEYS
    missing = allowed - keys
    unknown = keys - allowed
    if missing or unknown:
        raise StrictGate1Error("strict Gate 1 input has invalid top-level keys")
    return payload


@dataclass(frozen=True)
class StrictGate1Artifacts:
    """The three offline artifacts plus the explicit frozen pilot plan."""

    plan: CapturedPilotPlan
    assembly: StrictRunAssembly
    packet: StrictRunPacket
    authorization_request: StrictAuthorizationRequest

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_sha256": self.plan.sha256,
            "assembly_sha256": self.assembly.sha256,
            "packet_sha256": self.packet.sha256,
            "authorization_request_sha256": self.authorization_request.sha256,
            "planned_calls": self.plan.to_dict().get("planned_calls"),
            "execution_authorized": False,
            "live_execution_requested": False,
        }


def write_strict_gate1_artifacts(
    artifacts: StrictGate1Artifacts, output_dir: str | Path
) -> dict[str, Any]:
    """Write the offline artifact bundle and return only its public index."""
    if not isinstance(artifacts, StrictGate1Artifacts):
        raise StrictGate1Error("validated strict artifacts are required")

    def open_secure_parent(path: str | Path) -> tuple[int, str]:
        required_flags = ("O_DIRECTORY", "O_NOFOLLOW")
        if any(not hasattr(os, flag) for flag in required_flags):
            raise StrictGate1Error("strict Gate 1 output directory safety is unsupported")
        if any(function not in os.supports_dir_fd for function in (os.open, os.mkdir, os.stat)):
            raise StrictGate1Error("strict Gate 1 directory-fd safety is unsupported")

        directory = Path(path)
        if not directory.name or any(part in {".", ".."} for part in directory.parts):
            raise StrictGate1Error("strict Gate 1 output directory path is invalid")
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        try:
            current_fd = os.open(os.sep if directory.is_absolute() else ".", flags)
            try:
                parent_parts = (
                    directory.parent.parts[1:]
                    if directory.is_absolute()
                    else directory.parent.parts
                )
                for part in parent_parts:
                    try:
                        next_fd = os.open(part, flags, dir_fd=current_fd)
                    except FileNotFoundError:
                        try:
                            os.mkdir(part, 0o700, dir_fd=current_fd)
                        except FileExistsError:
                            pass
                        next_fd = os.open(part, flags, dir_fd=current_fd)
                    os.close(current_fd)
                    current_fd = next_fd
                return current_fd, directory.name
            except Exception:
                os.close(current_fd)
                raise
        except StrictGate1Error:
            raise
        except OSError as exc:
            raise StrictGate1Error(
                "strict Gate 1 output directory must be a real directory"
            ) from exc

    try:
        files = {
            "plan": "plan.private.json",
            "assembly": "assembly.private.json",
            "packet": "packet.json",
            "authorization_request": "authorization-request.json",
            "index": "index.json",
        }
        manifests = {
            files["plan"]: artifacts.plan.manifest_json,
            files["assembly"]: artifacts.assembly.manifest_json,
            files["packet"]: artifacts.packet.manifest_json,
            files["authorization_request"]: artifacts.authorization_request.manifest_json,
        }
        parent_fd, output_name = open_secure_parent(output_dir)
        output_fd: int | None = None
        stage_fd: int | None = None
        stage_name: str | None = None
        published = False
        try:
            targets = (*manifests, files["index"])
            if any(
                not isinstance(filename, str) or Path(filename).name != filename
                for filename in targets
            ):
                raise StrictGate1Error("strict Gate 1 artifact target is invalid")

            try:
                output_fd = os.open(
                    output_name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent_fd
                )
            except FileNotFoundError:
                output_fd = None
            except OSError as exc:
                raise StrictGate1Error(
                    "strict Gate 1 output directory must be a real directory"
                ) from exc
            if output_fd is not None:
                existing = set(os.listdir(output_fd))
                if existing & set(targets):
                    raise StrictGate1Error("strict Gate 1 artifact target already exists")
                if existing:
                    raise StrictGate1Error("strict Gate 1 output directory is not empty")

            index = artifacts.to_dict() | {
                "status": "prepared",
                "files": files,
            }
            contents = manifests | {
                files["index"]: json.dumps(index, ensure_ascii=True, indent=2, sort_keys=True)
                + "\n"
            }
            stage_name = f".{output_name}.strict-gate1-{secrets.token_hex(12)}.tmpdir"
            os.mkdir(stage_name, 0o700, dir_fd=parent_fd)
            stage_fd = os.open(
                stage_name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent_fd
            )
            try:
                for filename, content in contents.items():
                    descriptor = os.open(
                        filename,
                        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                        0o600,
                        dir_fd=stage_fd,
                    )
                    try:
                        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                            descriptor = -1
                            handle.write(content)
                            handle.flush()
                            os.fsync(handle.fileno())
                    finally:
                        if descriptor != -1:
                            os.close(descriptor)
                os.fsync(stage_fd)
                if output_fd is None:
                    _publish_new_directory(stage_name, output_name, parent_fd)
                else:
                    os.replace(stage_name, output_name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
                published = True
                stage_name = None
                os.fsync(parent_fd)
            except Exception:
                if not published and stage_fd is not None:
                    for filename in contents:
                        try:
                            os.unlink(filename, dir_fd=stage_fd)
                        except OSError:
                            pass
                raise
        finally:
            if stage_fd is not None:
                os.close(stage_fd)
            if output_fd is not None:
                os.close(output_fd)
            if stage_name is not None:
                try:
                    os.rmdir(stage_name, dir_fd=parent_fd)
                except OSError:
                    pass
            os.close(parent_fd)
    except StrictGate1Error:
        raise
    except OSError as exc:
        raise StrictGate1Error("could not write strict Gate 1 artifacts") from exc
    return index


def prepare_strict_gate1_artifact_files(
    input_path: str | Path, output_dir: str | Path
) -> dict[str, Any]:
    """Load, build, and write a strict Gate 1 bundle without authorizing execution."""
    return write_strict_gate1_artifacts(
        build_strict_gate1_artifacts(**load_strict_gate1_input(input_path)), output_dir
    )


def build_strict_gate1_artifacts(
    *,
    cases: list[dict[str, Any]],
    provider: str,
    model: str,
    backend_config_sha256: str,
    limits: dict[str, int],
    gold_reference: dict[str, Any],
    reviewer_metadata: dict[str, str],
    billing_scaffold: dict[str, Any] | None = None,
    billing_attestation: dict[str, Any] | None = None,
    repository_state: dict[str, Any],
    cleanup_declaration: dict[str, Any],
    checklist: dict[str, Any],
    generated_at: str,
) -> StrictGate1Artifacts:
    """Build bound, non-authorizing artifacts from explicit frozen evidence.

    ``cases`` must contain the three strict cases and their four explicit packs;
    no smoke-run manifest is accepted or consulted.
    """
    try:
        plan = prepare_captured_pilot(
            cases=cases,
            provider=provider,
            model=model,
            backend_config_sha256=backend_config_sha256,
            limits=limits,
        )
        if plan.to_dict().get("planned_calls") != 12:
            raise StrictGate1Error("strict plan must contain exactly 12 cells")
        assembly = build_strict_run_assembly(
            plan=plan,
            gold_reference=gold_reference,
            reviewer_metadata=reviewer_metadata,
            billing_scaffold=billing_scaffold,
            billing_attestation=billing_attestation,
            repository_state=repository_state,
            cleanup_declaration=cleanup_declaration,
        )
        packet = build_strict_run_packet(assembly=assembly, checklist=checklist)
        request = build_strict_authorization_request(
            packet=packet, assembly=assembly, generated_at=generated_at
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, StrictGate1Error):
            raise
        raise StrictGate1Error(str(exc)) from exc
    return StrictGate1Artifacts(plan, assembly, packet, request)


def preflight_strict_gate1(
    *,
    bearer_present: bool,
    retry_attempts: int,
    fallbacks: bool,
    tools: str,
    tools_enforced: bool,
    planned_cells: int,
    smoke_runner: bool = False,
) -> dict[str, Any]:
    """Return secret-safe admission information without network or authorization."""
    failures: list[str] = []
    if type(bearer_present) is not bool or not bearer_present:
        failures.append("gateway bearer is missing")
    if type(retry_attempts) is not int or retry_attempts != 0:
        failures.append("retry attempts must be exactly 0")
    if type(fallbacks) is not bool or fallbacks is not False:
        failures.append("fallbacks must be exactly false")
    if tools != "none" or tools_enforced is not True:
        failures.append("tools must be none and the no-tools path must be enforced")
    if type(planned_cells) is not int or planned_cells != 12:
        failures.append("strict plan must contain exactly 12 cells")
    if smoke_runner:
        failures.append("smoke runner policy is not permitted for strict execution")
    return {
        "status": "ready" if not failures else "blocked",
        "blockers": failures,
        "bearer_present": bearer_present is True,
        "retry_attempts": retry_attempts,
        "fallbacks": fallbacks,
        "tools": tools,
        "tools_enforced": tools_enforced is True,
        "planned_cells": planned_cells,
        "network_called": False,
        "execution_authorized": False,
        "live_execution_requested": False,
    }


def require_strict_gate1_preflight(**kwargs: Any) -> dict[str, Any]:
    report = preflight_strict_gate1(**kwargs)
    if report["status"] != "ready":
        raise StrictGate1Error("strict Gate 1 preflight blocked: " + "; ".join(report["blockers"]))
    return report


@dataclass(frozen=True)
class StrictGate1Cell:
    case_name: str
    arm: str
    prompt: str
    rendered_context: str | None
    selected_ids: tuple[str, ...]


_ECHO_TOKEN = re.compile(r"[a-z0-9]+", re.I)


def _contains_dispatched_material(answer: object, cell: StrictGate1Cell) -> bool:
    """Reject substantial copies of the private prompt or rendered context."""
    if not isinstance(answer, Mapping) or not isinstance(answer.get("answer"), str):
        return False
    answer_tokens = _ECHO_TOKEN.findall(answer["answer"].casefold())
    answer_text = " ".join(answer_tokens)
    for source in (cell.prompt, cell.rendered_context):
        if not isinstance(source, str):
            continue
        source_tokens = _ECHO_TOKEN.findall(source.casefold())
        # Short prompts and ordinary short answers do not provide enough signal.
        if len(" ".join(source_tokens)) < 24 or len(source_tokens) < 4:
            continue
        source_text = " ".join(source_tokens)
        if source_text in answer_text:
            return True
        required = max(5, (len(source_tokens) * 3 + 4) // 5)
        if any(
            " ".join(source_tokens[start : start + required]) in answer_text
            for start in range(len(source_tokens) - required + 1)
        ):
            return True
        # A copied source can be padded or reordered to evade contiguous spans.
        # Require a substantial overlap and enough source tokens to avoid
        # rejecting ordinary answers that happen to share a few short words.
        if len(source_tokens) >= 8:
            answer_counts = Counter(answer_tokens)
            overlap = sum(
                min(answer_counts.get(token, 0), count)
                for token, count in Counter(source_tokens).items()
            )
            if overlap >= max(6, (len(source_tokens) * 3 + 3) // 4):
                return True
    return False


_CELL_RESULT_SCHEMA = "strict-gate1-cell-result/v1"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_ERROR_CODE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_PRIVATE_KEY = re.compile(
    r"-----BEGIN(?:\s+[A-Z0-9]+)?\s+PRIVATE KEY-----|OPENSSH PRIVATE KEY", re.I
)
_SECRET_KEY = re.compile(r"(?:private[_-]?key|secret|token|password|credential|api[_-]?key)", re.I)
_PRIVATE_FIELD = re.compile(r"^(?:prompt|context|rendered[_-]?context|raw[_-]?response)$", re.I)
_SECRET_VALUE = re.compile(
    r"(?:"
    r"sk-(?:[A-Za-z0-9_-]{16,})"
    r"|ghp_[A-Za-z0-9]{30,}"
    r"|(?:AKIA|ASIA)[A-Z0-9]{16}"
    r"|Bearer\s+(?!token\b)[A-Za-z0-9._~+/=-]{8,}"
    r"|eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"
    r")"
)


def _contains_unsafe_result_value(value: object, key: str = "") -> bool:
    if _SECRET_KEY.search(key) or _PRIVATE_FIELD.search(key):
        return True
    if isinstance(value, dict):
        return any(
            _contains_unsafe_result_value(child, str(child_key))
            for child_key, child in value.items()
        )
    if isinstance(value, (list, tuple)):
        return any(_contains_unsafe_result_value(child) for child in value)
    return isinstance(value, str) and bool(
        _PRIVATE_KEY.search(value) or _SECRET_VALUE.search(value)
    )


def _freeze_result_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze_result_value(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_result_value(item) for item in value)
    return value


def _thaw_result_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw_result_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_result_value(item) for item in value]
    return value


@dataclass(frozen=True)
class StrictGate1CellResult:
    """Closed, public-safe result projection for one strict cell."""

    case_name: str
    arm: str
    status: str
    answer: dict[str, object] | None = None
    raw_response_digest: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    schema_version: str = _CELL_RESULT_SCHEMA

    def __post_init__(self) -> None:
        if self.schema_version != _CELL_RESULT_SCHEMA:
            raise StrictGate1Error("invalid strict cell result schema")
        if type(self.case_name) is not str or not self.case_name:
            raise StrictGate1Error("strict cell result case_name is invalid")
        if type(self.arm) is not str or not self.arm:
            raise StrictGate1Error("strict cell result arm is invalid")
        if self.status == "completed":
            if not validate_answer_envelope(self.answer):
                raise StrictGate1Error(
                    "completed strict cell result requires a valid answer envelope"
                )
            if (
                type(self.raw_response_digest) is not str
                or _SHA256.fullmatch(self.raw_response_digest) is None
            ):
                raise StrictGate1Error("completed strict cell result requires a response digest")
            if self.error_code is not None or self.error_message is not None:
                raise StrictGate1Error("completed strict cell result cannot contain an error")
        elif self.status == "failed":
            if (
                self.answer is not None
                or not self._valid_error_code(self.error_code)
                or not self._valid_error_message(self.error_message)
            ):
                raise StrictGate1Error("failed strict cell result requires an explicit safe error")
            if self.raw_response_digest is not None:
                raise StrictGate1Error("failed strict cell result cannot contain a response digest")
        else:
            raise StrictGate1Error("strict cell result status is invalid")
        if _contains_unsafe_result_value(self.to_dict()):
            raise StrictGate1Error("strict cell result contains private or secret material")
        if self.answer is not None:
            object.__setattr__(self, "answer", _freeze_result_value(self.answer))

    @staticmethod
    def _valid_error_code(value: object) -> bool:
        return (
            type(value) is str and 0 < len(value) <= 64 and _ERROR_CODE.fullmatch(value) is not None
        )

    @staticmethod
    def _valid_error_message(value: object) -> bool:
        return (
            type(value) is str
            and 0 < len(value) <= 160
            and not _contains_unsafe_result_value(value)
        )

    @classmethod
    def from_value(cls, value: object) -> "StrictGate1CellResult":
        if isinstance(value, cls):
            return value
        if type(value) is not dict or set(value) != {
            "schema_version",
            "case_name",
            "arm",
            "status",
            "answer",
            "raw_response_digest",
            "error_code",
            "error_message",
        }:
            raise StrictGate1Error("adapter returned an invalid strict cell result schema")
        try:
            return cls(**value)
        except (TypeError, ValueError) as exc:
            raise StrictGate1Error("adapter returned an invalid strict cell result") from exc

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "case_name": self.case_name,
            "arm": self.arm,
            "status": self.status,
            "answer": _thaw_result_value(self.answer),
            "raw_response_digest": self.raw_response_digest,
            "error_code": self.error_code,
            "error_message": self.error_message,
        }


StrictAdapter = Callable[[StrictGate1Cell], StrictGate1CellResult | dict[str, object]]


async def run_strict_gate1(
    *,
    artifacts: StrictGate1Artifacts,
    bearer_present: bool,
    retry_attempts: int,
    fallbacks: bool,
    tools: str,
    tools_enforced: bool,
    authorize: bool,
    adapter: StrictAdapter,
    smoke_runner: bool = False,
) -> list[StrictGate1CellResult]:
    """Run exactly the bound twelve-cell matrix through an injected adapter.

    This function never reads the bearer value, retries, falls back, or imports
    a provider adapter.  ``authorize`` is intentionally separate from artifact
    generation and must be true for execution to begin.
    """
    if not isinstance(artifacts, StrictGate1Artifacts):
        raise StrictGate1Error("validated strict artifacts are required")
    if authorize is not True:
        raise StrictGate1Error("explicit live authorization is required")
    if not callable(adapter):
        raise StrictGate1Error("an injected adapter is required")
    require_strict_gate1_preflight(
        bearer_present=bearer_present,
        retry_attempts=retry_attempts,
        fallbacks=fallbacks,
        tools=tools,
        tools_enforced=tools_enforced,
        planned_cells=artifacts.plan.to_dict().get("planned_calls"),
        smoke_runner=smoke_runner,
    )
    try:
        assembly = parse_strict_run_assembly(artifacts.assembly.manifest_json)
        packet = artifacts.packet
        validate_strict_run_packet_binding(packet, assembly)
        if (
            hashlib.sha256(artifacts.authorization_request.manifest_json.encode()).hexdigest()
            != artifacts.authorization_request.sha256
        ):
            raise StrictGate1Error("authorization request self-hash is invalid")
        request = parse_strict_authorization_request(artifacts.authorization_request.manifest_json)
    except StrictGate1Error:
        raise
    except (TypeError, ValueError) as exc:
        raise StrictGate1Error("artifacts are not validated and mutually bound") from exc
    request_manifest = request.to_dict()
    if (
        request_manifest["packet_sha256"] != packet.sha256
        or request_manifest["assembly_sha256"] != assembly.sha256
    ):
        raise StrictGate1Error("authorization request is not bound to packet and assembly")
    if (
        artifacts.plan.sha256 != assembly.plan_sha256
        or artifacts.plan.to_dict() != assembly.to_dict()["plan"]
    ):
        raise StrictGate1Error("pilot plan is not bound to the assembly")
    if any(
        value is not False
        for value in (
            request_manifest["execution_authorized"],
            request_manifest["live_execution_requested"],
        )
    ):
        raise StrictGate1Error("authorization artifact cannot authorize execution")

    plan = artifacts.plan.to_dict()
    cells = [
        StrictGate1Cell(
            case_name=case["name"],
            arm=arm["arm"],
            prompt=case["prompt"],
            rendered_context=arm["rendered_context"],
            selected_ids=tuple(arm["selected_ids"]),
        )
        for case in plan["cases"]
        for arm in case["arms"]
    ]
    if len(cells) != 12:
        raise StrictGate1Error("strict plan must contain exactly 12 cells")
    results: list[StrictGate1CellResult] = []
    for cell in cells:
        try:
            result = adapter(cell)
            if inspect.isawaitable(result):
                result = await result
        except Exception:
            results.append(
                StrictGate1CellResult(
                    case_name=cell.case_name,
                    arm=cell.arm,
                    status="failed",
                    error_code="adapter_exception",
                    error_message="strict adapter failed",
                )
            )
            continue
        validated = StrictGate1CellResult.from_value(result)
        if validated.case_name != cell.case_name or validated.arm != cell.arm:
            raise StrictGate1Error("adapter result does not match the dispatched strict cell")
        if validated.status == "completed" and _contains_dispatched_material(
            validated.answer, cell
        ):
            validated = StrictGate1CellResult(
                case_name=cell.case_name,
                arm=cell.arm,
                status="failed",
                error_code="public_material",
                error_message="answer contains dispatched material",
            )
        results.append(validated)
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare offline strict Gate 1 artifacts")
    parser.add_argument("--input", required=True, dest="input_path")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)
    index = prepare_strict_gate1_artifact_files(args.input_path, args.output_dir)
    print(json.dumps(index, ensure_ascii=True, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
