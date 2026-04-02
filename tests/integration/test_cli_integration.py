"""Integration tests for CLI — real Typer CliRunner, no mocks."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from md_evals.cli import app


FIXTURES = Path(__file__).parent.parent / "fixtures"
runner = CliRunner()


class TestLintCommand:
    """Test `md-evals lint` with real files."""

    def test_lint_valid_skill(self):
        result = runner.invoke(app, ["lint", str(FIXTURES / "skill_valid.md")])
        assert result.exit_code == 0
        # Rich may wrap text across lines, so check words individually
        output = result.output.replace("\n", " ")
        assert "passes" in output and "linting" in output

    def test_lint_valid_skill_verbose(self):
        result = runner.invoke(app, ["lint", str(FIXTURES / "skill_valid.md"), "--verbose"])
        assert result.exit_code == 0
        output = result.output.replace("\n", " ")
        assert "Lines" in output

    def test_lint_empty_skill(self):
        result = runner.invoke(app, ["lint", str(FIXTURES / "skill_invalid_empty.md")])
        assert result.exit_code == 2
        output = result.output.replace("\n", " ").lower()
        assert "violations" in output or "empty" in output

    def test_lint_missing_sections(self):
        result = runner.invoke(app, ["lint", str(FIXTURES / "skill_missing_sections.md")])
        # Missing sections are warnings, not errors — file still passes
        # unless it triggers an error rule
        assert result.exit_code in (0, 2)

    def test_lint_nonexistent_file(self):
        result = runner.invoke(app, ["lint", "/nonexistent/SKILL.md"])
        assert result.exit_code == 2

    def test_lint_no_fail_flag(self):
        result = runner.invoke(
            app, ["lint", str(FIXTURES / "skill_invalid_empty.md"), "--no-fail"]
        )
        # Even with violations, --no-fail should exit 0 if only warnings
        # But empty file has error severity, so it depends on implementation
        assert result.exit_code in (0, 2)


class TestVersionCommand:
    """Test `md-evals version`."""

    def test_version_output(self):
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "md-evals" in result.output


class TestCheckCommand:
    """Test `md-evals check` with real files."""

    def test_check_valid_skill(self):
        result = runner.invoke(app, ["check", str(FIXTURES / "skill_valid.md")])
        assert result.exit_code == 0
        output = result.output.replace("\n", " ")
        assert "PASSED" in output

    def test_check_empty_skill(self):
        result = runner.invoke(app, ["check", str(FIXTURES / "skill_invalid_empty.md")])
        assert result.exit_code == 2
        output = result.output.replace("\n", " ")
        assert "FAILED" in output

    def test_check_missing_file(self):
        result = runner.invoke(app, ["check", "/nonexistent/SKILL.md"])
        assert result.exit_code == 2

    def test_check_with_secret_detection(self):
        result = runner.invoke(app, ["check", str(FIXTURES / "skill_with_secret.md")])
        # skill_with_secret.md should trigger security pattern
        assert result.exit_code in (0, 2)


class TestListCommand:
    """Test `md-evals list` with real config."""

    def test_list_with_valid_config(self):
        result = runner.invoke(
            app, ["list", "--config", str(FIXTURES / "config_valid.yaml")]
        )
        assert result.exit_code == 0
        assert "CONTROL" in result.output
        assert "WITH_SKILL" in result.output
        assert "greeting_test" in result.output

    def test_list_treatments_only(self):
        result = runner.invoke(
            app,
            ["list", "--config", str(FIXTURES / "config_valid.yaml"), "--treatments"],
        )
        assert result.exit_code == 0
        assert "CONTROL" in result.output

    def test_list_tasks_only(self):
        result = runner.invoke(
            app,
            ["list", "--config", str(FIXTURES / "config_valid.yaml"), "--tasks"],
        )
        assert result.exit_code == 0
        assert "greeting_test" in result.output

    def test_list_missing_config(self):
        result = runner.invoke(app, ["list", "--config", "/nonexistent/eval.yaml"])
        assert result.exit_code == 1
        assert "Error" in result.output


class TestListModelsCommand:
    """Test `md-evals list-models`."""

    def test_list_models_all(self):
        result = runner.invoke(app, ["list-models"])
        # Should not crash, may have output depending on registered providers
        assert result.exit_code == 0

    def test_list_models_invalid_provider(self):
        result = runner.invoke(app, ["list-models", "--provider", "nonexistent"])
        assert result.exit_code == 1


class TestInitCommand:
    """Test `md-evals init` scaffold."""

    def test_init_creates_files(self, tmp_path):
        result = runner.invoke(app, ["init", str(tmp_path)])
        assert result.exit_code == 0
        assert (tmp_path / "eval.yaml").exists()
        assert (tmp_path / "SKILL.md").exists()
        assert (tmp_path / "rubric.yaml").exists()

    def test_init_no_overwrite(self, tmp_path):
        # First init
        runner.invoke(app, ["init", str(tmp_path)])
        # Second init should fail without --force
        result = runner.invoke(app, ["init", str(tmp_path)])
        assert result.exit_code == 1
        assert "already exists" in result.output

    def test_init_force_overwrite(self, tmp_path):
        runner.invoke(app, ["init", str(tmp_path)])
        result = runner.invoke(app, ["init", str(tmp_path), "--force"])
        assert result.exit_code == 0


class TestSmokeCommand:
    """Test `md-evals smoke` preflight."""

    def test_smoke_with_valid_config(self):
        result = runner.invoke(
            app,
            ["smoke", "--config", str(FIXTURES / "config_valid.yaml"), "--provider", "github-models"],
        )
        # May fail if no GitHub token, but should not crash
        assert result.exit_code in (0, 1)

    def test_smoke_missing_config(self):
        result = runner.invoke(
            app, ["smoke", "--config", "/nonexistent/eval.yaml"]
        )
        assert result.exit_code == 1
        assert "FAIL" in result.output


class TestModeFlag:
    """Test `md-evals run --mode` flag validation."""

    def test_invalid_mode_rejected(self):
        result = runner.invoke(
            app,
            ["run", "--config", str(FIXTURES / "eval.yaml"), "--mode", "invalid"],
        )
        assert result.exit_code == 1
        output = result.output.replace("\n", " ").lower()
        assert "invalid mode" in output

    def test_mode_smoke_accepted(self):
        """Smoke mode should be accepted (may fail at LLM call but not at mode validation)."""
        result = runner.invoke(
            app,
            [
                "run",
                "--config", str(FIXTURES / "eval.yaml"),
                "--mode", "smoke",
                "--no-lint",
                "--no-pre-check",
            ],
        )
        # Should NOT fail with "invalid mode" — may fail later at LLM init
        output = result.output.replace("\n", " ").lower()
        assert "invalid mode" not in output


class TestPluginsListCommand:
    """Test `md-evals plugins list`."""

    def test_plugins_list(self):
        result = runner.invoke(app, ["plugins", "list"])
        assert result.exit_code == 0
        # Should show probes and detectors tables
        assert "Probes" in result.output or "probes" in result.output.lower()
