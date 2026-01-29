"""
Data models for iottrafficgen
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ScenarioMetadata:
    """Metadata about a scenario"""
    name: str
    description: str


@dataclass
class Profile:
    """Configuration profile loaded from YAML"""
    tool: str
    name: str
    description: str
    tool_args: str
    
    @classmethod
    def from_yaml(cls, data: dict[str, Any]) -> "Profile":
        """Create Profile from parsed YAML data"""
        profile = data.get("profile", {})
        return cls(
            tool=profile.get("tool", "unknown"),
            name=profile.get("name", "unknown"),
            description=profile.get("description", ""),
            tool_args=profile.get("tool_args", ""),
        )


@dataclass
class Run:
    """A single execution run within a scenario"""
    id: str
    script: Path
    run_type: str
    label: str | None = None
    profile: Path | None = None
    env: dict[str, str] = field(default_factory=dict)
    
    @classmethod
    def from_yaml(cls, data: dict[str, Any], scenario_dir: Path) -> "Run":
        """Create Run from parsed YAML data"""
        # Resolve script path relative to scenario file
        script_path = scenario_dir / data["script"]
        
        # Resolve profile path if present
        profile_path = None
        if "profile" in data:
            profile_path = scenario_dir / data["profile"]
        
        return cls(
            id=data["id"],
            script=script_path,
            run_type=data["type"],
            label=data.get("label"),
            profile=profile_path,
            env=data.get("env", {}),
        )


@dataclass
class Scenario:
    """A complete traffic generation scenario"""
    metadata: ScenarioMetadata
    runs: list[Run]
    
    @classmethod
    def from_yaml(cls, yaml_path: Path, data: dict[str, Any]) -> "Scenario":
        """Create Scenario from parsed YAML data"""
        scenario_dir = yaml_path.parent
        
        scenario_meta = data.get("scenario", {})
        metadata = ScenarioMetadata(
            name=scenario_meta.get("name", "unnamed"),
            description=scenario_meta.get("description", ""),
        )
        
        runs = [
            Run.from_yaml(run_data, scenario_dir)
            for run_data in data.get("runs", [])
        ]
        
        return cls(metadata=metadata, runs=runs)


@dataclass
class RunResult:
    """Result of executing a run"""
    run_id: str
    start_time_utc: str
    end_time_utc: str
    duration_s: float
    returncode: int
    stdout: str
    stderr: str
    env_effective: dict[str, str]
    outputs_dir: Path