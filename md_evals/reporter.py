"""Reporter for formatting evaluation results."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from md_evals.metrics import build_usage_metrics
from md_evals.models import EvalConfig, ExecutionResult
from md_evals.scoring import EvalResult, eval_result_to_dict


class Reporter:
    """Formats and outputs evaluation results."""
    
    def __init__(self, config: EvalConfig):
        self.config = config
        self.console = Console()
        self._eval_result: EvalResult | None = None

    def set_eval_result(self, eval_result: EvalResult) -> None:
        """Set scoring result for inclusion in output.

        When set, the eval_result is serialized into the JSON output
        and a grade summary is printed in terminal reports.

        Args:
            eval_result: Scoring engine result for the evaluation.
        """
        self._eval_result = eval_result
    
    def report_terminal(
        self,
        results: list[ExecutionResult],
        verbose: bool = False
    ) -> None:
        """Print results to terminal.
        
        Args:
            results: List of execution results
            verbose: Show detailed output
        """
        if not results:
            self.console.print("[yellow]No results to display[/yellow]")
            return
        
        # Group by treatment
        by_treatment: dict[str, list[ExecutionResult]] = {}
        for result in results:
            if result.treatment not in by_treatment:
                by_treatment[result.treatment] = []
            by_treatment[result.treatment].append(result)
        
        # Build summary table
        table = Table(
            title="md-evals Results",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta"
        )
        table.add_column("Treatment", style="cyan")
        table.add_column("Tests", justify="center")
        table.add_column("Passed", justify="center")
        table.add_column("Pass Rate", justify="center")
        table.add_column("Avg Duration", justify="center")
        
        for treatment, treatment_results in by_treatment.items():
            total = len(treatment_results)
            passed = sum(1 for r in treatment_results if r.passed)
            pass_rate = (passed / total * 100) if total > 0 else 0
            
            # Calculate average duration
            durations = [
                r.response.duration_ms
                for r in treatment_results
                if r.response
            ]
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            # Color based on pass rate
            if pass_rate >= 80:
                pass_style = "green"
            elif pass_rate >= 50:
                pass_style = "yellow"
            else:
                pass_style = "red"
            
            table.add_row(
                treatment,
                f"{passed}/{total}",
                f"[{pass_style}]{passed}[/{pass_style}]",
                f"[{pass_style}]{pass_rate:.0f}%[/{pass_style}]",
                f"{avg_duration:.0f}ms"
            )
        
        self.console.print()
        self.console.print(table)
        self.console.print()
        
        # Show improvements if CONTROL exists
        if "CONTROL" in by_treatment:
            control_passed = sum(1 for r in by_treatment["CONTROL"] if r.passed)
            control_total = len(by_treatment["CONTROL"])
            control_rate = (control_passed / control_total * 100) if control_total > 0 else 0
            
            for treatment, treatment_results in by_treatment.items():
                if treatment == "CONTROL":
                    continue
                
                treatment_passed = sum(1 for r in treatment_results if r.passed)
                treatment_total = len(treatment_results)
                treatment_rate = (treatment_passed / treatment_total * 100) if treatment_total > 0 else 0
                
                improvement = treatment_rate - control_rate
                
                if improvement > 0:
                    self.console.print(
                        f"[green]▲[/green] {treatment}: +{improvement:.0f}% vs CONTROL"
                    )
                elif improvement < 0:
                    self.console.print(
                        f"[red]▼[/red] {treatment}: {improvement:.0f}% vs CONTROL"
                    )
        
        # ─── T-28: Grade summary from scoring engine ───
        if self._eval_result is not None:
            self._print_grade_summary(self._eval_result)

        # ─── T-15: Conditional usage metrics tables ───
        if self.config.output.include_usage_metrics:
            usage = build_usage_metrics(results, self.config)
            if usage:
                self._print_cost_metrics_table(usage)
                self._print_context_metrics_table(usage)
                self._print_comparison_table(usage)

        # Verbose output
        if verbose:
            self._print_verbose(results)
    
    def _print_grade_summary(self, eval_result: EvalResult) -> None:
        """Print grade summary with colored grades.

        Renders the overall grade prominently followed by a table of
        per-dimension scores, grades, and weights.

        Args:
            eval_result: Scoring engine result to display.
        """
        grade_colors = {
            "S": "yellow",
            "A": "green",
            "B": "blue",
            "C": "yellow",
            "D": "bright_red",
            "F": "red",
        }
        color = grade_colors.get(eval_result.overall_grade, "white")
        self.console.print(
            f"\n[bold]Overall Grade: [{color}]{eval_result.overall_grade}"
            f"[/{color}] ({eval_result.overall_score:.2f})[/bold]"
        )

        # Per-dimension table
        table = Table(title="Dimension Scores", box=box.ROUNDED)
        table.add_column("Dimension", style="cyan")
        table.add_column("Score", style="white")
        table.add_column("Grade", style="bold")
        table.add_column("Weight", style="dim")

        for d in eval_result.dimensions:
            d_color = grade_colors.get(d.grade, "white")
            table.add_row(
                d.dimension.capitalize(),
                f"{d.score:.2f}",
                f"[{d_color}]{d.grade}[/{d_color}]",
                f"{d.weight:.0%}",
            )

        self.console.print(table)
        self.console.print()

    def _print_cost_metrics_table(self, usage: dict[str, Any]) -> None:
        """Render Cost Metrics table per treatment.

        Columns: Treatment | Avg Prompt Tokens | Avg Completion Tokens |
                 Avg Total Tokens | Est. Cost USD

        Args:
            usage: The usage_metrics dict from build_usage_metrics().
        """
        variants = usage.get("variants", {})
        if not variants:
            return

        table = Table(
            title="Cost Metrics",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Treatment", style="cyan")
        table.add_column("Prompt Tokens", justify="right")
        table.add_column("Completion Tokens", justify="right")
        table.add_column("Total Tokens", justify="right")
        table.add_column("Latency (ms)", justify="right")
        table.add_column("Est. Cost USD", justify="right")

        for name, variant_data in variants.items():
            cost = variant_data.get("cost_metrics", {})
            prompt = cost.get("prompt_tokens", 0)
            completion = cost.get("completion_tokens", 0)
            total = cost.get("total_tokens", 0)
            latency = cost.get("latency_ms", 0)
            cost_usd = cost.get("estimated_cost_usd")

            cost_str = f"${cost_usd:.4f}" if cost_usd is not None else "N/A"

            table.add_row(
                name,
                f"{prompt:,}",
                f"{completion:,}",
                f"{total:,}",
                f"{latency:,}",
                cost_str,
            )

        self.console.print()
        self.console.print(table)

    def _print_context_metrics_table(self, usage: dict[str, Any]) -> None:
        """Render Context Metrics table per treatment.

        Columns: Treatment | Prompt Used | Context Window | Utilization % |
                 Headroom | Truncation Risk

        Args:
            usage: The usage_metrics dict from build_usage_metrics().
        """
        variants = usage.get("variants", {})
        if not variants:
            return

        table = Table(
            title="Context Metrics",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Treatment", style="cyan")
        table.add_column("Prompt Used", justify="right")
        table.add_column("Context Window", justify="right")
        table.add_column("Util %", justify="right")
        table.add_column("Headroom", justify="right")
        table.add_column("Risk", justify="center")

        for name, variant_data in variants.items():
            ctx = variant_data.get("context_metrics", {})
            prompt_used = ctx.get("prompt_tokens_used", 0)
            window = ctx.get("context_window_max_tokens")
            util_pct = ctx.get("context_utilization_pct")
            headroom = ctx.get("headroom_tokens")
            risk = ctx.get("truncation_risk", "unknown")

            window_str = f"{window:,}" if window is not None else "N/A"
            util_str = f"{util_pct:.1f}%" if util_pct is not None else "N/A"
            headroom_str = f"{headroom:,}" if headroom is not None else "N/A"

            # Color risk
            risk_colors = {"low": "green", "medium": "yellow", "high": "red", "unknown": "dim"}
            risk_color = risk_colors.get(risk, "dim")
            risk_str = f"[{risk_color}]{risk}[/{risk_color}]"

            table.add_row(
                name,
                f"{prompt_used:,}",
                window_str,
                util_str,
                headroom_str,
                risk_str,
            )

        self.console.print()
        self.console.print(table)

    def _print_comparison_table(self, usage: dict[str, Any]) -> None:
        """Render Comparison table between treatments.

        Shows deltas for key metrics between the first two treatments.

        Args:
            usage: The usage_metrics dict from build_usage_metrics().
        """
        comparison = usage.get("comparison")
        if not comparison:
            return

        variants = usage.get("variants", {})
        names = list(variants.keys())
        if len(names) < 2:
            return

        name_a, name_b = names[0], names[1]

        table = Table(
            title=f"Comparison ({name_a} vs {name_b})",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Metric", style="cyan")
        table.add_column(name_b, justify="right")
        table.add_column(name_a, justify="right")
        table.add_column("Delta", justify="right")
        table.add_column("Delta %", justify="right")

        # Select key metrics to show
        key_metrics = [
            ("cost_metrics", "total_tokens", "Total Tokens"),
            ("cost_metrics", "estimated_cost_usd", "Cost USD"),
            ("cost_metrics", "latency_ms", "Latency (ms)"),
            ("context_metrics", "context_utilization_pct", "Utilization %"),
            ("context_metrics", "headroom_tokens", "Headroom"),
        ]

        for domain, field_name, label in key_metrics:
            domain_data = comparison.get(domain, {})
            metric_data = domain_data.get(field_name, {})

            val_a = metric_data.get(name_a)
            val_b = metric_data.get(name_b)
            delta_abs = metric_data.get("delta_abs")
            delta_pct = metric_data.get("delta_pct")
            reason = metric_data.get("delta_pct_reason")

            # Format values
            def _fmt_val(v: Any, is_cost: bool = False, is_pct: bool = False) -> str:
                if v is None:
                    return "N/A"
                if is_cost:
                    return f"${v:.4f}"
                if is_pct:
                    return f"{v:.1f}%"
                if isinstance(v, float):
                    return f"{v:.2f}"
                return f"{v:,}"

            is_cost = field_name == "estimated_cost_usd"
            is_pct = field_name == "context_utilization_pct"

            val_b_str = _fmt_val(val_b, is_cost=is_cost, is_pct=is_pct)
            val_a_str = _fmt_val(val_a, is_cost=is_cost, is_pct=is_pct)

            # Format delta with color
            if delta_abs is not None:
                sign = "+" if delta_abs > 0 else ""
                if is_cost:
                    delta_str = f"{sign}${delta_abs:.4f}"
                elif is_pct:
                    delta_str = f"{sign}{delta_abs:.1f}%"
                elif isinstance(delta_abs, float):
                    delta_str = f"{sign}{delta_abs:.2f}"
                else:
                    delta_str = f"{sign}{delta_abs:,}"

                # Color: green for improvements (negative cost/tokens), red for degradation
                if delta_abs > 0:
                    delta_str = f"[red]{delta_str}[/red]"
                elif delta_abs < 0:
                    delta_str = f"[green]{delta_str}[/green]"
            else:
                delta_str = reason or "N/A"

            if delta_pct is not None:
                sign = "+" if delta_pct > 0 else ""
                pct_str = f"{sign}{delta_pct:.2f}%"
                if delta_pct > 0:
                    pct_str = f"[red]{pct_str}[/red]"
                elif delta_pct < 0:
                    pct_str = f"[green]{pct_str}[/green]"
            else:
                pct_str = reason or "N/A"

            table.add_row(label, val_b_str, val_a_str, delta_str, pct_str)

        self.console.print()
        self.console.print(table)

    def _print_verbose(self, results: list[ExecutionResult]) -> None:
        """Print verbose results."""
        for result in results:
            panel = Panel(
                f"[bold]Test:[/bold] {result.test}\n"
                f"[bold]Treatment:[/bold] {result.treatment}\n"
                f"[bold]Passed:[/bold] {result.passed}\n"
                f"[bold]Duration:[/bold] {result.response.duration_ms if result.response else 'N/A'}ms",
                title=f"Result: {result.treatment}/{result.test}",
                border_style="blue" if result.passed else "red"
            )
            self.console.print(panel)
    
    def report_json(
        self,
        results: list[ExecutionResult],
        output_path: str
    ) -> None:
        """Save results as JSON.
        
        Args:
            results: List of execution results
            output_path: Path to save JSON
        """
        output_data = self._build_output_data(results)
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, default=str)
    
    def report_markdown(
        self,
        results: list[ExecutionResult],
        output_path: str
    ) -> None:
        """Save results as Markdown.
        
        Args:
            results: List of execution results
            output_path: Path to save Markdown
        """
        md_content = self._build_markdown(results)
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md_content)
    
    def _build_output_data(
        self,
        results: list[ExecutionResult]
    ) -> dict[str, Any]:
        """Build output data structure."""
        # Group by treatment
        by_treatment: dict[str, list[ExecutionResult]] = {}
        for result in results:
            if result.treatment not in by_treatment:
                by_treatment[result.treatment] = []
            by_treatment[result.treatment].append(result)
        
        # Build summary
        summary = {}
        for treatment, treatment_results in by_treatment.items():
            total = len(treatment_results)
            passed = sum(1 for r in treatment_results if r.passed)
            
            summary[treatment] = {
                "total": total,
                "passed": passed,
                "pass_rate": passed / total if total > 0 else 0
            }
        
        output: dict[str, Any] = {
            "experiment_id": f"eval_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "config": {
                "name": self.config.name,
                "version": self.config.version
            },
            "results": [
                {
                    "treatment": r.treatment,
                    "test": r.test,
                    "prompt": r.prompt,
                    "response": r.response.content if r.response else None,
                    "passed": r.passed,
                    "evaluators": [
                        {
                            "name": e.evaluator_name,
                            "passed": e.passed,
                            "score": e.score,
                            "reason": e.reason
                        }
                        for e in r.evaluator_results
                    ],
                    "tokens": r.response.tokens if r.response else None,
                    "duration_ms": r.response.duration_ms if r.response else None,
                    "timestamp": r.timestamp
                }
                for r in results
            ],
            "summary": summary
        }

        # ─── T-14: Conditional inclusion of usage_metrics ───
        usage_metrics = build_usage_metrics(results, self.config)
        if usage_metrics is not None:
            output["report_schema_version"] = "2.0"
            output["feature_flags"] = {"include_usage_metrics": True}
            output["usage_metrics"] = usage_metrics

        # ─── T-27: Conditional inclusion of scoring eval_result ───
        if self._eval_result is not None:
            output["eval_result"] = eval_result_to_dict(self._eval_result)

        return output
    
    def _build_markdown(self, results: list[ExecutionResult]) -> str:
        """Build Markdown report."""
        md_lines = [
            "# md-evals Results",
            "",
            f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
            f"**Config:** {self.config.name} (v{self.config.version})",
            "",
            "## Summary",
            "",
            "| Treatment | Tests | Passed | Pass Rate |",
            "|-----------|-------|--------|-----------|"
        ]
        
        # Group by treatment
        by_treatment: dict[str, list[ExecutionResult]] = {}
        for result in results:
            if result.treatment not in by_treatment:
                by_treatment[result.treatment] = []
            by_treatment[result.treatment].append(result)
        
        for treatment, treatment_results in by_treatment.items():
            total = len(treatment_results)
            passed = sum(1 for r in treatment_results if r.passed)
            rate = passed / total * 100 if total > 0 else 0
            
            md_lines.append(f"| {treatment} | {total} | {passed} | {rate:.0f}% |")
        
        md_lines.extend(["", "## Details", ""])
        
        for treatment, treatment_results in by_treatment.items():
            md_lines.append(f"### {treatment}")
            md_lines.append("")
            
            for result in treatment_results:
                status = "✅" if result.passed else "❌"
                md_lines.append(f"- **{result.test}**: {status}")
                
                if result.evaluator_results:
                    md_lines.append("  - Evaluators:")
                    for eval_result in result.evaluator_results:
                        eval_status = "✅" if eval_result.passed else "❌"
                        md_lines.append(
                            f"    - {eval_result.evaluator_name}: {eval_status}"
                        )
            
            md_lines.append("")
        
        return "\n".join(md_lines)
    
    def calculate_summary(
        self,
        results: list[ExecutionResult]
    ) -> dict[str, Any]:
        """Calculate aggregate statistics.
        
        Args:
            results: List of execution results
            
        Returns:
            Summary statistics
        """
        if not results:
            return {}
        
        # Group by treatment
        by_treatment: dict[str, list[ExecutionResult]] = {}
        for result in results:
            if result.treatment not in by_treatment:
                by_treatment[result.treatment] = []
            by_treatment[result.treatment].append(result)
        
        summary = {}
        for treatment, treatment_results in by_treatment.items():
            passed = sum(1 for r in treatment_results if r.passed)
            total = len(treatment_results)
            
            # Duration stats
            durations = [r.response.duration_ms for r in treatment_results if r.response]
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            # Token stats
            tokens = [r.response.tokens for r in treatment_results if r.response]
            total_tokens = sum(tokens)
            
            summary[treatment] = {
                "passed": passed,
                "total": total,
                "pass_rate": passed / total if total > 0 else 0,
                "avg_duration_ms": avg_duration,
                "total_tokens": total_tokens
            }
        
        return summary
