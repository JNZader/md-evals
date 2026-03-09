"""Reporter for formatting evaluation results."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from md_evals.models import EvalConfig, ExecutionResult


class Reporter:
    """Formats and outputs evaluation results."""
    
    def __init__(self, config: EvalConfig):
        self.config = config
        self.console = Console()
    
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
        
        # Verbose output
        if verbose:
            self._print_verbose(results)
    
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
        
        return {
            "experiment_id": f"eval_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.utcnow().isoformat(),
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
    
    def _build_markdown(self, results: list[ExecutionResult]) -> str:
        """Build Markdown report."""
        md_lines = [
            "# md-evals Results",
            "",
            f"**Generated:** {datetime.utcnow().isoformat()}",
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
