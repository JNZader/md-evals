"""Built-in detectors — response scorers for the evaluation pipeline.

Provides three detectors that satisfy the
:class:`~md_evals.pipeline.protocols.Detector` protocol, plus an
aggregation function:

* :class:`LLMJudgeDetector` — uses a judge LLM to score
  (scenario, response) pairs with structured JSON output.
* :class:`FormatDetector` — regex-based structural quality checks
  (headings, code blocks, lists, line length).  Zero LLM calls.
* :class:`SecurityDetector` — pattern-matching for dangerous content
  (hardcoded secrets, dangerous commands, permissive permissions).
  Zero LLM calls.
* :func:`aggregate_detector_scores` — combines scores from multiple
  detectors into one :class:`DimensionScore` per unique dimension.

All detectors follow these design principles:

* **Graceful degradation** (REQ-SP07): LLM errors produce a score of
  0.0 with an error rationale — never an exception.
* **Deterministic free detectors**: ``FormatDetector`` and
  ``SecurityDetector`` make zero LLM calls and produce fully
  reproducible scores.
* **Clamped scores**: all returned scores are in ``[0.0, 1.0]``.

Design notes
------------
* Detectors access the judge LLM via ``context.metadata["judge_adapter"]``,
  which is an :class:`~md_evals.llm.LLMAdapter` instance injected by the
  judge stage before invoking detectors.
* ``score()`` is synchronous per the protocol, but calls the async LLM
  adapter via ``asyncio`` when needed (same pattern as probes).
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import TYPE_CHECKING, Any

from md_evals.scoring import DimensionScore, score_to_grade

if TYPE_CHECKING:
    from md_evals.llm import LLMAdapter
    from md_evals.pipeline.context import EvalContext, Scenario
    from md_evals.pipeline.skill_parser import ParsedSkill

logger = logging.getLogger(__name__)


# ─── Default grade thresholds (used when rubric is unavailable) ───

_DEFAULT_THRESHOLDS: dict[str, float] = {
    "A": 0.90,
    "B": 0.75,
    "C": 0.60,
    "D": 0.40,
}


# ─── Helpers ───


def _run_llm_complete(
    adapter: LLMAdapter,
    prompt: str,
    system_prompt: str | None = None,
    temperature: float | None = None,
) -> str | None:
    """Run an async LLM completion synchronously.

    Handles event loop detection: if already inside an async context,
    creates a new event loop in a thread to avoid ``RuntimeError``.

    Args:
        adapter: The LLM adapter to call.
        prompt: User prompt.
        system_prompt: Optional system prompt.
        temperature: Optional temperature override.

    Returns:
        The LLM response content string, or ``None`` on any error.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    async def _call() -> str:
        resp = await adapter.complete(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            stage_type="judge",
        )
        return resp.content

    try:
        if loop is not None and loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(asyncio.run, _call())
                return future.result(timeout=120)
        else:
            return asyncio.run(_call())
    except Exception as exc:
        logger.warning("LLM call failed in detector: %s", exc)
        return None


def _extract_json_object(text: str) -> dict[str, Any] | None:
    """Extract a JSON object from an LLM response, with fallback strategies.

    Tries in order:

    1. Direct ``json.loads`` on the full text.
    2. Regex extraction of the first ``{...}`` block.

    Args:
        text: Raw LLM response text that should contain a JSON object.

    Returns:
        A dict parsed from the response, or ``None`` if extraction fails.
    """
    # Strategy 1: direct parse
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except (json.JSONDecodeError, TypeError):
        pass

    # Strategy 2: extract first {...} block (greedy to get nested braces)
    match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass

    return None


def _get_thresholds(context: EvalContext) -> dict[str, float]:
    """Extract grade thresholds from context rubric, or return defaults.

    Args:
        context: Pipeline context that may carry a rubric.

    Returns:
        Grade threshold mapping.
    """
    try:
        if context.rubric is not None and hasattr(context.rubric, "grade_thresholds"):
            return context.rubric.grade_thresholds
    except (AttributeError, TypeError):
        pass
    return _DEFAULT_THRESHOLDS


# ─── LLMJudgeDetector ───


class LLMJudgeDetector:
    """Detector that uses a judge LLM to score responses.

    Sends a structured prompt to the judge LLM requesting a JSON
    response with ``score``, ``rationale``, and ``dimension`` fields.
    Includes pre-check findings from the context when available to
    give the judge additional context.

    On parse failure or LLM error, returns a :class:`DimensionScore`
    with ``score=0.0``.

    Args:
        target_dimension: The rubric dimension to score.  Defaults to
            the scenario's dimension at scoring time.

    Example
    -------
    >>> detector = LLMJudgeDetector()
    >>> detector.name
    'llm-judge'
    >>> detector.dimension
    'general'
    """

    def __init__(self, target_dimension: str = "general") -> None:
        self._dimension = target_dimension

    @property
    def name(self) -> str:
        """Short detector identifier."""
        return "llm-judge"

    @property
    def dimension(self) -> str:
        """Rubric dimension this detector targets."""
        return self._dimension

    def score(
        self,
        scenario: Scenario,
        response: str,
        skill: ParsedSkill,
        context: EvalContext,
    ) -> DimensionScore:
        """Score a response using the judge LLM.

        Constructs a structured prompt that includes the scenario,
        response, skill context, and any pre-check findings.  Parses
        the LLM's JSON response and returns a clamped score.

        Args:
            scenario: The test scenario that produced the response.
            response: Raw text response from the target LLM.
            skill: Structured representation of the SKILL.md file.
            context: Pipeline context carrying judge adapter and rubric.

        Returns:
            A :class:`DimensionScore` with score in ``[0.0, 1.0]``.
        """
        adapter: LLMAdapter | None = context.metadata.get("judge_adapter")
        thresholds = _get_thresholds(context)

        # Resolve effective dimension
        effective_dim = scenario.dimension or self._dimension

        if adapter is None:
            logger.warning(
                "LLMJudgeDetector: no judge_adapter in context, returning 0.0"
            )
            return DimensionScore(
                dimension=effective_dim,
                score=0.0,
                weight=0.0,
                grade=score_to_grade(0.0, thresholds),
            )

        # Build the judge prompt
        prompt = self._build_prompt(scenario, response, skill, context)
        content = _run_llm_complete(adapter, prompt, temperature=0.0)

        if content is None:
            return DimensionScore(
                dimension=effective_dim,
                score=0.0,
                weight=0.0,
                grade=score_to_grade(0.0, thresholds),
                evidence=["LLM judge call failed"],
            )

        # Parse JSON response
        result = _extract_json_object(content)
        if result is None:
            logger.warning(
                "LLMJudgeDetector: failed to parse JSON from judge response"
            )
            return DimensionScore(
                dimension=effective_dim,
                score=0.0,
                weight=0.0,
                grade=score_to_grade(0.0, thresholds),
                evidence=["Failed to parse judge response as JSON"],
            )

        # Extract and clamp score
        raw_score = result.get("score", 0.0)
        try:
            numeric_score = float(raw_score)
        except (ValueError, TypeError):
            numeric_score = 0.0
        clamped = max(0.0, min(1.0, numeric_score))

        rationale = str(result.get("rationale", ""))
        dim_from_judge = result.get("dimension", effective_dim)

        evidence_items: list[str] = []
        if rationale:
            evidence_items.append(rationale)

        return DimensionScore(
            dimension=dim_from_judge if dim_from_judge else effective_dim,
            score=clamped,
            weight=0.0,  # Weight is set during aggregation from rubric
            grade=score_to_grade(clamped, thresholds),
            evidence=evidence_items,
        )

    # ── Private helpers ──

    def _build_prompt(
        self,
        scenario: Scenario,
        response: str,
        skill: ParsedSkill,
        context: EvalContext,
    ) -> str:
        """Build the structured judge prompt.

        Includes scenario details, the target's response, skill context,
        and any pre-check findings for additional context.

        Args:
            scenario: The test scenario.
            response: The target LLM's response.
            skill: Parsed skill content.
            context: Pipeline context with optional pre-check results.

        Returns:
            Formatted prompt string.
        """
        parts: list[str] = [
            "You are an expert evaluator. Score the following LLM response "
            "against the given test scenario and skill guidelines.",
            "",
            f"## Skill: {skill.title or 'Untitled'}",
        ]

        if skill.description:
            parts.append(f"Description: {skill.description[:500]}")

        if skill.rules:
            parts.append("\n## Relevant Rules:")
            for rule in skill.rules[:10]:
                parts.append(f"- {rule}")

        parts.extend([
            "",
            f"## Test Scenario",
            f"Prompt: {scenario.prompt}",
            f"Expected behavior: {scenario.expected_behavior}",
            f"Dimension: {scenario.dimension or 'general'}",
            "",
            f"## Target Response",
            response[:3000],
        ])

        # Include pre-check findings if available
        if context.pre_check_result is not None:
            try:
                findings = context.pre_check_result.findings
                if findings:
                    parts.append("\n## Pre-check Findings:")
                    for finding in findings[:5]:
                        parts.append(
                            f"- [{finding.severity}] {finding.message}"
                        )
            except AttributeError:
                pass

        parts.extend([
            "",
            "## Instructions",
            "Evaluate the response and return a JSON object with exactly "
            "these fields:",
            '{"score": <float 0.0-1.0>, "rationale": "<explanation>", '
            '"dimension": "<dimension name>"}',
            "",
            "Score 1.0 = perfect, 0.0 = completely wrong. Be precise.",
            "Return ONLY the JSON object, no other text.",
        ])

        return "\n".join(parts)


# ─── FormatDetector ───


class FormatDetector:
    """Detector that evaluates structural formatting quality.

    Performs regex-based checks with **zero LLM calls**.  Evaluates:

    1. **Headings** — response contains markdown headings (``#``).
    2. **Code blocks** — response uses fenced code blocks (````` ``` `````).
    3. **Lists** — response contains bullet or numbered lists.
    4. **Consistent indentation** — no mixed tabs and spaces.
    5. **Line length** — no lines exceeding 200 characters.

    Score is computed as ``checks_passed / total_checks``.

    Example
    -------
    >>> detector = FormatDetector()
    >>> detector.name
    'format'
    >>> detector.dimension
    'format'
    """

    _TOTAL_CHECKS = 5

    @property
    def name(self) -> str:
        """Short detector identifier."""
        return "format"

    @property
    def dimension(self) -> str:
        """Rubric dimension this detector targets."""
        return "format"

    def score(
        self,
        scenario: Scenario,
        response: str,
        skill: ParsedSkill,
        context: EvalContext,
    ) -> DimensionScore:
        """Score the response's structural formatting quality.

        Runs five deterministic checks and returns a score equal to
        the fraction of checks that pass.

        Args:
            scenario: The test scenario (used for metadata only).
            response: Raw text response from the target LLM.
            skill: Structured representation of the SKILL.md (unused).
            context: Pipeline context (used for grade thresholds).

        Returns:
            A :class:`DimensionScore` with ``dimension="format"``.
        """
        thresholds = _get_thresholds(context)
        checks_passed = 0
        evidence: list[str] = []

        # Check 1: Has headings
        if re.search(r"^#{1,6}\s+\S", response, re.MULTILINE):
            checks_passed += 1
            evidence.append("Has markdown headings: PASS")
        else:
            evidence.append("Has markdown headings: FAIL")

        # Check 2: Has fenced code blocks
        if re.search(r"^```", response, re.MULTILINE):
            checks_passed += 1
            evidence.append("Has fenced code blocks: PASS")
        else:
            evidence.append("Has fenced code blocks: FAIL")

        # Check 3: Has lists (bullet or numbered)
        if re.search(r"^[\s]*[-*•]\s+\S|^\s*\d+\.\s+\S", response, re.MULTILINE):
            checks_passed += 1
            evidence.append("Has lists: PASS")
        else:
            evidence.append("Has lists: FAIL")

        # Check 4: Consistent indentation (no mixed tabs and spaces)
        lines = response.splitlines()
        has_tab_indent = any(line.startswith("\t") for line in lines if line.strip())
        has_space_indent = any(
            re.match(r"^ {2,}", line) for line in lines if line.strip()
        )
        if not (has_tab_indent and has_space_indent):
            checks_passed += 1
            evidence.append("Consistent indentation: PASS")
        else:
            evidence.append("Consistent indentation: FAIL (mixed tabs and spaces)")

        # Check 5: No very long lines (> 200 chars, excluding code blocks)
        in_code_block = False
        has_long_lines = False
        for line in lines:
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue
            if not in_code_block and len(line) > 200:
                has_long_lines = True
                break

        if not has_long_lines:
            checks_passed += 1
            evidence.append("No very long lines: PASS")
        else:
            evidence.append("No very long lines: FAIL (>200 chars)")

        final_score = checks_passed / self._TOTAL_CHECKS

        return DimensionScore(
            dimension="format",
            score=final_score,
            weight=0.0,  # Weight is set during aggregation from rubric
            grade=score_to_grade(final_score, thresholds),
            evidence=evidence,
        )


# ─── SecurityDetector ───


# Hardcoded security patterns — common dangerous content patterns
_SECURITY_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Hardcoded secrets and credentials
    (
        re.compile(
            r"""(?:api[_-]?key|secret|password|token|credential)\s*[:=]\s*['"][^'"]{8,}['"]""",
            re.IGNORECASE,
        ),
        "Potential hardcoded secret or credential",
    ),
    (
        re.compile(r"(?:AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}"),
        "Potential AWS access key",
    ),
    (
        re.compile(r"ghp_[A-Za-z0-9]{36}"),
        "Potential GitHub personal access token",
    ),
    # Dangerous commands
    (
        re.compile(r"\brm\s+-rf\s+/\b"),
        "Dangerous recursive delete from root",
    ),
    (
        re.compile(r"\bchmod\s+777\b"),
        "Permissive file permission (777)",
    ),
    (
        re.compile(r"\bcurl\b.*\|\s*(?:sudo\s+)?(?:ba)?sh\b"),
        "Piping curl output to shell execution",
    ),
    # Permissive configurations
    (
        re.compile(r"(?:disable|skip|no)[_-]?(?:ssl|tls|verify|auth)", re.IGNORECASE),
        "Disabled security feature (SSL/TLS/auth verification)",
    ),
    (
        re.compile(r"\b0\.0\.0\.0\b.*(?:listen|bind|host)", re.IGNORECASE),
        "Binding to all interfaces (0.0.0.0)",
    ),
    # SQL injection patterns in examples
    (
        re.compile(r"""f['"].*\{.*\}.*(?:SELECT|INSERT|UPDATE|DELETE|DROP)\b""", re.IGNORECASE),
        "Potential SQL injection via f-string interpolation",
    ),
]


class SecurityDetector:
    """Detector that scans for security anti-patterns in responses.

    Performs pattern matching with **zero LLM calls**.  Checks for:

    * Hardcoded secrets and credentials (API keys, AWS keys, tokens).
    * Dangerous shell commands (``rm -rf /``, ``chmod 777``).
    * Insecure configurations (disabled SSL, binding to 0.0.0.0).
    * SQL injection patterns (f-string interpolation in SQL).

    Scoring: starts at 1.0 and subtracts 0.2 per issue found,
    with a minimum of 0.0.

    Example
    -------
    >>> detector = SecurityDetector()
    >>> detector.name
    'security'
    >>> detector.dimension
    'safety'
    """

    _PENALTY_PER_ISSUE = 0.2

    @property
    def name(self) -> str:
        """Short detector identifier."""
        return "security"

    @property
    def dimension(self) -> str:
        """Rubric dimension this detector targets."""
        return "safety"

    def score(
        self,
        scenario: Scenario,
        response: str,
        skill: ParsedSkill,
        context: EvalContext,
    ) -> DimensionScore:
        """Score the response for security anti-patterns.

        Scans the response against a list of security patterns and
        penalises each match.  Score starts at 1.0 and drops by
        0.2 per issue (minimum 0.0).

        Args:
            scenario: The test scenario (used for metadata only).
            response: Raw text response from the target LLM.
            skill: Structured representation of the SKILL.md (unused).
            context: Pipeline context (used for grade thresholds).

        Returns:
            A :class:`DimensionScore` with ``dimension="safety"``.
        """
        thresholds = _get_thresholds(context)
        issues: list[str] = []

        for pattern, message in _SECURITY_PATTERNS:
            matches = pattern.findall(response)
            if matches:
                issues.append(f"{message} ({len(matches)} occurrence(s))")

        # Calculate score
        penalty = len(issues) * self._PENALTY_PER_ISSUE
        final_score = max(0.0, 1.0 - penalty)

        evidence: list[str]
        if issues:
            evidence = [f"Security issue: {issue}" for issue in issues]
        else:
            evidence = ["No security issues detected"]

        return DimensionScore(
            dimension="safety",
            score=final_score,
            weight=0.0,  # Weight is set during aggregation from rubric
            grade=score_to_grade(final_score, thresholds),
            evidence=evidence,
        )


# ─── Aggregation ───


def aggregate_detector_scores(
    scores: list[DimensionScore],
    weights: dict[str, float] | None = None,
) -> list[DimensionScore]:
    """Aggregate multiple detector scores per dimension.

    When multiple detectors score the same dimension (e.g. both
    ``LLMJudgeDetector`` and ``FormatDetector`` score "format"),
    this function combines them into a single weighted score per
    unique dimension.

    Default weights:

    * LLM-based detectors (``llm-judge``): ``0.7``
    * Free detectors (``format``, ``security``, etc.): ``0.3``

    If ``weights`` is provided, it maps detector names to weight
    values.  Detectors not in the map default to ``0.5``.

    Args:
        scores: List of :class:`DimensionScore` objects from all
            detectors.  Each score's ``evidence`` list should include
            a ``"detector:<name>"`` entry for proper weight resolution
            (falls back to default weight if missing).
        weights: Optional mapping of detector name → weight.  If
            ``None``, default LLM/free weights are applied.

    Returns:
        A list of :class:`DimensionScore` objects — one per unique
        dimension — with aggregated scores and merged evidence.
    """
    if not scores:
        return []

    # Default weight strategy: LLM detectors get 0.7, free detectors 0.3
    default_weights: dict[str, float] = {
        "llm-judge": 0.7,
        "format": 0.3,
        "security": 0.3,
    }
    effective_weights = weights if weights is not None else default_weights

    # Group scores by dimension
    grouped: dict[str, list[tuple[DimensionScore, float]]] = {}
    for ds in scores:
        dim = ds.dimension
        if dim not in grouped:
            grouped[dim] = []

        # Resolve detector name from evidence
        detector_name = _extract_detector_name(ds)
        w = effective_weights.get(detector_name, 0.5)
        grouped[dim].append((ds, w))

    # Aggregate each dimension
    result: list[DimensionScore] = []
    for dim, scored_pairs in grouped.items():
        total_weight = sum(w for _, w in scored_pairs)

        if total_weight == 0.0:
            # Degenerate case — simple average
            avg_score = (
                sum(ds.score for ds, _ in scored_pairs) / len(scored_pairs)
            )
        else:
            avg_score = (
                sum(ds.score * w for ds, w in scored_pairs) / total_weight
            )

        clamped = max(0.0, min(1.0, avg_score))

        # Merge evidence from all detectors
        merged_evidence: list[str] = []
        for ds, _ in scored_pairs:
            merged_evidence.extend(ds.evidence)

        # Use the maximum rubric weight from constituent scores
        max_rubric_weight = max(ds.weight for ds, _ in scored_pairs)

        # Get thresholds from first score's grade context — rebuild grade
        # Use default thresholds for aggregated grade
        grade = score_to_grade(clamped, _DEFAULT_THRESHOLDS)

        result.append(
            DimensionScore(
                dimension=dim,
                score=round(clamped, 4),
                weight=max_rubric_weight,
                grade=grade,
                evidence=merged_evidence,
            )
        )

    return result


def _extract_detector_name(ds: DimensionScore) -> str:
    """Extract the detector name from a DimensionScore's evidence.

    Looks for evidence entries matching ``"detector:<name>"`` pattern.

    Args:
        ds: A dimension score with evidence list.

    Returns:
        The detector name, or ``"unknown"`` if not found.
    """
    for item in ds.evidence:
        if item.startswith("detector:"):
            return item.split(":", 1)[1].strip()
    return "unknown"
