"""Mission reporter — generates markdown reports from mission results."""

from __future__ import annotations

from pathlib import Path

from md_evals.mission.models import MissionResult
from md_evals.mission.tracker import RegressionReport


class MissionReporter:
    """Generates markdown reports for mission runs.

    Produces a structured report with:
    - Mission metadata (name, model, skill, timestamp)
    - Summary table (total, passed, failed, pass rate)
    - Per-test results with criteria details
    - Regression comparison (if previous run exists)
    """

    @staticmethod
    def generate(
        result: MissionResult,
        regression: RegressionReport | None = None,
    ) -> str:
        """Generate a markdown report from mission results.

        Args:
            result: Current mission run result.
            regression: Optional regression comparison report.

        Returns:
            Markdown string.
        """
        lines: list[str] = []

        # Header
        lines.append(f"# Mission Report: {result.mission_name}")
        lines.append("")
        lines.append(f"**Version:** {result.version}")
        lines.append(f"**Timestamp:** {result.timestamp}")
        lines.append(f"**Model:** {result.model}")
        lines.append(f"**Provider:** {result.provider}")
        if result.skill_under_test:
            lines.append(f"**Skill:** {result.skill_under_test}")
        if result.tags:
            lines.append(f"**Tags:** {', '.join(result.tags)}")
        lines.append("")

        # Summary
        s = result.summary
        lines.append("## Summary")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Total Tests | {s.total} |")
        lines.append(f"| Passed | {s.passed} |")
        lines.append(f"| Failed | {s.failed} |")
        lines.append(f"| Pass Rate | {s.pass_rate:.0%} |")
        lines.append(f"| Duration | {s.duration_ms}ms |")
        lines.append("")

        # Test Results
        lines.append("## Test Results")
        lines.append("")
        lines.append("| Test | Status | Score | Duration |")
        lines.append("|------|--------|-------|----------|")
        for tr in result.test_results:
            status = "PASS" if tr.passed else "FAIL"
            icon = "+" if tr.passed else "-"
            lines.append(
                f"| {tr.test_name} | {icon} {status} | {tr.score:.2f} | {tr.duration_ms}ms |"
            )
        lines.append("")

        # Criteria details for failed tests
        failed = [tr for tr in result.test_results if not tr.passed]
        if failed:
            lines.append("## Failed Test Details")
            lines.append("")
            for tr in failed:
                lines.append(f"### {tr.test_name}")
                lines.append("")
                if tr.error:
                    lines.append(f"**Error:** {tr.error}")
                    lines.append("")
                for cr in tr.criteria_results:
                    cr_status = "PASS" if cr.get("passed") else "FAIL"
                    cr_icon = "+" if cr.get("passed") else "-"
                    reason = cr.get("reason", "")
                    reason_text = f" -- {reason}" if reason else ""
                    lines.append(
                        f"- {cr_icon} **{cr.get('name', 'unnamed')}** ({cr.get('type', '?')}): "
                        f"{cr_status}{reason_text}"
                    )
                lines.append("")

        # Regression section
        if regression is not None:
            lines.extend(MissionReporter._render_regression(regression))

        return "\n".join(lines)

    @staticmethod
    def _render_regression(report: RegressionReport) -> list[str]:
        """Render the regression comparison section."""
        lines: list[str] = []
        lines.append("## Regression Analysis")
        lines.append("")

        if report.previous_timestamp:
            lines.append(f"**Compared against:** {report.previous_timestamp}")
        else:
            lines.append("**First run** -- no previous results to compare.")
            lines.append("")
            return lines

        lines.append("")
        lines.append("| Metric | Count |")
        lines.append("|--------|-------|")
        lines.append(f"| Regressions | {report.regressions} |")
        lines.append(f"| Improvements | {report.improvements} |")
        lines.append(f"| Stable | {report.stable} |")
        lines.append(f"| New Tests | {report.new_tests} |")
        lines.append("")

        if report.has_regressions:
            lines.append("### Regressions")
            lines.append("")
            lines.append("| Test | Previous | Current | Score Delta |")
            lines.append("|------|----------|---------|-------------|")
            for item in report.items:
                if item.status == "regression":
                    prev = "PASS" if item.previous_passed else "FAIL"
                    curr = "PASS" if item.current_passed else "FAIL"
                    lines.append(
                        f"| {item.test_name} | {prev} | {curr} | {item.score_delta:+.2f} |"
                    )
            lines.append("")

        improvements = [i for i in report.items if i.status == "improvement"]
        if improvements:
            lines.append("### Improvements")
            lines.append("")
            lines.append("| Test | Previous | Current | Score Delta |")
            lines.append("|------|----------|---------|-------------|")
            for item in improvements:
                prev = "PASS" if item.previous_passed else "FAIL"
                curr = "PASS" if item.current_passed else "FAIL"
                lines.append(
                    f"| {item.test_name} | {prev} | {curr} | {item.score_delta:+.2f} |"
                )
            lines.append("")

        return lines

    @staticmethod
    def save(content: str, output_path: str | Path) -> Path:
        """Save the markdown report to a file.

        Args:
            content: Markdown content.
            output_path: Destination file path.

        Returns:
            Path to the saved file.
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path
