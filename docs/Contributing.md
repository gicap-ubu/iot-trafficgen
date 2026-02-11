# Contributing

Guide for adding new attack scenarios, tool profiles, and execution scripts to `iottrafficgen`.

---

## Project Structure Overview

```
iottrafficgen/
├── src/iottrafficgen/    # Python package (core engine, CLI, models)
├── scripts/              # Executable scripts (attacks + benign)
├── scenarios/            # YAML scenario definitions
├── profiles/             # YAML tool argument profiles
└── docs/                 # Documentation
```

The three extension points for adding new traffic types are **scripts**, **scenarios**, and **profiles**. The core engine (`src/iottrafficgen/`) does not need modification for most additions.

---

## Adding a New Attack Category

### 1. Create the script

Create a script in `scripts/attacks/<category>/`:

```bash
# scripts/attacks/my_attack/my_attack.sh
#!/usr/bin/env bash
set -euo pipefail

# Read configuration from environment variables
: "${TARGET_IP:?TARGET_IP is required}"
: "${DURATION_SECONDS:?DURATION_SECONDS is required}"

TOOL_ARGS="${TOOL_ARGS:-}"
RUN_ID="${RUN_ID:-run_unknown}"
OUT_DIR="${OUT_DIR:-runs/${RUN_ID}/my_attack}"

mkdir -p "$OUT_DIR"

# Validate tool availability
if ! command -v mytool &>/dev/null; then
    echo "[my_attack] ERROR: mytool not found in PATH"
    exit 1
fi

# Handle SIGINT/SIGTERM for graceful shutdown
trap 'echo "[my_attack] Interrupted"; exit 130' INT TERM

# Execute
read -r -a ARGS <<< "$TOOL_ARGS"
OUTPUT_FILE="${OUT_DIR}/output.txt"

set +e
timeout "$DURATION_SECONDS" mytool "${ARGS[@]}" "$TARGET_IP" > "$OUTPUT_FILE" 2>&1
EXIT_CODE=$?
set -e

echo "[my_attack] Completed"
exit $EXIT_CODE
```

Script requirements:

- Read all configuration from **environment variables** (not CLI arguments).
- Use `RUN_ID` and `OUT_DIR` (injected by the engine) for output organization.
- Handle `SIGINT`/`SIGTERM` for graceful shutdown (exit code 130).
- Exit with the tool's exit code.
- Mark the script as executable: `chmod +x scripts/attacks/my_attack/my_attack.sh`.

### 2. Create a profile

Create a profile in `profiles/<category>/`:

```yaml
# profiles/my_attack/profile_01.yaml
profile:
  tool: mytool
  name: MY_ATTACK_VARIANT_1
  description: "My attack with fast rate and large payload"
  tool_args: "--fast --payload-size 1024"
```

The `tool_args` string is passed as the `TOOL_ARGS` environment variable to the script.

### 3. Create a scenario

Create a scenario in `scenarios/<category>/`:

```yaml
# scenarios/my_attack/01.yaml
scenario:
  name: "MY_ATTACK_FAST_LARGE"
  description: "My attack with fast rate and large payload"
  markers:
    enabled: true
    host: "MARKER_HOST_PLACEHOLDER"
    port: 55556

runs:
  - id: my_attack_01
    type: attack
    label: "MY_ATTACK_FAST_LARGE"
    script: ../../scripts/attacks/my_attack/my_attack.sh
    profile: ../../profiles/my_attack/profile_01.yaml
    env:
      TARGET_IP: "TARGET_IP_PLACEHOLDER"
      DURATION_SECONDS: "DURATION_SECONDS_PLACEHOLDER"
```

Path rules:
- `script` and `profile` paths are **relative to the scenario file**.
- Use `_PLACEHOLDER` suffix for values the user must configure.
- Non-placeholder values (e.g., `"80"`) are used directly.

### 4. Validate

```bash
# Dry run to check configuration
iottrafficgen run scenarios/my_attack/01.yaml --dry-run

# Verify it appears in the listing
iottrafficgen list --category my_attack
```

---

## Adding a Scenario Variant

To add a variant of an existing attack (e.g., a new NMAP timing profile):

1. Create a new profile: `profiles/nmap/profile_31.yaml`
2. Create a new scenario: `scenarios/nmap/31.yaml`
3. Reference the new profile from the new scenario.

No script changes are needed — the same script runs with different `TOOL_ARGS`.

---

## Adding a Benign Traffic Component

Benign traffic scripts follow the same pattern but with `type: "benign"` in the scenario.

For **Python scripts**, catch `KeyboardInterrupt` to allow graceful shutdown when the user presses Ctrl+C. This is important: the engine sends `SIGINT` to stop indefinitely-running scripts and collect metadata cleanly.

```python
#!/usr/bin/env python3
# scripts/benign/my_sensor.py

import os
import time
import json

BROKER_IP  = os.environ.get('BROKER_IP', '192.168.1.121')
OUT_DIR    = os.environ.get('OUT_DIR', '.')

print(f"[my_sensor] Starting — broker: {BROKER_IP}")

try:
    while True:
        # generate and publish sensor data
        time.sleep(1)

except KeyboardInterrupt:
    print("\n[my_sensor] Stopped by user")

    # Write any final outputs to OUT_DIR
    summary = {"broker": BROKER_IP, "status": "completed"}
    with open(os.path.join(OUT_DIR, "summary.json"), "w") as f:
        json.dump(summary, f)
```

Define the scenario with `type: benign`:

```yaml
runs:
  - id: my_sensor_01
    type: benign
    label: "MY_SENSOR_COMPONENT"
    script: ../../scripts/benign/my_sensor.py
    env:
      BROKER_IP: "192.168.1.121_PLACEHOLDER"
```

The marker system automatically sends `BENIGN_START` / `BENIGN_END` events instead of `ATTACK_START` / `ATTACK_END`.

---

## Updating the Interactive Menu

If you add a new attack category, update the `CATEGORIES` dictionary in `src/iottrafficgen/interactive.py`:

```python
CATEGORIES = {
    # ... existing categories ...
    "9": {
        "name": "My New Category",
        "path": "scenarios/my_attack",
        "count": 1,
        "description": "My new attack type"
    },
}
```

Adjust the exit option accordingly.

---

## Code Style

- **Python:** follow existing patterns in `src/iottrafficgen/`.
- **Shell scripts:** use `set -euo pipefail`, validate required variables with `: "${VAR:?message}"`.
- **YAML:** 2-space indentation, quote strings with special characters.

---

## Running Tests

```bash
pip install -e ".[dev]"
pytest
```

---

## Checklist for New Contributions

- [ ] Script reads configuration from environment variables
- [ ] Script handles SIGINT/SIGTERM gracefully (exit code 130 for shell, `KeyboardInterrupt` for Python)
- [ ] Script validates tool availability and provides a clear error message
- [ ] Script writes outputs to `$OUT_DIR`
- [ ] Profile YAML has `tool`, `name`, `description`, `tool_args`
- [ ] Scenario YAML has `scenario.name`, `scenario.description`, `runs`
- [ ] Scenario uses `_PLACEHOLDER` for environment-specific values
- [ ] Paths in scenario are relative and correct
- [ ] `iottrafficgen run <scenario> --dry-run` passes
- [ ] `iottrafficgen list` shows the new scenario