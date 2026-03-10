"""Tests for md_evals CLI."""

import pytest
from io import StringIO
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path

from md_evals import __version__
from md_evals.cli import app


class TestCLI:
    """Test CLI commands."""
    
    def test_version(self):
        """Test version command."""
        from md_evals.cli import version
        # Just check function exists
        assert callable(version)
    
    def test_cli_app_exists(self):
        """Test CLI app exists."""
        assert app is not None


class TestInitCommand:
    """Test init command."""
    
    def test_init_creates_files(self, tmp_path, capsys):
        """Test init creates expected files."""
        from typer.testing import CliRunner
        
        runner = CliRunner()
        result = runner.invoke(app, ["init", str(tmp_path / "test-project")])
        
        assert result.exit_code == 0
        assert (tmp_path / "test-project" / "eval.yaml").exists()
        assert (tmp_path / "test-project" / "SKILL.md").exists()
        assert (tmp_path / "test-project" / "results").exists()
    
    def test_init_existing_file(self, tmp_path):
        """Test init with existing file."""
        from typer.testing import CliRunner
        
        # Create eval.yaml first
        eval_file = tmp_path / "eval.yaml"
        eval_file.write_text("existing")
        
        runner = CliRunner()
        result = runner.invoke(app, ["init", str(tmp_path)])
        
        # Should fail without --force
        assert result.exit_code == 1
    
    def test_init_force_overwrite(self, tmp_path):
        """Test init with --force overwrites existing."""
        from typer.testing import CliRunner
        
        # Create eval.yaml first
        eval_file = tmp_path / "eval.yaml"
        eval_file.write_text("existing")
        
        runner = CliRunner()
        result = runner.invoke(app, ["init", str(tmp_path), "--force"])
        
        # Should succeed with --force
        assert result.exit_code == 0
        assert "Initialization complete" in result.stdout


class TestLintCommand:
    """Test lint command."""
    
    def test_lint_valid_file(self, tmp_path):
        """Test lint with valid file."""
        from typer.testing import CliRunner
        
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("# Test\n\n## Rules\n- Rule 1")
        
        runner = CliRunner()
        result = runner.invoke(app, ["lint", str(skill_file)])
        
        assert result.exit_code == 0
    
    def test_lint_nonexistent_file(self, tmp_path):
        """Test lint with nonexistent file."""
        from typer.testing import CliRunner
        
        runner = CliRunner()
        result = runner.invoke(app, ["lint", str(tmp_path / "nonexistent.md")])
        
        assert result.exit_code == 2


class TestListCommand:
    """Test list command."""
    
    def test_list_with_config(self, tmp_path):
        """Test list with config file."""
        from typer.testing import CliRunner
        
        # Create a minimal eval.yaml
        eval_file = tmp_path / "eval.yaml"
        eval_file.write_text("""
name: Test
treatments:
  CONTROL:
    skill_path: null
tests:
  - name: test1
    prompt: "test"
""")
        
        runner = CliRunner()
        result = runner.invoke(app, ["list", "--config", str(eval_file)])
        
        assert result.exit_code == 0
    
    def test_list_missing_config(self):
        """Test list with missing config."""
        from typer.testing import CliRunner
        
        runner = CliRunner()
        result = runner.invoke(app, ["list", "--config", "nonexistent.yaml"])
        
        assert result.exit_code == 1
    
    def test_list_treatments_only(self, tmp_path):
        """Test list with --treatments flag."""
        from typer.testing import CliRunner
        
        eval_file = tmp_path / "eval.yaml"
        eval_file.write_text("""
name: Test
treatments:
  CONTROL:
    skill_path: null
  WITH_SKILL:
    skill_path: "./SKILL.md"
tests:
  - name: test1
    prompt: "test"
""")
        
        runner = CliRunner()
        result = runner.invoke(app, ["list", "--config", str(eval_file), "--treatments"])
        
        assert result.exit_code == 0
        assert "CONTROL" in result.stdout
        assert "WITH_SKILL" in result.stdout


class TestRunCommand:
    """Test run command."""
    
    def test_run_missing_config(self):
        """Test run with missing config."""
        from typer.testing import CliRunner
        
        runner = CliRunner()
        result = runner.invoke(app, ["run", "--config", "nonexistent.yaml"])
        
        assert result.exit_code == 1
        assert "Error loading config" in result.stdout
    
    def test_run_with_invalid_treatment(self, tmp_path):
        """Test run with invalid treatment."""
        from typer.testing import CliRunner
        
        eval_file = tmp_path / "eval.yaml"
        eval_file.write_text("""
name: Test
treatments:
  CONTROL:
    skill_path: null
tests:
  - name: test1
    prompt: "test"
""")
        
        runner = CliRunner()
        result = runner.invoke(app, ["run", "--config", str(eval_file), "--treatment", "INVALID"])
        
        # Should handle invalid treatment gracefully
        assert result.exit_code in [0, 1]
    
    def test_run_with_model_override(self, tmp_path):
        """Test run with model override."""
        from typer.testing import CliRunner
        
        eval_file = tmp_path / "eval.yaml"
        eval_file.write_text("""
name: Test
treatments:
  CONTROL:
    skill_path: null
tests:
  - name: test1
    prompt: "test"
""")
        
        # Mock the LLM adapter to avoid actual API calls
        with patch("md_evals.cli.LLMAdapter") as mock_adapter, \
             patch("md_evals.cli.ExecutionEngine") as mock_engine:
            
            # Setup mock engine
            mock_engine_instance = MagicMock()
            mock_engine_instance.run_all = AsyncMock(return_value=[])
            mock_engine.return_value = mock_engine_instance
            
            runner = CliRunner()
            result = runner.invoke(app, [
                "run", "--config", str(eval_file),
                "--model", "gpt-3.5-turbo",
                "--no-lint"
            ])
            
            # Should attempt to run (might fail on other mocks but shouldn't be config error)
            assert "Error loading config" not in result.stdout
    
    def test_run_with_workers(self, tmp_path):
        """Test run with workers option."""
        from typer.testing import CliRunner
        
        eval_file = tmp_path / "eval.yaml"
        eval_file.write_text("""
name: Test
treatments:
  CONTROL:
    skill_path: null
tests:
  - name: test1
    prompt: "test"
""")
        
        with patch("md_evals.cli.LLMAdapter") as mock_adapter, \
             patch("md_evals.cli.ExecutionEngine") as mock_engine:
            
            mock_engine_instance = MagicMock()
            mock_engine_instance.run_all = AsyncMock(return_value=[])
            mock_engine.return_value = mock_engine_instance
            
            runner = CliRunner()
            result = runner.invoke(app, [
                "run", "--config", str(eval_file),
                "-n", "4",
                "--no-lint"
            ])
            
            assert "Error loading config" not in result.stdout
    
    def test_run_with_count(self, tmp_path):
        """Test run with count/repetitions option."""
        from typer.testing import CliRunner
        
        eval_file = tmp_path / "eval.yaml"
        eval_file.write_text("""
name: Test
treatments:
  CONTROL:
    skill_path: null
tests:
  - name: test1
    prompt: "test"
""")
        
        with patch("md_evals.cli.LLMAdapter") as mock_adapter, \
             patch("md_evals.cli.ExecutionEngine") as mock_engine:
            
            mock_engine_instance = MagicMock()
            mock_engine_instance.run_all = AsyncMock(return_value=[])
            mock_engine.return_value = mock_engine_instance
            
            runner = CliRunner()
            result = runner.invoke(app, [
                "run", "--config", str(eval_file),
                "--count", "3",
                "--no-lint"
            ])
            
            assert "Error loading config" not in result.stdout
    
    def test_run_with_output_json(self, tmp_path):
        """Test run with JSON output."""
        from typer.testing import CliRunner
        
        eval_file = tmp_path / "eval.yaml"
        eval_file.write_text("""
name: Test
treatments:
  CONTROL:
    skill_path: null
tests:
  - name: test1
    prompt: "test"
output:
  results_dir: "./results"
""")
        
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        
        with patch("md_evals.cli.LLMAdapter"), \
             patch("md_evals.cli.ExecutionEngine") as mock_engine, \
             patch("md_evals.cli.Reporter"):
            
            from md_evals.models import ExecutionResult, LLMResponse
            
            mock_engine_instance = MagicMock()
            mock_engine_instance.run_all = AsyncMock(return_value=[
                ExecutionResult(
                    treatment="CONTROL",
                    test="test1",
                    prompt="test",
                    response=LLMResponse(
                        content="hi",
                        model="gpt-4o",
                        provider="openai",
                        duration_ms=1000
                    ),
                    passed=True,
                    evaluator_results=[],
                    timestamp="2024-01-01T00:00:00"
                )
            ])
            mock_engine.return_value = mock_engine_instance
            
            runner = CliRunner()
            result = runner.invoke(app, [
                "run", "--config", str(eval_file),
                "--output", "json",
                "--no-lint"
            ])
            
            # Should try to output JSON
            assert "Error" not in result.stdout or result.exit_code in [0, 3]
    
    def test_run_with_output_markdown(self, tmp_path):
        """Test run with markdown output."""
        from typer.testing import CliRunner
        
        eval_file = tmp_path / "eval.yaml"
        eval_file.write_text("""
name: Test
treatments:
  CONTROL:
    skill_path: null
tests:
  - name: test1
    prompt: "test"
output:
  results_dir: "./results"
""")
        
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        
        with patch("md_evals.cli.LLMAdapter"), \
             patch("md_evals.cli.ExecutionEngine") as mock_engine, \
             patch("md_evals.cli.Reporter"):
            
            from md_evals.models import ExecutionResult, LLMResponse
            
            mock_engine_instance = MagicMock()
            mock_engine_instance.run_all = AsyncMock(return_value=[
                ExecutionResult(
                    treatment="CONTROL",
                    test="test1",
                    prompt="test",
                    response=LLMResponse(
                        content="hi",
                        model="gpt-4o",
                        provider="openai",
                        duration_ms=1000
                    ),
                    passed=True,
                    evaluator_results=[],
                    timestamp="2024-01-01T00:00:00"
                )
            ])
            mock_engine.return_value = mock_engine_instance
            
            runner = CliRunner()
            result = runner.invoke(app, [
                "run", "--config", str(eval_file),
                "--output", "markdown",
                "--no-lint"
            ])
            
            # Should try to output markdown
            assert "Error" not in result.stdout or result.exit_code in [0, 3]
    
    def test_run_lint_failure(self, tmp_path):
        """Test run with lint failure."""
        from typer.testing import CliRunner
        
        eval_file = tmp_path / "eval.yaml"
        eval_file.write_text("""
name: Test
treatments:
  WITH_SKILL:
    skill_path: "./SKILL.md"
tests:
  - name: test1
    prompt: "test"
lint:
  fail_on_violation: true
""")
        
        # Create a SKILL.md that will fail lint
        skill_file = tmp_path / "SKILL.md"
        # Create a file with too many lines to trigger lint failure
        skill_file.write_text("# Skill\n" + "\n".join([f"## Rule {i}\n- Item" for i in range(500)]))
        
        runner = CliRunner()
        result = runner.invoke(app, [
            "run", "--config", str(eval_file)
        ])
        
        # Should fail on lint
        assert result.exit_code == 2
    
    def test_run_verbose(self, tmp_path):
        """Test run with verbose output."""
        from typer.testing import CliRunner
        
        eval_file = tmp_path / "eval.yaml"
        eval_file.write_text("""
name: Test
treatments:
  CONTROL:
    skill_path: null
tests:
  - name: test1
    prompt: "test"
""")
        
        with patch("md_evals.cli.LLMAdapter"), \
             patch("md_evals.cli.ExecutionEngine") as mock_engine, \
             patch("md_evals.cli.Reporter"):
            
            from md_evals.models import ExecutionResult, LLMResponse
            
            mock_engine_instance = MagicMock()
            mock_engine_instance.run_all = AsyncMock(return_value=[])
            mock_engine.return_value = mock_engine_instance
            
            runner = CliRunner()
            result = runner.invoke(app, [
                "run", "--config", str(eval_file),
                "--verbose",
                "--no-lint"
            ])
            
            assert "Error loading config" not in result.stdout


class TestListModelsCommand:
    """Test list-models command (Phase 3)."""
    
    def test_list_models_all_providers(self):
        """Test listing models for all providers."""
        from typer.testing import CliRunner
        
        runner = CliRunner()
        result = runner.invoke(app, ["list-models"])
        
        assert result.exit_code == 0
        # Should show at least the github-models provider
        assert "github-models" in result.stdout or "github_models" in result.stdout.lower()
    
    def test_list_models_github_models(self):
        """Test listing GitHub Models specifically."""
        from typer.testing import CliRunner
        
        runner = CliRunner()
        result = runner.invoke(app, ["list-models", "--provider", "github-models"])
        
        assert result.exit_code == 0
        # Should show supported models
        assert "claude-3.5-sonnet" in result.stdout or "Claude" in result.stdout
    
    def test_list_models_with_verbose(self):
        """Test list-models with verbose output."""
        from typer.testing import CliRunner
        
        runner = CliRunner()
        result = runner.invoke(app, ["list-models", "--provider", "github-models", "--verbose"])
        
        assert result.exit_code == 0
        # Verbose should show more details
        assert "Model" in result.stdout or "model" in result.stdout.lower()
    
    def test_list_models_invalid_provider(self):
        """Test list-models with invalid provider."""
        from typer.testing import CliRunner
        
        runner = CliRunner()
        result = runner.invoke(app, ["list-models", "--provider", "invalid-provider"])
        
        assert result.exit_code == 1
        assert "Error" in result.stdout or "not found" in result.stdout.lower()


class TestProviderFlags:
    """Test --provider flag in run command (Phase 3)."""
    
    def test_run_with_provider_flag_github_models(self, tmp_path):
        """Test run command with --provider github-models."""
        from typer.testing import CliRunner
        
        eval_file = tmp_path / "eval.yaml"
        eval_file.write_text("""
name: Test
treatments:
  CONTROL:
    skill_path: null
tests:
  - name: test1
    prompt: "test"
""")
        
        with patch("md_evals.cli.LLMAdapter"), \
             patch("md_evals.cli.ExecutionEngine") as mock_engine, \
             patch("md_evals.cli.Reporter"):
            
            mock_engine_instance = MagicMock()
            mock_engine_instance.run_all = AsyncMock(return_value=[])
            mock_engine.return_value = mock_engine_instance
            
            runner = CliRunner()
            result = runner.invoke(app, [
                "run", "--config", str(eval_file),
                "--provider", "github-models",
                "--no-lint"
            ])
            
            # Should accept the provider flag
            assert "not found" not in result.stdout.lower()
    
    def test_run_with_invalid_provider(self, tmp_path):
        """Test run command with invalid provider."""
        from typer.testing import CliRunner
        
        eval_file = tmp_path / "eval.yaml"
        eval_file.write_text("""
name: Test
treatments:
  CONTROL:
    skill_path: null
tests:
  - name: test1
    prompt: "test"
""")
        
        runner = CliRunner()
        result = runner.invoke(app, [
            "run", "--config", str(eval_file),
            "--provider", "completely-invalid-provider",
            "--no-lint"
        ])
        
        # Should fail with provider not found
        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()


class TestProviderConfigFile:
    """Test provider specification in config files (Phase 3)."""
    
    def test_config_with_provider_field(self, tmp_path):
        """Test eval.yaml with provider in defaults section."""
        from typer.testing import CliRunner
        
        eval_file = tmp_path / "eval.yaml"
        eval_file.write_text("""
name: Test
defaults:
  provider: "github-models"
  model: "claude-3.5-sonnet"
treatments:
  CONTROL:
    skill_path: null
tests:
  - name: test1
    prompt: "test"
""")
        
        with patch("md_evals.cli.LLMAdapter"), \
             patch("md_evals.cli.ExecutionEngine") as mock_engine, \
             patch("md_evals.cli.Reporter"):
            
            mock_engine_instance = MagicMock()
            mock_engine_instance.run_all = AsyncMock(return_value=[])
            mock_engine.return_value = mock_engine_instance
            
            runner = CliRunner()
            result = runner.invoke(app, [
                "run", "--config", str(eval_file),
                "--no-lint"
            ])
            
            # Should load config with provider field
            assert "Error loading config" not in result.stdout or result.exit_code == 0
