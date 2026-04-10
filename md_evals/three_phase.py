"""Three-phase evaluation pipeline: Structure -> Analyze -> Generate.

Orchestrates deterministic evaluation in three sequential phases:

1. **Structure** — validate input/output format (JSON valid? fields present?).
2. **Analyze** — evaluate quality of analysis (keywords, sections, depth).
3. **Generate** — evaluate final output quality (pattern match, constraints).

Each phase is independently testable and uses the existing Grader protocol.
Phases execute sequentially: if Structure fails, Analyze and Generate are
skipped (fail-fast by default, configurable).

The evaluator operates on a workspace directory (same as WorkspaceRunner)
or on raw string content for lightweight in-memory evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from md_evals.models import EvaluatorResult


class Phase(str, Enum):
    """Evaluation phase identifiers."""

    STRUCTURE = "structure"
    ANALYZE = "analyze"
    GENERATE = "generate"


@dataclass(frozen=True)
class PhaseResult:
    """Result from a single evaluation phase.

    Attributes:
        phase: Which phase produced this result.
        passed: True if ALL graders in the phase passed.
        grader_results: Individual results from each grader.
        skipped: True if this phase was skipped (prior phase failed).
    """

    phase: Phase
    passed: bool
    grader_results: list[EvaluatorResult] = field(default_factory=list)
    skipped: bool = False


@dataclass(frozen=True)
class ThreePhaseResult:
    """Complete result from the three-phase evaluation pipeline.

    Attributes:
        passed: True if ALL phases passed.
        phases: Results for each phase (always 3 entries).
        overall_score: Weighted average across all phases (0.0-1.0).
        failed_phase: The first phase that failed, or None if all passed.
    """

    passed: bool
    phases: list[PhaseResult] = field(default_factory=list)
    overall_score: float = 0.0
    failed_phase: Phase | None = None


@dataclass
class PhaseConfig:
    """Configuration for a single phase.

    Attributes:
        graders: List of graders to apply in this phase.
        weight: Weight for scoring (0.0-1.0). Weights across phases
            should sum to 1.0 but are normalized if they don't.
        required: If True, failure in this phase stops subsequent phases.
    """

    graders: list[Any] = field(default_factory=list)  # list[Grader]
    weight: float = 1.0
    required: bool = True


class ThreePhaseEvaluator:
    """Orchestrates the three-phase evaluation pipeline.

    Each phase contains a list of graders.  Phases execute in order:
    Structure -> Analyze -> Generate.  If a required phase fails,
    subsequent phases are skipped.

    Example::

        evaluator = ThreePhaseEvaluator(
            structure=PhaseConfig(graders=[JSONValidGrader(...)]),
            analyze=PhaseConfig(graders=[KeywordCoverageGrader(...)]),
            generate=PhaseConfig(graders=[OutputMatchGrader(...)]),
        )
        result = evaluator.evaluate(workspace_path)
    """

    def __init__(
        self,
        structure: PhaseConfig | None = None,
        analyze: PhaseConfig | None = None,
        generate: PhaseConfig | None = None,
    ) -> None:
        self._phases: dict[Phase, PhaseConfig] = {
            Phase.STRUCTURE: structure or PhaseConfig(),
            Phase.ANALYZE: analyze or PhaseConfig(),
            Phase.GENERATE: generate or PhaseConfig(),
        }

    def evaluate(self, workspace: Path) -> ThreePhaseResult:
        """Run all three phases against a workspace directory.

        Args:
            workspace: Root directory containing files to evaluate.

        Returns:
            ThreePhaseResult with per-phase and overall results.
        """
        phase_results: list[PhaseResult] = []
        failed_phase: Phase | None = None
        stop = False

        for phase in (Phase.STRUCTURE, Phase.ANALYZE, Phase.GENERATE):
            config = self._phases[phase]

            if stop:
                phase_results.append(
                    PhaseResult(phase=phase, passed=False, skipped=True)
                )
                continue

            grader_results = self._run_graders(config.graders, workspace)
            passed = all(r.passed for r in grader_results) if grader_results else True

            phase_results.append(
                PhaseResult(
                    phase=phase,
                    passed=passed,
                    grader_results=grader_results,
                )
            )

            if not passed and config.required:
                failed_phase = phase
                stop = True

        overall_score = self._calculate_score(phase_results)
        all_passed = all(pr.passed for pr in phase_results)

        return ThreePhaseResult(
            passed=all_passed,
            phases=phase_results,
            overall_score=overall_score,
            failed_phase=None if all_passed else failed_phase,
        )

    def evaluate_content(self, content: str) -> ThreePhaseResult:
        """Run all three phases against raw string content.

        Creates a temporary workspace with the content as ``output.json``
        for graders that work in file mode, but primarily passes content
        through graders that support the ``content`` parameter.

        This is a convenience method for testing without a real workspace.

        Args:
            content: Raw string to evaluate.

        Returns:
            ThreePhaseResult with per-phase and overall results.
        """
        import tempfile
        import shutil

        workspace = Path(tempfile.mkdtemp(prefix="three_phase_eval_"))
        try:
            # Write content as output.json for file-based graders
            (workspace / "output.json").write_text(content, encoding="utf-8")
            return self.evaluate(workspace)
        finally:
            shutil.rmtree(workspace, ignore_errors=True)

    @staticmethod
    def _run_graders(
        graders: list[Any], workspace: Path
    ) -> list[EvaluatorResult]:
        """Execute all graders against the workspace."""
        results: list[EvaluatorResult] = []
        for grader in graders:
            result = grader.grade(workspace)
            results.append(result)
        return results

    def _calculate_score(self, phase_results: list[PhaseResult]) -> float:
        """Calculate weighted average score across all phases."""
        total_weight = 0.0
        weighted_sum = 0.0

        for pr in phase_results:
            phase = pr.phase
            config = self._phases[phase]

            if pr.skipped:
                # Skipped phases contribute 0 score at their weight
                total_weight += config.weight
                continue

            if pr.grader_results:
                phase_score = sum(r.score for r in pr.grader_results) / len(
                    pr.grader_results
                )
            else:
                phase_score = 1.0  # Empty phase = pass

            weighted_sum += phase_score * config.weight
            total_weight += config.weight

        if total_weight == 0.0:
            return 0.0

        return round(weighted_sum / total_weight, 4)
