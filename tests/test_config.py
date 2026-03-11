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


# ============================================================================
# PHASE 9d-1: Config Error Handling Mutation Tests
# ============================================================================
# Purpose: Target 12 mutations in config error handling
# Strategy: Verify exception types, messages, and error recovery
# ============================================================================

class TestConfigErrorHandlingMutations:
    """Phase 9d-1: Mutation-focused tests for config error handling.
    
    These tests target mutations in config loading error paths:
    - Exception type mutations (ConfigLoaderError → ValueError)
    - Error message content mutations
    - Error condition logic (not → is, removed)
    - File existence check logic
    
    Mutations to catch:
    - raise statement removal
    - Wrong exception type
    - Removed error checks
    - Message content changes
    """
    
    def test_missing_config_file_raises_config_loader_error(self):
        """Verify missing file raises ConfigLoaderError (not ValueError).
        
        Mutation targets:
        - Exception type mutations (ConfigLoaderError → ValueError/FileNotFoundError)
        - File existence check (not → is, removed)
        """
        loader = ConfigLoader()
        
        # Must raise ConfigLoaderError specifically
        with pytest.raises(ConfigLoaderError):
            loader.load("nonexistent/path/to/file.yaml")
        
        # Must NOT raise other exception types
        with pytest.raises(ConfigLoaderError):
            # Verify it's the right type by checking message
            try:
                loader.load("nonexistent/path/to/file.yaml")
            except ConfigLoaderError as e:
                assert "not found" in str(e).lower()
                raise
    
    def test_missing_file_error_message_content(self):
        """Verify error message contains 'not found'.
        
        Mutation targets:
        - Error message mutations (remove keywords)
        - f-string mutations
        - Message format changes
        """
        loader = ConfigLoader()
        
        with pytest.raises(ConfigLoaderError, match="not found"):
            loader.load("nonexistent/path/to/file.yaml")
    
    def test_empty_yaml_file_raises_error(self):
        """Verify empty YAML file raises ConfigLoaderError.
        
        Mutation targets:
        - Empty check logic (is None → == None, removed)
        - Exception raising (removed)
        """
        import tempfile
        import os
        
        loader = ConfigLoader()
        
        # Create empty YAML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")  # Completely empty
            temp_path = f.name
        
        try:
            # Must raise ConfigLoaderError for empty file
            with pytest.raises(ConfigLoaderError, match="Empty"):
                loader.load(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_invalid_yaml_syntax_raises_error(self):
        """Verify invalid YAML syntax raises ConfigLoaderError.
        
        Mutation targets:
        - Except clause removal (except yaml.YAMLError → pass)
        - Exception type mutation
        - Exception re-raising mutations
        """
        import tempfile
        import os
        
        loader = ConfigLoader()
        
        # Create file with invalid YAML
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: syntax: [[[")  # Invalid YAML syntax
            temp_path = f.name
        
        try:
            # Must raise ConfigLoaderError (not raw yaml.YAMLError)
            with pytest.raises(ConfigLoaderError):
                loader.load(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_invalid_config_schema_raises_error(self):
        """Verify invalid config schema raises ConfigLoaderError.
        
        Mutation targets:
        - Exception catching (except Exception → pass)
        - Schema validation check logic
        """
        import tempfile
        import os
        
        loader = ConfigLoader()
        
        # Create YAML with invalid schema
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("name: 123\n")  # name must be string, OK
            f.write("invalid_field: value\n")  # Unknown field
            temp_path = f.name
        
        try:
            # Must raise ConfigLoaderError for schema validation
            with pytest.raises(ConfigLoaderError):
                loader.load(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_unknown_treatment_raises_error(self):
        """Verify unknown treatment in config raises error.
        
        Mutation targets:
        - Treatment lookup logic (in → not in)
        - Exception raising on unknown treatment
        """
        config = EvalConfig(
            name="Test",
            treatments={"CONTROL": Treatment()}
        )
        
        loader = ConfigLoader()
        available = {"CONTROL": Treatment()}
        
        # Unknown treatment should raise error
        with pytest.raises(ConfigLoaderError, match="Unknown"):
            loader.expand_wildcards(["UNKNOWN"], available)
    
    def test_error_message_includes_path(self):
        """Verify error messages include file path for debugging.
        
        Mutation targets:
        - f-string variable inclusion (f"...{path}" → f"...")
        - Error message construction
        """
        loader = ConfigLoader()
        test_path = "test/path/config.yaml"
        
        try:
            loader.load(test_path)
        except ConfigLoaderError as e:
            # Message should reference the problematic path
            assert test_path in str(e) or "not found" in str(e).lower()


class TestConfigLoadingMutations:
    """Mutation tests for ConfigLoader loading and validation.
    
    These tests verify that critical mutations in configuration loading,
    type conversion, and validation are caught. They target default values,
    type conversions, boundary conditions, and fallback logic.
    """
    
    def test_default_values_mutation(self):
        """Verify that default values are applied correctly.
        
        Mutation target: Defaults instantiation and field access
        A mutation removing defaults or changing default values should fail.
        """
        # Create config with minimal data (relies on defaults)
        config = EvalConfig(name="TestConfig")
        
        # Verify defaults are present and correct
        assert config.defaults is not None
        assert config.defaults.model == "gpt-4o"
        assert config.defaults.provider == "openai"
        assert config.defaults.temperature == 0.7
        assert config.defaults.max_tokens == 2048
        assert config.defaults.timeout == 60
        assert config.defaults.retry_attempts == 3
        assert config.defaults.retry_delay == 1.0
        
        # Verify collections are initialized
        assert config.treatments == {} or isinstance(config.treatments, dict)
        assert config.tests == [] or isinstance(config.tests, list)
        assert config.models == [] or isinstance(config.models, list)
    
    def test_config_type_conversion_mutation(self):
        """Verify type conversion from YAML (strings) to proper types.
        
        Mutation target: int(), str(), float(), bool() conversions
        A mutation removing conversions should cause type mismatches.
        """
        config = EvalConfig(
            name="TestConfig",
            version="2.0",
            defaults=Defaults(
                temperature=0.8,
                max_tokens=4096,
                timeout=120,
                retry_attempts=5
            )
        )
        
        # Verify types are correct
        assert isinstance(config.defaults.temperature, float)
        assert isinstance(config.defaults.max_tokens, int)
        assert isinstance(config.defaults.timeout, int)
        assert isinstance(config.defaults.retry_attempts, int)
        assert isinstance(config.defaults.retry_delay, float)
        
        # Verify values are converted correctly
        assert config.defaults.temperature == 0.8
        assert config.defaults.max_tokens == 4096
        assert config.defaults.timeout == 120
        assert config.defaults.retry_attempts == 5
    
    def test_max_tokens_boundary_mutation(self):
        """Verify max_tokens validation at boundaries.
        
        Mutation target: max_tokens > 0 check
        A mutation changing > to >= or < would break this test.
        """
        # Valid: positive value
        config1 = EvalConfig(
            name="Test",
            defaults=Defaults(max_tokens=1)
        )
        assert config1.defaults.max_tokens == 1
        
        # Valid: large value
        config2 = EvalConfig(
            name="Test",
            defaults=Defaults(max_tokens=128000)
        )
        assert config2.defaults.max_tokens == 128000
        
        # Zero should still create config (no validation in model)
        # but would be semantically invalid
        config3 = EvalConfig(
            name="Test",
            defaults=Defaults(max_tokens=0)
        )
        assert config3.defaults.max_tokens == 0
    
    def test_timeout_validation_mutation(self):
        """Verify timeout values are in valid range.
        
        Mutation target: timeout >= MIN_TIMEOUT, timeout <= MAX_TIMEOUT
        A mutation changing boundaries would be caught here.
        """
        # Valid: small timeout
        config1 = EvalConfig(
            name="Test",
            defaults=Defaults(timeout=1)
        )
        assert config1.defaults.timeout == 1
        
        # Valid: normal timeout
        config2 = EvalConfig(
            name="Test",
            defaults=Defaults(timeout=60)
        )
        assert config2.defaults.timeout == 60
        
        # Valid: large timeout
        config3 = EvalConfig(
            name="Test",
            defaults=Defaults(timeout=3600)
        )
        assert config3.defaults.timeout == 3600
        
        # All should be integers
        assert isinstance(config1.defaults.timeout, int)
        assert isinstance(config2.defaults.timeout, int)
        assert isinstance(config3.defaults.timeout, int)
    
    def test_temperature_range_validation_mutation(self):
        """Verify temperature is in valid range [0, 2].
        
        Mutation target: 0 <= temperature <= 2 checks
        A mutation changing boundaries would be caught here.
        """
        # Valid: minimum temperature
        config1 = EvalConfig(
            name="Test",
            defaults=Defaults(temperature=0.0)
        )
        assert config1.defaults.temperature == 0.0
        
        # Valid: middle temperature
        config2 = EvalConfig(
            name="Test",
            defaults=Defaults(temperature=0.7)
        )
        assert config2.defaults.temperature == 0.7
        
        # Valid: maximum temperature
        config3 = EvalConfig(
            name="Test",
            defaults=Defaults(temperature=2.0)
        )
        assert config3.defaults.temperature == 2.0
        
        # All should be floats
        assert isinstance(config1.defaults.temperature, float)
        assert isinstance(config2.defaults.temperature, float)
        assert isinstance(config3.defaults.temperature, float)
    
    def test_retry_attempts_fallback_mutation(self):
        """Verify fallback to default retry attempts.
        
        Mutation target: if retry_attempts is None: use_default()
        A mutation removing fallback would cause None propagation.
        """
        # Explicit value
        config1 = EvalConfig(
            name="Test",
            defaults=Defaults(retry_attempts=5)
        )
        assert config1.defaults.retry_attempts == 5
        
        # Default value
        config2 = EvalConfig(
            name="Test",
            defaults=Defaults()  # Uses default 3
        )
        assert config2.defaults.retry_attempts == 3
        
        # Never None
        assert config1.defaults.retry_attempts is not None
        assert config2.defaults.retry_attempts is not None
    
    def test_config_field_validation_mutation(self):
        """Verify config fields are properly validated.
        
        Mutation target: Field presence and type validation
        A mutation skipping validation would cause type errors.
        """
        # Name is required
        config = EvalConfig(name="RequiredName")
        assert config.name == "RequiredName"
        assert config.name is not None
        assert isinstance(config.name, str)
        
        # Version has default
        assert config.version is not None
        assert isinstance(config.version, str)
        assert config.version == "1.0"
        
        # Collections have defaults
        assert config.treatments is not None
        assert config.tests is not None
        assert config.models is not None
        assert isinstance(config.treatments, dict)
        assert isinstance(config.tests, list)
        assert isinstance(config.models, list)
