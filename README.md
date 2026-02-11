# iottrafficgen

**Reproducible IoT Traffic Generation Framework for Cybersecurity Research**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0-green.svg)](pyproject.toml)

`iottrafficgen` is an open-source framework for generating reproducible IoT network traffic in controlled laboratory environments. It enables cybersecurity researchers to produce labeled datasets containing both benign IoT behavior and traffic patterns associated with common attack techniques. The framework integrates automated ground-truth labeling via UDP markers and structured JSON metadata per execution.

The framework is intended for controlled laboratory experimentation and dataset creation, not for operational intrusion detection or exploitation.

---

## Requirements

- **OS:** Linux (Ubuntu 20.04+, Raspberry Pi OS)
- **Python:** 3.10 or higher
- **Network:** Isolated laboratory environment

**External tools** (installed separately, only needed for their respective attack categories):

| Tool | Category | Install (Debian/Ubuntu) |
|------|----------|-------------------------|
| `nmap` | Reconnaissance | `apt install nmap` |
| `hydra` | SSH Brute Force | `apt install hydra` |
| `sqlmap` | SQL Injection | `apt install sqlmap` |
| `hping3` | SYN/ICMP Flood | `apt install hping3` |
| `arpspoof` | ARP Spoofing | `apt install dsniff` |

See [docs/Installation.md](docs/Installation.md) for the full installation guide and laboratory setup.

---

## Installation

```bash
git clone https://github.com/branly-martinez/iottrafficgen.git
cd iottrafficgen
pip install -e .
iottrafficgen --version
```

---

## Quick Start

### Interactive mode

```bash
iottrafficgen run
```

Launches an interactive menu to browse available scenarios, configure parameters, and execute.

### Direct execution

```bash
# Run a specific scenario
iottrafficgen run scenarios/nmap/01.yaml

# Validate without executing
iottrafficgen run scenarios/nmap/01.yaml --dry-run

# List all available scenarios
iottrafficgen list
```

### Programmatic API

```python
from pathlib import Path
from iottrafficgen import run_scenario

run_scenario(
    scenario_path=Path("scenarios/nmap/01.yaml"),
    workspace=Path("/data/captures"),
    dry_run=False,
    verbose=True,
    quiet=False,
)
```

---

## Available Scenarios

| Category | Scenarios | Tool | Description |
|----------|-----------|------|-------------|
| NMAP Reconnaissance | 30 | `nmap` | SYN/ACK/FIN/NULL scans, port ranges, timing profiles (T1–T5) |
| SSH Brute Force | 6 | `hydra` | Credential attacks with varying thread counts and timeouts |
| SQL Injection | 6 | `sqlmap` | Time-based, Boolean-based, and error-based techniques |
| Denial of Service | 17 | `hping3`, Python | SYN flood (6), ICMP flood (7), MQTT flood (4) |
| ARP Spoofing (MITM) | 1 | `arpspoof` | Man-in-the-middle via ARP cache poisoning |
| MQTT Injection | 2 | Python | False sensor data injection into MQTT topics |
| DNS Beaconing | 1 | Python | C2 communication simulation via DNS queries |
| Benign Traffic | 3 | Python | IoT device swarm, MQTT bridge, infrastructure check |

**Total: 66 scenarios.** Each scenario has a corresponding profile with tool-specific parameters.

---

## How It Works

`iottrafficgen` orchestrates traffic generation in four steps:

1. **Load** — Parses the scenario YAML and the referenced tool profile.
2. **Configure** — Prompts for placeholder values; validates tools and scripts.
3. **Execute** — Sends a `*_START` UDP marker, runs the backend script, sends a `*_END` marker.
4. **Record** — Writes `run_metadata.json` and `execution.log` to a timestamped directory under `runs/`.

The separation between scenario (what to do), profile (how to configure the tool), and script (how to execute it) allows full reproducibility: re-running the same YAML with the same parameters produces an identical traffic pattern.

---

## Output Structure

Each execution produces a timestamped directory under `runs/`:

```
runs/
└── nmap_01_20260209_143022/
    ├── run_metadata.json      # Execution metadata (JSON)
    ├── execution.log          # Detailed execution log
    └── outputs/               # Tool-specific output files
```

`run_metadata.json` captures all execution parameters, timestamps, environment variables, and exit codes for reproducibility.

---

## Ground-Truth Markers

`iottrafficgen` sends UDP packets marking the exact start and end of each traffic event, enabling precise labeling when combined with packet capture tools (tcpdump, Wireshark, Zeek).

```json
{
  "type": "GROUND_TRUTH",
  "event": "ATTACK_START",
  "attack_id": "nmap_01_20260209_143022",
  "ts_iso_utc": "2026-02-09T14:30:22Z",
  "target_ip": "192.168.8.121",
  "label": "NMAP_SYN_HUB_P1_1000_T3"
}
```

Default destination: `127.0.0.1:55556` (UDP). Configurable per scenario.

---

## Security Notice

This software generates network traffic patterns associated with attack techniques. It must be used exclusively in controlled laboratory environments that are physically isolated or logically segmented from production networks.

Only target systems you own or have explicit authorization to test.

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/installation.md](docs/installation.md) | Full installation guide and laboratory setup |
| [docs/examples.md](docs/examples.md) | Practical usage examples and dataset creation workflow |
| [docs/contributing.md](docs/contributing.md) | How to add new scenarios, profiles, and scripts |
| [scenarios/README.md](scenarios/README.md) | Scenario YAML format and field reference |
| [profiles/README.md](profiles/README.md) | Profile system and tool argument reference |
| [scripts/README.md](scripts/README.md) | Backend script descriptions and environment variables |

---

## License

MIT License — see [LICENSE](LICENSE) for details.  
Copyright (c) 2026 Branly Martínez, Grupo de Investigación de Inteligencia Artificial Aplicada, Universidad de Burgos, Spain.