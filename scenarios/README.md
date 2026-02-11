# scenarios/

YAML scenario definitions for all traffic generation experiments. Each file encodes a complete, reproducible configuration for a single traffic generation run.

## Directory Structure

```
scenarios/
├── nmap/                   # 30 NMAP reconnaissance scenarios
│   ├── 01.yaml .. 30.yaml
├── bruteforce/             # 6 SSH brute force scenarios
│   ├── 01.yaml .. 06.yaml
├── sqli/                   # 6 SQL injection scenarios
│   ├── 01.yaml .. 06.yaml
├── denial_of_service/      # 17 DoS attack scenarios
│   ├── syn_01.yaml .. syn_06.yaml      # SYN flood variants
│   ├── icmp_01.yaml .. icmp_07.yaml    # ICMP flood variants
│   └── mqtt_01.yaml .. mqtt_04.yaml    # MQTT flood variants
├── mitm/                   # 1 ARP spoofing scenario
│   └── 01.yaml
├── mqtt_inj/               # 2 MQTT false data injection scenarios
│   ├── 01.yaml, 02.yaml
├── dns_beacon/             # 1 DNS beaconing scenario
│   └── 01.yaml
└── benign/                 # 3 benign baseline traffic scenarios
    ├── 01_device_swarm.yaml
    ├── 02_mqtt_bridge.yaml
    └── 03_infrastructure.yaml
```

**Total: 66 scenario files** (63 attack + 3 benign).

## YAML Schema

Every scenario file follows this structure:

```yaml
scenario:
  name: "SCENARIO_NAME"              # Unique identifier
  description: "Human-readable description"
  category: "attack"                  # Optional: "attack" or "benign"

  markers:                            # Ground-truth marker configuration
    enabled: true                     # true/false
    host: "MARKER_HOST_PLACEHOLDER"   # UDP destination IP
    port: 55556                       # UDP destination port

runs:
  - id: "unique_run_id"              # Unique identifier within the scenario
    type: "attack"                   # "attack" or "benign"
    label: "SCENARIO_NAME"           # Label for markers and metadata
    script: "../../scripts/attacks/category/script.sh"   # Relative path to script
    profile: "../../profiles/category/profile_NN.yaml"   # Relative path to profile
    env:                             # Environment variables passed to the script
      TARGET_IP: "TARGET_IP_PLACEHOLDER"
      DURATION_SECONDS: "60"
```

### Field Reference

| Field | Required | Description |
|-------|----------|-------------|
| `scenario.name` | Yes | Unique scenario name used in metadata and markers |
| `scenario.description` | Yes | Human-readable description shown in interactive menus |
| `scenario.markers.enabled` | No | Enable/disable UDP ground-truth markers (default: `true`) |
| `scenario.markers.host` | No | Marker destination IP (default: `127.0.0.1`) |
| `scenario.markers.port` | No | Marker destination port (default: `55556`) |
| `runs[].id` | Yes | Unique run identifier within the scenario |
| `runs[].type` | Yes | `"attack"` or `"benign"` |
| `runs[].label` | No | Human-readable label for markers |
| `runs[].script` | Yes | Relative path from scenario file to the executable script |
| `runs[].profile` | No | Relative path to the tool profile YAML |
| `runs[].env` | No | Dictionary of environment variables |

### Placeholders

Values ending in `_PLACEHOLDER` indicate variables that must be configured before execution. In interactive mode, the user is prompted to provide values; defaults are extracted from the prefix before `_PLACEHOLDER`.

Examples:
- `TARGET_IP_PLACEHOLDER` -> prompts for target IP with no default
- `192.168.1.10_PLACEHOLDER` -> prompts with `192.168.1.10` as default
- `DURATION_SECONDS_PLACEHOLDER` -> prompts for duration with no default

Non-placeholder values (e.g., `"80"`, `"1883"`) are used directly without prompting.

### Path Resolution

Script and profile paths are resolved relative to the scenario file location. For example, a scenario at `scenarios/nmap/01.yaml` with `script: ../../scripts/attacks/nmap/nmap_scan.sh` resolves to the project root `scripts/attacks/nmap/nmap_scan.sh`.

## Scenario Categories

### NMAP Reconnaissance (30 scenarios)

Covers systematic variation of NMAP scan parameters:

- **Scan types**: SYN (`-sS`), ACK (`-sA`), FIN (`-sF`), NULL (`-sN`)
- **Port ranges**: 1-1000, 1-10000, 1-65535
- **Timing profiles**: T1 (sneaky), T2 (polite), T3 (normal), T4 (aggressive), T5 (insane)
- **Target roles**: HUB, SENSOR (different IoT device types)

### SSH Brute Force (6 scenarios)

Varies Hydra parameters:

- Thread counts (1, 4, 16 threads)
- Connection timeouts
- Wait times between attempts

### SQL Injection (6 scenarios)

Varies SQLMap configuration:

- Injection techniques: time-based, Boolean-based, error-based
- Detection levels and risk levels
- Request delays for stealth variation

### Denial of Service (17 scenarios)

Three DoS sub-categories:

- **SYN flood (6)**: Varies packet rate (`--fast`, `--faster`, `--flood`), payload size, and target port.
- **ICMP flood (7)**: Varies ICMP packet rate and payload size.
- **MQTT flood (4)**: Varies QoS level (0, 1, 2), payload size (64B-1024B), and publish rate.

### ARP Spoofing (1 scenario)

Bidirectional ARP spoofing between two targets for man-in-the-middle interception. Requires two victim IPs and a duration.

### MQTT Injection (2 scenarios)

False data injection into MQTT topics at different rates:

- Fast rate (0.05s delay, 0.01s jitter)
- Slow rate (higher delay and jitter for stealth)

### DNS Beaconing (1 scenario)

Simulates command-and-control beaconing via DNS queries with configurable:

- Query interval and jitter
- High-entropy label length (to simulate encoded C2 data)

### Benign Traffic (3 scenarios)

- **01_device_swarm.yaml**: 30 simulated IoT sensors sending MQTT, HTTP, and UDP traffic.
- **02_mqtt_bridge.yaml**: MQTT subscriber that writes sensor data to a relational database.
- **03_infrastructure.yaml**: Verifies that required services (Apache, MariaDB, MQTT) are available.

## Creating New Scenarios

1. Create a YAML file following the schema above.
2. Place it in the appropriate category subdirectory (or create a new one).
3. Reference scripts from `scripts/` and profiles from `profiles/` using relative paths.
4. Use `_PLACEHOLDER` suffixed values for variables that should be configured per-environment.
5. Validate with `iottrafficgen run your_scenario.yaml --dry-run`.
