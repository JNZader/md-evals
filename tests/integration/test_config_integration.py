"""Integration tests for config loading — real YAML files, no mocks."""

from pathlib import Path

import pytest

from md_evals.config import ConfigLoader, ConfigLoaderError


FIXTURES = Path(__file__).parent.parent / "fixtures"


class TestConfigLoadReal:
    """Load real YAML config files and validate parsing."""

    def test_load_valid_config(self):
        config = ConfigLoader.load(str(FIXTURES / "config_valid.yaml"))
        assert config.name == "Integration Test Eval"
        assert config.version == "1.0"
        assert config.defaults.model == "gpt-4o"
        assert config.defaults.provider == "openai"
        assert config.defaults.temperature == 0.7

    def test_load_valid_config_treatments(self):
        config = ConfigLoader.load(str(FIXTURES / "config_valid.yaml"))
        assert "CONTROL" in config.treatments
        assert "WITH_SKILL" in config.treatments
        assert config.treatments["CONTROL"].skill_path is None
        assert config.treatments["WITH_SKILL"].skill_path == "./tests/fixtures/skill_valid.md"

    def test_load_valid_config_tests(self):
        config = ConfigLoader.load(str(FIXTURES / "config_valid.yaml"))
        assert len(config.tests) == 2
        assert config.tests[0].name == "greeting_test"
        assert config.tests[1].name == "math_test"
        assert "{name}" in config.tests[0].prompt
        assert config.tests[0].variables["name"] == "World"

    def test_load_valid_config_evaluators(self):
        config = ConfigLoader.load(str(FIXTURES / "config_valid.yaml"))
        evaluators = config.tests[0].evaluators
        assert len(evaluators) == 1
        assert evaluators[0].type == "regex"
        assert evaluators[0].name == "has_hello"
        assert evaluators[0].pattern == "[Hh]ello"

    def test_load_existing_fixture(self):
        """Load the pre-existing eval.yaml fixture."""
        config = ConfigLoader.load(str(FIXTURES / "eval.yaml"))
        assert config.name == "Example Evaluation"
        assert "CONTROL" in config.treatments
        assert "WITH_SKILL" in config.treatments


class TestConfigLoadErrors:
    """Error handling for malformed or missing configs."""

    def test_missing_file_raises(self):
        with pytest.raises(ConfigLoaderError, match="not found"):
            ConfigLoader.load("/nonexistent/path/eval.yaml")

    def test_malformed_yaml_raises(self):
        with pytest.raises(ConfigLoaderError, match="Invalid YAML"):
            ConfigLoader.load(str(FIXTURES / "config_malformed.yaml"))

    def test_empty_config_raises(self, tmp_path):
        empty = tmp_path / "empty.yaml"
        empty.write_text("")
        with pytest.raises(ConfigLoaderError, match="Empty config"):
            ConfigLoader.load(str(empty))

    def test_invalid_structure_raises(self, tmp_path):
        bad = tmp_path / "bad.yaml"
        bad.write_text("just_a_string: true\n")
        with pytest.raises(ConfigLoaderError, match="Invalid configuration"):
            ConfigLoader.load(str(bad))


class TestConfigValidation:
    """Validate config objects for warnings and issues."""

    def test_validate_valid_config(self):
        config = ConfigLoader.load(str(FIXTURES / "config_valid.yaml"))
        warnings = ConfigLoader.validate(config)
        # Valid config should have no warnings (has CONTROL and tests)
        assert not any("No tests defined" in w for w in warnings)
        assert not any("No treatments defined" in w for w in warnings)

    def test_validate_warns_missing_control(self, tmp_path):
        cfg = tmp_path / "no_control.yaml"
        cfg.write_text(
            'name: "Test"\n'
            "treatments:\n"
            "  TREATMENT_A:\n"
            '    description: "A"\n'
            "tests:\n"
            '  - name: "t1"\n'
            '    prompt: "hello"\n'
        )
        config = ConfigLoader.load(str(cfg))
        warnings = ConfigLoader.validate(config)
        assert any("CONTROL" in w for w in warnings)


class TestWildcardExpansion:
    """Test treatment wildcard expansion with real config data."""

    def test_expand_exact_match(self):
        available = {"CONTROL": {}, "WITH_SKILL": {}, "OTHER": {}}
        result = ConfigLoader.expand_wildcards(["CONTROL"], available)
        assert result == ["CONTROL"]

    def test_expand_wildcard_star(self):
        available = {"CONTROL": {}, "WITH_SKILL_A": {}, "WITH_SKILL_B": {}}
        result = ConfigLoader.expand_wildcards(["WITH_*"], available)
        assert "WITH_SKILL_A" in result
        assert "WITH_SKILL_B" in result
        assert "CONTROL" not in result

    def test_expand_wildcard_question_mark(self):
        available = {"V1": {}, "V2": {}, "V3": {}, "V10": {}}
        result = ConfigLoader.expand_wildcards(["V?"], available)
        assert sorted(result) == ["V1", "V2", "V3"]

    def test_expand_unknown_raises(self):
        available = {"CONTROL": {}}
        with pytest.raises(ConfigLoaderError, match="Unknown treatment"):
            ConfigLoader.expand_wildcards(["NONEXISTENT"], available)

    def test_expand_multiple_patterns(self):
        available = {"CONTROL": {}, "SKA": {}, "SKB": {}, "OTHER": {}}
        result = ConfigLoader.expand_wildcards(["SK*", "CONTROL"], available)
        assert "SKA" in result
        assert "SKB" in result
        assert "CONTROL" in result
