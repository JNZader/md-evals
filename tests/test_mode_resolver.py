"""Tests for md_evals.mode_resolver."""

import pytest

from md_evals.mode_resolver import MODE_PRESETS, resolve_mode


class TestModePresets:
    """Verify MODE_PRESETS contain correct defaults."""

    def test_smoke_preset(self):
        preset = MODE_PRESETS["smoke"]
        assert preset.repetitions == 1
        assert preset.fail_fast is True
        assert preset.save_baseline is False
        assert preset.compare_baseline is False

    def test_reliable_preset(self):
        preset = MODE_PRESETS["reliable"]
        assert preset.repetitions == 5
        assert preset.fail_fast is False
        assert preset.save_baseline is True
        assert preset.compare_baseline is False

    def test_regression_preset(self):
        preset = MODE_PRESETS["regression"]
        assert preset.repetitions == 3
        assert preset.fail_fast is False
        assert preset.save_baseline is False
        assert preset.compare_baseline is True


class TestResolveMode:
    """Test resolve_mode function."""

    def test_none_mode_returns_none(self):
        result = resolve_mode(None)
        assert result is None

    def test_invalid_mode_returns_none(self):
        result = resolve_mode("nonexistent")  # type: ignore
        assert result is None

    @pytest.mark.parametrize(
        "mode,expected_reps,expected_ff",
        [
            ("smoke", 1, True),
            ("reliable", 5, False),
            ("regression", 3, False),
        ],
    )
    def test_mode_returns_correct_defaults(self, mode, expected_reps, expected_ff):
        result = resolve_mode(mode)  # type: ignore
        assert result is not None
        assert result.repetitions == expected_reps
        assert result.fail_fast == expected_ff

    def test_cli_count_overrides_preset(self):
        result = resolve_mode("reliable", cli_count=10)  # type: ignore
        assert result is not None
        assert result.repetitions == 10
        # Other fields still from preset
        assert result.fail_fast is False
        assert result.save_baseline is True

    def test_cli_fail_fast_overrides_preset(self):
        result = resolve_mode("reliable", cli_fail_fast=True)  # type: ignore
        assert result is not None
        assert result.fail_fast is True
        # Repetitions still from preset
        assert result.repetitions == 5

    def test_cli_both_overrides(self):
        result = resolve_mode("smoke", cli_count=3, cli_fail_fast=False)  # type: ignore
        assert result is not None
        assert result.repetitions == 3
        assert result.fail_fast is False

    def test_baseline_flags_not_overridable(self):
        """save_baseline and compare_baseline come from preset only."""
        result = resolve_mode("regression")  # type: ignore
        assert result is not None
        assert result.compare_baseline is True
        assert result.save_baseline is False
