import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path

import yaml

from . import __version__


def execute_script(script_path: Path) -> subprocess.CompletedProcess:
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    return subprocess.run(
        [str(script_path)],
        capture_output=True,
        text=True,
        check=True,
    )


def run_yaml_scenario(scenario_path: Path, output_dir: Path) -> None:
    with open(scenario_path, "r") as f:
        scenario = yaml.safe_load(f)

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

        start_time = datetime.utcnow()
        result = execute_script(script_path)
        end_time = datetime.utcnow()

        metadata["runs"].append({
            "id": run.get("id"),
            "type": run.get("type"),
            "label": run.get("label"),
            "script": str(script_path),
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
