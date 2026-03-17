"""Citation validation for LLM judge responses.

Provides a citation system that requires the LLM judge to cite specific
lines from the SKILL.md file when scoring responses.  Citations are
validated against the actual content to catch hallucinated references.

Phase 3 — Trust & Verification (Feature #5):

* :class:`Citation` — frozen dataclass representing a single line citation.
* :class:`CitationValidator` — validates citations against actual SKILL.md content.
* :func:`citation_penalty` — computes a score penalty based on unverified citations.

Design notes
------------
* Citations use 1-based line numbers (matching text editor conventions).
* Text matching is fuzzy: a citation verifies if the cited text is
  *contained* in the actual line (case-insensitive, stripped).
* The penalty function returns a value in ``[0.0, 0.2]`` — enough to
  meaningfully penalize hallucinated citations without overwhelming the
  actual score signal.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, replace

logger = logging.getLogger(__name__)


# ─── Data Classes ───


@dataclass(frozen=True)
class Citation:
    """A citation referencing a specific line in SKILL.md.

    Frozen value object produced by parsing the LLM judge's response
    and validated against the actual file content.

    Attributes:
        line: 1-based line number in the SKILL.md file.
        text: Quoted text from the cited line.
        supports: Which dimension this citation supports (e.g. "correctness").
        verified: Whether the citation was validated against actual content.
    """

    line: int
    text: str
    supports: str
    verified: bool = False


# ─── Validator ───


class CitationValidator:
    """Validates citations against actual SKILL.md content.

    Checks that each citation's line number exists in the file and that
    the cited text appears on (or near) that line.  Uses fuzzy matching:
    a citation verifies if its text (stripped, lowercased) is contained
    in the actual line content (stripped, lowercased).

    Example
    -------
    >>> validator = CitationValidator()
    >>> content = "Line 1\\nAlways use strict mode\\nLine 3"
    >>> citations = [Citation(line=2, text="use strict mode", supports="correctness")]
    >>> validated = validator.validate(citations, content)
    >>> validated[0].verified
    True
    """

    def validate(
        self,
        citations: list[Citation],
        skill_content: str,
    ) -> list[Citation]:
        """Validate citations against actual SKILL.md content.

        For each citation, checks:
        1. The line number is within the file's line count.
        2. The cited text is contained in the actual line (fuzzy match).

        Args:
            citations: List of citations to validate.
            skill_content: The raw SKILL.md content to validate against.

        Returns:
            A new list of :class:`Citation` objects with ``verified``
            set to ``True`` for valid citations.
        """
        if not citations:
            return []

        lines = skill_content.splitlines()
        total_lines = len(lines)
        validated: list[Citation] = []

        for citation in citations:
            is_valid = self._verify_single(citation, lines, total_lines)
            validated.append(replace(citation, verified=is_valid))

        verified_count = sum(1 for c in validated if c.verified)
        logger.debug(
            "Citation validation: %d/%d verified",
            verified_count,
            len(validated),
        )

        return validated

    def _verify_single(
        self,
        citation: Citation,
        lines: list[str],
        total_lines: int,
    ) -> bool:
        """Verify a single citation against file content.

        Uses fuzzy matching: the cited text (stripped, lowercased)
        must be contained in the actual line (stripped, lowercased).

        Args:
            citation: The citation to verify.
            lines: Split lines of the SKILL.md content.
            total_lines: Total number of lines in the file.

        Returns:
            ``True`` if the citation is valid.
        """
        # Check line number is within bounds (1-based)
        if citation.line < 1 or citation.line > total_lines:
            logger.debug(
                "Citation line %d out of range (1-%d)",
                citation.line,
                total_lines,
            )
            return False

        # Get actual line content (convert to 0-based index)
        actual_line = lines[citation.line - 1].strip().lower()
        cited_text = citation.text.strip().lower()

        if not cited_text:
            # Empty citation text is never valid
            return False

        # Fuzzy contains check
        return cited_text in actual_line


# ─── Penalty Calculation ───


def citation_penalty(citations: list[Citation]) -> float:
    """Compute a score penalty based on unverified citations.

    Returns a penalty in ``[0.0, 0.2]`` proportional to the fraction
    of unverified citations.  If all citations verify, the penalty is
    ``0.0``.  If none verify, the penalty is ``0.2``.

    The penalty is designed to be subtracted from the raw score to
    adjust for hallucinated evidence.

    Args:
        citations: List of validated citations (with ``verified`` set).

    Returns:
        A float in ``[0.0, 0.2]``.  Returns ``0.0`` for empty lists.
    """
    if not citations:
        return 0.0

    total = len(citations)
    unverified = sum(1 for c in citations if not c.verified)
    unverified_ratio = unverified / total

    # Scale to max penalty of 0.2
    max_penalty = 0.2
    return round(unverified_ratio * max_penalty, 4)
