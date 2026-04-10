"""Tests for md_evals.pipeline.skill_parser — structured SKILL.md extraction.

Covers complete parsing, missing sections, YAML frontmatter, title,
rules, examples, triggers, empty content, and file-not-found handling.
"""

from __future__ import annotations

import pytest

from md_evals.pipeline.skill_parser import SkillExample, SkillParser


# ── Fixtures ──


COMPLETE_SKILL_MD = """\
---
name: test-skill
version: "1.0"
---

# Test Skill

## Description

A skill for testing the parser with all sections present.

## Rules

- Always greet the user
- Use bullet points for lists
- Keep responses under 200 words

## Examples

### Example 1

**Input:** Hello there
**Expected:** A friendly greeting response

### Example 2

**Input:** How do I sort a list?
**Output:** A code example showing list sorting

## Triggers

Trigger: greeting, hello, welcome
"""

MINIMAL_SKILL_MD = """\
# Minimal Skill

Just a title and some text, no structured sections.
"""

SKILL_WITH_MISSING_SECTIONS = """\
# Incomplete Skill

## Description

This skill has a description but no rules, examples, or triggers.
"""


# ============================================================================
# 1. Complete SKILL.md Parsing
# ============================================================================


def test_parse_complete_skill_title():
    """Parser extracts H1 title from complete SKILL.md."""
    skill = SkillParser.parse_content(COMPLETE_SKILL_MD)
    assert skill.title == "Test Skill"


def test_parse_complete_skill_description():
    """Parser extracts description section."""
    skill = SkillParser.parse_content(COMPLETE_SKILL_MD)
    assert "testing the parser" in skill.description


def test_parse_complete_skill_rules():
    """Parser extracts bullet points from Rules section."""
    skill = SkillParser.parse_content(COMPLETE_SKILL_MD)
    assert len(skill.rules) == 3
    assert "Always greet the user" in skill.rules
    assert "Use bullet points for lists" in skill.rules
    assert "Keep responses under 200 words" in skill.rules


def test_parse_complete_skill_examples():
    """Parser extracts examples with H3 subsections."""
    skill = SkillParser.parse_content(COMPLETE_SKILL_MD)
    assert len(skill.examples) == 2
    assert skill.examples[0].title == "Example 1"
    assert skill.examples[1].title == "Example 2"


def test_parse_complete_skill_example_input_expected():
    """Parser extracts Input/Expected from example body."""
    skill = SkillParser.parse_content(COMPLETE_SKILL_MD)
    ex1 = skill.examples[0]
    assert ex1.input_text == "Hello there"
    assert "friendly greeting" in ex1.expected_output


def test_parse_complete_skill_example_output_alias():
    """Parser recognises **Output:** as alias for **Expected:**."""
    skill = SkillParser.parse_content(COMPLETE_SKILL_MD)
    ex2 = skill.examples[1]
    assert "code example" in ex2.expected_output


def test_parse_complete_skill_triggers():
    """Parser extracts trigger keywords from Trigger: line."""
    skill = SkillParser.parse_content(COMPLETE_SKILL_MD)
    assert "greeting" in skill.triggers
    assert "hello" in skill.triggers
    assert "welcome" in skill.triggers


def test_parse_complete_skill_sections_dict():
    """Parser populates sections dict keyed by lowercased H2 headings."""
    skill = SkillParser.parse_content(COMPLETE_SKILL_MD)
    assert "description" in skill.sections
    assert "rules" in skill.sections
    assert "examples" in skill.sections
    assert "triggers" in skill.sections


def test_parse_complete_skill_raw_content():
    """Parser preserves raw_content as-is."""
    skill = SkillParser.parse_content(COMPLETE_SKILL_MD)
    assert skill.raw_content == COMPLETE_SKILL_MD


# ============================================================================
# 2. YAML Frontmatter
# ============================================================================


def test_parse_yaml_frontmatter():
    """Parser extracts YAML frontmatter metadata."""
    skill = SkillParser.parse_content(COMPLETE_SKILL_MD)
    assert skill.metadata.get("name") == "test-skill"
    assert skill.metadata.get("version") == "1.0"


def test_parse_no_frontmatter():
    """Parser returns empty metadata when no frontmatter present."""
    skill = SkillParser.parse_content(MINIMAL_SKILL_MD)
    assert skill.metadata == {}


# ============================================================================
# 3. Missing Sections — Graceful Degradation
# ============================================================================


def test_parse_missing_rules_returns_empty():
    """Missing ## Rules section results in empty rules list."""
    skill = SkillParser.parse_content(SKILL_WITH_MISSING_SECTIONS)
    assert skill.rules == []


def test_parse_missing_examples_returns_empty():
    """Missing ## Examples section results in empty examples list."""
    skill = SkillParser.parse_content(SKILL_WITH_MISSING_SECTIONS)
    assert skill.examples == []


def test_parse_missing_triggers_returns_empty():
    """Missing Trigger: line results in empty triggers list."""
    skill = SkillParser.parse_content(SKILL_WITH_MISSING_SECTIONS)
    assert skill.triggers == []


# ============================================================================
# 4. Empty and Edge Cases
# ============================================================================


def test_parse_empty_content():
    """Empty string returns a ParsedSkill with all defaults."""
    skill = SkillParser.parse_content("")
    assert skill.title == ""
    assert skill.description == ""
    assert skill.rules == []
    assert skill.examples == []
    assert skill.triggers == []
    assert skill.metadata == {}


def test_parse_whitespace_only():
    """Whitespace-only content is treated as empty."""
    skill = SkillParser.parse_content("   \n\n  \t  ")
    assert skill.title == ""
    assert skill.rules == []


def test_parse_file_not_found(tmp_path):
    """SkillParser.parse raises FileNotFoundError for missing path."""
    missing = str(tmp_path / "nonexistent.md")
    with pytest.raises(FileNotFoundError, match="Skill file not found"):
        SkillParser.parse(missing)


def test_parse_file_from_disk(tmp_path):
    """SkillParser.parse reads and parses a real file."""
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("# Disk Skill\n\n## Description\n\nHello from disk.\n")
    skill = SkillParser.parse(str(skill_file))
    assert skill.title == "Disk Skill"
    assert "Hello from disk" in skill.description


# ============================================================================
# 5. SkillExample Dataclass
# ============================================================================


def test_skill_example_frozen():
    """SkillExample is frozen."""
    ex = SkillExample(title="Test", input_text="in", expected_output="out")
    with pytest.raises(AttributeError):
        ex.title = "changed"  # type: ignore[misc]


def test_skill_example_defaults():
    """SkillExample fields default to empty strings."""
    ex = SkillExample()
    assert ex.title == ""
    assert ex.input_text == ""
    assert ex.expected_output == ""
