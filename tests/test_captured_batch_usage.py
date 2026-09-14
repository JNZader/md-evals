"""Offline usage summaries for declared captured batch cells."""

from copy import deepcopy
from dataclasses import asdict, dataclass
import json

import pytest

from md_evals.captured_batch_comparison import (
    ARMS,
    BatchComparison,
    compare_captured_batch,
)


A = "a" * 64
DIGEST = "d" * 64


@dataclass
class Response:
    content: object
    usage_provenance: object = None
    prompt_tokens: object = "legacy prompt is ignored"
    completion_tokens_detail: object = "legacy completion is ignored"
    total_tokens: object = "legacy total is ignored"
    tokens: object = "legacy tokens are ignored"


@dataclass
class Row:
    task: str
    repetition: int
    arm: str
    prompt: str
    rendered_context_sha256: str | None
    selected_ids: tuple[str, ...]
    status: str
    response: Response


def gold() -> dict[str, object]:
    return {"answer": "VALUE", "citations": [], "abstain": False}


def usage(status: str, **counters: object) -> dict[str, object]:
    return {"status": status, "origin": "cli-output", "eventCount": 1, **counters}


def row(
    arm: str, *, repetition: int = 0, status: str = "completed", response: Response | None = None
) -> Row:
    return Row(
        task="task",
        repetition=repetition,
        arm=arm,
        prompt="resolved:task",
        rendered_context_sha256=None if arm == "CONTROL" else DIGEST,
        selected_ids=() if arm == "CONTROL" else (A,),
        status=status,
        response=response or Response(json.dumps(gold())),
    )


def summaries(result):
    return {summary.arm: summary for summary in result.usage_summaries}


def repeated_rows(overrides, omitted=()):
    return [
        row(arm, repetition=repetition, response=overrides.get((arm, repetition)))
        for repetition in range(2)
        for arm in ARMS
        if (arm, repetition) not in omitted
    ]


def test_all_reported_zero_usage_is_additive_serializable_and_arm_ordered():
    rows = [
        row(
            arm,
            response=Response(json.dumps(gold()), usage("reported", inputTokens=0, outputTokens=0)),
        )
        for arm in ARMS
    ]

    result = compare_captured_batch(rows, expected_by_task={"task": gold()}, repetitions=1)

    assert [summary.arm for summary in result.usage_summaries] == list(ARMS)
    assert all(
        asdict(summary)
        == {
            "arm": summary.arm,
            "declared_n": 1,
            "responses": 1,
            "llm_errors": 0,
            "missing": 0,
            "reported": 1,
            "partial": 0,
            "unknown": 0,
            "prompt_tokens_known_subtotal": 0,
            "completion_tokens_known_subtotal": 0,
            "total_tokens_known_subtotal": 0,
            "prompt_tokens_complete_total": 0,
            "completion_tokens_complete_total": 0,
            "total_tokens_complete_total": 0,
        }
        for summary in result.usage_summaries
    )
    assert BatchComparison((), (), (), (), 0, False).usage_summaries == ()


def test_usage_partitions_partial_known_subtotals_and_arm_complete_totals_without_legacy_fields():
    reported = Response(json.dumps(gold()), usage("reported", inputTokens=2, outputTokens=3))
    partial_input = Response(json.dumps(gold()), usage("partial", inputTokens=5))
    invalid_unknown = Response(
        json.dumps(gold()), {"status": "unknown", "reason": "not-a-supported-reason"}
    )
    partial_output = Response(json.dumps(gold()), usage("partial", outputTokens=7))
    rows = [
        row("CONTROL", response=reported),
        row("B_STRUCTURE", response=partial_input),
        row("C_MEMORY", response=invalid_unknown),
        row("E_PAIRED", response=partial_output),
    ]
    before = deepcopy(rows)

    result = compare_captured_batch(rows, expected_by_task={"task": gold()}, repetitions=1)

    assert rows == before
    by_arm = summaries(result)
    assert asdict(by_arm["CONTROL"]) == {
        "arm": "CONTROL",
        "declared_n": 1,
        "responses": 1,
        "llm_errors": 0,
        "missing": 0,
        "reported": 1,
        "partial": 0,
        "unknown": 0,
        "prompt_tokens_known_subtotal": 2,
        "completion_tokens_known_subtotal": 3,
        "total_tokens_known_subtotal": 5,
        "prompt_tokens_complete_total": 2,
        "completion_tokens_complete_total": 3,
        "total_tokens_complete_total": 5,
    }
    assert (
        by_arm["B_STRUCTURE"].prompt_tokens_known_subtotal,
        by_arm["B_STRUCTURE"].completion_tokens_known_subtotal,
        by_arm["B_STRUCTURE"].total_tokens_known_subtotal,
    ) == (5, None, None)
    assert (
        by_arm["E_PAIRED"].prompt_tokens_known_subtotal,
        by_arm["E_PAIRED"].completion_tokens_known_subtotal,
        by_arm["E_PAIRED"].total_tokens_known_subtotal,
    ) == (None, 7, None)
    assert (by_arm["B_STRUCTURE"].partial, by_arm["C_MEMORY"].unknown) == (1, 1)
    assert all(
        value is None
            for arm in ("B_STRUCTURE", "C_MEMORY", "E_PAIRED")
        for value in (
            by_arm[arm].prompt_tokens_complete_total,
            by_arm[arm].completion_tokens_complete_total,
            by_arm[arm].total_tokens_complete_total,
        )
    )


def test_errors_missing_none_and_malformed_answers_are_accounted_from_declared_cells():
    malformed = Response("not-json", usage("reported", inputTokens=11, outputTokens=13))
    no_provenance = Response(json.dumps(gold()), None)
    rows = [
        row("CONTROL", response=malformed),
        row(
            "B_STRUCTURE",
            status="llm_error",
            response=Response(json.dumps(gold()), usage("reported", inputTokens=1, outputTokens=1)),
        ),
        row("C_MEMORY", response=no_provenance),
    ]

    result = compare_captured_batch(rows, expected_by_task={"task": gold()}, repetitions=1)

    by_arm = summaries(result)
    assert (by_arm["CONTROL"].responses, by_arm["CONTROL"].reported) == (1, 1)
    assert by_arm["CONTROL"].total_tokens_known_subtotal == 24
    assert (by_arm["B_STRUCTURE"].responses, by_arm["B_STRUCTURE"].llm_errors) == (0, 1)
    assert (by_arm["C_MEMORY"].responses, by_arm["C_MEMORY"].unknown) == (1, 1)
    assert (by_arm["E_PAIRED"].responses, by_arm["E_PAIRED"].missing) == (0, 1)
    assert all(
        summary.responses + summary.llm_errors + summary.missing == summary.declared_n
        for summary in result.usage_summaries
    )


def test_missing_provenance_attribute_is_unknown_without_using_legacy_response_fields():
    missing_attribute = Response(json.dumps(gold()))
    del missing_attribute.usage_provenance
    rows = [row(arm) for arm in ARMS]
    rows[0] = row("CONTROL", response=missing_attribute)

    result = compare_captured_batch(rows, expected_by_task={"task": gold()}, repetitions=1)

    control = summaries(result)["CONTROL"]
    assert (control.responses, control.unknown, control.total_tokens_known_subtotal) == (1, 1, None)


@pytest.mark.parametrize(
    ("overrides", "omitted", "arm", "expected"),
    [
        (
            {
                ("CONTROL", 0): Response(
                    json.dumps(gold()), usage("reported", inputTokens=2, outputTokens=3)
                ),
                ("CONTROL", 1): Response(
                    json.dumps(gold()), usage("reported", inputTokens=5, outputTokens=7)
                ),
            },
            {("E_PAIRED", 1)},
            "CONTROL",
            (7, 10, 17, 7, 10, 17),
        ),
        (
            {
                ("B_STRUCTURE", 0): Response(json.dumps(gold()), usage("partial", inputTokens=3)),
                ("B_STRUCTURE", 1): Response(json.dumps(gold()), usage("partial", outputTokens=4)),
            },
            set(),
            "B_STRUCTURE",
            (3, 4, None, None, None, None),
        ),
        (
            {
                ("C_MEMORY", 0): Response(
                    json.dumps(gold()), usage("reported", inputTokens=2, outputTokens=3)
                ),
                ("C_MEMORY", 1): Response(
                    json.dumps(gold()), {"status": "unknown", "reason": "invalid"}
                ),
            },
            set(),
            "C_MEMORY",
            (2, 3, 5, None, None, None),
        ),
    ],
)
def test_multi_cell_arm_usage_aggregates_without_cross_arm_completeness(
    overrides, omitted, arm, expected
):
    result = compare_captured_batch(
        repeated_rows(overrides, omitted), expected_by_task={"task": gold()}, repetitions=2
    )

    summary = summaries(result)[arm]
    assert (
        summary.prompt_tokens_known_subtotal,
        summary.completion_tokens_known_subtotal,
        summary.total_tokens_known_subtotal,
        summary.prompt_tokens_complete_total,
        summary.completion_tokens_complete_total,
        summary.total_tokens_complete_total,
    ) == expected
    if omitted:
        assert summaries(result)["E_PAIRED"].missing == 1


def test_empty_rows_emit_four_all_missing_usage_summaries_and_existing_validation_remains_strict():
    result = compare_captured_batch([], expected_by_task={"task": gold()}, repetitions=1)

    assert [(item.arm, item.declared_n, item.missing) for item in result.usage_summaries] == [
        (arm, 1, 1) for arm in ARMS
    ]
    assert all(
        item.responses == item.llm_errors == item.reported == item.partial == item.unknown == 0
        and item.prompt_tokens_known_subtotal is None
        and item.completion_tokens_known_subtotal is None
        and item.total_tokens_known_subtotal is None
        for item in result.usage_summaries
    )
    with pytest.raises(ValueError):
        compare_captured_batch([], expected_by_task={}, repetitions=1)
