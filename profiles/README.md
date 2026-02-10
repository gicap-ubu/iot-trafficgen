# profiles/

Tool argument profiles that define specific configurations for each external tool. Profiles are referenced by scenario YAML files and their `tool_args` field is injected as the `TOOL_ARGS` environment variable at execution time.

## Directory Structure

```
profiles/
├── nmap/                       # 30 NMAP scan profiles
│   └── profile_01.yaml .. profile_30.yaml
├── bruteforce/                 # 6 Hydra SSH brute force profiles
│   └── profile_01.yaml .. profile_06.yaml
├── sqli/                       # 6 SQLMap injection profiles
│   └── profile_01.yaml .. profile_06.yaml
├── denial_of_service/          # 17 DoS profiles
│   ├── syn_profile_01.yaml .. syn_profile_06.yaml
│   ├── icmp_profile_01.yaml .. icmp_profile_07.yaml
│   └── mqtt_profile_01.yaml .. mqtt_profile_04.yaml
├── mitm/                       # 1 ARP spoofing profile
│   └── profile_01.yaml
├── mqtt_inj/                   # 2 MQTT injection profiles
│   └── profile_01.yaml, profile_02.yaml
├── dns_beacon/                 # 1 DNS beaconing profile
│   └── profile_01.yaml
└── benign/                     # 1 benign traffic profile
    └── profile_01.yaml
```

**Total: 64 profile files.**

## YAML Schema

### Attack Profiles

```yaml
profile:
  tool: "tool_name"            # External tool identifier (nmap, hydra, sqlmap, hping3)
  name: "PROFILE_NAME"        # Unique profile name
  description: "Description"  # Human-readable description
  tool_args: "arguments"      # Command-line arguments passed to the tool
```

### Benign Profiles

Benign profiles may omit the `profile:` wrapper:

```yaml
name: "IoT Lab Baseline Profile"
description: "Original lab configuration: 30 sensors, 3-6s interval, mixed protocols"
tool_args: ""
```

## How Profiles Are Used

1. A scenario YAML references a profile via a relative path in the `profile` field.
2. The core engine loads the profile and extracts `tool_args`.
3. `tool_args` is injected as the `TOOL_ARGS` environment variable.
4. The execution script reads `TOOL_ARGS` and passes the arguments to the external tool.

This separation allows the same script to be reused with different tool configurations without modification.

## Profile Examples by Category

### NMAP

```yaml
profile:
  tool: nmap
  name: NMAP_SYN_HUB_P1_1000_T3
  description: "SYN scan HUB ports 1-1000, timing T3"
  tool_args: "-sS -p 1-1000 -T3"
```

Parameters varied across NMAP profiles:

| Parameter | Values | NMAP Flag |
|-----------|--------|-----------|
| Scan type | SYN, ACK, FIN, NULL | `-sS`, `-sA`, `-sF`, `-sN` |
| Port range | 1-1000, 1-10000, 1-65535 | `-p` |
| Timing | T1 through T5 | `-T1` .. `-T5` |

### Hydra (SSH Brute Force)

```yaml
profile:
  tool: hydra
  name: SSH_BF_LOW_STEALTH
  description: "SSH brute force with 1 thread, 300s timeout, stealth mode"
  tool_args: "-t 1 -w 10 -W 1"
```

Parameters varied across Hydra profiles:

| Parameter | Values | Hydra Flag |
|-----------|--------|------------|
| Threads | 1, 4, 16 | `-t` |
| Timeout | 10s, 30s | `-w` |
| Wait between attempts | 1s, 3s | `-W` |

### SQLMap (SQL Injection)

```yaml
profile:
  tool: sqlmap
  name: SQLI_P1_BOOLEAN_SLOW
  description: "SQL injection with Boolean-based technique, slow delay (0.5s), level 2"
  tool_args: "--delay 0.5 --level 2 --risk 1 --technique B --fresh-queries --flush-session"
```

Parameters varied across SQLMap profiles:

| Parameter | Values | SQLMap Flag |
|-----------|--------|-------------|
| Technique | Boolean (B), Time-based (T), Error-based (E) | `--technique` |
| Delay | 0.5s, 1.0s, 2.0s | `--delay` |
| Level | 1, 2, 3 | `--level` |
| Risk | 1, 2 | `--risk` |

### hping3 (DoS)

```yaml
profile:
  tool: hping3
  name: SYN_FLOOD_HIGH_RATE_STD
  description: "SYN flood high rate (u10000), standard payload (120B)"
  tool_args: "-d 120 -r -i u10000"
```

Parameters varied across DoS profiles:

| Parameter | Values | hping3 Flag |
|-----------|--------|-------------|
| Payload size | 64B, 120B, 512B, 1024B | `-d` |
| Packet interval | u1000, u10000, u100000, `--flood` | `-i` |
| Relative seq display | enabled | `-r` |

## Creating New Profiles

1. Create a YAML file in the appropriate category subdirectory.
2. Follow the schema above, specifying `tool`, `name`, `description`, and `tool_args`.
3. Reference the new profile from a scenario YAML using a relative path.
4. Validate with `iottrafficgen run your_scenario.yaml --dry-run`.

The `tool_args` string is passed as-is to the execution script, which in turn passes it to the external tool. Ensure the arguments are valid for the specified tool version.
