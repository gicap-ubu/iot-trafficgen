#!/usr/bin/env python3
"""
MQTT to SQL Bridge
Subscribes to MQTT topics and writes data to MariaDB/MySQL database

Environment Variables:
    MQTT_BROKER: MQTT broker address (default: localhost)
    DB_HOST: Database server address (required)
    DB_USER: Database username (default: admin_iot)
    DB_PASSWORD: Database password (default: secreto)
    DB_NAME: Database name (default: iot_db)
    MQTT_TOPIC: MQTT topic to subscribe (default: planta/#)
    DURATION_SECONDS: How long to run (optional, runs forever if not set)
"""
import json
import threading
import sys
import os
import time
from datetime import datetime

# Check for required dependencies
try:
    import paho.mqtt.client as mqtt
    HAS_MQTT = True
except ImportError:
    print("[ERROR] paho-mqtt library not installed", file=sys.stderr)
    print("Install: pip install paho-mqtt", file=sys.stderr)
    sys.exit(1)

try:
    import mysql.connector
    HAS_MYSQL = True
except ImportError:
    print("[ERROR] mysql-connector-python library not installed", file=sys.stderr)
    print("Install: pip install mysql-connector-python", file=sys.stderr)
    sys.exit(1)

# ================= CONFIGURATION FROM ENVIRONMENT =================
MQTT_BROKER = os.environ.get('MQTT_BROKER', 'localhost')
MQTT_TOPIC = os.environ.get('MQTT_TOPIC', 'planta/#')

DB_HOST = os.environ.get('DB_HOST')
DB_USER = os.environ.get('DB_USER', 'admin_iot')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'secreto')
DB_NAME = os.environ.get('DB_NAME', 'iot_db')

DURATION_SECONDS = os.environ.get('DURATION_SECONDS')

# Validate required parameters
if not DB_HOST:
    sys.exit("[mqtt_bridge] ERROR: DB_HOST environment variable is required")

DB_CONFIG = {
    'user': DB_USER,
    'password': DB_PASSWORD,
    'host': DB_HOST,
    'database': DB_NAME
}

# Statistics
stats = {
    'received': 0,
    'written': 0,
    'errors': 0
}

# ================= SQL WRITE FUNCTION (THREADED) =================
def write_to_sql(sensor_data):
    """
    Write sensor data to remote database
    Executed in separate thread to avoid blocking MQTT callback
    """
    try:
        sensor_id = sensor_data.get('id', 0)
        data_val = sensor_data.get('v', 0.0)
        
        if sensor_id == 0:
            return

        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        sql = "UPDATE sensores SET valor = %s, fecha = NOW() WHERE id = %s"
        cursor.execute(sql, (data_val, sensor_id))

        conn.commit()
        cursor.close()
        conn.close()

        stats['written'] += 1
        print(f"[mqtt_bridge] SQL OK: ID {sensor_id} = {data_val}")

    except mysql.connector.Error as err:
        stats['errors'] += 1
        print(f"[mqtt_bridge] SQL ERROR: {err}", file=sys.stderr)
    except Exception as e:
        stats['errors'] += 1
        print(f"[mqtt_bridge] ERROR: {e}", file=sys.stderr)

# ================= MQTT CALLBACKS =================
def on_connect(client, userdata, flags, rc):
    """Called when connected to MQTT broker"""
    if rc == 0:
        print(f"[mqtt_bridge] Connected to MQTT broker: {MQTT_BROKER}")
        print(f"[mqtt_bridge] Subscribing to: {MQTT_TOPIC}")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"[mqtt_bridge] Connection failed: {rc}", file=sys.stderr)
        sys.exit(1)

def on_message(client, userdata, msg):
    """Called when MQTT message received"""
    try:
        payload = msg.payload.decode('utf-8')
        data = json.loads(payload)
        
        stats['received'] += 1
        print(f"[mqtt_bridge] Received ID {data.get('id', 'N/A')} on {msg.topic}")

        # Launch SQL write in separate thread to avoid blocking
        t = threading.Thread(target=write_to_sql, args=(data,))
        t.daemon = True
        t.start()

    except json.JSONDecodeError as e:
        stats['errors'] += 1
        print(f"[mqtt_bridge] JSON decode error: {e}", file=sys.stderr)
    except Exception as e:
        stats['errors'] += 1
        print(f"[mqtt_bridge] Message error: {e}", file=sys.stderr)

# ================= MAIN =================
if __name__ == '__main__':
    print(f"[mqtt_bridge] Starting MQTT to SQL Bridge")
    print(f"[mqtt_bridge] MQTT: {MQTT_BROKER} / Topic: {MQTT_TOPIC}")
    print(f"[mqtt_bridge] Database: {DB_USER}@{DB_HOST}/{DB_NAME}")
    
    if DURATION_SECONDS:
        duration = int(DURATION_SECONDS)
        print(f"[mqtt_bridge] Duration: {duration}s")
    else:
        print(f"[mqtt_bridge] Duration: Infinite (Ctrl+C to stop)")

    # Test database connection
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        conn.close()
        print(f"[mqtt_bridge] Database connection OK")
    except mysql.connector.Error as err:
        print(f"[mqtt_bridge] Database connection FAILED: {err}", file=sys.stderr)
        sys.exit(1)

    # Setup MQTT client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(MQTT_BROKER, 1883, 60)
        
        # Run for specified duration or forever
        if DURATION_SECONDS:
            duration = int(DURATION_SECONDS)
            client.loop_start()
            
            start_time = time.time()
            while time.time() - start_time < duration:
                time.sleep(1)
            
            client.loop_stop()
            print(f"\n[mqtt_bridge] Duration completed ({duration}s)")
        else:
            client.loop_forever()
            
    except KeyboardInterrupt:
        print("\n[mqtt_bridge] Interrupted by user")
    except Exception as e:
        print(f"[mqtt_bridge] Fatal error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        client.disconnect()
        print(f"[mqtt_bridge] Statistics:")
        print(f"  Received: {stats['received']}")
        print(f"  Written:  {stats['written']}")
        print(f"  Errors:   {stats['errors']}")
        print(f"[mqtt_bridge] Completed")