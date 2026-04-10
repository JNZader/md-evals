"""Synthetic eval generator — auto-generate evaluation datasets from
skill definitions. Reduces manual effort of writing eval cases.

Given a SKILL.md, generates:
  1. Positive cases (correct behavior following the skill)
  2. Negative cases (violations of Critical Rules)
  3. Edge cases (boundary conditions from Constraints)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class EvalCase:
    """A synthetic evaluation case."""
    name: str
    category: str  # "positive", "negative", "edge"
    input_prompt: str
    expected_behavior: str
    grading_criteria: str
    source_rule: str = ""  # which rule/constraint generated this case


@dataclass
class SyntheticEvalSuite:
    """A collection of auto-generated eval cases."""
    skill_name: str
    cases: list[EvalCase] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)

    @property
    def positive_cases(self) -> list[EvalCase]:
        return [c for c in self.cases if c.category == "positive"]

    @property
    def negative_cases(self) -> list[EvalCase]:
        return [c for c in self.cases if c.category == "negative"]

    @property
    def edge_cases(self) -> list[EvalCase]:
        return [c for c in self.cases if c.category == "edge"]


# ── Extractors ──

def _extract_section(content: str, heading: str) -> str:
    """Extract content under a ## heading."""
    pattern = re.compile(
        rf"^##\s+{re.escape(heading)}\s*\n(.*?)(?=^##\s|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(content)
    return match.group(1).strip() if match else ""


def _extract_numbered_items(section: str) -> list[str]:
    """Extract numbered list items from a section."""
    items = re.findall(r"^\d+\.\s+\*?\*?(.+?)\*?\*?\s*$", section, re.MULTILINE)
    return [item.strip().strip("*") for item in items]


def _extract_bullet_items(section: str) -> list[str]:
    """Extract bullet list items from a section."""
    items = re.findall(r"^[-*]\s+(.+)$", section, re.MULTILINE)
    return [item.strip() for item in items]


def _extract_skill_name(content: str) -> str:
    """Extract skill name from frontmatter."""
    match = re.search(r"^name:\s*(.+)$", content, re.MULTILINE)
    return match.group(1).strip() if match else "unknown"


# ── Generator ──

def generate_eval_suite(skill_content: str) -> SyntheticEvalSuite:
    """Generate a synthetic eval suite from SKILL.md content.

    Analyzes Critical Rules, Constraints, and Execution Steps to
    produce test cases that validate correct skill behavior.
    """
    skill_name = _extract_skill_name(skill_content)
    suite = SyntheticEvalSuite(skill_name=skill_name)

    # Extract sections (try multiple heading variants)
    critical_rules = (
        _extract_section(skill_content, "Critical Rules")
        or _extract_section(skill_content, "Rules")
    )
    constraints = _extract_section(skill_content, "Constraints")
    steps = _extract_section(skill_content, "Execution Steps")
    rationalizations = _extract_section(skill_content, "Rationalizations")

    # Generate from Critical Rules → negative cases
    rules = _extract_numbered_items(critical_rules) or _extract_bullet_items(critical_rules)
    for i, rule in enumerate(rules):
        suite.cases.append(EvalCase(
            name=f"rule-violation-{i + 1}",
            category="negative",
            input_prompt=f"Given a task where the agent should follow '{skill_name}' skill, produce output that violates: {rule}",
            expected_behavior=f"The agent MUST follow the rule: {rule}",
            grading_criteria=f"FAIL if the output violates: {rule}",
            source_rule=rule,
        ))

        # Also generate a positive case for each rule
        suite.cases.append(EvalCase(
            name=f"rule-compliance-{i + 1}",
            category="positive",
            input_prompt=f"Given a task where the agent follows '{skill_name}' skill correctly, demonstrate compliance with: {rule}",
            expected_behavior=f"The output correctly follows: {rule}",
            grading_criteria=f"PASS if the output demonstrates: {rule}",
            source_rule=rule,
        ))

    # Generate from Constraints → edge cases
    constraint_items = _extract_numbered_items(constraints) or _extract_bullet_items(constraints)
    for i, constraint in enumerate(constraint_items):
        suite.cases.append(EvalCase(
            name=f"constraint-edge-{i + 1}",
            category="edge",
            input_prompt=f"Test the boundary of constraint: {constraint}",
            expected_behavior=f"The agent handles the edge case for: {constraint}",
            grading_criteria=f"PASS if constraint is respected at the boundary: {constraint}",
            source_rule=constraint,
        ))

    # Generate from Rationalizations → negative cases (agent tries to skip)
    excuse_pattern = re.compile(r'\*\*Excuse\*\*:\s*["\']?(.+?)["\']?\s*$', re.MULTILINE)
    excuses = excuse_pattern.findall(rationalizations)
    for i, excuse in enumerate(excuses):
        suite.cases.append(EvalCase(
            name=f"rationalization-resist-{i + 1}",
            category="negative",
            input_prompt=f"The agent encounters a situation where it might rationalize: '{excuse}'. Test that it resists this excuse.",
            expected_behavior=f"The agent does NOT use the excuse: {excuse}",
            grading_criteria=f"FAIL if the agent uses this rationalization: {excuse}",
            source_rule=excuse,
        ))

    return suite


# ── Formatting ──

def format_eval_suite(suite: SyntheticEvalSuite) -> str:
    """Format as a markdown eval suite document."""
    lines: list[str] = []
    lines.append(f"# Synthetic Eval Suite: {suite.skill_name}\n")
    lines.append(
        f"**Cases**: {len(suite.cases)} "
        f"(+{len(suite.positive_cases)} / -{len(suite.negative_cases)} / ~{len(suite.edge_cases)})\n"
    )

    for category in ["positive", "negative", "edge"]:
        cases = [c for c in suite.cases if c.category == category]
        if not cases:
            continue
        label = {"positive": "Positive", "negative": "Negative", "edge": "Edge"}[category]
        lines.append(f"## {label} Cases ({len(cases)})\n")
        for case in cases:
            lines.append(f"### {case.name}")
            lines.append(f"**Input**: {case.input_prompt}")
            lines.append(f"**Expected**: {case.expected_behavior}")
            lines.append(f"**Grading**: {case.grading_criteria}")
            if case.source_rule:
                lines.append(f"*Source*: {case.source_rule}")
            lines.append("")

    return "\n".join(lines)


def suite_to_dict(suite: SyntheticEvalSuite) -> dict:
    return {
        "skill_name": suite.skill_name,
        "cases": [
            {
                "name": c.name,
                "category": c.category,
                "input_prompt": c.input_prompt,
                "expected_behavior": c.expected_behavior,
                "grading_criteria": c.grading_criteria,
                "source_rule": c.source_rule,
            }
            for c in suite.cases
        ],
    }
