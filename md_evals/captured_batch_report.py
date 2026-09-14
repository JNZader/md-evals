"""Privacy-minimized JSON projection of already captured batch summaries."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from md_evals.captured_batch_comparison import compare_captured_batch

if TYPE_CHECKING:
    from collections.abc import Iterable


SCHEMA_VERSION = "captured-batch-report/v1"
TOKEN_FIELDS = (
    "prompt_tokens_known_subtotal",
    "completion_tokens_known_subtotal",
    "total_tokens_known_subtotal",
    "prompt_tokens_complete_total",
    "completion_tokens_complete_total",
    "total_tokens_complete_total",
)
LIMITATIONS = (
    "Captured-batch results are not statistical utility or Gate1 evidence.",
    "Token counters are not billing, provider identity, or measured token savings.",
    "This export does not authorize live execution or provide global pooled totals.",
)


def _quality(summary: object) -> dict[str, int | float | None]:
    return {
        "declared_n": summary.declared_n,
        "completed": summary.completed,
        "llm_errors": summary.llm_errors,
        "missing": summary.missing,
        "passes": summary.passes,
        "nonpasses": summary.nonpasses,
        "malformed_answers": summary.malformed_answers,
        "contract_pass_rate": summary.contract_pass_rate,
    }


def _usage(summary: object) -> dict[str, int | str | None]:
    result = {
        "declared_n": summary.declared_n,
        "responses": summary.responses,
        "llm_errors": summary.llm_errors,
        "missing": summary.missing,
        "reported": summary.reported,
        "partial": summary.partial,
        "unknown": summary.unknown,
        "token_count_encoding": "decimal-string",
    }
    result.update(
        {
            field: None if (value := getattr(summary, field)) is None else str(value)
            for field in TOKEN_FIELDS
        }
    )
    return result


def build_captured_report(
    rows: Iterable[object], *, expected_by_task: dict[str, dict[str, object]], repetitions: int
) -> dict[str, object]:
    """Return a deterministic allowlisted projection of raw captured rows."""
    comparison = compare_captured_batch(
        rows, expected_by_task=expected_by_task, repetitions=repetitions
    )
    quality = {summary.arm: summary for summary in comparison.arm_summaries}
    usage = {summary.arm: summary for summary in comparison.usage_summaries}
    return {
        "schema_version": SCHEMA_VERSION,
        "declared_n_per_arm": comparison.declared_n,
        "complete": comparison.complete,
        "arms": [
            {
                "arm": summary.arm,
                "quality": _quality(quality[summary.arm]),
                "usage": _usage(usage[summary.arm]),
            }
            for summary in comparison.arm_summaries
        ],
        "cohorts": [
            {
                "arm": cohort.arm,
                "abstain": cohort.abstain,
                "declared_n": cohort.declared_n,
                "passes": cohort.passes,
                "contract_pass_rate": cohort.contract_pass_rate,
            }
            for cohort in comparison.cohort_summaries
        ],
        "paired_comparisons": [
            {
                "name": pair.name,
                "candidate_arm": pair.candidate_arm,
                "baseline_arm": pair.baseline_arm,
                "declared_n": pair.declared_n,
                "available": pair.available,
                "wins": pair.wins,
                "losses": pair.losses,
                "both_pass": pair.both_pass,
                "both_nonpass": pair.both_nonpass,
                "delta": pair.delta,
                "dominance": pair.dominance,
            }
            for pair in comparison.paired_comparisons
        ],
        "limitations": list(LIMITATIONS),
    }


def render_captured_report_json(
    rows: Iterable[object], *, expected_by_task: dict[str, dict[str, object]], repetitions: int
) -> str:
    """Build the report and render stable UTF-8-safe JSON text without writing it."""
    return (
        json.dumps(
            build_captured_report(rows, expected_by_task=expected_by_task, repetitions=repetitions),
            sort_keys=True,
            indent=2,
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    )
