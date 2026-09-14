"""Pure declared-grid comparison for raw captured four-arm execution rows.

This module deliberately joins already captured rows to the public strict grader.
It neither executes models nor infers the declared benchmark contract from rows.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from md_evals.bridge_usage import decode_usage_provenance
from md_evals.captured_answer_grader import GradeResult, GradingCaseError, grade_captured_answer

if TYPE_CHECKING:
    from collections.abc import Iterable


ARMS = ("CONTROL", "B_STRUCTURE", "C_MEMORY", "E_PAIRED")
_LEGACY_ARM = "D_UNION"
_PAIR_DEFINITIONS = (
    ("E_PAIRED_vs_B_STRUCTURE", "E_PAIRED", "B_STRUCTURE"),
    ("E_PAIRED_vs_C_MEMORY", "E_PAIRED", "C_MEMORY"),
)
_ID = re.compile(r"[0-9a-f]{64}")


class CapturedBatchComparisonError(ValueError):
    """Declared batch setup or a relevant raw-row field is malformed."""


@dataclass(frozen=True)
class CellAssessment:
    """One planned task/repetition/arm cell, including explicitly missing cells."""

    task: str
    repetition: int
    arm: str
    state: Literal["completed", "llm_error", "missing"]
    grade: GradeResult | None


@dataclass(frozen=True)
class ArmSummary:
    """Counts over the declared N cells for one arm."""

    arm: str
    declared_n: int
    completed: int
    llm_errors: int
    missing: int
    passes: int
    nonpasses: int
    malformed_answers: int
    contract_pass_rate: float | None


@dataclass(frozen=True)
class CohortSummary:
    """An arm-local declared cohort split by the gold abstention contract."""

    arm: str
    abstain: bool
    declared_n: int
    passes: int
    contract_pass_rate: float | None


@dataclass(frozen=True)
class PairedComparison:
    """A fixed E_PAIRED pair; unavailable whenever any planned cell is missing."""

    name: str
    candidate_arm: str
    baseline_arm: str
    declared_n: int
    available: bool
    wins: int | None
    losses: int | None
    both_pass: int | None
    both_nonpass: int | None
    delta: float | None
    dominance: Literal["candidate", "baseline", "inconclusive"] | None = None


@dataclass(frozen=True)
class ArmUsageSummary:
    """Validated arm telemetry, with known subtotals distinct from complete totals.

    Known subtotals add independently available provenance counters. Complete
    totals require every declared arm cell to be reported; telemetry is neither
    billing nor identity attestation, and error-cell usage remains unknown.
    """

    arm: str
    declared_n: int
    responses: int
    llm_errors: int
    missing: int
    reported: int
    partial: int
    unknown: int
    prompt_tokens_known_subtotal: int | None
    completion_tokens_known_subtotal: int | None
    total_tokens_known_subtotal: int | None
    prompt_tokens_complete_total: int | None
    completion_tokens_complete_total: int | None
    total_tokens_complete_total: int | None


@dataclass(frozen=True)
class BatchComparison:
    """Complete declared-grid result without model-quality or statistical claims."""

    cells: tuple[CellAssessment, ...]
    arm_summaries: tuple[ArmSummary, ...]
    cohort_summaries: tuple[CohortSummary, ...]
    paired_comparisons: tuple[PairedComparison, ...]
    declared_n: int
    complete: bool
    usage_summaries: tuple[ArmUsageSummary, ...] = ()

    @property
    def assessments(self) -> tuple[CellAssessment, ...]:
        """Compatibility name for the planned cell assessments."""
        return self.cells


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CapturedBatchComparisonError(message)


def _field(row: object, name: str) -> object:
    marker = object()
    value = getattr(row, name, marker)
    _require(value is not marker, f"row missing {name}")
    return value


def _valid_id(value: object) -> bool:
    return type(value) is str and _ID.fullmatch(value) is not None


def _validate_declarations(
    expected_by_task: object, repetitions: object
) -> tuple[tuple[str, ...], dict[str, dict[str, object]], int]:
    _require(type(repetitions) is int and repetitions > 0, "repetitions must be a positive int")
    _require(
        type(expected_by_task) is dict and bool(expected_by_task), "expected_by_task is required"
    )
    _require(
        all(type(task) is str and bool(task) for task in expected_by_task),
        "declared task names must be nonempty strings",
    )
    expected = dict(expected_by_task)
    for task in sorted(expected):
        try:
            # The public grader validates gold before parsing this discarded invalid response.
            grade_captured_answer("", expected[task], [])
        except GradingCaseError as exc:
            raise CapturedBatchComparisonError(f"invalid expected gold for {task}") from exc
    return tuple(sorted(expected)), expected, repetitions


def _validated_row(
    row: object, tasks: tuple[str, ...], repetitions: int
) -> tuple[tuple[str, int, str], object]:
    task = _field(row, "task")
    repetition = _field(row, "repetition")
    arm = _field(row, "arm")
    prompt = _field(row, "prompt")
    digest = _field(row, "rendered_context_sha256")
    selected_ids = _field(row, "selected_ids")
    status = _field(row, "status")
    _require(type(task) is str and bool(task) and task in tasks, "unknown or invalid task")
    _require(type(repetition) is int and 0 <= repetition < repetitions, "invalid repetition")
    _require(arm in ARMS or arm == _LEGACY_ARM, "unknown arm")
    _require(type(prompt) is str and bool(prompt), "invalid resolved prompt")
    _require(type(selected_ids) in (tuple, list), "invalid selected IDs")
    _require(all(_valid_id(item) for item in selected_ids), "invalid selected IDs")
    _require(
        digest is None or (type(digest) is str and _ID.fullmatch(digest) is not None),
        "invalid rendered context digest",
    )
    _require(status in ("completed", "llm_error"), "invalid row status")
    if arm == "CONTROL":
        _require(not selected_ids and digest is None, "CONTROL must not carry selected context")
    elif arm == "E_PAIRED":
        _require(digest is not None, "E_PAIRED requires a rendered context digest")
    else:
        _require(
            (not selected_ids and digest is None)
            or (bool(selected_ids) and digest is not None),
            "selected IDs and rendered context digest must agree",
        )
    return (task, repetition, arm), row


def _check_row_consistency(rows_by_key: dict[tuple[str, int, str], object]) -> None:
    prompts: dict[str, str] = {}
    contexts: dict[tuple[str, str], tuple[tuple[str, ...], str | None]] = {}
    for (task, _repetition, arm), row in rows_by_key.items():
        prompt = _field(row, "prompt")
        selected = tuple(_field(row, "selected_ids"))
        digest = _field(row, "rendered_context_sha256")
        _require(task not in prompts or prompts[task] == prompt, "inconsistent resolved prompt")
        prompts[task] = prompt
        context_key = (task, arm)
        context = (selected, digest)
        _require(
            context_key not in contexts or contexts[context_key] == context,
            "inconsistent selected IDs or rendered context digest",
        )
        contexts[context_key] = context


def _assess_cells(
    rows_by_key: dict[tuple[str, int, str], object],
    tasks: tuple[str, ...],
    expected: dict[str, dict[str, object]],
    repetitions: int,
    arms: tuple[str, ...],
) -> tuple[CellAssessment, ...]:
    cells = []
    for task in tasks:
        for repetition in range(repetitions):
            for arm in arms:
                row = rows_by_key.get((task, repetition, arm))
                if row is None:
                    cells.append(CellAssessment(task, repetition, arm, "missing", None))
                    continue
                status = _field(row, "status")
                if status == "llm_error":
                    cells.append(CellAssessment(task, repetition, arm, "llm_error", None))
                    continue
                response = _field(row, "response")
                marker = object()
                content = getattr(response, "content", marker)
                _require(content is not marker, "completed row response is malformed")
                grade = grade_captured_answer(content, expected[task], _field(row, "selected_ids"))
                cells.append(CellAssessment(task, repetition, arm, "completed", grade))
    return tuple(cells)


def _arm_summaries(
    cells: tuple[CellAssessment, ...], complete: bool, arms: tuple[str, ...]
) -> tuple[ArmSummary, ...]:
    summaries = []
    for arm in arms:
        arm_cells = tuple(cell for cell in cells if cell.arm == arm)
        completed = tuple(cell for cell in arm_cells if cell.state == "completed")
        passed = sum(cell.grade.passed for cell in completed if cell.grade is not None)
        malformed = sum(not cell.grade.format_valid for cell in completed if cell.grade is not None)
        declared_n = len(arm_cells)
        summaries.append(
            ArmSummary(
                arm=arm,
                declared_n=declared_n,
                completed=len(completed),
                llm_errors=sum(cell.state == "llm_error" for cell in arm_cells),
                missing=sum(cell.state == "missing" for cell in arm_cells),
                passes=passed,
                nonpasses=declared_n - passed,
                malformed_answers=malformed,
                contract_pass_rate=passed / declared_n if complete else None,
            )
        )
    return tuple(summaries)


def _cohort_summaries(
    cells: tuple[CellAssessment, ...], expected: dict[str, dict[str, object]], complete: bool,
    arms: tuple[str, ...],
) -> tuple[CohortSummary, ...]:
    summaries = []
    for arm in arms:
        for abstain in (True, False):
            cohort = tuple(
                cell
                for cell in cells
                if cell.arm == arm and expected[cell.task]["abstain"] is abstain
            )
            passes = sum(
                cell.grade.passed
                for cell in cohort
                if cell.state == "completed" and cell.grade is not None
            )
            declared_n = len(cohort)
            summaries.append(
                CohortSummary(
                    arm=arm,
                    abstain=abstain,
                    declared_n=declared_n,
                    passes=passes,
                    contract_pass_rate=(passes / declared_n if complete and declared_n else None),
                )
            )
    return tuple(summaries)


def _paired_comparisons(
    cells: tuple[CellAssessment, ...], complete: bool, arms: tuple[str, ...]
) -> tuple[PairedComparison, ...]:
    by_key = {(cell.task, cell.repetition, cell.arm): cell for cell in cells}
    declared_n = len(cells) // len(arms)
    comparisons = []
    for name, candidate_arm, baseline_arm in _PAIR_DEFINITIONS:
        if not complete:
            comparisons.append(
                PairedComparison(
                    name,
                    candidate_arm,
                    baseline_arm,
                    declared_n,
                    False,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                )
            )
            continue
        wins = losses = both_pass = both_nonpass = 0
        for task, repetition, _arm in sorted(by_key):
            if _arm != candidate_arm:
                continue
            candidate = by_key[(task, repetition, candidate_arm)]
            baseline = by_key[(task, repetition, baseline_arm)]
            candidate_pass = candidate.grade is not None and candidate.grade.passed
            baseline_pass = baseline.grade is not None and baseline.grade.passed
            if candidate_pass and not baseline_pass:
                wins += 1
            elif baseline_pass and not candidate_pass:
                losses += 1
            elif candidate_pass:
                both_pass += 1
            else:
                both_nonpass += 1
        comparisons.append(
            PairedComparison(
                name,
                candidate_arm,
                baseline_arm,
                declared_n,
                True,
                wins,
                losses,
                both_pass,
                both_nonpass,
                (wins - losses) / declared_n,
                "candidate" if wins > losses else "baseline" if losses > wins else "inconclusive",
            )
        )
    return tuple(comparisons)


def _sum_known(values: list[int]) -> int | None:
    return sum(values) if values else None


def _usage_summaries(
    cells: tuple[CellAssessment, ...], rows_by_key: dict[tuple[str, int, str], object],
    arms: tuple[str, ...],
) -> tuple[ArmUsageSummary, ...]:
    """Summarize only normalized provenance from already validated completed rows."""
    summaries = []
    for arm in arms:
        arm_cells = tuple(cell for cell in cells if cell.arm == arm)
        prompt_known: list[int] = []
        completion_known: list[int] = []
        total_known: list[int] = []
        reported = partial = unknown = 0
        for cell in arm_cells:
            if cell.state != "completed":
                continue
            row = rows_by_key[(cell.task, cell.repetition, cell.arm)]
            response = _field(row, "response")
            normalized, prompt_tokens, completion_tokens, total_tokens, _legacy_tokens = (
                decode_usage_provenance(getattr(response, "usage_provenance", None))
            )
            status = normalized["status"]
            if status == "reported":
                reported += 1
            elif status == "partial":
                partial += 1
            else:
                unknown += 1
            if prompt_tokens is not None:
                prompt_known.append(prompt_tokens)
            if completion_tokens is not None:
                completion_known.append(completion_tokens)
            if total_tokens is not None:
                total_known.append(total_tokens)
        declared_n = len(arm_cells)
        responses = sum(cell.state == "completed" for cell in arm_cells)
        llm_errors = sum(cell.state == "llm_error" for cell in arm_cells)
        missing = sum(cell.state == "missing" for cell in arm_cells)
        fully_reported = responses == declared_n and reported == declared_n
        summaries.append(
            ArmUsageSummary(
                arm=arm,
                declared_n=declared_n,
                responses=responses,
                llm_errors=llm_errors,
                missing=missing,
                reported=reported,
                partial=partial,
                unknown=unknown,
                prompt_tokens_known_subtotal=_sum_known(prompt_known),
                completion_tokens_known_subtotal=_sum_known(completion_known),
                total_tokens_known_subtotal=_sum_known(total_known),
                prompt_tokens_complete_total=sum(prompt_known) if fully_reported else None,
                completion_tokens_complete_total=(
                    sum(completion_known) if fully_reported else None
                ),
                total_tokens_complete_total=sum(total_known) if fully_reported else None,
            )
        )
    return tuple(summaries)


def compare_captured_batch(
    rows: Iterable[object], *, expected_by_task: dict[str, dict[str, object]], repetitions: int
) -> BatchComparison:
    """Compare a declared task × repetition × four-arm batch of raw captured rows.

    Gold is validated before any actual response is read.  Missing cells make the
    result incomplete and suppress all rates and paired deltas rather than reducing N.
    """
    tasks, expected, repetitions = _validate_declarations(expected_by_task, repetitions)
    try:
        supplied_rows = tuple(rows)
    except TypeError as exc:
        raise CapturedBatchComparisonError("rows must be iterable") from exc
    rows_by_key: dict[tuple[str, int, str], object] = {}
    for row in supplied_rows:
        key, validated = _validated_row(row, tasks, repetitions)
        _require(key not in rows_by_key, "duplicate task/repetition/arm cell")
        rows_by_key[key] = validated
    _check_row_consistency(rows_by_key)
    arms = ARMS + ((_LEGACY_ARM,) if _LEGACY_ARM in {key[2] for key in rows_by_key} else ())
    cells = _assess_cells(rows_by_key, tasks, expected, repetitions, arms)
    complete = all(cell.state != "missing" for cell in cells)
    return BatchComparison(
        cells=cells,
        arm_summaries=_arm_summaries(cells, complete, arms),
        cohort_summaries=_cohort_summaries(cells, expected, complete, arms),
        paired_comparisons=_paired_comparisons(cells, complete, arms),
        declared_n=len(tasks) * repetitions,
        complete=complete,
        usage_summaries=_usage_summaries(cells, rows_by_key, arms),
    )
