"""Mode resolver for testing modes (smoke, reliable, regression)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from md_evals.models import TestingMode


@dataclass
class ModeDefaults:
    """Default execution parameters for a testing mode."""

    repetitions: int
    fail_fast: bool
    save_baseline: bool = False
    compare_baseline: bool = False


MODE_PRESETS: dict[str, ModeDefaults] = {
    "smoke": ModeDefaults(repetitions=1, fail_fast=True),
    "reliable": ModeDefaults(
        repetitions=5, fail_fast=False, save_baseline=True
    ),
    "regression": ModeDefaults(
        repetitions=3, fail_fast=False, compare_baseline=True
    ),
}


def resolve_mode(
    mode: "TestingMode | None",
    *,
    cli_count: int | None = None,
    cli_fail_fast: bool | None = None,
) -> ModeDefaults | None:
    """Resolve a testing mode into execution defaults.

    CLI overrides always win over mode presets.

    Args:
        mode: The testing mode name, or None for default behavior.
        cli_count: Explicit --count from CLI (overrides preset repetitions).
        cli_fail_fast: Explicit --fail-fast from CLI (overrides preset).

    Returns:
        ModeDefaults with resolved values, or None if no mode specified.
    """
    if mode is None:
        return None

    preset = MODE_PRESETS.get(mode)
    if preset is None:
        return None

    # Start from preset, apply CLI overrides
    return ModeDefaults(
        repetitions=cli_count if cli_count is not None else preset.repetitions,
        fail_fast=cli_fail_fast if cli_fail_fast is not None else preset.fail_fast,
        save_baseline=preset.save_baseline,
        compare_baseline=preset.compare_baseline,
    )
