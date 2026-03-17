"""CLI commands for md-evals."""

import asyncio
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
from md_evals.models import LinterConfig
from md_evals.precheck import PreCheckEngine
from md_evals.providers.github_models import GitHubModelsProvider
from md_evals.reporter import Reporter
from md_evals.rubric import RubricLoader, RubricNotFoundError, RubricValidationError
from md_evals.provider_registry import ProviderRegistry

logger = logging.getLogger(__name__)

app = typer.Typer(
    name="md-evals",
    help="Evaluate AI skills with Control vs Treatment testing",
    add_completion=False
)
console = Console()


def _print_github_auth_help() -> None:
    """Print actionable GitHub Models authentication help."""
    console.print("\n[yellow]GitHub Models auth preflight (priority order):[/yellow]")
    console.print("1. Preferred: set [bold]GITHUB_TOKEN[/bold] in your shell or .env")
    console.print("   [dim]export GITHUB_TOKEN=github_pat_...[/dim]")
    console.print("2. Fallback: use GitHub CLI token from [bold]gh auth login[/bold]")
    console.print("   [dim]gh auth login && gh auth token[/dim]")
    console.print("3. Run smoke preflight")
    console.print("   [dim]md-evals smoke --provider github-models --config examples/eval_with_github_models.yaml[/dim]")


@app.command()
def version():
    """Show version."""
    console.print(f"md-evals {__version__}")


@app.command()
def check(
    skill_path: Annotated[str, typer.Argument(help="Path to SKILL.md file to check")] = "SKILL.md",
    rubric: Annotated[Optional[str], typer.Option("--rubric", "-r", help="Path to rubric.yaml")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Show detailed check results")] = False,
):
    """Run deterministic pre-check on a SKILL.md file (no LLM, no cost)."""
    # Load rubric via resolution chain
    try:
        rubric_config = RubricLoader.resolve(rubric)
    except RubricNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)
    except RubricValidationError as e:
        console.print(f"[red]Invalid rubric: {e}[/red]")
        raise typer.Exit(code=1)

    # Run pre-check
    engine = PreCheckEngine(rubric_config)
    result = engine.run(skill_path)

    # Print results
    if result.passed:
        console.print(f"[green]✓ {skill_path} — Pre-check PASSED ({result.checks_run} checks, {len(result.findings)} findings, {result.duration_ms}ms)[/green]")
    else:
        error_count = sum(1 for f in result.findings if f.severity == "error")
        warn_count = sum(1 for f in result.findings if f.severity == "warning")
        console.print(f"[red]✗ {skill_path} — Pre-check FAILED ({result.checks_run} checks, {len(result.findings)} findings, {result.duration_ms}ms)[/red]")

    # Show findings
    if result.findings:
        for finding in result.findings:
            severity_color = {"error": "red", "warning": "yellow", "info": "blue"}.get(finding.severity, "white")
            line_info = f" (line {finding.line})" if finding.line else ""
            console.print(f"  [{severity_color}][{finding.severity.upper()}][/{severity_color}] {finding.message}{line_info}")

    # Exit code
    raise typer.Exit(code=0 if result.passed else 2)


@app.command()
def init(
    directory: Annotated[str, typer.Argument(help="Directory to initialize")] = ".",
    force: Annotated[bool, typer.Option("--force", "-f", help="Overwrite existing files")] = False,
):
    """Scaffold eval.yaml and SKILL.md template."""
    directory_path = Path(directory)
    
    # Create directory if it doesn't exist
    directory_path.mkdir(parents=True, exist_ok=True)
    
    # Check for existing files
    eval_yaml = directory_path / "eval.yaml"
    skill_md = directory_path / "SKILL.md"
    
    if eval_yaml.exists() and not force:
        console.print("[yellow]eval.yaml already exists. Use --force to overwrite.[/yellow]")
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
    
    # Create rubric.yaml
    rubric_yaml = directory_path / "rubric.yaml"
    if rubric_yaml.exists() and not force:
        console.print("[yellow]rubric.yaml already exists. Use --force to overwrite.[/yellow]")
    else:
        # Copy default rubric with comments
        default_rubric_path = RubricLoader.BUILTIN_PATH
        rubric_content = default_rubric_path.read_text(encoding="utf-8")
        rubric_yaml.write_text(rubric_content)
        console.print(f"[green]Created {rubric_yaml}[/green]")
    
    # Create results directory
    results_dir = directory_path / "results"
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
    rubric: Annotated[Optional[str], typer.Option("--rubric", "-r", help="Path to rubric.yaml")] = None,
    count: Annotated[int, typer.Option("--count", help="Number of repetitions")] = 1,
    workers: Annotated[int, typer.Option("-n", help="Number of parallel workers")] = 1,
    output: Annotated[str, typer.Option("--output", "-o", help="Output format")] = "table",
    no_lint: Annotated[bool, typer.Option("--no-lint", help="Skip linting")] = False,
    no_pre_check: Annotated[bool, typer.Option("--no-pre-check", help="Skip pre-check phase")] = False,
    force: Annotated[bool, typer.Option("--force", help="Run LLM eval even on pre-check errors")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Verbose output")] = False,
    debug: Annotated[bool, typer.Option("--debug", help="Enable debug logging for provider initialization")] = False,
    collect_usage_metrics: Annotated[Optional[bool], typer.Option("--collect-usage-metrics/--no-collect-usage-metrics", help="Collect extended usage metrics (cost + context)")] = None,
    pipeline: Annotated[Optional[bool], typer.Option("--pipeline/--no-pipeline", help="Force pipeline mode on/off")] = None,
    probe: Annotated[Optional[str], typer.Option("--probe", help="Comma-separated probe names (e.g., dimension,edge-case)")] = None,
):
    """Run evaluations with support for GitHub Models and other providers."""
    # Configure logging if debug is enabled
    if debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format="[%(levelname)s] %(name)s: %(message)s"
        )
        logger.debug("Debug logging enabled")
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
    
    # Resolve usage metrics flag (CLI > YAML > default)
    if collect_usage_metrics is not None:
        # CLI flag was explicitly passed — takes precedence
        config_obj.output.include_usage_metrics = collect_usage_metrics
    # else: keep YAML value (or default False)

    # ── Pipeline mode detection ──
    use_pipeline = False
    if pipeline is True:
        use_pipeline = True
    elif pipeline is False:
        use_pipeline = False
    elif config_obj.pipeline and isinstance(config_obj.pipeline, dict) and config_obj.pipeline.get("enabled", False):
        use_pipeline = True

    if use_pipeline:
        from md_evals.pipeline.runner import PipelineRunner
        from md_evals.pipeline.config import PipelineConfig

        # Load rubric
        try:
            rubric_config = RubricLoader.resolve(rubric)
        except (RubricNotFoundError, RubricValidationError) as e:
            console.print(f"[red]Rubric error: {e}[/red]")
            raise typer.Exit(code=1)

        # Build pipeline config from YAML dict or defaults
        pipeline_dict = config_obj.pipeline if isinstance(config_obj.pipeline, dict) else {}
        if probe:
            pipeline_dict["probes"] = [p.strip() for p in probe.split(",")]
        pipeline_config = PipelineConfig(**{k: v for k, v in pipeline_dict.items() if k != "enabled"})

        # Find skill path from treatments
        skill_path = None
        for treatment_cfg in config_obj.treatments.values():
            if treatment_cfg.skill_path:
                skill_path = treatment_cfg.skill_path
                break

        if not skill_path:
            console.print("[red]No skill_path found in treatments for pipeline mode.[/red]")
            raise typer.Exit(code=1)

        console.print("[cyan]Running in pipeline mode...[/cyan]")
        runner = PipelineRunner(config=config_obj, rubric=rubric_config, pipeline_config=pipeline_config)

        try:
            result = runner.run_sync(skill_path)
        except Exception as e:
            console.print(f"[red]Pipeline error: {e}[/red]")
            raise typer.Exit(code=3)

        # Print pipeline results
        console.print(f"\n[bold]Pipeline Result: {result.skill_path}[/bold]")
        console.print(f"  Overall Grade: [bold]{result.overall_grade}[/bold]  Score: {result.overall_score:.2f}")
        if result.dimensions:
            for dim in result.dimensions:
                console.print(f"  {dim.dimension}: {dim.score:.2f} ({dim.grade}) weight={dim.weight:.2f}")

        exit_code = 0 if result.overall_grade in ("S", "A", "B") else 4
        raise typer.Exit(code=exit_code)

    # Pre-check phase (before LLM eval)
    if not no_pre_check:
        try:
            rubric_config = RubricLoader.resolve(rubric)
        except (RubricNotFoundError, RubricValidationError) as e:
            console.print(f"[red]Rubric error: {e}[/red]")
            raise typer.Exit(code=1)

        pc_engine = PreCheckEngine(rubric_config)
        # Run pre-check on all skill files
        skill_files = set()
        for treatment_cfg in config_obj.treatments.values():
            if treatment_cfg.skill_path:
                skill_files.add(treatment_cfg.skill_path)

        pre_check_failed = False
        for skill_file in skill_files:
            pc_result = pc_engine.run(skill_file)
            if not pc_result.passed:
                console.print(f"[yellow]Pre-check findings for {skill_file}:[/yellow]")
                for finding in pc_result.findings:
                    sev_color = {"error": "red", "warning": "yellow", "info": "blue"}.get(finding.severity, "white")
                    console.print(f"  [{sev_color}][{finding.severity.upper()}][/{sev_color}] {finding.message}")
                pre_check_failed = True
            elif pc_result.findings:  # passed but has warnings
                console.print(f"[yellow]Pre-check warnings for {skill_file}:[/yellow]")
                for finding in pc_result.findings:
                    if finding.severity == "warning":
                        console.print(f"  [yellow][WARNING][/yellow] {finding.message}")

        if pre_check_failed and not force:
            console.print("[red]Pre-check failed. Use --force to run LLM eval anyway, or --no-pre-check to skip.[/red]")
            raise typer.Exit(code=2)
        elif pre_check_failed and force:
            console.print("[yellow]Pre-check failed but --force specified. Continuing with LLM eval...[/yellow]")

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
        logger.debug("LLM adapter initialized successfully")
    except Exception as e:
        # Enhanced error message for GitHub Models authentication
        error_msg = str(e).lower()
        if "github" in error_msg and "token" in error_msg:
            console.print(f"[red]Authentication Error: {e}[/red]")
            _print_github_auth_help()
            console.print("[dim]Token generation: https://github.com/settings/tokens[/dim]")
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
            _print_github_auth_help()
            console.print("[dim]Token generation: https://github.com/settings/tokens[/dim]")
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


@app.command()
def smoke(
    config: Annotated[str, typer.Option("--config", "-c", help="Config file path to validate")] = "eval.yaml",
    provider: Annotated[str, typer.Option("--provider", "-p", help="Provider to preflight")] = "github-models",
):
    """Run local preflight checks without calling provider APIs."""
    checks_ok = True
    console.print("[cyan]Running smoke preflight checks...[/cyan]")

    # Check provider registration
    try:
        ProviderRegistry.get(provider)
        console.print(f"[green]PASS[/green] Provider registered: {provider}")
    except ValueError as e:
        checks_ok = False
        console.print(f"[red]FAIL[/red] Provider not available: {e}")

    # Check config parsing
    config_path = Path(config)
    if not config_path.exists():
        checks_ok = False
        console.print(f"[red]FAIL[/red] Config file not found: {config}")
    else:
        try:
            ConfigLoader.load(str(config_path))
            console.print(f"[green]PASS[/green] Config valid: {config}")
        except ConfigLoaderError as e:
            checks_ok = False
            console.print(f"[red]FAIL[/red] Invalid config: {e}")

    # Auth preflight for GitHub Models
    if provider.lower().replace("_", "-") in {"github-models", "github models"}:
        token, source = GitHubModelsProvider.resolve_token_source()
        if token:
            source_label = "GITHUB_TOKEN" if source == "env" else "gh auth token" if source == "gh" else source
            console.print(f"[green]PASS[/green] GitHub auth token available via: {source_label}")
        else:
            checks_ok = False
            console.print("[red]FAIL[/red] No GitHub auth token found")
            _print_github_auth_help()

    if checks_ok:
        console.print("[bold green]Smoke preflight passed.[/bold green]")
        raise typer.Exit(code=0)

    console.print("[bold red]Smoke preflight failed.[/bold red]")
    raise typer.Exit(code=1)


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


# ── Plugins subcommand ──

plugins_app = typer.Typer(name="plugins", help="Manage probes and detectors")
app.add_typer(plugins_app)


@plugins_app.command("list")
def plugins_list():
    """List available probes and detectors."""
    from md_evals.pipeline.plugins import discover_probes, discover_detectors

    probes = discover_probes()
    detectors = discover_detectors()

    table = Table(title="Available Probes", show_header=True, header_style="bold")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Source", style="green")

    from md_evals.pipeline.plugins import BUILTIN_PROBES
    for name in probes:
        source = "built-in" if name in BUILTIN_PROBES else "plugin"
        table.add_row(name, "probe", source)

    console.print(table)

    table2 = Table(title="Available Detectors", show_header=True, header_style="bold")
    table2.add_column("Name", style="cyan")
    table2.add_column("Type", style="magenta")
    table2.add_column("Source", style="green")

    from md_evals.pipeline.plugins import BUILTIN_DETECTORS
    for name in detectors:
        source = "built-in" if name in BUILTIN_DETECTORS else "plugin"
        table2.add_row(name, "detector", source)

    console.print(table2)


if __name__ == "__main__":
    app()
