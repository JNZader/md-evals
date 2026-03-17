"""Static HTML export for evaluation results.

Generates self-contained HTML reports with inline CSS and SVG radar
charts. No external JavaScript or CSS dependencies — the entire report
is a single HTML file that can be opened in any browser or attached to
CI artifacts.

Key class:

- :class:`HTMLExporter` — Renders :class:`~md_evals.scoring.EvalResult`
  or :class:`~md_evals.suites.SuiteResult` to standalone HTML.
"""

from __future__ import annotations

import html
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from md_evals.scoring import EvalResult, eval_result_to_dict

if TYPE_CHECKING:
    from md_evals.suites import SuiteResult


# ─── Constants ───

GRADE_COLORS: dict[str, str] = {
    "S": "#FFD700",
    "A": "#22C55E",
    "B": "#3B82F6",
    "C": "#EAB308",
    "D": "#F97316",
    "F": "#EF4444",
}

GRADE_LABELS: dict[str, str] = {
    "S": "Exceptional",
    "A": "Excellent",
    "B": "Good",
    "C": "Adequate",
    "D": "Poor",
    "F": "Failing",
}


# ─── SVG Radar Chart Generator ───


def _build_svg_radar(dimensions: list[dict[str, Any]], size: int = 400) -> str:
    """Build an SVG radar chart from dimension data.

    Args:
        dimensions: List of dicts with 'dimension', 'score', 'grade' keys.
        size: Width/height of the SVG in pixels.

    Returns:
        SVG markup string.
    """
    if not dimensions:
        return ""

    cx, cy = size / 2, size / 2
    radius = size * 0.38
    n = len(dimensions)
    angle_step = 2 * math.pi / n

    # Build grid rings
    grid_lines: list[str] = []
    for ring_pct in (0.2, 0.4, 0.6, 0.8, 1.0):
        r = radius * ring_pct
        points = []
        for i in range(n):
            angle = -math.pi / 2 + i * angle_step
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            points.append(f"{x:.1f},{y:.1f}")
        grid_lines.append(
            f'<polygon points="{" ".join(points)}" '
            f'fill="none" stroke="#374151" stroke-width="0.5"/>'
        )

    # Build axis lines
    axis_lines: list[str] = []
    for i in range(n):
        angle = -math.pi / 2 + i * angle_step
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        axis_lines.append(
            f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" '
            f'stroke="#374151" stroke-width="0.5"/>'
        )

    # Build data polygon
    data_points: list[str] = []
    for i, dim in enumerate(dimensions):
        score = max(0.0, min(1.0, dim.get("score", 0)))
        angle = -math.pi / 2 + i * angle_step
        r = radius * score
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        data_points.append(f"{x:.1f},{y:.1f}")

    data_polygon = (
        f'<polygon points="{" ".join(data_points)}" '
        f'fill="#8B5CF6" fill-opacity="0.3" stroke="#8B5CF6" stroke-width="2"/>'
    )

    # Build data point dots
    dots: list[str] = []
    for i, dim in enumerate(dimensions):
        score = max(0.0, min(1.0, dim.get("score", 0)))
        angle = -math.pi / 2 + i * angle_step
        r = radius * score
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        dots.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" '
            f'fill="#8B5CF6" stroke="white" stroke-width="1"/>'
        )

    # Build labels
    labels: list[str] = []
    for i, dim in enumerate(dimensions):
        angle = -math.pi / 2 + i * angle_step
        label_r = radius + 28
        x = cx + label_r * math.cos(angle)
        y = cy + label_r * math.sin(angle)
        name = dim.get("dimension", "").capitalize()
        grade = dim.get("grade", "")
        color = GRADE_COLORS.get(grade, "#9CA3AF")
        anchor = "middle"
        if abs(math.cos(angle)) > 0.3:
            anchor = "start" if math.cos(angle) > 0 else "end"
        labels.append(
            f'<text x="{x:.1f}" y="{y:.1f}" fill="#9CA3AF" '
            f'font-size="12" text-anchor="{anchor}" dominant-baseline="central">'
            f'{html.escape(name)} '
            f'<tspan fill="{color}" font-weight="bold">{html.escape(grade)}</tspan>'
            f'</text>'
        )

    svg = f"""\
<svg viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg"
     width="{size}" height="{size}" style="max-width:100%;height:auto;">
  {"".join(grid_lines)}
  {"".join(axis_lines)}
  {data_polygon}
  {"".join(dots)}
  {"".join(labels)}
</svg>"""
    return svg


# ─── CSS ───


_CSS = """\
:root {
  --bg-primary: #111827;
  --bg-secondary: #1F2937;
  --bg-card: #1F2937;
  --text-primary: #F9FAFB;
  --text-secondary: #9CA3AF;
  --text-muted: #6B7280;
  --border: #374151;
  --accent: #8B5CF6;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, monospace;
  background: var(--bg-primary);
  color: var(--text-primary);
  line-height: 1.6;
  padding: 2rem;
  max-width: 960px;
  margin: 0 auto;
}
h1 { font-size: 1.75rem; margin-bottom: 0.5rem; }
h2 { font-size: 1.25rem; margin: 1.5rem 0 0.75rem; color: var(--text-secondary); }
.meta { color: var(--text-muted); font-size: 0.85rem; margin-bottom: 1.5rem; }
.grade-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 4rem;
  height: 4rem;
  border-radius: 50%;
  font-size: 2rem;
  font-weight: bold;
  margin: 1rem 0;
}
.grade-label {
  font-size: 0.9rem;
  margin-left: 0.75rem;
}
.grade-row {
  display: flex;
  align-items: center;
  margin: 1rem 0;
}
.score-text {
  color: var(--text-secondary);
  font-size: 1.1rem;
  margin-left: 1rem;
}
.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1.25rem;
  margin-bottom: 1rem;
}
.radar-container {
  display: flex;
  justify-content: center;
  margin: 1.5rem 0;
}
table {
  width: 100%;
  border-collapse: collapse;
  margin: 0.75rem 0;
}
th, td {
  padding: 0.5rem 0.75rem;
  text-align: left;
  border-bottom: 1px solid var(--border);
}
th {
  color: var(--text-secondary);
  font-weight: 600;
  font-size: 0.85rem;
  text-transform: uppercase;
}
td { font-size: 0.9rem; }
.evidence-list { list-style: disc; padding-left: 1.5rem; margin-top: 0.25rem; }
.evidence-list li { color: var(--text-muted); font-size: 0.8rem; }
.pass { color: #22C55E; }
.fail { color: #EF4444; }
.suite-summary {
  display: flex;
  gap: 2rem;
  margin: 1rem 0;
}
.suite-stat {
  text-align: center;
}
.suite-stat .number {
  font-size: 2rem;
  font-weight: bold;
}
.suite-stat .label {
  font-size: 0.8rem;
  color: var(--text-muted);
}
.footer {
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border);
  color: var(--text-muted);
  font-size: 0.8rem;
  text-align: center;
}
"""


# ─── HTML Exporter ───


class HTMLExporter:
    """Generate self-contained HTML reports from EvalResult or SuiteResult.

    All CSS is inlined — no external dependencies. The radar chart is
    rendered as inline SVG (no JavaScript required).
    """

    def export(self, result: EvalResult, output_path: str) -> str:
        """Generate an HTML file from a single EvalResult.

        Args:
            result: The evaluation result to render.
            output_path: Filesystem path for the output HTML file.

        Returns:
            The output_path string (for chaining convenience).
        """
        html_content = self._render(result)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(html_content, encoding="utf-8")
        return output_path

    def export_suite(self, suite_result: SuiteResult, output_path: str) -> str:
        """Generate an HTML report for a full suite.

        Args:
            suite_result: The suite result to render.
            output_path: Filesystem path for the output HTML file.

        Returns:
            The output_path string.
        """
        html_content = self._render_suite(suite_result)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(html_content, encoding="utf-8")
        return output_path

    def export_from_json(self, json_path: str, output_path: str) -> str:
        """Load a JSON result file and export as HTML.

        Args:
            json_path: Path to a JSON file containing eval results.
            output_path: Filesystem path for the output HTML file.

        Returns:
            The output_path string.

        Raises:
            FileNotFoundError: If json_path doesn't exist.
            ValueError: If the JSON is not a valid eval result.
        """
        data = json.loads(Path(json_path).read_text(encoding="utf-8"))
        html_content = self._render_from_dict(data)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(html_content, encoding="utf-8")
        return output_path

    # ─── Internal rendering ───

    def _render(self, result: EvalResult) -> str:
        """Render a single EvalResult to self-contained HTML."""
        data = eval_result_to_dict(result)
        return self._render_from_dict(data)

    def _render_from_dict(self, data: dict[str, Any]) -> str:
        """Render from a serialized eval result dict."""
        skill_path = data.get("skill_path", "unknown")
        grade = data.get("overall_grade", "F")
        score = data.get("overall_score", 0.0)
        dimensions = data.get("dimensions", [])
        metadata = data.get("metadata", {})
        pre_check = data.get("pre_check")

        grade_color = GRADE_COLORS.get(grade, "#EF4444")
        grade_label = GRADE_LABELS.get(grade, "Unknown")

        # Build radar SVG
        radar_svg = _build_svg_radar(dimensions)

        # Build dimensions table
        dim_rows = ""
        for d in dimensions:
            d_grade = d.get("grade", "F")
            d_color = GRADE_COLORS.get(d_grade, "#EF4444")
            d_name = html.escape(d.get("dimension", "").capitalize())
            d_score = d.get("score", 0)
            d_weight = d.get("weight", 0)
            evidence = d.get("evidence", [])

            evidence_html = ""
            if evidence:
                items = "".join(
                    f"<li>{html.escape(str(e))}</li>" for e in evidence
                )
                evidence_html = f'<ul class="evidence-list">{items}</ul>'

            dim_rows += f"""\
<tr>
  <td>{d_name}</td>
  <td>{d_score:.2f}</td>
  <td style="color:{d_color};font-weight:bold">{html.escape(d_grade)}</td>
  <td>{d_weight:.0%}</td>
  <td>{evidence_html}</td>
</tr>
"""

        # Build pre-check section
        precheck_html = ""
        if pre_check:
            passed = pre_check.get("passed", False)
            findings = pre_check.get("findings", [])
            status_class = "pass" if passed else "fail"
            status_text = "PASSED" if passed else "FAILED"
            findings_html = ""
            for f in findings:
                sev = f.get("severity", "info")
                msg = html.escape(f.get("message", ""))
                sev_color = {"error": "#EF4444", "warning": "#EAB308", "info": "#3B82F6"}.get(sev, "#9CA3AF")
                findings_html += f'<li style="color:{sev_color}">[{sev.upper()}] {msg}</li>'

            precheck_html = f"""\
<div class="card">
  <h2>Pre-Check</h2>
  <p class="{status_class}">Status: {status_text}</p>
  {"<ul class='evidence-list'>" + findings_html + "</ul>" if findings_html else ""}
</div>
"""

        # Build metadata section
        model = html.escape(str(metadata.get("model", "unknown")))
        provider = html.escape(str(metadata.get("provider", "unknown")))
        total_ms = metadata.get("total_duration_ms", 0)
        timestamp = html.escape(str(metadata.get("timestamp", "")))

        meta_html = f"Model: {model} · Provider: {provider}"
        if total_ms:
            meta_html += f" · Duration: {total_ms}ms"
        if timestamp:
            meta_html += f" · {timestamp}"

        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>md-evals Report — {html.escape(skill_path)}</title>
  <style>{_CSS}</style>
</head>
<body>
  <h1>md-evals Report</h1>
  <p class="meta">{html.escape(skill_path)}</p>

  <div class="grade-row">
    <div class="grade-badge" style="background:{grade_color}20;color:{grade_color}">
      {html.escape(grade)}
    </div>
    <span class="grade-label" style="color:{grade_color}">{grade_label}</span>
    <span class="score-text">Score: {score:.2f}</span>
  </div>

  <div class="radar-container">{radar_svg}</div>

  <div class="card">
    <h2>Dimensions</h2>
    <table>
      <thead>
        <tr><th>Dimension</th><th>Score</th><th>Grade</th><th>Weight</th><th>Evidence</th></tr>
      </thead>
      <tbody>{dim_rows}</tbody>
    </table>
  </div>

  {precheck_html}

  <div class="card">
    <h2>Metadata</h2>
    <p class="meta">{meta_html}</p>
  </div>

  <div class="footer">
    Generated by md-evals · {now}
  </div>
</body>
</html>
"""

    def _render_suite(self, suite_result: SuiteResult) -> str:
        """Render a SuiteResult to self-contained HTML."""
        name = html.escape(suite_result.name or "Eval Suite")
        status_class = "pass" if suite_result.passed else "fail"
        status_text = "PASSED" if suite_result.passed else "FAILED"

        # Skill result cards
        skill_cards = ""
        for skill_path, eval_result, meets in suite_result.results:
            grade = eval_result.overall_grade
            grade_color = GRADE_COLORS.get(grade, "#EF4444")
            threshold_class = "pass" if meets else "fail"
            threshold_text = "PASS" if meets else "FAIL"
            skill_cards += f"""\
<div class="card">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <div>
      <strong>{html.escape(skill_path)}</strong>
      <span class="grade-label" style="color:{grade_color};margin-left:0.5rem">{html.escape(grade)}</span>
      <span class="score-text">{eval_result.overall_score:.2f}</span>
    </div>
    <span class="{threshold_class}" style="font-weight:bold">{threshold_text}</span>
  </div>
</div>
"""

        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>md-evals Suite Report — {name}</title>
  <style>{_CSS}</style>
</head>
<body>
  <h1>Suite Report: {name}</h1>
  <p class="{status_class}" style="font-size:1.1rem;font-weight:bold">
    Status: {status_text}
  </p>

  <div class="suite-summary">
    <div class="suite-stat">
      <div class="number">{suite_result.total_skills}</div>
      <div class="label">Total</div>
    </div>
    <div class="suite-stat">
      <div class="number pass">{suite_result.passed_skills}</div>
      <div class="label">Passed</div>
    </div>
    <div class="suite-stat">
      <div class="number fail">{suite_result.failed_skills}</div>
      <div class="label">Failed</div>
    </div>
  </div>

  <h2>Skill Results</h2>
  {skill_cards}

  <div class="footer">
    Generated by md-evals · {now}
  </div>
</body>
</html>
"""
