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
from typing import Annotated
from typing import Callable
from typing import ClassVar

MutantDict = Annotated[dict[str, Callable], "Mutant"] # type: ignore


def _mutmut_trampoline(orig, mutants, call_args, call_kwargs, self_arg = None): # type: ignore
    """Forward call to original or mutated function, depending on the environment"""
    import os # type: ignore
    mutant_under_test = os.environ['MUTANT_UNDER_TEST'] # type: ignore
    if mutant_under_test == 'fail': # type: ignore
        from mutmut.__main__ import MutmutProgrammaticFailException # type: ignore
        raise MutmutProgrammaticFailException('Failed programmatically')       # type: ignore
    elif mutant_under_test == 'stats': # type: ignore
        from mutmut.__main__ import record_trampoline_hit # type: ignore
        record_trampoline_hit(orig.__module__ + '.' + orig.__name__) # type: ignore
        # (for class methods, orig is bound and thus does not need the explicit self argument)
        result = orig(*call_args, **call_kwargs) # type: ignore
        return result # type: ignore
    prefix = orig.__module__ + '.' + orig.__name__ + '__mutmut_' # type: ignore
    if not mutant_under_test.startswith(prefix): # type: ignore
        result = orig(*call_args, **call_kwargs) # type: ignore
        return result # type: ignore
    mutant_name = mutant_under_test.rpartition('.')[-1] # type: ignore
    if self_arg is not None: # type: ignore
        # call to a class method where self is not bound
        result = mutants[mutant_name](self_arg, *call_args, **call_kwargs) # type: ignore
    else:
        result = mutants[mutant_name](*call_args, **call_kwargs) # type: ignore
    return result # type: ignore


class Reporter:
    """Formats and outputs evaluation results."""
    
    def __init__(self, config: EvalConfig):
        args = [config]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁReporterǁ__init____mutmut_orig'), object.__getattribute__(self, 'xǁReporterǁ__init____mutmut_mutants'), args, kwargs, self)
    
    def xǁReporterǁ__init____mutmut_orig(self, config: EvalConfig):
        self.config = config
        self.console = Console()
    
    def xǁReporterǁ__init____mutmut_1(self, config: EvalConfig):
        self.config = None
        self.console = Console()
    
    def xǁReporterǁ__init____mutmut_2(self, config: EvalConfig):
        self.config = config
        self.console = None
    
    xǁReporterǁ__init____mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁReporterǁ__init____mutmut_1': xǁReporterǁ__init____mutmut_1, 
        'xǁReporterǁ__init____mutmut_2': xǁReporterǁ__init____mutmut_2
    }
    xǁReporterǁ__init____mutmut_orig.__name__ = 'xǁReporterǁ__init__'
    
    def report_terminal(
        self,
        results: list[ExecutionResult],
        verbose: bool = False
    ) -> None:
        args = [results, verbose]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁReporterǁreport_terminal__mutmut_orig'), object.__getattribute__(self, 'xǁReporterǁreport_terminal__mutmut_mutants'), args, kwargs, self)
    
    def xǁReporterǁreport_terminal__mutmut_orig(
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
    
    def xǁReporterǁreport_terminal__mutmut_1(
        self,
        results: list[ExecutionResult],
        verbose: bool = True
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
    
    def xǁReporterǁreport_terminal__mutmut_2(
        self,
        results: list[ExecutionResult],
        verbose: bool = False
    ) -> None:
        """Print results to terminal.
        
        Args:
            results: List of execution results
            verbose: Show detailed output
        """
        if results:
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
    
    def xǁReporterǁreport_terminal__mutmut_3(
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
            self.console.print(None)
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
    
    def xǁReporterǁreport_terminal__mutmut_4(
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
            self.console.print("XX[yellow]No results to display[/yellow]XX")
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
    
    def xǁReporterǁreport_terminal__mutmut_5(
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
            self.console.print("[yellow]no results to display[/yellow]")
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
    
    def xǁReporterǁreport_terminal__mutmut_6(
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
            self.console.print("[YELLOW]NO RESULTS TO DISPLAY[/YELLOW]")
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
    
    def xǁReporterǁreport_terminal__mutmut_7(
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
        by_treatment: dict[str, list[ExecutionResult]] = None
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
    
    def xǁReporterǁreport_terminal__mutmut_8(
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
            if result.treatment in by_treatment:
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
    
    def xǁReporterǁreport_terminal__mutmut_9(
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
                by_treatment[result.treatment] = None
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
    
    def xǁReporterǁreport_terminal__mutmut_10(
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
            by_treatment[result.treatment].append(None)
        
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
    
    def xǁReporterǁreport_terminal__mutmut_11(
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
        table = None
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
    
    def xǁReporterǁreport_terminal__mutmut_12(
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
            title=None,
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
    
    def xǁReporterǁreport_terminal__mutmut_13(
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
            box=None,
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
    
    def xǁReporterǁreport_terminal__mutmut_14(
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
            show_header=None,
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
    
    def xǁReporterǁreport_terminal__mutmut_15(
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
            header_style=None
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
    
    def xǁReporterǁreport_terminal__mutmut_16(
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
    
    def xǁReporterǁreport_terminal__mutmut_17(
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
    
    def xǁReporterǁreport_terminal__mutmut_18(
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
    
    def xǁReporterǁreport_terminal__mutmut_19(
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
    
    def xǁReporterǁreport_terminal__mutmut_20(
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
            title="XXmd-evals ResultsXX",
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
    
    def xǁReporterǁreport_terminal__mutmut_21(
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
            title="md-evals results",
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
    
    def xǁReporterǁreport_terminal__mutmut_22(
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
            title="MD-EVALS RESULTS",
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
    
    def xǁReporterǁreport_terminal__mutmut_23(
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
            show_header=False,
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
    
    def xǁReporterǁreport_terminal__mutmut_24(
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
            header_style="XXbold magentaXX"
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
    
    def xǁReporterǁreport_terminal__mutmut_25(
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
            header_style="BOLD MAGENTA"
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
    
    def xǁReporterǁreport_terminal__mutmut_26(
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
        table.add_column(None, style="cyan")
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
    
    def xǁReporterǁreport_terminal__mutmut_27(
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
        table.add_column("Treatment", style=None)
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
    
    def xǁReporterǁreport_terminal__mutmut_28(
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
        table.add_column(style="cyan")
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
    
    def xǁReporterǁreport_terminal__mutmut_29(
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
        table.add_column("Treatment", )
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
    
    def xǁReporterǁreport_terminal__mutmut_30(
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
        table.add_column("XXTreatmentXX", style="cyan")
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
    
    def xǁReporterǁreport_terminal__mutmut_31(
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
        table.add_column("treatment", style="cyan")
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
    
    def xǁReporterǁreport_terminal__mutmut_32(
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
        table.add_column("TREATMENT", style="cyan")
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
    
    def xǁReporterǁreport_terminal__mutmut_33(
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
        table.add_column("Treatment", style="XXcyanXX")
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
    
    def xǁReporterǁreport_terminal__mutmut_34(
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
        table.add_column("Treatment", style="CYAN")
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
    
    def xǁReporterǁreport_terminal__mutmut_35(
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
        table.add_column(None, justify="center")
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
    
    def xǁReporterǁreport_terminal__mutmut_36(
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
        table.add_column("Tests", justify=None)
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
    
    def xǁReporterǁreport_terminal__mutmut_37(
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
        table.add_column(justify="center")
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
    
    def xǁReporterǁreport_terminal__mutmut_38(
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
        table.add_column("Tests", )
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
    
    def xǁReporterǁreport_terminal__mutmut_39(
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
        table.add_column("XXTestsXX", justify="center")
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
    
    def xǁReporterǁreport_terminal__mutmut_40(
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
        table.add_column("tests", justify="center")
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
    
    def xǁReporterǁreport_terminal__mutmut_41(
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
        table.add_column("TESTS", justify="center")
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
    
    def xǁReporterǁreport_terminal__mutmut_42(
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
        table.add_column("Tests", justify="XXcenterXX")
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
    
    def xǁReporterǁreport_terminal__mutmut_43(
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
        table.add_column("Tests", justify="CENTER")
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
    
    def xǁReporterǁreport_terminal__mutmut_44(
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
        table.add_column(None, justify="center")
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
    
    def xǁReporterǁreport_terminal__mutmut_45(
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
        table.add_column("Passed", justify=None)
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
    
    def xǁReporterǁreport_terminal__mutmut_46(
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
        table.add_column(justify="center")
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
    
    def xǁReporterǁreport_terminal__mutmut_47(
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
        table.add_column("Passed", )
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
    
    def xǁReporterǁreport_terminal__mutmut_48(
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
        table.add_column("XXPassedXX", justify="center")
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
    
    def xǁReporterǁreport_terminal__mutmut_49(
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
        table.add_column("passed", justify="center")
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
    
    def xǁReporterǁreport_terminal__mutmut_50(
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
        table.add_column("PASSED", justify="center")
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
    
    def xǁReporterǁreport_terminal__mutmut_51(
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
        table.add_column("Passed", justify="XXcenterXX")
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
    
    def xǁReporterǁreport_terminal__mutmut_52(
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
        table.add_column("Passed", justify="CENTER")
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
    
    def xǁReporterǁreport_terminal__mutmut_53(
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
        table.add_column(None, justify="center")
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
    
    def xǁReporterǁreport_terminal__mutmut_54(
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
        table.add_column("Pass Rate", justify=None)
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
    
    def xǁReporterǁreport_terminal__mutmut_55(
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
        table.add_column(justify="center")
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
    
    def xǁReporterǁreport_terminal__mutmut_56(
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
        table.add_column("Pass Rate", )
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
    
    def xǁReporterǁreport_terminal__mutmut_57(
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
        table.add_column("XXPass RateXX", justify="center")
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
    
    def xǁReporterǁreport_terminal__mutmut_58(
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
        table.add_column("pass rate", justify="center")
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
    
    def xǁReporterǁreport_terminal__mutmut_59(
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
        table.add_column("PASS RATE", justify="center")
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
    
    def xǁReporterǁreport_terminal__mutmut_60(
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
        table.add_column("Pass Rate", justify="XXcenterXX")
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
    
    def xǁReporterǁreport_terminal__mutmut_61(
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
        table.add_column("Pass Rate", justify="CENTER")
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
    
    def xǁReporterǁreport_terminal__mutmut_62(
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
        table.add_column(None, justify="center")
        
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
    
    def xǁReporterǁreport_terminal__mutmut_63(
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
        table.add_column("Avg Duration", justify=None)
        
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
    
    def xǁReporterǁreport_terminal__mutmut_64(
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
        table.add_column(justify="center")
        
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
    
    def xǁReporterǁreport_terminal__mutmut_65(
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
        table.add_column("Avg Duration", )
        
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
    
    def xǁReporterǁreport_terminal__mutmut_66(
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
        table.add_column("XXAvg DurationXX", justify="center")
        
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
    
    def xǁReporterǁreport_terminal__mutmut_67(
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
        table.add_column("avg duration", justify="center")
        
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
    
    def xǁReporterǁreport_terminal__mutmut_68(
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
        table.add_column("AVG DURATION", justify="center")
        
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
    
    def xǁReporterǁreport_terminal__mutmut_69(
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
        table.add_column("Avg Duration", justify="XXcenterXX")
        
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
    
    def xǁReporterǁreport_terminal__mutmut_70(
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
        table.add_column("Avg Duration", justify="CENTER")
        
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
    
    def xǁReporterǁreport_terminal__mutmut_71(
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
            total = None
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
    
    def xǁReporterǁreport_terminal__mutmut_72(
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
            passed = None
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
    
    def xǁReporterǁreport_terminal__mutmut_73(
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
            passed = sum(None)
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
    
    def xǁReporterǁreport_terminal__mutmut_74(
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
            passed = sum(2 for r in treatment_results if r.passed)
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
    
    def xǁReporterǁreport_terminal__mutmut_75(
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
            pass_rate = None
            
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
    
    def xǁReporterǁreport_terminal__mutmut_76(
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
            pass_rate = (passed / total / 100) if total > 0 else 0
            
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
    
    def xǁReporterǁreport_terminal__mutmut_77(
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
            pass_rate = (passed * total * 100) if total > 0 else 0
            
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
    
    def xǁReporterǁreport_terminal__mutmut_78(
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
            pass_rate = (passed / total * 101) if total > 0 else 0
            
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
    
    def xǁReporterǁreport_terminal__mutmut_79(
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
            pass_rate = (passed / total * 100) if total >= 0 else 0
            
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
    
    def xǁReporterǁreport_terminal__mutmut_80(
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
            pass_rate = (passed / total * 100) if total > 1 else 0
            
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
    
    def xǁReporterǁreport_terminal__mutmut_81(
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
            pass_rate = (passed / total * 100) if total > 0 else 1
            
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
    
    def xǁReporterǁreport_terminal__mutmut_82(
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
            durations = None
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
    
    def xǁReporterǁreport_terminal__mutmut_83(
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
            avg_duration = None
            
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
    
    def xǁReporterǁreport_terminal__mutmut_84(
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
            avg_duration = sum(durations) * len(durations) if durations else 0
            
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
    
    def xǁReporterǁreport_terminal__mutmut_85(
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
            avg_duration = sum(None) / len(durations) if durations else 0
            
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
    
    def xǁReporterǁreport_terminal__mutmut_86(
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
            avg_duration = sum(durations) / len(durations) if durations else 1
            
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
    
    def xǁReporterǁreport_terminal__mutmut_87(
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
            if pass_rate > 80:
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
    
    def xǁReporterǁreport_terminal__mutmut_88(
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
            if pass_rate >= 81:
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
    
    def xǁReporterǁreport_terminal__mutmut_89(
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
                pass_style = None
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
    
    def xǁReporterǁreport_terminal__mutmut_90(
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
                pass_style = "XXgreenXX"
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
    
    def xǁReporterǁreport_terminal__mutmut_91(
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
                pass_style = "GREEN"
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
    
    def xǁReporterǁreport_terminal__mutmut_92(
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
            elif pass_rate > 50:
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
    
    def xǁReporterǁreport_terminal__mutmut_93(
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
            elif pass_rate >= 51:
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
    
    def xǁReporterǁreport_terminal__mutmut_94(
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
                pass_style = None
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
    
    def xǁReporterǁreport_terminal__mutmut_95(
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
                pass_style = "XXyellowXX"
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
    
    def xǁReporterǁreport_terminal__mutmut_96(
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
                pass_style = "YELLOW"
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
    
    def xǁReporterǁreport_terminal__mutmut_97(
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
                pass_style = None
            
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
    
    def xǁReporterǁreport_terminal__mutmut_98(
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
                pass_style = "XXredXX"
            
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
    
    def xǁReporterǁreport_terminal__mutmut_99(
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
                pass_style = "RED"
            
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
    
    def xǁReporterǁreport_terminal__mutmut_100(
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
                None,
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
    
    def xǁReporterǁreport_terminal__mutmut_101(
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
                None,
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
    
    def xǁReporterǁreport_terminal__mutmut_102(
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
                None,
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
    
    def xǁReporterǁreport_terminal__mutmut_103(
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
                None,
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
    
    def xǁReporterǁreport_terminal__mutmut_104(
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
                None
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
    
    def xǁReporterǁreport_terminal__mutmut_105(
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
    
    def xǁReporterǁreport_terminal__mutmut_106(
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
    
    def xǁReporterǁreport_terminal__mutmut_107(
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
    
    def xǁReporterǁreport_terminal__mutmut_108(
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
    
    def xǁReporterǁreport_terminal__mutmut_109(
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
    
    def xǁReporterǁreport_terminal__mutmut_110(
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
        self.console.print(None)
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
    
    def xǁReporterǁreport_terminal__mutmut_111(
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
        if "XXCONTROLXX" in by_treatment:
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
    
    def xǁReporterǁreport_terminal__mutmut_112(
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
        if "control" in by_treatment:
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
    
    def xǁReporterǁreport_terminal__mutmut_113(
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
        if "CONTROL" not in by_treatment:
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
    
    def xǁReporterǁreport_terminal__mutmut_114(
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
            control_passed = None
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
    
    def xǁReporterǁreport_terminal__mutmut_115(
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
            control_passed = sum(None)
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
    
    def xǁReporterǁreport_terminal__mutmut_116(
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
            control_passed = sum(2 for r in by_treatment["CONTROL"] if r.passed)
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
    
    def xǁReporterǁreport_terminal__mutmut_117(
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
            control_passed = sum(1 for r in by_treatment["XXCONTROLXX"] if r.passed)
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
    
    def xǁReporterǁreport_terminal__mutmut_118(
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
            control_passed = sum(1 for r in by_treatment["control"] if r.passed)
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
    
    def xǁReporterǁreport_terminal__mutmut_119(
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
            control_total = None
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
    
    def xǁReporterǁreport_terminal__mutmut_120(
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
            control_rate = None
            
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
    
    def xǁReporterǁreport_terminal__mutmut_121(
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
            control_rate = (control_passed / control_total / 100) if control_total > 0 else 0
            
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
    
    def xǁReporterǁreport_terminal__mutmut_122(
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
            control_rate = (control_passed * control_total * 100) if control_total > 0 else 0
            
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
    
    def xǁReporterǁreport_terminal__mutmut_123(
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
            control_rate = (control_passed / control_total * 101) if control_total > 0 else 0
            
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
    
    def xǁReporterǁreport_terminal__mutmut_124(
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
            control_rate = (control_passed / control_total * 100) if control_total >= 0 else 0
            
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
    
    def xǁReporterǁreport_terminal__mutmut_125(
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
            control_rate = (control_passed / control_total * 100) if control_total > 1 else 0
            
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
    
    def xǁReporterǁreport_terminal__mutmut_126(
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
            control_rate = (control_passed / control_total * 100) if control_total > 0 else 1
            
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
    
    def xǁReporterǁreport_terminal__mutmut_127(
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
                if treatment != "CONTROL":
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
    
    def xǁReporterǁreport_terminal__mutmut_128(
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
                if treatment == "XXCONTROLXX":
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
    
    def xǁReporterǁreport_terminal__mutmut_129(
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
                if treatment == "control":
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
    
    def xǁReporterǁreport_terminal__mutmut_130(
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
                    break
                
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
    
    def xǁReporterǁreport_terminal__mutmut_131(
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
                
                treatment_passed = None
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
    
    def xǁReporterǁreport_terminal__mutmut_132(
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
                
                treatment_passed = sum(None)
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
    
    def xǁReporterǁreport_terminal__mutmut_133(
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
                
                treatment_passed = sum(2 for r in treatment_results if r.passed)
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
    
    def xǁReporterǁreport_terminal__mutmut_134(
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
                treatment_total = None
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
    
    def xǁReporterǁreport_terminal__mutmut_135(
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
                treatment_rate = None
                
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
    
    def xǁReporterǁreport_terminal__mutmut_136(
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
                treatment_rate = (treatment_passed / treatment_total / 100) if treatment_total > 0 else 0
                
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
    
    def xǁReporterǁreport_terminal__mutmut_137(
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
                treatment_rate = (treatment_passed * treatment_total * 100) if treatment_total > 0 else 0
                
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
    
    def xǁReporterǁreport_terminal__mutmut_138(
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
                treatment_rate = (treatment_passed / treatment_total * 101) if treatment_total > 0 else 0
                
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
    
    def xǁReporterǁreport_terminal__mutmut_139(
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
                treatment_rate = (treatment_passed / treatment_total * 100) if treatment_total >= 0 else 0
                
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
    
    def xǁReporterǁreport_terminal__mutmut_140(
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
                treatment_rate = (treatment_passed / treatment_total * 100) if treatment_total > 1 else 0
                
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
    
    def xǁReporterǁreport_terminal__mutmut_141(
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
                treatment_rate = (treatment_passed / treatment_total * 100) if treatment_total > 0 else 1
                
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
    
    def xǁReporterǁreport_terminal__mutmut_142(
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
                
                improvement = None
                
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
    
    def xǁReporterǁreport_terminal__mutmut_143(
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
                
                improvement = treatment_rate + control_rate
                
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
    
    def xǁReporterǁreport_terminal__mutmut_144(
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
                
                if improvement >= 0:
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
    
    def xǁReporterǁreport_terminal__mutmut_145(
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
                
                if improvement > 1:
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
    
    def xǁReporterǁreport_terminal__mutmut_146(
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
                        None
                    )
                elif improvement < 0:
                    self.console.print(
                        f"[red]▼[/red] {treatment}: {improvement:.0f}% vs CONTROL"
                    )
        
        # Verbose output
        if verbose:
            self._print_verbose(results)
    
    def xǁReporterǁreport_terminal__mutmut_147(
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
                elif improvement <= 0:
                    self.console.print(
                        f"[red]▼[/red] {treatment}: {improvement:.0f}% vs CONTROL"
                    )
        
        # Verbose output
        if verbose:
            self._print_verbose(results)
    
    def xǁReporterǁreport_terminal__mutmut_148(
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
                elif improvement < 1:
                    self.console.print(
                        f"[red]▼[/red] {treatment}: {improvement:.0f}% vs CONTROL"
                    )
        
        # Verbose output
        if verbose:
            self._print_verbose(results)
    
    def xǁReporterǁreport_terminal__mutmut_149(
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
                        None
                    )
        
        # Verbose output
        if verbose:
            self._print_verbose(results)
    
    def xǁReporterǁreport_terminal__mutmut_150(
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
            self._print_verbose(None)
    
    xǁReporterǁreport_terminal__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁReporterǁreport_terminal__mutmut_1': xǁReporterǁreport_terminal__mutmut_1, 
        'xǁReporterǁreport_terminal__mutmut_2': xǁReporterǁreport_terminal__mutmut_2, 
        'xǁReporterǁreport_terminal__mutmut_3': xǁReporterǁreport_terminal__mutmut_3, 
        'xǁReporterǁreport_terminal__mutmut_4': xǁReporterǁreport_terminal__mutmut_4, 
        'xǁReporterǁreport_terminal__mutmut_5': xǁReporterǁreport_terminal__mutmut_5, 
        'xǁReporterǁreport_terminal__mutmut_6': xǁReporterǁreport_terminal__mutmut_6, 
        'xǁReporterǁreport_terminal__mutmut_7': xǁReporterǁreport_terminal__mutmut_7, 
        'xǁReporterǁreport_terminal__mutmut_8': xǁReporterǁreport_terminal__mutmut_8, 
        'xǁReporterǁreport_terminal__mutmut_9': xǁReporterǁreport_terminal__mutmut_9, 
        'xǁReporterǁreport_terminal__mutmut_10': xǁReporterǁreport_terminal__mutmut_10, 
        'xǁReporterǁreport_terminal__mutmut_11': xǁReporterǁreport_terminal__mutmut_11, 
        'xǁReporterǁreport_terminal__mutmut_12': xǁReporterǁreport_terminal__mutmut_12, 
        'xǁReporterǁreport_terminal__mutmut_13': xǁReporterǁreport_terminal__mutmut_13, 
        'xǁReporterǁreport_terminal__mutmut_14': xǁReporterǁreport_terminal__mutmut_14, 
        'xǁReporterǁreport_terminal__mutmut_15': xǁReporterǁreport_terminal__mutmut_15, 
        'xǁReporterǁreport_terminal__mutmut_16': xǁReporterǁreport_terminal__mutmut_16, 
        'xǁReporterǁreport_terminal__mutmut_17': xǁReporterǁreport_terminal__mutmut_17, 
        'xǁReporterǁreport_terminal__mutmut_18': xǁReporterǁreport_terminal__mutmut_18, 
        'xǁReporterǁreport_terminal__mutmut_19': xǁReporterǁreport_terminal__mutmut_19, 
        'xǁReporterǁreport_terminal__mutmut_20': xǁReporterǁreport_terminal__mutmut_20, 
        'xǁReporterǁreport_terminal__mutmut_21': xǁReporterǁreport_terminal__mutmut_21, 
        'xǁReporterǁreport_terminal__mutmut_22': xǁReporterǁreport_terminal__mutmut_22, 
        'xǁReporterǁreport_terminal__mutmut_23': xǁReporterǁreport_terminal__mutmut_23, 
        'xǁReporterǁreport_terminal__mutmut_24': xǁReporterǁreport_terminal__mutmut_24, 
        'xǁReporterǁreport_terminal__mutmut_25': xǁReporterǁreport_terminal__mutmut_25, 
        'xǁReporterǁreport_terminal__mutmut_26': xǁReporterǁreport_terminal__mutmut_26, 
        'xǁReporterǁreport_terminal__mutmut_27': xǁReporterǁreport_terminal__mutmut_27, 
        'xǁReporterǁreport_terminal__mutmut_28': xǁReporterǁreport_terminal__mutmut_28, 
        'xǁReporterǁreport_terminal__mutmut_29': xǁReporterǁreport_terminal__mutmut_29, 
        'xǁReporterǁreport_terminal__mutmut_30': xǁReporterǁreport_terminal__mutmut_30, 
        'xǁReporterǁreport_terminal__mutmut_31': xǁReporterǁreport_terminal__mutmut_31, 
        'xǁReporterǁreport_terminal__mutmut_32': xǁReporterǁreport_terminal__mutmut_32, 
        'xǁReporterǁreport_terminal__mutmut_33': xǁReporterǁreport_terminal__mutmut_33, 
        'xǁReporterǁreport_terminal__mutmut_34': xǁReporterǁreport_terminal__mutmut_34, 
        'xǁReporterǁreport_terminal__mutmut_35': xǁReporterǁreport_terminal__mutmut_35, 
        'xǁReporterǁreport_terminal__mutmut_36': xǁReporterǁreport_terminal__mutmut_36, 
        'xǁReporterǁreport_terminal__mutmut_37': xǁReporterǁreport_terminal__mutmut_37, 
        'xǁReporterǁreport_terminal__mutmut_38': xǁReporterǁreport_terminal__mutmut_38, 
        'xǁReporterǁreport_terminal__mutmut_39': xǁReporterǁreport_terminal__mutmut_39, 
        'xǁReporterǁreport_terminal__mutmut_40': xǁReporterǁreport_terminal__mutmut_40, 
        'xǁReporterǁreport_terminal__mutmut_41': xǁReporterǁreport_terminal__mutmut_41, 
        'xǁReporterǁreport_terminal__mutmut_42': xǁReporterǁreport_terminal__mutmut_42, 
        'xǁReporterǁreport_terminal__mutmut_43': xǁReporterǁreport_terminal__mutmut_43, 
        'xǁReporterǁreport_terminal__mutmut_44': xǁReporterǁreport_terminal__mutmut_44, 
        'xǁReporterǁreport_terminal__mutmut_45': xǁReporterǁreport_terminal__mutmut_45, 
        'xǁReporterǁreport_terminal__mutmut_46': xǁReporterǁreport_terminal__mutmut_46, 
        'xǁReporterǁreport_terminal__mutmut_47': xǁReporterǁreport_terminal__mutmut_47, 
        'xǁReporterǁreport_terminal__mutmut_48': xǁReporterǁreport_terminal__mutmut_48, 
        'xǁReporterǁreport_terminal__mutmut_49': xǁReporterǁreport_terminal__mutmut_49, 
        'xǁReporterǁreport_terminal__mutmut_50': xǁReporterǁreport_terminal__mutmut_50, 
        'xǁReporterǁreport_terminal__mutmut_51': xǁReporterǁreport_terminal__mutmut_51, 
        'xǁReporterǁreport_terminal__mutmut_52': xǁReporterǁreport_terminal__mutmut_52, 
        'xǁReporterǁreport_terminal__mutmut_53': xǁReporterǁreport_terminal__mutmut_53, 
        'xǁReporterǁreport_terminal__mutmut_54': xǁReporterǁreport_terminal__mutmut_54, 
        'xǁReporterǁreport_terminal__mutmut_55': xǁReporterǁreport_terminal__mutmut_55, 
        'xǁReporterǁreport_terminal__mutmut_56': xǁReporterǁreport_terminal__mutmut_56, 
        'xǁReporterǁreport_terminal__mutmut_57': xǁReporterǁreport_terminal__mutmut_57, 
        'xǁReporterǁreport_terminal__mutmut_58': xǁReporterǁreport_terminal__mutmut_58, 
        'xǁReporterǁreport_terminal__mutmut_59': xǁReporterǁreport_terminal__mutmut_59, 
        'xǁReporterǁreport_terminal__mutmut_60': xǁReporterǁreport_terminal__mutmut_60, 
        'xǁReporterǁreport_terminal__mutmut_61': xǁReporterǁreport_terminal__mutmut_61, 
        'xǁReporterǁreport_terminal__mutmut_62': xǁReporterǁreport_terminal__mutmut_62, 
        'xǁReporterǁreport_terminal__mutmut_63': xǁReporterǁreport_terminal__mutmut_63, 
        'xǁReporterǁreport_terminal__mutmut_64': xǁReporterǁreport_terminal__mutmut_64, 
        'xǁReporterǁreport_terminal__mutmut_65': xǁReporterǁreport_terminal__mutmut_65, 
        'xǁReporterǁreport_terminal__mutmut_66': xǁReporterǁreport_terminal__mutmut_66, 
        'xǁReporterǁreport_terminal__mutmut_67': xǁReporterǁreport_terminal__mutmut_67, 
        'xǁReporterǁreport_terminal__mutmut_68': xǁReporterǁreport_terminal__mutmut_68, 
        'xǁReporterǁreport_terminal__mutmut_69': xǁReporterǁreport_terminal__mutmut_69, 
        'xǁReporterǁreport_terminal__mutmut_70': xǁReporterǁreport_terminal__mutmut_70, 
        'xǁReporterǁreport_terminal__mutmut_71': xǁReporterǁreport_terminal__mutmut_71, 
        'xǁReporterǁreport_terminal__mutmut_72': xǁReporterǁreport_terminal__mutmut_72, 
        'xǁReporterǁreport_terminal__mutmut_73': xǁReporterǁreport_terminal__mutmut_73, 
        'xǁReporterǁreport_terminal__mutmut_74': xǁReporterǁreport_terminal__mutmut_74, 
        'xǁReporterǁreport_terminal__mutmut_75': xǁReporterǁreport_terminal__mutmut_75, 
        'xǁReporterǁreport_terminal__mutmut_76': xǁReporterǁreport_terminal__mutmut_76, 
        'xǁReporterǁreport_terminal__mutmut_77': xǁReporterǁreport_terminal__mutmut_77, 
        'xǁReporterǁreport_terminal__mutmut_78': xǁReporterǁreport_terminal__mutmut_78, 
        'xǁReporterǁreport_terminal__mutmut_79': xǁReporterǁreport_terminal__mutmut_79, 
        'xǁReporterǁreport_terminal__mutmut_80': xǁReporterǁreport_terminal__mutmut_80, 
        'xǁReporterǁreport_terminal__mutmut_81': xǁReporterǁreport_terminal__mutmut_81, 
        'xǁReporterǁreport_terminal__mutmut_82': xǁReporterǁreport_terminal__mutmut_82, 
        'xǁReporterǁreport_terminal__mutmut_83': xǁReporterǁreport_terminal__mutmut_83, 
        'xǁReporterǁreport_terminal__mutmut_84': xǁReporterǁreport_terminal__mutmut_84, 
        'xǁReporterǁreport_terminal__mutmut_85': xǁReporterǁreport_terminal__mutmut_85, 
        'xǁReporterǁreport_terminal__mutmut_86': xǁReporterǁreport_terminal__mutmut_86, 
        'xǁReporterǁreport_terminal__mutmut_87': xǁReporterǁreport_terminal__mutmut_87, 
        'xǁReporterǁreport_terminal__mutmut_88': xǁReporterǁreport_terminal__mutmut_88, 
        'xǁReporterǁreport_terminal__mutmut_89': xǁReporterǁreport_terminal__mutmut_89, 
        'xǁReporterǁreport_terminal__mutmut_90': xǁReporterǁreport_terminal__mutmut_90, 
        'xǁReporterǁreport_terminal__mutmut_91': xǁReporterǁreport_terminal__mutmut_91, 
        'xǁReporterǁreport_terminal__mutmut_92': xǁReporterǁreport_terminal__mutmut_92, 
        'xǁReporterǁreport_terminal__mutmut_93': xǁReporterǁreport_terminal__mutmut_93, 
        'xǁReporterǁreport_terminal__mutmut_94': xǁReporterǁreport_terminal__mutmut_94, 
        'xǁReporterǁreport_terminal__mutmut_95': xǁReporterǁreport_terminal__mutmut_95, 
        'xǁReporterǁreport_terminal__mutmut_96': xǁReporterǁreport_terminal__mutmut_96, 
        'xǁReporterǁreport_terminal__mutmut_97': xǁReporterǁreport_terminal__mutmut_97, 
        'xǁReporterǁreport_terminal__mutmut_98': xǁReporterǁreport_terminal__mutmut_98, 
        'xǁReporterǁreport_terminal__mutmut_99': xǁReporterǁreport_terminal__mutmut_99, 
        'xǁReporterǁreport_terminal__mutmut_100': xǁReporterǁreport_terminal__mutmut_100, 
        'xǁReporterǁreport_terminal__mutmut_101': xǁReporterǁreport_terminal__mutmut_101, 
        'xǁReporterǁreport_terminal__mutmut_102': xǁReporterǁreport_terminal__mutmut_102, 
        'xǁReporterǁreport_terminal__mutmut_103': xǁReporterǁreport_terminal__mutmut_103, 
        'xǁReporterǁreport_terminal__mutmut_104': xǁReporterǁreport_terminal__mutmut_104, 
        'xǁReporterǁreport_terminal__mutmut_105': xǁReporterǁreport_terminal__mutmut_105, 
        'xǁReporterǁreport_terminal__mutmut_106': xǁReporterǁreport_terminal__mutmut_106, 
        'xǁReporterǁreport_terminal__mutmut_107': xǁReporterǁreport_terminal__mutmut_107, 
        'xǁReporterǁreport_terminal__mutmut_108': xǁReporterǁreport_terminal__mutmut_108, 
        'xǁReporterǁreport_terminal__mutmut_109': xǁReporterǁreport_terminal__mutmut_109, 
        'xǁReporterǁreport_terminal__mutmut_110': xǁReporterǁreport_terminal__mutmut_110, 
        'xǁReporterǁreport_terminal__mutmut_111': xǁReporterǁreport_terminal__mutmut_111, 
        'xǁReporterǁreport_terminal__mutmut_112': xǁReporterǁreport_terminal__mutmut_112, 
        'xǁReporterǁreport_terminal__mutmut_113': xǁReporterǁreport_terminal__mutmut_113, 
        'xǁReporterǁreport_terminal__mutmut_114': xǁReporterǁreport_terminal__mutmut_114, 
        'xǁReporterǁreport_terminal__mutmut_115': xǁReporterǁreport_terminal__mutmut_115, 
        'xǁReporterǁreport_terminal__mutmut_116': xǁReporterǁreport_terminal__mutmut_116, 
        'xǁReporterǁreport_terminal__mutmut_117': xǁReporterǁreport_terminal__mutmut_117, 
        'xǁReporterǁreport_terminal__mutmut_118': xǁReporterǁreport_terminal__mutmut_118, 
        'xǁReporterǁreport_terminal__mutmut_119': xǁReporterǁreport_terminal__mutmut_119, 
        'xǁReporterǁreport_terminal__mutmut_120': xǁReporterǁreport_terminal__mutmut_120, 
        'xǁReporterǁreport_terminal__mutmut_121': xǁReporterǁreport_terminal__mutmut_121, 
        'xǁReporterǁreport_terminal__mutmut_122': xǁReporterǁreport_terminal__mutmut_122, 
        'xǁReporterǁreport_terminal__mutmut_123': xǁReporterǁreport_terminal__mutmut_123, 
        'xǁReporterǁreport_terminal__mutmut_124': xǁReporterǁreport_terminal__mutmut_124, 
        'xǁReporterǁreport_terminal__mutmut_125': xǁReporterǁreport_terminal__mutmut_125, 
        'xǁReporterǁreport_terminal__mutmut_126': xǁReporterǁreport_terminal__mutmut_126, 
        'xǁReporterǁreport_terminal__mutmut_127': xǁReporterǁreport_terminal__mutmut_127, 
        'xǁReporterǁreport_terminal__mutmut_128': xǁReporterǁreport_terminal__mutmut_128, 
        'xǁReporterǁreport_terminal__mutmut_129': xǁReporterǁreport_terminal__mutmut_129, 
        'xǁReporterǁreport_terminal__mutmut_130': xǁReporterǁreport_terminal__mutmut_130, 
        'xǁReporterǁreport_terminal__mutmut_131': xǁReporterǁreport_terminal__mutmut_131, 
        'xǁReporterǁreport_terminal__mutmut_132': xǁReporterǁreport_terminal__mutmut_132, 
        'xǁReporterǁreport_terminal__mutmut_133': xǁReporterǁreport_terminal__mutmut_133, 
        'xǁReporterǁreport_terminal__mutmut_134': xǁReporterǁreport_terminal__mutmut_134, 
        'xǁReporterǁreport_terminal__mutmut_135': xǁReporterǁreport_terminal__mutmut_135, 
        'xǁReporterǁreport_terminal__mutmut_136': xǁReporterǁreport_terminal__mutmut_136, 
        'xǁReporterǁreport_terminal__mutmut_137': xǁReporterǁreport_terminal__mutmut_137, 
        'xǁReporterǁreport_terminal__mutmut_138': xǁReporterǁreport_terminal__mutmut_138, 
        'xǁReporterǁreport_terminal__mutmut_139': xǁReporterǁreport_terminal__mutmut_139, 
        'xǁReporterǁreport_terminal__mutmut_140': xǁReporterǁreport_terminal__mutmut_140, 
        'xǁReporterǁreport_terminal__mutmut_141': xǁReporterǁreport_terminal__mutmut_141, 
        'xǁReporterǁreport_terminal__mutmut_142': xǁReporterǁreport_terminal__mutmut_142, 
        'xǁReporterǁreport_terminal__mutmut_143': xǁReporterǁreport_terminal__mutmut_143, 
        'xǁReporterǁreport_terminal__mutmut_144': xǁReporterǁreport_terminal__mutmut_144, 
        'xǁReporterǁreport_terminal__mutmut_145': xǁReporterǁreport_terminal__mutmut_145, 
        'xǁReporterǁreport_terminal__mutmut_146': xǁReporterǁreport_terminal__mutmut_146, 
        'xǁReporterǁreport_terminal__mutmut_147': xǁReporterǁreport_terminal__mutmut_147, 
        'xǁReporterǁreport_terminal__mutmut_148': xǁReporterǁreport_terminal__mutmut_148, 
        'xǁReporterǁreport_terminal__mutmut_149': xǁReporterǁreport_terminal__mutmut_149, 
        'xǁReporterǁreport_terminal__mutmut_150': xǁReporterǁreport_terminal__mutmut_150
    }
    xǁReporterǁreport_terminal__mutmut_orig.__name__ = 'xǁReporterǁreport_terminal'
    
    def _print_verbose(self, results: list[ExecutionResult]) -> None:
        args = [results]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁReporterǁ_print_verbose__mutmut_orig'), object.__getattribute__(self, 'xǁReporterǁ_print_verbose__mutmut_mutants'), args, kwargs, self)
    
    def xǁReporterǁ_print_verbose__mutmut_orig(self, results: list[ExecutionResult]) -> None:
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
    
    def xǁReporterǁ_print_verbose__mutmut_1(self, results: list[ExecutionResult]) -> None:
        """Print verbose results."""
        for result in results:
            panel = None
            self.console.print(panel)
    
    def xǁReporterǁ_print_verbose__mutmut_2(self, results: list[ExecutionResult]) -> None:
        """Print verbose results."""
        for result in results:
            panel = Panel(
                None,
                title=f"Result: {result.treatment}/{result.test}",
                border_style="blue" if result.passed else "red"
            )
            self.console.print(panel)
    
    def xǁReporterǁ_print_verbose__mutmut_3(self, results: list[ExecutionResult]) -> None:
        """Print verbose results."""
        for result in results:
            panel = Panel(
                f"[bold]Test:[/bold] {result.test}\n"
                f"[bold]Treatment:[/bold] {result.treatment}\n"
                f"[bold]Passed:[/bold] {result.passed}\n"
                f"[bold]Duration:[/bold] {result.response.duration_ms if result.response else 'N/A'}ms",
                title=None,
                border_style="blue" if result.passed else "red"
            )
            self.console.print(panel)
    
    def xǁReporterǁ_print_verbose__mutmut_4(self, results: list[ExecutionResult]) -> None:
        """Print verbose results."""
        for result in results:
            panel = Panel(
                f"[bold]Test:[/bold] {result.test}\n"
                f"[bold]Treatment:[/bold] {result.treatment}\n"
                f"[bold]Passed:[/bold] {result.passed}\n"
                f"[bold]Duration:[/bold] {result.response.duration_ms if result.response else 'N/A'}ms",
                title=f"Result: {result.treatment}/{result.test}",
                border_style=None
            )
            self.console.print(panel)
    
    def xǁReporterǁ_print_verbose__mutmut_5(self, results: list[ExecutionResult]) -> None:
        """Print verbose results."""
        for result in results:
            panel = Panel(
                title=f"Result: {result.treatment}/{result.test}",
                border_style="blue" if result.passed else "red"
            )
            self.console.print(panel)
    
    def xǁReporterǁ_print_verbose__mutmut_6(self, results: list[ExecutionResult]) -> None:
        """Print verbose results."""
        for result in results:
            panel = Panel(
                f"[bold]Test:[/bold] {result.test}\n"
                f"[bold]Treatment:[/bold] {result.treatment}\n"
                f"[bold]Passed:[/bold] {result.passed}\n"
                f"[bold]Duration:[/bold] {result.response.duration_ms if result.response else 'N/A'}ms",
                border_style="blue" if result.passed else "red"
            )
            self.console.print(panel)
    
    def xǁReporterǁ_print_verbose__mutmut_7(self, results: list[ExecutionResult]) -> None:
        """Print verbose results."""
        for result in results:
            panel = Panel(
                f"[bold]Test:[/bold] {result.test}\n"
                f"[bold]Treatment:[/bold] {result.treatment}\n"
                f"[bold]Passed:[/bold] {result.passed}\n"
                f"[bold]Duration:[/bold] {result.response.duration_ms if result.response else 'N/A'}ms",
                title=f"Result: {result.treatment}/{result.test}",
                )
            self.console.print(panel)
    
    def xǁReporterǁ_print_verbose__mutmut_8(self, results: list[ExecutionResult]) -> None:
        """Print verbose results."""
        for result in results:
            panel = Panel(
                f"[bold]Test:[/bold] {result.test}\n"
                f"[bold]Treatment:[/bold] {result.treatment}\n"
                f"[bold]Passed:[/bold] {result.passed}\n"
                f"[bold]Duration:[/bold] {result.response.duration_ms if result.response else 'XXN/AXX'}ms",
                title=f"Result: {result.treatment}/{result.test}",
                border_style="blue" if result.passed else "red"
            )
            self.console.print(panel)
    
    def xǁReporterǁ_print_verbose__mutmut_9(self, results: list[ExecutionResult]) -> None:
        """Print verbose results."""
        for result in results:
            panel = Panel(
                f"[bold]Test:[/bold] {result.test}\n"
                f"[bold]Treatment:[/bold] {result.treatment}\n"
                f"[bold]Passed:[/bold] {result.passed}\n"
                f"[bold]Duration:[/bold] {result.response.duration_ms if result.response else 'n/a'}ms",
                title=f"Result: {result.treatment}/{result.test}",
                border_style="blue" if result.passed else "red"
            )
            self.console.print(panel)
    
    def xǁReporterǁ_print_verbose__mutmut_10(self, results: list[ExecutionResult]) -> None:
        """Print verbose results."""
        for result in results:
            panel = Panel(
                f"[bold]Test:[/bold] {result.test}\n"
                f"[bold]Treatment:[/bold] {result.treatment}\n"
                f"[bold]Passed:[/bold] {result.passed}\n"
                f"[bold]Duration:[/bold] {result.response.duration_ms if result.response else 'N/A'}ms",
                title=f"Result: {result.treatment}/{result.test}",
                border_style="XXblueXX" if result.passed else "red"
            )
            self.console.print(panel)
    
    def xǁReporterǁ_print_verbose__mutmut_11(self, results: list[ExecutionResult]) -> None:
        """Print verbose results."""
        for result in results:
            panel = Panel(
                f"[bold]Test:[/bold] {result.test}\n"
                f"[bold]Treatment:[/bold] {result.treatment}\n"
                f"[bold]Passed:[/bold] {result.passed}\n"
                f"[bold]Duration:[/bold] {result.response.duration_ms if result.response else 'N/A'}ms",
                title=f"Result: {result.treatment}/{result.test}",
                border_style="BLUE" if result.passed else "red"
            )
            self.console.print(panel)
    
    def xǁReporterǁ_print_verbose__mutmut_12(self, results: list[ExecutionResult]) -> None:
        """Print verbose results."""
        for result in results:
            panel = Panel(
                f"[bold]Test:[/bold] {result.test}\n"
                f"[bold]Treatment:[/bold] {result.treatment}\n"
                f"[bold]Passed:[/bold] {result.passed}\n"
                f"[bold]Duration:[/bold] {result.response.duration_ms if result.response else 'N/A'}ms",
                title=f"Result: {result.treatment}/{result.test}",
                border_style="blue" if result.passed else "XXredXX"
            )
            self.console.print(panel)
    
    def xǁReporterǁ_print_verbose__mutmut_13(self, results: list[ExecutionResult]) -> None:
        """Print verbose results."""
        for result in results:
            panel = Panel(
                f"[bold]Test:[/bold] {result.test}\n"
                f"[bold]Treatment:[/bold] {result.treatment}\n"
                f"[bold]Passed:[/bold] {result.passed}\n"
                f"[bold]Duration:[/bold] {result.response.duration_ms if result.response else 'N/A'}ms",
                title=f"Result: {result.treatment}/{result.test}",
                border_style="blue" if result.passed else "RED"
            )
            self.console.print(panel)
    
    def xǁReporterǁ_print_verbose__mutmut_14(self, results: list[ExecutionResult]) -> None:
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
            self.console.print(None)
    
    xǁReporterǁ_print_verbose__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁReporterǁ_print_verbose__mutmut_1': xǁReporterǁ_print_verbose__mutmut_1, 
        'xǁReporterǁ_print_verbose__mutmut_2': xǁReporterǁ_print_verbose__mutmut_2, 
        'xǁReporterǁ_print_verbose__mutmut_3': xǁReporterǁ_print_verbose__mutmut_3, 
        'xǁReporterǁ_print_verbose__mutmut_4': xǁReporterǁ_print_verbose__mutmut_4, 
        'xǁReporterǁ_print_verbose__mutmut_5': xǁReporterǁ_print_verbose__mutmut_5, 
        'xǁReporterǁ_print_verbose__mutmut_6': xǁReporterǁ_print_verbose__mutmut_6, 
        'xǁReporterǁ_print_verbose__mutmut_7': xǁReporterǁ_print_verbose__mutmut_7, 
        'xǁReporterǁ_print_verbose__mutmut_8': xǁReporterǁ_print_verbose__mutmut_8, 
        'xǁReporterǁ_print_verbose__mutmut_9': xǁReporterǁ_print_verbose__mutmut_9, 
        'xǁReporterǁ_print_verbose__mutmut_10': xǁReporterǁ_print_verbose__mutmut_10, 
        'xǁReporterǁ_print_verbose__mutmut_11': xǁReporterǁ_print_verbose__mutmut_11, 
        'xǁReporterǁ_print_verbose__mutmut_12': xǁReporterǁ_print_verbose__mutmut_12, 
        'xǁReporterǁ_print_verbose__mutmut_13': xǁReporterǁ_print_verbose__mutmut_13, 
        'xǁReporterǁ_print_verbose__mutmut_14': xǁReporterǁ_print_verbose__mutmut_14
    }
    xǁReporterǁ_print_verbose__mutmut_orig.__name__ = 'xǁReporterǁ_print_verbose'
    
    def report_json(
        self,
        results: list[ExecutionResult],
        output_path: str
    ) -> None:
        args = [results, output_path]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁReporterǁreport_json__mutmut_orig'), object.__getattribute__(self, 'xǁReporterǁreport_json__mutmut_mutants'), args, kwargs, self)
    
    def xǁReporterǁreport_json__mutmut_orig(
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
    
    def xǁReporterǁreport_json__mutmut_1(
        self,
        results: list[ExecutionResult],
        output_path: str
    ) -> None:
        """Save results as JSON.
        
        Args:
            results: List of execution results
            output_path: Path to save JSON
        """
        output_data = None
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, default=str)
    
    def xǁReporterǁreport_json__mutmut_2(
        self,
        results: list[ExecutionResult],
        output_path: str
    ) -> None:
        """Save results as JSON.
        
        Args:
            results: List of execution results
            output_path: Path to save JSON
        """
        output_data = self._build_output_data(None)
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, default=str)
    
    def xǁReporterǁreport_json__mutmut_3(
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
        
        Path(output_path).parent.mkdir(parents=None, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, default=str)
    
    def xǁReporterǁreport_json__mutmut_4(
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
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=None)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, default=str)
    
    def xǁReporterǁreport_json__mutmut_5(
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
        
        Path(output_path).parent.mkdir(exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, default=str)
    
    def xǁReporterǁreport_json__mutmut_6(
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
        
        Path(output_path).parent.mkdir(parents=True, )
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, default=str)
    
    def xǁReporterǁreport_json__mutmut_7(
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
        
        Path(None).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, default=str)
    
    def xǁReporterǁreport_json__mutmut_8(
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
        
        Path(output_path).parent.mkdir(parents=False, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, default=str)
    
    def xǁReporterǁreport_json__mutmut_9(
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
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=False)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, default=str)
    
    def xǁReporterǁreport_json__mutmut_10(
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
        
        with open(None, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, default=str)
    
    def xǁReporterǁreport_json__mutmut_11(
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
        
        with open(output_path, None, encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, default=str)
    
    def xǁReporterǁreport_json__mutmut_12(
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
        
        with open(output_path, "w", encoding=None) as f:
            json.dump(output_data, f, indent=2, default=str)
    
    def xǁReporterǁreport_json__mutmut_13(
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
        
        with open("w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, default=str)
    
    def xǁReporterǁreport_json__mutmut_14(
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
        
        with open(output_path, encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, default=str)
    
    def xǁReporterǁreport_json__mutmut_15(
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
        
        with open(output_path, "w", ) as f:
            json.dump(output_data, f, indent=2, default=str)
    
    def xǁReporterǁreport_json__mutmut_16(
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
        
        with open(output_path, "XXwXX", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, default=str)
    
    def xǁReporterǁreport_json__mutmut_17(
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
        
        with open(output_path, "W", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, default=str)
    
    def xǁReporterǁreport_json__mutmut_18(
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
        
        with open(output_path, "w", encoding="XXutf-8XX") as f:
            json.dump(output_data, f, indent=2, default=str)
    
    def xǁReporterǁreport_json__mutmut_19(
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
        
        with open(output_path, "w", encoding="UTF-8") as f:
            json.dump(output_data, f, indent=2, default=str)
    
    def xǁReporterǁreport_json__mutmut_20(
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
            json.dump(None, f, indent=2, default=str)
    
    def xǁReporterǁreport_json__mutmut_21(
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
            json.dump(output_data, None, indent=2, default=str)
    
    def xǁReporterǁreport_json__mutmut_22(
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
            json.dump(output_data, f, indent=None, default=str)
    
    def xǁReporterǁreport_json__mutmut_23(
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
            json.dump(output_data, f, indent=2, default=None)
    
    def xǁReporterǁreport_json__mutmut_24(
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
            json.dump(f, indent=2, default=str)
    
    def xǁReporterǁreport_json__mutmut_25(
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
            json.dump(output_data, indent=2, default=str)
    
    def xǁReporterǁreport_json__mutmut_26(
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
            json.dump(output_data, f, default=str)
    
    def xǁReporterǁreport_json__mutmut_27(
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
            json.dump(output_data, f, indent=2, )
    
    def xǁReporterǁreport_json__mutmut_28(
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
            json.dump(output_data, f, indent=3, default=str)
    
    xǁReporterǁreport_json__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁReporterǁreport_json__mutmut_1': xǁReporterǁreport_json__mutmut_1, 
        'xǁReporterǁreport_json__mutmut_2': xǁReporterǁreport_json__mutmut_2, 
        'xǁReporterǁreport_json__mutmut_3': xǁReporterǁreport_json__mutmut_3, 
        'xǁReporterǁreport_json__mutmut_4': xǁReporterǁreport_json__mutmut_4, 
        'xǁReporterǁreport_json__mutmut_5': xǁReporterǁreport_json__mutmut_5, 
        'xǁReporterǁreport_json__mutmut_6': xǁReporterǁreport_json__mutmut_6, 
        'xǁReporterǁreport_json__mutmut_7': xǁReporterǁreport_json__mutmut_7, 
        'xǁReporterǁreport_json__mutmut_8': xǁReporterǁreport_json__mutmut_8, 
        'xǁReporterǁreport_json__mutmut_9': xǁReporterǁreport_json__mutmut_9, 
        'xǁReporterǁreport_json__mutmut_10': xǁReporterǁreport_json__mutmut_10, 
        'xǁReporterǁreport_json__mutmut_11': xǁReporterǁreport_json__mutmut_11, 
        'xǁReporterǁreport_json__mutmut_12': xǁReporterǁreport_json__mutmut_12, 
        'xǁReporterǁreport_json__mutmut_13': xǁReporterǁreport_json__mutmut_13, 
        'xǁReporterǁreport_json__mutmut_14': xǁReporterǁreport_json__mutmut_14, 
        'xǁReporterǁreport_json__mutmut_15': xǁReporterǁreport_json__mutmut_15, 
        'xǁReporterǁreport_json__mutmut_16': xǁReporterǁreport_json__mutmut_16, 
        'xǁReporterǁreport_json__mutmut_17': xǁReporterǁreport_json__mutmut_17, 
        'xǁReporterǁreport_json__mutmut_18': xǁReporterǁreport_json__mutmut_18, 
        'xǁReporterǁreport_json__mutmut_19': xǁReporterǁreport_json__mutmut_19, 
        'xǁReporterǁreport_json__mutmut_20': xǁReporterǁreport_json__mutmut_20, 
        'xǁReporterǁreport_json__mutmut_21': xǁReporterǁreport_json__mutmut_21, 
        'xǁReporterǁreport_json__mutmut_22': xǁReporterǁreport_json__mutmut_22, 
        'xǁReporterǁreport_json__mutmut_23': xǁReporterǁreport_json__mutmut_23, 
        'xǁReporterǁreport_json__mutmut_24': xǁReporterǁreport_json__mutmut_24, 
        'xǁReporterǁreport_json__mutmut_25': xǁReporterǁreport_json__mutmut_25, 
        'xǁReporterǁreport_json__mutmut_26': xǁReporterǁreport_json__mutmut_26, 
        'xǁReporterǁreport_json__mutmut_27': xǁReporterǁreport_json__mutmut_27, 
        'xǁReporterǁreport_json__mutmut_28': xǁReporterǁreport_json__mutmut_28
    }
    xǁReporterǁreport_json__mutmut_orig.__name__ = 'xǁReporterǁreport_json'
    
    def report_markdown(
        self,
        results: list[ExecutionResult],
        output_path: str
    ) -> None:
        args = [results, output_path]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁReporterǁreport_markdown__mutmut_orig'), object.__getattribute__(self, 'xǁReporterǁreport_markdown__mutmut_mutants'), args, kwargs, self)
    
    def xǁReporterǁreport_markdown__mutmut_orig(
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
    
    def xǁReporterǁreport_markdown__mutmut_1(
        self,
        results: list[ExecutionResult],
        output_path: str
    ) -> None:
        """Save results as Markdown.
        
        Args:
            results: List of execution results
            output_path: Path to save Markdown
        """
        md_content = None
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md_content)
    
    def xǁReporterǁreport_markdown__mutmut_2(
        self,
        results: list[ExecutionResult],
        output_path: str
    ) -> None:
        """Save results as Markdown.
        
        Args:
            results: List of execution results
            output_path: Path to save Markdown
        """
        md_content = self._build_markdown(None)
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md_content)
    
    def xǁReporterǁreport_markdown__mutmut_3(
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
        
        Path(output_path).parent.mkdir(parents=None, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md_content)
    
    def xǁReporterǁreport_markdown__mutmut_4(
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
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=None)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md_content)
    
    def xǁReporterǁreport_markdown__mutmut_5(
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
        
        Path(output_path).parent.mkdir(exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md_content)
    
    def xǁReporterǁreport_markdown__mutmut_6(
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
        
        Path(output_path).parent.mkdir(parents=True, )
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md_content)
    
    def xǁReporterǁreport_markdown__mutmut_7(
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
        
        Path(None).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md_content)
    
    def xǁReporterǁreport_markdown__mutmut_8(
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
        
        Path(output_path).parent.mkdir(parents=False, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md_content)
    
    def xǁReporterǁreport_markdown__mutmut_9(
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
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=False)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md_content)
    
    def xǁReporterǁreport_markdown__mutmut_10(
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
        
        with open(None, "w", encoding="utf-8") as f:
            f.write(md_content)
    
    def xǁReporterǁreport_markdown__mutmut_11(
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
        
        with open(output_path, None, encoding="utf-8") as f:
            f.write(md_content)
    
    def xǁReporterǁreport_markdown__mutmut_12(
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
        
        with open(output_path, "w", encoding=None) as f:
            f.write(md_content)
    
    def xǁReporterǁreport_markdown__mutmut_13(
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
        
        with open("w", encoding="utf-8") as f:
            f.write(md_content)
    
    def xǁReporterǁreport_markdown__mutmut_14(
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
        
        with open(output_path, encoding="utf-8") as f:
            f.write(md_content)
    
    def xǁReporterǁreport_markdown__mutmut_15(
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
        
        with open(output_path, "w", ) as f:
            f.write(md_content)
    
    def xǁReporterǁreport_markdown__mutmut_16(
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
        
        with open(output_path, "XXwXX", encoding="utf-8") as f:
            f.write(md_content)
    
    def xǁReporterǁreport_markdown__mutmut_17(
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
        
        with open(output_path, "W", encoding="utf-8") as f:
            f.write(md_content)
    
    def xǁReporterǁreport_markdown__mutmut_18(
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
        
        with open(output_path, "w", encoding="XXutf-8XX") as f:
            f.write(md_content)
    
    def xǁReporterǁreport_markdown__mutmut_19(
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
        
        with open(output_path, "w", encoding="UTF-8") as f:
            f.write(md_content)
    
    def xǁReporterǁreport_markdown__mutmut_20(
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
            f.write(None)
    
    xǁReporterǁreport_markdown__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁReporterǁreport_markdown__mutmut_1': xǁReporterǁreport_markdown__mutmut_1, 
        'xǁReporterǁreport_markdown__mutmut_2': xǁReporterǁreport_markdown__mutmut_2, 
        'xǁReporterǁreport_markdown__mutmut_3': xǁReporterǁreport_markdown__mutmut_3, 
        'xǁReporterǁreport_markdown__mutmut_4': xǁReporterǁreport_markdown__mutmut_4, 
        'xǁReporterǁreport_markdown__mutmut_5': xǁReporterǁreport_markdown__mutmut_5, 
        'xǁReporterǁreport_markdown__mutmut_6': xǁReporterǁreport_markdown__mutmut_6, 
        'xǁReporterǁreport_markdown__mutmut_7': xǁReporterǁreport_markdown__mutmut_7, 
        'xǁReporterǁreport_markdown__mutmut_8': xǁReporterǁreport_markdown__mutmut_8, 
        'xǁReporterǁreport_markdown__mutmut_9': xǁReporterǁreport_markdown__mutmut_9, 
        'xǁReporterǁreport_markdown__mutmut_10': xǁReporterǁreport_markdown__mutmut_10, 
        'xǁReporterǁreport_markdown__mutmut_11': xǁReporterǁreport_markdown__mutmut_11, 
        'xǁReporterǁreport_markdown__mutmut_12': xǁReporterǁreport_markdown__mutmut_12, 
        'xǁReporterǁreport_markdown__mutmut_13': xǁReporterǁreport_markdown__mutmut_13, 
        'xǁReporterǁreport_markdown__mutmut_14': xǁReporterǁreport_markdown__mutmut_14, 
        'xǁReporterǁreport_markdown__mutmut_15': xǁReporterǁreport_markdown__mutmut_15, 
        'xǁReporterǁreport_markdown__mutmut_16': xǁReporterǁreport_markdown__mutmut_16, 
        'xǁReporterǁreport_markdown__mutmut_17': xǁReporterǁreport_markdown__mutmut_17, 
        'xǁReporterǁreport_markdown__mutmut_18': xǁReporterǁreport_markdown__mutmut_18, 
        'xǁReporterǁreport_markdown__mutmut_19': xǁReporterǁreport_markdown__mutmut_19, 
        'xǁReporterǁreport_markdown__mutmut_20': xǁReporterǁreport_markdown__mutmut_20
    }
    xǁReporterǁreport_markdown__mutmut_orig.__name__ = 'xǁReporterǁreport_markdown'
    
    def _build_output_data(
        self,
        results: list[ExecutionResult]
    ) -> dict[str, Any]:
        args = [results]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁReporterǁ_build_output_data__mutmut_orig'), object.__getattribute__(self, 'xǁReporterǁ_build_output_data__mutmut_mutants'), args, kwargs, self)
    
    def xǁReporterǁ_build_output_data__mutmut_orig(
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
    
    def xǁReporterǁ_build_output_data__mutmut_1(
        self,
        results: list[ExecutionResult]
    ) -> dict[str, Any]:
        """Build output data structure."""
        # Group by treatment
        by_treatment: dict[str, list[ExecutionResult]] = None
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
    
    def xǁReporterǁ_build_output_data__mutmut_2(
        self,
        results: list[ExecutionResult]
    ) -> dict[str, Any]:
        """Build output data structure."""
        # Group by treatment
        by_treatment: dict[str, list[ExecutionResult]] = {}
        for result in results:
            if result.treatment in by_treatment:
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
    
    def xǁReporterǁ_build_output_data__mutmut_3(
        self,
        results: list[ExecutionResult]
    ) -> dict[str, Any]:
        """Build output data structure."""
        # Group by treatment
        by_treatment: dict[str, list[ExecutionResult]] = {}
        for result in results:
            if result.treatment not in by_treatment:
                by_treatment[result.treatment] = None
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
    
    def xǁReporterǁ_build_output_data__mutmut_4(
        self,
        results: list[ExecutionResult]
    ) -> dict[str, Any]:
        """Build output data structure."""
        # Group by treatment
        by_treatment: dict[str, list[ExecutionResult]] = {}
        for result in results:
            if result.treatment not in by_treatment:
                by_treatment[result.treatment] = []
            by_treatment[result.treatment].append(None)
        
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
    
    def xǁReporterǁ_build_output_data__mutmut_5(
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
        summary = None
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
    
    def xǁReporterǁ_build_output_data__mutmut_6(
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
            total = None
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
    
    def xǁReporterǁ_build_output_data__mutmut_7(
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
            passed = None
            
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
    
    def xǁReporterǁ_build_output_data__mutmut_8(
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
            passed = sum(None)
            
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
    
    def xǁReporterǁ_build_output_data__mutmut_9(
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
            passed = sum(2 for r in treatment_results if r.passed)
            
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
    
    def xǁReporterǁ_build_output_data__mutmut_10(
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
            
            summary[treatment] = None
        
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
    
    def xǁReporterǁ_build_output_data__mutmut_11(
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
                "XXtotalXX": total,
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
    
    def xǁReporterǁ_build_output_data__mutmut_12(
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
                "TOTAL": total,
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
    
    def xǁReporterǁ_build_output_data__mutmut_13(
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
                "XXpassedXX": passed,
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
    
    def xǁReporterǁ_build_output_data__mutmut_14(
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
                "PASSED": passed,
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
    
    def xǁReporterǁ_build_output_data__mutmut_15(
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
                "XXpass_rateXX": passed / total if total > 0 else 0
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
    
    def xǁReporterǁ_build_output_data__mutmut_16(
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
                "PASS_RATE": passed / total if total > 0 else 0
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
    
    def xǁReporterǁ_build_output_data__mutmut_17(
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
                "pass_rate": passed * total if total > 0 else 0
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
    
    def xǁReporterǁ_build_output_data__mutmut_18(
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
                "pass_rate": passed / total if total >= 0 else 0
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
    
    def xǁReporterǁ_build_output_data__mutmut_19(
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
                "pass_rate": passed / total if total > 1 else 0
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
    
    def xǁReporterǁ_build_output_data__mutmut_20(
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
                "pass_rate": passed / total if total > 0 else 1
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
    
    def xǁReporterǁ_build_output_data__mutmut_21(
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
            "XXexperiment_idXX": f"eval_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
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
    
    def xǁReporterǁ_build_output_data__mutmut_22(
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
            "EXPERIMENT_ID": f"eval_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
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
    
    def xǁReporterǁ_build_output_data__mutmut_23(
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
            "experiment_id": f"eval_{datetime.utcnow().strftime(None)}",
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
    
    def xǁReporterǁ_build_output_data__mutmut_24(
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
            "experiment_id": f"eval_{datetime.utcnow().strftime('XX%Y%m%d_%H%M%SXX')}",
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
    
    def xǁReporterǁ_build_output_data__mutmut_25(
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
            "experiment_id": f"eval_{datetime.utcnow().strftime('%y%m%d_%h%m%s')}",
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
    
    def xǁReporterǁ_build_output_data__mutmut_26(
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
            "experiment_id": f"eval_{datetime.utcnow().strftime('%Y%M%D_%H%M%S')}",
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
    
    def xǁReporterǁ_build_output_data__mutmut_27(
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
            "XXtimestampXX": datetime.utcnow().isoformat(),
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
    
    def xǁReporterǁ_build_output_data__mutmut_28(
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
            "TIMESTAMP": datetime.utcnow().isoformat(),
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
    
    def xǁReporterǁ_build_output_data__mutmut_29(
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
            "XXconfigXX": {
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
    
    def xǁReporterǁ_build_output_data__mutmut_30(
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
            "CONFIG": {
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
    
    def xǁReporterǁ_build_output_data__mutmut_31(
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
                "XXnameXX": self.config.name,
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
    
    def xǁReporterǁ_build_output_data__mutmut_32(
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
                "NAME": self.config.name,
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
    
    def xǁReporterǁ_build_output_data__mutmut_33(
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
                "XXversionXX": self.config.version
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
    
    def xǁReporterǁ_build_output_data__mutmut_34(
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
                "VERSION": self.config.version
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
    
    def xǁReporterǁ_build_output_data__mutmut_35(
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
            "XXresultsXX": [
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
    
    def xǁReporterǁ_build_output_data__mutmut_36(
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
            "RESULTS": [
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
    
    def xǁReporterǁ_build_output_data__mutmut_37(
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
                    "XXtreatmentXX": r.treatment,
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
    
    def xǁReporterǁ_build_output_data__mutmut_38(
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
                    "TREATMENT": r.treatment,
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
    
    def xǁReporterǁ_build_output_data__mutmut_39(
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
                    "XXtestXX": r.test,
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
    
    def xǁReporterǁ_build_output_data__mutmut_40(
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
                    "TEST": r.test,
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
    
    def xǁReporterǁ_build_output_data__mutmut_41(
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
                    "XXpromptXX": r.prompt,
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
    
    def xǁReporterǁ_build_output_data__mutmut_42(
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
                    "PROMPT": r.prompt,
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
    
    def xǁReporterǁ_build_output_data__mutmut_43(
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
                    "XXresponseXX": r.response.content if r.response else None,
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
    
    def xǁReporterǁ_build_output_data__mutmut_44(
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
                    "RESPONSE": r.response.content if r.response else None,
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
    
    def xǁReporterǁ_build_output_data__mutmut_45(
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
                    "XXpassedXX": r.passed,
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
    
    def xǁReporterǁ_build_output_data__mutmut_46(
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
                    "PASSED": r.passed,
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
    
    def xǁReporterǁ_build_output_data__mutmut_47(
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
                    "XXevaluatorsXX": [
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
    
    def xǁReporterǁ_build_output_data__mutmut_48(
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
                    "EVALUATORS": [
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
    
    def xǁReporterǁ_build_output_data__mutmut_49(
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
                            "XXnameXX": e.evaluator_name,
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
    
    def xǁReporterǁ_build_output_data__mutmut_50(
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
                            "NAME": e.evaluator_name,
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
    
    def xǁReporterǁ_build_output_data__mutmut_51(
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
                            "XXpassedXX": e.passed,
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
    
    def xǁReporterǁ_build_output_data__mutmut_52(
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
                            "PASSED": e.passed,
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
    
    def xǁReporterǁ_build_output_data__mutmut_53(
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
                            "XXscoreXX": e.score,
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
    
    def xǁReporterǁ_build_output_data__mutmut_54(
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
                            "SCORE": e.score,
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
    
    def xǁReporterǁ_build_output_data__mutmut_55(
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
                            "XXreasonXX": e.reason
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
    
    def xǁReporterǁ_build_output_data__mutmut_56(
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
                            "REASON": e.reason
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
    
    def xǁReporterǁ_build_output_data__mutmut_57(
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
                    "XXtokensXX": r.response.tokens if r.response else None,
                    "duration_ms": r.response.duration_ms if r.response else None,
                    "timestamp": r.timestamp
                }
                for r in results
            ],
            "summary": summary
        }
    
    def xǁReporterǁ_build_output_data__mutmut_58(
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
                    "TOKENS": r.response.tokens if r.response else None,
                    "duration_ms": r.response.duration_ms if r.response else None,
                    "timestamp": r.timestamp
                }
                for r in results
            ],
            "summary": summary
        }
    
    def xǁReporterǁ_build_output_data__mutmut_59(
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
                    "XXduration_msXX": r.response.duration_ms if r.response else None,
                    "timestamp": r.timestamp
                }
                for r in results
            ],
            "summary": summary
        }
    
    def xǁReporterǁ_build_output_data__mutmut_60(
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
                    "DURATION_MS": r.response.duration_ms if r.response else None,
                    "timestamp": r.timestamp
                }
                for r in results
            ],
            "summary": summary
        }
    
    def xǁReporterǁ_build_output_data__mutmut_61(
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
                    "XXtimestampXX": r.timestamp
                }
                for r in results
            ],
            "summary": summary
        }
    
    def xǁReporterǁ_build_output_data__mutmut_62(
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
                    "TIMESTAMP": r.timestamp
                }
                for r in results
            ],
            "summary": summary
        }
    
    def xǁReporterǁ_build_output_data__mutmut_63(
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
            "XXsummaryXX": summary
        }
    
    def xǁReporterǁ_build_output_data__mutmut_64(
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
            "SUMMARY": summary
        }
    
    xǁReporterǁ_build_output_data__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁReporterǁ_build_output_data__mutmut_1': xǁReporterǁ_build_output_data__mutmut_1, 
        'xǁReporterǁ_build_output_data__mutmut_2': xǁReporterǁ_build_output_data__mutmut_2, 
        'xǁReporterǁ_build_output_data__mutmut_3': xǁReporterǁ_build_output_data__mutmut_3, 
        'xǁReporterǁ_build_output_data__mutmut_4': xǁReporterǁ_build_output_data__mutmut_4, 
        'xǁReporterǁ_build_output_data__mutmut_5': xǁReporterǁ_build_output_data__mutmut_5, 
        'xǁReporterǁ_build_output_data__mutmut_6': xǁReporterǁ_build_output_data__mutmut_6, 
        'xǁReporterǁ_build_output_data__mutmut_7': xǁReporterǁ_build_output_data__mutmut_7, 
        'xǁReporterǁ_build_output_data__mutmut_8': xǁReporterǁ_build_output_data__mutmut_8, 
        'xǁReporterǁ_build_output_data__mutmut_9': xǁReporterǁ_build_output_data__mutmut_9, 
        'xǁReporterǁ_build_output_data__mutmut_10': xǁReporterǁ_build_output_data__mutmut_10, 
        'xǁReporterǁ_build_output_data__mutmut_11': xǁReporterǁ_build_output_data__mutmut_11, 
        'xǁReporterǁ_build_output_data__mutmut_12': xǁReporterǁ_build_output_data__mutmut_12, 
        'xǁReporterǁ_build_output_data__mutmut_13': xǁReporterǁ_build_output_data__mutmut_13, 
        'xǁReporterǁ_build_output_data__mutmut_14': xǁReporterǁ_build_output_data__mutmut_14, 
        'xǁReporterǁ_build_output_data__mutmut_15': xǁReporterǁ_build_output_data__mutmut_15, 
        'xǁReporterǁ_build_output_data__mutmut_16': xǁReporterǁ_build_output_data__mutmut_16, 
        'xǁReporterǁ_build_output_data__mutmut_17': xǁReporterǁ_build_output_data__mutmut_17, 
        'xǁReporterǁ_build_output_data__mutmut_18': xǁReporterǁ_build_output_data__mutmut_18, 
        'xǁReporterǁ_build_output_data__mutmut_19': xǁReporterǁ_build_output_data__mutmut_19, 
        'xǁReporterǁ_build_output_data__mutmut_20': xǁReporterǁ_build_output_data__mutmut_20, 
        'xǁReporterǁ_build_output_data__mutmut_21': xǁReporterǁ_build_output_data__mutmut_21, 
        'xǁReporterǁ_build_output_data__mutmut_22': xǁReporterǁ_build_output_data__mutmut_22, 
        'xǁReporterǁ_build_output_data__mutmut_23': xǁReporterǁ_build_output_data__mutmut_23, 
        'xǁReporterǁ_build_output_data__mutmut_24': xǁReporterǁ_build_output_data__mutmut_24, 
        'xǁReporterǁ_build_output_data__mutmut_25': xǁReporterǁ_build_output_data__mutmut_25, 
        'xǁReporterǁ_build_output_data__mutmut_26': xǁReporterǁ_build_output_data__mutmut_26, 
        'xǁReporterǁ_build_output_data__mutmut_27': xǁReporterǁ_build_output_data__mutmut_27, 
        'xǁReporterǁ_build_output_data__mutmut_28': xǁReporterǁ_build_output_data__mutmut_28, 
        'xǁReporterǁ_build_output_data__mutmut_29': xǁReporterǁ_build_output_data__mutmut_29, 
        'xǁReporterǁ_build_output_data__mutmut_30': xǁReporterǁ_build_output_data__mutmut_30, 
        'xǁReporterǁ_build_output_data__mutmut_31': xǁReporterǁ_build_output_data__mutmut_31, 
        'xǁReporterǁ_build_output_data__mutmut_32': xǁReporterǁ_build_output_data__mutmut_32, 
        'xǁReporterǁ_build_output_data__mutmut_33': xǁReporterǁ_build_output_data__mutmut_33, 
        'xǁReporterǁ_build_output_data__mutmut_34': xǁReporterǁ_build_output_data__mutmut_34, 
        'xǁReporterǁ_build_output_data__mutmut_35': xǁReporterǁ_build_output_data__mutmut_35, 
        'xǁReporterǁ_build_output_data__mutmut_36': xǁReporterǁ_build_output_data__mutmut_36, 
        'xǁReporterǁ_build_output_data__mutmut_37': xǁReporterǁ_build_output_data__mutmut_37, 
        'xǁReporterǁ_build_output_data__mutmut_38': xǁReporterǁ_build_output_data__mutmut_38, 
        'xǁReporterǁ_build_output_data__mutmut_39': xǁReporterǁ_build_output_data__mutmut_39, 
        'xǁReporterǁ_build_output_data__mutmut_40': xǁReporterǁ_build_output_data__mutmut_40, 
        'xǁReporterǁ_build_output_data__mutmut_41': xǁReporterǁ_build_output_data__mutmut_41, 
        'xǁReporterǁ_build_output_data__mutmut_42': xǁReporterǁ_build_output_data__mutmut_42, 
        'xǁReporterǁ_build_output_data__mutmut_43': xǁReporterǁ_build_output_data__mutmut_43, 
        'xǁReporterǁ_build_output_data__mutmut_44': xǁReporterǁ_build_output_data__mutmut_44, 
        'xǁReporterǁ_build_output_data__mutmut_45': xǁReporterǁ_build_output_data__mutmut_45, 
        'xǁReporterǁ_build_output_data__mutmut_46': xǁReporterǁ_build_output_data__mutmut_46, 
        'xǁReporterǁ_build_output_data__mutmut_47': xǁReporterǁ_build_output_data__mutmut_47, 
        'xǁReporterǁ_build_output_data__mutmut_48': xǁReporterǁ_build_output_data__mutmut_48, 
        'xǁReporterǁ_build_output_data__mutmut_49': xǁReporterǁ_build_output_data__mutmut_49, 
        'xǁReporterǁ_build_output_data__mutmut_50': xǁReporterǁ_build_output_data__mutmut_50, 
        'xǁReporterǁ_build_output_data__mutmut_51': xǁReporterǁ_build_output_data__mutmut_51, 
        'xǁReporterǁ_build_output_data__mutmut_52': xǁReporterǁ_build_output_data__mutmut_52, 
        'xǁReporterǁ_build_output_data__mutmut_53': xǁReporterǁ_build_output_data__mutmut_53, 
        'xǁReporterǁ_build_output_data__mutmut_54': xǁReporterǁ_build_output_data__mutmut_54, 
        'xǁReporterǁ_build_output_data__mutmut_55': xǁReporterǁ_build_output_data__mutmut_55, 
        'xǁReporterǁ_build_output_data__mutmut_56': xǁReporterǁ_build_output_data__mutmut_56, 
        'xǁReporterǁ_build_output_data__mutmut_57': xǁReporterǁ_build_output_data__mutmut_57, 
        'xǁReporterǁ_build_output_data__mutmut_58': xǁReporterǁ_build_output_data__mutmut_58, 
        'xǁReporterǁ_build_output_data__mutmut_59': xǁReporterǁ_build_output_data__mutmut_59, 
        'xǁReporterǁ_build_output_data__mutmut_60': xǁReporterǁ_build_output_data__mutmut_60, 
        'xǁReporterǁ_build_output_data__mutmut_61': xǁReporterǁ_build_output_data__mutmut_61, 
        'xǁReporterǁ_build_output_data__mutmut_62': xǁReporterǁ_build_output_data__mutmut_62, 
        'xǁReporterǁ_build_output_data__mutmut_63': xǁReporterǁ_build_output_data__mutmut_63, 
        'xǁReporterǁ_build_output_data__mutmut_64': xǁReporterǁ_build_output_data__mutmut_64
    }
    xǁReporterǁ_build_output_data__mutmut_orig.__name__ = 'xǁReporterǁ_build_output_data'
    
    def _build_markdown(self, results: list[ExecutionResult]) -> str:
        args = [results]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁReporterǁ_build_markdown__mutmut_orig'), object.__getattribute__(self, 'xǁReporterǁ_build_markdown__mutmut_mutants'), args, kwargs, self)
    
    def xǁReporterǁ_build_markdown__mutmut_orig(self, results: list[ExecutionResult]) -> str:
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
    
    def xǁReporterǁ_build_markdown__mutmut_1(self, results: list[ExecutionResult]) -> str:
        """Build Markdown report."""
        md_lines = None
        
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
    
    def xǁReporterǁ_build_markdown__mutmut_2(self, results: list[ExecutionResult]) -> str:
        """Build Markdown report."""
        md_lines = [
            "XX# md-evals ResultsXX",
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
    
    def xǁReporterǁ_build_markdown__mutmut_3(self, results: list[ExecutionResult]) -> str:
        """Build Markdown report."""
        md_lines = [
            "# md-evals results",
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
    
    def xǁReporterǁ_build_markdown__mutmut_4(self, results: list[ExecutionResult]) -> str:
        """Build Markdown report."""
        md_lines = [
            "# MD-EVALS RESULTS",
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
    
    def xǁReporterǁ_build_markdown__mutmut_5(self, results: list[ExecutionResult]) -> str:
        """Build Markdown report."""
        md_lines = [
            "# md-evals Results",
            "XXXX",
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
    
    def xǁReporterǁ_build_markdown__mutmut_6(self, results: list[ExecutionResult]) -> str:
        """Build Markdown report."""
        md_lines = [
            "# md-evals Results",
            "",
            f"**Generated:** {datetime.utcnow().isoformat()}",
            f"**Config:** {self.config.name} (v{self.config.version})",
            "XXXX",
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
    
    def xǁReporterǁ_build_markdown__mutmut_7(self, results: list[ExecutionResult]) -> str:
        """Build Markdown report."""
        md_lines = [
            "# md-evals Results",
            "",
            f"**Generated:** {datetime.utcnow().isoformat()}",
            f"**Config:** {self.config.name} (v{self.config.version})",
            "",
            "XX## SummaryXX",
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
    
    def xǁReporterǁ_build_markdown__mutmut_8(self, results: list[ExecutionResult]) -> str:
        """Build Markdown report."""
        md_lines = [
            "# md-evals Results",
            "",
            f"**Generated:** {datetime.utcnow().isoformat()}",
            f"**Config:** {self.config.name} (v{self.config.version})",
            "",
            "## summary",
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
    
    def xǁReporterǁ_build_markdown__mutmut_9(self, results: list[ExecutionResult]) -> str:
        """Build Markdown report."""
        md_lines = [
            "# md-evals Results",
            "",
            f"**Generated:** {datetime.utcnow().isoformat()}",
            f"**Config:** {self.config.name} (v{self.config.version})",
            "",
            "## SUMMARY",
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
    
    def xǁReporterǁ_build_markdown__mutmut_10(self, results: list[ExecutionResult]) -> str:
        """Build Markdown report."""
        md_lines = [
            "# md-evals Results",
            "",
            f"**Generated:** {datetime.utcnow().isoformat()}",
            f"**Config:** {self.config.name} (v{self.config.version})",
            "",
            "## Summary",
            "XXXX",
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
    
    def xǁReporterǁ_build_markdown__mutmut_11(self, results: list[ExecutionResult]) -> str:
        """Build Markdown report."""
        md_lines = [
            "# md-evals Results",
            "",
            f"**Generated:** {datetime.utcnow().isoformat()}",
            f"**Config:** {self.config.name} (v{self.config.version})",
            "",
            "## Summary",
            "",
            "XX| Treatment | Tests | Passed | Pass Rate |XX",
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
    
    def xǁReporterǁ_build_markdown__mutmut_12(self, results: list[ExecutionResult]) -> str:
        """Build Markdown report."""
        md_lines = [
            "# md-evals Results",
            "",
            f"**Generated:** {datetime.utcnow().isoformat()}",
            f"**Config:** {self.config.name} (v{self.config.version})",
            "",
            "## Summary",
            "",
            "| treatment | tests | passed | pass rate |",
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
    
    def xǁReporterǁ_build_markdown__mutmut_13(self, results: list[ExecutionResult]) -> str:
        """Build Markdown report."""
        md_lines = [
            "# md-evals Results",
            "",
            f"**Generated:** {datetime.utcnow().isoformat()}",
            f"**Config:** {self.config.name} (v{self.config.version})",
            "",
            "## Summary",
            "",
            "| TREATMENT | TESTS | PASSED | PASS RATE |",
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
    
    def xǁReporterǁ_build_markdown__mutmut_14(self, results: list[ExecutionResult]) -> str:
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
            "XX|-----------|-------|--------|-----------|XX"
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
    
    def xǁReporterǁ_build_markdown__mutmut_15(self, results: list[ExecutionResult]) -> str:
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
        by_treatment: dict[str, list[ExecutionResult]] = None
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
    
    def xǁReporterǁ_build_markdown__mutmut_16(self, results: list[ExecutionResult]) -> str:
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
            if result.treatment in by_treatment:
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
    
    def xǁReporterǁ_build_markdown__mutmut_17(self, results: list[ExecutionResult]) -> str:
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
                by_treatment[result.treatment] = None
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
    
    def xǁReporterǁ_build_markdown__mutmut_18(self, results: list[ExecutionResult]) -> str:
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
            by_treatment[result.treatment].append(None)
        
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
    
    def xǁReporterǁ_build_markdown__mutmut_19(self, results: list[ExecutionResult]) -> str:
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
            total = None
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
    
    def xǁReporterǁ_build_markdown__mutmut_20(self, results: list[ExecutionResult]) -> str:
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
            passed = None
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
    
    def xǁReporterǁ_build_markdown__mutmut_21(self, results: list[ExecutionResult]) -> str:
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
            passed = sum(None)
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
    
    def xǁReporterǁ_build_markdown__mutmut_22(self, results: list[ExecutionResult]) -> str:
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
            passed = sum(2 for r in treatment_results if r.passed)
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
    
    def xǁReporterǁ_build_markdown__mutmut_23(self, results: list[ExecutionResult]) -> str:
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
            rate = None
            
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
    
    def xǁReporterǁ_build_markdown__mutmut_24(self, results: list[ExecutionResult]) -> str:
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
            rate = passed / total / 100 if total > 0 else 0
            
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
    
    def xǁReporterǁ_build_markdown__mutmut_25(self, results: list[ExecutionResult]) -> str:
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
            rate = passed * total * 100 if total > 0 else 0
            
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
    
    def xǁReporterǁ_build_markdown__mutmut_26(self, results: list[ExecutionResult]) -> str:
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
            rate = passed / total * 101 if total > 0 else 0
            
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
    
    def xǁReporterǁ_build_markdown__mutmut_27(self, results: list[ExecutionResult]) -> str:
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
            rate = passed / total * 100 if total >= 0 else 0
            
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
    
    def xǁReporterǁ_build_markdown__mutmut_28(self, results: list[ExecutionResult]) -> str:
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
            rate = passed / total * 100 if total > 1 else 0
            
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
    
    def xǁReporterǁ_build_markdown__mutmut_29(self, results: list[ExecutionResult]) -> str:
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
            rate = passed / total * 100 if total > 0 else 1
            
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
    
    def xǁReporterǁ_build_markdown__mutmut_30(self, results: list[ExecutionResult]) -> str:
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
            
            md_lines.append(None)
        
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
    
    def xǁReporterǁ_build_markdown__mutmut_31(self, results: list[ExecutionResult]) -> str:
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
        
        md_lines.extend(None)
        
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
    
    def xǁReporterǁ_build_markdown__mutmut_32(self, results: list[ExecutionResult]) -> str:
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
        
        md_lines.extend(["XXXX", "## Details", ""])
        
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
    
    def xǁReporterǁ_build_markdown__mutmut_33(self, results: list[ExecutionResult]) -> str:
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
        
        md_lines.extend(["", "XX## DetailsXX", ""])
        
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
    
    def xǁReporterǁ_build_markdown__mutmut_34(self, results: list[ExecutionResult]) -> str:
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
        
        md_lines.extend(["", "## details", ""])
        
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
    
    def xǁReporterǁ_build_markdown__mutmut_35(self, results: list[ExecutionResult]) -> str:
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
        
        md_lines.extend(["", "## DETAILS", ""])
        
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
    
    def xǁReporterǁ_build_markdown__mutmut_36(self, results: list[ExecutionResult]) -> str:
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
        
        md_lines.extend(["", "## Details", "XXXX"])
        
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
    
    def xǁReporterǁ_build_markdown__mutmut_37(self, results: list[ExecutionResult]) -> str:
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
            md_lines.append(None)
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
    
    def xǁReporterǁ_build_markdown__mutmut_38(self, results: list[ExecutionResult]) -> str:
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
            md_lines.append(None)
            
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
    
    def xǁReporterǁ_build_markdown__mutmut_39(self, results: list[ExecutionResult]) -> str:
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
            md_lines.append("XXXX")
            
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
    
    def xǁReporterǁ_build_markdown__mutmut_40(self, results: list[ExecutionResult]) -> str:
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
                status = None
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
    
    def xǁReporterǁ_build_markdown__mutmut_41(self, results: list[ExecutionResult]) -> str:
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
                status = "XX✅XX" if result.passed else "❌"
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
    
    def xǁReporterǁ_build_markdown__mutmut_42(self, results: list[ExecutionResult]) -> str:
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
                status = "✅" if result.passed else "XX❌XX"
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
    
    def xǁReporterǁ_build_markdown__mutmut_43(self, results: list[ExecutionResult]) -> str:
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
                md_lines.append(None)
                
                if result.evaluator_results:
                    md_lines.append("  - Evaluators:")
                    for eval_result in result.evaluator_results:
                        eval_status = "✅" if eval_result.passed else "❌"
                        md_lines.append(
                            f"    - {eval_result.evaluator_name}: {eval_status}"
                        )
            
            md_lines.append("")
        
        return "\n".join(md_lines)
    
    def xǁReporterǁ_build_markdown__mutmut_44(self, results: list[ExecutionResult]) -> str:
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
                    md_lines.append(None)
                    for eval_result in result.evaluator_results:
                        eval_status = "✅" if eval_result.passed else "❌"
                        md_lines.append(
                            f"    - {eval_result.evaluator_name}: {eval_status}"
                        )
            
            md_lines.append("")
        
        return "\n".join(md_lines)
    
    def xǁReporterǁ_build_markdown__mutmut_45(self, results: list[ExecutionResult]) -> str:
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
                    md_lines.append("XX  - Evaluators:XX")
                    for eval_result in result.evaluator_results:
                        eval_status = "✅" if eval_result.passed else "❌"
                        md_lines.append(
                            f"    - {eval_result.evaluator_name}: {eval_status}"
                        )
            
            md_lines.append("")
        
        return "\n".join(md_lines)
    
    def xǁReporterǁ_build_markdown__mutmut_46(self, results: list[ExecutionResult]) -> str:
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
                    md_lines.append("  - evaluators:")
                    for eval_result in result.evaluator_results:
                        eval_status = "✅" if eval_result.passed else "❌"
                        md_lines.append(
                            f"    - {eval_result.evaluator_name}: {eval_status}"
                        )
            
            md_lines.append("")
        
        return "\n".join(md_lines)
    
    def xǁReporterǁ_build_markdown__mutmut_47(self, results: list[ExecutionResult]) -> str:
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
                    md_lines.append("  - EVALUATORS:")
                    for eval_result in result.evaluator_results:
                        eval_status = "✅" if eval_result.passed else "❌"
                        md_lines.append(
                            f"    - {eval_result.evaluator_name}: {eval_status}"
                        )
            
            md_lines.append("")
        
        return "\n".join(md_lines)
    
    def xǁReporterǁ_build_markdown__mutmut_48(self, results: list[ExecutionResult]) -> str:
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
                        eval_status = None
                        md_lines.append(
                            f"    - {eval_result.evaluator_name}: {eval_status}"
                        )
            
            md_lines.append("")
        
        return "\n".join(md_lines)
    
    def xǁReporterǁ_build_markdown__mutmut_49(self, results: list[ExecutionResult]) -> str:
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
                        eval_status = "XX✅XX" if eval_result.passed else "❌"
                        md_lines.append(
                            f"    - {eval_result.evaluator_name}: {eval_status}"
                        )
            
            md_lines.append("")
        
        return "\n".join(md_lines)
    
    def xǁReporterǁ_build_markdown__mutmut_50(self, results: list[ExecutionResult]) -> str:
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
                        eval_status = "✅" if eval_result.passed else "XX❌XX"
                        md_lines.append(
                            f"    - {eval_result.evaluator_name}: {eval_status}"
                        )
            
            md_lines.append("")
        
        return "\n".join(md_lines)
    
    def xǁReporterǁ_build_markdown__mutmut_51(self, results: list[ExecutionResult]) -> str:
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
                            None
                        )
            
            md_lines.append("")
        
        return "\n".join(md_lines)
    
    def xǁReporterǁ_build_markdown__mutmut_52(self, results: list[ExecutionResult]) -> str:
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
            
            md_lines.append(None)
        
        return "\n".join(md_lines)
    
    def xǁReporterǁ_build_markdown__mutmut_53(self, results: list[ExecutionResult]) -> str:
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
            
            md_lines.append("XXXX")
        
        return "\n".join(md_lines)
    
    def xǁReporterǁ_build_markdown__mutmut_54(self, results: list[ExecutionResult]) -> str:
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
        
        return "\n".join(None)
    
    def xǁReporterǁ_build_markdown__mutmut_55(self, results: list[ExecutionResult]) -> str:
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
        
        return "XX\nXX".join(md_lines)
    
    xǁReporterǁ_build_markdown__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁReporterǁ_build_markdown__mutmut_1': xǁReporterǁ_build_markdown__mutmut_1, 
        'xǁReporterǁ_build_markdown__mutmut_2': xǁReporterǁ_build_markdown__mutmut_2, 
        'xǁReporterǁ_build_markdown__mutmut_3': xǁReporterǁ_build_markdown__mutmut_3, 
        'xǁReporterǁ_build_markdown__mutmut_4': xǁReporterǁ_build_markdown__mutmut_4, 
        'xǁReporterǁ_build_markdown__mutmut_5': xǁReporterǁ_build_markdown__mutmut_5, 
        'xǁReporterǁ_build_markdown__mutmut_6': xǁReporterǁ_build_markdown__mutmut_6, 
        'xǁReporterǁ_build_markdown__mutmut_7': xǁReporterǁ_build_markdown__mutmut_7, 
        'xǁReporterǁ_build_markdown__mutmut_8': xǁReporterǁ_build_markdown__mutmut_8, 
        'xǁReporterǁ_build_markdown__mutmut_9': xǁReporterǁ_build_markdown__mutmut_9, 
        'xǁReporterǁ_build_markdown__mutmut_10': xǁReporterǁ_build_markdown__mutmut_10, 
        'xǁReporterǁ_build_markdown__mutmut_11': xǁReporterǁ_build_markdown__mutmut_11, 
        'xǁReporterǁ_build_markdown__mutmut_12': xǁReporterǁ_build_markdown__mutmut_12, 
        'xǁReporterǁ_build_markdown__mutmut_13': xǁReporterǁ_build_markdown__mutmut_13, 
        'xǁReporterǁ_build_markdown__mutmut_14': xǁReporterǁ_build_markdown__mutmut_14, 
        'xǁReporterǁ_build_markdown__mutmut_15': xǁReporterǁ_build_markdown__mutmut_15, 
        'xǁReporterǁ_build_markdown__mutmut_16': xǁReporterǁ_build_markdown__mutmut_16, 
        'xǁReporterǁ_build_markdown__mutmut_17': xǁReporterǁ_build_markdown__mutmut_17, 
        'xǁReporterǁ_build_markdown__mutmut_18': xǁReporterǁ_build_markdown__mutmut_18, 
        'xǁReporterǁ_build_markdown__mutmut_19': xǁReporterǁ_build_markdown__mutmut_19, 
        'xǁReporterǁ_build_markdown__mutmut_20': xǁReporterǁ_build_markdown__mutmut_20, 
        'xǁReporterǁ_build_markdown__mutmut_21': xǁReporterǁ_build_markdown__mutmut_21, 
        'xǁReporterǁ_build_markdown__mutmut_22': xǁReporterǁ_build_markdown__mutmut_22, 
        'xǁReporterǁ_build_markdown__mutmut_23': xǁReporterǁ_build_markdown__mutmut_23, 
        'xǁReporterǁ_build_markdown__mutmut_24': xǁReporterǁ_build_markdown__mutmut_24, 
        'xǁReporterǁ_build_markdown__mutmut_25': xǁReporterǁ_build_markdown__mutmut_25, 
        'xǁReporterǁ_build_markdown__mutmut_26': xǁReporterǁ_build_markdown__mutmut_26, 
        'xǁReporterǁ_build_markdown__mutmut_27': xǁReporterǁ_build_markdown__mutmut_27, 
        'xǁReporterǁ_build_markdown__mutmut_28': xǁReporterǁ_build_markdown__mutmut_28, 
        'xǁReporterǁ_build_markdown__mutmut_29': xǁReporterǁ_build_markdown__mutmut_29, 
        'xǁReporterǁ_build_markdown__mutmut_30': xǁReporterǁ_build_markdown__mutmut_30, 
        'xǁReporterǁ_build_markdown__mutmut_31': xǁReporterǁ_build_markdown__mutmut_31, 
        'xǁReporterǁ_build_markdown__mutmut_32': xǁReporterǁ_build_markdown__mutmut_32, 
        'xǁReporterǁ_build_markdown__mutmut_33': xǁReporterǁ_build_markdown__mutmut_33, 
        'xǁReporterǁ_build_markdown__mutmut_34': xǁReporterǁ_build_markdown__mutmut_34, 
        'xǁReporterǁ_build_markdown__mutmut_35': xǁReporterǁ_build_markdown__mutmut_35, 
        'xǁReporterǁ_build_markdown__mutmut_36': xǁReporterǁ_build_markdown__mutmut_36, 
        'xǁReporterǁ_build_markdown__mutmut_37': xǁReporterǁ_build_markdown__mutmut_37, 
        'xǁReporterǁ_build_markdown__mutmut_38': xǁReporterǁ_build_markdown__mutmut_38, 
        'xǁReporterǁ_build_markdown__mutmut_39': xǁReporterǁ_build_markdown__mutmut_39, 
        'xǁReporterǁ_build_markdown__mutmut_40': xǁReporterǁ_build_markdown__mutmut_40, 
        'xǁReporterǁ_build_markdown__mutmut_41': xǁReporterǁ_build_markdown__mutmut_41, 
        'xǁReporterǁ_build_markdown__mutmut_42': xǁReporterǁ_build_markdown__mutmut_42, 
        'xǁReporterǁ_build_markdown__mutmut_43': xǁReporterǁ_build_markdown__mutmut_43, 
        'xǁReporterǁ_build_markdown__mutmut_44': xǁReporterǁ_build_markdown__mutmut_44, 
        'xǁReporterǁ_build_markdown__mutmut_45': xǁReporterǁ_build_markdown__mutmut_45, 
        'xǁReporterǁ_build_markdown__mutmut_46': xǁReporterǁ_build_markdown__mutmut_46, 
        'xǁReporterǁ_build_markdown__mutmut_47': xǁReporterǁ_build_markdown__mutmut_47, 
        'xǁReporterǁ_build_markdown__mutmut_48': xǁReporterǁ_build_markdown__mutmut_48, 
        'xǁReporterǁ_build_markdown__mutmut_49': xǁReporterǁ_build_markdown__mutmut_49, 
        'xǁReporterǁ_build_markdown__mutmut_50': xǁReporterǁ_build_markdown__mutmut_50, 
        'xǁReporterǁ_build_markdown__mutmut_51': xǁReporterǁ_build_markdown__mutmut_51, 
        'xǁReporterǁ_build_markdown__mutmut_52': xǁReporterǁ_build_markdown__mutmut_52, 
        'xǁReporterǁ_build_markdown__mutmut_53': xǁReporterǁ_build_markdown__mutmut_53, 
        'xǁReporterǁ_build_markdown__mutmut_54': xǁReporterǁ_build_markdown__mutmut_54, 
        'xǁReporterǁ_build_markdown__mutmut_55': xǁReporterǁ_build_markdown__mutmut_55
    }
    xǁReporterǁ_build_markdown__mutmut_orig.__name__ = 'xǁReporterǁ_build_markdown'
    
    def calculate_summary(
        self,
        results: list[ExecutionResult]
    ) -> dict[str, Any]:
        args = [results]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁReporterǁcalculate_summary__mutmut_orig'), object.__getattribute__(self, 'xǁReporterǁcalculate_summary__mutmut_mutants'), args, kwargs, self)
    
    def xǁReporterǁcalculate_summary__mutmut_orig(
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
    
    def xǁReporterǁcalculate_summary__mutmut_1(
        self,
        results: list[ExecutionResult]
    ) -> dict[str, Any]:
        """Calculate aggregate statistics.
        
        Args:
            results: List of execution results
            
        Returns:
            Summary statistics
        """
        if results:
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
    
    def xǁReporterǁcalculate_summary__mutmut_2(
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
        by_treatment: dict[str, list[ExecutionResult]] = None
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
    
    def xǁReporterǁcalculate_summary__mutmut_3(
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
            if result.treatment in by_treatment:
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
    
    def xǁReporterǁcalculate_summary__mutmut_4(
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
                by_treatment[result.treatment] = None
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
    
    def xǁReporterǁcalculate_summary__mutmut_5(
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
            by_treatment[result.treatment].append(None)
        
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
    
    def xǁReporterǁcalculate_summary__mutmut_6(
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
        
        summary = None
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
    
    def xǁReporterǁcalculate_summary__mutmut_7(
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
            passed = None
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
    
    def xǁReporterǁcalculate_summary__mutmut_8(
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
            passed = sum(None)
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
    
    def xǁReporterǁcalculate_summary__mutmut_9(
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
            passed = sum(2 for r in treatment_results if r.passed)
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
    
    def xǁReporterǁcalculate_summary__mutmut_10(
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
            total = None
            
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
    
    def xǁReporterǁcalculate_summary__mutmut_11(
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
            durations = None
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
    
    def xǁReporterǁcalculate_summary__mutmut_12(
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
            avg_duration = None
            
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
    
    def xǁReporterǁcalculate_summary__mutmut_13(
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
            avg_duration = sum(durations) * len(durations) if durations else 0
            
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
    
    def xǁReporterǁcalculate_summary__mutmut_14(
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
            avg_duration = sum(None) / len(durations) if durations else 0
            
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
    
    def xǁReporterǁcalculate_summary__mutmut_15(
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
            avg_duration = sum(durations) / len(durations) if durations else 1
            
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
    
    def xǁReporterǁcalculate_summary__mutmut_16(
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
            tokens = None
            total_tokens = sum(tokens)
            
            summary[treatment] = {
                "passed": passed,
                "total": total,
                "pass_rate": passed / total if total > 0 else 0,
                "avg_duration_ms": avg_duration,
                "total_tokens": total_tokens
            }
        
        return summary
    
    def xǁReporterǁcalculate_summary__mutmut_17(
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
            total_tokens = None
            
            summary[treatment] = {
                "passed": passed,
                "total": total,
                "pass_rate": passed / total if total > 0 else 0,
                "avg_duration_ms": avg_duration,
                "total_tokens": total_tokens
            }
        
        return summary
    
    def xǁReporterǁcalculate_summary__mutmut_18(
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
            total_tokens = sum(None)
            
            summary[treatment] = {
                "passed": passed,
                "total": total,
                "pass_rate": passed / total if total > 0 else 0,
                "avg_duration_ms": avg_duration,
                "total_tokens": total_tokens
            }
        
        return summary
    
    def xǁReporterǁcalculate_summary__mutmut_19(
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
            
            summary[treatment] = None
        
        return summary
    
    def xǁReporterǁcalculate_summary__mutmut_20(
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
                "XXpassedXX": passed,
                "total": total,
                "pass_rate": passed / total if total > 0 else 0,
                "avg_duration_ms": avg_duration,
                "total_tokens": total_tokens
            }
        
        return summary
    
    def xǁReporterǁcalculate_summary__mutmut_21(
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
                "PASSED": passed,
                "total": total,
                "pass_rate": passed / total if total > 0 else 0,
                "avg_duration_ms": avg_duration,
                "total_tokens": total_tokens
            }
        
        return summary
    
    def xǁReporterǁcalculate_summary__mutmut_22(
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
                "XXtotalXX": total,
                "pass_rate": passed / total if total > 0 else 0,
                "avg_duration_ms": avg_duration,
                "total_tokens": total_tokens
            }
        
        return summary
    
    def xǁReporterǁcalculate_summary__mutmut_23(
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
                "TOTAL": total,
                "pass_rate": passed / total if total > 0 else 0,
                "avg_duration_ms": avg_duration,
                "total_tokens": total_tokens
            }
        
        return summary
    
    def xǁReporterǁcalculate_summary__mutmut_24(
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
                "XXpass_rateXX": passed / total if total > 0 else 0,
                "avg_duration_ms": avg_duration,
                "total_tokens": total_tokens
            }
        
        return summary
    
    def xǁReporterǁcalculate_summary__mutmut_25(
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
                "PASS_RATE": passed / total if total > 0 else 0,
                "avg_duration_ms": avg_duration,
                "total_tokens": total_tokens
            }
        
        return summary
    
    def xǁReporterǁcalculate_summary__mutmut_26(
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
                "pass_rate": passed * total if total > 0 else 0,
                "avg_duration_ms": avg_duration,
                "total_tokens": total_tokens
            }
        
        return summary
    
    def xǁReporterǁcalculate_summary__mutmut_27(
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
                "pass_rate": passed / total if total >= 0 else 0,
                "avg_duration_ms": avg_duration,
                "total_tokens": total_tokens
            }
        
        return summary
    
    def xǁReporterǁcalculate_summary__mutmut_28(
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
                "pass_rate": passed / total if total > 1 else 0,
                "avg_duration_ms": avg_duration,
                "total_tokens": total_tokens
            }
        
        return summary
    
    def xǁReporterǁcalculate_summary__mutmut_29(
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
                "pass_rate": passed / total if total > 0 else 1,
                "avg_duration_ms": avg_duration,
                "total_tokens": total_tokens
            }
        
        return summary
    
    def xǁReporterǁcalculate_summary__mutmut_30(
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
                "XXavg_duration_msXX": avg_duration,
                "total_tokens": total_tokens
            }
        
        return summary
    
    def xǁReporterǁcalculate_summary__mutmut_31(
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
                "AVG_DURATION_MS": avg_duration,
                "total_tokens": total_tokens
            }
        
        return summary
    
    def xǁReporterǁcalculate_summary__mutmut_32(
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
                "XXtotal_tokensXX": total_tokens
            }
        
        return summary
    
    def xǁReporterǁcalculate_summary__mutmut_33(
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
                "TOTAL_TOKENS": total_tokens
            }
        
        return summary
    
    xǁReporterǁcalculate_summary__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁReporterǁcalculate_summary__mutmut_1': xǁReporterǁcalculate_summary__mutmut_1, 
        'xǁReporterǁcalculate_summary__mutmut_2': xǁReporterǁcalculate_summary__mutmut_2, 
        'xǁReporterǁcalculate_summary__mutmut_3': xǁReporterǁcalculate_summary__mutmut_3, 
        'xǁReporterǁcalculate_summary__mutmut_4': xǁReporterǁcalculate_summary__mutmut_4, 
        'xǁReporterǁcalculate_summary__mutmut_5': xǁReporterǁcalculate_summary__mutmut_5, 
        'xǁReporterǁcalculate_summary__mutmut_6': xǁReporterǁcalculate_summary__mutmut_6, 
        'xǁReporterǁcalculate_summary__mutmut_7': xǁReporterǁcalculate_summary__mutmut_7, 
        'xǁReporterǁcalculate_summary__mutmut_8': xǁReporterǁcalculate_summary__mutmut_8, 
        'xǁReporterǁcalculate_summary__mutmut_9': xǁReporterǁcalculate_summary__mutmut_9, 
        'xǁReporterǁcalculate_summary__mutmut_10': xǁReporterǁcalculate_summary__mutmut_10, 
        'xǁReporterǁcalculate_summary__mutmut_11': xǁReporterǁcalculate_summary__mutmut_11, 
        'xǁReporterǁcalculate_summary__mutmut_12': xǁReporterǁcalculate_summary__mutmut_12, 
        'xǁReporterǁcalculate_summary__mutmut_13': xǁReporterǁcalculate_summary__mutmut_13, 
        'xǁReporterǁcalculate_summary__mutmut_14': xǁReporterǁcalculate_summary__mutmut_14, 
        'xǁReporterǁcalculate_summary__mutmut_15': xǁReporterǁcalculate_summary__mutmut_15, 
        'xǁReporterǁcalculate_summary__mutmut_16': xǁReporterǁcalculate_summary__mutmut_16, 
        'xǁReporterǁcalculate_summary__mutmut_17': xǁReporterǁcalculate_summary__mutmut_17, 
        'xǁReporterǁcalculate_summary__mutmut_18': xǁReporterǁcalculate_summary__mutmut_18, 
        'xǁReporterǁcalculate_summary__mutmut_19': xǁReporterǁcalculate_summary__mutmut_19, 
        'xǁReporterǁcalculate_summary__mutmut_20': xǁReporterǁcalculate_summary__mutmut_20, 
        'xǁReporterǁcalculate_summary__mutmut_21': xǁReporterǁcalculate_summary__mutmut_21, 
        'xǁReporterǁcalculate_summary__mutmut_22': xǁReporterǁcalculate_summary__mutmut_22, 
        'xǁReporterǁcalculate_summary__mutmut_23': xǁReporterǁcalculate_summary__mutmut_23, 
        'xǁReporterǁcalculate_summary__mutmut_24': xǁReporterǁcalculate_summary__mutmut_24, 
        'xǁReporterǁcalculate_summary__mutmut_25': xǁReporterǁcalculate_summary__mutmut_25, 
        'xǁReporterǁcalculate_summary__mutmut_26': xǁReporterǁcalculate_summary__mutmut_26, 
        'xǁReporterǁcalculate_summary__mutmut_27': xǁReporterǁcalculate_summary__mutmut_27, 
        'xǁReporterǁcalculate_summary__mutmut_28': xǁReporterǁcalculate_summary__mutmut_28, 
        'xǁReporterǁcalculate_summary__mutmut_29': xǁReporterǁcalculate_summary__mutmut_29, 
        'xǁReporterǁcalculate_summary__mutmut_30': xǁReporterǁcalculate_summary__mutmut_30, 
        'xǁReporterǁcalculate_summary__mutmut_31': xǁReporterǁcalculate_summary__mutmut_31, 
        'xǁReporterǁcalculate_summary__mutmut_32': xǁReporterǁcalculate_summary__mutmut_32, 
        'xǁReporterǁcalculate_summary__mutmut_33': xǁReporterǁcalculate_summary__mutmut_33
    }
    xǁReporterǁcalculate_summary__mutmut_orig.__name__ = 'xǁReporterǁcalculate_summary'
