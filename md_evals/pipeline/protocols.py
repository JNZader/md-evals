"""Pipeline protocols — structural interfaces for stages, probes, and detectors.

Defines the three core extension points of the pipeline using
``typing.Protocol`` (ADR-01: Protocols, Not ABCs).  Any class that
implements the required shape satisfies the contract — no inheritance
or import of these types is needed by plugin authors.

All protocols are ``@runtime_checkable`` so that ``isinstance()`` checks
work at runtime for validation and debugging.

Design notes
------------
* ``from __future__ import annotations`` + ``TYPE_CHECKING`` guard keeps
  this module dependency-free at runtime.  Only type checkers resolve the
  forward references.
* Property-based ``name`` (and ``dimension`` on ``Detector``) avoids
  requiring ``__init__`` parameter conventions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from md_evals.pipeline.context import EvalContext, Scenario, StageResult
    from md_evals.pipeline.skill_parser import ParsedSkill
    from md_evals.scoring import DimensionScore


@runtime_checkable
class PipelineStage(Protocol):
    """Protocol for pipeline execution stages.

    Each stage reads from and writes to a shared :class:`EvalContext`,
    returning a :class:`StageResult` indicating success or failure with
    timing information.

    Implementers must provide:

    ``name``
        A human-readable identifier for logging and error reporting.
    ``execute(context)``
        The async entry point.  Receives the mutable context, performs
        its work, and returns a frozen ``StageResult``.

    Example
    -------
    >>> class MyStage:
    ...     @property
    ...     def name(self) -> str:
    ...         return "my-stage"
    ...     async def execute(self, context):
    ...         # ... do work ...
    ...         return StageResult(success=True, duration_ms=42)
    """

    @property
    def name(self) -> str:
        """Human-readable stage identifier."""
        ...

    async def execute(self, context: EvalContext) -> StageResult:
        """Run the stage against *context* and return a result.

        Stages SHOULD NOT raise exceptions — capture errors in the
        returned ``StageResult`` instead.  The pipeline orchestrator
        wraps execution with a timeout and exception handler regardless.

        Args:
            context: The mutable evaluation context shared across stages.

        Returns:
            A frozen ``StageResult`` with success flag, timing, and
            optional error message.
        """
        ...


@runtime_checkable
class Probe(Protocol):
    """Protocol for scenario generators (what to test).

    Probes analyse a parsed skill and produce a list of
    :class:`Scenario` objects that the auditor stage feeds into the
    target LLM.  Probes may be purely deterministic or may themselves
    call an LLM (via the auditor adapter on ``context``).

    Implementers must provide:

    ``name``
        A short identifier used in configuration and logging.
    ``generate_scenarios(skill, context)``
        Produces one or more scenarios targeting the skill under test.

    Example
    -------
    >>> class GreetingProbe:
    ...     @property
    ...     def name(self) -> str:
    ...         return "greeting"
    ...     def generate_scenarios(self, skill, context):
    ...         return [Scenario(probe_name="greeting", prompt="Say hello")]
    """

    @property
    def name(self) -> str:
        """Short probe identifier (e.g. ``"dimension"``, ``"edge-case"``)."""
        ...

    def generate_scenarios(
        self,
        skill: ParsedSkill,
        context: EvalContext,
    ) -> list[Scenario]:
        """Generate test scenarios from the parsed skill.

        Args:
            skill: Structured representation of the SKILL.md file.
            context: Pipeline context (may carry rubric, config, etc.).

        Returns:
            A list of ``Scenario`` objects.  An empty list is valid
            (probe found nothing applicable).
        """
        ...


@runtime_checkable
class Detector(Protocol):
    """Protocol for response scorers (how to judge).

    Detectors evaluate a (scenario, response) pair and produce a
    :class:`DimensionScore` for a specific rubric dimension.  They may
    use LLM-based judgement or purely deterministic pattern matching.

    Implementers must provide:

    ``name``
        A short identifier used in configuration and logging.
    ``dimension``
        The rubric dimension this detector scores (e.g. ``"format"``).
    ``score(scenario, response, skill, context)``
        Evaluate the response and return a ``DimensionScore``.

    Example
    -------
    >>> class LengthDetector:
    ...     @property
    ...     def name(self) -> str:
    ...         return "length-check"
    ...     @property
    ...     def dimension(self) -> str:
    ...         return "completeness"
    ...     def score(self, scenario, response, skill, context):
    ...         s = min(len(response) / 500, 1.0)
    ...         return DimensionScore(dimension="completeness", score=s, weight=0.2, grade="B")
    """

    @property
    def name(self) -> str:
        """Short detector identifier (e.g. ``"llm-judge"``, ``"format"``)."""
        ...

    @property
    def dimension(self) -> str:
        """Rubric dimension this detector targets (e.g. ``"safety"``)."""
        ...

    def score(
        self,
        scenario: Scenario,
        response: str,
        skill: ParsedSkill,
        context: EvalContext,
    ) -> DimensionScore:
        """Score a response for this detector's dimension.

        Args:
            scenario: The test scenario that produced the response.
            response: Raw text response from the target LLM.
            skill: Structured representation of the SKILL.md file.
            context: Pipeline context (may carry rubric, config, etc.).

        Returns:
            A frozen ``DimensionScore`` with score in ``[0.0, 1.0]``.
        """
        ...
