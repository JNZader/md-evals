"""Comprehensive tests for md_evals.export module.

Tests cover:
  - HTMLExporter._render (single result HTML generation)
  - HTMLExporter.export (file writing)
  - HTMLExporter.export_suite (suite HTML generation)
  - HTMLExporter.export_from_json (JSON → HTML conversion)
  - _build_svg_radar (SVG radar chart generation)
  - GRADE_COLORS and GRADE_LABELS constants
  - Edge cases: empty dimensions, missing metadata, pre-check findings
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from md_evals.export import (
    GRADE_COLORS,
    GRADE_LABELS,
    HTMLExporter,
    _build_svg_radar,
)
from md_evals.scoring import DimensionScore, EvalMetadata, EvalResult
from md_evals.suites import SuiteResult


# ─── Fixtures ───


def _make_eval_result(
    grade: str = "B",
    score: float = 0.78,
    skill_path: str = "test.md",
    with_precheck: bool = False,
) -> EvalResult:
    """Create a minimal EvalResult for testing."""
    from md_evals.precheck import PreCheckResult, PreCheckFinding

    pre_check = None
    if with_precheck:
        pre_check = PreCheckResult(
            passed=True,
            findings=[
                PreCheckFinding(
                    check="required_sections",
                    message="Missing 'Examples' section",
                    severity="warning",
                    line=None,
                ),
            ],
            checks_run=5,
            duration_ms=12,
        )

    return EvalResult(
        skill_path=skill_path,
        overall_grade=grade,
        overall_score=score,
        dimensions=[
            DimensionScore("correctness", 0.9, 0.25, "A"),
            DimensionScore("completeness", 0.7, 0.20, "B"),
            DimensionScore("format", 0.6, 0.15, "C"),
            DimensionScore("adherence", 0.85, 0.20, "A"),
            DimensionScore("safety", 0.95, 0.20, "S"),
        ],
        pre_check=pre_check,
        metadata=EvalMetadata(
            model="gpt-4o",
            provider="github-models",
            total_duration_ms=1234,
            timestamp="2025-01-15T10:30:00Z",
        ),
    )


# ============================================================================
# Constants
# ============================================================================


class TestConstants:
    def test_grade_colors_all_grades(self):
        for grade in ("S", "A", "B", "C", "D", "F"):
            assert grade in GRADE_COLORS
            assert GRADE_COLORS[grade].startswith("#")

    def test_grade_labels_all_grades(self):
        for grade in ("S", "A", "B", "C", "D", "F"):
            assert grade in GRADE_LABELS
            assert isinstance(GRADE_LABELS[grade], str)


# ============================================================================
# SVG Radar Chart
# ============================================================================


class TestSVGRadar:
    def test_empty_dimensions(self):
        assert _build_svg_radar([]) == ""

    def test_single_dimension(self):
        svg = _build_svg_radar([{"dimension": "correctness", "score": 0.9, "grade": "A"}])
        assert "<svg" in svg
        assert "Correctness" in svg

    def test_multiple_dimensions(self):
        dims = [
            {"dimension": "correctness", "score": 0.9, "grade": "A"},
            {"dimension": "completeness", "score": 0.7, "grade": "B"},
            {"dimension": "format", "score": 0.6, "grade": "C"},
        ]
        svg = _build_svg_radar(dims)
        assert "<svg" in svg
        assert "polygon" in svg
        assert "Correctness" in svg
        assert "Completeness" in svg

    def test_score_clamping(self):
        dims = [
            {"dimension": "test", "score": 1.5, "grade": "S"},
            {"dimension": "test2", "score": -0.3, "grade": "F"},
        ]
        svg = _build_svg_radar(dims)
        assert "<svg" in svg


# ============================================================================
# HTMLExporter._render
# ============================================================================


class TestHTMLRender:
    def test_basic_render(self):
        result = _make_eval_result()
        exporter = HTMLExporter()
        html = exporter._render(result)

        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "md-evals Report" in html
        assert "test.md" in html
        assert "B" in html  # grade
        assert "0.78" in html  # score

    def test_render_contains_dimensions(self):
        result = _make_eval_result()
        exporter = HTMLExporter()
        html = exporter._render(result)

        assert "Correctness" in html
        assert "Completeness" in html
        assert "Format" in html

    def test_render_contains_metadata(self):
        result = _make_eval_result()
        exporter = HTMLExporter()
        html = exporter._render(result)

        assert "gpt-4o" in html
        assert "github-models" in html

    def test_render_with_precheck(self):
        result = _make_eval_result(with_precheck=True)
        exporter = HTMLExporter()
        html = exporter._render(result)

        assert "Pre-Check" in html
        assert "PASSED" in html

    def test_render_contains_radar_svg(self):
        result = _make_eval_result()
        exporter = HTMLExporter()
        html = exporter._render(result)

        assert "<svg" in html
        assert "polygon" in html

    def test_render_self_contained(self):
        """HTML should not reference external resources."""
        result = _make_eval_result()
        exporter = HTMLExporter()
        html = exporter._render(result)

        # No external CSS/JS links
        assert 'href="http' not in html
        assert 'src="http' not in html
        assert "<style>" in html

    def test_render_empty_dimensions(self):
        result = EvalResult(
            skill_path="empty.md",
            overall_grade="F",
            overall_score=0.0,
            dimensions=[],
            pre_check=None,
            metadata=EvalMetadata(model="test", provider="test"),
        )
        exporter = HTMLExporter()
        html = exporter._render(result)
        assert "<!DOCTYPE html>" in html
        assert "F" in html


# ============================================================================
# HTMLExporter.export (file writing)
# ============================================================================


class TestHTMLExport:
    def test_export_creates_file(self, tmp_path: Path):
        result = _make_eval_result()
        exporter = HTMLExporter()
        output = tmp_path / "report.html"
        returned = exporter.export(result, str(output))

        assert output.exists()
        assert returned == str(output)
        content = output.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content

    def test_export_creates_parent_dirs(self, tmp_path: Path):
        result = _make_eval_result()
        exporter = HTMLExporter()
        output = tmp_path / "sub" / "dir" / "report.html"
        exporter.export(result, str(output))

        assert output.exists()


# ============================================================================
# HTMLExporter.export_suite
# ============================================================================


class TestHTMLExportSuite:
    def test_export_suite(self, tmp_path: Path):
        er1 = _make_eval_result("A", 0.92, "skill1.md")
        er2 = _make_eval_result("C", 0.55, "skill2.md")

        suite_result = SuiteResult(
            name="backend-skills",
            passed=False,
            results=[
                ("skill1.md", er1, True),
                ("skill2.md", er2, False),
            ],
            total_skills=2,
            passed_skills=1,
            failed_skills=1,
        )

        exporter = HTMLExporter()
        output = tmp_path / "suite_report.html"
        exporter.export_suite(suite_result, str(output))

        content = output.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content
        assert "backend-skills" in content
        assert "FAILED" in content
        assert "skill1.md" in content
        assert "skill2.md" in content


# ============================================================================
# HTMLExporter.export_from_json
# ============================================================================


class TestHTMLExportFromJSON:
    def test_export_from_json(self, tmp_path: Path):
        data = {
            "skill_path": "test.md",
            "overall_grade": "B",
            "overall_score": 0.78,
            "dimensions": [
                {"dimension": "correctness", "score": 0.9, "weight": 0.5, "grade": "A"},
                {"dimension": "completeness", "score": 0.7, "weight": 0.5, "grade": "B"},
            ],
            "metadata": {"model": "gpt-4o", "provider": "test"},
            "pre_check": None,
        }
        json_file = tmp_path / "result.json"
        json_file.write_text(json.dumps(data))

        exporter = HTMLExporter()
        output = tmp_path / "from_json.html"
        exporter.export_from_json(str(json_file), str(output))

        content = output.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content
        assert "B" in content
        assert "test.md" in content
