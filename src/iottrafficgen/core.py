"""
Core execution logic
"""
import fcntl
import json
import os
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import click

from . import __version__
from .errors import (
    IoTTrafficGenError,
    PermissionError as IoTPermissionError,
    PlaceholderNotConfiguredError,
    ProfileNotFoundError,
    ToolNotInstalledError,
    check_tool_installed,
    detect_placeholders,
    get_install_hint,
    validate_script_executable,
)
from .logger import get_logger
from .markers import create_marker_system_from_scenario
from .models import Profile, Run, RunResult, Scenario
from .utils import (
    execute_shell_script,
    get_timestamp_utc,
    load_yaml_file,
    validate_scenario_schema,
)

# Patrones de líneas a filtrar del output
NOISE_PATTERNS = [
    r'https?://github\.com',
    r'^\s*$',
]

def should_filter_line(line: str) -> bool:
    """Check if a line should be filtered from output."""
    for pattern in NOISE_PATTERNS:
        if re.search(pattern, line, re.IGNORECASE):
            return True
    return False


def load_scenario(scenario_path: Path) -> Scenario:
    """
    Load and validate a scenario from YAML file.
    
    Args:
        scenario_path: Path to scenario YAML
        
    Returns:
        Validated Scenario object
    """
    logger = get_logger()
    logger.debug(f"Loading scenario: {scenario_path}")
    
    data = load_yaml_file(scenario_path)
    validate_scenario_schema(data)
    
    logger.debug("Scenario validation passed")
    return Scenario.from_yaml(scenario_path, data)


def load_profile(profile_path: Path) -> Profile:
    """
    Load a profile from YAML file.
    
    Args:
        profile_path: Path to profile YAML
        
    Returns:
        Profile object
    """
    logger = get_logger()
    logger.debug(f"Loading profile: {profile_path}")
    
    if not profile_path.exists():
        raise ProfileNotFoundError(profile_path)
    
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
    logger = get_logger()
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_id_unique = f"{run.id}_{timestamp}"
    
    logger.info(f"Preparing run: {run_id_unique}")
    
    run_dir = workspace / "runs" / run_id_unique
    outputs_dir = run_dir / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    
    from .logger import setup_logging
    if not dry_run:
        log_file = run_dir / "execution.log"
        logger = setup_logging(log_dir=run_dir, verbose=True, quiet=False)
        logger.info(f"Logging to: {log_file}")
    
    env = run.env.copy()
    env["RUN_ID"] = run_id_unique
    env["OUT_DIR"] = str(outputs_dir)
    
    placeholders = detect_placeholders(env)
    if placeholders:
        raise PlaceholderNotConfiguredError(placeholders, run.script)
    
    validate_script_executable(run.script)
    
    if run.profile:
        profile = load_profile(run.profile)
        env["TOOL_ARGS"] = profile.tool_args
        click.echo(f"    → Profile: {run.profile.name} ({profile.name})")
        logger.debug(f"Loaded profile: {profile.name}")
    
    click.echo(f"    → Script: {run.script}")
    click.echo(f"    → Run ID: {run_id_unique}")
    click.echo(f"    → Output dir: {outputs_dir}")
    
    if "TARGET_IP" in env:
        click.echo(f"    → Target: {env['TARGET_IP']}")
    if "TOOL_ARGS" in env:
        click.echo(f"    → Tool args: {env['TOOL_ARGS']}")
    
    logger.debug(f"Environment variables: {json.dumps(env, indent=2)}")
    
    marker_metadata = {
        "target_ip": env.get("TARGET_IP"),
        "run_type": run.run_type,
        "label": run.label,
    }
    
    logger.info("Sending ATTACK_START marker")
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
        logger.info("[DRY RUN] Skipping execution")
        returncode = 0
        stdout = "[dry run - no output]"
        stderr = ""
    else:
        # Check if we have a known duration
        duration_str = env.get('DURATION_SECONDS')
        has_duration = False
        duration_secs = 0
        
        if duration_str:
            try:
                duration_secs = int(duration_str)
                has_duration = True
            except (ValueError, TypeError):
                pass
        
        click.echo()
        if has_duration:
            click.echo(f"    Executing (duration: {duration_secs}s)...")
        else:
            click.echo(f"    Executing...")
        click.echo()
        
        logger.info(f"Executing script: {run.script}")
        
        proc = subprocess.Popen(
            ['bash', str(run.script)],
            env={**os.environ, **env},
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        output_lines = []
        returncode = 0
        
        if has_duration:
            # Configurar stdout como no bloqueante
            if proc.stdout:
                fd = proc.stdout.fileno()
                fl = fcntl.fcntl(fd, fcntl.F_GETFL)
                fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
            
            with click.progressbar(
                length=duration_secs,
                label='    Progress',
                show_eta=True,
                show_percent=True,
                bar_template='    %(label)s [%(bar)s] %(info)s',
                fill_char='━',
                empty_char='─'
            ) as bar:
                elapsed = 0
                while proc.poll() is None and elapsed < duration_secs:
                    time.sleep(1)
                    elapsed += 1
                    bar.update(1)
                    
                    # Leer output disponible sin bloquear
                    if proc.stdout:
                        try:
                            while True:
                                line = proc.stdout.readline()
                                if not line:
                                    break
                                output_lines.append(line)
                        except (IOError, BlockingIOError):
                            pass
                
                # Si terminó antes, completar la barra
                if elapsed < duration_secs and proc.poll() is not None:
                    bar.update(duration_secs - elapsed)
            
            # Terminar proceso si sigue corriendo después del timeout
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
            
            # Para procesos terminados por timeout, consideramos éxito (0)
            returncode = proc.returncode if proc.returncode is not None else 0
            # Si fue terminado por señal (negativo) después del timeout, es éxito
            if returncode < 0:
                returncode = 0
        else:
            # Sin duración: mostrar output en tiempo real, filtrado
            while proc.poll() is None:
                if not proc.stdout:
                    time.sleep(0.1)
                    continue
                    
                line = proc.stdout.readline()
                if not line:
                    time.sleep(0.1)
                    continue
                
                output_lines.append(line)
                
                # Mostrar línea si no es ruido
                if line.strip() and not should_filter_line(line):
                    click.echo(f"    {line.rstrip()}")
        
        # Leer output restante
        if proc.stdout:
            try:
                remaining = proc.stdout.read()
                if remaining:
                    output_lines.append(remaining)
                    if not has_duration:
                        for line in remaining.splitlines():
                            if line.strip() and not should_filter_line(line):
                                click.echo(f"    {line}")
            except (IOError, BlockingIOError, TypeError):
                pass
        
        stdout = ''.join(output_lines)
        stderr = ""
        
        # Solo asignar returncode si no fue ya asignado (caso timeout)
        if not has_duration:
            returncode = proc.returncode if proc.returncode is not None else 0
        
        logger.debug(f"Script exit code: {returncode}")
        
        if returncode != 0:
            logger.warning(f"Script failed with exit code {returncode}")
    
    end_time = datetime.utcnow()
    end_time_str = get_timestamp_utc()
    duration = (end_time - start_time).total_seconds()
    
    logger.info(f"Execution completed in {duration:.2f}s with code {returncode}")
    
    marker_metadata.update({
        "returncode": returncode,
        "duration_s": duration,
    })
    
    logger.info("Sending ATTACK_END marker")
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
    logger = get_logger()
    
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
    logger.debug(f"Saved metadata: {metadata_file}")


def save_scenario_metadata(
    scenario: Scenario,
    results: list[RunResult],
    workspace: Path,
) -> None:
    logger = get_logger()
    
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
    
    click.echo(f"\n[METADATA] Scenario metadata: {metadata_file}")
    logger.info(f"Saved scenario metadata: {metadata_file}")


def run_scenario(
    scenario_path: Path,
    workspace: Path,
    dry_run: bool = False,
    verbose: bool = False,
    quiet: bool = False,
) -> None:
    from .logger import setup_logging
    
    logger = setup_logging(log_dir=None, verbose=verbose, quiet=quiet)
    
    logger.info(f"iottrafficgen v{__version__}")
    logger.info(f"Loading scenario: {scenario_path}")
    
    click.echo(f"Loading scenario: {scenario_path}")
    
    try:
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
            logger.info(f"Markers enabled: {marker_host}:{marker_port}")
        else:
            click.echo("Ground truth markers: disabled")
            logger.info("Markers disabled")
        
        click.echo()
        
        if dry_run:
            click.secho("[DRY RUN MODE - No scripts will be executed]", fg="yellow")
            logger.info("DRY RUN mode enabled")
            click.echo()
        
        results = []
        for i, run in enumerate(scenario.runs, 1):
            click.echo(f"[{i}/{len(scenario.runs)}] Run: {run.id} ({run.run_type})")
            logger.info(f"Starting run {i}/{len(scenario.runs)}: {run.id}")
            
            result = execute_run(run, workspace, marker_system, dry_run)
            results.append(result)
            
            if result.returncode == 0:
                click.secho(f"    [OK] Completed in {result.duration_s:.2f}s\n", fg="green")
                logger.info(f"Run completed successfully in {result.duration_s:.2f}s")
            else:
                click.secho(f"    [FAILED] Exit code {result.returncode}\n", fg="red")
                logger.error(f"Run failed with exit code {result.returncode}")
        
        if not dry_run:
            save_scenario_metadata(scenario, results, workspace)
        
        logger.info("Scenario execution completed")
    
    except IoTTrafficGenError as e:
        logger.error(f"Error: {e.message}")
        e.display()
        raise SystemExit(1)
    
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise