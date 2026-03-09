"""CLI commands for md-evals."""

import typer

app = typer.Typer(
    name="md-evals",
    help="Evaluate AI skills with Control vs Treatment testing",
)


@app.command()
def version():
    """Show version."""
    from md_evals import __version__
    typer.echo(f"md-evals {__version__}")
