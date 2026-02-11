"""
Core execution logic
"""
import fcntl
import json
import os
import re
import signal
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


def get_script_command(script_path: Path) -> list[str]:
    """
    Determine the appropriate command to execute a script based on its extension.
    
    Args:
        script_path: Path to the script file
        
    Returns:
        List of command arguments
    """
    suffix = script_path.suffix.lower()
    
    if suffix == '.py':
        return ['python3', str(script_path)]
    elif suffix in ('.sh', '.bash'):
        return ['bash', str(script_path)]
    else:
        return ['bash', str(script_path)]


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
    
    is_benign = run.run_type == "benign"
    start_event = "BENIGN_START" if is_benign else "ATTACK_START"
    end_event = "BENIGN_END" if is_benign else "ATTACK_END"
    
    marker_metadata = {
        "target_ip": env.get("TARGET_IP"),
        "run_type": run.run_type,
        "label": run.label,
    }
    
    logger.info(f"Sending {start_event} marker")
    marker_system.send(
        event=start_event,
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
            click.echo(f"    Executing... (Press Ctrl+C to stop)")
        click.echo()
        
        logger.info(f"Executing script: {run.script}")
        
        script_path = Path(run.script)
        cmd = get_script_command(script_path)
        
        logger.debug(f"Command: {' '.join(cmd)}")
        
        proc = subprocess.Popen(
            cmd,
            env={**os.environ, **env},
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        output_lines = []
        returncode = 0
        user_interrupted = False
        
        # Setup signal handler for user Ctrl+C
        def handle_sigint(signum, frame):
            nonlocal user_interrupted
            user_interrupted = True
            logger.info("User pressed Ctrl+C, forwarding to script...")
            if proc.poll() is None:
                proc.send_signal(signal.SIGINT)
        
        # Register signal handler
        old_handler = signal.signal(signal.SIGINT, handle_sigint)
        
        try:
            if has_duration:
                if proc.stdout:
                    fd = proc.stdout.fileno()
                    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
                    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
                
                with click.progressbar(
                    length=duration_secs,
                    label='    Progress',
                    show_eta=True,
                    show_percent=True,
                ) as bar:
                    start = time.time()
                    while True:
                        elapsed = int(time.time() - start)
                        if elapsed >= duration_secs:
                            break
                        if proc.poll() is not None:
                            break
                        if user_interrupted:
                            break
                        bar.update(min(1, duration_secs - elapsed))
                        time.sleep(1)
                        
                        if proc.stdout:
                            try:
                                while True:
                                    line = proc.stdout.readline()
                                    if not line:
                                        break
                                    output_lines.append(line)
                            except (IOError, BlockingIOError):
                                pass
                    
                    if elapsed < duration_secs and proc.poll() is not None:
                        bar.update(duration_secs - elapsed)
                
                # If duration expired (not user interrupt), send SIGINT
                if not user_interrupted and proc.poll() is None:
                    logger.info("Duration expired, sending SIGINT for graceful shutdown...")
                    proc.send_signal(signal.SIGINT)
                    try:
                        proc.wait(timeout=10)
                        logger.info("Script completed graceful shutdown")
                    except subprocess.TimeoutExpired:
                        logger.warning("Script did not respond to SIGINT, forcing termination")
                        proc.kill()
                        proc.wait()
            else:
                # No duration - run until user stops or script finishes
                while proc.poll() is None:
                    if user_interrupted:
                        break
                        
                    if not proc.stdout:
                        time.sleep(0.1)
                        continue
                        
                    line = proc.stdout.readline()
                    if not line:
                        time.sleep(0.1)
                        continue
                    
                    output_lines.append(line)
                    
                    if line.strip() and not should_filter_line(line):
                        click.echo(f"    {line.rstrip()}")
            
            # Wait for process to finish gracefully
            if proc.poll() is None:
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    logger.warning("Script did not finish in time, forcing termination")
                    proc.kill()
                    proc.wait()
            
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
            
        finally:
            # Restore original signal handler
            signal.signal(signal.SIGINT, old_handler)
        
        stdout = ''.join(output_lines)
        stderr = ""
        
        if has_duration or user_interrupted:
            returncode = proc.returncode if proc.returncode is not None else 0
            # Exit code 130 (128+2) is normal for SIGINT, treat as success
            if returncode < 0 or returncode in (130, 143):
                returncode = 0
        else:
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
    
    logger.info(f"Sending {end_event} marker")
    marker_system.send(
        event=end_event,
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
    Save run metadata with enriched information for benign traffic.
    
    For benign runs, extracts device count, infrastructure configuration,
    and protocol information from environment variables.
    """
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
    
    if run.run_type == "benign":
        env = result.env_effective
        benign_config = {
            "device_count": None,
            "device_range": None,
            "base_ip": env.get("BASE_IP"),
            "protocols": [],
            "infrastructure": {},
        }
        
        if "RANGE_START" in env and "RANGE_END" in env:
            try:
                start = int(env["RANGE_START"])
                end = int(env["RANGE_END"])
                benign_config["device_count"] = end - start + 1
                benign_config["device_range"] = f"{start}-{end}"
            except (ValueError, TypeError):
                pass
        
        if "BROKER_IP" in env:
            benign_config["infrastructure"]["mqtt_broker"] = env["BROKER_IP"]
        if "WEB_SERVER_IP" in env:
            benign_config["infrastructure"]["web_server"] = env["WEB_SERVER_IP"]
        if "DB_HOST" in env:
            benign_config["infrastructure"]["database"] = env["DB_HOST"]
        
        script_name = str(run.script).lower()
        
        if "mqtt" in script_name or "BROKER_IP" in env:
            benign_config["protocols"].append("mqtt")
        
        if "http" in script_name or "WEB_SERVER_IP" in env:
            benign_config["protocols"].append("http")
        
        if "udp" in script_name or "swarm" in script_name.lower() or "device" in script_name.lower():
            benign_config["protocols"].append("udp")
        
        metadata["benign_config"] = benign_config
    
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