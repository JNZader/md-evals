"""Comprehensive tests for md_evals.plugin_eval module.

Tests cover:
  - PluginManifest dataclass
  - PluginEvalResult dataclass
  - PluginEvaluator.load_manifest (JSON parsing, validation)
  - PluginEvaluator.discover_skills (directory scanning)
  - PluginEvaluator._aggregate (grade aggregation)
  - PluginEvaluator.evaluate (mocked pipeline)
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from md_evals.plugin_eval import (
    PluginError,
    PluginEvaluator,
    PluginEvalResult,
    PluginManifest,
)
from md_evals.scoring import DimensionScore, EvalMetadata, EvalResult


# ─── Fixtures ───


def _make_eval_result(grade: str = "B", score: float = 0.78) -> EvalResult:
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


def _make_plugin_dir(tmp_path: Path, with_manifest: bool = True) -> Path:
    """Create a minimal plugin directory structure."""
    plugin_dir = tmp_path / "my-plugin"
    plugin_dir.mkdir()

    if with_manifest:
        manifest = {
            "name": "test-plugin",
            "description": "A test plugin",
            "version": "1.0.0",
            "skills": ["skills/go-backend/SKILL.md", "skills/fastapi/SKILL.md"],
            "commands": [],
        }
        (plugin_dir / "plugin.json").write_text(json.dumps(manifest))

    # Create skills directory
    (plugin_dir / "skills" / "go-backend").mkdir(parents=True)
    (plugin_dir / "skills" / "go-backend" / "SKILL.md").write_text(
        "# Go Backend\n\n## Description\nGo patterns\n\n## Rules\n- Rule 1\n\n## Examples\n"
    )

    (plugin_dir / "skills" / "fastapi").mkdir(parents=True)
    (plugin_dir / "skills" / "fastapi" / "SKILL.md").write_text(
        "# FastAPI\n\n## Description\nFastAPI patterns\n\n## Rules\n- Rule 1\n\n## Examples\n"
    )

    return plugin_dir


# ============================================================================
# PluginManifest
# ============================================================================


class TestPluginManifest:
    def test_defaults(self):
        m = PluginManifest()
        assert m.name == ""
        assert m.version == ""
        assert m.skills == []
        assert m.commands == []

    def test_with_values(self):
        m = PluginManifest(
            name="my-plugin",
            description="desc",
            version="1.0.0",
            skills=["s1.md"],
            commands=["c1.py"],
        )
        assert m.name == "my-plugin"
        assert len(m.skills) == 1


# ============================================================================
# PluginEvalResult
# ============================================================================


class TestPluginEvalResult:
    def test_defaults(self):
        r = PluginEvalResult(plugin_name="test", manifest_valid=True)
        assert r.plugin_name == "test"
        assert r.manifest_valid is True
        assert r.skill_results == []
        assert r.aggregate_grade == "F"
        assert r.aggregate_score == 0.0


# ============================================================================
# PluginEvaluator.load_manifest
# ============================================================================


class TestLoadManifest:
    def test_valid_manifest(self, tmp_path: Path):
        plugin_dir = _make_plugin_dir(tmp_path)
        manifest = PluginEvaluator.load_manifest(str(plugin_dir))
        assert manifest.name == "test-plugin"
        assert manifest.version == "1.0.0"
        assert len(manifest.skills) == 2

    def test_missing_manifest(self, tmp_path: Path):
        plugin_dir = tmp_path / "no-manifest"
        plugin_dir.mkdir()
        with pytest.raises(PluginError, match="plugin.json not found"):
            PluginEvaluator.load_manifest(str(plugin_dir))

    def test_invalid_json(self, tmp_path: Path):
        plugin_dir = tmp_path / "bad-json"
        plugin_dir.mkdir()
        (plugin_dir / "plugin.json").write_text("{{{invalid")
        with pytest.raises(PluginError, match="Failed to parse"):
            PluginEvaluator.load_manifest(str(plugin_dir))

    def test_non_object_json(self, tmp_path: Path):
        plugin_dir = tmp_path / "array-json"
        plugin_dir.mkdir()
        (plugin_dir / "plugin.json").write_text("[1, 2, 3]")
        with pytest.raises(PluginError, match="must be a JSON object"):
            PluginEvaluator.load_manifest(str(plugin_dir))


# ============================================================================
# PluginEvaluator.discover_skills
# ============================================================================


class TestDiscoverSkills:
    def test_discover_from_manifest_and_dir(self, tmp_path: Path):
        plugin_dir = _make_plugin_dir(tmp_path)
        skills = PluginEvaluator.discover_skills(str(plugin_dir))
        # Should find 2 skills from manifest + directory scan (deduplicated)
        assert len(skills) == 2
        assert any("go-backend" in s for s in skills)
        assert any("fastapi" in s for s in skills)

    def test_discover_without_manifest(self, tmp_path: Path):
        plugin_dir = _make_plugin_dir(tmp_path, with_manifest=False)
        skills = PluginEvaluator.discover_skills(str(plugin_dir))
        assert len(skills) == 2

    def test_discover_root_skill(self, tmp_path: Path):
        plugin_dir = tmp_path / "simple-plugin"
        plugin_dir.mkdir()
        (plugin_dir / "SKILL.md").write_text("# Root Skill")
        skills = PluginEvaluator.discover_skills(str(plugin_dir))
        assert len(skills) == 1

    def test_discover_empty_dir(self, tmp_path: Path):
        plugin_dir = tmp_path / "empty-plugin"
        plugin_dir.mkdir()
        skills = PluginEvaluator.discover_skills(str(plugin_dir))
        assert len(skills) == 0

    def test_discover_commands_dir(self, tmp_path: Path):
        plugin_dir = tmp_path / "cmd-plugin"
        plugin_dir.mkdir()
        (plugin_dir / "commands").mkdir()
        (plugin_dir / "commands" / "SKILL.md").write_text("# Command Skill")
        skills = PluginEvaluator.discover_skills(str(plugin_dir))
        assert len(skills) == 1

    def test_deduplication(self, tmp_path: Path):
        """Skills listed in manifest AND found in directory should not be duplicated."""
        plugin_dir = _make_plugin_dir(tmp_path)
        skills = PluginEvaluator.discover_skills(str(plugin_dir))
        # All paths should be unique
        assert len(skills) == len(set(skills))


# ============================================================================
# PluginEvaluator._aggregate
# ============================================================================


class TestAggregate:
    def test_aggregate_empty(self):
        score, grade = PluginEvaluator._aggregate([])
        assert score == 0.0
        assert grade == "F"

    def test_aggregate_single(self):
        result = _make_eval_result("A", 0.90)
        score, grade = PluginEvaluator._aggregate([result])
        assert score == 0.9
        assert grade == "A"

    def test_aggregate_multiple(self):
        r1 = _make_eval_result("A", 0.90)
        r2 = _make_eval_result("B", 0.75)
        score, grade = PluginEvaluator._aggregate([r1, r2])
        assert 0.82 < score < 0.83  # avg of 0.90 and 0.75
        assert grade == "B"


# ============================================================================
# PluginEvaluator.evaluate (mocked)
# ============================================================================


class TestPluginEvaluate:
    @pytest.mark.asyncio
    async def test_evaluate_success(self, tmp_path: Path):
        plugin_dir = _make_plugin_dir(tmp_path)
        config = MagicMock()
        config.defaults = MagicMock()
        rubric = MagicMock()

        evaluator = PluginEvaluator(config=config, rubric=rubric)
        eval_result = _make_eval_result("A", 0.90)

        with patch("md_evals.pipeline.runner.PipelineRunner") as MockPR:
            mock_instance = MagicMock()
            mock_instance.run = AsyncMock(return_value=eval_result)
            MockPR.return_value = mock_instance

            result = await evaluator.evaluate(str(plugin_dir))

        assert result.plugin_name == "test-plugin"
        assert result.manifest_valid is True
        assert len(result.skill_results) == 2
        assert result.aggregate_grade == "A"

    @pytest.mark.asyncio
    async def test_evaluate_no_skills(self, tmp_path: Path):
        plugin_dir = tmp_path / "empty"
        plugin_dir.mkdir()

        evaluator = PluginEvaluator()
        result = await evaluator.evaluate(str(plugin_dir))

        assert result.manifest_valid is False
        assert result.aggregate_grade == "F"
        assert len(result.skill_results) == 0
