#!/usr/bin/env bash
set -euo pipefail

: "${BROKER_IP:?BROKER_IP is required}"
: "${BROKER_PORT:?BROKER_PORT is required}"
: "${TOPIC1:?TOPIC1 is required}"
: "${TOPIC2:?TOPIC2 is required}"
: "${MALICIOUS_VALUE:?MALICIOUS_VALUE is required}"
: "${BASE_DELAY:?BASE_DELAY is required}"
: "${JITTER:?JITTER is required}"

RUN_ID="${RUN_ID:-run_unknown}"
OUT_DIR="${OUT_DIR:-runs/${RUN_ID}/mqtt_injection}"
PYTHON_SCRIPT="${PYTHON_SCRIPT:-mqtt_injection.py}"

mkdir -p "$OUT_DIR"

echo "[mqtt_injection] BROKER=${BROKER_IP}:${BROKER_PORT}"
echo "[mqtt_injection] TOPICS=${TOPIC1}, ${TOPIC2}"
echo "[mqtt_injection] MALICIOUS_VALUE=${MALICIOUS_VALUE}"
echo "[mqtt_injection] BASE_DELAY=${BASE_DELAY}s"
echo "[mqtt_injection] JITTER=${JITTER}s"
echo "[mqtt_injection] OUT_DIR=${OUT_DIR}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT_PATH="${SCRIPT_DIR}/${PYTHON_SCRIPT}"

if [[ ! -f "$PYTHON_SCRIPT_PATH" ]]; then
    echo "[mqtt_injection] ERROR: Python script not found: $PYTHON_SCRIPT_PATH"
    echo "[mqtt_injection] Make sure mqtt_injection.py is in the same directory"
    exit 1
fi

if ! command -v python3 &>/dev/null; then
    echo "[mqtt_injection] ERROR: python3 not found in PATH"
    exit 1
fi

if ! python3 -c "import paho.mqtt.client" 2>/dev/null; then
    echo "[mqtt_injection] ERROR: paho-mqtt library not installed"
    echo "[mqtt_injection] Install: pip install paho-mqtt"
    exit 1
fi

OUTPUT_FILE="${OUT_DIR}/mqtt_injection_output.txt"

echo "[mqtt_injection] CMD: python3 $PYTHON_SCRIPT_PATH $BROKER_IP $BROKER_PORT $TOPIC1 $TOPIC2 $MALICIOUS_VALUE $BASE_DELAY $JITTER"
echo "[mqtt_injection] Starting MQTT false data injection..."
echo "[mqtt_injection] Press Ctrl+C to stop"

set +e
python3 "$PYTHON_SCRIPT_PATH" "$BROKER_IP" "$BROKER_PORT" "$TOPIC1" "$TOPIC2" "$MALICIOUS_VALUE" "$BASE_DELAY" "$JITTER" > "$OUTPUT_FILE" 2>&1 &

PYTHON_PID=$!
echo "[mqtt_injection] Python PID: $PYTHON_PID"

wait $PYTHON_PID
EXIT_CODE=$?
set -e

echo "[mqtt_injection] Python exit code: $EXIT_CODE"

if [[ -f "$OUTPUT_FILE" ]]; then
    echo "[mqtt_injection] Output saved to: $OUTPUT_FILE"
    
    if grep -q "Connection failed" "$OUTPUT_FILE"; then
        echo "[mqtt_injection] ERROR: Connection to MQTT broker failed"
        cat "$OUTPUT_FILE"
    fi
else
    echo "[mqtt_injection] WARNING: No output file generated"
fi

echo "[mqtt_injection] Completed"
exit $EXIT_CODE
