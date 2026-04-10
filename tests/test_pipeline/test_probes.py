"""Tests for md_evals.pipeline.probes — scenario generators.

Uses mocks for LLM calls. Verifies DimensionProbe, EdgeCaseProbe, and
ComplianceProbe generate correct Scenario objects with proper lineage.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
import json


from md_evals.pipeline.config import AuditorConfig, PipelineConfig
from md_evals.pipeline.context import EvalContext
from md_evals.pipeline.probes import (
    ComplianceProbe,
    DimensionProbe,
    EdgeCaseProbe,
    _extract_json_array,
)
from md_evals.pipeline.skill_parser import ParsedSkill, SkillExample


# ── Helpers ──


def _make_context(adapter=None, pipeline_config=None):
    """Create an EvalContext with optional auditor adapter in metadata."""
    ctx = EvalContext(pipeline_config=pipeline_config)
    if adapter is not None:
        ctx.metadata["auditor_adapter"] = adapter
    return ctx


def _make_skill(**kwargs):
    """Create a ParsedSkill with sensible defaults."""
    defaults = {
        "raw_content": "# Test Skill\n\nContent here",
        "title": "Test Skill",
        "description": "A test skill",
        "rules": ["Rule 1", "Rule 2"],
        "examples": [SkillExample(title="Ex1", input_text="hello", expected_output="world")],
        "triggers": ["test"],
        "sections": {},
        "metadata": {},
    }
    defaults.update(kwargs)
    return ParsedSkill(**defaults)


def _make_mock_adapter(response_content: str):
    """Create a mock LLMAdapter that returns a fixed response."""
    adapter = MagicMock()
    mock_response = MagicMock()
    mock_response.content = response_content
    adapter.complete = AsyncMock(return_value=mock_response)
    return adapter


# ============================================================================
# 1. _extract_json_array Helper
# ============================================================================


def test_extract_json_array_direct_parse():
    """Direct JSON array parsing succeeds."""
    text = json.dumps([{"prompt": "test", "expected_behavior": "ok"}])
    result = _extract_json_array(text)
    assert len(result) == 1
    assert result[0]["prompt"] == "test"


def test_extract_json_array_with_surrounding_text():
    """Extracts JSON from surrounding markdown text."""
    text = 'Here is the result:\n[{"prompt": "hi"}]\nDone.'
    result = _extract_json_array(text)
    assert len(result) == 1


def test_extract_json_array_empty_on_garbage():
    """Returns empty list for non-JSON input."""
    result = _extract_json_array("not json at all")
    assert result == []


def test_extract_json_array_single_object():
    """Single JSON object (not array) is wrapped in a list."""
    text = '{"prompt": "solo"}'
    result = _extract_json_array(text)
    assert len(result) == 1
    assert result[0]["prompt"] == "solo"


# ============================================================================
# 2. DimensionProbe Tests
# ============================================================================


def test_dimension_probe_name():
    """DimensionProbe.name is always 'dimension'."""
    probe = DimensionProbe("correctness", "accuracy of content")
    assert probe.name == "dimension"


def test_dimension_probe_fallback_when_no_adapter():
    """DimensionProbe falls back to templates when no adapter in context."""
    probe = DimensionProbe("correctness", "accuracy of content")
    ctx = _make_context(adapter=None)
    skill = _make_skill()

    scenarios = probe.generate_scenarios(skill, ctx)

    assert len(scenarios) >= 1
    assert all(s.probe_name == "dimension" for s in scenarios)
    assert all(s.dimension == "correctness" for s in scenarios)
    assert all(s.metadata.get("source") in ("fallback", "fallback_example") for s in scenarios)


def test_dimension_probe_with_llm(monkeypatch):
    """DimensionProbe uses LLM when adapter is available."""
    llm_response = json.dumps([
        {"prompt": "Test correctness scenario", "expected_behavior": "Should be correct"},
    ])

    # Mock _run_llm_complete to avoid async issues
    monkeypatch.setattr(
        "md_evals.pipeline.probes._run_llm_complete",
        lambda adapter, prompt, **kwargs: llm_response,
    )

    adapter = MagicMock()
    probe = DimensionProbe("correctness", "accuracy of content")
    ctx = _make_context(adapter=adapter)
    skill = _make_skill()

    scenarios = probe.generate_scenarios(skill, ctx)

    assert len(scenarios) == 1
    assert scenarios[0].prompt == "Test correctness scenario"
    assert scenarios[0].dimension == "correctness"
    assert scenarios[0].metadata["source"] == "llm"


def test_dimension_probe_falls_back_on_llm_failure(monkeypatch):
    """DimensionProbe falls back when LLM returns None."""
    monkeypatch.setattr(
        "md_evals.pipeline.probes._run_llm_complete",
        lambda adapter, prompt, **kwargs: None,
    )

    adapter = MagicMock()
    probe = DimensionProbe("correctness", "accuracy")
    ctx = _make_context(adapter=adapter)
    skill = _make_skill()

    scenarios = probe.generate_scenarios(skill, ctx)

    assert len(scenarios) >= 1
    assert all(s.metadata.get("source") in ("fallback", "fallback_example") for s in scenarios)


def test_dimension_probe_respects_scenarios_per_probe(monkeypatch):
    """DimensionProbe requests correct number of scenarios from LLM."""
    captured_prompts = []

    def mock_complete(adapter, prompt, **kwargs):
        captured_prompts.append(prompt)
        return json.dumps([{"prompt": "s1", "expected_behavior": "e1"}])

    monkeypatch.setattr("md_evals.pipeline.probes._run_llm_complete", mock_complete)

    config = PipelineConfig(auditor=AuditorConfig(scenarios_per_probe=7))
    adapter = MagicMock()
    ctx = _make_context(adapter=adapter, pipeline_config=config)
    probe = DimensionProbe("format", "structure")
    skill = _make_skill()

    probe.generate_scenarios(skill, ctx)

    assert "7" in captured_prompts[0]  # The prompt should mention N=7


# ============================================================================
# 3. EdgeCaseProbe Tests
# ============================================================================


def test_edge_case_probe_name():
    """EdgeCaseProbe.name is always 'edge-case'."""
    probe = EdgeCaseProbe()
    assert probe.name == "edge-case"


def test_edge_case_probe_fallback_when_no_adapter():
    """EdgeCaseProbe generates deterministic fallback scenarios without adapter."""
    probe = EdgeCaseProbe()
    ctx = _make_context(adapter=None)
    skill = _make_skill()

    scenarios = probe.generate_scenarios(skill, ctx)

    assert len(scenarios) >= 2  # empty_input + minimal_input at minimum
    assert all(s.probe_name == "edge-case" for s in scenarios)
    assert all(s.dimension == "" for s in scenarios)


def test_edge_case_probe_fallback_includes_adversarial():
    """EdgeCaseProbe adds adversarial scenario when skill has rules."""
    probe = EdgeCaseProbe()
    ctx = _make_context(adapter=None)
    skill = _make_skill(rules=["Must be polite"])

    scenarios = probe.generate_scenarios(skill, ctx)

    types = [s.metadata.get("type") for s in scenarios]
    assert "adversarial" in types


def test_edge_case_probe_with_llm(monkeypatch):
    """EdgeCaseProbe uses LLM when adapter is available."""
    llm_response = json.dumps([
        {"prompt": "Empty input edge case", "expected_behavior": "Handle gracefully"},
    ])
    monkeypatch.setattr(
        "md_evals.pipeline.probes._run_llm_complete",
        lambda adapter, prompt, **kwargs: llm_response,
    )

    adapter = MagicMock()
    probe = EdgeCaseProbe()
    ctx = _make_context(adapter=adapter)
    skill = _make_skill()

    scenarios = probe.generate_scenarios(skill, ctx)

    assert len(scenarios) == 1
    assert scenarios[0].metadata["source"] == "llm"
    assert scenarios[0].metadata["type"] == "edge_case"


# ============================================================================
# 4. ComplianceProbe Tests
# ============================================================================


def test_compliance_probe_name():
    """ComplianceProbe.name is always 'compliance'."""
    probe = ComplianceProbe()
    assert probe.name == "compliance"


def test_compliance_probe_empty_rules():
    """ComplianceProbe returns empty list when skill has no rules."""
    probe = ComplianceProbe()
    ctx = _make_context(adapter=None)
    skill = _make_skill(rules=[])

    scenarios = probe.generate_scenarios(skill, ctx)

    assert scenarios == []


def test_compliance_probe_fallback():
    """ComplianceProbe generates one scenario per rule in fallback mode."""
    probe = ComplianceProbe()
    ctx = _make_context(adapter=None)
    skill = _make_skill(rules=["Be concise", "Use examples", "Cite sources"])

    scenarios = probe.generate_scenarios(skill, ctx)

    assert len(scenarios) == 3
    assert all(s.probe_name == "compliance" for s in scenarios)
    assert all(s.dimension == "adherence" for s in scenarios)
    for i, s in enumerate(scenarios):
        assert s.metadata["rule_index"] == i
        assert s.metadata["rule_text"] == skill.rules[i]


def test_compliance_probe_with_llm(monkeypatch):
    """ComplianceProbe uses LLM to generate compliance scenarios."""
    llm_response = json.dumps([
        {"prompt": "Test rule 1", "expected_behavior": "Complies with rule", "rule_index": 0},
    ])
    monkeypatch.setattr(
        "md_evals.pipeline.probes._run_llm_complete",
        lambda adapter, prompt, **kwargs: llm_response,
    )

    adapter = MagicMock()
    probe = ComplianceProbe()
    ctx = _make_context(adapter=adapter)
    skill = _make_skill(rules=["Be concise"])

    scenarios = probe.generate_scenarios(skill, ctx)

    assert len(scenarios) == 1
    assert scenarios[0].metadata["source"] == "llm"
    assert scenarios[0].metadata["type"] == "compliance"
    assert scenarios[0].metadata["rule_text"] == "Be concise"
