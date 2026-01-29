"""
Core execution logic for iottrafficgen
"""
import json
from datetime import datetime
from pathlib import Path

import click

from . import __version__
from .markers import create_marker_system_from_scenario
from .models import Profile, Run, RunResult, Scenario
from .utils import (
    execute_shell_script,
    get_timestamp_utc,
    load_yaml_file,
    validate_scenario_schema,
)


def load_scenario(scenario_path: Path) -> Scenario:
    """
    Load and validate a scenario from YAML file.
    
    Args:
        scenario_path: Path to scenario YAML
        
    Returns:
        Validated Scenario object
    """
    data = load_yaml_file(scenario_path)
    validate_scenario_schema(data)
    return Scenario.from_yaml(scenario_path, data)


def load_profile(profile_path: Path) -> Profile:
    """
    Load a profile from YAML file.
    
    Args:
        profile_path: Path to profile YAML
        
    Returns:
        Profile object
    """
    data = load_yaml_file(profile_path)
    return Profile.from_yaml(data)


def execute_run(
    run: Run,
    workspace: Path,
    marker_system,
    dry_run: bool = False,
) -> RunResult:
    """
    Execute a single run with ground truth markers.
    
    Args:
        run: Run configuration
        workspace: Working directory
        marker_system: MarkerSystem instance for UDP markers
        dry_run: If True, skip actual execution
        
    Returns:
        RunResult with execution details
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_id_unique = f"{run.id}_{timestamp}"
    
    run_dir = workspace / "runs" / run_id_unique
    outputs_dir = run_dir / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    
    env = run.env.copy()
    env["RUN_ID"] = run_id_unique
    env["OUT_DIR"] = str(outputs_dir)
    
    if run.profile:
        if not run.profile.exists():
            raise FileNotFoundError(f"Profile not found: {run.profile}")
        
        profile = load_profile(run.profile)
        env["TOOL_ARGS"] = profile.tool_args
        click.echo(f"    → Profile: {run.profile.name} ({profile.name})")
    
    click.echo(f"    → Script: {run.script}")
    click.echo(f"    → Run ID: {run_id_unique}")
    click.echo(f"    → Output dir: {outputs_dir}")
    if "TARGET_IP" in env:
        click.echo(f"    → Target: {env['TARGET_IP']}")
    if "TOOL_ARGS" in env:
        click.echo(f"    → Tool args: {env['TOOL_ARGS']}")
    
    marker_metadata = {
        "target_ip": env.get("TARGET_IP"),
        "run_type": run.run_type,
        "label": run.label,
    }
    
    marker_system.send(
        event="ATTACK_START",
        attack_id=run_id_unique,
        attack_name=run.label or run.id,
        metadata=marker_metadata,
    )
    
    start_time = datetime.utcnow()
    start_time_str = get_timestamp_utc()
    
    if dry_run:
        click.echo(f"    → [DRY RUN] Would execute: {run.script}")
        returncode = 0
        stdout = "[dry run - no output]"
        stderr = ""
    else:
        result = execute_shell_script(run.script, env)
        returncode = result.returncode
        stdout = result.stdout
        stderr = result.stderr
        
        if stdout:
            click.echo(stdout, nl=False)
        
        if stderr and returncode != 0:
            click.secho(stderr, fg="yellow", nl=False)
    
    end_time = datetime.utcnow()
    end_time_str = get_timestamp_utc()
    duration = (end_time - start_time).total_seconds()
    
    marker_metadata.update({
        "returncode": returncode,
        "duration_s": duration,
    })
    
    marker_system.send(
        event="ATTACK_END",
        attack_id=run_id_unique,
        attack_name=run.label or run.id,
        metadata=marker_metadata,
    )
    
    result_obj = RunResult(
        run_id=run_id_unique,
        start_time_utc=start_time_str,
        end_time_utc=end_time_str,
        duration_s=duration,
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
        env_effective=env,
        outputs_dir=outputs_dir,
    )
    
    save_run_metadata(run, result_obj, run_dir)
    
    return result_obj


def save_run_metadata(run: Run, result: RunResult, run_dir: Path) -> None:
    """
    Save metadata for a single run.
    
    Args:
        run: Run configuration
        result: Execution result
        run_dir: Directory to save metadata
    """
    metadata = {
        "tool": "iottrafficgen",
        "version": __version__,
        "run_id": result.run_id,
        "run_id_base": run.id,
        "type": run.run_type,
        "label": run.label,
        "script": str(run.script),
        "profile": str(run.profile) if run.profile else None,
        "start_time_utc": result.start_time_utc,
        "end_time_utc": result.end_time_utc,
        "duration_s": result.duration_s,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "env_effective": result.env_effective,
        "outputs_dir": str(result.outputs_dir),
    }
    
    metadata_file = run_dir / "run_metadata.json"
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    click.echo(f"    → Metadata: {metadata_file}")


def save_scenario_metadata(
    scenario: Scenario,
    results: list[RunResult],
    workspace: Path,
) -> None:
    """
    Save overall scenario metadata.
    
    Args:
        scenario: Scenario configuration
        results: List of run results
        workspace: Working directory
    """
    metadata = {
        "tool": "iottrafficgen",
        "version": __version__,
        "scenario": {
            "name": scenario.metadata.name,
            "description": scenario.metadata.description,
        },
        "generated_at_utc": get_timestamp_utc(),
        "runs": [
            {
                "id": r.run_id,
                "start_time_utc": r.start_time_utc,
                "end_time_utc": r.end_time_utc,
                "duration_s": r.duration_s,
                "returncode": r.returncode,
                "outputs_dir": str(r.outputs_dir),
            }
            for r in results
        ],
    }
    
    metadata_dir = workspace / ".iottrafficgen"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    metadata_file = metadata_dir / f"scenario_metadata_{timestamp}.json"
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    click.echo(f"\n📊 Scenario metadata: {metadata_file}")


def run_scenario(
    scenario_path: Path,
    workspace: Path,
    dry_run: bool = False,
) -> None:
    """
    Execute a traffic generation scenario.
    
    Args:
        scenario_path: Path to scenario YAML file
        workspace: Working directory for outputs
        dry_run: If True, only validate without executing
    """
    click.echo(f"Loading scenario: {scenario_path}")
    
    scenario_data = load_yaml_file(scenario_path)
    validate_scenario_schema(scenario_data)
    scenario = Scenario.from_yaml(scenario_path, scenario_data)
    
    marker_system = create_marker_system_from_scenario(scenario_data)
    
    click.echo(f"Scenario: {scenario.metadata.name}")
    click.echo(f"Description: {scenario.metadata.description}")
    click.echo(f"Runs: {len(scenario.runs)}")
    click.echo(f"Workspace: {workspace}")
    
    scenario_markers = scenario_data.get("scenario", {}).get("markers", {})
    if scenario_markers.get("enabled", True):
        marker_host = scenario_markers.get("host", "127.0.0.1")
        marker_port = scenario_markers.get("port", 55556)
        click.echo(f"Ground truth markers: enabled → {marker_host}:{marker_port}")
    else:
        click.echo("Ground truth markers: disabled")
    
    click.echo()
    
    if dry_run:
        click.secho("[DRY RUN MODE - No scripts will be executed]", fg="yellow")
        click.echo()
    
    results = []
    for i, run in enumerate(scenario.runs, 1):
        click.echo(f"[{i}/{len(scenario.runs)}] Run: {run.id} ({run.run_type})")
        
        try:
            result = execute_run(run, workspace, marker_system, dry_run)
            results.append(result)
            
            if result.returncode == 0:
                click.secho(f"    ✓ Success (duration: {result.duration_s:.2f}s)\n", fg="green")
            else:
                click.secho(f"    ✗ Failed with code {result.returncode}\n", fg="red")
        
        except Exception as e:
            click.secho(f"    ✗ Error: {e}\n", fg="red")
            raise
    
    if not dry_run:
        save_scenario_metadata(scenario, results, workspace)