"""Tests for the ThreePhaseEvaluator orchestrator."""

import json
from pathlib import Path

from md_evals.three_phase import (
    Phase,
    PhaseConfig,
    PhaseResult,
    ThreePhaseEvaluator,
    ThreePhaseResult,
)
from md_evals.graders.structure_grader import (
    JSONValidGrader,
    RequiredFieldsGrader,
    FieldTypeGrader,
)
from md_evals.graders.analysis_grader import (
    KeywordCoverageGrader,
    MinLengthGrader,
)
from md_evals.graders.generation_grader import (
    OutputMatchGrader,
    ConstraintGrader,
)


class TestThreePhaseEvaluatorAllPass:
    """Tests where all phases pass."""

    def test_all_phases_pass(self, tmp_path: Path):
        data = json.dumps({
            "analysis": "The system uses React and TypeScript",
            "score": 0.95,
            "recommendations": ["Use caching", "Add tests"],
        })
        (tmp_path / "output.json").write_text(data)

        evaluator = ThreePhaseEvaluator(
            structure=PhaseConfig(
                graders=[
                    JSONValidGrader(name="json_valid", path="output.json"),
                    RequiredFieldsGrader(
                        name="fields",
                        path="output.json",
                        required_fields=["analysis", "score"],
                    ),
                ],
            ),
            analyze=PhaseConfig(
                graders=[
                    KeywordCoverageGrader(
                        name="keywords",
                        content=data,
                        keywords=["React", "TypeScript"],
                    ),
                ],
            ),
            generate=PhaseConfig(
                graders=[
                    OutputMatchGrader(
                        name="output",
                        content=data,
                        patterns=[r"recommendations"],
                    ),
                ],
            ),
        )

        result = evaluator.evaluate(tmp_path)
        assert result.passed is True
        assert result.failed_phase is None
        assert len(result.phases) == 3
        assert all(pr.passed for pr in result.phases)
        assert result.overall_score > 0.0

    def test_empty_phases_pass(self, tmp_path: Path):
        evaluator = ThreePhaseEvaluator()
        result = evaluator.evaluate(tmp_path)
        assert result.passed is True
        assert result.overall_score == 1.0


class TestThreePhaseEvaluatorFailFast:
    """Tests where early phases fail and skip later ones."""

    def test_structure_failure_skips_analyze_and_generate(self, tmp_path: Path):
        (tmp_path / "output.json").write_text("not valid json")

        evaluator = ThreePhaseEvaluator(
            structure=PhaseConfig(
                graders=[
                    JSONValidGrader(name="json_valid", path="output.json"),
                ],
                required=True,
            ),
            analyze=PhaseConfig(
                graders=[
                    KeywordCoverageGrader(
                        name="kw", content="test", keywords=["test"]
                    ),
                ],
            ),
            generate=PhaseConfig(
                graders=[
                    OutputMatchGrader(
                        name="out", content="test", patterns=[r"test"]
                    ),
                ],
            ),
        )

        result = evaluator.evaluate(tmp_path)
        assert result.passed is False
        assert result.failed_phase == Phase.STRUCTURE
        assert result.phases[0].passed is False
        assert result.phases[1].skipped is True
        assert result.phases[2].skipped is True

    def test_analyze_failure_skips_generate(self, tmp_path: Path):
        (tmp_path / "output.json").write_text('{"valid": true}')

        evaluator = ThreePhaseEvaluator(
            structure=PhaseConfig(
                graders=[
                    JSONValidGrader(name="json_valid", path="output.json"),
                ],
            ),
            analyze=PhaseConfig(
                graders=[
                    KeywordCoverageGrader(
                        name="kw",
                        content="nothing relevant",
                        keywords=["specific_missing_keyword"],
                    ),
                ],
                required=True,
            ),
            generate=PhaseConfig(
                graders=[
                    OutputMatchGrader(
                        name="out", content="test", patterns=[r"test"]
                    ),
                ],
            ),
        )

        result = evaluator.evaluate(tmp_path)
        assert result.passed is False
        assert result.failed_phase == Phase.ANALYZE
        assert result.phases[0].passed is True
        assert result.phases[1].passed is False
        assert result.phases[2].skipped is True


class TestThreePhaseEvaluatorNonRequired:
    """Tests where phases are not required (no fail-fast)."""

    def test_non_required_structure_failure_continues(self, tmp_path: Path):
        (tmp_path / "output.json").write_text("not json")

        evaluator = ThreePhaseEvaluator(
            structure=PhaseConfig(
                graders=[
                    JSONValidGrader(name="json_valid", path="output.json"),
                ],
                required=False,  # Don't fail-fast
            ),
            analyze=PhaseConfig(
                graders=[
                    MinLengthGrader(
                        name="len", content="enough words here", min_words=2
                    ),
                ],
            ),
            generate=PhaseConfig(
                graders=[
                    OutputMatchGrader(
                        name="out",
                        content="generated output",
                        patterns=[r"generated"],
                    ),
                ],
            ),
        )

        result = evaluator.evaluate(tmp_path)
        assert result.passed is False  # Structure failed
        assert result.phases[0].passed is False
        assert result.phases[1].passed is True
        assert result.phases[1].skipped is False
        assert result.phases[2].passed is True


class TestThreePhaseEvaluatorScoring:
    """Tests for weighted scoring across phases."""

    def test_weighted_scoring(self, tmp_path: Path):
        evaluator = ThreePhaseEvaluator(
            structure=PhaseConfig(
                graders=[
                    JSONValidGrader(name="json", content='{"valid": true}'),
                ],
                weight=0.3,
            ),
            analyze=PhaseConfig(
                graders=[
                    KeywordCoverageGrader(
                        name="kw",
                        content="has keyword_a only",
                        keywords=["keyword_a", "keyword_b"],
                        pass_threshold=0.0,
                    ),
                ],
                weight=0.4,
            ),
            generate=PhaseConfig(
                graders=[
                    OutputMatchGrader(
                        name="out",
                        content="matches pattern",
                        patterns=[r"matches"],
                    ),
                ],
                weight=0.3,
            ),
        )

        result = evaluator.evaluate(tmp_path)
        # Structure: 1.0 * 0.3 = 0.3
        # Analyze: 0.5 * 0.4 = 0.2 (1 of 2 keywords)
        # Generate: 1.0 * 0.3 = 0.3
        # Total = 0.8 / 1.0 = 0.8
        assert 0.79 <= result.overall_score <= 0.81

    def test_skipped_phase_scores_zero(self, tmp_path: Path):
        evaluator = ThreePhaseEvaluator(
            structure=PhaseConfig(
                graders=[
                    JSONValidGrader(name="json", content="bad json"),
                ],
                weight=0.5,
                required=True,
            ),
            analyze=PhaseConfig(weight=0.25),
            generate=PhaseConfig(weight=0.25),
        )

        result = evaluator.evaluate(tmp_path)
        # Structure: 0.0 * 0.5 = 0.0
        # Analyze: 0.0 * 0.25 = 0.0 (skipped)
        # Generate: 0.0 * 0.25 = 0.0 (skipped)
        assert result.overall_score == 0.0


class TestThreePhaseEvaluatorContentMode:
    """Tests for evaluate_content convenience method."""

    def test_evaluate_content_valid_json(self):
        data = json.dumps({"key": "value", "count": 42})

        evaluator = ThreePhaseEvaluator(
            structure=PhaseConfig(
                graders=[
                    JSONValidGrader(name="json", path="output.json"),
                    RequiredFieldsGrader(
                        name="fields",
                        path="output.json",
                        required_fields=["key", "count"],
                    ),
                ],
            ),
        )

        result = evaluator.evaluate_content(data)
        assert result.passed is True

    def test_evaluate_content_invalid_json(self):
        evaluator = ThreePhaseEvaluator(
            structure=PhaseConfig(
                graders=[
                    JSONValidGrader(name="json", path="output.json"),
                ],
            ),
        )

        result = evaluator.evaluate_content("not json at all")
        assert result.passed is False


class TestPhaseResultModel:
    """Tests for the PhaseResult data model."""

    def test_phase_result_defaults(self):
        pr = PhaseResult(phase=Phase.STRUCTURE, passed=True)
        assert pr.skipped is False
        assert pr.grader_results == []

    def test_three_phase_result_defaults(self):
        r = ThreePhaseResult(passed=True)
        assert r.overall_score == 0.0
        assert r.failed_phase is None
        assert r.phases == []


class TestPhaseEnum:
    """Tests for Phase enum."""

    def test_phase_values(self):
        assert Phase.STRUCTURE.value == "structure"
        assert Phase.ANALYZE.value == "analyze"
        assert Phase.GENERATE.value == "generate"

    def test_phase_string_comparison(self):
        assert Phase.STRUCTURE == "structure"


class TestIntegrationFullPipeline:
    """Integration tests combining all three phases with realistic data."""

    def test_skill_evaluation_output(self, tmp_path: Path):
        """Simulate evaluating a skill analysis output."""
        output = json.dumps({
            "skill_name": "react-19",
            "analysis": {
                "strengths": [
                    "Clear component patterns",
                    "Good TypeScript integration",
                ],
                "weaknesses": ["Missing error boundaries"],
                "coverage": 0.85,
            },
            "recommendations": "Add error boundary patterns and testing guides.",
            "score": 0.85,
        })
        (tmp_path / "output.json").write_text(output)

        evaluator = ThreePhaseEvaluator(
            structure=PhaseConfig(
                graders=[
                    JSONValidGrader(name="json_valid", path="output.json"),
                    RequiredFieldsGrader(
                        name="required_fields",
                        path="output.json",
                        required_fields=[
                            "skill_name",
                            "analysis",
                            "recommendations",
                            "score",
                        ],
                    ),
                    FieldTypeGrader(
                        name="field_types",
                        content=output,
                        field_types={
                            "skill_name": "str",
                            "analysis": "dict",
                            "score": "number",
                        },
                    ),
                ],
                weight=0.3,
            ),
            analyze=PhaseConfig(
                graders=[
                    KeywordCoverageGrader(
                        name="concept_coverage",
                        content=output,
                        keywords=["strengths", "weaknesses", "coverage"],
                    ),
                    MinLengthGrader(
                        name="min_length",
                        content=output,
                        min_chars=50,
                    ),
                ],
                weight=0.3,
            ),
            generate=PhaseConfig(
                graders=[
                    OutputMatchGrader(
                        name="has_recommendations",
                        content=output,
                        patterns=[r"recommendations"],
                    ),
                    ConstraintGrader(
                        name="no_secrets",
                        content=output,
                        forbidden_patterns=[r"API_KEY", r"SECRET"],
                    ),
                ],
                weight=0.4,
            ),
        )

        result = evaluator.evaluate(tmp_path)
        assert result.passed is True
        assert result.overall_score > 0.9
        assert len(result.phases) == 3
        assert all(not pr.skipped for pr in result.phases)
