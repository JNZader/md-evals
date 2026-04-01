"""Mission runner — executes all test cases in a mission YAML file."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

import yaml

from md_evals.mission.models import (
    MissionConfig,
    MissionPassCriteria,
    MissionResult,
    MissionSummary,
    MissionTestCase,
    MissionTestResult,
)


class MissionLoadError(Exception):
    """Raised when a mission YAML file cannot be loaded or validated."""


class MissionRunner:
    """Loads and executes mission YAML files.

    The runner evaluates each test case against its pass criteria using
    deterministic evaluators (regex, exact-match) or delegates to an
    LLM adapter for llm-judge criteria.

    Args:
        llm_adapter: Optional LLM adapter for llm-judge criteria and
            prompt execution. When ``None``, llm-judge criteria are
            skipped and prompts are not sent to an LLM.
    """

    def __init__(self, llm_adapter: Any | None = None) -> None:
        self._llm_adapter = llm_adapter

    # ── Public API ──

    @staticmethod
    def load(path: str | Path) -> MissionConfig:
        """Load and validate a mission YAML file.

        Args:
            path: Path to the mission YAML file.

        Returns:
            Validated MissionConfig.

        Raises:
            MissionLoadError: If file is missing, invalid YAML, or fails
                Pydantic validation.
        """
        file_path = Path(path)
        if not file_path.exists():
            raise MissionLoadError(f"Mission file not found: {path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            raise MissionLoadError(f"Invalid YAML in {path}: {exc}")

        if data is None:
            raise MissionLoadError(f"Empty mission file: {path}")

        try:
            return MissionConfig(**data)
        except Exception as exc:
            raise MissionLoadError(f"Invalid mission config in {path}: {exc}")

    async def run(self, config: MissionConfig) -> MissionResult:
        """Execute all test cases in a mission.

        Args:
            config: Validated mission configuration.

        Returns:
            MissionResult with per-test outcomes and summary.
        """
        test_results: list[MissionTestResult] = []
        total_start = time.monotonic()

        for test_case in config.test_cases:
            result = await self._run_test_case(test_case, config)
            test_results.append(result)

        total_duration = int((time.monotonic() - total_start) * 1000)

        passed_count = sum(1 for r in test_results if r.passed)
        total_count = len(test_results)

        summary = MissionSummary(
            total=total_count,
            passed=passed_count,
            failed=total_count - passed_count,
            pass_rate=passed_count / total_count if total_count > 0 else 0.0,
            duration_ms=total_duration,
        )

        return MissionResult(
            mission_name=config.name,
            version=config.version,
            skill_under_test=config.skill_under_test,
            model=config.model,
            provider=config.provider,
            test_results=test_results,
            summary=summary,
            tags=config.tags,
        )

    def save_result(self, result: MissionResult, results_dir: str) -> Path:
        """Persist a mission result as JSON.

        Args:
            result: Mission result to save.
            results_dir: Directory for result files.

        Returns:
            Path to the saved JSON file.
        """
        dir_path = Path(results_dir)
        dir_path.mkdir(parents=True, exist_ok=True)

        # Sanitize mission name for filesystem
        safe_name = re.sub(r"[^\w\-]", "_", result.mission_name)
        timestamp = result.timestamp.replace(":", "-").replace("+", "_")
        filename = f"{safe_name}_{timestamp}.json"

        file_path = dir_path / filename
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(result.model_dump(mode="json"), f, indent=2, default=str)

        return file_path

    # ── Private ──

    async def _run_test_case(
        self,
        test_case: MissionTestCase,
        config: MissionConfig,
    ) -> MissionTestResult:
        """Execute a single test case and evaluate its criteria."""
        start = time.monotonic()

        # Build prompt with variable substitution
        prompt = test_case.prompt
        for key, value in test_case.variables.items():
            prompt = prompt.replace(f"{{{key}}}", value)

        # Get LLM response if adapter is available
        response_content = ""
        if self._llm_adapter is not None:
            try:
                from md_evals.llm import inject_skill

                final_prompt, system_prompt = inject_skill(
                    prompt, config.skill_under_test
                )
                response = await self._llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
                response_content = response.content
            except Exception as exc:
                duration = int((time.monotonic() - start) * 1000)
                return MissionTestResult(
                    test_name=test_case.name,
                    passed=False,
                    score=0.0,
                    error=f"LLM error: {exc}",
                    duration_ms=duration,
                )

        # Evaluate pass criteria
        criteria_results: list[dict[str, Any]] = []
        for criterion in test_case.pass_criteria:
            cr = self._evaluate_criterion(criterion, response_content)
            criteria_results.append(cr)

        duration = int((time.monotonic() - start) * 1000)

        all_passed = all(cr["passed"] for cr in criteria_results) if criteria_results else True
        avg_score = (
            sum(cr["score"] for cr in criteria_results) / len(criteria_results)
            if criteria_results
            else 1.0
        )

        return MissionTestResult(
            test_name=test_case.name,
            passed=all_passed,
            score=round(avg_score, 4),
            criteria_results=criteria_results,
            response_content=response_content,
            duration_ms=duration,
        )

    @staticmethod
    def _evaluate_criterion(
        criterion: MissionPassCriteria,
        content: str,
    ) -> dict[str, Any]:
        """Evaluate a single pass criterion against content."""
        if criterion.type == "regex":
            return MissionRunner._eval_regex(criterion, content)
        elif criterion.type == "exact-match":
            return MissionRunner._eval_exact_match(criterion, content)
        elif criterion.type == "llm-judge":
            # LLM-judge requires async; return pending for now
            return {
                "name": criterion.name,
                "type": "llm-judge",
                "passed": False,
                "score": 0.0,
                "reason": "LLM-judge evaluation not supported in sync mode",
            }
        elif criterion.type == "grader":
            return {
                "name": criterion.name,
                "type": "grader",
                "passed": False,
                "score": 0.0,
                "reason": f"Grader '{criterion.grader_type}' requires workspace context",
            }
        else:
            return {
                "name": criterion.name,
                "type": criterion.type,
                "passed": False,
                "score": 0.0,
                "reason": f"Unknown criterion type: {criterion.type}",
            }

    @staticmethod
    def _eval_regex(criterion: MissionPassCriteria, content: str) -> dict[str, Any]:
        """Evaluate regex criterion."""
        pattern = criterion.pattern or ""
        try:
            compiled = re.compile(pattern, re.MULTILINE | re.IGNORECASE)
            match = compiled.search(content)
            passed = match is not None if criterion.pass_on_match else match is None
            return {
                "name": criterion.name,
                "type": "regex",
                "passed": passed,
                "score": 1.0 if passed else 0.0,
                "reason": None if passed else f"Pattern '{pattern}' not matched",
            }
        except re.error as exc:
            return {
                "name": criterion.name,
                "type": "regex",
                "passed": False,
                "score": 0.0,
                "reason": f"Invalid regex: {exc}",
            }

    @staticmethod
    def _eval_exact_match(
        criterion: MissionPassCriteria, content: str
    ) -> dict[str, Any]:
        """Evaluate exact-match criterion."""
        expected = criterion.expected or ""
        if criterion.case_sensitive:
            passed = expected in content
        else:
            passed = expected.lower() in content.lower()

        return {
            "name": criterion.name,
            "type": "exact-match",
            "passed": passed,
            "score": 1.0 if passed else 0.0,
            "reason": None if passed else "Expected text not found",
        }
