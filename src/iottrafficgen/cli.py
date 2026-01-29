"""
Command-line interface for iottrafficgen
"""
import sys
from pathlib import Path

import click

from . import __version__
from .core import run_scenario


@click.group()
@click.version_option(version=__version__, prog_name="iottrafficgen")
def main():
    """
    iottrafficgen - Reproducible IoT traffic generation
    
    A framework for generating reproducible IoT traffic in controlled
    laboratory environments for cybersecurity research.
    """
    pass


@main.command()
@click.argument(
    "scenario",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--workspace",
    type=click.Path(path_type=Path),
    default=Path.cwd(),
    help="Working directory for outputs (default: current directory)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Validate scenario without executing scripts",
)
def run(scenario: Path, workspace: Path, dry_run: bool):
    """
    Execute a traffic generation scenario from a YAML file.
    
    SCENARIO: Path to the scenario YAML file
    
    Example:
        iottrafficgen run scenarios/example_scenario.yaml
    """
    try:
        click.echo(f"Loading scenario: {scenario}")
        click.echo(f"Workspace: {workspace}")
        
        if dry_run:
            click.echo("[DRY RUN] Validating scenario only...")
        
        # Llamar a la función principal de ejecución
        run_scenario(
            scenario_path=scenario,
            workspace=workspace,
            dry_run=dry_run,
        )
        
        click.secho("✓ Scenario completed successfully", fg="green")
        
    except FileNotFoundError as e:
        click.secho(f"✗ Error: {e}", fg="red", err=True)
        sys.exit(1)
    except ValueError as e:
        click.secho(f"✗ Validation error: {e}", fg="red", err=True)
        sys.exit(1)
    except Exception as e:
        click.secho(f"✗ Unexpected error: {e}", fg="red", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()