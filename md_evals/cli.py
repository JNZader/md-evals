"""CLI commands for md-evals."""

import asyncio
import sys
import logging
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from typing_extensions import Annotated, Optional

from md_evals import __version__
from md_evals.config import ConfigLoader, ConfigLoaderError
from md_evals.engine import ExecutionEngine
from md_evals.evaluator import EvaluatorEngine
from md_evals.llm import LLMAdapter
from md_evals.linter import LinterEngine
from md_evals.models import LinterConfig, Defaults
from md_evals.reporter import Reporter
from md_evals.provider_registry import ProviderRegistry
from md_evals.providers import GitHubModelsProvider

logger = logging.getLogger(__name__)

app = typer.Typer(
    name="md-evals",
    help="Evaluate AI skills with Control vs Treatment testing",
    add_completion=False
)
console = Console()


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
    provider: Annotated[Optional[str], typer.Option("--provider", "-p", help="Override provider (e.g., github-models, openai, anthropic)")] = None,
    count: Annotated[int, typer.Option("--count", help="Number of repetitions")] = 1,
    workers: Annotated[int, typer.Option("-n", help="Number of parallel workers")] = 1,
    output: Annotated[str, typer.Option("--output", "-o", help="Output format")] = "table",
    no_lint: Annotated[bool, typer.Option("--no-lint", help="Skip linting")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Verbose output")] = False,
    debug: Annotated[bool, typer.Option("--debug", help="Enable debug logging for provider initialization")] = False,
):
    """Run evaluations with support for GitHub Models and other providers."""
    # Configure logging if debug is enabled
    if debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format="[%(levelname)s] %(name)s: %(message)s"
        )
        logger.debug(f"Debug logging enabled")
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
    if provider:
        # Normalize provider name (github-models, GitHub Models, github_models)
        config_obj.defaults.provider = provider
        logger.debug(f"Provider override: {provider}")
        # Validate provider exists in registry
        try:
            ProviderRegistry.get(provider)
        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
            console.print("[yellow]Available providers:[/yellow]")
            for pname in ProviderRegistry.list_providers().keys():
                console.print(f"  - {pname}")
            raise typer.Exit(code=1)
    
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
    try:
        logger.debug(f"Initializing LLM adapter: provider={config_obj.defaults.provider}, model={config_obj.defaults.model}")
        llm_adapter = LLMAdapter(
            model=config_obj.defaults.model,
            provider=config_obj.defaults.provider,
            defaults=config_obj.defaults
        )
        logger.debug(f"LLM adapter initialized successfully")
    except Exception as e:
        # Enhanced error message for GitHub Models authentication
        error_msg = str(e).lower()
        if "github" in error_msg and "token" in error_msg:
            console.print(f"[red]Authentication Error: {e}[/red]")
            console.print("\n[yellow]GitHub Models Troubleshooting:[/yellow]")
            console.print("1. Set your GitHub token: export GITHUB_TOKEN=github_pat_...")
            console.print("2. Generate a token at: https://github.com/settings/tokens")
            console.print("3. Check your .env file for GITHUB_TOKEN")
        else:
            console.print(f"[red]Error initializing provider: {e}[/red]")
        raise typer.Exit(code=1)
    
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
        # Enhanced error messages for various provider errors
        error_msg = str(e)
        error_lower = error_msg.lower()
        
        console.print(f"[red]Error during execution: {error_msg}[/red]")
        
        if "github" in error_lower and "rate" in error_lower:
            console.print("\n[yellow]Rate Limit Help:[/yellow]")
            console.print("- Free tier limit: 15 requests/minute")
            console.print("- Consider: batching requests, caching responses, or waiting")
        elif "github" in error_lower and "token" in error_lower:
            console.print("\n[yellow]GitHub Token Help:[/yellow]")
            console.print("- Check: export GITHUB_TOKEN=github_pat_...")
            console.print("- Generate: https://github.com/settings/tokens")
        elif "context" in error_lower or "token limit" in error_lower:
            console.print("\n[yellow]Context Window Help:[/yellow]")
            console.print("- Prompt too long for selected model")
            console.print("- Try: shorter prompts or models with larger context windows")
        
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


@app.command("list-models")
def list_models(
    provider: Annotated[Optional[str], typer.Option("--provider", "-p", help="Provider to list models for (default: all)")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Show additional metadata")] = False,
):
    """List available models for providers.
    
    Examples:
        md-evals list-models                          # Show all providers
        md-evals list-models --provider github-models # Show GitHub Models only
        md-evals list-models --provider openai        # Show OpenAI models
    """
    registry = ProviderRegistry()
    
    # If specific provider requested
    if provider:
        try:
            provider_class = registry.get(provider)
        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(code=1)
        
        # Display models for this provider
        if hasattr(provider_class, 'supported_models'):
            models = provider_class.supported_models()
            if models:
                _display_provider_models(provider, provider_class, models, verbose)
            else:
                console.print(f"[yellow]No models found for provider '{provider}'[/yellow]")
        else:
            console.print(f"[yellow]Provider '{provider}' does not support model listing[/yellow]")
    else:
        # Display all providers and their models
        providers = registry.list_providers()
        if not providers:
            console.print("[yellow]No providers registered[/yellow]")
            raise typer.Exit(code=0)
        
        for pname, pclass in providers.items():
            if hasattr(pclass, 'supported_models'):
                models = pclass.supported_models()
                if models:
                    _display_provider_models(pname, pclass, models, verbose)


def _display_provider_models(provider_name: str, provider_class, models: dict, verbose: bool = False):
    """Display models for a specific provider in a formatted table.
    
    Args:
        provider_name: Provider name (e.g., 'github-models')
        provider_class: Provider class
        models: Dict of model name -> metadata
        verbose: Show detailed metadata
    """
    console.print(f"\n[bold cyan]{provider_name}:[/bold cyan]")
    
    # Create table
    table = Table(title=f"{provider_name} Models", show_header=True, header_style="bold")
    table.add_column("Model Name", style="cyan")
    table.add_column("Provider", style="magenta")
    table.add_column("Context Window", style="green")
    table.add_column("Status", style="yellow")
    
    if verbose:
        table.add_column("Temperature", style="blue")
        table.add_column("Cost", style="red")
        table.add_column("Rate Limit", style="white")
        table.add_column("Notes", style="dim")
    
    # Add rows for each model
    for model_name, metadata in models.items():
        if verbose:
            table.add_row(
                model_name,
                getattr(metadata, 'provider', 'unknown'),
                f"{getattr(metadata, 'context_window', 'N/A'):,}",
                getattr(metadata, 'status', 'unknown'),
                f"{getattr(metadata, 'temperature_range', (0, 1))[0]:.1f}–{getattr(metadata, 'temperature_range', (0, 1))[1]:.1f}",
                getattr(metadata, 'cost', 'unknown'),
                getattr(metadata, 'rate_limit', 'unknown'),
                getattr(metadata, 'notes', ''),
            )
        else:
            table.add_row(
                model_name,
                getattr(metadata, 'provider', 'unknown'),
                f"{getattr(metadata, 'context_window', 'N/A'):,}",
                getattr(metadata, 'status', 'unknown'),
            )
    
    console.print(table)


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
