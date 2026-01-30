#!/usr/bin/env bash
set -euo pipefail

: "${BROKER_IP:?BROKER_IP is required}"
: "${BROKER_PORT:?BROKER_PORT is required}"
: "${QOS:?QOS is required}"
: "${PAYLOAD_SIZE:?PAYLOAD_SIZE is required}"
: "${RATE:?RATE (pps) is required}"

RUN_ID="${RUN_ID:-run_unknown}"
OUT_DIR="${OUT_DIR:-runs/${RUN_ID}/mqtt_flood}"
PYTHON_SCRIPT="${PYTHON_SCRIPT:-mqtt_flood.py}"

mkdir -p "$OUT_DIR"

echo "[mqtt_flood] BROKER=${BROKER_IP}:${BROKER_PORT}"
echo "[mqtt_flood] QOS=${QOS}"
echo "[mqtt_flood] PAYLOAD_SIZE=${PAYLOAD_SIZE}"
echo "[mqtt_flood] RATE=${RATE} pps"
echo "[mqtt_flood] OUT_DIR=${OUT_DIR}"
echo "[mqtt_flood] PYTHON_SCRIPT=${PYTHON_SCRIPT}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT_PATH="${SCRIPT_DIR}/${PYTHON_SCRIPT}"

if [[ ! -f "$PYTHON_SCRIPT_PATH" ]]; then
    echo "[mqtt_flood] ERROR: Python script not found: $PYTHON_SCRIPT_PATH"
    echo "[mqtt_flood] Make sure mqtt_flood.py is in the same directory as this script"
    exit 1
fi

if ! command -v python3 &>/dev/null; then
    echo "[mqtt_flood] ERROR: python3 not found in PATH"
    exit 1
fi

if ! python3 -c "import paho.mqtt.client" 2>/dev/null; then
    echo "[mqtt_flood] ERROR: paho-mqtt library not installed"
    echo "[mqtt_flood] Install: pip install paho-mqtt"
    exit 1
fi

OUTPUT_FILE="${OUT_DIR}/mqtt_output.txt"

echo "[mqtt_flood] CMD: python3 $PYTHON_SCRIPT_PATH $BROKER_IP $BROKER_PORT $QOS $PAYLOAD_SIZE $RATE"
echo "[mqtt_flood] Starting MQTT flood attack..."
echo "[mqtt_flood] Press Ctrl+C to stop"

set +e
python3 "$PYTHON_SCRIPT_PATH" "$BROKER_IP" "$BROKER_PORT" "$QOS" "$PAYLOAD_SIZE" "$RATE" > "$OUTPUT_FILE" 2>&1 &

PYTHON_PID=$!
echo "[mqtt_flood] Python PID: $PYTHON_PID"

wait $PYTHON_PID
EXIT_CODE=$?
set -e

echo "[mqtt_flood] Python exit code: $EXIT_CODE"

if [[ -f "$OUTPUT_FILE" ]]; then
    echo "[mqtt_flood] Output saved to: $OUTPUT_FILE"
    OUT_LINES=$(wc -l < "$OUTPUT_FILE" 2>/dev/null || echo "0")
    echo "[mqtt_flood] Output lines: $OUT_LINES"
    
    if grep -q "Connection failed" "$OUTPUT_FILE"; then
        echo "[mqtt_flood] ERROR: Connection to MQTT broker failed"
        cat "$OUTPUT_FILE"
    fi
else
    echo "[mqtt_flood] WARNING: No output file generated"
fi

echo "[mqtt_flood] Completed"
exit $EXIT_CODE
