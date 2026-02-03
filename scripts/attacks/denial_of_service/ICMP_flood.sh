#!/usr/bin/env bash
set -euo pipefail

: "${TARGET_IP:?TARGET_IP is required}"
: "${DURATION_SECONDS:?DURATION_SECONDS is required}"

TOOL_ARGS="${TOOL_ARGS:-}"
RUN_ID="${RUN_ID:-run_unknown}"
OUT_DIR="${OUT_DIR:-runs/${RUN_ID}/icmp_flood}"

mkdir -p "$OUT_DIR"

echo "[icmp_flood] TARGET=${TARGET_IP}"
echo "[icmp_flood] DURATION=${DURATION_SECONDS}s"
echo "[icmp_flood] TOOL_ARGS=${TOOL_ARGS}"
echo "[icmp_flood] OUT_DIR=${OUT_DIR}"

HPING_BIN=$(command -v hping3 2>/dev/null || echo "hping3")

if ! command -v "$HPING_BIN" &>/dev/null; then
    echo "[icmp_flood] ERROR: hping3 not found in PATH"
    exit 1
fi

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
    echo "[icmp_flood] WARNING: hping3 requires root privileges"
fi

read -r -a ARGS <<< "$TOOL_ARGS"

OUTPUT_FILE="${OUT_DIR}/hping3_output.txt"

printf '[icmp_flood] CMD: timeout %s %s --icmp' "$DURATION_SECONDS" "$HPING_BIN"
for a in "${ARGS[@]}"; do printf ' %q' "$a"; done
printf ' %q > %q 2>&1\n' "$TARGET_IP" "$OUTPUT_FILE"

trap 'echo "[icmp_flood] Interrupted"; exit 130' INT TERM

set +e
timeout "$DURATION_SECONDS" "$HPING_BIN" \
    --icmp \
    "${ARGS[@]}" \
    "$TARGET_IP" \
    > "$OUTPUT_FILE" 2>&1

EXIT_CODE=$?
set -e

if [[ $EXIT_CODE -eq 124 ]]; then
    echo "[icmp_flood] Completed (timeout)"
    EXIT_CODE=0
elif [[ $EXIT_CODE -eq 130 ]]; then
    echo "[icmp_flood] Interrupted"
else
    echo "[icmp_flood] Exit code: $EXIT_CODE"
fi

echo "[icmp_flood] Completed"
exit $EXIT_CODE