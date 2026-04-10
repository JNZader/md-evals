"""Tests for md_evals.pipeline.gherkin — Gherkin scenario parsing and probe.

Verifies GherkinScenario, parse_gherkin_scenarios, and GherkinProbe with
comprehensive format coverage.
"""

from __future__ import annotations

import pytest

from md_evals.pipeline.context import EvalContext
from md_evals.pipeline.gherkin import GherkinScenario, GherkinProbe, parse_gherkin_scenarios
from md_evals.pipeline.skill_parser import ParsedSkill


# ── Helpers ──


def _make_skill(**kwargs):
    """Create a ParsedSkill with sensible defaults."""
    defaults = {
        "raw_content": "# Test\nContent",
        "title": "Test",
        "description": "A test",
        "rules": [],
        "examples": [],
        "triggers": [],
        "sections": {},
        "metadata": {},
    }
    defaults.update(kwargs)
    return ParsedSkill(**defaults)


def _make_context():
    """Create a minimal EvalContext."""
    return EvalContext()


# ============================================================================
# 1. GherkinScenario Dataclass Tests
# ============================================================================


class TestGherkinScenario:
    """Tests for the GherkinScenario frozen dataclass."""

    def test_create_scenario(self):
        """GherkinScenario can be created with required fields."""
        s = GherkinScenario(given="a React component", when="skill is applied", then="no useMemo", raw="raw")
        assert s.given == "a React component"
        assert s.when == "skill is applied"
        assert s.then == "no useMemo"
        assert s.raw == "raw"

    def test_scenario_is_frozen(self):
        """GherkinScenario is immutable."""
        s = GherkinScenario(given="a", when="b", then="c", raw="d")
        with pytest.raises(AttributeError):
            s.given = "x"  # type: ignore[misc]

    def test_scenario_equality(self):
        """Two scenarios with same values are equal."""
        s1 = GherkinScenario(given="a", when="b", then="c", raw="d")
        s2 = GherkinScenario(given="a", when="b", then="c", raw="d")
        assert s1 == s2


# ============================================================================
# 2. parse_gherkin_scenarios Tests
# ============================================================================


class TestParseGherkinScenarios:
    """Tests for the parse_gherkin_scenarios function."""

    def test_parse_bullet_format(self):
        """Parses bullet-format Given/When/Then."""
        content = """\
## Scenarios
- Given a React component with useState
  When the skill is applied
  Then the output should not contain useMemo

- Given an empty input
  When processed
  Then return a helpful error message
"""
        scenarios = parse_gherkin_scenarios(content)
        assert len(scenarios) == 2
        assert "React component" in scenarios[0].given
        assert "skill is applied" in scenarios[0].when
        assert "useMemo" in scenarios[0].then

    def test_parse_block_format(self):
        """Parses block-format (no bullets) Given/When/Then."""
        content = """\
## Scenarios

Given a Python function
When the skill is applied
Then the output should use type hints
"""
        scenarios = parse_gherkin_scenarios(content)
        assert len(scenarios) == 1
        assert "Python function" in scenarios[0].given
        assert "type hints" in scenarios[0].then

    def test_parse_acceptance_criteria_heading(self):
        """Recognizes ## Acceptance Criteria heading."""
        content = """\
## Acceptance Criteria
- Given a user request
  When processed
  Then respond in JSON format
"""
        scenarios = parse_gherkin_scenarios(content)
        assert len(scenarios) == 1
        assert "JSON format" in scenarios[0].then

    def test_parse_empty_content(self):
        """Empty content returns empty list."""
        assert parse_gherkin_scenarios("") == []

    def test_parse_no_scenarios_section(self):
        """Content without scenarios section returns empty list."""
        content = """\
# Skill Title

## Rules
- Rule 1
- Rule 2
"""
        scenarios = parse_gherkin_scenarios(content)
        assert scenarios == []

    def test_parse_case_insensitive_keywords(self):
        """Given/When/Then keywords are case-insensitive."""
        content = """\
## Scenarios
- given a component
  when rendered
  then display correctly
"""
        scenarios = parse_gherkin_scenarios(content)
        assert len(scenarios) == 1

    def test_parse_multiline_then(self):
        """Then clause can span to end of block."""
        content = """\
## Scenarios
- Given a complex input
  When the skill processes it
  Then the output should be valid and well-formatted
"""
        scenarios = parse_gherkin_scenarios(content)
        assert len(scenarios) == 1
        assert "valid" in scenarios[0].then

    def test_parse_multiple_scenarios(self):
        """Multiple scenarios are all parsed."""
        content = """\
## Scenarios
- Given scenario one
  When action one
  Then result one

- Given scenario two
  When action two
  Then result two

- Given scenario three
  When action three
  Then result three
"""
        scenarios = parse_gherkin_scenarios(content)
        assert len(scenarios) == 3

    def test_parse_section_body_directly(self):
        """Can parse section body without ## heading."""
        content = """\
- Given a direct input
  When processed directly
  Then return direct output
"""
        scenarios = parse_gherkin_scenarios(content)
        assert len(scenarios) == 1

    def test_parse_scenarios_section_stops_at_next_h2(self):
        """Parsing stops at the next ## heading."""
        content = """\
## Scenarios
- Given a test
  When applied
  Then succeed

## Rules
- This should not be parsed as a scenario
  Given fake context
  When fake action
  Then fake result
"""
        scenarios = parse_gherkin_scenarios(content)
        assert len(scenarios) == 1

    def test_parsed_scenario_has_raw(self):
        """Each parsed scenario includes the raw text."""
        content = """\
## Scenarios
- Given a test case
  When evaluated
  Then pass
"""
        scenarios = parse_gherkin_scenarios(content)
        assert len(scenarios) == 1
        assert "Given" in scenarios[0].raw


# ============================================================================
# 3. GherkinProbe Tests
# ============================================================================


class TestGherkinProbe:
    """Tests for the GherkinProbe pipeline probe."""

    def setup_method(self):
        self.probe = GherkinProbe()

    def test_probe_name(self):
        """GherkinProbe has name 'gherkin'."""
        assert self.probe.name == "gherkin"

    def test_probe_satisfies_protocol(self):
        """GherkinProbe satisfies the Probe protocol."""
        from md_evals.pipeline.protocols import Probe
        assert isinstance(self.probe, Probe)

    def test_generate_scenarios_from_sections(self):
        """Probe generates scenarios from skill sections."""
        skill = _make_skill(
            sections={
                "scenarios": (
                    "- Given a React component\n"
                    "  When the skill is applied\n"
                    "  Then use hooks correctly"
                ),
            },
            raw_content="# Skill\n## Scenarios\n- Given a React component\n  When the skill is applied\n  Then use hooks correctly",
        )
        context = _make_context()
        scenarios = self.probe.generate_scenarios(skill, context)
        assert len(scenarios) == 1
        assert scenarios[0].probe_name == "gherkin"
        assert "React component" in scenarios[0].prompt

    def test_generate_scenarios_from_acceptance_criteria(self):
        """Probe recognizes 'acceptance criteria' section key."""
        skill = _make_skill(
            sections={
                "acceptance criteria": (
                    "- Given a user input\n"
                    "  When validated\n"
                    "  Then return success"
                ),
            },
        )
        context = _make_context()
        scenarios = self.probe.generate_scenarios(skill, context)
        assert len(scenarios) == 1

    def test_generate_scenarios_fallback_to_raw(self):
        """Probe falls back to raw_content if no section found."""
        raw = (
            "# Skill\n\n## Scenarios\n"
            "- Given raw content\n"
            "  When parsed\n"
            "  Then succeed"
        )
        skill = _make_skill(sections={}, raw_content=raw)
        context = _make_context()
        scenarios = self.probe.generate_scenarios(skill, context)
        assert len(scenarios) == 1

    def test_generate_empty_when_no_gherkin(self):
        """Probe returns empty list when no Gherkin content found."""
        skill = _make_skill(sections={}, raw_content="# Simple\nNo gherkin here")
        context = _make_context()
        scenarios = self.probe.generate_scenarios(skill, context)
        assert scenarios == []

    def test_scenario_metadata(self):
        """Generated scenarios include gherkin metadata."""
        skill = _make_skill(
            sections={
                "scenarios": (
                    "- Given context\n"
                    "  When action\n"
                    "  Then result"
                ),
            },
        )
        context = _make_context()
        scenarios = self.probe.generate_scenarios(skill, context)
        assert scenarios[0].metadata["source"] == "gherkin"
        assert scenarios[0].metadata["type"] == "acceptance_criteria"
        assert "given" in scenarios[0].metadata
        assert "when" in scenarios[0].metadata
        assert "then" in scenarios[0].metadata

    def test_scenario_dimension_is_empty(self):
        """Gherkin scenarios have empty dimension (span multiple)."""
        skill = _make_skill(
            sections={
                "scenarios": (
                    "- Given test\n"
                    "  When applied\n"
                    "  Then succeed"
                ),
            },
        )
        context = _make_context()
        scenarios = self.probe.generate_scenarios(skill, context)
        assert scenarios[0].dimension == ""

    def test_scenario_prompt_format(self):
        """Scenario prompt combines Given and When clauses."""
        skill = _make_skill(
            sections={
                "scenarios": (
                    "- Given a form input\n"
                    "  When submitted\n"
                    "  Then validate"
                ),
            },
        )
        context = _make_context()
        scenarios = self.probe.generate_scenarios(skill, context)
        prompt = scenarios[0].prompt
        assert "Given" in prompt
        assert "form input" in prompt
        assert "when" in prompt.lower()
