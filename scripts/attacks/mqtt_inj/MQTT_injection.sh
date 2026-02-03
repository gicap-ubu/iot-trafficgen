#!/usr/bin/env bash
set -euo pipefail

: "${BROKER_IP:?BROKER_IP is required}"
: "${BROKER_PORT:?BROKER_PORT is required}"
: "${TOPIC1:?TOPIC1 is required}"
: "${TOPIC2:?TOPIC2 is required}"
: "${MALICIOUS_VALUE:?MALICIOUS_VALUE is required}"
: "${BASE_DELAY:?BASE_DELAY is required}"
: "${JITTER:?JITTER is required}"
: "${DURATION_SECONDS:?DURATION_SECONDS is required}"

RUN_ID="${RUN_ID:-run_unknown}"
OUT_DIR="${OUT_DIR:-runs/${RUN_ID}/mqtt_injection}"
PYTHON_SCRIPT="${PYTHON_SCRIPT:-mqtt_injection.py}"

mkdir -p "$OUT_DIR"

echo "[mqtt_injection] BROKER=${BROKER_IP}:${BROKER_PORT}"
echo "[mqtt_injection] TOPICS=${TOPIC1}, ${TOPIC2}"
echo "[mqtt_injection] MALICIOUS_VALUE=${MALICIOUS_VALUE}"
echo "[mqtt_injection] BASE_DELAY=${BASE_DELAY}s"
echo "[mqtt_injection] JITTER=${JITTER}s"
echo "[mqtt_injection] DURATION=${DURATION_SECONDS}s"
echo "[mqtt_injection] OUT_DIR=${OUT_DIR}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT_PATH="${SCRIPT_DIR}/${PYTHON_SCRIPT}"

if [[ ! -f "$PYTHON_SCRIPT_PATH" ]]; then
    echo "[mqtt_injection] ERROR: Python script not found: $PYTHON_SCRIPT_PATH"
    exit 1
fi

PYTHON_BIN=$(command -v python3 2>/dev/null || echo "python3")

if ! command -v "$PYTHON_BIN" &>/dev/null; then
    echo "[mqtt_injection] ERROR: python3 not found in PATH"
    exit 1
fi

if ! "$PYTHON_BIN" -c "import paho.mqtt.client" 2>/dev/null; then
    echo "[mqtt_injection] ERROR: paho-mqtt library not installed"
    exit 1
fi

OUTPUT_FILE="${OUT_DIR}/mqtt_injection_output.txt"

printf '[mqtt_injection] CMD: timeout %s %s %s %s %s %s %s %s %s %s\n' \
    "$DURATION_SECONDS" "$PYTHON_BIN" "$PYTHON_SCRIPT_PATH" \
    "$BROKER_IP" "$BROKER_PORT" "$TOPIC1" "$TOPIC2" \
    "$MALICIOUS_VALUE" "$BASE_DELAY" "$JITTER"

trap 'echo "[mqtt_injection] Interrupted"; exit 130' INT TERM

set +e
timeout "$DURATION_SECONDS" "$PYTHON_BIN" "$PYTHON_SCRIPT_PATH" \
    "$BROKER_IP" "$BROKER_PORT" "$TOPIC1" "$TOPIC2" \
    "$MALICIOUS_VALUE" "$BASE_DELAY" "$JITTER" \
    > "$OUTPUT_FILE" 2>&1

EXIT_CODE=$?
set -e

if [[ $EXIT_CODE -eq 124 ]]; then
    echo "[mqtt_injection] Completed (timeout)"
    EXIT_CODE=0
elif [[ $EXIT_CODE -eq 130 ]]; then
    echo "[mqtt_injection] Interrupted"
else
    echo "[mqtt_injection] Exit code: $EXIT_CODE"
fi

if [[ -f "$OUTPUT_FILE" ]] && grep -q "Connection failed" "$OUTPUT_FILE"; then
    echo "[mqtt_injection] ERROR: Connection to MQTT broker failed"
fi

echo "[mqtt_injection] Completed"
exit $EXIT_CODE