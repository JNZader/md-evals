"""T-18: Tests for CLI flag precedence: --collect-usage-metrics / --no-collect-usage-metrics.

Phase 6 — Verifies the 4 combinations of CLI × YAML per spec REQ-04-S1 to S4.

Covers: AC-16 (CLI flag precedence over YAML).
"""

from unittest.mock import patch, MagicMock, AsyncMock

from md_evals.cli import app
from md_evals.models import ExecutionResult, LLMResponse


def _make_result() -> ExecutionResult:
    """Create a minimal ExecutionResult for CLI tests."""
    return ExecutionResult(
        treatment="CONTROL",
        test="test_1",
        prompt="test",
        response=LLMResponse(
            content="response",
            model="gpt-4o",
            provider="openai",
            tokens=10,
            duration_ms=500,
        ),
        passed=True,
        evaluator_results=[],
        timestamp="2026-03-15T14:30:22Z",
    )


class TestUsageMetricsCLIPrecedence:
    """REQ-04: Verify CLI flag precedence over YAML config.

    4 scenarios:
    S1: CLI not passed + YAML false/absent → off
    S2: CLI --collect-usage-metrics + YAML false → on (CLI wins)
    S3: CLI not passed + YAML true → on
    S4: CLI --no-collect-usage-metrics + YAML true → off (CLI wins)
    """

    def test_s1_no_cli_yaml_false(self, tmp_path):
        """REQ-04-S1: No CLI flag + YAML false → include_usage_metrics = False."""
        from typer.testing import CliRunner

        eval_file = tmp_path / "eval.yaml"
        eval_file.write_text("""
name: Test
defaults:
  provider: openai
  model: gpt-4o
treatments:
  CONTROL:
    skill_path: null
tests:
  - name: test1
    prompt: "test"
output:
  include_usage_metrics: false
""")

        with patch("md_evals.cli.LLMAdapter"), \
             patch("md_evals.cli.ExecutionEngine") as mock_engine, \
             patch("md_evals.cli.Reporter") as mock_reporter_class:

            mock_engine_instance = MagicMock()
            mock_engine_instance.run_all = AsyncMock(return_value=[_make_result()])
            mock_engine.return_value = mock_engine_instance

            mock_reporter = MagicMock()
            mock_reporter_class.return_value = mock_reporter

            runner = CliRunner()
            runner.invoke(app, [
                "run", "--config", str(eval_file), "--no-lint"
            ])

            # Verify the Reporter was created with config where flag is off
            config_used = mock_reporter_class.call_args[0][0]
            assert config_used.output.include_usage_metrics is False

    def test_s1_no_cli_yaml_absent(self, tmp_path):
        """REQ-04-S1: No CLI flag + YAML absent → include_usage_metrics = False (default)."""
        from typer.testing import CliRunner

        eval_file = tmp_path / "eval.yaml"
        eval_file.write_text("""
name: Test
defaults:
  provider: openai
  model: gpt-4o
treatments:
  CONTROL:
    skill_path: null
tests:
  - name: test1
    prompt: "test"
""")

        with patch("md_evals.cli.LLMAdapter"), \
             patch("md_evals.cli.ExecutionEngine") as mock_engine, \
             patch("md_evals.cli.Reporter") as mock_reporter_class:

            mock_engine_instance = MagicMock()
            mock_engine_instance.run_all = AsyncMock(return_value=[_make_result()])
            mock_engine.return_value = mock_engine_instance

            mock_reporter = MagicMock()
            mock_reporter_class.return_value = mock_reporter

            runner = CliRunner()
            runner.invoke(app, [
                "run", "--config", str(eval_file), "--no-lint"
            ])

            config_used = mock_reporter_class.call_args[0][0]
            assert config_used.output.include_usage_metrics is False

    def test_s2_cli_on_yaml_false(self, tmp_path):
        """REQ-04-S2: CLI --collect-usage-metrics + YAML false → on (CLI wins)."""
        from typer.testing import CliRunner

        eval_file = tmp_path / "eval.yaml"
        eval_file.write_text("""
name: Test
defaults:
  provider: openai
  model: gpt-4o
treatments:
  CONTROL:
    skill_path: null
tests:
  - name: test1
    prompt: "test"
output:
  include_usage_metrics: false
""")

        with patch("md_evals.cli.LLMAdapter"), \
             patch("md_evals.cli.ExecutionEngine") as mock_engine, \
             patch("md_evals.cli.Reporter") as mock_reporter_class:

            mock_engine_instance = MagicMock()
            mock_engine_instance.run_all = AsyncMock(return_value=[_make_result()])
            mock_engine.return_value = mock_engine_instance

            mock_reporter = MagicMock()
            mock_reporter_class.return_value = mock_reporter

            runner = CliRunner()
            runner.invoke(app, [
                "run", "--config", str(eval_file),
                "--collect-usage-metrics",
                "--no-lint"
            ])

            config_used = mock_reporter_class.call_args[0][0]
            assert config_used.output.include_usage_metrics is True

    def test_s3_no_cli_yaml_true(self, tmp_path):
        """REQ-04-S3: No CLI flag + YAML true → on."""
        from typer.testing import CliRunner

        eval_file = tmp_path / "eval.yaml"
        eval_file.write_text("""
name: Test
defaults:
  provider: openai
  model: gpt-4o
treatments:
  CONTROL:
    skill_path: null
tests:
  - name: test1
    prompt: "test"
output:
  include_usage_metrics: true
""")

        with patch("md_evals.cli.LLMAdapter"), \
             patch("md_evals.cli.ExecutionEngine") as mock_engine, \
             patch("md_evals.cli.Reporter") as mock_reporter_class:

            mock_engine_instance = MagicMock()
            mock_engine_instance.run_all = AsyncMock(return_value=[_make_result()])
            mock_engine.return_value = mock_engine_instance

            mock_reporter = MagicMock()
            mock_reporter_class.return_value = mock_reporter

            runner = CliRunner()
            runner.invoke(app, [
                "run", "--config", str(eval_file), "--no-lint"
            ])

            config_used = mock_reporter_class.call_args[0][0]
            assert config_used.output.include_usage_metrics is True

    def test_s4_cli_off_yaml_true(self, tmp_path):
        """REQ-04-S4: CLI --no-collect-usage-metrics + YAML true → off (CLI wins)."""
        from typer.testing import CliRunner

        eval_file = tmp_path / "eval.yaml"
        eval_file.write_text("""
name: Test
defaults:
  provider: openai
  model: gpt-4o
treatments:
  CONTROL:
    skill_path: null
tests:
  - name: test1
    prompt: "test"
output:
  include_usage_metrics: true
""")

        with patch("md_evals.cli.LLMAdapter"), \
             patch("md_evals.cli.ExecutionEngine") as mock_engine, \
             patch("md_evals.cli.Reporter") as mock_reporter_class:

            mock_engine_instance = MagicMock()
            mock_engine_instance.run_all = AsyncMock(return_value=[_make_result()])
            mock_engine.return_value = mock_engine_instance

            mock_reporter = MagicMock()
            mock_reporter_class.return_value = mock_reporter

            runner = CliRunner()
            runner.invoke(app, [
                "run", "--config", str(eval_file),
                "--no-collect-usage-metrics",
                "--no-lint"
            ])

            config_used = mock_reporter_class.call_args[0][0]
            assert config_used.output.include_usage_metrics is False


class TestCLIHelpShowsFlag:
    """Verify --collect-usage-metrics appears in help output."""

    def test_run_help_shows_usage_metrics_flag(self):
        """AC-16: --collect-usage-metrics visible in --help.

        Note: Typer may truncate long option names with '…' in narrow terminals.
        We check for the truncated prefix to handle this.
        """
        from typer.testing import CliRunner
        import re

        runner = CliRunner()
        result = runner.invoke(app, ["run", "--help"])

        # Strip ANSI codes and normalize whitespace
        clean = re.sub(r'\x1b\[[0-9;]*m', '', result.stdout)
        condensed = re.sub(r'\s+', ' ', clean)

        # Typer may truncate to "--collect-usage-me…" in narrow terminal
        assert "collect-usage-me" in condensed, (
            "Expected '--collect-usage-metrics' (possibly truncated) in help output"
        )
        assert "no-collect-usag" in condensed, (
            "Expected '--no-collect-usage-metrics' (possibly truncated) in help output"
        )
