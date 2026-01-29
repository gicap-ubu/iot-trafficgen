"""
Ground truth marker system for traffic synchronization
"""
import json
import socket
import time
from datetime import datetime
from typing import Any

import click


class MarkerSystem:
    """Sends UDP markers for traffic synchronization with network captures"""
    
    def __init__(
        self,
        enabled: bool = True,
        host: str = "127.0.0.1",
        port: int = 55556,
    ):
        self.enabled = enabled
        self.host = host
        self.port = port
    
    def send(
        self,
        event: str,
        attack_id: str,
        attack_name: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Send a ground truth marker via UDP.
        
        Args:
            event: Event type (ATTACK_START, ATTACK_END)
            attack_id: Unique identifier for this attack run
            attack_name: Human-readable attack name
            metadata: Additional metadata to include in marker
        """
        if not self.enabled:
            return
        
        payload = {
            "type": "GROUND_TRUTH",
            "event": event,
            "attack_id": attack_id,
            "attack": attack_name,
            "ts_unix": int(time.time()),
            "ts_iso_utc": datetime.utcnow().isoformat() + "Z",
            "duration_mode": "EPISODIC",
        }
        
        if metadata:
            payload.update(metadata)
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(1.0)
            sock.sendto(
                json.dumps(payload).encode("utf-8"),
                (self.host, self.port)
            )
            sock.close()
            click.echo(f"    → Marker: {event} → {self.host}:{self.port}")
        except socket.timeout:
            click.secho(f"    ⚠ Marker timeout: {self.host}:{self.port}", fg="yellow")
        except Exception as e:
            click.secho(f"    ⚠ Marker error: {e}", fg="yellow")


def create_marker_system_from_scenario(scenario_data: dict) -> MarkerSystem:
    """
    Create a MarkerSystem from scenario configuration.
    
    Args:
        scenario_data: Parsed scenario YAML data
        
    Returns:
        Configured MarkerSystem instance
    """
    scenario_meta = scenario_data.get("scenario", {})
    markers_config = scenario_meta.get("markers", {})
    
    return MarkerSystem(
        enabled=markers_config.get("enabled", True),
        host=markers_config.get("host", "127.0.0.1"),
        port=markers_config.get("port", 55556),
    )