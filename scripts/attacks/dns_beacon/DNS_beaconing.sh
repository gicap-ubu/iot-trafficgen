#!/usr/bin/env bash
set -euo pipefail

: "${RESOLVER_IP:?RESOLVER_IP is required}"
: "${INTERVAL:?INTERVAL is required}"
: "${JITTER:?JITTER is required}"
: "${LABEL_LEN:?LABEL_LEN is required}"

RUN_ID="${RUN_ID:-run_unknown}"
OUT_DIR="${OUT_DIR:-runs/${RUN_ID}/dns_beacon}"
PYTHON_SCRIPT="${PYTHON_SCRIPT:-dns_beaconing.py}"

mkdir -p "$OUT_DIR"

echo "[dns_beacon] RESOLVER=${RESOLVER_IP}"
echo "[dns_beacon] INTERVAL=${INTERVAL}s"
echo "[dns_beacon] JITTER=${JITTER}"
echo "[dns_beacon] LABEL_LEN=${LABEL_LEN}"
echo "[dns_beacon] OUT_DIR=${OUT_DIR}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT_PATH="${SCRIPT_DIR}/${PYTHON_SCRIPT}"

if [[ ! -f "$PYTHON_SCRIPT_PATH" ]]; then
    echo "[dns_beacon] ERROR: Python script not found: $PYTHON_SCRIPT_PATH"
    exit 1
fi

if ! command -v python3 &>/dev/null; then
    echo "[dns_beacon] ERROR: python3 not found in PATH"
    exit 1
fi

if ! python3 -c "import dns.resolver" 2>/dev/null; then
    echo "[dns_beacon] ERROR: dnspython library not installed"
    echo "[dns_beacon] Install: pip install dnspython"
    exit 1
fi

OUTPUT_FILE="${OUT_DIR}/dns_beacon_output.txt"

echo "[dns_beacon] CMD: python3 $PYTHON_SCRIPT_PATH $RESOLVER_IP $INTERVAL $JITTER $LABEL_LEN"
echo "[dns_beacon] Starting DNS beaconing attack..."
echo "[dns_beacon] Press Ctrl+C to stop"

set +e
python3 "$PYTHON_SCRIPT_PATH" "$RESOLVER_IP" "$INTERVAL" "$JITTER" "$LABEL_LEN" > "$OUTPUT_FILE" 2>&1 &

PYTHON_PID=$!
echo "[dns_beacon] Python PID: $PYTHON_PID"

wait $PYTHON_PID
EXIT_CODE=$?
set -e

echo "[dns_beacon] Python exit code: $EXIT_CODE"

if [[ -f "$OUTPUT_FILE" ]]; then
    echo "[dns_beacon] Output saved to: $OUTPUT_FILE"
else
    echo "[dns_beacon] WARNING: No output file generated"
fi

echo "[dns_beacon] Completed"
exit $EXIT_CODE
