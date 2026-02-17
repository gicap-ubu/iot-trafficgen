# Installation Guide

Complete installation instructions for `iottrafficgen` and the laboratory infrastructure it requires.

---

## 1. System Requirements

| Requirement | Minimum |
|-------------|---------|
| OS | Linux (Ubuntu 20.04+, Raspberry Pi OS, Debian 11+) |
| Python | 3.10 or higher |
| Network | Isolated laboratory environment (no internet access) |
| Privileges | Root access required for DoS and MITM scenarios |

---

## 2. Install iottrafficgen

```bash
# Clone the repository
git clone https://github.com/gicap-ubu/iot-trafficgen.git
cd iottrafficgen

# Install the package (editable mode)
pip install -e .

# Verify
iottrafficgen --version
```

This installs the following Python dependencies automatically:

| Package | Purpose |
|---------|---------|
| `pyyaml` >= 6.0 | YAML scenario/profile parsing |
| `click` >= 8.1 | CLI framework |
| `colorama` >= 0.4.6 | Colored terminal output |
| `paho-mqtt` >= 1.6.0 | MQTT client (benign traffic + MQTT attacks) |
| `dnspython` >= 2.0.0 | DNS operations (beaconing simulation) |
| `requests` >= 2.28.0 | HTTP requests (IoT device simulation) |
| `mysql-connector-python` >= 8.0.0 | Database connectivity (MQTT bridge) |

For development (includes `pytest`):

```bash
pip install -e ".[dev]"
```

---

## 3. Install External Tools

Install only the tools required for the attack categories you plan to use.

### All tools at once (Debian/Ubuntu)

```bash
sudo apt update
sudo apt install -y nmap hydra sqlmap hping3 dsniff
```

### Individual tools

| Tool | Category | Install | Verify |
|------|----------|---------|--------|
| `nmap` | NMAP Reconnaissance (30 scenarios) | `sudo apt install nmap` | `nmap --version` |
| `hydra` | SSH Brute Force (6 scenarios) | `sudo apt install hydra` | `hydra -h` |
| `sqlmap` | SQL Injection (6 scenarios) | `sudo apt install sqlmap` | `sqlmap --version` |
| `hping3` | SYN/ICMP Flood (13 scenarios) | `sudo apt install hping3` | `sudo hping3 --version` |
| `arpspoof` | ARP Spoofing (1 scenario) | `sudo apt install dsniff` | `which arpspoof` |

`iottrafficgen` validates tool availability before execution and provides installation hints if a required tool is missing.

> **Note:** DoS (SYN flood, ICMP flood) and MITM (ARP spoofing) scenarios require root privileges to send raw packets. Use `sudo iottrafficgen run` for these categories, or run the session as root.

---

## 4. Laboratory Infrastructure (Benign Traffic)

The benign traffic scenarios require additional services. This section is only needed if you plan to use the Device Swarm, MQTT Bridge, or Infrastructure Check scenarios.

### 4.1 MQTT Broker (Mosquitto)

```bash
sudo apt install -y mosquitto mosquitto-clients

# Start the service
sudo systemctl enable mosquitto
sudo systemctl start mosquitto

# Verify
mosquitto_sub -t "test" -C 1 &
mosquitto_pub -t "test" -m "hello"
```

### 4.2 Apache + PHP

Required for the HTTP endpoint used by the IoT Device Swarm.

```bash
sudo apt install -y apache2 php libapache2-mod-php

sudo systemctl enable apache2
sudo systemctl start apache2

# Verify
curl -s http://localhost/ | head -5
```

### 4.3 MariaDB / MySQL

Required for the MQTT Bridge scenario.

```bash
sudo apt install -y mariadb-server

sudo systemctl enable mariadb
sudo systemctl start mariadb

# Secure installation
sudo mysql_secure_installation

# Create the database and user
sudo mysql -e "
CREATE DATABASE IF NOT EXISTS iot_db;
CREATE USER IF NOT EXISTS 'admin_iot'@'localhost' IDENTIFIED BY 'secreto';
GRANT ALL PRIVILEGES ON iot_db.* TO 'admin_iot'@'localhost';
FLUSH PRIVILEGES;
"

# Create the sensor data table
sudo mysql iot_db -e "
CREATE TABLE IF NOT EXISTS sensores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_id VARCHAR(50),
    topic VARCHAR(100),
    payload TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
"
```

### 4.4 Virtual IP Addresses (Device Swarm)

The IoT Device Swarm binds each simulated sensor to a unique virtual IP. Configure them on the interface connected to your lab network:

```bash
# Replace eth0 with your actual interface
INTERFACE="eth0"
BASE="192.168.1"

for i in $(seq 150 179); do
    sudo ip addr add "${BASE}.${i}/24" dev "$INTERFACE"
done

# Verify
ip addr show dev "$INTERFACE" | grep "192.168.1.1[5-7]"
```

To remove virtual IPs:

```bash
for i in $(seq 150 179); do
    sudo ip addr del "${BASE}.${i}/24" dev "$INTERFACE"
done
```

### 4.5 Verify Infrastructure

Run the built-in infrastructure check:

```bash
iottrafficgen run scenarios/benign/03_infrastructure.yaml
```

This verifies Apache, MariaDB, database schema, and web endpoint availability.

---

## 5. Network Capture Setup

To create labeled datasets, run a packet capture alongside `iottrafficgen`. The ground-truth markers (UDP packets on port 55556) are embedded in the same capture, enabling precise labeling.

### tcpdump

```bash
# Capture all traffic on the lab interface
sudo tcpdump -i eth0 -w capture.pcap &

# Run a scenario
iottrafficgen run scenarios/nmap/01.yaml

# Stop capture
kill %1
```

### Wireshark / tshark

```bash
sudo tshark -i eth0 -w capture.pcap -f "not port 22"
```

### Filtering Markers

To extract ground-truth markers from a capture:

```bash
tshark -r capture.pcap -Y "udp.port == 55556" -T json
```

---

## 6. Verification Checklist

After installation, verify your setup:

```bash
# 1. iottrafficgen itself
iottrafficgen --version

# 2. Dry-run a scenario (no tools or network needed)
iottrafficgen run scenarios/nmap/01.yaml --dry-run

# 3. List all available scenarios
iottrafficgen list --count-only

# 4. Check external tools
nmap --version
hydra -h 2>&1 | head -1
sqlmap --version
sudo hping3 --version
which arpspoof

# 5. Check lab services (if using benign traffic)
iottrafficgen run scenarios/benign/03_infrastructure.yaml
```

> **Note:** Steps 4 and 5 are optional depending on which scenario categories you intend to use.
