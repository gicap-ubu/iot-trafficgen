#!/usr/bin/env bash
set -euo pipefail

: "${BROKER_IP:?BROKER_IP is required}"
: "${BROKER_PORT:?BROKER_PORT is required}"
: "${QOS:?QOS is required}"
: "${PAYLOAD_SIZE:?PAYLOAD_SIZE is required}"
: "${RATE:?RATE (pps) is required}"
: "${DURATION_SECONDS:?DURATION_SECONDS is required}"

RUN_ID="${RUN_ID:-run_unknown}"
OUT_DIR="${OUT_DIR:-runs/${RUN_ID}/mqtt_flood}"
PYTHON_SCRIPT="${PYTHON_SCRIPT:-mqtt_flood.py}"

mkdir -p "$OUT_DIR"

echo "[mqtt_flood] BROKER=${BROKER_IP}:${BROKER_PORT}"
echo "[mqtt_flood] QOS=${QOS}"
echo "[mqtt_flood] PAYLOAD_SIZE=${PAYLOAD_SIZE}"
echo "[mqtt_flood] RATE=${RATE} pps"
echo "[mqtt_flood] DURATION=${DURATION_SECONDS}s"
echo "[mqtt_flood] OUT_DIR=${OUT_DIR}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT_PATH="${SCRIPT_DIR}/${PYTHON_SCRIPT}"

if [[ ! -f "$PYTHON_SCRIPT_PATH" ]]; then
    echo "[mqtt_flood] ERROR: Python script not found: $PYTHON_SCRIPT_PATH"
    exit 1
fi

PYTHON_BIN=$(command -v python3 2>/dev/null || echo "python3")

if ! command -v "$PYTHON_BIN" &>/dev/null; then
    echo "[mqtt_flood] ERROR: python3 not found in PATH"
    exit 1
fi

if ! "$PYTHON_BIN" -c "import paho.mqtt.client" 2>/dev/null; then
    echo "[mqtt_flood] ERROR: paho-mqtt library not installed"
    exit 1
fi

OUTPUT_FILE="${OUT_DIR}/mqtt_output.txt"

printf '[mqtt_flood] CMD: timeout %s %s %s %s %s %s %s %s\n' \
    "$DURATION_SECONDS" "$PYTHON_BIN" "$PYTHON_SCRIPT_PATH" \
    "$BROKER_IP" "$BROKER_PORT" "$QOS" "$PAYLOAD_SIZE" "$RATE"

trap 'echo "[mqtt_flood] Interrupted"; exit 130' INT TERM

set +e
timeout "$DURATION_SECONDS" "$PYTHON_BIN" "$PYTHON_SCRIPT_PATH" \
    "$BROKER_IP" "$BROKER_PORT" "$QOS" "$PAYLOAD_SIZE" "$RATE" \
    > "$OUTPUT_FILE" 2>&1

EXIT_CODE=$?
set -e

if [[ $EXIT_CODE -eq 124 ]]; then
    echo "[mqtt_flood] Completed (timeout)"
    EXIT_CODE=0
elif [[ $EXIT_CODE -eq 130 ]]; then
    echo "[mqtt_flood] Interrupted"
else
    echo "[mqtt_flood] Exit code: $EXIT_CODE"
fi

if [[ -f "$OUTPUT_FILE" ]] && grep -q "Connection failed" "$OUTPUT_FILE"; then
    echo "[mqtt_flood] ERROR: Connection to MQTT broker failed"
fi

echo "[mqtt_flood] Completed"
exit $EXIT_CODE