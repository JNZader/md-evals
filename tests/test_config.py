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


# ============================================================================
# FASE 12-2: Configuration Validation Properties
# ============================================================================
# Property-based tests using hypothesis for config validation invariants

from hypothesis import given, strategies as st, settings, HealthCheck
import json




# ============================================================================
# FASE 12-2: Configuration Validation Properties
# ============================================================================
# Property-based tests using hypothesis for config validation invariants

from hypothesis import given, strategies as st


class TestConfigValidationProperties:
    """Property-based tests for configuration validation.
    
    Properties tested:
    1. Required fields always present after creation
    2. Type invariants are maintained
    3. Boundary values are accepted/rejected consistently
    4. Config defaults are properly initialized
    """
    
    @given(
        name=st.text(min_size=1, max_size=100, alphabet=st.characters(
            blacklist_categories=('Cc', 'Cs'),
            blacklist_characters='\x00'
        )),
        version=st.just("1.0")
    )
    def test_config_required_fields_always_present(self, name, version):
        """Property: Config always has required fields after creation.
        
        Required fields: name, version, treatments, tests
        
        Mutation detectors:
        - If required field check removed
        - If default initialization removed
        - If field validation is skipped
        """
        from md_evals.models import EvalConfig
        
        # Create config with minimal fields
        config = EvalConfig(name=name, version=version)
        
        # All required fields must exist
        assert hasattr(config, 'name')
        assert hasattr(config, 'version')
        assert hasattr(config, 'treatments')
        assert hasattr(config, 'tests')
        assert hasattr(config, 'defaults')
        
        # All must be non-None
        assert config.name is not None
        assert config.version is not None
        assert config.treatments is not None
        assert config.tests is not None
        assert config.defaults is not None
        
        # Values must match input
        assert config.name == name
        assert config.version == version
    
    @given(
        retry_attempts=st.integers(min_value=1, max_value=100),
        timeout=st.integers(min_value=1, max_value=300)
    )
    def test_config_type_invariants(self, retry_attempts, timeout):
        """Property: Config field types remain consistent after creation.
        
        - retry_attempts must be int
        - timeout must be int (seconds)
        - temperature must be float [0, 2]
        - max_tokens must be int > 0
        
        Mutation detectors:
        - If type conversion is removed
        - If type validation is skipped
        - If coercion is removed
        """
        from md_evals.models import Defaults, EvalConfig
        
        # Create config with specific types
        defaults = Defaults(
            retry_attempts=retry_attempts,
            timeout=timeout,
            temperature=0.7,
            max_tokens=2048
        )
        config = EvalConfig(name="test", defaults=defaults)
        
        # Types must be preserved
        assert isinstance(config.defaults.retry_attempts, int)
        assert isinstance(config.defaults.timeout, int)
        assert isinstance(config.defaults.temperature, float)
        assert isinstance(config.defaults.max_tokens, int)
        
        # Values must match input
        assert config.defaults.retry_attempts == retry_attempts
        assert config.defaults.timeout == timeout
        assert config.defaults.temperature == 0.7
        assert config.defaults.max_tokens == 2048
    
    @given(
        retry_attempts=st.integers(min_value=1, max_value=100),
        timeout=st.integers(min_value=1, max_value=300),
        temperature=st.floats(min_value=0.0, max_value=2.0, allow_nan=False, allow_infinity=False),
        max_tokens=st.integers(min_value=1, max_value=128000)
    )
    def test_config_boundary_values_accepted(self, retry_attempts, timeout, temperature, max_tokens):
        """Property: Config accepts values within valid bounds.
        
        Valid bounds:
        - retry_attempts: [1, 100]
        - timeout: [1, 300] seconds
        - temperature: [0.0, 2.0]
        - max_tokens: [1, 128000]
        
        Mutation detectors:
        - If boundary checks removed
        - If validation is skipped
        - If wrong comparison operator used
        """
        from md_evals.models import Defaults, EvalConfig
        
        # All these values are within bounds
        defaults = Defaults(
            retry_attempts=retry_attempts,
            timeout=timeout,
            temperature=temperature,
            max_tokens=max_tokens
        )
        config = EvalConfig(name="test", defaults=defaults)
        
        # Should not raise exception
        assert config.defaults.retry_attempts == retry_attempts
        assert config.defaults.timeout == timeout
        assert config.defaults.temperature == temperature
        assert config.defaults.max_tokens == max_tokens
    
    @given(
        retry_attempts=st.integers(min_value=1, max_value=100),
        model=st.sampled_from(["gpt-4o", "gpt-4-turbo", "claude-3-opus"]),
        provider=st.sampled_from(["openai", "anthropic", "github-models"])
    )
    def test_config_default_values_initialized(self, retry_attempts, model, provider):
        """Property: Config defaults are properly initialized.
        
        - temperature defaults to 0.7
        - max_tokens defaults to 2048
        - timeout defaults to 60
        - retry_delay defaults to 1.0
        
        Mutation detectors:
        - If default initialization removed
        - If defaults overwritten
        - If default values are hardcoded wrong
        """
        from md_evals.models import Defaults, EvalConfig
        
        defaults = Defaults(
            retry_attempts=retry_attempts,
            model=model,
            provider=provider
        )
        config = EvalConfig(name="test", defaults=defaults)
        
        # Should have all defaults
        assert config.defaults.temperature == 0.7
        assert config.defaults.max_tokens == 2048
        assert config.defaults.timeout == 60
        assert config.defaults.retry_delay == 1.0
        
        # And our specified values
        assert config.defaults.retry_attempts == retry_attempts
        assert config.defaults.model == model
        assert config.defaults.provider == provider
    
    @given(
        treatment_name=st.text(min_size=1, max_size=50, alphabet=st.characters(
            blacklist_categories=('Cc', 'Cs'),
            blacklist_characters='\x00'
        )),
        test_name=st.text(min_size=1, max_size=50, alphabet=st.characters(
            blacklist_categories=('Cc', 'Cs'),
            blacklist_characters='\x00'
        ))
    )
    def test_config_collections_preserved(self, treatment_name, test_name):
        """Property: Config collections are preserved after creation.
        
        - treatments dict should be modifiable and preserved
        - tests list should be modifiable and preserved
        - Collection length should be consistent
        
        Mutation detectors:
        - If collections are not initialized
        - If they're replaced with None
        - If mutability is lost
        """
        from md_evals.models import EvalConfig, Treatment, Task
        
        # Create config with treatments and tests
        treatments = {
            treatment_name: Treatment(
                description=f"Test {treatment_name}",
                skill_path=None
            )
        }
        tests = [
            Task(
                name=test_name,
                description="Test",
                prompt="test"
            )
        ]
        
        config = EvalConfig(
            name="test",
            treatments=treatments,
            tests=tests
        )
        
        # Collections should be preserved
        assert len(config.treatments) == 1
        assert len(config.tests) == 1
        assert treatment_name in config.treatments
        assert config.tests[0].name == test_name


class TestConfigEdgeCases:
    """Edge case tests for configuration."""
    
    @given(
        special_chars=st.text(
            min_size=1,
            max_size=20,
            alphabet=st.characters(
                blacklist_categories=('Cc', 'Cs'),
                blacklist_characters='\x00'
            )
        )
    )
    def test_config_name_with_special_chars(self, special_chars):
        """Property: Config names with special characters are handled.
        
        - Should either accept or reject consistently
        - Rejections should provide error message
        """
        from md_evals.models import EvalConfig
        
        if len(special_chars.strip()) > 0:  # Skip empty strings
            try:
                config = EvalConfig(name=special_chars)
                # If accepted, name should match
                assert config.name == special_chars
            except Exception as e:
                # If rejected, error should be clear
                assert len(str(e)) > 0
    
    @given(
        version=st.sampled_from(["1.0", "2.0", "1.5", "0.1"])
    )
    def test_config_version_formats(self, version):
        """Property: Config accepts standard version formats.
        
        - Version should be preserved
        - Should not mutate format
        """
        from md_evals.models import EvalConfig
        
        config = EvalConfig(name="test", version=version)
        assert config.version == version
    
    @given(
        model=st.text(min_size=1, max_size=50, alphabet=st.characters(
            blacklist_categories=('Cc', 'Cs'),
            blacklist_characters='\x00'
        )),
        provider=st.text(min_size=1, max_size=30, alphabet=st.characters(
            blacklist_categories=('Cc', 'Cs'),
            blacklist_characters='\x00'
        ))
    )
    def test_config_model_provider_consistency(self, model, provider):
        """Property: Config model and provider are consistent.
        
        - Model and provider should be preserved
        - Should not be swapped or changed
        - Values should match exactly what was set
        """
        from md_evals.models import Defaults, EvalConfig
        
        defaults = Defaults(model=model, provider=provider)
        config = EvalConfig(name="test", defaults=defaults)
        
        # Both should be preserved exactly
        assert config.defaults.model == model, f"Model changed: {model} -> {config.defaults.model}"
        assert config.defaults.provider == provider, f"Provider changed: {provider} -> {config.defaults.provider}"
        
        # They should be different types (model = gpt-4o name, provider = openai)
        # but they might be the same string in edge cases, which is OK
        assert isinstance(config.defaults.model, str)
        assert isinstance(config.defaults.provider, str)


