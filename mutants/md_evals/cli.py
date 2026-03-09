"""CLI commands for md-evals."""

import asyncio
import sys
from pathlib import Path

import typer
from rich.console import Console
from typing_extensions import Annotated, Optional

from md_evals import __version__
from md_evals.config import ConfigLoader, ConfigLoaderError
from md_evals.engine import ExecutionEngine
from md_evals.evaluator import EvaluatorEngine
from md_evals.llm import LLMAdapter
from md_evals.linter import LinterEngine
from md_evals.models import LinterConfig, Defaults
from md_evals.reporter import Reporter

app = typer.Typer(
    name="md-evals",
    help="Evaluate AI skills with Control vs Treatment testing",
    add_completion=False
)
console = Console()
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


@app.command()
def version():
    """Show version."""
    console.print(f"md-evals {__version__}")


@app.command()
def init(
    directory: Annotated[str, typer.Argument(help="Directory to initialize")] = ".",
    force: Annotated[bool, typer.Option("--force", "-f", help="Overwrite existing files")] = False,
):
    """Scaffold eval.yaml and SKILL.md template."""
    directory = Path(directory)
    
    # Create directory if it doesn't exist
    directory.mkdir(parents=True, exist_ok=True)
    
    # Check for existing files
    eval_yaml = directory / "eval.yaml"
    skill_md = directory / "SKILL.md"
    
    if eval_yaml.exists() and not force:
        console.print(f"[yellow]eval.yaml already exists. Use --force to overwrite.[/yellow]")
        raise typer.Exit(code=1)
    
    # Create eval.yaml
    eval_content = '''name: "My Evaluation"
version: "1.0"
description: "Evaluation of my skill"

defaults:
  model: "gpt-4o"
  provider: "openai"
  temperature: 0.7
  max_tokens: 2048
  timeout: 60
  retry_attempts: 3

treatments:
  CONTROL:
    description: "Baseline without skill"
    skill_path: null
  
  WITH_SKILL:
    description: "With skill injected"
    skill_path: "./SKILL.md"

tests:
  - name: "example_test"
    description: "Example test case"
    prompt: "Hello, {name}! How are you?"
    variables:
      name: "World"
    evaluators:
      - type: "regex"
        name: "has_greeting"
        pattern: "Hello"
        pass_on_match: true

lint:
  max_lines: 400
  fail_on_violation: true

output:
  format: "table"
  save_results: true
  results_dir: "./results"

execution:
  parallel_workers: 1
  repetitions: 1
  fail_fast: false
'''
    
    eval_yaml.write_text(eval_content)
    console.print(f"[green]Created {eval_yaml}[/green]")
    
    # Create SKILL.md template
    skill_content = '''# My Skill

## Description
Describe what this skill does and when it should be applied.

## Rules
- Rule 1: Be specific and actionable
- Rule 2: Keep it concise
- Rule 3: Focus on outcomes

## Examples

### Example 1
**Input:** User asks for help
**Expected behavior:** Provide helpful, specific guidance

### Example 2  
**Input:** User asks for code
**Expected behavior:** Provide clean, well-documented code
'''
    
    skill_md.write_text(skill_content)
    console.print(f"[green]Created {skill_md}[/green]")
    
    # Create results directory
    results_dir = directory / "results"
    results_dir.mkdir(exist_ok=True)
    console.print(f"[green]Created {results_dir}/[/green]")
    
    console.print("\n[bold green]Initialization complete![/bold green]")
    console.print("Run 'md-evals run' to start evaluation.")


@app.command()
def run(
    config: Annotated[str, typer.Option("--config", "-c", help="Config file path")] = "eval.yaml",
    treatment: Annotated[Optional[str], typer.Option("--treatment", "-t", help="Treatment(s) to run (comma-separated or wildcard)")] = None,
    model: Annotated[Optional[str], typer.Option("--model", "-m", help="Override model")] = None,
    count: Annotated[int, typer.Option("--count", help="Number of repetitions")] = 1,
    workers: Annotated[int, typer.Option("-n", help="Number of parallel workers")] = 1,
    output: Annotated[str, typer.Option("--output", "-o", help="Output format")] = "table",
    no_lint: Annotated[bool, typer.Option("--no-lint", help="Skip linting")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Verbose output")] = False,
):
    """Run evaluations."""
    try:
        # Load config
        config_obj = ConfigLoader.load(config)
    except ConfigLoaderError as e:
        console.print(f"[red]Error loading config: {e}[/red]")
        raise typer.Exit(code=1)
    
    # Override execution settings
    if count > 1:
        config_obj.execution.repetitions = count
    if workers > 1:
        config_obj.execution.parallel_workers = workers
    if model:
        config_obj.defaults.model = model
    
    # Run linter first (optional)
    if not no_lint:
        lint_config = LinterConfig(
            max_lines=config_obj.lint.max_lines,
            fail_on_violation=config_obj.lint.fail_on_violation
        )
        linter = LinterEngine(lint_config)
        
        # Find skill files to lint
        skill_files = set()
        for treatment_cfg in config_obj.treatments.values():
            if treatment_cfg.skill_path:
                skill_files.add(treatment_cfg.skill_path)
        
        for skill_file in skill_files:
            report = linter.run(skill_file)
            if not report.passed:
                console.print(f"[yellow]Linter warnings for {skill_file}:[/yellow]")
                for violation in report.violations:
                    console.print(f"  [{violation.severity}] {violation.message}")
                
                if config_obj.lint.fail_on_violation:
                    console.print("[red]Linter failed. Use --no-lint to skip.[/red]")
                    raise typer.Exit(code=2)
    
    # Determine treatments to run
    try:
        if treatment:
            treatments = [t.strip() for t in treatment.split(",")]
            treatments = ConfigLoader.expand_wildcards(treatments, config_obj.treatments)
        else:
            treatments = list(config_obj.treatments.keys())
    except ConfigLoaderError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)
    
    # Add CONTROL if not present
    if "CONTROL" not in treatments:
        treatments.insert(0, "CONTROL")
    
    # Run evaluation
    console.print(f"[cyan]Running {len(treatments)} treatment(s)...[/cyan]")
    
    # Create LLM adapter
    llm_adapter = LLMAdapter(
        model=config_obj.defaults.model,
        provider=config_obj.defaults.provider,
        defaults=config_obj.defaults
    )
    
    # Create evaluator engine
    evaluator_engine = EvaluatorEngine(llm_adapter=llm_adapter)
    
    # Create execution engine
    engine = ExecutionEngine(
        config=config_obj,
        llm_adapter=llm_adapter,
        evaluator_engine=evaluator_engine
    )
    
    # Run
    try:
        results = asyncio.run(engine.run_all(treatments))
    except Exception as e:
        console.print(f"[red]Error during execution: {e}[/red]")
        raise typer.Exit(code=3)
    
    # Report
    reporter = Reporter(config_obj)
    
    if output == "table":
        reporter.report_terminal(results, verbose)
    elif output == "json":
        output_path = f"{config_obj.output.results_dir}/results.json"
        reporter.report_json(results, output_path)
        console.print(f"[green]Saved results to {output_path}[/green]")
    elif output == "markdown":
        output_path = f"{config_obj.output.results_dir}/results.md"
        reporter.report_markdown(results, output_path)
        console.print(f"[green]Saved results to {output_path}[/green]")
    
    # Exit code based on results
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    
    if passed == total:
        raise typer.Exit(code=0)
    elif passed > 0:
        raise typer.Exit(code=0)  # Partial success
    else:
        raise typer.Exit(code=4)


@app.command()
def lint(
    skill_path: Annotated[str, typer.Argument(help="Skill file to lint")] = "SKILL.md",
    fail: Annotated[bool, typer.Option("--fail", "-f", help="Exit with error on violations")] = True,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Show details")] = False,
):
    """Validate SKILL.md against constraints."""
    config = LinterConfig(fail_on_violation=fail)
    engine = LinterEngine(config)
    
    report = engine.run(skill_path)
    
    if report.passed:
        console.print(f"[green]✓ {skill_path} passes linting[/green]")
        if verbose:
            console.print(f"  Lines: {report.line_count}")
        raise typer.Exit(code=0)
    else:
        console.print(f"[red]✗ {skill_path} has violations:[/red]")
        for violation in report.violations:
            severity = violation.severity.upper()
            console.print(f"  [{severity}] {violation.message}")
        
        if verbose:
            console.print(f"  Total lines: {report.line_count}")
        
        if fail:
            raise typer.Exit(code=2)
        else:
            raise typer.Exit(code=0)


@app.command()
def list(
    config: Annotated[str, typer.Option("--config", "-c", help="Config file path")] = "eval.yaml",
    treatments: Annotated[bool, typer.Option("--treatments", "-t", help="List treatments")] = False,
    tasks: Annotated[bool, typer.Option("--tasks", help="List tasks")] = False,
):
    """List available tasks and treatments."""
    try:
        config_obj = ConfigLoader.load(config)
    except ConfigLoaderError as e:
        console.print(f"[red]Error loading config: {e}[/red]")
        raise typer.Exit(code=1)
    
    # Default: show both
    show_all = not treatments and not tasks
    
    if show_all or treatments:
        console.print("[bold]Treatments:[/bold]")
        for name, treatment in config_obj.treatments.items():
            skill = treatment.skill_path or "(none)"
            desc = treatment.description or ""
            console.print(f"  - {name}: {desc} [{skill}]")
    
    if show_all or tasks:
        console.print("\n[bold]Tasks:[/bold]")
        for task in config_obj.tests:
            console.print(f"  - {task.name}: {task.description or ''}")
            for eval in task.evaluators:
                console.print(f"      - {eval.type}: {eval.name}")


if __name__ == "__main__":
    app()
