"""Comprehensive tests for md_evals.suites module.

Tests cover:
  - SkillEntry, SuiteConfig, SuiteResult dataclass contracts
  - grade_meets_threshold logic (all grade pairs, unknown grades)
  - SuiteLoader.load (YAML parsing, validation, error handling)
  - SuiteLoader.from_dict (dict parsing, edge cases)
  - SuiteRunner with mocked PipelineRunner
"""

from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from md_evals.scoring import DimensionScore, EvalMetadata, EvalResult
from md_evals.suites import (
    SkillEntry,
    SuiteConfig,
    SuiteLoader,
    SuiteLoadError,
    SuiteResult,
    SuiteRunner,
    grade_meets_threshold,
)


# ─── Fixtures ───


def _make_eval_result(grade: str = "B", score: float = 0.78) -> EvalResult:
    """Create a minimal EvalResult for testing."""
    return EvalResult(
        skill_path="test.md",
        overall_grade=grade,
        overall_score=score,
        dimensions=[
            DimensionScore("correctness", 0.9, 0.5, "A"),
            DimensionScore("completeness", 0.7, 0.5, "B"),
        ],
        pre_check=None,
        metadata=EvalMetadata(model="gpt-4o", provider="mock"),
    )


# ============================================================================
# SkillEntry
# ============================================================================


class TestSkillEntry:
    def test_defaults(self):
        entry = SkillEntry(path="skills/go.md")
        assert entry.path == "skills/go.md"
        assert entry.min_grade == "C"

    def test_custom_grade(self):
        entry = SkillEntry(path="skills/rust.md", min_grade="A")
        assert entry.min_grade == "A"


# ============================================================================
# SuiteConfig
# ============================================================================


class TestSuiteConfig:
    def test_defaults(self):
        config = SuiteConfig()
        assert config.name == ""
        assert config.skills == []
        assert config.pre_check == "required"
        assert config.rubric is None

    def test_with_skills(self):
        config = SuiteConfig(
            name="backend",
            skills=[
                SkillEntry("go.md", "B"),
                SkillEntry("rust.md", "A"),
            ],
        )
        assert config.name == "backend"
        assert len(config.skills) == 2
        assert config.skills[0].min_grade == "B"


# ============================================================================
# SuiteResult
# ============================================================================


class TestSuiteResult:
    def test_defaults(self):
        result = SuiteResult(name="test", passed=True)
        assert result.name == "test"
        assert result.passed is True
        assert result.results == []
        assert result.total_skills == 0

    def test_with_results(self):
        er = _make_eval_result()
        result = SuiteResult(
            name="test",
            passed=False,
            results=[("skill.md", er, False)],
            total_skills=1,
            passed_skills=0,
            failed_skills=1,
        )
        assert not result.passed
        assert result.failed_skills == 1


# ============================================================================
# grade_meets_threshold
# ============================================================================


class TestGradeMeetsThreshold:
    """Tests for the grade comparison function."""

    @pytest.mark.parametrize(
        "actual,minimum,expected",
        [
            ("S", "S", True),
            ("S", "A", True),
            ("S", "F", True),
            ("A", "A", True),
            ("A", "B", True),
            ("A", "S", False),
            ("B", "B", True),
            ("B", "C", True),
            ("B", "A", False),
            ("C", "C", True),
            ("C", "B", False),
            ("D", "D", True),
            ("D", "C", False),
            ("F", "F", True),
            ("F", "D", False),
            ("F", "S", False),
        ],
    )
    def test_all_combinations(self, actual, minimum, expected):
        assert grade_meets_threshold(actual, minimum) == expected

    def test_unknown_actual_grade(self):
        assert grade_meets_threshold("X", "C") is False

    def test_unknown_minimum_grade(self):
        assert grade_meets_threshold("B", "X") is False


# ============================================================================
# SuiteLoader
# ============================================================================


class TestSuiteLoader:
    """Tests for YAML loading and parsing."""

    def test_load_valid_file(self, tmp_path: Path):
        suite_file = tmp_path / "suite.yaml"
        suite_file.write_text(
            textwrap.dedent("""\
            name: backend-skills
            skills:
              - path: skills/go.md
                min_grade: B
              - path: skills/rust.md
                min_grade: A
            pre_check: required
            """)
        )
        config = SuiteLoader.load(str(suite_file))
        assert config.name == "backend-skills"
        assert len(config.skills) == 2
        assert config.skills[0].path == "skills/go.md"
        assert config.skills[0].min_grade == "B"
        assert config.skills[1].min_grade == "A"

    def test_load_string_skills(self, tmp_path: Path):
        suite_file = tmp_path / "suite.yaml"
        suite_file.write_text(
            textwrap.dedent("""\
            name: simple
            skills:
              - skills/go.md
              - skills/rust.md
            """)
        )
        config = SuiteLoader.load(str(suite_file))
        assert len(config.skills) == 2
        assert config.skills[0].path == "skills/go.md"
        assert config.skills[0].min_grade == "C"  # default

    def test_load_missing_file(self):
        with pytest.raises(SuiteLoadError, match="not found"):
            SuiteLoader.load("/nonexistent/suite.yaml")

    def test_load_empty_file(self, tmp_path: Path):
        suite_file = tmp_path / "suite.yaml"
        suite_file.write_text("")
        with pytest.raises(SuiteLoadError, match="empty"):
            SuiteLoader.load(str(suite_file))

    def test_load_invalid_yaml(self, tmp_path: Path):
        suite_file = tmp_path / "suite.yaml"
        suite_file.write_text("{{{{invalid yaml")
        with pytest.raises(SuiteLoadError, match="Invalid YAML"):
            SuiteLoader.load(str(suite_file))

    def test_load_invalid_pre_check(self, tmp_path: Path):
        suite_file = tmp_path / "suite.yaml"
        suite_file.write_text(
            textwrap.dedent("""\
            name: test
            skills: []
            pre_check: invalid_value
            """)
        )
        with pytest.raises(SuiteLoadError, match="Invalid pre_check"):
            SuiteLoader.load(str(suite_file))

    def test_load_invalid_min_grade(self, tmp_path: Path):
        suite_file = tmp_path / "suite.yaml"
        suite_file.write_text(
            textwrap.dedent("""\
            name: test
            skills:
              - path: test.md
                min_grade: X
            """)
        )
        with pytest.raises(SuiteLoadError, match="Invalid min_grade"):
            SuiteLoader.load(str(suite_file))

    def test_load_missing_path(self, tmp_path: Path):
        suite_file = tmp_path / "suite.yaml"
        suite_file.write_text(
            textwrap.dedent("""\
            name: test
            skills:
              - min_grade: B
            """)
        )
        with pytest.raises(SuiteLoadError, match="missing 'path'"):
            SuiteLoader.load(str(suite_file))

    def test_from_dict(self):
        config = SuiteLoader.from_dict({
            "name": "test",
            "skills": [
                {"path": "a.md", "min_grade": "B"},
            ],
        })
        assert config.name == "test"
        assert len(config.skills) == 1

    def test_from_dict_not_a_dict(self):
        with pytest.raises(SuiteLoadError, match="must be a YAML mapping"):
            SuiteLoader.from_dict("not a dict")  # type: ignore[arg-type]

    def test_skills_not_a_list(self, tmp_path: Path):
        suite_file = tmp_path / "suite.yaml"
        suite_file.write_text(
            textwrap.dedent("""\
            name: test
            skills: "not a list"
            """)
        )
        with pytest.raises(SuiteLoadError, match="must be a list"):
            SuiteLoader.load(str(suite_file))

    def test_skill_entry_invalid_type(self, tmp_path: Path):
        suite_file = tmp_path / "suite.yaml"
        suite_file.write_text(
            textwrap.dedent("""\
            name: test
            skills:
              - 42
            """)
        )
        with pytest.raises(SuiteLoadError, match="must be a string or mapping"):
            SuiteLoader.load(str(suite_file))

    def test_load_with_rubric(self, tmp_path: Path):
        suite_file = tmp_path / "suite.yaml"
        suite_file.write_text(
            textwrap.dedent("""\
            name: test
            skills: []
            rubric: custom_rubric.yaml
            """)
        )
        config = SuiteLoader.load(str(suite_file))
        assert config.rubric == "custom_rubric.yaml"


# ============================================================================
# SuiteRunner
# ============================================================================


class TestSuiteRunner:
    """Tests for suite execution with mocked pipeline."""

    @pytest.fixture
    def mock_runner_deps(self):
        """Create mock config, rubric, pipeline_config."""
        config = MagicMock()
        config.defaults = MagicMock()
        rubric = MagicMock()
        return config, rubric

    @pytest.mark.asyncio
    async def test_run_all_pass(self, mock_runner_deps):
        config, rubric = mock_runner_deps
        runner = SuiteRunner(config=config, rubric=rubric)

        eval_result = _make_eval_result("A", 0.92)

        with patch("md_evals.pipeline.runner.PipelineRunner") as MockPR:
            mock_pr_instance = MagicMock()
            mock_pr_instance.run = AsyncMock(return_value=eval_result)
            MockPR.return_value = mock_pr_instance

            suite = SuiteConfig(
                name="test",
                skills=[
                    SkillEntry("a.md", "B"),
                    SkillEntry("b.md", "C"),
                ],
            )
            result = await runner.run(suite)

        assert result.passed is True
        assert result.total_skills == 2
        assert result.passed_skills == 2
        assert result.failed_skills == 0

    @pytest.mark.asyncio
    async def test_run_with_failure(self, mock_runner_deps):
        config, rubric = mock_runner_deps
        runner = SuiteRunner(config=config, rubric=rubric)

        eval_result = _make_eval_result("C", 0.55)

        with patch("md_evals.pipeline.runner.PipelineRunner") as MockPR:
            mock_pr_instance = MagicMock()
            mock_pr_instance.run = AsyncMock(return_value=eval_result)
            MockPR.return_value = mock_pr_instance

            suite = SuiteConfig(
                name="test",
                skills=[
                    SkillEntry("a.md", "A"),  # C < A → fail
                ],
            )
            result = await runner.run(suite)

        assert result.passed is False
        assert result.failed_skills == 1

    @pytest.mark.asyncio
    async def test_run_handles_exception(self, mock_runner_deps):
        config, rubric = mock_runner_deps
        runner = SuiteRunner(config=config, rubric=rubric)

        with patch("md_evals.pipeline.runner.PipelineRunner") as MockPR:
            mock_pr_instance = MagicMock()
            mock_pr_instance.run = AsyncMock(side_effect=RuntimeError("boom"))
            MockPR.return_value = mock_pr_instance

            suite = SuiteConfig(
                name="test",
                skills=[SkillEntry("broken.md", "C")],
            )
            result = await runner.run(suite)

        assert result.passed is False
        assert result.failed_skills == 1
        assert result.results[0][1].overall_grade == "F"

    @pytest.mark.asyncio
    async def test_run_empty_suite(self, mock_runner_deps):
        config, rubric = mock_runner_deps
        runner = SuiteRunner(config=config, rubric=rubric)

        with patch("md_evals.pipeline.runner.PipelineRunner") as MockPR:
            MockPR.return_value = MagicMock()

            suite = SuiteConfig(name="empty", skills=[])
            result = await runner.run(suite)

        assert result.passed is True
        assert result.total_skills == 0
