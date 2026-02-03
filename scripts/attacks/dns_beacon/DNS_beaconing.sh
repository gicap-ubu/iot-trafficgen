#!/usr/bin/env bash
set -euo pipefail

: "${RESOLVER_IP:?RESOLVER_IP is required}"
: "${INTERVAL:?INTERVAL is required}"
: "${JITTER:?JITTER is required}"
: "${LABEL_LEN:?LABEL_LEN is required}"
: "${DURATION_SECONDS:?DURATION_SECONDS is required}"

RUN_ID="${RUN_ID:-run_unknown}"
OUT_DIR="${OUT_DIR:-runs/${RUN_ID}/dns_beacon}"
PYTHON_SCRIPT="${PYTHON_SCRIPT:-dns_beaconing.py}"

mkdir -p "$OUT_DIR"

echo "[dns_beacon] RESOLVER=${RESOLVER_IP}"
echo "[dns_beacon] INTERVAL=${INTERVAL}s"
echo "[dns_beacon] JITTER=${JITTER}"
echo "[dns_beacon] LABEL_LEN=${LABEL_LEN}"
echo "[dns_beacon] DURATION=${DURATION_SECONDS}s"
echo "[dns_beacon] OUT_DIR=${OUT_DIR}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT_PATH="${SCRIPT_DIR}/${PYTHON_SCRIPT}"

if [[ ! -f "$PYTHON_SCRIPT_PATH" ]]; then
    echo "[dns_beacon] ERROR: Python script not found: $PYTHON_SCRIPT_PATH"
    exit 1
fi

PYTHON_BIN=$(command -v python3 2>/dev/null || echo "python3")

if ! command -v "$PYTHON_BIN" &>/dev/null; then
    echo "[dns_beacon] ERROR: python3 not found in PATH"
    exit 1
fi

if ! "$PYTHON_BIN" -c "import dns.resolver" 2>/dev/null; then
    echo "[dns_beacon] ERROR: dnspython library not installed"
    exit 1
fi

OUTPUT_FILE="${OUT_DIR}/dns_beacon_output.txt"

printf '[dns_beacon] CMD: timeout %s %s %s %s %s %s %s\n' \
    "$DURATION_SECONDS" "$PYTHON_BIN" "$PYTHON_SCRIPT_PATH" \
    "$RESOLVER_IP" "$INTERVAL" "$JITTER" "$LABEL_LEN"

trap 'echo "[dns_beacon] Interrupted"; exit 130' INT TERM

set +e
timeout "$DURATION_SECONDS" "$PYTHON_BIN" "$PYTHON_SCRIPT_PATH" \
    "$RESOLVER_IP" "$INTERVAL" "$JITTER" "$LABEL_LEN" \
    > "$OUTPUT_FILE" 2>&1

EXIT_CODE=$?
set -e

if [[ $EXIT_CODE -eq 124 ]]; then
    echo "[dns_beacon] Completed (timeout)"
    EXIT_CODE=0
elif [[ $EXIT_CODE -eq 130 ]]; then
    echo "[dns_beacon] Interrupted"
else
    echo "[dns_beacon] Exit code: $EXIT_CODE"
fi

echo "[dns_beacon] Completed"
exit $EXIT_CODE