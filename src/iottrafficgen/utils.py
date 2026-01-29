"""
Utility functions for iottrafficgen
"""
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


def get_timestamp_utc() -> str:
    """Get current UTC timestamp in ISO format"""
    return datetime.utcnow().isoformat() + "Z"


def get_timestamp_unix() -> int:
    """Get current Unix timestamp"""
    return int(datetime.utcnow().timestamp())


def load_yaml_file(path: Path) -> dict[str, Any]:
    """
    Load and parse a YAML file.
    
    Args:
        path: Path to YAML file
        
    Returns:
        Parsed YAML content as dictionary
        
    Raises:
        FileNotFoundError: If file doesn't exist
        yaml.YAMLError: If file is not valid YAML
    """
    if not path.exists():
        raise FileNotFoundError(f"YAML file not found: {path}")
    
    with open(path, "r", encoding="utf-8") as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {path}: {e}")


def validate_scenario_schema(data: dict[str, Any]) -> None:
    """
    Validate basic scenario YAML structure.
    
    Args:
        data: Parsed YAML data
        
    Raises:
        ValueError: If schema is invalid
    """
    if "scenario" not in data:
        raise ValueError("Missing required key 'scenario'")
    
    scenario = data["scenario"]
    if "name" not in scenario:
        raise ValueError("Scenario must have 'name' field")
    
    if "runs" not in data:
        raise ValueError("Missing required key 'runs'")
    
    runs = data["runs"]
    if not isinstance(runs, list):
        raise ValueError("'runs' must be a list")
    
    if len(runs) == 0:
        raise ValueError("Scenario must have at least one run")
    
    # Validate each run
    for i, run in enumerate(runs):
        if "id" not in run:
            raise ValueError(f"Run {i} missing required 'id' field")
        if "script" not in run:
            raise ValueError(f"Run {i} missing required 'script' field")
        if "type" not in run:
            raise ValueError(f"Run {i} missing required 'type' field")


def execute_shell_script(
    script_path: Path,
    env_vars: dict[str, str],
    timeout: int | None = None,
) -> subprocess.CompletedProcess:
    """
    Execute a shell script with environment variables.
    
    Args:
        script_path: Path to script
        env_vars: Environment variables to pass
        timeout: Optional timeout in seconds
        
    Returns:
        CompletedProcess with stdout, stderr, returncode
    """
    import os
    
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")
    
    # Make script executable
    script_path.chmod(0o755)
    
    # Prepare environment
    env = os.environ.copy()
    env.update({str(k): str(v) for k, v in env_vars.items()})
    
    # Execute (check=False to capture errors without raising)
    result = subprocess.run(
        [str(script_path)],
        capture_output=True,
        text=True,
        check=False,
        env=env,
        timeout=timeout,
    )
    
    return result