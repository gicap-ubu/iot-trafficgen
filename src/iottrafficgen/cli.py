import os
import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path

import yaml

from . import __version__


def execute_script(script_path: Path, extra_env: dict | None = None) -> subprocess.CompletedProcess:
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    env = os.environ.copy()
    if extra_env:
        env.update({str(k): str(v) for k, v in extra_env.items()})

    return subprocess.run(
        [str(script_path)],
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )


def load_yaml(path: Path) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def run_yaml_scenario(scenario_path: Path, output_dir: Path) -> None:
    scenario = load_yaml(scenario_path)

    output_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "tool": "iottrafficgen",
        "version": __version__,
        "scenario": scenario.get("scenario", {}),
        "runs": [],
        "generated_at_utc": datetime.utcnow().isoformat(),
    }

    for run in scenario.get("runs", []):
        script_path = Path(run["script"])

        # ---------- ENV BASE ----------
        env = run.get("env", {}).copy()

        # ---------- PROFILE INJECTION ----------
        if "profile" in run:
            profile_cfg = load_yaml(Path(run["profile"])).get("profile", {})
            if "tool_args" in profile_cfg:
                env["TOOL_ARGS"] = profile_cfg["tool_args"]

        start_time = datetime.utcnow()
        result = execute_script(script_path, env)
        end_time = datetime.utcnow()

        metadata["runs"].append({
            "id": run.get("id"),
            "type": run.get("type"),
            "label": run.get("label"),
            "script": str(script_path),
            "profile": run.get("profile"),
            "start_time_utc": start_time.isoformat(),
            "end_time_utc": end_time.isoformat(),
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        })

        # Mostrar stdout en tiempo real (debug)
        if result.stdout:
            print(result.stdout, end="")

    output_file = output_dir / "scenario_metadata.json"
    with open(output_file, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"Scenario finished. Metadata saved to {output_file}")


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(
        prog="iottrafficgen",
        description="Reproducible IoT traffic generation (GICAP)",
    )

    parser.add_argument("--version", action="version", version=__version__)

    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Run a YAML scenario")
    run_p.add_argument("scenario", help="Path to scenario.yaml")
    run_p.add_argument(
        "--output",
        default="runs/latest",
        help="Output directory",
    )

    args = parser.parse_args(argv)

    if args.command == "run":
        run_yaml_scenario(Path(args.scenario), Path(args.output))
