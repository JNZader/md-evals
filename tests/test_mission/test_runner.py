"""Tests for MissionRunner."""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
import yaml
from pydantic import ValidationError

from md_evals.llm import LLMError, LLMTimeoutError
from md_evals.mission.models import (
    MissionConfig,
    MissionPassCriteria,
    MissionTestCase,
)
from md_evals.mission.runner import MissionLoadError, MissionRunner


class TestMissionLoad:
    """Tests for MissionRunner.load()."""

    def test_load_valid_yaml(self, tmp_path):
        mission_yaml = tmp_path / "mission.yaml"
        mission_yaml.write_text(
            yaml.dump(
                {
                    "name": "test-mission",
                    "test_cases": [
                        {
                            "name": "basic",
                            "prompt": "Say hello",
                            "pass_criteria": [
                                {
                                    "type": "regex",
                                    "name": "has_hello",
                                    "pattern": "[Hh]ello",
                                }
                            ],
                        }
                    ],
                }
            )
        )
        config = MissionRunner.load(str(mission_yaml))
        assert config.name == "test-mission"
        assert len(config.test_cases) == 1
        assert config.test_cases[0].name == "basic"

    def test_load_missing_file(self):
        with pytest.raises(MissionLoadError, match="not found"):
            MissionRunner.load("/nonexistent/mission.yaml")

    def test_load_invalid_yaml(self, tmp_path):
        bad = tmp_path / "bad.yaml"
        bad.write_text(": : : invalid yaml {{{")
        with pytest.raises(MissionLoadError, match="Invalid YAML"):
            MissionRunner.load(str(bad))

    def test_load_empty_file(self, tmp_path):
        empty = tmp_path / "empty.yaml"
        empty.write_text("")
        with pytest.raises(MissionLoadError, match="Empty"):
            MissionRunner.load(str(empty))

    def test_load_invalid_schema(self, tmp_path):
        bad_schema = tmp_path / "bad_schema.yaml"
        bad_schema.write_text(yaml.dump({"invalid_field": "value"}))
        with pytest.raises(MissionLoadError, match="Invalid mission config"):
            MissionRunner.load(str(bad_schema))

    def test_load_full_config(self, tmp_path):
        mission_yaml = tmp_path / "full.yaml"
        mission_yaml.write_text(
            yaml.dump(
                {
                    "name": "full-mission",
                    "version": "2.0",
                    "description": "A complete mission",
                    "skill_under_test": "./SKILL.md",
                    "model": "claude-3",
                    "provider": "anthropic",
                    "schedule_hint": "0 0 * * 0",
                    "results_dir": ".results",
                    "tags": ["weekly"],
                    "test_cases": [
                        {
                            "name": "t1",
                            "prompt": "Hello {name}",
                            "variables": {"name": "World"},
                            "pass_criteria": [
                                {"type": "regex", "name": "check", "pattern": "Hello"}
                            ],
                        }
                    ],
                }
            )
        )
        config = MissionRunner.load(str(mission_yaml))
        assert config.version == "2.0"
        assert config.skill_under_test == "./SKILL.md"
        assert config.schedule_hint == "0 0 * * 0"


class TestMissionRunDeterministic:
    """Tests for MissionRunner.run() with deterministic criteria (no LLM)."""

    @pytest.mark.asyncio
    async def test_regex_pass(self):
        config = MissionConfig(
            name="regex-test",
            test_cases=[
                MissionTestCase(
                    name="check_hello",
                    prompt="Say hello",
                    pass_criteria=[
                        MissionPassCriteria(
                            type="regex", name="has_hello", pattern="[Hh]ello"
                        )
                    ],
                )
            ],
        )
        # Without LLM adapter, response_content is empty, regex won't match
        runner = MissionRunner(llm_adapter=None)
        result = await runner.run(config)
        assert result.mission_name == "regex-test"
        assert len(result.test_results) == 1
        # No LLM = empty content = regex fails
        assert result.test_results[0].passed is False

    @pytest.mark.asyncio
    async def test_regex_pass_on_no_match(self):
        """Test regex with pass_on_match=False (should pass when pattern NOT found)."""
        config = MissionConfig(
            name="negative-test",
            test_cases=[
                MissionTestCase(
                    name="no_profanity",
                    prompt="Be polite",
                    pass_criteria=[
                        MissionPassCriteria(
                            type="regex",
                            name="no_bad_words",
                            pattern="badword",
                            pass_on_match=False,
                        )
                    ],
                )
            ],
        )
        runner = MissionRunner(llm_adapter=None)
        result = await runner.run(config)
        # Empty content, pattern not found, pass_on_match=False -> passes
        assert result.test_results[0].passed is True

    @pytest.mark.asyncio
    async def test_exact_match_case_insensitive(self):
        config = MissionConfig(
            name="exact-test",
            test_cases=[
                MissionTestCase(
                    name="check_text",
                    prompt="test",
                    pass_criteria=[
                        MissionPassCriteria(
                            type="exact-match",
                            name="has_text",
                            expected="HELLO",
                            case_sensitive=False,
                        )
                    ],
                )
            ],
        )
        runner = MissionRunner(llm_adapter=None)
        result = await runner.run(config)
        # Empty content, no match
        assert result.test_results[0].passed is False

    @pytest.mark.asyncio
    async def test_no_criteria_passes(self):
        """Test case with no criteria should pass."""
        config = MissionConfig(
            name="no-criteria",
            test_cases=[
                MissionTestCase(name="empty", prompt="anything")
            ],
        )
        runner = MissionRunner(llm_adapter=None)
        result = await runner.run(config)
        assert result.test_results[0].passed is True
        assert result.test_results[0].score == 1.0

    @pytest.mark.asyncio
    async def test_summary_calculation(self):
        config = MissionConfig(
            name="summary-test",
            test_cases=[
                MissionTestCase(
                    name="pass1",
                    prompt="test",
                    pass_criteria=[
                        MissionPassCriteria(
                            type="regex",
                            name="always_pass",
                            pattern="nonexistent",
                            pass_on_match=False,
                        )
                    ],
                ),
                MissionTestCase(
                    name="fail1",
                    prompt="test",
                    pass_criteria=[
                        MissionPassCriteria(
                            type="regex",
                            name="always_fail",
                            pattern="must_match",
                            pass_on_match=True,
                        )
                    ],
                ),
            ],
        )
        runner = MissionRunner(llm_adapter=None)
        result = await runner.run(config)
        assert result.summary.total == 2
        assert result.summary.passed == 1
        assert result.summary.failed == 1
        assert result.summary.pass_rate == 0.5

    @pytest.mark.asyncio
    async def test_empty_mission(self):
        config = MissionConfig(name="empty-mission", test_cases=[])
        runner = MissionRunner(llm_adapter=None)
        result = await runner.run(config)
        assert result.summary.total == 0
        assert result.summary.pass_rate == 0.0

    @pytest.mark.asyncio
    async def test_multiple_criteria_all_must_pass(self):
        config = MissionConfig(
            name="multi-criteria",
            test_cases=[
                MissionTestCase(
                    name="multi",
                    prompt="test",
                    pass_criteria=[
                        MissionPassCriteria(
                            type="regex",
                            name="c1",
                            pattern="nonexistent",
                            pass_on_match=False,
                        ),
                        MissionPassCriteria(
                            type="regex",
                            name="c2",
                            pattern="also_nonexistent",
                            pass_on_match=False,
                        ),
                    ],
                )
            ],
        )
        runner = MissionRunner(llm_adapter=None)
        result = await runner.run(config)
        assert result.test_results[0].passed is True


class TestMissionSaveResult:
    """Tests for MissionRunner.save_result()."""

    @pytest.mark.asyncio
    async def test_save_and_load(self, tmp_path):
        config = MissionConfig(
            name="save-test",
            results_dir=str(tmp_path / "results"),
            test_cases=[
                MissionTestCase(name="t1", prompt="test")
            ],
        )
        runner = MissionRunner(llm_adapter=None)
        result = await runner.run(config)
        saved_path = runner.save_result(result, config.results_dir)

        assert saved_path.exists()
        with open(saved_path) as f:
            data = json.load(f)
        assert data["mission_name"] == "save-test"
        assert len(data["test_results"]) == 1

    @pytest.mark.asyncio
    async def test_save_creates_directory(self, tmp_path):
        deep_dir = str(tmp_path / "a" / "b" / "c")
        config = MissionConfig(
            name="deep-save",
            results_dir=deep_dir,
            test_cases=[],
        )
        runner = MissionRunner(llm_adapter=None)
        result = await runner.run(config)
        saved_path = runner.save_result(result, deep_dir)
        assert saved_path.exists()


class TestNarrowedExceptions:
    """Verify that specific exceptions are caught and generic ones propagate."""

    def test_load_catches_validation_error(self, tmp_path):
        """Pydantic ValidationError is caught and wrapped as MissionLoadError."""
        bad_schema = tmp_path / "bad.yaml"
        # Missing required 'name' field triggers ValidationError
        bad_schema.write_text(yaml.dump({"test_cases": "not_a_list"}))
        with pytest.raises(MissionLoadError, match="Invalid mission config"):
            MissionRunner.load(str(bad_schema))

    def test_load_catches_type_error(self, tmp_path):
        """TypeError from unpacking is caught and wrapped as MissionLoadError."""
        bad = tmp_path / "bad.yaml"
        # A list instead of a dict causes TypeError on **data
        bad.write_text("- item1\n- item2\n")
        with pytest.raises(MissionLoadError, match="Invalid mission config"):
            MissionRunner.load(str(bad))

    def test_load_propagates_unexpected_exceptions(self, tmp_path):
        """Exceptions NOT in the narrow list propagate uncaught."""
        valid = tmp_path / "valid.yaml"
        valid.write_text(yaml.dump({"name": "test", "test_cases": []}))
        with patch(
            "md_evals.mission.runner.MissionConfig",
            side_effect=RuntimeError("unexpected"),
        ):
            with pytest.raises(RuntimeError, match="unexpected"):
                MissionRunner.load(str(valid))

    @pytest.mark.asyncio
    async def test_run_catches_llm_error(self):
        """LLMError from the adapter is caught, test marked as failed."""
        adapter = AsyncMock()
        adapter.complete = AsyncMock(side_effect=LLMError("API rate limit"))
        config = MissionConfig(
            name="llm-err",
            test_cases=[
                MissionTestCase(
                    name="t1",
                    prompt="hello",
                    pass_criteria=[
                        MissionPassCriteria(type="regex", name="c1", pattern="hi"),
                    ],
                )
            ],
        )
        runner = MissionRunner(llm_adapter=adapter)
        with patch("md_evals.llm.inject_skill", return_value=("hello", None)):
            result = await runner.run(config)
        assert result.test_results[0].passed is False
        assert "LLM error" in result.test_results[0].error

    @pytest.mark.asyncio
    async def test_run_catches_llm_timeout_error(self):
        """LLMTimeoutError from the adapter is caught, test marked as failed."""
        adapter = AsyncMock()
        adapter.complete = AsyncMock(
            side_effect=LLMTimeoutError({"message": "timed out"})
        )
        config = MissionConfig(
            name="timeout-err",
            test_cases=[
                MissionTestCase(
                    name="t1",
                    prompt="hello",
                    pass_criteria=[
                        MissionPassCriteria(type="regex", name="c1", pattern="hi"),
                    ],
                )
            ],
        )
        runner = MissionRunner(llm_adapter=adapter)
        with patch("md_evals.llm.inject_skill", return_value=("hello", None)):
            result = await runner.run(config)
        assert result.test_results[0].passed is False
        assert "LLM error" in result.test_results[0].error

    @pytest.mark.asyncio
    async def test_run_catches_file_not_found_from_inject_skill(self):
        """FileNotFoundError from inject_skill is caught."""
        adapter = AsyncMock()
        config = MissionConfig(
            name="fnf-err",
            skill_under_test="./nonexistent.md",
            test_cases=[
                MissionTestCase(
                    name="t1",
                    prompt="hello",
                    pass_criteria=[
                        MissionPassCriteria(type="regex", name="c1", pattern="hi"),
                    ],
                )
            ],
        )
        runner = MissionRunner(llm_adapter=adapter)
        with patch(
            "md_evals.llm.inject_skill",
            side_effect=FileNotFoundError("Skill file not found"),
        ):
            result = await runner.run(config)
        assert result.test_results[0].passed is False
        assert "LLM error" in result.test_results[0].error

    @pytest.mark.asyncio
    async def test_run_propagates_unexpected_exceptions(self):
        """Exceptions NOT in the narrow list propagate uncaught from _run_test_case."""
        adapter = AsyncMock()
        config = MissionConfig(
            name="unhandled",
            test_cases=[
                MissionTestCase(
                    name="t1",
                    prompt="hello",
                    pass_criteria=[
                        MissionPassCriteria(type="regex", name="c1", pattern="hi"),
                    ],
                )
            ],
        )
        runner = MissionRunner(llm_adapter=adapter)
        with patch(
            "md_evals.llm.inject_skill",
            side_effect=RuntimeError("unexpected bug"),
        ):
            with pytest.raises(RuntimeError, match="unexpected bug"):
                await runner.run(config)
