"""Closed-answer grading contracts, independent of execution and providers."""

import ast
import json
from copy import deepcopy
from dataclasses import FrozenInstanceError, asdict
from pathlib import Path

import pytest

from md_evals.captured_answer_grader import GradingCaseError, grade_captured_answer

A, B, C = "a" * 64, "b" * 64, "c" * 64


def gold():
    return {"answer": "VALUE", "citations": [A, B], "abstain": False}


def assert_invalid(result, reason):
    assert not result.valid and not result.passed
    assert asdict(result) == {
        "format_valid": False,
        "answer_matches": False,
        "citations_match": False,
        "citations_visible": False,
        "abstention_matches": False,
        "reason_code": reason,
    }


def test_exact_success_and_json_whitespace():
    raw = " \t\r\n" + json.dumps(gold()) + "\n "
    result = grade_captured_answer(raw, gold(), [A, B])
    assert result.valid and result.passed and result.reason_code == "matched"
    assert all(value for key, value in asdict(result).items() if key != "reason_code")


@pytest.mark.parametrize("answer", ["value", " VALUE", "VALUE ", "VALUE\n", "prefix VALUE", "VALU"])
def test_answers_require_exact_values_not_normalization_or_substrings(answer):
    result = grade_captured_answer(json.dumps(dict(gold(), answer=answer)), gold(), [A, B])
    assert result.format_valid and not result.answer_matches and not result.passed
    assert result.citations_match and result.citations_visible and result.abstention_matches
    assert result.reason_code == "mismatch"


@pytest.mark.parametrize(
    "citations,selected,matches,visible",
    [
        ([B, A], [A, B], True, True),
        ([A], [A, B], False, True),
        ([], [A, B], False, True),
        ([A, B, C], [A, B, C], False, True),
        ([A, B], [A], True, False),
        ([A, B], [], True, False),
    ],
)
def test_gold_citation_set_and_actual_visibility_are_independent(
    citations, selected, matches, visible
):
    response = dict(gold(), citations=citations)
    result = grade_captured_answer(json.dumps(response), gold(), selected)
    assert result.valid and result.answer_matches and result.abstention_matches
    assert result.citations_match is matches and result.citations_visible is visible
    assert result.passed is (matches and visible)


@pytest.mark.parametrize("expected_abstain", [False, True])
@pytest.mark.parametrize("returned_abstain", [False, True])
def test_abstention_policy_is_explicit_not_inferred_from_empty_selection(
    expected_abstain, returned_abstain
):
    abstained = {"answer": None, "citations": [], "abstain": True}
    expected = abstained if expected_abstain else gold()
    response = abstained if returned_abstain else gold()
    result = grade_captured_answer(json.dumps(response), expected, [A, B])
    assert result.valid and result.abstention_matches is (expected_abstain == returned_abstain)
    assert result.passed is (expected_abstain == returned_abstain)


@pytest.mark.parametrize("raw", [None, b"{}", 1, True, [], {}])
def test_nontext_response_is_model_failure_not_case_failure(raw):
    assert_invalid(grade_captured_answer(raw, gold(), [A, B]), "response_type")


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "not JSON",
        "```json\n{}\n```",
        "{} trailing",
        "{}{}",
        '{"answer":"VALUE","answer":"VALUE","citations":[],"abstain":false}',
        '{"answer":{"nested":1,"nested":2},"citations":[],"abstain":false}',
        "NaN",
        "Infinity",
        "-Infinity",
        '{"answer":NaN,"citations":[],"abstain":false}',
        "\u00a0{}",
        "{}\u00a0",
    ],
)
def test_parser_rejects_non_json_or_ambiguous_documents(raw):
    assert_invalid(grade_captured_answer(raw, gold(), [A, B]), "invalid_json")


def test_deep_valid_json_never_becomes_a_valid_answer():
    # Deep arrays are valid JSON; parser recursion limits vary across runtimes.
    raw = "[" * 2000 + "0" + "]" * 2000
    result = grade_captured_answer(raw, gold(), [A, B])
    assert result.reason_code in {"invalid_json", "invalid_envelope"}
    assert_invalid(result, result.reason_code)
    assert result == grade_captured_answer(raw, gold(), [A, B])


BAD_ENVELOPES = [
    None,
    [],
    "VALUE",
    1,
    True,
    {},
    {"answer": "VALUE", "citations": [A, B]},
    dict(gold(), extra="secret"),
    dict(gold(), answer=""),
    dict(gold(), answer=None),
    dict(gold(), answer=1),
    dict(gold(), answer=True),
    dict(gold(), abstain=1),
    dict(gold(), abstain="false"),
    dict(gold(), citations=""),
    dict(gold(), citations={}),
    dict(gold(), citations=[1]),
    dict(gold(), citations=[A, A]),
    dict(gold(), citations=["a" * 63]),
    dict(gold(), citations=["G" * 64]),
    dict(gold(), citations=[A + "\n"]),
    {"answer": "VALUE", "citations": [], "abstain": True},
    {"answer": None, "citations": [A], "abstain": True},
]


@pytest.mark.parametrize("response", BAD_ENVELOPES)
def test_invalid_answer_shape_disables_every_scoring_axis(response):
    assert_invalid(grade_captured_answer(json.dumps(response), gold(), [A, B]), "invalid_envelope")


@pytest.mark.parametrize("expected", BAD_ENVELOPES + [dict(gold(), citations=(A, B))])
def test_bad_gold_is_setup_error_even_when_model_output_is_also_invalid(expected):
    with pytest.raises(GradingCaseError) as error:
        grade_captured_answer("not JSON", expected, [A, B])
    assert str(error.value) == "invalid expected envelope"


@pytest.mark.parametrize("selected", [None, A, {}, [1], [True], ["a" * 63], ["G" * 64], [A + "\n"]])
def test_bad_selected_ids_are_setup_errors_not_model_failures(selected):
    with pytest.raises(GradingCaseError) as error:
        grade_captured_answer("not JSON", gold(), selected)
    assert str(error.value) == "invalid selected IDs"


@pytest.mark.parametrize("selected", [[A, A, B], (A, B, A)])
def test_duplicate_selected_ids_are_valid_and_inputs_remain_unchanged(selected):
    expected = gold()
    before = deepcopy((expected, selected))
    raw = json.dumps(expected)
    result = grade_captured_answer(raw, expected, selected)
    assert result.passed and result == grade_captured_answer(raw, expected, selected)
    assert (expected, selected) == before
    with pytest.raises(FrozenInstanceError):
        result.reason_code = "changed"


def test_empty_gold_citation_visibility_is_vacuous_not_grounding():
    expected = dict(gold(), citations=[])
    result = grade_captured_answer(json.dumps(expected), expected, [])
    assert result.citations_visible and result.citations_match and result.passed


def test_reason_codes_do_not_include_response_or_gold_text():
    expected = dict(gold(), answer="SECRET_GOLD")
    response = dict(expected, answer="SECRET_OUTPUT")
    valid = grade_captured_answer(json.dumps(response), expected, [A, B])
    invalid = grade_captured_answer("SECRET_OUTPUT", expected, [A, B])
    assert valid.reason_code == "mismatch" and invalid.reason_code == "invalid_json"
    assert "SECRET" not in repr(valid) + repr(invalid)


def test_unicode_answer_equality_preserves_exact_codepoints():
    expected = dict(gold(), answer="café 雪")
    assert grade_captured_answer(json.dumps(expected), expected, [A, B]).passed
    response = dict(expected, answer="cafe\u0301 雪")
    assert not grade_captured_answer(json.dumps(response), expected, [A, B]).answer_matches


def test_grader_imports_only_standard_library_not_execution_or_providers():
    source = Path(__file__).parents[1] / "md_evals/captured_answer_grader.py"
    nodes = ast.walk(ast.parse(source.read_text()))
    imports = []
    for node in nodes:
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module)
    assert set(imports) == {"json", "re", "dataclasses"}
