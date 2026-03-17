"""Gherkin-like eval scenario parser and probe.

Allows SKILL.md authors to embed acceptance criteria using Given/When/Then
syntax in ``## Scenarios`` or ``## Acceptance Criteria`` sections.

Phase 3 — Trust & Verification (Feature #10):

* :class:`GherkinScenario` — frozen dataclass for a parsed scenario.
* :func:`parse_gherkin_scenarios` — extracts Gherkin scenarios from content.
* :class:`GherkinProbe` — pipeline probe that converts Gherkin scenarios
  into :class:`~md_evals.pipeline.context.Scenario` objects.

Supported formats
-----------------
Block format::

    Given a React component with useState
    When the skill is applied
    Then the output should not contain useMemo

Bullet format::

    - Given a React component with useState
      When the skill is applied
      Then the output should not contain useMemo

Both ``## Scenarios`` and ``## Acceptance Criteria`` section headings
are recognized.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from md_evals.pipeline.context import Scenario

if TYPE_CHECKING:
    from md_evals.pipeline.context import EvalContext
    from md_evals.pipeline.skill_parser import ParsedSkill

logger = logging.getLogger(__name__)


# ─── Data Classes ───


@dataclass(frozen=True)
class GherkinScenario:
    """A parsed Given/When/Then scenario.

    Frozen value object representing a single Gherkin-style acceptance
    criterion extracted from a SKILL.md file.

    Attributes:
        given: The precondition / context.
        when: The action / trigger.
        then: The expected outcome / assertion.
        raw: The original text from which this scenario was parsed.
    """

    given: str
    when: str
    then: str
    raw: str


# ─── Parser ───


def parse_gherkin_scenarios(content: str) -> list[GherkinScenario]:
    """Parse Gherkin-like scenarios from markdown content.

    Scans for ``## Scenarios`` or ``## Acceptance Criteria`` sections
    and extracts Given/When/Then triplets.  Supports both block and
    bullet formats.

    Args:
        content: Full markdown content (or just the section body).

    Returns:
        A list of :class:`GherkinScenario` objects.  Empty if no
        scenarios are found.
    """
    # Extract the relevant section(s)
    section_body = _extract_scenario_section(content)
    if not section_body:
        # Try parsing the raw content directly (caller may pass section body)
        section_body = content

    scenarios: list[GherkinScenario] = []

    # Strategy 1: Find Given/When/Then blocks using regex
    # Handles both block and bullet formats
    pattern = re.compile(
        r"(?:^|\n)\s*-?\s*Given\s+(.+?)"
        r"\s+When\s+(.+?)"
        r"\s+Then\s+(.+?)(?=\n\s*(?:-\s*Given|\n\s*Given|$)|\Z)",
        re.DOTALL | re.IGNORECASE,
    )

    for match in pattern.finditer(section_body):
        given_text = _clean_text(match.group(1))
        when_text = _clean_text(match.group(2))
        then_text = _clean_text(match.group(3))
        raw_text = match.group(0).strip()

        if given_text and when_text and then_text:
            scenarios.append(
                GherkinScenario(
                    given=given_text,
                    when=when_text,
                    then=then_text,
                    raw=raw_text,
                )
            )

    if scenarios:
        logger.debug("Parsed %d Gherkin scenarios", len(scenarios))
    else:
        logger.debug("No Gherkin scenarios found in content")

    return scenarios


def _extract_scenario_section(content: str) -> str:
    """Extract the body of ## Scenarios or ## Acceptance Criteria sections.

    Looks for H2 headings matching either name and returns the content
    between that heading and the next H2 (or end of file).

    Args:
        content: Full markdown content.

    Returns:
        Section body text, or empty string if not found.
    """
    pattern = re.compile(
        r"^##\s+(?:Scenarios|Acceptance\s+Criteria)\s*$",
        re.MULTILINE | re.IGNORECASE,
    )
    match = pattern.search(content)
    if not match:
        return ""

    start = match.end()
    # Find next H2 or end of content
    next_h2 = re.search(r"^##\s+", content[start:], re.MULTILINE)
    if next_h2:
        end = start + next_h2.start()
    else:
        end = len(content)

    return content[start:end]


def _clean_text(text: str) -> str:
    """Clean extracted text by collapsing whitespace and stripping.

    Args:
        text: Raw extracted text.

    Returns:
        Cleaned text string.
    """
    # Collapse newlines and multiple spaces into single spaces
    cleaned = re.sub(r"\s+", " ", text.strip())
    return cleaned


# ─── Probe ───


class GherkinProbe:
    """Probe that generates scenarios from Gherkin-style acceptance criteria.

    Reads the ``scenarios`` or ``acceptance criteria`` section from a
    :class:`ParsedSkill` and converts each Given/When/Then triplet into
    a :class:`Scenario` for the evaluation pipeline.

    This is a **zero-LLM** probe — all scenarios are deterministically
    derived from the SKILL.md content.

    Example
    -------
    >>> probe = GherkinProbe()
    >>> probe.name
    'gherkin'
    """

    @property
    def name(self) -> str:
        """Short probe identifier."""
        return "gherkin"

    def generate_scenarios(
        self,
        skill: ParsedSkill,
        context: EvalContext,
    ) -> list[Scenario]:
        """Generate test scenarios from Gherkin acceptance criteria.

        Looks in the skill's ``sections`` dict for keys matching
        ``"scenarios"`` or ``"acceptance criteria"``, parses Gherkin
        triplets, and converts each to a pipeline :class:`Scenario`.

        If no Gherkin scenarios are found, falls back to parsing the
        full ``raw_content`` of the skill.

        Args:
            skill: Structured representation of the SKILL.md file.
            context: Pipeline context (unused — this probe makes no
                LLM calls).

        Returns:
            A list of :class:`Scenario` objects.  Empty if no Gherkin
            scenarios are found.
        """
        # Try sections first
        section_content = ""
        for key in ("scenarios", "acceptance criteria"):
            if key in skill.sections:
                section_content = skill.sections[key]
                break

        # Parse Gherkin scenarios
        if section_content:
            gherkin_scenarios = parse_gherkin_scenarios(section_content)
        else:
            # Fall back to full content
            gherkin_scenarios = parse_gherkin_scenarios(skill.raw_content)

        # Convert to pipeline Scenarios
        pipeline_scenarios: list[Scenario] = []
        for i, gs in enumerate(gherkin_scenarios):
            pipeline_scenarios.append(
                Scenario(
                    probe_name=self.name,
                    prompt=f"Given {gs.given}, when {gs.when}",
                    expected_behavior=gs.then,
                    dimension="",  # Gherkin scenarios span multiple dimensions
                    metadata={
                        "source": "gherkin",
                        "type": "acceptance_criteria",
                        "scenario_index": i,
                        "given": gs.given,
                        "when": gs.when,
                        "then": gs.then,
                    },
                )
            )

        logger.debug(
            "GherkinProbe generated %d scenarios from skill '%s'",
            len(pipeline_scenarios),
            skill.title or "untitled",
        )

        return pipeline_scenarios
