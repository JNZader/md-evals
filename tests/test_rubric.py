"""Comprehensive unit tests for md_evals.rubric module.

Tests cover all public types and functions:
  - RubricConfig validation (weights, thresholds, regex, dimensions)
  - RubricLoader (load, load_default, resolve, resolution chain)
  - Edge cases (floating-point, single dimension, zero weight, S-grade optional)
"""

from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from md_evals.rubric import (
    RubricConfig,
    RubricLoader,
    RubricNotFoundError,
    RubricValidationError,
    DimensionConfig,
)


# ============================================================================
# Constants
# ============================================================================

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _minimal_rubric_data(**overrides):
    """Build minimal valid rubric dict, applying overrides."""
    data = {
        "version": "1.0",
        "dimensions": {
            "correctness": {"weight": 0.50},
            "completeness": {"weight": 0.50},
        },
        "grade_thresholds": {
            "A": 0.85,
            "B": 0.70,
            "C": 0.50,
            "D": 0.30,
        },
    }
    data.update(overrides)
    return data


# ============================================================================
# 1. RubricConfig — default rubric loads correctly
# ============================================================================


def test_default_rubric_loads_with_7_dimensions():
    """Default rubric has exactly 7 dimensions."""
    rubric = RubricLoader.load_default()
    assert len(rubric.dimensions) == 7


def test_default_rubric_weights_sum_to_one():
    """Default rubric dimension weights sum to 1.0."""
    rubric = RubricLoader.load_default()
    total = sum(d.weight for d in rubric.dimensions.values())
    assert total == pytest.approx(1.0, abs=0.001)


def test_default_rubric_has_required_grades():
    """Default rubric has A, B, C, D grade thresholds."""
    rubric = RubricLoader.load_default()
    assert {"A", "B", "C", "D"}.issubset(rubric.grade_thresholds.keys())


# ============================================================================
# 2. RubricConfig — invalid weights rejected
# ============================================================================


def test_invalid_weights_rejected():
    """Weights summing to 0.80 are rejected with RubricValidationError."""
    with pytest.raises(RubricValidationError, match="weights must sum to 1.0"):
        RubricLoader.load(str(FIXTURES_DIR / "rubric_invalid_weights.yaml"))


def test_invalid_weights_inline():
    """Inline config with weights summing to 0.60 is rejected."""
    data = _minimal_rubric_data(
        dimensions={
            "a": {"weight": 0.30},
            "b": {"weight": 0.30},
        }
    )
    with pytest.raises(RubricValidationError, match="weights must sum to 1.0"):
        RubricConfig(**data)


# ============================================================================
# 3. RubricConfig — duplicate dimension names
# ============================================================================


def test_duplicate_dimension_names_overwritten_by_yaml():
    """YAML naturally deduplicates keys — last one wins.

    We test the model validator still accepts the result (only 1 dim).
    If only one dim remains, weights must still sum to 1.0.
    """
    yaml_content = """
version: "1.0"
dimensions:
  correctness:
    weight: 0.50
  correctness:
    weight: 1.0
grade_thresholds:
  A: 0.85
  B: 0.70
  C: 0.50
  D: 0.30
"""
    data = yaml.safe_load(yaml_content)
    # YAML dedup: only one "correctness" with weight=1.0
    config = RubricConfig(**data)
    assert len(config.dimensions) == 1
    assert config.dimensions["correctness"].weight == 1.0


# ============================================================================
# 4. RubricConfig — non-monotonic thresholds
# ============================================================================


def test_non_monotonic_thresholds_rejected():
    """Non-monotonic thresholds (A=0.85, B=0.90) are rejected."""
    with pytest.raises(RubricValidationError, match="strictly decreasing"):
        RubricLoader.load(str(FIXTURES_DIR / "rubric_non_monotonic.yaml"))


def test_non_monotonic_thresholds_inline():
    """Inline config where C > B is rejected."""
    data = _minimal_rubric_data(
        grade_thresholds={"A": 0.85, "B": 0.50, "C": 0.70, "D": 0.30}
    )
    with pytest.raises(RubricValidationError, match="strictly decreasing"):
        RubricConfig(**data)


# ============================================================================
# 5. RubricConfig — invalid regex rejected
# ============================================================================


def test_invalid_regex_rejected():
    """Invalid regex in security pattern raises RubricValidationError."""
    with pytest.raises(RubricValidationError, match="Invalid regex"):
        RubricLoader.load(str(FIXTURES_DIR / "rubric_bad_regex.yaml"))


# ============================================================================
# 6. RubricConfig — missing required thresholds
# ============================================================================


def test_missing_required_thresholds():
    """Missing A/B/C/D thresholds raise RubricValidationError."""
    data = _minimal_rubric_data(
        grade_thresholds={"A": 0.85, "B": 0.70}  # missing C and D
    )
    with pytest.raises(RubricValidationError, match="Missing required grade"):
        RubricConfig(**data)


def test_missing_single_threshold():
    """Missing just D threshold is rejected."""
    data = _minimal_rubric_data(
        grade_thresholds={"A": 0.85, "B": 0.70, "C": 0.50}
    )
    with pytest.raises(RubricValidationError, match="Missing required grade"):
        RubricConfig(**data)


# ============================================================================
# 7. RubricConfig — unsupported version
# ============================================================================


def test_unsupported_version_rejected():
    """Version '2.0' is rejected."""
    data = _minimal_rubric_data(version="2.0")
    with pytest.raises(RubricValidationError, match="Unsupported rubric version"):
        RubricConfig(**data)


def test_unsupported_version_string():
    """Arbitrary version string is rejected."""
    data = _minimal_rubric_data(version="0.1-beta")
    with pytest.raises(RubricValidationError, match="Unsupported rubric version"):
        RubricConfig(**data)


# ============================================================================
# 8. RubricConfig — empty dimensions
# ============================================================================


def test_empty_dimensions_rejected():
    """Empty dimensions dict raises RubricValidationError."""
    data = _minimal_rubric_data(dimensions={})
    with pytest.raises(RubricValidationError, match="at least one dimension"):
        RubricConfig(**data)


# ============================================================================
# 9. RubricConfig — custom dimension without description → warning
# ============================================================================


def test_custom_dimension_empty_description_warns(caplog):
    """Custom dimension with empty description emits a warning."""
    data = _minimal_rubric_data(
        dimensions={
            "correctness": {"weight": 0.50, "description": "Accuracy"},
            "creativity": {"weight": 0.50},  # custom, no description
        }
    )
    with caplog.at_level(logging.WARNING, logger="md_evals.rubric"):
        config = RubricConfig(**data)

    assert any("creativity" in r.message for r in caplog.records)
    assert len(config.dimensions) == 2


def test_builtin_dimension_empty_description_no_warning(caplog):
    """Built-in dimension (e.g. 'correctness') with empty description → no warning."""
    data = _minimal_rubric_data(
        dimensions={
            "correctness": {"weight": 1.0},  # built-in, empty desc is OK
        }
    )
    with caplog.at_level(logging.WARNING, logger="md_evals.rubric"):
        RubricConfig(**data)

    creativity_warnings = [
        r for r in caplog.records if "correctness" in r.message
    ]
    assert len(creativity_warnings) == 0


# ============================================================================
# 10. RubricLoader — load_default()
# ============================================================================


def test_load_default_returns_rubric_config():
    """load_default() returns a valid RubricConfig."""
    rubric = RubricLoader.load_default()
    assert isinstance(rubric, RubricConfig)
    assert rubric.version == "1.0"


# ============================================================================
# 11. RubricLoader — load() with valid file
# ============================================================================


def test_load_valid_file():
    """load() with a valid fixture returns a RubricConfig."""
    rubric = RubricLoader.load(str(FIXTURES_DIR / "rubric_default.yaml"))
    assert isinstance(rubric, RubricConfig)
    assert len(rubric.dimensions) == 7


def test_load_custom_dimensions_file():
    """Custom dimensions file loads and includes non-builtin dimensions."""
    rubric = RubricLoader.load(str(FIXTURES_DIR / "rubric_custom_dimensions.yaml"))
    assert "creativity" in rubric.dimensions
    assert "tone" in rubric.dimensions


# ============================================================================
# 12. RubricLoader — load() nonexistent file
# ============================================================================


def test_load_nonexistent_file_raises():
    """load() with nonexistent path raises RubricNotFoundError."""
    with pytest.raises(RubricNotFoundError, match="not found"):
        RubricLoader.load("/nonexistent/rubric.yaml")


# ============================================================================
# 13. RubricLoader — load() empty file
# ============================================================================


def test_load_empty_file_raises(tmp_path):
    """load() with empty YAML file raises RubricValidationError."""
    empty_file = tmp_path / "empty.yaml"
    empty_file.write_text("")

    with pytest.raises(RubricValidationError, match="empty"):
        RubricLoader.load(str(empty_file))


# ============================================================================
# 14. RubricLoader — resolution chain: CLI wins over CWD
# ============================================================================


def test_resolve_cli_flag_wins(tmp_path):
    """Resolution chain: CLI flag path is used over CWD rubric.yaml."""
    # Create a CWD rubric with 2 dimensions
    cwd_rubric = tmp_path / "rubric.yaml"
    cwd_rubric.write_text(yaml.dump(_minimal_rubric_data()))

    # Create a CLI rubric with 1 dimension
    cli_rubric = tmp_path / "cli_rubric.yaml"
    cli_data = _minimal_rubric_data(
        dimensions={"only_one": {"weight": 1.0, "description": "CLI dim"}}
    )
    cli_rubric.write_text(yaml.dump(cli_data))

    with patch.object(Path, "cwd", return_value=tmp_path):
        result = RubricLoader.resolve(cli_rubric=str(cli_rubric))

    assert "only_one" in result.dimensions
    assert len(result.dimensions) == 1


# ============================================================================
# 15. RubricLoader — resolution chain: CWD wins over home
# ============================================================================


def test_resolve_cwd_wins_over_home(tmp_path):
    """Resolution chain: CWD rubric.yaml is used before home directory."""
    cwd_dir = tmp_path / "cwd"
    cwd_dir.mkdir()
    cwd_rubric = cwd_dir / "rubric.yaml"
    cwd_data = _minimal_rubric_data(
        dimensions={"cwd_dim": {"weight": 1.0, "description": "From CWD"}}
    )
    cwd_rubric.write_text(yaml.dump(cwd_data))

    home_dir = tmp_path / "home"
    home_dir.mkdir()
    home_md_evals = home_dir / ".md-evals"
    home_md_evals.mkdir()
    home_rubric = home_md_evals / "rubric.yaml"
    home_data = _minimal_rubric_data(
        dimensions={"home_dim": {"weight": 1.0, "description": "From home"}}
    )
    home_rubric.write_text(yaml.dump(home_data))

    with (
        patch.object(Path, "cwd", return_value=cwd_dir),
        patch.object(RubricLoader, "HOME_PATH", home_rubric),
    ):
        result = RubricLoader.resolve()

    assert "cwd_dim" in result.dimensions


# ============================================================================
# 16. Edge case — floating-point boundary
# ============================================================================


def test_weights_at_floating_point_boundary():
    """Weights summing to 0.9999999999999998 pass within tolerance."""
    data = _minimal_rubric_data(
        dimensions={
            "a": {"weight": 1 / 3},
            "b": {"weight": 1 / 3},
            "c": {"weight": 1 / 3},
        }
    )
    # 1/3 * 3 = 0.9999999999999998 in IEEE 754
    config = RubricConfig(**data)
    total = sum(d.weight for d in config.dimensions.values())
    assert abs(total - 1.0) < 0.001


# ============================================================================
# 17. Edge case — single dimension rubric
# ============================================================================


def test_single_dimension_rubric():
    """A rubric with exactly one dimension is valid."""
    data = _minimal_rubric_data(
        dimensions={"only": {"weight": 1.0, "description": "The only one"}}
    )
    config = RubricConfig(**data)
    assert len(config.dimensions) == 1
    assert config.dimensions["only"].weight == 1.0


# ============================================================================
# 18. Edge case — S grade optional
# ============================================================================


def test_s_grade_optional():
    """Rubric without S grade is valid; A is the top grade."""
    rubric = RubricLoader.load(str(FIXTURES_DIR / "rubric_no_s_grade.yaml"))
    assert "S" not in rubric.grade_thresholds
    assert "A" in rubric.grade_thresholds


# ============================================================================
# 19. Edge case — custom dimensions with description
# ============================================================================


def test_custom_dimensions_with_description_no_warning(caplog):
    """Custom dimension with a description does NOT produce a warning."""
    data = _minimal_rubric_data(
        dimensions={
            "correctness": {"weight": 0.50},
            "creativity": {"weight": 0.50, "description": "Novel solutions"},
        }
    )
    with caplog.at_level(logging.WARNING, logger="md_evals.rubric"):
        config = RubricConfig(**data)

    # "creativity" has a description → no warning
    creativity_warnings = [
        r for r in caplog.records if "creativity" in r.message
    ]
    assert len(creativity_warnings) == 0
    assert config.dimensions["creativity"].description == "Novel solutions"


# ============================================================================
# 20. Edge case — zero-weight dimension
# ============================================================================


def test_zero_weight_dimension():
    """A dimension with weight=0.0 is allowed if total sums to 1.0."""
    data = _minimal_rubric_data(
        dimensions={
            "main": {"weight": 1.0},
            "optional": {"weight": 0.0},
        }
    )
    config = RubricConfig(**data)
    assert config.dimensions["optional"].weight == 0.0
    total = sum(d.weight for d in config.dimensions.values())
    assert total == pytest.approx(1.0)


# ============================================================================
# 21. Additional validation edge cases
# ============================================================================


def test_threshold_out_of_range_rejected():
    """Grade threshold value of 0.0 (not in (0.0, 1.0]) is rejected."""
    data = _minimal_rubric_data(
        grade_thresholds={"A": 0.85, "B": 0.70, "C": 0.50, "D": 0.0}
    )
    with pytest.raises(RubricValidationError, match="must be in"):
        RubricConfig(**data)


def test_threshold_above_one_rejected():
    """Grade threshold value > 1.0 is rejected."""
    data = _minimal_rubric_data(
        grade_thresholds={"A": 1.5, "B": 0.70, "C": 0.50, "D": 0.30}
    )
    with pytest.raises(RubricValidationError, match="must be in"):
        RubricConfig(**data)


def test_unknown_grade_letter_rejected():
    """Unknown grade letter 'E' is rejected."""
    data = _minimal_rubric_data(
        grade_thresholds={"A": 0.85, "B": 0.70, "C": 0.50, "D": 0.30, "E": 0.10}
    )
    with pytest.raises(RubricValidationError, match="Unknown grade"):
        RubricConfig(**data)


def test_load_invalid_yaml_raises(tmp_path):
    """Malformed YAML raises RubricValidationError."""
    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text("version: [invalid\n  yaml: {broken")

    with pytest.raises(RubricValidationError, match="Invalid YAML"):
        RubricLoader.load(str(bad_yaml))


def test_pre_check_config_defaults():
    """PreCheckConfig defaults are applied when not specified."""
    data = _minimal_rubric_data()
    config = RubricConfig(**data)

    assert config.pre_check.max_lines == 400
    assert "Description" in config.pre_check.required_sections
    assert config.pre_check.security_patterns == []
