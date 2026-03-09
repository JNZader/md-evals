"""Tests for config loader."""

import pytest
from pathlib import Path
from md_evals.config import ConfigLoader, ConfigLoaderError
from md_evals.models import EvalConfig, Defaults, Treatment, Task, RegexEvaluator


class TestConfigLoader:
    """Test ConfigLoader."""
    
    def test_load_valid_yaml(self, tmp_path):
        """Test loading valid YAML."""
        config_content = """
name: "Test Eval"
version: "1.0"
defaults:
  model: "gpt-4o"
  temperature: 0.5
treatments:
  CONTROL:
    description: "No skill"
    skill_path: null
  WITH_SKILL:
    description: "With skill"
    skill_path: "./skill.md"
tests:
  - name: "test1"
    prompt: "Say {word}"
    variables:
      word: "hello"
    evaluators:
      - type: "regex"
        name: "has_hello"
        pattern: "hello"
"""
        config_file = tmp_path / "eval.yaml"
        config_file.write_text(config_content)
        
        config = ConfigLoader.load(str(config_file))
        
        assert config.name == "Test Eval"
        assert config.version == "1.0"
        assert config.defaults.model == "gpt-4o"
        assert config.defaults.temperature == 0.5
        assert "CONTROL" in config.treatments
        assert "WITH_SKILL" in config.treatments
        assert len(config.tests) == 1
        assert config.tests[0].name == "test1"
    
    def test_load_file_not_found(self):
        """Test loading non-existent file."""
        with pytest.raises(ConfigLoaderError, match="not found"):
            ConfigLoader.load("nonexistent.yaml")
    
    def test_load_empty_file(self, tmp_path):
        """Test loading empty file."""
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")
        
        with pytest.raises(ConfigLoaderError, match="Empty"):
            ConfigLoader.load(str(config_file))
    
    def test_load_invalid_yaml(self, tmp_path):
        """Test loading invalid YAML."""
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text("name: [}")
        
        with pytest.raises(ConfigLoaderError, match="Invalid YAML"):
            ConfigLoader.load(str(config_file))
    
    def test_validate_valid_config(self):
        """Test validation of valid config."""
        config = EvalConfig(
            name="Test",
            treatments={
                "CONTROL": Treatment(),
                "WITH_SKILL": Treatment(skill_path="./skill.md")
            },
            tests=[Task(name="test", prompt="test")]
        )
        
        warnings = ConfigLoader.validate(config)
        
        # Should have warning about missing skill file
        assert len(warnings) > 0
    
    def test_validate_empty_treatments(self):
        """Test validation with no treatments."""
        config = EvalConfig(name="Test", treatments={})
        
        warnings = ConfigLoader.validate(config)
        
        assert any("No treatments" in w for w in warnings)
    
    def test_validate_empty_tests(self):
        """Test validation with no tests."""
        config = EvalConfig(name="Test", treatments={"CONTROL": Treatment()})
        
        warnings = ConfigLoader.validate(config)
        
        assert any("No tests" in w for w in warnings)
    
    def test_validate_missing_control(self):
        """Test validation without CONTROL treatment."""
        config = EvalConfig(
            name="Test",
            treatments={"WITH_SKILL": Treatment(skill_path="./skill.md")}
        )
        
        warnings = ConfigLoader.validate(config)
        
        assert any("CONTROL" in w for w in warnings)
    
    def test_expand_wildcards_exact(self):
        """Test expanding exact treatment names."""
        available = {"CONTROL": Treatment(), "WITH_SKILL": Treatment()}
        
        result = ConfigLoader.expand_wildcards(["CONTROL"], available)
        
        assert result == ["CONTROL"]
    
    def test_expand_wildcards_asterisk(self):
        """Test expanding asterisk wildcard."""
        available = {
            "CONTROL": Treatment(),
            "LCC_SHORT": Treatment(),
            "LCC_LONG": Treatment(),
            "OTHER": Treatment()
        }
        
        result = ConfigLoader.expand_wildcards(["LCC_*"], available)
        
        assert set(result) == {"LCC_SHORT", "LCC_LONG"}
    
    def test_expand_wildcards_question(self):
        """Test expanding question mark wildcard."""
        available = {
            "CONTROL": Treatment(),
            "TEST_A": Treatment(),
            "TEST_B": Treatment()
        }
        
        result = ConfigLoader.expand_wildcards(["TEST_?"], available)
        
        assert set(result) == {"TEST_A", "TEST_B"}
    
    def test_expand_wildcards_unknown(self):
        """Test expanding unknown treatment."""
        available = {"CONTROL": Treatment()}
        
        with pytest.raises(ConfigLoaderError, match="Unknown"):
            ConfigLoader.expand_wildcards(["UNKNOWN"], available)
    
    def test_save_config(self, tmp_path):
        """Test saving configuration."""
        config = EvalConfig(
            name="Test",
            defaults=Defaults(model="gpt-4o"),
            treatments={"CONTROL": Treatment()}
        )
        
        config_file = tmp_path / "output.yaml"
        ConfigLoader.save(config, str(config_file))
        
        assert config_file.exists()
        
        loaded = ConfigLoader.load(str(config_file))
        assert loaded.name == "Test"
        assert loaded.defaults.model == "gpt-4o"
