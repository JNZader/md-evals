"""Tests for md_evals.pipeline.detectors — response scorers.

Verifies FormatDetector, SecurityDetector, LLMJudgeDetector, and
aggregate_detector_scores with mocked LLM calls.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from md_evals.pipeline.context import EvalContext, Scenario
from md_evals.pipeline.detectors import (
    FormatDetector,
    LLMJudgeDetector,
    SecurityDetector,
    aggregate_detector_scores,
    _extract_json_object,
)
from md_evals.pipeline.skill_parser import ParsedSkill
from md_evals.scoring import DimensionScore


# ── Helpers ──


def _make_context(**metadata_extras):
    """Create an EvalContext with optional metadata."""
    ctx = EvalContext()
    ctx.metadata.update(metadata_extras)
    return ctx


def _make_skill():
    """Create a minimal ParsedSkill for testing."""
    return ParsedSkill(
        raw_content="# Test\nContent",
        title="Test",
        description="A test",
        rules=["Rule 1"],
    )


def _make_scenario(**kwargs):
    """Create a Scenario with defaults."""
    defaults = {"probe_name": "test", "prompt": "test prompt", "dimension": "general"}
    defaults.update(kwargs)
    return Scenario(**defaults)


# ============================================================================
# 1. FormatDetector Tests
# ============================================================================


WELL_FORMATTED_RESPONSE = """\
# Response Title

Here is a well-formatted response.

## Section 1

- Bullet point one
- Bullet point two

```python
def hello():
    print("Hello")
```

Short lines, consistent indentation.
"""

POORLY_FORMATTED_RESPONSE = "no headings no code blocks no lists just a single line"


def test_format_detector_name_and_dimension():
    """FormatDetector has correct name and dimension."""
    d = FormatDetector()
    assert d.name == "format"
    assert d.dimension == "format"


def test_format_detector_well_formatted():
    """Well-formatted content scores high."""
    d = FormatDetector()
    ctx = _make_context()
    scenario = _make_scenario()
    skill = _make_skill()

    result = d.score(scenario, WELL_FORMATTED_RESPONSE, skill, ctx)

    assert result.dimension == "format"
    assert result.score >= 0.8  # should pass most checks
    assert len(result.evidence) == 5  # one per check


def test_format_detector_poorly_formatted():
    """Poorly formatted content scores low."""
    d = FormatDetector()
    ctx = _make_context()
    scenario = _make_scenario()
    skill = _make_skill()

    result = d.score(scenario, POORLY_FORMATTED_RESPONSE, skill, ctx)

    assert result.dimension == "format"
    assert result.score <= 0.4  # should fail most checks


def test_format_detector_no_llm_calls():
    """FormatDetector makes ZERO LLM calls — verify with mock."""
    d = FormatDetector()
    mock_adapter = MagicMock()
    ctx = _make_context(judge_adapter=mock_adapter)
    scenario = _make_scenario()
    skill = _make_skill()

    d.score(scenario, "some content", skill, ctx)

    # Verify the adapter was never called
    mock_adapter.complete.assert_not_called()


def test_format_detector_mixed_indentation():
    """Mixed tabs and spaces causes indentation check to fail."""
    d = FormatDetector()
    ctx = _make_context()
    response = "# Title\n\t\ttabbed line\n    spaced line\n- item"
    result = d.score(_make_scenario(), response, _make_skill(), ctx)

    # Should fail indentation check
    evidence_str = " ".join(result.evidence)
    assert "Consistent indentation: FAIL" in evidence_str


def test_format_detector_long_lines():
    """Lines > 200 chars outside code blocks are penalized."""
    d = FormatDetector()
    ctx = _make_context()
    long_line = "x" * 250
    response = f"# Title\n\n{long_line}\n\n- item"
    result = d.score(_make_scenario(), response, _make_skill(), ctx)

    evidence_str = " ".join(result.evidence)
    assert "No very long lines: FAIL" in evidence_str


# ============================================================================
# 2. SecurityDetector Tests
# ============================================================================


def test_security_detector_name_and_dimension():
    """SecurityDetector has correct name and dimension."""
    d = SecurityDetector()
    assert d.name == "security"
    assert d.dimension == "safety"


def test_security_detector_clean_content():
    """Clean content with no security issues scores 1.0."""
    d = SecurityDetector()
    ctx = _make_context()
    clean = "Here is a helpful response about Python programming."

    result = d.score(_make_scenario(), clean, _make_skill(), ctx)

    assert result.dimension == "safety"
    assert result.score == 1.0
    assert "No security issues detected" in result.evidence


def test_security_detector_hardcoded_secret():
    """Content with hardcoded secret scores < 1.0."""
    d = SecurityDetector()
    ctx = _make_context()
    content = 'api_key = "sk-1234567890abcdef"'

    result = d.score(_make_scenario(), content, _make_skill(), ctx)

    assert result.score < 1.0
    assert any("secret" in e.lower() or "credential" in e.lower() for e in result.evidence)


def test_security_detector_dangerous_command():
    """Content with rm -rf /root scores < 1.0."""
    d = SecurityDetector()
    ctx = _make_context()
    # The regex requires \b after /, so use a path like /root
    content = "To fix this, run: rm -rf /root and start over"

    result = d.score(_make_scenario(), content, _make_skill(), ctx)

    assert result.score < 1.0


def test_security_detector_chmod_777():
    """Content with chmod 777 is flagged."""
    d = SecurityDetector()
    ctx = _make_context()
    content = "Set permissions with chmod 777 on the directory"

    result = d.score(_make_scenario(), content, _make_skill(), ctx)

    assert result.score < 1.0
    assert any("777" in e for e in result.evidence)


def test_security_detector_multiple_issues():
    """Multiple security issues accumulate penalties."""
    d = SecurityDetector()
    ctx = _make_context()
    content = (
        'api_key = "sk-1234567890abcdef"\n'
        "chmod 777 /var/data\n"
        "rm -rf / --no-preserve-root"
    )

    result = d.score(_make_scenario(), content, _make_skill(), ctx)

    # 3 issues × 0.2 penalty = 0.6 penalty → score 0.4
    assert result.score <= 0.6


def test_security_detector_no_llm_calls():
    """SecurityDetector makes ZERO LLM calls."""
    d = SecurityDetector()
    mock_adapter = MagicMock()
    ctx = _make_context(judge_adapter=mock_adapter)

    d.score(_make_scenario(), "content", _make_skill(), ctx)

    mock_adapter.complete.assert_not_called()


# ============================================================================
# 3. LLMJudgeDetector Tests
# ============================================================================


def test_llm_judge_detector_name_and_dimension():
    """LLMJudgeDetector has correct name and dimension."""
    d = LLMJudgeDetector()
    assert d.name == "llm-judge"
    assert d.dimension == "general"


def test_llm_judge_detector_custom_dimension():
    """LLMJudgeDetector accepts custom target_dimension."""
    d = LLMJudgeDetector(target_dimension="correctness")
    assert d.dimension == "correctness"


def test_llm_judge_detector_parses_valid_json(monkeypatch):
    """LLMJudgeDetector parses valid JSON from judge response."""
    judge_response = json.dumps({
        "score": 0.85,
        "rationale": "Good response",
        "dimension": "correctness",
    })
    monkeypatch.setattr(
        "md_evals.pipeline.detectors._run_llm_complete",
        lambda adapter, prompt, **kwargs: judge_response,
    )

    adapter = MagicMock()
    d = LLMJudgeDetector(target_dimension="correctness")
    ctx = _make_context(judge_adapter=adapter)

    result = d.score(_make_scenario(), "Good answer", _make_skill(), ctx)

    assert result.score == 0.85
    assert result.dimension == "correctness"
    assert "Good response" in result.evidence


def test_llm_judge_detector_json_parse_failure(monkeypatch):
    """LLMJudgeDetector returns score 0.0 on JSON parse failure."""
    monkeypatch.setattr(
        "md_evals.pipeline.detectors._run_llm_complete",
        lambda adapter, prompt, **kwargs: "not json at all, just text",
    )

    adapter = MagicMock()
    d = LLMJudgeDetector()
    ctx = _make_context(judge_adapter=adapter)

    result = d.score(_make_scenario(), "response", _make_skill(), ctx)

    assert result.score == 0.0
    assert any("parse" in e.lower() or "json" in e.lower() for e in result.evidence)


def test_llm_judge_detector_llm_failure(monkeypatch):
    """LLMJudgeDetector returns score 0.0 on LLM failure."""
    monkeypatch.setattr(
        "md_evals.pipeline.detectors._run_llm_complete",
        lambda adapter, prompt, **kwargs: None,
    )

    adapter = MagicMock()
    d = LLMJudgeDetector()
    ctx = _make_context(judge_adapter=adapter)

    result = d.score(_make_scenario(), "response", _make_skill(), ctx)

    assert result.score == 0.0


def test_llm_judge_detector_no_adapter():
    """LLMJudgeDetector returns score 0.0 when no adapter in context."""
    d = LLMJudgeDetector()
    ctx = _make_context()  # no judge_adapter

    result = d.score(_make_scenario(), "response", _make_skill(), ctx)

    assert result.score == 0.0


def test_llm_judge_detector_includes_precheck_findings(monkeypatch):
    """LLMJudgeDetector includes pre-check findings in the prompt."""
    captured_prompts = []

    def mock_complete(adapter, prompt, **kwargs):
        captured_prompts.append(prompt)
        return json.dumps({"score": 0.8, "rationale": "OK", "dimension": "general"})

    monkeypatch.setattr("md_evals.pipeline.detectors._run_llm_complete", mock_complete)

    # Create a mock pre_check_result with findings
    finding = MagicMock()
    finding.severity = "warning"
    finding.message = "Missing description section"
    pre_check = MagicMock()
    pre_check.findings = [finding]

    adapter = MagicMock()
    d = LLMJudgeDetector()
    ctx = _make_context(judge_adapter=adapter)
    ctx.pre_check_result = pre_check

    d.score(_make_scenario(), "response", _make_skill(), ctx)

    assert len(captured_prompts) == 1
    assert "Missing description section" in captured_prompts[0]


def test_llm_judge_detector_clamps_score(monkeypatch):
    """LLMJudgeDetector clamps scores outside [0.0, 1.0]."""
    judge_response = json.dumps({
        "score": 1.5,
        "rationale": "Over 9000",
        "dimension": "general",
    })
    monkeypatch.setattr(
        "md_evals.pipeline.detectors._run_llm_complete",
        lambda adapter, prompt, **kwargs: judge_response,
    )

    adapter = MagicMock()
    d = LLMJudgeDetector()
    ctx = _make_context(judge_adapter=adapter)

    result = d.score(_make_scenario(), "response", _make_skill(), ctx)

    assert result.score == 1.0  # clamped from 1.5


# ============================================================================
# 4. _extract_json_object Helper
# ============================================================================


def test_extract_json_object_direct():
    """Direct JSON object parsing."""
    text = '{"score": 0.9, "rationale": "good"}'
    result = _extract_json_object(text)
    assert result is not None
    assert result["score"] == 0.9


def test_extract_json_object_with_surrounding():
    """Extracts JSON from surrounding text."""
    text = 'Here is the result: {"score": 0.7} end.'
    result = _extract_json_object(text)
    assert result is not None
    assert result["score"] == 0.7


def test_extract_json_object_returns_none_on_garbage():
    """Returns None for non-JSON input."""
    result = _extract_json_object("not json")
    assert result is None


# ============================================================================
# 5. aggregate_detector_scores Tests
# ============================================================================


def test_aggregate_empty_scores():
    """Empty input returns empty list."""
    result = aggregate_detector_scores([])
    assert result == []


def test_aggregate_single_detector():
    """Single detector score passes through."""
    scores = [
        DimensionScore(
            dimension="format", score=0.8, weight=0.0, grade="B",
            evidence=["detector:format", "Has headings: PASS"],
        ),
    ]
    result = aggregate_detector_scores(scores)
    assert len(result) == 1
    assert result[0].dimension == "format"
    assert result[0].score == pytest.approx(0.8, abs=0.01)


def test_aggregate_multiple_detectors_same_dimension():
    """Multiple detectors on same dimension → weighted average."""
    scores = [
        DimensionScore(
            dimension="format", score=0.9, weight=0.0, grade="A",
            evidence=["detector:llm-judge"],
        ),
        DimensionScore(
            dimension="format", score=0.6, weight=0.0, grade="C",
            evidence=["detector:format"],
        ),
    ]
    result = aggregate_detector_scores(scores)
    assert len(result) == 1
    assert result[0].dimension == "format"
    # llm-judge weight=0.7, format weight=0.3 → (0.9*0.7 + 0.6*0.3) / 1.0
    expected = (0.9 * 0.7 + 0.6 * 0.3) / (0.7 + 0.3)
    assert result[0].score == pytest.approx(expected, abs=0.01)


def test_aggregate_different_dimensions():
    """Scores for different dimensions produce separate entries."""
    scores = [
        DimensionScore(
            dimension="format", score=0.8, weight=0.0, grade="B",
            evidence=["detector:format"],
        ),
        DimensionScore(
            dimension="safety", score=1.0, weight=0.0, grade="A",
            evidence=["detector:security"],
        ),
    ]
    result = aggregate_detector_scores(scores)
    assert len(result) == 2
    dims = {r.dimension for r in result}
    assert dims == {"format", "safety"}


def test_aggregate_merges_evidence():
    """Aggregation merges evidence from all detectors."""
    scores = [
        DimensionScore(
            dimension="general", score=0.8, weight=0.0, grade="B",
            evidence=["detector:llm-judge", "rationale 1"],
        ),
        DimensionScore(
            dimension="general", score=0.9, weight=0.0, grade="A",
            evidence=["detector:llm-judge", "rationale 2"],
        ),
    ]
    result = aggregate_detector_scores(scores)
    assert len(result) == 1
    assert "rationale 1" in result[0].evidence
    assert "rationale 2" in result[0].evidence
