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
            treatments = [k for k in config_obj.treatments.keys()]
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
    args = [provider_name, provider_class, models, verbose]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__display_provider_models__mutmut_orig, x__display_provider_models__mutmut_mutants, args, kwargs, None)


def x__display_provider_models__mutmut_orig(provider_name: str, provider_class, models: dict, verbose: bool = False):
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


def x__display_provider_models__mutmut_1(provider_name: str, provider_class, models: dict, verbose: bool = True):
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


def x__display_provider_models__mutmut_2(provider_name: str, provider_class, models: dict, verbose: bool = False):
    """Display models for a specific provider in a formatted table.
    
    Args:
        provider_name: Provider name (e.g., 'github-models')
        provider_class: Provider class
        models: Dict of model name -> metadata
        verbose: Show detailed metadata
    """
    console.print(None)
    
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


def x__display_provider_models__mutmut_3(provider_name: str, provider_class, models: dict, verbose: bool = False):
    """Display models for a specific provider in a formatted table.
    
    Args:
        provider_name: Provider name (e.g., 'github-models')
        provider_class: Provider class
        models: Dict of model name -> metadata
        verbose: Show detailed metadata
    """
    console.print(f"\n[bold cyan]{provider_name}:[/bold cyan]")
    
    # Create table
    table = None
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


def x__display_provider_models__mutmut_4(provider_name: str, provider_class, models: dict, verbose: bool = False):
    """Display models for a specific provider in a formatted table.
    
    Args:
        provider_name: Provider name (e.g., 'github-models')
        provider_class: Provider class
        models: Dict of model name -> metadata
        verbose: Show detailed metadata
    """
    console.print(f"\n[bold cyan]{provider_name}:[/bold cyan]")
    
    # Create table
    table = Table(title=None, show_header=True, header_style="bold")
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


def x__display_provider_models__mutmut_5(provider_name: str, provider_class, models: dict, verbose: bool = False):
    """Display models for a specific provider in a formatted table.
    
    Args:
        provider_name: Provider name (e.g., 'github-models')
        provider_class: Provider class
        models: Dict of model name -> metadata
        verbose: Show detailed metadata
    """
    console.print(f"\n[bold cyan]{provider_name}:[/bold cyan]")
    
    # Create table
    table = Table(title=f"{provider_name} Models", show_header=None, header_style="bold")
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


def x__display_provider_models__mutmut_6(provider_name: str, provider_class, models: dict, verbose: bool = False):
    """Display models for a specific provider in a formatted table.
    
    Args:
        provider_name: Provider name (e.g., 'github-models')
        provider_class: Provider class
        models: Dict of model name -> metadata
        verbose: Show detailed metadata
    """
    console.print(f"\n[bold cyan]{provider_name}:[/bold cyan]")
    
    # Create table
    table = Table(title=f"{provider_name} Models", show_header=True, header_style=None)
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


def x__display_provider_models__mutmut_7(provider_name: str, provider_class, models: dict, verbose: bool = False):
    """Display models for a specific provider in a formatted table.
    
    Args:
        provider_name: Provider name (e.g., 'github-models')
        provider_class: Provider class
        models: Dict of model name -> metadata
        verbose: Show detailed metadata
    """
    console.print(f"\n[bold cyan]{provider_name}:[/bold cyan]")
    
    # Create table
    table = Table(show_header=True, header_style="bold")
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


def x__display_provider_models__mutmut_8(provider_name: str, provider_class, models: dict, verbose: bool = False):
    """Display models for a specific provider in a formatted table.
    
    Args:
        provider_name: Provider name (e.g., 'github-models')
        provider_class: Provider class
        models: Dict of model name -> metadata
        verbose: Show detailed metadata
    """
    console.print(f"\n[bold cyan]{provider_name}:[/bold cyan]")
    
    # Create table
    table = Table(title=f"{provider_name} Models", header_style="bold")
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


def x__display_provider_models__mutmut_9(provider_name: str, provider_class, models: dict, verbose: bool = False):
    """Display models for a specific provider in a formatted table.
    
    Args:
        provider_name: Provider name (e.g., 'github-models')
        provider_class: Provider class
        models: Dict of model name -> metadata
        verbose: Show detailed metadata
    """
    console.print(f"\n[bold cyan]{provider_name}:[/bold cyan]")
    
    # Create table
    table = Table(title=f"{provider_name} Models", show_header=True, )
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


def x__display_provider_models__mutmut_10(provider_name: str, provider_class, models: dict, verbose: bool = False):
    """Display models for a specific provider in a formatted table.
    
    Args:
        provider_name: Provider name (e.g., 'github-models')
        provider_class: Provider class
        models: Dict of model name -> metadata
        verbose: Show detailed metadata
    """
    console.print(f"\n[bold cyan]{provider_name}:[/bold cyan]")
    
    # Create table
    table = Table(title=f"{provider_name} Models", show_header=False, header_style="bold")
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


def x__display_provider_models__mutmut_11(provider_name: str, provider_class, models: dict, verbose: bool = False):
    """Display models for a specific provider in a formatted table.
    
    Args:
        provider_name: Provider name (e.g., 'github-models')
        provider_class: Provider class
        models: Dict of model name -> metadata
        verbose: Show detailed metadata
    """
    console.print(f"\n[bold cyan]{provider_name}:[/bold cyan]")
    
    # Create table
    table = Table(title=f"{provider_name} Models", show_header=True, header_style="XXboldXX")
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


def x__display_provider_models__mutmut_12(provider_name: str, provider_class, models: dict, verbose: bool = False):
    """Display models for a specific provider in a formatted table.
    
    Args:
        provider_name: Provider name (e.g., 'github-models')
        provider_class: Provider class
        models: Dict of model name -> metadata
        verbose: Show detailed metadata
    """
    console.print(f"\n[bold cyan]{provider_name}:[/bold cyan]")
    
    # Create table
    table = Table(title=f"{provider_name} Models", show_header=True, header_style="BOLD")
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


def x__display_provider_models__mutmut_13(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
    table.add_column(None, style="cyan")
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


def x__display_provider_models__mutmut_14(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
    table.add_column("Model Name", style=None)
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


def x__display_provider_models__mutmut_15(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
    table.add_column(style="cyan")
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


def x__display_provider_models__mutmut_16(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
    table.add_column("Model Name", )
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


def x__display_provider_models__mutmut_17(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
    table.add_column("XXModel NameXX", style="cyan")
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


def x__display_provider_models__mutmut_18(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
    table.add_column("model name", style="cyan")
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


def x__display_provider_models__mutmut_19(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
    table.add_column("MODEL NAME", style="cyan")
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


def x__display_provider_models__mutmut_20(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
    table.add_column("Model Name", style="XXcyanXX")
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


def x__display_provider_models__mutmut_21(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
    table.add_column("Model Name", style="CYAN")
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


def x__display_provider_models__mutmut_22(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
    table.add_column(None, style="magenta")
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


def x__display_provider_models__mutmut_23(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
    table.add_column("Provider", style=None)
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


def x__display_provider_models__mutmut_24(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
    table.add_column(style="magenta")
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


def x__display_provider_models__mutmut_25(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
    table.add_column("Provider", )
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


def x__display_provider_models__mutmut_26(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
    table.add_column("XXProviderXX", style="magenta")
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


def x__display_provider_models__mutmut_27(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
    table.add_column("provider", style="magenta")
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


def x__display_provider_models__mutmut_28(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
    table.add_column("PROVIDER", style="magenta")
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


def x__display_provider_models__mutmut_29(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
    table.add_column("Provider", style="XXmagentaXX")
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


def x__display_provider_models__mutmut_30(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
    table.add_column("Provider", style="MAGENTA")
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


def x__display_provider_models__mutmut_31(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
    table.add_column(None, style="green")
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


def x__display_provider_models__mutmut_32(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
    table.add_column("Context Window", style=None)
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


def x__display_provider_models__mutmut_33(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
    table.add_column(style="green")
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


def x__display_provider_models__mutmut_34(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
    table.add_column("Context Window", )
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


def x__display_provider_models__mutmut_35(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
    table.add_column("XXContext WindowXX", style="green")
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


def x__display_provider_models__mutmut_36(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
    table.add_column("context window", style="green")
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


def x__display_provider_models__mutmut_37(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
    table.add_column("CONTEXT WINDOW", style="green")
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


def x__display_provider_models__mutmut_38(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
    table.add_column("Context Window", style="XXgreenXX")
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


def x__display_provider_models__mutmut_39(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
    table.add_column("Context Window", style="GREEN")
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


def x__display_provider_models__mutmut_40(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
    table.add_column(None, style="yellow")
    
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


def x__display_provider_models__mutmut_41(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
    table.add_column("Status", style=None)
    
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


def x__display_provider_models__mutmut_42(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
    table.add_column(style="yellow")
    
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


def x__display_provider_models__mutmut_43(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
    table.add_column("Status", )
    
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


def x__display_provider_models__mutmut_44(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
    table.add_column("XXStatusXX", style="yellow")
    
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


def x__display_provider_models__mutmut_45(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
    table.add_column("status", style="yellow")
    
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


def x__display_provider_models__mutmut_46(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
    table.add_column("STATUS", style="yellow")
    
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


def x__display_provider_models__mutmut_47(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
    table.add_column("Status", style="XXyellowXX")
    
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


def x__display_provider_models__mutmut_48(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
    table.add_column("Status", style="YELLOW")
    
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


def x__display_provider_models__mutmut_49(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
        table.add_column(None, style="blue")
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


def x__display_provider_models__mutmut_50(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
        table.add_column("Temperature", style=None)
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


def x__display_provider_models__mutmut_51(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
        table.add_column(style="blue")
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


def x__display_provider_models__mutmut_52(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
        table.add_column("Temperature", )
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


def x__display_provider_models__mutmut_53(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
        table.add_column("XXTemperatureXX", style="blue")
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


def x__display_provider_models__mutmut_54(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
        table.add_column("temperature", style="blue")
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


def x__display_provider_models__mutmut_55(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
        table.add_column("TEMPERATURE", style="blue")
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


def x__display_provider_models__mutmut_56(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
        table.add_column("Temperature", style="XXblueXX")
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


def x__display_provider_models__mutmut_57(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
        table.add_column("Temperature", style="BLUE")
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


def x__display_provider_models__mutmut_58(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
        table.add_column(None, style="red")
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


def x__display_provider_models__mutmut_59(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
        table.add_column("Cost", style=None)
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


def x__display_provider_models__mutmut_60(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
        table.add_column(style="red")
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


def x__display_provider_models__mutmut_61(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
        table.add_column("Cost", )
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


def x__display_provider_models__mutmut_62(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
        table.add_column("XXCostXX", style="red")
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


def x__display_provider_models__mutmut_63(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
        table.add_column("cost", style="red")
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


def x__display_provider_models__mutmut_64(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
        table.add_column("COST", style="red")
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


def x__display_provider_models__mutmut_65(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
        table.add_column("Cost", style="XXredXX")
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


def x__display_provider_models__mutmut_66(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
        table.add_column("Cost", style="RED")
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


def x__display_provider_models__mutmut_67(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
        table.add_column(None, style="white")
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


def x__display_provider_models__mutmut_68(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
        table.add_column("Rate Limit", style=None)
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


def x__display_provider_models__mutmut_69(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
        table.add_column(style="white")
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


def x__display_provider_models__mutmut_70(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
        table.add_column("Rate Limit", )
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


def x__display_provider_models__mutmut_71(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
        table.add_column("XXRate LimitXX", style="white")
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


def x__display_provider_models__mutmut_72(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
        table.add_column("rate limit", style="white")
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


def x__display_provider_models__mutmut_73(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
        table.add_column("RATE LIMIT", style="white")
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


def x__display_provider_models__mutmut_74(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
        table.add_column("Rate Limit", style="XXwhiteXX")
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


def x__display_provider_models__mutmut_75(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
        table.add_column("Rate Limit", style="WHITE")
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


def x__display_provider_models__mutmut_76(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
        table.add_column(None, style="dim")
    
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


def x__display_provider_models__mutmut_77(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
        table.add_column("Notes", style=None)
    
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


def x__display_provider_models__mutmut_78(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
        table.add_column(style="dim")
    
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


def x__display_provider_models__mutmut_79(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
        table.add_column("Notes", )
    
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


def x__display_provider_models__mutmut_80(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
        table.add_column("XXNotesXX", style="dim")
    
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


def x__display_provider_models__mutmut_81(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
        table.add_column("notes", style="dim")
    
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


def x__display_provider_models__mutmut_82(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
        table.add_column("NOTES", style="dim")
    
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


def x__display_provider_models__mutmut_83(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
        table.add_column("Notes", style="XXdimXX")
    
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


def x__display_provider_models__mutmut_84(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
        table.add_column("Notes", style="DIM")
    
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


def x__display_provider_models__mutmut_85(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                None,
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


def x__display_provider_models__mutmut_86(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                None,
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


def x__display_provider_models__mutmut_87(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                None,
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


def x__display_provider_models__mutmut_88(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                None,
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


def x__display_provider_models__mutmut_89(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                None,
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


def x__display_provider_models__mutmut_90(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                None,
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


def x__display_provider_models__mutmut_91(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                None,
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


def x__display_provider_models__mutmut_92(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                None,
            )
        else:
            table.add_row(
                model_name,
                getattr(metadata, 'provider', 'unknown'),
                f"{getattr(metadata, 'context_window', 'N/A'):,}",
                getattr(metadata, 'status', 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_93(provider_name: str, provider_class, models: dict, verbose: bool = False):
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


def x__display_provider_models__mutmut_94(provider_name: str, provider_class, models: dict, verbose: bool = False):
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


def x__display_provider_models__mutmut_95(provider_name: str, provider_class, models: dict, verbose: bool = False):
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


def x__display_provider_models__mutmut_96(provider_name: str, provider_class, models: dict, verbose: bool = False):
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


def x__display_provider_models__mutmut_97(provider_name: str, provider_class, models: dict, verbose: bool = False):
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


def x__display_provider_models__mutmut_98(provider_name: str, provider_class, models: dict, verbose: bool = False):
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


def x__display_provider_models__mutmut_99(provider_name: str, provider_class, models: dict, verbose: bool = False):
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


def x__display_provider_models__mutmut_100(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                )
        else:
            table.add_row(
                model_name,
                getattr(metadata, 'provider', 'unknown'),
                f"{getattr(metadata, 'context_window', 'N/A'):,}",
                getattr(metadata, 'status', 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_101(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(None, 'provider', 'unknown'),
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


def x__display_provider_models__mutmut_102(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, None, 'unknown'),
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


def x__display_provider_models__mutmut_103(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'provider', None),
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


def x__display_provider_models__mutmut_104(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr('provider', 'unknown'),
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


def x__display_provider_models__mutmut_105(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'unknown'),
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


def x__display_provider_models__mutmut_106(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'provider', ),
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


def x__display_provider_models__mutmut_107(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'XXproviderXX', 'unknown'),
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


def x__display_provider_models__mutmut_108(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'PROVIDER', 'unknown'),
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


def x__display_provider_models__mutmut_109(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'provider', 'XXunknownXX'),
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


def x__display_provider_models__mutmut_110(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'provider', 'UNKNOWN'),
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


def x__display_provider_models__mutmut_111(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr(None, 'context_window', 'N/A'):,}",
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


def x__display_provider_models__mutmut_112(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr(metadata, None, 'N/A'):,}",
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


def x__display_provider_models__mutmut_113(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr(metadata, 'context_window', None):,}",
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


def x__display_provider_models__mutmut_114(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr('context_window', 'N/A'):,}",
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


def x__display_provider_models__mutmut_115(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr(metadata, 'N/A'):,}",
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


def x__display_provider_models__mutmut_116(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr(metadata, 'context_window', ):,}",
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


def x__display_provider_models__mutmut_117(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr(metadata, 'XXcontext_windowXX', 'N/A'):,}",
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


def x__display_provider_models__mutmut_118(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr(metadata, 'CONTEXT_WINDOW', 'N/A'):,}",
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


def x__display_provider_models__mutmut_119(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr(metadata, 'context_window', 'XXN/AXX'):,}",
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


def x__display_provider_models__mutmut_120(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr(metadata, 'context_window', 'n/a'):,}",
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


def x__display_provider_models__mutmut_121(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(None, 'status', 'unknown'),
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


def x__display_provider_models__mutmut_122(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, None, 'unknown'),
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


def x__display_provider_models__mutmut_123(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'status', None),
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


def x__display_provider_models__mutmut_124(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr('status', 'unknown'),
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


def x__display_provider_models__mutmut_125(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'unknown'),
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


def x__display_provider_models__mutmut_126(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'status', ),
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


def x__display_provider_models__mutmut_127(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'XXstatusXX', 'unknown'),
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


def x__display_provider_models__mutmut_128(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'STATUS', 'unknown'),
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


def x__display_provider_models__mutmut_129(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'status', 'XXunknownXX'),
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


def x__display_provider_models__mutmut_130(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'status', 'UNKNOWN'),
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


def x__display_provider_models__mutmut_131(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr(None, 'temperature_range', (0, 1))[0]:.1f}–{getattr(metadata, 'temperature_range', (0, 1))[1]:.1f}",
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


def x__display_provider_models__mutmut_132(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr(metadata, None, (0, 1))[0]:.1f}–{getattr(metadata, 'temperature_range', (0, 1))[1]:.1f}",
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


def x__display_provider_models__mutmut_133(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr(metadata, 'temperature_range', None)[0]:.1f}–{getattr(metadata, 'temperature_range', (0, 1))[1]:.1f}",
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


def x__display_provider_models__mutmut_134(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr('temperature_range', (0, 1))[0]:.1f}–{getattr(metadata, 'temperature_range', (0, 1))[1]:.1f}",
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


def x__display_provider_models__mutmut_135(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr(metadata, (0, 1))[0]:.1f}–{getattr(metadata, 'temperature_range', (0, 1))[1]:.1f}",
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


def x__display_provider_models__mutmut_136(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr(metadata, 'temperature_range', )[0]:.1f}–{getattr(metadata, 'temperature_range', (0, 1))[1]:.1f}",
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


def x__display_provider_models__mutmut_137(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr(metadata, 'XXtemperature_rangeXX', (0, 1))[0]:.1f}–{getattr(metadata, 'temperature_range', (0, 1))[1]:.1f}",
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


def x__display_provider_models__mutmut_138(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr(metadata, 'TEMPERATURE_RANGE', (0, 1))[0]:.1f}–{getattr(metadata, 'temperature_range', (0, 1))[1]:.1f}",
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


def x__display_provider_models__mutmut_139(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr(metadata, 'temperature_range', (1, 1))[0]:.1f}–{getattr(metadata, 'temperature_range', (0, 1))[1]:.1f}",
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


def x__display_provider_models__mutmut_140(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr(metadata, 'temperature_range', (0, 2))[0]:.1f}–{getattr(metadata, 'temperature_range', (0, 1))[1]:.1f}",
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


def x__display_provider_models__mutmut_141(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr(metadata, 'temperature_range', (0, 1))[1]:.1f}–{getattr(metadata, 'temperature_range', (0, 1))[1]:.1f}",
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


def x__display_provider_models__mutmut_142(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr(metadata, 'temperature_range', (0, 1))[0]:.1f}–{getattr(None, 'temperature_range', (0, 1))[1]:.1f}",
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


def x__display_provider_models__mutmut_143(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr(metadata, 'temperature_range', (0, 1))[0]:.1f}–{getattr(metadata, None, (0, 1))[1]:.1f}",
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


def x__display_provider_models__mutmut_144(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr(metadata, 'temperature_range', (0, 1))[0]:.1f}–{getattr(metadata, 'temperature_range', None)[1]:.1f}",
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


def x__display_provider_models__mutmut_145(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr(metadata, 'temperature_range', (0, 1))[0]:.1f}–{getattr('temperature_range', (0, 1))[1]:.1f}",
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


def x__display_provider_models__mutmut_146(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr(metadata, 'temperature_range', (0, 1))[0]:.1f}–{getattr(metadata, (0, 1))[1]:.1f}",
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


def x__display_provider_models__mutmut_147(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr(metadata, 'temperature_range', (0, 1))[0]:.1f}–{getattr(metadata, 'temperature_range', )[1]:.1f}",
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


def x__display_provider_models__mutmut_148(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr(metadata, 'temperature_range', (0, 1))[0]:.1f}–{getattr(metadata, 'XXtemperature_rangeXX', (0, 1))[1]:.1f}",
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


def x__display_provider_models__mutmut_149(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr(metadata, 'temperature_range', (0, 1))[0]:.1f}–{getattr(metadata, 'TEMPERATURE_RANGE', (0, 1))[1]:.1f}",
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


def x__display_provider_models__mutmut_150(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr(metadata, 'temperature_range', (0, 1))[0]:.1f}–{getattr(metadata, 'temperature_range', (1, 1))[1]:.1f}",
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


def x__display_provider_models__mutmut_151(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr(metadata, 'temperature_range', (0, 1))[0]:.1f}–{getattr(metadata, 'temperature_range', (0, 2))[1]:.1f}",
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


def x__display_provider_models__mutmut_152(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr(metadata, 'temperature_range', (0, 1))[0]:.1f}–{getattr(metadata, 'temperature_range', (0, 1))[2]:.1f}",
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


def x__display_provider_models__mutmut_153(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(None, 'cost', 'unknown'),
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


def x__display_provider_models__mutmut_154(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, None, 'unknown'),
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


def x__display_provider_models__mutmut_155(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'cost', None),
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


def x__display_provider_models__mutmut_156(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr('cost', 'unknown'),
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


def x__display_provider_models__mutmut_157(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'unknown'),
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


def x__display_provider_models__mutmut_158(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'cost', ),
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


def x__display_provider_models__mutmut_159(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'XXcostXX', 'unknown'),
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


def x__display_provider_models__mutmut_160(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'COST', 'unknown'),
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


def x__display_provider_models__mutmut_161(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'cost', 'XXunknownXX'),
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


def x__display_provider_models__mutmut_162(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'cost', 'UNKNOWN'),
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


def x__display_provider_models__mutmut_163(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(None, 'rate_limit', 'unknown'),
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


def x__display_provider_models__mutmut_164(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, None, 'unknown'),
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


def x__display_provider_models__mutmut_165(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'rate_limit', None),
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


def x__display_provider_models__mutmut_166(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr('rate_limit', 'unknown'),
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


def x__display_provider_models__mutmut_167(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'unknown'),
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


def x__display_provider_models__mutmut_168(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'rate_limit', ),
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


def x__display_provider_models__mutmut_169(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'XXrate_limitXX', 'unknown'),
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


def x__display_provider_models__mutmut_170(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'RATE_LIMIT', 'unknown'),
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


def x__display_provider_models__mutmut_171(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'rate_limit', 'XXunknownXX'),
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


def x__display_provider_models__mutmut_172(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'rate_limit', 'UNKNOWN'),
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


def x__display_provider_models__mutmut_173(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(None, 'notes', ''),
            )
        else:
            table.add_row(
                model_name,
                getattr(metadata, 'provider', 'unknown'),
                f"{getattr(metadata, 'context_window', 'N/A'):,}",
                getattr(metadata, 'status', 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_174(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, None, ''),
            )
        else:
            table.add_row(
                model_name,
                getattr(metadata, 'provider', 'unknown'),
                f"{getattr(metadata, 'context_window', 'N/A'):,}",
                getattr(metadata, 'status', 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_175(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'notes', None),
            )
        else:
            table.add_row(
                model_name,
                getattr(metadata, 'provider', 'unknown'),
                f"{getattr(metadata, 'context_window', 'N/A'):,}",
                getattr(metadata, 'status', 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_176(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr('notes', ''),
            )
        else:
            table.add_row(
                model_name,
                getattr(metadata, 'provider', 'unknown'),
                f"{getattr(metadata, 'context_window', 'N/A'):,}",
                getattr(metadata, 'status', 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_177(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, ''),
            )
        else:
            table.add_row(
                model_name,
                getattr(metadata, 'provider', 'unknown'),
                f"{getattr(metadata, 'context_window', 'N/A'):,}",
                getattr(metadata, 'status', 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_178(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'notes', ),
            )
        else:
            table.add_row(
                model_name,
                getattr(metadata, 'provider', 'unknown'),
                f"{getattr(metadata, 'context_window', 'N/A'):,}",
                getattr(metadata, 'status', 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_179(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'XXnotesXX', ''),
            )
        else:
            table.add_row(
                model_name,
                getattr(metadata, 'provider', 'unknown'),
                f"{getattr(metadata, 'context_window', 'N/A'):,}",
                getattr(metadata, 'status', 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_180(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'NOTES', ''),
            )
        else:
            table.add_row(
                model_name,
                getattr(metadata, 'provider', 'unknown'),
                f"{getattr(metadata, 'context_window', 'N/A'):,}",
                getattr(metadata, 'status', 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_181(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'notes', 'XXXX'),
            )
        else:
            table.add_row(
                model_name,
                getattr(metadata, 'provider', 'unknown'),
                f"{getattr(metadata, 'context_window', 'N/A'):,}",
                getattr(metadata, 'status', 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_182(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                None,
                getattr(metadata, 'provider', 'unknown'),
                f"{getattr(metadata, 'context_window', 'N/A'):,}",
                getattr(metadata, 'status', 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_183(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                None,
                f"{getattr(metadata, 'context_window', 'N/A'):,}",
                getattr(metadata, 'status', 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_184(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                None,
                getattr(metadata, 'status', 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_185(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                None,
            )
    
    console.print(table)


def x__display_provider_models__mutmut_186(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'provider', 'unknown'),
                f"{getattr(metadata, 'context_window', 'N/A'):,}",
                getattr(metadata, 'status', 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_187(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr(metadata, 'context_window', 'N/A'):,}",
                getattr(metadata, 'status', 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_188(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'status', 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_189(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                )
    
    console.print(table)


def x__display_provider_models__mutmut_190(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(None, 'provider', 'unknown'),
                f"{getattr(metadata, 'context_window', 'N/A'):,}",
                getattr(metadata, 'status', 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_191(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, None, 'unknown'),
                f"{getattr(metadata, 'context_window', 'N/A'):,}",
                getattr(metadata, 'status', 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_192(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'provider', None),
                f"{getattr(metadata, 'context_window', 'N/A'):,}",
                getattr(metadata, 'status', 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_193(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr('provider', 'unknown'),
                f"{getattr(metadata, 'context_window', 'N/A'):,}",
                getattr(metadata, 'status', 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_194(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'unknown'),
                f"{getattr(metadata, 'context_window', 'N/A'):,}",
                getattr(metadata, 'status', 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_195(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'provider', ),
                f"{getattr(metadata, 'context_window', 'N/A'):,}",
                getattr(metadata, 'status', 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_196(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'XXproviderXX', 'unknown'),
                f"{getattr(metadata, 'context_window', 'N/A'):,}",
                getattr(metadata, 'status', 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_197(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'PROVIDER', 'unknown'),
                f"{getattr(metadata, 'context_window', 'N/A'):,}",
                getattr(metadata, 'status', 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_198(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'provider', 'XXunknownXX'),
                f"{getattr(metadata, 'context_window', 'N/A'):,}",
                getattr(metadata, 'status', 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_199(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'provider', 'UNKNOWN'),
                f"{getattr(metadata, 'context_window', 'N/A'):,}",
                getattr(metadata, 'status', 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_200(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr(None, 'context_window', 'N/A'):,}",
                getattr(metadata, 'status', 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_201(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr(metadata, None, 'N/A'):,}",
                getattr(metadata, 'status', 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_202(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr(metadata, 'context_window', None):,}",
                getattr(metadata, 'status', 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_203(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr('context_window', 'N/A'):,}",
                getattr(metadata, 'status', 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_204(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr(metadata, 'N/A'):,}",
                getattr(metadata, 'status', 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_205(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr(metadata, 'context_window', ):,}",
                getattr(metadata, 'status', 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_206(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr(metadata, 'XXcontext_windowXX', 'N/A'):,}",
                getattr(metadata, 'status', 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_207(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr(metadata, 'CONTEXT_WINDOW', 'N/A'):,}",
                getattr(metadata, 'status', 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_208(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr(metadata, 'context_window', 'XXN/AXX'):,}",
                getattr(metadata, 'status', 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_209(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                f"{getattr(metadata, 'context_window', 'n/a'):,}",
                getattr(metadata, 'status', 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_210(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(None, 'status', 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_211(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, None, 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_212(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'status', None),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_213(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr('status', 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_214(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_215(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'status', ),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_216(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'XXstatusXX', 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_217(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'STATUS', 'unknown'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_218(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'status', 'XXunknownXX'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_219(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
                getattr(metadata, 'status', 'UNKNOWN'),
            )
    
    console.print(table)


def x__display_provider_models__mutmut_220(provider_name: str, provider_class, models: dict, verbose: bool = False):
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
    
    console.print(None)

x__display_provider_models__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__display_provider_models__mutmut_1': x__display_provider_models__mutmut_1, 
    'x__display_provider_models__mutmut_2': x__display_provider_models__mutmut_2, 
    'x__display_provider_models__mutmut_3': x__display_provider_models__mutmut_3, 
    'x__display_provider_models__mutmut_4': x__display_provider_models__mutmut_4, 
    'x__display_provider_models__mutmut_5': x__display_provider_models__mutmut_5, 
    'x__display_provider_models__mutmut_6': x__display_provider_models__mutmut_6, 
    'x__display_provider_models__mutmut_7': x__display_provider_models__mutmut_7, 
    'x__display_provider_models__mutmut_8': x__display_provider_models__mutmut_8, 
    'x__display_provider_models__mutmut_9': x__display_provider_models__mutmut_9, 
    'x__display_provider_models__mutmut_10': x__display_provider_models__mutmut_10, 
    'x__display_provider_models__mutmut_11': x__display_provider_models__mutmut_11, 
    'x__display_provider_models__mutmut_12': x__display_provider_models__mutmut_12, 
    'x__display_provider_models__mutmut_13': x__display_provider_models__mutmut_13, 
    'x__display_provider_models__mutmut_14': x__display_provider_models__mutmut_14, 
    'x__display_provider_models__mutmut_15': x__display_provider_models__mutmut_15, 
    'x__display_provider_models__mutmut_16': x__display_provider_models__mutmut_16, 
    'x__display_provider_models__mutmut_17': x__display_provider_models__mutmut_17, 
    'x__display_provider_models__mutmut_18': x__display_provider_models__mutmut_18, 
    'x__display_provider_models__mutmut_19': x__display_provider_models__mutmut_19, 
    'x__display_provider_models__mutmut_20': x__display_provider_models__mutmut_20, 
    'x__display_provider_models__mutmut_21': x__display_provider_models__mutmut_21, 
    'x__display_provider_models__mutmut_22': x__display_provider_models__mutmut_22, 
    'x__display_provider_models__mutmut_23': x__display_provider_models__mutmut_23, 
    'x__display_provider_models__mutmut_24': x__display_provider_models__mutmut_24, 
    'x__display_provider_models__mutmut_25': x__display_provider_models__mutmut_25, 
    'x__display_provider_models__mutmut_26': x__display_provider_models__mutmut_26, 
    'x__display_provider_models__mutmut_27': x__display_provider_models__mutmut_27, 
    'x__display_provider_models__mutmut_28': x__display_provider_models__mutmut_28, 
    'x__display_provider_models__mutmut_29': x__display_provider_models__mutmut_29, 
    'x__display_provider_models__mutmut_30': x__display_provider_models__mutmut_30, 
    'x__display_provider_models__mutmut_31': x__display_provider_models__mutmut_31, 
    'x__display_provider_models__mutmut_32': x__display_provider_models__mutmut_32, 
    'x__display_provider_models__mutmut_33': x__display_provider_models__mutmut_33, 
    'x__display_provider_models__mutmut_34': x__display_provider_models__mutmut_34, 
    'x__display_provider_models__mutmut_35': x__display_provider_models__mutmut_35, 
    'x__display_provider_models__mutmut_36': x__display_provider_models__mutmut_36, 
    'x__display_provider_models__mutmut_37': x__display_provider_models__mutmut_37, 
    'x__display_provider_models__mutmut_38': x__display_provider_models__mutmut_38, 
    'x__display_provider_models__mutmut_39': x__display_provider_models__mutmut_39, 
    'x__display_provider_models__mutmut_40': x__display_provider_models__mutmut_40, 
    'x__display_provider_models__mutmut_41': x__display_provider_models__mutmut_41, 
    'x__display_provider_models__mutmut_42': x__display_provider_models__mutmut_42, 
    'x__display_provider_models__mutmut_43': x__display_provider_models__mutmut_43, 
    'x__display_provider_models__mutmut_44': x__display_provider_models__mutmut_44, 
    'x__display_provider_models__mutmut_45': x__display_provider_models__mutmut_45, 
    'x__display_provider_models__mutmut_46': x__display_provider_models__mutmut_46, 
    'x__display_provider_models__mutmut_47': x__display_provider_models__mutmut_47, 
    'x__display_provider_models__mutmut_48': x__display_provider_models__mutmut_48, 
    'x__display_provider_models__mutmut_49': x__display_provider_models__mutmut_49, 
    'x__display_provider_models__mutmut_50': x__display_provider_models__mutmut_50, 
    'x__display_provider_models__mutmut_51': x__display_provider_models__mutmut_51, 
    'x__display_provider_models__mutmut_52': x__display_provider_models__mutmut_52, 
    'x__display_provider_models__mutmut_53': x__display_provider_models__mutmut_53, 
    'x__display_provider_models__mutmut_54': x__display_provider_models__mutmut_54, 
    'x__display_provider_models__mutmut_55': x__display_provider_models__mutmut_55, 
    'x__display_provider_models__mutmut_56': x__display_provider_models__mutmut_56, 
    'x__display_provider_models__mutmut_57': x__display_provider_models__mutmut_57, 
    'x__display_provider_models__mutmut_58': x__display_provider_models__mutmut_58, 
    'x__display_provider_models__mutmut_59': x__display_provider_models__mutmut_59, 
    'x__display_provider_models__mutmut_60': x__display_provider_models__mutmut_60, 
    'x__display_provider_models__mutmut_61': x__display_provider_models__mutmut_61, 
    'x__display_provider_models__mutmut_62': x__display_provider_models__mutmut_62, 
    'x__display_provider_models__mutmut_63': x__display_provider_models__mutmut_63, 
    'x__display_provider_models__mutmut_64': x__display_provider_models__mutmut_64, 
    'x__display_provider_models__mutmut_65': x__display_provider_models__mutmut_65, 
    'x__display_provider_models__mutmut_66': x__display_provider_models__mutmut_66, 
    'x__display_provider_models__mutmut_67': x__display_provider_models__mutmut_67, 
    'x__display_provider_models__mutmut_68': x__display_provider_models__mutmut_68, 
    'x__display_provider_models__mutmut_69': x__display_provider_models__mutmut_69, 
    'x__display_provider_models__mutmut_70': x__display_provider_models__mutmut_70, 
    'x__display_provider_models__mutmut_71': x__display_provider_models__mutmut_71, 
    'x__display_provider_models__mutmut_72': x__display_provider_models__mutmut_72, 
    'x__display_provider_models__mutmut_73': x__display_provider_models__mutmut_73, 
    'x__display_provider_models__mutmut_74': x__display_provider_models__mutmut_74, 
    'x__display_provider_models__mutmut_75': x__display_provider_models__mutmut_75, 
    'x__display_provider_models__mutmut_76': x__display_provider_models__mutmut_76, 
    'x__display_provider_models__mutmut_77': x__display_provider_models__mutmut_77, 
    'x__display_provider_models__mutmut_78': x__display_provider_models__mutmut_78, 
    'x__display_provider_models__mutmut_79': x__display_provider_models__mutmut_79, 
    'x__display_provider_models__mutmut_80': x__display_provider_models__mutmut_80, 
    'x__display_provider_models__mutmut_81': x__display_provider_models__mutmut_81, 
    'x__display_provider_models__mutmut_82': x__display_provider_models__mutmut_82, 
    'x__display_provider_models__mutmut_83': x__display_provider_models__mutmut_83, 
    'x__display_provider_models__mutmut_84': x__display_provider_models__mutmut_84, 
    'x__display_provider_models__mutmut_85': x__display_provider_models__mutmut_85, 
    'x__display_provider_models__mutmut_86': x__display_provider_models__mutmut_86, 
    'x__display_provider_models__mutmut_87': x__display_provider_models__mutmut_87, 
    'x__display_provider_models__mutmut_88': x__display_provider_models__mutmut_88, 
    'x__display_provider_models__mutmut_89': x__display_provider_models__mutmut_89, 
    'x__display_provider_models__mutmut_90': x__display_provider_models__mutmut_90, 
    'x__display_provider_models__mutmut_91': x__display_provider_models__mutmut_91, 
    'x__display_provider_models__mutmut_92': x__display_provider_models__mutmut_92, 
    'x__display_provider_models__mutmut_93': x__display_provider_models__mutmut_93, 
    'x__display_provider_models__mutmut_94': x__display_provider_models__mutmut_94, 
    'x__display_provider_models__mutmut_95': x__display_provider_models__mutmut_95, 
    'x__display_provider_models__mutmut_96': x__display_provider_models__mutmut_96, 
    'x__display_provider_models__mutmut_97': x__display_provider_models__mutmut_97, 
    'x__display_provider_models__mutmut_98': x__display_provider_models__mutmut_98, 
    'x__display_provider_models__mutmut_99': x__display_provider_models__mutmut_99, 
    'x__display_provider_models__mutmut_100': x__display_provider_models__mutmut_100, 
    'x__display_provider_models__mutmut_101': x__display_provider_models__mutmut_101, 
    'x__display_provider_models__mutmut_102': x__display_provider_models__mutmut_102, 
    'x__display_provider_models__mutmut_103': x__display_provider_models__mutmut_103, 
    'x__display_provider_models__mutmut_104': x__display_provider_models__mutmut_104, 
    'x__display_provider_models__mutmut_105': x__display_provider_models__mutmut_105, 
    'x__display_provider_models__mutmut_106': x__display_provider_models__mutmut_106, 
    'x__display_provider_models__mutmut_107': x__display_provider_models__mutmut_107, 
    'x__display_provider_models__mutmut_108': x__display_provider_models__mutmut_108, 
    'x__display_provider_models__mutmut_109': x__display_provider_models__mutmut_109, 
    'x__display_provider_models__mutmut_110': x__display_provider_models__mutmut_110, 
    'x__display_provider_models__mutmut_111': x__display_provider_models__mutmut_111, 
    'x__display_provider_models__mutmut_112': x__display_provider_models__mutmut_112, 
    'x__display_provider_models__mutmut_113': x__display_provider_models__mutmut_113, 
    'x__display_provider_models__mutmut_114': x__display_provider_models__mutmut_114, 
    'x__display_provider_models__mutmut_115': x__display_provider_models__mutmut_115, 
    'x__display_provider_models__mutmut_116': x__display_provider_models__mutmut_116, 
    'x__display_provider_models__mutmut_117': x__display_provider_models__mutmut_117, 
    'x__display_provider_models__mutmut_118': x__display_provider_models__mutmut_118, 
    'x__display_provider_models__mutmut_119': x__display_provider_models__mutmut_119, 
    'x__display_provider_models__mutmut_120': x__display_provider_models__mutmut_120, 
    'x__display_provider_models__mutmut_121': x__display_provider_models__mutmut_121, 
    'x__display_provider_models__mutmut_122': x__display_provider_models__mutmut_122, 
    'x__display_provider_models__mutmut_123': x__display_provider_models__mutmut_123, 
    'x__display_provider_models__mutmut_124': x__display_provider_models__mutmut_124, 
    'x__display_provider_models__mutmut_125': x__display_provider_models__mutmut_125, 
    'x__display_provider_models__mutmut_126': x__display_provider_models__mutmut_126, 
    'x__display_provider_models__mutmut_127': x__display_provider_models__mutmut_127, 
    'x__display_provider_models__mutmut_128': x__display_provider_models__mutmut_128, 
    'x__display_provider_models__mutmut_129': x__display_provider_models__mutmut_129, 
    'x__display_provider_models__mutmut_130': x__display_provider_models__mutmut_130, 
    'x__display_provider_models__mutmut_131': x__display_provider_models__mutmut_131, 
    'x__display_provider_models__mutmut_132': x__display_provider_models__mutmut_132, 
    'x__display_provider_models__mutmut_133': x__display_provider_models__mutmut_133, 
    'x__display_provider_models__mutmut_134': x__display_provider_models__mutmut_134, 
    'x__display_provider_models__mutmut_135': x__display_provider_models__mutmut_135, 
    'x__display_provider_models__mutmut_136': x__display_provider_models__mutmut_136, 
    'x__display_provider_models__mutmut_137': x__display_provider_models__mutmut_137, 
    'x__display_provider_models__mutmut_138': x__display_provider_models__mutmut_138, 
    'x__display_provider_models__mutmut_139': x__display_provider_models__mutmut_139, 
    'x__display_provider_models__mutmut_140': x__display_provider_models__mutmut_140, 
    'x__display_provider_models__mutmut_141': x__display_provider_models__mutmut_141, 
    'x__display_provider_models__mutmut_142': x__display_provider_models__mutmut_142, 
    'x__display_provider_models__mutmut_143': x__display_provider_models__mutmut_143, 
    'x__display_provider_models__mutmut_144': x__display_provider_models__mutmut_144, 
    'x__display_provider_models__mutmut_145': x__display_provider_models__mutmut_145, 
    'x__display_provider_models__mutmut_146': x__display_provider_models__mutmut_146, 
    'x__display_provider_models__mutmut_147': x__display_provider_models__mutmut_147, 
    'x__display_provider_models__mutmut_148': x__display_provider_models__mutmut_148, 
    'x__display_provider_models__mutmut_149': x__display_provider_models__mutmut_149, 
    'x__display_provider_models__mutmut_150': x__display_provider_models__mutmut_150, 
    'x__display_provider_models__mutmut_151': x__display_provider_models__mutmut_151, 
    'x__display_provider_models__mutmut_152': x__display_provider_models__mutmut_152, 
    'x__display_provider_models__mutmut_153': x__display_provider_models__mutmut_153, 
    'x__display_provider_models__mutmut_154': x__display_provider_models__mutmut_154, 
    'x__display_provider_models__mutmut_155': x__display_provider_models__mutmut_155, 
    'x__display_provider_models__mutmut_156': x__display_provider_models__mutmut_156, 
    'x__display_provider_models__mutmut_157': x__display_provider_models__mutmut_157, 
    'x__display_provider_models__mutmut_158': x__display_provider_models__mutmut_158, 
    'x__display_provider_models__mutmut_159': x__display_provider_models__mutmut_159, 
    'x__display_provider_models__mutmut_160': x__display_provider_models__mutmut_160, 
    'x__display_provider_models__mutmut_161': x__display_provider_models__mutmut_161, 
    'x__display_provider_models__mutmut_162': x__display_provider_models__mutmut_162, 
    'x__display_provider_models__mutmut_163': x__display_provider_models__mutmut_163, 
    'x__display_provider_models__mutmut_164': x__display_provider_models__mutmut_164, 
    'x__display_provider_models__mutmut_165': x__display_provider_models__mutmut_165, 
    'x__display_provider_models__mutmut_166': x__display_provider_models__mutmut_166, 
    'x__display_provider_models__mutmut_167': x__display_provider_models__mutmut_167, 
    'x__display_provider_models__mutmut_168': x__display_provider_models__mutmut_168, 
    'x__display_provider_models__mutmut_169': x__display_provider_models__mutmut_169, 
    'x__display_provider_models__mutmut_170': x__display_provider_models__mutmut_170, 
    'x__display_provider_models__mutmut_171': x__display_provider_models__mutmut_171, 
    'x__display_provider_models__mutmut_172': x__display_provider_models__mutmut_172, 
    'x__display_provider_models__mutmut_173': x__display_provider_models__mutmut_173, 
    'x__display_provider_models__mutmut_174': x__display_provider_models__mutmut_174, 
    'x__display_provider_models__mutmut_175': x__display_provider_models__mutmut_175, 
    'x__display_provider_models__mutmut_176': x__display_provider_models__mutmut_176, 
    'x__display_provider_models__mutmut_177': x__display_provider_models__mutmut_177, 
    'x__display_provider_models__mutmut_178': x__display_provider_models__mutmut_178, 
    'x__display_provider_models__mutmut_179': x__display_provider_models__mutmut_179, 
    'x__display_provider_models__mutmut_180': x__display_provider_models__mutmut_180, 
    'x__display_provider_models__mutmut_181': x__display_provider_models__mutmut_181, 
    'x__display_provider_models__mutmut_182': x__display_provider_models__mutmut_182, 
    'x__display_provider_models__mutmut_183': x__display_provider_models__mutmut_183, 
    'x__display_provider_models__mutmut_184': x__display_provider_models__mutmut_184, 
    'x__display_provider_models__mutmut_185': x__display_provider_models__mutmut_185, 
    'x__display_provider_models__mutmut_186': x__display_provider_models__mutmut_186, 
    'x__display_provider_models__mutmut_187': x__display_provider_models__mutmut_187, 
    'x__display_provider_models__mutmut_188': x__display_provider_models__mutmut_188, 
    'x__display_provider_models__mutmut_189': x__display_provider_models__mutmut_189, 
    'x__display_provider_models__mutmut_190': x__display_provider_models__mutmut_190, 
    'x__display_provider_models__mutmut_191': x__display_provider_models__mutmut_191, 
    'x__display_provider_models__mutmut_192': x__display_provider_models__mutmut_192, 
    'x__display_provider_models__mutmut_193': x__display_provider_models__mutmut_193, 
    'x__display_provider_models__mutmut_194': x__display_provider_models__mutmut_194, 
    'x__display_provider_models__mutmut_195': x__display_provider_models__mutmut_195, 
    'x__display_provider_models__mutmut_196': x__display_provider_models__mutmut_196, 
    'x__display_provider_models__mutmut_197': x__display_provider_models__mutmut_197, 
    'x__display_provider_models__mutmut_198': x__display_provider_models__mutmut_198, 
    'x__display_provider_models__mutmut_199': x__display_provider_models__mutmut_199, 
    'x__display_provider_models__mutmut_200': x__display_provider_models__mutmut_200, 
    'x__display_provider_models__mutmut_201': x__display_provider_models__mutmut_201, 
    'x__display_provider_models__mutmut_202': x__display_provider_models__mutmut_202, 
    'x__display_provider_models__mutmut_203': x__display_provider_models__mutmut_203, 
    'x__display_provider_models__mutmut_204': x__display_provider_models__mutmut_204, 
    'x__display_provider_models__mutmut_205': x__display_provider_models__mutmut_205, 
    'x__display_provider_models__mutmut_206': x__display_provider_models__mutmut_206, 
    'x__display_provider_models__mutmut_207': x__display_provider_models__mutmut_207, 
    'x__display_provider_models__mutmut_208': x__display_provider_models__mutmut_208, 
    'x__display_provider_models__mutmut_209': x__display_provider_models__mutmut_209, 
    'x__display_provider_models__mutmut_210': x__display_provider_models__mutmut_210, 
    'x__display_provider_models__mutmut_211': x__display_provider_models__mutmut_211, 
    'x__display_provider_models__mutmut_212': x__display_provider_models__mutmut_212, 
    'x__display_provider_models__mutmut_213': x__display_provider_models__mutmut_213, 
    'x__display_provider_models__mutmut_214': x__display_provider_models__mutmut_214, 
    'x__display_provider_models__mutmut_215': x__display_provider_models__mutmut_215, 
    'x__display_provider_models__mutmut_216': x__display_provider_models__mutmut_216, 
    'x__display_provider_models__mutmut_217': x__display_provider_models__mutmut_217, 
    'x__display_provider_models__mutmut_218': x__display_provider_models__mutmut_218, 
    'x__display_provider_models__mutmut_219': x__display_provider_models__mutmut_219, 
    'x__display_provider_models__mutmut_220': x__display_provider_models__mutmut_220
}
x__display_provider_models__mutmut_orig.__name__ = 'x__display_provider_models'


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
