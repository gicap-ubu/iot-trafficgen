"""IoT Benign & Attack Traffic Generator"""
import sys
from pathlib import Path
import click
import yaml
from colorama import Fore, Style, init

from . import __version__
from .core import run_scenario
from .interactive import interactive_mode

# Initialize colorama
init(autoreset=True)


@click.group()
@click.version_option(version=__version__, prog_name="iottrafficgen")
def main():
    """
    IoT Benign & Attack Traffic Generator (IoT B_ATG)
    
    A professional framework for generating reproducible IoT traffic patterns
    (benign and attack) in controlled laboratory environments for cybersecurity 
    research and dataset creation.
    
    Features:
      - 63 pre-configured attack scenarios across 7 categories
      - Interactive menu system for easy scenario selection
      - Automated ground-truth labeling with UDP markers
      - Comprehensive logging and error handling
      - Progress tracking and execution monitoring
    
    Quick Start:
      iottrafficgen run                    # Interactive mode
      iottrafficgen list                   # Show all scenarios
      iottrafficgen run scenario.yaml      # Execute specific scenario
    
    For detailed documentation, visit:
      https://github.com/yourusername/iot-trafficgen
    """
    pass


@main.command()
@click.argument(
    "scenario",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=False,
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
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Enable verbose logging (DEBUG level)",
)
@click.option(
    "--quiet", "-q",
    is_flag=True,
    help="Quiet mode - only show errors",
)
def run(scenario: Path, workspace: Path, dry_run: bool, verbose: bool, quiet: bool):
    """
    Execute an IoT attack traffic generation scenario.
    
    \b
    Without SCENARIO argument: Launches interactive menu for scenario selection
    With SCENARIO argument: Executes the specified YAML scenario file
    
    \b
    Examples:
      iottrafficgen run
        → Interactive mode: Browse and select from 63 scenarios
      
      iottrafficgen run scenarios/nmap/01.yaml
        → Execute specific NMAP reconnaissance scenario
      
      iottrafficgen run scenarios/sqli/01.yaml --verbose
        → Execute SQL injection with detailed logging
      
      iottrafficgen run scenarios/bruteforce/01.yaml --dry-run
        → Validate SSH brute force scenario without execution
    
    \b
    Logging Options:
      --verbose: Show DEBUG level logs (detailed execution info)
      --quiet:   Only show errors (minimal output)
      (default): Show INFO level logs (standard output)
    
    \b
    Output Structure:
      runs/<run_id>/
        ├── execution.log       # Detailed execution log
        ├── run_metadata.json   # Structured metadata
        └── outputs/            # Attack-specific outputs
    """
    try:
        # If no scenario provided, enter interactive mode
        if scenario is None:
            selected_scenario = interactive_mode(workspace)
            
            if selected_scenario is None:
                # User exited
                sys.exit(0)
            
            scenario = selected_scenario
        
        click.echo(f"\nLoading scenario: {scenario}")
        click.echo(f"Workspace: {workspace}")
        
        if dry_run:
            click.echo("[DRY RUN] Validating scenario only...")
        
        # Call main execution function with new parameters
        run_scenario(
            scenario_path=scenario,
            workspace=workspace,
            dry_run=dry_run,
            verbose=verbose,
            quiet=quiet,
        )
        
        click.secho("\n[SUCCESS] Scenario completed successfully", fg="green")
        
    except FileNotFoundError as e:
        click.secho(f"[ERROR] {e}", fg="red", err=True)
        sys.exit(1)
    except ValueError as e:
        click.secho(f"[ERROR] Validation error: {e}", fg="red", err=True)
        sys.exit(1)
    except Exception as e:
        click.secho(f"[ERROR] Unexpected error: {e}", fg="red", err=True)
        sys.exit(1)


@main.command(name='list')
@click.option(
    "--workspace",
    type=click.Path(path_type=Path),
    default=Path.cwd(),
    help="Working directory (default: current directory)",
)
@click.option(
    "--category", "-c",
    type=str,
    help="Filter by category (e.g., 'nmap', 'ssh', 'sqli')",
)
@click.option(
    "--count-only",
    is_flag=True,
    help="Only show total count",
)
def list_scenarios(workspace: Path, category: str, count_only: bool):
    """
    List all available IoT attack scenarios.
    
    Displays organized catalog of 63 pre-configured attack scenarios
    across 7 categories: NMAP, SSH Brute Force, SQL Injection,
    Denial of Service, ARP Spoofing, MQTT Injection, and DNS Beaconing.
    
    \b
    Examples:
      iottrafficgen list
        → Show all 63 scenarios organized by category
      
      iottrafficgen list --category nmap
        → Show only NMAP reconnaissance scenarios (30)
      
      iottrafficgen list --category dos
        → Show only Denial of Service scenarios (17)
      
      iottrafficgen list --count-only
        → Display total scenario count only
      
      iottrafficgen list | grep SQL
        → Search for specific attack types (grep-friendly)
    
    \b
    Output includes:
      • Scenario file path (relative to workspace)
      • Full description from YAML metadata
      • Total count per category
    """
    scenarios_dir = workspace / "scenarios"
    
    if not scenarios_dir.exists():
        click.secho("[ERROR] No scenarios directory found", fg="red")
        click.echo(f"Expected: {scenarios_dir}")
        sys.exit(1)
    
    # Scan for scenario categories
    categories_data = {}
    
    for category_dir in sorted(scenarios_dir.iterdir()):
        if not category_dir.is_dir() or category_dir.name.startswith('.'):
            continue
        
        # Apply category filter
        if category and category.lower() not in category_dir.name.lower():
            continue
        
        scenarios = []
        for yaml_file in sorted(category_dir.glob("*.yaml")):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    if data and 'scenario' in data:
                        name = data['scenario'].get('name', 'Unknown')
                        description = data['scenario'].get('description', 'No description')
                        scenarios.append({
                            'file': yaml_file,
                            'name': name,
                            'description': description
                        })
            except Exception:
                # Skip files that can't be read
                continue
        
        if scenarios:
            categories_data[category_dir.name] = scenarios
    
    if not categories_data:
        click.secho("No scenarios found", fg="yellow")
        sys.exit(0)
    
    # Count only mode
    if count_only:
        total = sum(len(scenarios) for scenarios in categories_data.values())
        click.echo(f"Total scenarios: {total}")
        sys.exit(0)
    
    # Display header
    click.echo(f"\n{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}")
    click.echo(f"{Fore.CYAN}  Available Attack Scenarios{Style.RESET_ALL}")
    click.echo(f"{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}\n")
    
    total_count = 0
    
    # Display categories and scenarios
    for cat_name, scenarios in categories_data.items():
        # Category header
        category_title = cat_name.replace('_', ' ').title()
        click.echo(f"{Fore.YELLOW}{category_title}{Style.RESET_ALL} ({len(scenarios)} scenarios)")
        click.echo(f"{Fore.YELLOW}{'-' * 70}{Style.RESET_ALL}")
        
        for scenario in scenarios:
            relative_path = scenario['file'].relative_to(workspace)
            click.echo(f"  {Fore.GREEN}-{Style.RESET_ALL} {relative_path}")
            click.echo(f"    {scenario['description']}")
        
        click.echo()
        total_count += len(scenarios)
    
    # Footer
    click.echo(f"{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}")
    click.echo(f"Total: {Fore.GREEN}{total_count}{Style.RESET_ALL} scenarios across {Fore.GREEN}{len(categories_data)}{Style.RESET_ALL} categories")
    click.echo()


if __name__ == "__main__":
    main()
