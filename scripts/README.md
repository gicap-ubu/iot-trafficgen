# scripts/

Executable scripts for traffic generation. These scripts are invoked by the `iottrafficgen` core engine; they are not intended to be run directly.

## Directory Structure

```
scripts/
├── attacks/                    # Attack traffic generation (7 categories)
│   ├── nmap/
│   │   └── nmap_scan.sh        # NMAP network reconnaissance wrapper
│   ├── bruteforce/
│   │   ├── ssh_bruteforce.sh   # Hydra SSH brute force wrapper
│   │   └── example_passwd.txt  # Example password list for testing
│   ├── sqli/
│   │   └── sql_injection.sh    # SQLMap SQL injection wrapper
│   ├── denial_of_service/
│   │   ├── SYN_flood.sh        # SYN flood via hping3
│   │   ├── ICMP_flood.sh       # ICMP flood via hping3
│   │   ├── MQTT_flood.sh       # MQTT flood wrapper (calls mqtt_flood.py)
│   │   └── mqtt_flood.py       # MQTT publish flood implementation
│   ├── mitm/
│   │   └── ARP_spoofing.sh     # ARP cache poisoning (bidirectional)
│   ├── mqtt_inj/
│   │   ├── MQTT_injection.sh   # MQTT false data injection wrapper
│   │   └── mqtt_injection.py   # Publishes fabricated sensor data to MQTT topics
│   └── dns_beacon/
│       ├── DNS_beaconing.sh    # DNS beaconing wrapper
│       └── dns_beaconing.py    # Simulates C2 communication via DNS queries
│
└── benign/                     # Benign baseline traffic generation
    ├── IoT_DeviceSwarm.py      # 30 virtual IoT sensors (MQTT, HTTP, UDP)
    ├── MQTT_Bridge.py          # MQTT-to-database connector
    └── check_infrastructure.sh # Service verification (Apache, MariaDB, MQTT)
```

## How Scripts Are Invoked

Scripts are executed by the core engine (`core.py`) based on scenario YAML definitions. The engine:

1. Resolves the script path relative to the scenario file.
2. Injects environment variables from the scenario `env` block and the loaded profile (`TOOL_ARGS`).
3. Adds `RUN_ID` and `OUT_DIR` to the environment for output organization.
4. Detects the script type by file extension (`.sh` -> `bash`, `.py` -> `python3`).
5. Sends ground-truth markers (`ATTACK_START`/`ATTACK_END`) before and after execution.

Scripts should **not** be invoked directly unless for isolated testing.

## Attack Scripts

### nmap_scan.sh

Wrapper for NMAP network scanning.

| Variable | Required | Description |
|----------|----------|-------------|
| `TARGET_IP` | Yes | Target IP address |
| `TOOL_ARGS` | Yes | NMAP arguments (from profile, e.g., `-sS -p 1-1000 -T3`) |
| `RUN_ID` | Auto | Unique run identifier |
| `OUT_DIR` | Auto | Output directory |

Outputs: NMAP scan results in `-oA` format (XML, grepable, normal).

### ssh_bruteforce.sh

Wrapper for Hydra SSH credential attacks.

| Variable | Required | Description |
|----------|----------|-------------|
| `TARGET_IP` | Yes | Target SSH server IP |
| `TARGET_PORT` | No | SSH port (default: 22) |
| `USERNAME` | Yes | Target username |
| `WORDLIST` | Yes | Path to password wordlist |
| `TOOL_ARGS` | No | Additional Hydra arguments (from profile) |

Outputs: `hydra_output.txt` with discovered credentials (if any).

### sql_injection.sh

Wrapper for SQLMap automated SQL injection testing.

| Variable | Required | Description |
|----------|----------|-------------|
| `TARGET_URL` | Yes | Target URL with injectable parameter |
| `SQLMAP_OUTPUT_DIR` | Yes | SQLMap internal output directory |
| `TOOL_ARGS` | No | Additional SQLMap arguments (from profile) |

Runs in `--batch` mode (no interactive prompts). Outputs: `sqlmap_output.txt`.

### SYN_flood.sh

SYN flood attack via hping3. Requires root privileges.

| Variable | Required | Description |
|----------|----------|-------------|
| `TARGET_IP` | Yes | Target IP address |
| `TARGET_PORT` | Yes | Target TCP port |
| `DURATION_SECONDS` | Yes | Attack duration in seconds |
| `TOOL_ARGS` | No | Additional hping3 arguments (from profile, e.g., `--flood -d 120`) |

### ICMP_flood.sh

ICMP flood attack via hping3. Requires root privileges.

| Variable | Required | Description |
|----------|----------|-------------|
| `TARGET_IP` | Yes | Target IP address |
| `DURATION_SECONDS` | Yes | Attack duration in seconds |
| `TOOL_ARGS` | No | Additional hping3 arguments (from profile) |

### MQTT_flood.sh / mqtt_flood.py

MQTT publish flood attack. The bash script wraps the Python implementation.

| Variable | Required | Description |
|----------|----------|-------------|
| `BROKER_IP` | Yes | MQTT broker IP |
| `BROKER_PORT` | Yes | MQTT broker port |
| `QOS` | Yes | MQTT QoS level (0, 1, or 2) |
| `PAYLOAD_SIZE` | Yes | Message payload size in bytes |
| `RATE` | Yes | Target publish rate in packets per second |

### ARP_spoofing.sh

Bidirectional ARP spoofing for man-in-the-middle interception. Requires root privileges.

| Variable | Required | Description |
|----------|----------|-------------|
| `TARGET_A` | Yes | First victim IP (e.g., IoT device) |
| `TARGET_B` | Yes | Second victim IP (e.g., gateway) |
| `DURATION_SECONDS` | Yes | Attack duration in seconds |
| `NETWORK_INTERFACE` | No | Network interface (auto-detected if not set) |

Enables IP forwarding during execution and restores the original setting on cleanup.

### MQTT_injection.sh / mqtt_injection.py

Publishes fabricated sensor data to MQTT topics, simulating a false data injection attack.

### DNS_beaconing.sh / dns_beaconing.py

Generates periodic DNS queries to simulate command-and-control beaconing behavior.

## Benign Traffic Scripts

### IoT_DeviceSwarm.py

Simulates 30 virtual IoT sensors, each bound to a unique virtual IP address. Generates mixed-protocol traffic:

- **MQTT**: Publishes sensor readings (temperature, humidity, etc.) to topic-per-device.
- **HTTP**: Sends GET requests to a web server endpoint.
- **UDP**: Sends raw UDP packets to simulate lightweight sensor telemetry.

| Variable | Required | Description |
|----------|----------|-------------|
| `BROKER_IP` | Yes | MQTT broker IP address |
| `WEB_SERVER_IP` | Yes | HTTP server IP address |
| `BASE_IP` | No | IP range base (default: `192.168.1`) |
| `RANGE_START` | No | First device octet (default: `150`) |
| `RANGE_END` | No | Last device octet (default: `179`) |

Supports indefinite execution (runs until Ctrl+C) or duration-based execution.

### MQTT_Bridge.py

Connects an MQTT broker to a MariaDB/MySQL database. Subscribes to sensor topics and inserts received data into a relational schema.

| Variable | Required | Description |
|----------|----------|-------------|
| `BROKER_IP` | Yes | MQTT broker IP |
| `DB_HOST` | Yes | Database host |
| `DB_USER` | Yes | Database username |
| `DB_PASS` | Yes | Database password |
| `DB_NAME` | Yes | Database name |

### check_infrastructure.sh

Verifies that the required IoT laboratory infrastructure is running:

- Apache/HTTP server status and connectivity
- MariaDB/MySQL service and schema validation
- MQTT broker availability

Returns non-zero exit code if any service is unavailable.

## Adding New Scripts

To add a new attack or benign traffic script:

1. Create the script in the appropriate subdirectory under `scripts/attacks/` or `scripts/benign/`.
2. The script must read configuration from environment variables (not command-line arguments to the script itself).
3. Use `RUN_ID` and `OUT_DIR` (injected by the engine) to organize output files.
4. Handle `SIGINT`/`SIGTERM` for graceful shutdown.
5. Create a corresponding scenario YAML in `scenarios/` and (optionally) a profile in `profiles/`.
