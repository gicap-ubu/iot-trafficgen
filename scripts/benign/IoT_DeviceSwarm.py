#!/usr/bin/env python3
"""
IoT Device Swarm - Benign Traffic Generator
Simulates realistic IoT sensor behavior with MQTT, HTTP, and UDP protocols

Environment Variables:
    BROKER_IP: MQTT broker address (required)
    WEB_SERVER_IP: HTTP server address (required)
    BASE_IP: Base IP for virtual devices (default: 192.168.8)
    RANGE_START: First device ID (default: 150)
    RANGE_END: Last device ID (default: 179)
    DURATION_SECONDS: How long to run (optional, runs indefinitely if not set)
"""
from __future__ import annotations

import threading
import time
import random
import json
import socket
import sys
import os
from datetime import datetime
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    import requests as requests_module
    from paho.mqtt import client as mqtt_module

HAS_REQUESTS = False
HAS_MQTT = False

try:
    import requests
    from requests.adapters import HTTPAdapter
    HAS_REQUESTS = True
except ImportError:
    requests = None  # type: ignore[assignment]
    HTTPAdapter = None  # type: ignore[assignment, misc]
    print("[WARNING] requests library not installed. HTTP traffic will be disabled.")

try:
    import paho.mqtt.client as mqtt
    HAS_MQTT = True
except ImportError:
    mqtt = None  # type: ignore[assignment]
    print("[WARNING] paho-mqtt library not installed. MQTT traffic will be disabled.")

BROKER_IP: Optional[str] = os.environ.get('BROKER_IP')
WEB_SERVER_IP: Optional[str] = os.environ.get('WEB_SERVER_IP')
BASE_IP: str = os.environ.get('BASE_IP', '192.168.8')
RANGE_START: int = int(os.environ.get('RANGE_START', '150'))
RANGE_END: int = int(os.environ.get('RANGE_END', '179'))

DURATION_SECONDS: Optional[int] = None
duration_str = os.environ.get('DURATION_SECONDS')
if duration_str:
    try:
        DURATION_SECONDS = int(duration_str)
    except (ValueError, TypeError):
        pass

if not BROKER_IP:
    sys.exit("[ERROR] BROKER_IP environment variable is required")
if not WEB_SERVER_IP:
    sys.exit("[ERROR] WEB_SERVER_IP environment variable is required")

BROKER_IP_VALIDATED: str = BROKER_IP
WEB_SERVER_IP_VALIDATED: str = WEB_SERVER_IP

DEBUG: bool = os.environ.get('DEBUG', 'false').lower() == 'true'
print_lock = threading.Lock()


def log(ip: str, msg: str, level: str = "INFO") -> None:
    """Thread-safe logging"""
    if not DEBUG and level == "INFO":
        return
    timestamp = datetime.now().strftime("%H:%M:%S")
    with print_lock:
        print(f"[{timestamp}] [{ip}] {msg}")


class IotDevice(threading.Thread):
    def __init__(self, ip: str, dev_id: int) -> None:
        super().__init__()
        self.ip = ip
        self.dev_id = dev_id
        self.daemon = True
        self.running = True

        self.personality = dev_id % 3

        self.temp = random.uniform(20.0, 30.0)
        self.battery = random.uniform(80.0, 100.0)
        self.pressure = random.uniform(1000.0, 1015.0)

        self.http_session: Optional[requests_module.Session] = None
        if HAS_REQUESTS and requests is not None:
            self.http_session = requests.Session()
            if HTTPAdapter is not None:
                self.http_session.mount('http://', HTTPAdapter())

    def update_physics(self) -> None:
        """Update sensor readings with random walk"""
        self.temp += random.uniform(-0.5, 0.5)
        self.temp = max(15.0, min(self.temp, 90.0))

        self.battery -= random.uniform(0.001, 0.01)
        if self.battery < 10.0:
            self.battery = random.uniform(90.0, 100.0)

        self.pressure += random.uniform(-1.0, 1.0)
        self.pressure = max(800.0, self.pressure)

    def send_mqtt(self) -> None:
        """Send telemetry via MQTT"""
        if not HAS_MQTT or mqtt is None:
            return

        client = mqtt.Client(client_id=f"Dev_{self.dev_id}_{random.randint(1000, 9999)}")
        try:
            client.connect(BROKER_IP_VALIDATED, 1883, 60, bind_address=self.ip)

            payload = {
                "id": self.dev_id,
                "t": round(self.temp, 2),
                "p": round(self.pressure, 1),
                "v": round(self.battery, 2),
                "ts": time.time()
            }
            client.publish(f"planta/sensor/{self.dev_id}", json.dumps(payload))
            client.disconnect()

            if DEBUG:
                log(self.ip, f"MQTT sent: temp={payload['t']}", "DEBUG")
        except Exception as e:
            if DEBUG:
                log(self.ip, f"MQTT error: {e}", "DEBUG")

    def send_http(self) -> None:
        """Send battery status via HTTP"""
        if not HAS_REQUESTS or self.http_session is None:
            return

        try:
            url = f"http://{WEB_SERVER_IP_VALIDATED}/index.php?id={self.dev_id}&batt={int(self.battery)}"
            self.http_session.get(url, timeout=1)

            if DEBUG:
                log(self.ip, f"HTTP sent: battery={int(self.battery)}", "DEBUG")
        except Exception as e:
            if DEBUG:
                log(self.ip, f"HTTP error: {e}", "DEBUG")

    def send_udp(self) -> None:
        """Send keepalive via UDP"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.bind((self.ip, 0))
                msg = f"KEEP_ALIVE:{self.dev_id}".encode()
                sock.sendto(msg, (BROKER_IP_VALIDATED, 8888))

                if DEBUG:
                    log(self.ip, "UDP keepalive sent", "DEBUG")
        except Exception as e:
            if DEBUG:
                log(self.ip, f"UDP error: {e}", "DEBUG")

    def stop(self) -> None:
        """Stop the device thread"""
        self.running = False

    def run(self) -> None:
        """Main device loop"""
        time.sleep(random.uniform(0, 5))
        log(self.ip, f"Started. Personality: {self.personality} (0=Hybrid, 1=MQTT, 2=Legacy)")

        while self.running:
            self.update_physics()

            if self.personality == 0:
                self.send_mqtt()
                if random.random() < 0.3:
                    self.send_http()

            elif self.personality == 1:
                self.send_mqtt()

            elif self.personality == 2:
                self.send_udp()
                if random.random() < 0.4:
                    self.send_http()
                if random.random() < 0.2:
                    self.send_mqtt()

            time.sleep(random.uniform(3.0, 6.0))


if __name__ == "__main__":
    if os.geteuid() != 0:
        sys.exit("[iot_swarm] ERROR: Root privileges required (use sudo)")

    device_count = RANGE_END - RANGE_START + 1

    print(f"[iot_swarm] Starting IoT Device Swarm")
    print(f"[iot_swarm] Devices: {device_count} (IDs {RANGE_START}-{RANGE_END})")
    print(f"[iot_swarm] MQTT Broker: {BROKER_IP_VALIDATED}")
    print(f"[iot_swarm] HTTP Server: {WEB_SERVER_IP_VALIDATED}")
    if DURATION_SECONDS:
        print(f"[iot_swarm] Duration: {DURATION_SECONDS}s")
    else:
        print(f"[iot_swarm] Duration: Indefinite")
    print(f"[iot_swarm] Base IP: {BASE_IP}")

    threads: list[IotDevice] = []
    for i in range(RANGE_START, RANGE_END + 1):
        ip = f"{BASE_IP}.{i}"
        device = IotDevice(ip, i)
        device.start()
        threads.append(device)

    print(f"[iot_swarm] {len(threads)} devices running")

    try:
        if DURATION_SECONDS:
            print(f"[iot_swarm] Will stop automatically after {DURATION_SECONDS}s")
            time.sleep(DURATION_SECONDS)
            print(f"\n[iot_swarm] Duration completed ({DURATION_SECONDS}s)")
        else:
            print(f"[iot_swarm] Running indefinitely (press Ctrl+C to stop)")
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        print("\n[iot_swarm] Stopped by user")
    finally:
        for device in threads:
            device.stop()

        for device in threads:
            device.join(timeout=2)

        print("[iot_swarm] Completed")