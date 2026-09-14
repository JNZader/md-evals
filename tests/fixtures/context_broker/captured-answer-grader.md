# Grade a declared closed-answer contract

`grade_captured_answer(raw_response, expected, selected_ids)` returns a frozen
`GradeResult` using only the standard library. Example:

```python
expected = {"answer": "VALUE", "citations": ["a" * 64], "abstain": False}
result = grade_captured_answer(json.dumps(expected), expected, ["a" * 64])
assert result.passed
```

The caller supplies trusted gold metadata and the actual selected evidence IDs;
neither gold answers nor grading policy belong in model input. Grade only actual
completed response text. Execution errors remain separate caller-owned outcomes.

## Exact envelope and result

The JSON object has exactly `answer`, `citations`, and `abstain`.
With `abstain=false`, answer is a nonempty string; with `abstain=true`, answer
must be null and citations empty. Citations are a list of unique lowercase
64-hex IDs. Selected IDs may be a list or tuple and may contain duplicates.
Duplicate JSON keys, nonfinite constants, trailing content, fences, wrong types,
extra keys, and inconsistent abstention are invalid. Only JSON whitespace
outside the document is tolerated; answer values are never trimmed or normalized.

Separate booleans report `format_valid` (`valid` alias), `answer_matches`,
`citations_match` (order-independent exact gold set), `citations_visible`
(all returned IDs were selected), and `abstention_matches`. `passed` is their
conjunction. Invalid model output sets every axis false with a bounded reason
code; malformed gold or selected IDs instead raise `GradingCaseError`.
Reason codes are `response_type`, `invalid_json`, `invalid_envelope`,
`matched`, or `mismatch`; they never include output or gold text.

Gold citations may be absent from selected context. Guessing those exact IDs
can match gold but fails visibility. Empty citation visibility is vacuously true,
not factual grounding. The caller declares expected abstention explicitly and
owns semantic gold/source linking. This is closed-fixture equality, not a general
natural-language quality measure, semantic judge, runner integration, comparison,
or demonstrated benefit from any context arm.
