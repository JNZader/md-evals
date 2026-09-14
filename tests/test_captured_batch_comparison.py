"""Tests for declared-grid comparison of captured four-arm rows."""

import copy
import json
import subprocess
import sys
from dataclasses import dataclass

import pytest

from md_evals.captured_batch_comparison import (
    ARMS,
    CapturedBatchComparisonError,
    compare_captured_batch,
)


A = "a" * 64
B = "b" * 64
DIGEST = "d" * 64


@dataclass
class Response:
    content: object


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
    timestamp: object = None
    unused_telemetry: object = None


def gold(answer="VALUE", citations=(), abstain=False):
    return {"answer": answer, "citations": list(citations), "abstain": abstain}


def response(expected, *, passed=True):
    if passed:
        return Response(json.dumps(expected))
    return Response(json.dumps(dict(expected, answer="WRONG")))


def row(task, repetition, arm, expected, *, passed=True, status="completed", **changes):
    selected = () if arm == "CONTROL" else (A,)
    values = {
        "task": task,
        "repetition": repetition,
        "arm": arm,
        "prompt": f"resolved:{task}",
        "rendered_context_sha256": None if arm == "CONTROL" else DIGEST,
        "selected_ids": selected,
        "status": status,
        "response": response(expected, passed=passed),
    }
    values.update(changes)
    return Row(**values)


def grid(expected_by_task, repetitions=1, outcomes=None):
    outcomes = outcomes or {}
    return [
        row(task, rep, arm, expected, **outcomes.get((task, rep, arm), {}))
        for task, expected in expected_by_task.items()
        for rep in range(repetitions)
        for arm in ARMS
    ]


def test_complete_batch_orders_cells_independent_of_input_shuffle_and_does_not_mutate_rows():
    expected = {"beta": gold(), "alpha": gold()}
    rows = grid(expected, repetitions=2)
    before = copy.deepcopy(rows)
    result = compare_captured_batch(list(reversed(rows)), expected_by_task=expected, repetitions=2)
    assert [(cell.task, cell.repetition, cell.arm) for cell in result.cells] == [
        (task, rep, arm) for task in ("alpha", "beta") for rep in range(2) for arm in ARMS
    ]
    assert rows == before
    assert result.complete and result.declared_n == 4
    assert [summary.contract_pass_rate for summary in result.arm_summaries] == [1.0] * 4


def test_fixed_pairs_count_wins_losses_and_ties_over_declared_denominator():
    expected = {"task": gold()}
    rows = grid(
        expected,
        repetitions=3,
        outcomes={
            ("task", 0, "B_STRUCTURE"): {"passed": False},
            ("task", 1, "E_PAIRED"): {"passed": False},
        },
    )
    result = compare_captured_batch(rows, expected_by_task=expected, repetitions=3)
    comparisons = {comparison.name: comparison for comparison in result.paired_comparisons}
    paired_structure = comparisons["E_PAIRED_vs_B_STRUCTURE"]
    assert paired_structure.available
    assert (paired_structure.wins, paired_structure.losses) == (1, 1)
    assert (paired_structure.both_pass, paired_structure.both_nonpass) == (1, 0)
    assert paired_structure.delta == 0.0
    assert (
        comparisons["E_PAIRED_vs_C_MEMORY"].losses,
        comparisons["E_PAIRED_vs_C_MEMORY"].both_pass,
    ) == (1, 2)


def test_llm_error_is_not_graded_even_if_content_looks_correct():
    expected = {"task": gold()}
    rows = grid(expected, outcomes={("task", 0, "E_PAIRED"): {"status": "llm_error"}})
    result = compare_captured_batch(rows, expected_by_task=expected, repetitions=1)
    cell = next(cell for cell in result.cells if cell.arm == "E_PAIRED")
    summary = next(item for item in result.arm_summaries if item.arm == "E_PAIRED")
    assert cell.state == "llm_error" and cell.grade is None
    assert summary.llm_errors == 1 and summary.passes == 0 and summary.contract_pass_rate == 0.0


def test_legacy_d_union_rows_remain_accepted_without_becoming_paired_comparisons():
    expected = {"task": gold()}
    rows = grid(expected) + [row("task", 0, "D_UNION", expected["task"])]
    result = compare_captured_batch(rows, expected_by_task=expected, repetitions=1)
    legacy = next(item for item in result.arm_summaries if item.arm == "D_UNION")
    assert legacy.passes == 1 and legacy.contract_pass_rate == 1.0
    assert all(item.candidate_arm != "D_UNION" and item.baseline_arm != "D_UNION" for item in result.paired_comparisons)


def test_invalid_json_is_a_completed_malformed_answer_in_denominator():
    expected = {"task": gold()}
    rows = grid(
        expected,
        outcomes={("task", 0, "C_MEMORY"): {"response": Response("not JSON")}},
    )
    result = compare_captured_batch(rows, expected_by_task=expected, repetitions=1)
    cell = next(cell for cell in result.cells if cell.arm == "C_MEMORY")
    summary = next(item for item in result.arm_summaries if item.arm == "C_MEMORY")
    assert cell.state == "completed" and cell.grade.reason_code == "invalid_json"
    assert (summary.completed, summary.malformed_answers, summary.passes) == (1, 1, 0)
    assert summary.contract_pass_rate == 0.0


def test_required_gold_citations_are_not_relaxed_for_control_or_hidden_context():
    expected = {"task": gold(citations=(A,))}
    rows = grid(expected)
    result = compare_captured_batch(rows, expected_by_task=expected, repetitions=1)
    control = next(cell for cell in result.cells if cell.arm == "CONTROL")
    structure = next(cell for cell in result.cells if cell.arm == "B_STRUCTURE")
    assert not control.grade.passed and not control.grade.citations_visible
    assert structure.grade.passed and structure.grade.citations_visible


@pytest.mark.parametrize(
    "changes",
    [
        {"task": "unknown"},
        {"arm": "E_OTHER"},
        {"repetition": 2},
        {"status": "pending"},
        {"task": ""},
        {"repetition": True},
        {"selected_ids": [A]},
    ],
)
def test_rejects_unknown_or_malformed_relevant_row_fields(changes):
    expected = {"task": gold()}
    rows = grid(expected)
    values = dict(rows[0].__dict__)
    values.update(changes)
    rows[0] = Row(**values)
    with pytest.raises(CapturedBatchComparisonError):
        compare_captured_batch(rows, expected_by_task=expected, repetitions=1)


def test_rejects_duplicate_cell_key_before_summary():
    expected = {"task": gold()}
    rows = grid(expected)
    rows.append(rows[0])
    with pytest.raises(CapturedBatchComparisonError, match="duplicate"):
        compare_captured_batch(rows, expected_by_task=expected, repetitions=1)


def test_empty_and_partial_grids_are_incomplete_and_suppress_rates_and_pair_counts():
    expected = {"task": gold()}
    empty = compare_captured_batch([], expected_by_task=expected, repetitions=1)
    partial = compare_captured_batch(grid(expected)[:-1], expected_by_task=expected, repetitions=1)
    for result in (empty, partial):
        assert not result.complete
        assert all(summary.contract_pass_rate is None for summary in result.arm_summaries)
        assert all(not item.available and item.delta is None for item in result.paired_comparisons)
        assert all(item.wins is None and item.losses is None for item in result.paired_comparisons)
    assert sum(cell.state == "missing" for cell in empty.cells) == 4
    assert sum(cell.state == "missing" for cell in partial.cells) == 1


def test_invalid_gold_fails_before_rows_even_when_every_cell_is_missing_or_error():
    invalid = {"task": {"answer": "VALUE", "citations": ["bad"], "abstain": False}}
    with pytest.raises(CapturedBatchComparisonError, match="invalid expected"):
        compare_captured_batch([], expected_by_task=invalid, repetitions=1)
    rows = grid(
        {"task": gold()}, outcomes={("task", 0, arm): {"status": "llm_error"} for arm in ARMS}
    )
    with pytest.raises(CapturedBatchComparisonError, match="invalid expected"):
        compare_captured_batch(rows, expected_by_task=invalid, repetitions=1)


def test_gold_abstention_cohorts_use_declared_tasks_and_zero_cohort_rate_is_none():
    expected = {"abstain": gold(answer=None, citations=(), abstain=True), "answer": gold()}
    result = compare_captured_batch(grid(expected), expected_by_task=expected, repetitions=1)
    cohorts = {cohort.abstain: cohort for cohort in result.cohort_summaries}
    assert (cohorts[True].declared_n, cohorts[True].contract_pass_rate) == (1, 1.0)
    assert (cohorts[False].declared_n, cohorts[False].contract_pass_rate) == (1, 1.0)
    only_answer = compare_captured_batch(
        grid({"answer": gold()}), expected_by_task={"answer": gold()}, repetitions=1
    )
    no_abstention = {cohort.abstain: cohort for cohort in only_answer.cohort_summaries}[True]
    assert no_abstention.declared_n == 0 and no_abstention.contract_pass_rate is None


def test_context_prompt_and_id_contracts_are_checked_without_deduplicating_ids():
    expected = {"task": gold()}
    rows = grid(expected, repetitions=2)
    rows[4] = row("task", 1, "CONTROL", expected["task"], prompt="different")
    with pytest.raises(CapturedBatchComparisonError, match="prompt"):
        compare_captured_batch(rows, expected_by_task=expected, repetitions=2)
    rows = grid(expected, repetitions=2)
    rows[4 + 1] = row("task", 1, "B_STRUCTURE", expected["task"], selected_ids=(A, A))
    with pytest.raises(CapturedBatchComparisonError, match="selected"):
        compare_captured_batch(rows, expected_by_task=expected, repetitions=2)
    rows = grid(expected)
    rows[0] = row("task", 0, "CONTROL", expected["task"], selected_ids=(A,))
    with pytest.raises(CapturedBatchComparisonError, match="CONTROL"):
        compare_captured_batch(rows, expected_by_task=expected, repetitions=1)


def test_empty_paired_source_packs_accept_digest_without_selected_ids_and_reach_reporting():
    expected = {"task": gold()}
    rows = grid(expected)
    for arm in ("B_STRUCTURE", "C_MEMORY"):
        rows[ARMS.index(arm)] = row(
            "task",
            0,
            arm,
            expected["task"],
            selected_ids=(),
            rendered_context_sha256=None,
        )
    rows[ARMS.index("E_PAIRED")] = row(
        "task",
        0,
        "E_PAIRED",
        expected["task"],
        selected_ids=(),
        rendered_context_sha256=DIGEST,
    )

    result = compare_captured_batch(rows, expected_by_task=expected, repetitions=1)

    assert result.complete
    paired = {item.name: item for item in result.paired_comparisons}
    assert paired["E_PAIRED_vs_B_STRUCTURE"].available
    assert paired["E_PAIRED_vs_C_MEMORY"].available
    assert all(item.both_pass == 1 for item in paired.values())


@pytest.mark.parametrize("digest", [None, "not-a-sha256-digest"])
def test_empty_e_paired_selection_requires_digest_before_pair_comparisons(digest):
    expected = {"task": gold()}
    e_paired = row(
        "task",
        0,
        "E_PAIRED",
        expected["task"],
        selected_ids=(),
        rendered_context_sha256=digest,
    )

    with pytest.raises(CapturedBatchComparisonError, match="E_PAIRED|digest"):
        compare_captured_batch([e_paired], expected_by_task=expected, repetitions=1)


@pytest.mark.parametrize(
    "arm,selected_ids,digest",
    [
        ("B_STRUCTURE", (), DIGEST),
        ("C_MEMORY", (), DIGEST),
        ("E_PAIRED", (A,), None),
        ("E_PAIRED", (), "not-a-sha256-digest"),
    ],
)
def test_rejects_malformed_digest_and_selected_id_combinations(arm, selected_ids, digest):
    expected = {"task": gold()}
    rows = grid(expected)
    rows[ARMS.index(arm)] = row(
        "task",
        0,
        arm,
        expected["task"],
        selected_ids=selected_ids,
        rendered_context_sha256=digest,
    )

    with pytest.raises(CapturedBatchComparisonError):
        compare_captured_batch(rows, expected_by_task=expected, repetitions=1)


def test_optional_telemetry_is_ignored_and_provider_modules_are_not_imported():
    expected = {"task": gold()}
    marker = object()
    rows = grid(expected)
    rows[0].unused_telemetry = None
    rows[1].unused_telemetry = marker
    result = compare_captured_batch(rows, expected_by_task=expected, repetitions=1)
    assert result.complete and rows[1].unused_telemetry is marker
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import md_evals.captured_batch_comparison; "
            "assert not {'litellm', 'md_evals.engine', 'md_evals.models'} & set(sys.modules)",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
