"""Strict equality grading for a caller-declared closed-answer JSON contract."""

import json
import re
from dataclasses import dataclass


class GradingCaseError(ValueError):
    """Trusted benchmark setup is malformed; this is not a model-answer failure."""


@dataclass(frozen=True)
class GradeResult:
    format_valid: bool
    answer_matches: bool
    citations_match: bool
    citations_visible: bool
    abstention_matches: bool
    reason_code: str

    @property
    def valid(self) -> bool:
        """Compatibility name for format validity, not overall correctness."""
        return self.format_valid

    @property
    def passed(self) -> bool:
        return all(
            (
                self.format_valid,
                self.answer_matches,
                self.citations_match,
                self.citations_visible,
                self.abstention_matches,
            )
        )


def _is_id(value) -> bool:
    return type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def validate_answer_envelope(value) -> bool:
    """Return whether ``value`` is the exact closed captured-answer envelope."""
    if type(value) is not dict or set(value) != {"answer", "citations", "abstain"}:
        return False
    citations = value["citations"]
    if (
        type(value["abstain"]) is not bool
        or type(citations) is not list
        or not all(_is_id(item) for item in citations)
        or len(citations) != len(set(citations))
    ):
        return False
    if value["abstain"]:
        return value["answer"] is None and citations == []
    return type(value["answer"]) is str and bool(value["answer"])


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def _reject_nonfinite(_constant):
    raise ValueError("non-finite constant")


def _invalid(reason):
    return GradeResult(False, False, False, False, False, reason)


def grade_captured_answer(
    raw_response: str, expected: dict[str, object], selected_ids: list[str] | tuple[str, ...]
) -> GradeResult:
    """Grade completed response text only; gold meaning and execution status are caller-owned."""
    if not validate_answer_envelope(expected):
        raise GradingCaseError("invalid expected envelope")
    if type(selected_ids) not in (list, tuple) or not all(_is_id(item) for item in selected_ids):
        raise GradingCaseError("invalid selected IDs")
    if type(raw_response) is not str:
        return _invalid("response_type")
    try:
        response = json.loads(
            raw_response, object_pairs_hook=_unique_object, parse_constant=_reject_nonfinite
        )
    except (ValueError, RecursionError):
        return _invalid("invalid_json")
    if not validate_answer_envelope(response):
        return _invalid("invalid_envelope")
    returned_citations = set(response["citations"])
    axes = (
        response["answer"] == expected["answer"],
        returned_citations == set(expected["citations"]),
        returned_citations <= set(selected_ids),
        response["abstain"] == expected["abstain"],
    )
    return GradeResult(True, *axes, "matched" if all(axes) else "mismatch")
