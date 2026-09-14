"""Contract tests for the privacy-minimized captured batch report."""

from copy import deepcopy
from dataclasses import dataclass
import json
import subprocess
import sys

import pytest

from md_evals.captured_batch_comparison import ARMS, CapturedBatchComparisonError
from md_evals.captured_batch_report import build_captured_report, render_captured_report_json


IDENTIFIER = "a" * 64
DIGEST = "d" * 64


@dataclass
class Response:
    content: object
    usage_provenance: object = None
    raw_response: object = "SECRET-RAW-RESPONSE"


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
    metadata: object = "SECRET-METADATA"


def gold(*, abstain=False):
    return {"answer": None if abstain else "VALUE", "citations": [], "abstain": abstain}


def usage(status, **counters):
    return {"status": status, "origin": "cli-output", "eventCount": 1, **counters}


def row(task, repetition, arm, expected, **changes):
    values = {
        "task": task,
        "repetition": repetition,
        "arm": arm,
        "prompt": "SECRET-PROMPT",
        "rendered_context_sha256": None if arm == "CONTROL" else DIGEST,
        "selected_ids": () if arm == "CONTROL" else (IDENTIFIER,),
        "status": "completed",
        "response": Response(json.dumps(expected)),
    }
    values.update(changes)
    return Row(**values)


def grid(expected, repetitions=1, omitted=(), changes=None):
    changes = changes or {}
    return [
        row(task, repetition, arm, value, **changes.get((task, repetition, arm), {}))
        for task, value in expected.items()
        for repetition in range(repetitions)
        for arm in ARMS
        if (task, repetition, arm) not in omitted
    ]


def test_complete_report_projects_only_fixed_ordered_summary_fields_and_is_pure():
    expected = {"SECRET-TASK-A": gold(), "SECRET-TASK-B": gold(abstain=True)}
    rows = grid(expected, repetitions=2)
    before = deepcopy(rows)

    report = build_captured_report(reversed(rows), expected_by_task=expected, repetitions=2)

    assert rows == before
    assert report["schema_version"] == "captured-batch-report/v1"
    assert (report["declared_n_per_arm"], report["complete"]) == (4, True)
    assert [item["arm"] for item in report["arms"]] == list(ARMS)
    assert [item["arm"] for item in report["cohorts"]] == [
        arm for arm in ARMS for _ in (True, False)
    ]
    assert set(report["arms"][0]) == {"arm", "quality", "usage"}
    assert set(report["arms"][0]["quality"]) == {
        "declared_n",
        "completed",
        "llm_errors",
        "missing",
        "passes",
        "nonpasses",
        "malformed_answers",
        "contract_pass_rate",
    }
    assert set(report["arms"][0]["usage"]) == {
        "declared_n",
        "responses",
        "llm_errors",
        "missing",
        "reported",
        "partial",
        "unknown",
        "prompt_tokens_known_subtotal",
        "completion_tokens_known_subtotal",
        "total_tokens_known_subtotal",
        "prompt_tokens_complete_total",
        "completion_tokens_complete_total",
        "total_tokens_complete_total",
        "token_count_encoding",
    }
    assert all(item["usage"]["token_count_encoding"] == "decimal-string" for item in report["arms"])
    assert report["paired_comparisons"][0]["name"] == "E_PAIRED_vs_B_STRUCTURE"
    rendered = render_captured_report_json(rows, expected_by_task=expected, repetitions=2)
    assert rendered.endswith("\n") and json.loads(rendered) == build_captured_report(
        rows, expected_by_task=expected, repetitions=2
    )
    assert all(
        secret not in rendered
        for secret in (
            "SECRET-TASK",
            "SECRET-PROMPT",
            "SECRET-METADATA",
            "SECRET-RAW",
            DIGEST,
            IDENTIFIER,
        )
    )


def test_incomplete_quality_is_independent_from_complete_arm_usage_and_nulls_are_preserved():
    expected = {"task": gold()}
    rows = grid(expected, repetitions=2, omitted={("task", 1, "E_PAIRED")})
    rows = [
        row_item
        if row_item.arm != "CONTROL"
        else Row(
            **{
                **row_item.__dict__,
                "response": Response(
                    json.dumps(gold()), usage("reported", inputTokens=0, outputTokens=0)
                ),
            }
        )
        for row_item in rows
    ]

    report = build_captured_report(rows, expected_by_task=expected, repetitions=2)

    control = report["arms"][0]
    assert not report["complete"] and control["quality"]["contract_pass_rate"] is None
    assert control["usage"]["prompt_tokens_complete_total"] == "0"
    assert control["usage"]["completion_tokens_complete_total"] == "0"
    assert all(
        item["delta"] is None and not item["available"] for item in report["paired_comparisons"]
    )


def test_usage_encoding_covers_reported_partial_unknown_errors_and_exact_large_aggregates():
    expected = {"task": gold()}
    huge = 2**53 - 1
    rows = grid(
        expected,
        repetitions=2,
        changes={
            ("task", 0, "CONTROL"): {
                "response": Response(
                    json.dumps(gold()), usage("reported", inputTokens=huge, outputTokens=0)
                )
            },
            ("task", 1, "CONTROL"): {
                "response": Response(
                    json.dumps(gold()), usage("reported", inputTokens=1, outputTokens=0)
                )
            },
            ("task", 0, "B_STRUCTURE"): {
                "response": Response(json.dumps(gold()), usage("partial", inputTokens=3))
            },
            ("task", 0, "C_MEMORY"): {
                "response": Response(json.dumps(gold()), usage("unknown", reason="missing"))
            },
            ("task", 0, "E_PAIRED"): {"status": "llm_error"},
        },
    )

    report = build_captured_report(rows, expected_by_task=expected, repetitions=2)

    arms = {item["arm"]: item for item in report["arms"]}
    assert arms["CONTROL"]["usage"]["prompt_tokens_complete_total"] == str(huge + 1)
    assert arms["CONTROL"]["usage"]["total_tokens_known_subtotal"] == str(huge + 1)
    assert arms["B_STRUCTURE"]["usage"]["prompt_tokens_known_subtotal"] == "3"
    assert arms["B_STRUCTURE"]["usage"]["total_tokens_complete_total"] is None
    assert arms["C_MEMORY"]["usage"]["unknown"] == 2
    assert arms["E_PAIRED"]["usage"]["llm_errors"] == 1


def test_order_and_generator_do_not_change_stable_json_bytes():
    expected = {"beta": gold(), "alpha": gold()}
    rows = grid(expected, repetitions=2)
    first = render_captured_report_json(iter(rows), expected_by_task=expected, repetitions=2)
    second = render_captured_report_json(reversed(rows), expected_by_task=expected, repetitions=2)
    assert first == second


def test_validation_errors_are_inherited_and_manual_summaries_are_not_an_api():
    expected = {"task": gold()}
    rows = grid(expected)
    with pytest.raises(CapturedBatchComparisonError):
        build_captured_report(rows + [rows[0]], expected_by_task=expected, repetitions=1)
    with pytest.raises(CapturedBatchComparisonError):
        build_captured_report([], expected_by_task={"task": {"answer": "bad"}}, repetitions=1)
    with pytest.raises(CapturedBatchComparisonError):
        build_captured_report(object(), expected_by_task=expected, repetitions=1)


def test_import_is_pure_and_does_not_load_model_or_provider_modules():
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import md_evals.captured_batch_report; "
            "assert not {'litellm', 'md_evals.engine', 'md_evals.models'} & set(sys.modules)",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
