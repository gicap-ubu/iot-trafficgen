# Usage Examples

Practical examples for using `iottrafficgen` to generate labeled traffic datasets.

---

## 1. Interactive Mode

The simplest way to use `iottrafficgen`. Launch and follow the menu:

```bash
iottrafficgen run
```

The interactive mode:

1. Shows a category menu (NMAP, Brute Force, SQL Injection, etc.).
2. Lets you browse scenarios within a category.
3. Displays scenario details (name, description, profile, script).
4. Prompts for environment-specific values (target IPs, durations).
5. Asks for execution confirmation.

Default values are shown in `[brackets]`. Press Enter to accept or type a custom value.

---

## 2. Running a Single Scenario

### NMAP Reconnaissance

```bash
iottrafficgen run scenarios/nmap/01.yaml
```

You will be prompted for:
- `TARGET_IP` -- the IP of the device to scan
- `MARKER_HOST` -- where to send ground-truth markers

Output in `runs/nmap_01_<timestamp>/outputs/`:
- `scan.nmap` -- human-readable scan results
- `scan.xml` -- XML output
- `scan.gnmap` -- grepable output

### SSH Brute Force

```bash
iottrafficgen run scenarios/bruteforce/01.yaml
```

Prompts for: `TARGET_IP`, `USERNAME`, `WORDLIST`, `MARKER_HOST`.

### SQL Injection

```bash
iottrafficgen run scenarios/sqli/01.yaml
```

Prompts for: `TARGET_URL` (with injectable parameter), `SQLMAP_OUTPUT_DIR`, `MARKER_HOST`.

### Denial of Service (SYN Flood)

```bash
# Requires root
sudo iottrafficgen run scenarios/denial_of_service/syn_01.yaml
```

Prompts for: `TARGET_IP`, `DURATION_SECONDS`, `MARKER_HOST`.

Shows a progress bar during execution.

### MQTT False Data Injection

```bash
iottrafficgen run scenarios/mqtt_inj/01.yaml
```

Prompts for: `BROKER_IP`, `DURATION_SECONDS`, `MARKER_HOST`.

### Benign IoT Traffic

```bash
iottrafficgen run scenarios/benign/01_device_swarm.yaml
```

Prompts for: `BROKER_IP`, `WEB_SERVER_IP`.

Runs indefinitely (Ctrl+C to stop). Generates MQTT, HTTP, and UDP traffic from 30 simulated sensors.

---

## 3. Dry Run (Validation)

Validate a scenario without executing any scripts:

```bash
iottrafficgen run scenarios/nmap/01.yaml --dry-run
```

Dry run checks:
- YAML syntax and required fields
- Script file existence
- Profile file existence
- Placeholder detection

---

## 4. Listing and Filtering Scenarios

```bash
# List all scenarios
iottrafficgen list

# Filter by category
iottrafficgen list --category nmap
iottrafficgen list --category bruteforce
iottrafficgen list --category dos

# Count only
iottrafficgen list --count-only
```

---

## 5. Custom Workspace

By default, output is written to the current directory. Use `--workspace` to redirect:

```bash
iottrafficgen run scenarios/nmap/01.yaml --workspace /data/experiment_01
```

Output structure:
```
/data/experiment_01/
├── runs/
│   └── nmap_01_20260209_143022/
│       ├── run_metadata.json
│       ├── execution.log
│       └── outputs/
└── .iottrafficgen/
    └── scenario_metadata_20260209_143022.json
```

---

## 6. Logging Levels

```bash
# Default: INFO level
iottrafficgen run scenarios/nmap/01.yaml

# Verbose: DEBUG level (detailed execution info)
iottrafficgen run scenarios/nmap/01.yaml --verbose

# Quiet: errors only
iottrafficgen run scenarios/nmap/01.yaml --quiet
```

Logs are always written to `runs/<run_id>/execution.log` regardless of console verbosity.

---

## 7. Dataset Creation Workflow

A typical workflow for creating a labeled dataset:

### Step 1: Start packet capture

```bash
sudo tcpdump -i eth0 -w dataset_capture.pcap &
TCPDUMP_PID=$!
```

### Step 2: Generate benign baseline traffic

```bash
# In a separate terminal, start the device swarm
iottrafficgen run scenarios/benign/01_device_swarm.yaml &
```

### Step 3: Execute attack scenarios

```bash
# Run multiple attack scenarios sequentially
iottrafficgen run scenarios/nmap/01.yaml
iottrafficgen run scenarios/nmap/05.yaml
iottrafficgen run scenarios/bruteforce/01.yaml
sudo iottrafficgen run scenarios/denial_of_service/syn_01.yaml
```

### Step 4: Stop capture and benign traffic

```bash
# Stop benign traffic (Ctrl+C in its terminal)
# Stop packet capture
kill $TCPDUMP_PID
```

### Step 5: Extract ground-truth labels

```bash
# Extract markers from capture
tshark -r dataset_capture.pcap -Y "udp.port == 55556" -T json > markers.json
```

### Step 6: Collect metadata

All execution metadata is in:
- `runs/*/run_metadata.json` -- per-run metadata
- `.iottrafficgen/scenario_metadata_*.json` -- per-scenario metadata

---

## 8. Programmatic API

Use `iottrafficgen` as a Python library for automated pipelines:

```python
from pathlib import Path
from iottrafficgen import run_scenario

scenarios = [
    "scenarios/nmap/01.yaml",
    "scenarios/nmap/05.yaml",
    "scenarios/nmap/10.yaml",
]

workspace = Path("/data/experiment_01")

for scenario in scenarios:
    run_scenario(
        scenario_path=Path(scenario),
        workspace=workspace,
        dry_run=False,
        verbose=False,
        quiet=True,
    )
```
