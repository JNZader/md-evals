"""Skill parser — structured extraction from SKILL.md files.

Parses ``SKILL.md`` content into a :class:`ParsedSkill` dataclass that
provides structured access to the skill's title, description, rules,
examples, triggers, sections, and metadata.  The parsed representation
is used by probes (for targeted scenario generation) and the auditor
stage.

Design notes
------------
* **No external dependencies** (ADR-05): uses only Python stdlib
  (``re``, ``pathlib``).  No markdown-parsing libraries.
* **Graceful degradation** (REQ-SP07): if extraction fails for any
  section, the parser returns the raw text or an empty collection and
  logs a warning — it never raises an exception during parsing.
* **YAML frontmatter**: optionally parsed via ``yaml.safe_load`` if
  ``PyYAML`` is available.  Falls back silently if not installed.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ─── Data Classes ───


@dataclass(frozen=True)
class SkillExample:
    """A parsed example from a SKILL.md file.

    Extracted from ``## Examples`` subsections (H3 headings).  The
    ``input_text`` and ``expected_output`` fields are populated when the
    example body contains ``**Input:**`` / ``**Expected:**`` markers.

    Attributes:
        title: The H3 heading text (e.g. ``"Example 1"``).
        input_text: The input portion of the example, or empty string.
        expected_output: The expected output, or empty string.
    """

    title: str = ""
    input_text: str = ""
    expected_output: str = ""


@dataclass
class ParsedSkill:
    """Structured representation of a SKILL.md file.

    Mutable dataclass built incrementally by :class:`SkillParser`.
    After parsing, all fields are populated (possibly with empty defaults
    for sections not found in the source file).

    Attributes:
        raw_content: The complete, unmodified file content.
        title: First H1 heading text, or empty string.
        description: Content of the ``## Description`` section, or empty string.
        rules: Bullet points extracted from the ``## Rules`` section.
        examples: Structured examples extracted from ``## Examples``.
        triggers: Trigger keywords parsed from a ``Trigger:`` line.
        sections: Mapping of H2 heading (lowercased) → section body text.
        metadata: YAML frontmatter key-value pairs, if present.
    """

    raw_content: str = ""
    title: str = ""
    description: str = ""
    rules: list[str] = field(default_factory=list)
    examples: list[SkillExample] = field(default_factory=list)
    triggers: list[str] = field(default_factory=list)
    sections: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


# ─── Parser ───


class SkillParser:
    """Parse SKILL.md files into structured :class:`ParsedSkill` objects.

    The parser operates in two modes:

    * :meth:`parse` — reads a file from disk, then delegates to
      :meth:`parse_content`.
    * :meth:`parse_content` — parses a raw markdown string directly
      (useful for testing and in-memory content).

    Parsing strategy
    ----------------
    1. Extract optional YAML frontmatter (between ``---`` markers).
    2. Extract the first H1 heading as ``title``.
    3. Split the body by H2 headings into ``sections``.
    4. Extract ``description`` from the ``## Description`` section.
    5. Extract bullet points from ``## Rules`` into ``rules``.
    6. Extract ``## Examples`` subsections into ``examples``.
    7. Extract ``Trigger:`` line keywords into ``triggers``.
    """

    @classmethod
    def parse(cls, path: str) -> ParsedSkill:
        """Parse a SKILL.md file from disk.

        Args:
            path: Filesystem path to the SKILL.md file.

        Returns:
            A populated :class:`ParsedSkill` instance.

        Raises:
            FileNotFoundError: If *path* does not exist.
        """
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Skill file not found: {path}")

        content = file_path.read_text(encoding="utf-8")
        return cls.parse_content(content)

    @classmethod
    def parse_content(cls, content: str) -> ParsedSkill:
        """Parse SKILL.md content from a raw string.

        Never raises exceptions during parsing — malformed sections
        result in empty fields with a logged warning.

        Args:
            content: The raw markdown content to parse.

        Returns:
            A populated :class:`ParsedSkill` instance.
        """
        if not content.strip():
            return ParsedSkill(raw_content=content)

        skill = ParsedSkill(raw_content=content)

        # 1. Extract YAML frontmatter
        skill.metadata = cls._extract_frontmatter(content)

        # 2. Remove frontmatter for body parsing
        body = cls._strip_frontmatter(content)

        # 3. Extract title (first H1)
        skill.title = cls._extract_title(body)

        # 4. Split into sections by H2
        skill.sections = cls._extract_sections(body)

        # 5. Extract description
        skill.description = skill.sections.get("description", "").strip()

        # 6. Extract rules
        rules_text = skill.sections.get("rules", "")
        skill.rules = cls._extract_bullet_points(rules_text)

        # 7. Extract examples
        examples_text = skill.sections.get("examples", "")
        skill.examples = cls._extract_examples(examples_text)

        # 8. Extract triggers
        skill.triggers = cls._extract_triggers(content)

        return skill

    # ── Private extraction helpers ──

    @staticmethod
    def _extract_frontmatter(content: str) -> dict[str, Any]:
        """Extract YAML frontmatter between ``---`` markers.

        Returns an empty dict if no frontmatter is found or if
        ``PyYAML`` is not installed.

        Args:
            content: Full file content including potential frontmatter.

        Returns:
            Parsed frontmatter as a dict, or ``{}``.
        """
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if not match:
            return {}

        try:
            import yaml  # noqa: F811 — optional dependency

            parsed = yaml.safe_load(match.group(1))
            return parsed if isinstance(parsed, dict) else {}
        except ImportError:
            logger.debug("PyYAML not available — skipping frontmatter parsing")
            return {}
        except Exception:
            logger.warning("Failed to parse YAML frontmatter")
            return {}

    @staticmethod
    def _strip_frontmatter(content: str) -> str:
        """Remove YAML frontmatter from content.

        Args:
            content: Full file content.

        Returns:
            Content with frontmatter removed.
        """
        return re.sub(
            r"^---\s*\n.*?\n---\s*\n",
            "",
            content,
            count=1,
            flags=re.DOTALL,
        )

    @staticmethod
    def _extract_title(content: str) -> str:
        """Extract the first H1 heading.

        Args:
            content: Markdown content (frontmatter already stripped).

        Returns:
            The H1 heading text, or empty string if not found.
        """
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        return match.group(1).strip() if match else ""

    @staticmethod
    def _extract_sections(content: str) -> dict[str, str]:
        """Split content into sections by H2 headings.

        Each section's key is the heading text lowercased; the value is
        the body text between this heading and the next H2 (or end of
        file).

        Args:
            content: Markdown content (frontmatter already stripped).

        Returns:
            Mapping of lowercased heading → section body text.
        """
        sections: dict[str, str] = {}
        pattern = re.compile(r"^##\s+(.+)$", re.MULTILINE)
        matches = list(pattern.finditer(content))

        for i, match in enumerate(matches):
            name = match.group(1).strip().lower()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            sections[name] = content[start:end].strip()

        return sections

    @staticmethod
    def _extract_bullet_points(text: str) -> list[str]:
        """Extract bullet points from text.

        Recognises ``-``, ``*``, and ``•`` as bullet markers.

        Args:
            text: Section body text.

        Returns:
            List of bullet-point texts (markers stripped).
        """
        points: list[str] = []
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith(("- ", "* ", "• ")):
                points.append(stripped[2:].strip())
        return points

    @staticmethod
    def _extract_examples(text: str) -> list[SkillExample]:
        """Extract examples from H3 subsections within ``## Examples``.

        Each H3 heading becomes an example.  Within the body, the parser
        looks for ``**Input:**`` and ``**Expected:**`` (or ``**Output:**``)
        markers to populate structured fields.

        Args:
            text: Content of the ``## Examples`` section.

        Returns:
            List of :class:`SkillExample` objects.
        """
        examples: list[SkillExample] = []
        pattern = re.compile(r"^###\s+(.+)$", re.MULTILINE)
        matches = list(pattern.finditer(text))

        for i, match in enumerate(matches):
            title = match.group(1).strip()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[start:end].strip()

            # Try to extract input/output patterns
            input_text = ""
            expected = ""

            input_match = re.search(
                r"\*\*Input:?\*\*\s*(.+?)(?=\*\*|$)", body, re.DOTALL
            )
            if input_match:
                input_text = input_match.group(1).strip()

            expected_match = re.search(
                r"\*\*(?:Expected|Output):?\*\*\s*(.+?)(?=\*\*|$)",
                body,
                re.DOTALL,
            )
            if expected_match:
                expected = expected_match.group(1).strip()

            examples.append(
                SkillExample(
                    title=title,
                    input_text=input_text,
                    expected_output=expected,
                )
            )

        return examples

    @staticmethod
    def _extract_triggers(content: str) -> list[str]:
        """Extract trigger keywords from content.

        Looks for a ``Trigger:`` (or ``Triggers:``) line and splits the
        value by commas or semicolons.

        Args:
            content: Full file content (including frontmatter).

        Returns:
            List of trigger keyword strings, or ``[]``.
        """
        match = re.search(
            r"(?:^|\n)\s*(?:Triggers?)\s*:\s*(.+)$",
            content,
            re.MULTILINE | re.IGNORECASE,
        )
        if match:
            text = match.group(1).strip()
            return [t.strip() for t in re.split(r"[,;]", text) if t.strip()]
        return []
