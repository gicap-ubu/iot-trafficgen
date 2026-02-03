#!/usr/bin/env bash
set -euo pipefail

: "${TARGET_IP:?TARGET_IP is required}"

TOOL_ARGS="${TOOL_ARGS:-${NMAP_ARGS:-}}"
: "${TOOL_ARGS:?TOOL_ARGS is required}"

RUN_ID="${RUN_ID:-run_unknown}"
OUT_DIR="${OUT_DIR:-runs/${RUN_ID}/nmap}"
mkdir -p "$OUT_DIR"

echo "[nmap_scan] TARGET=${TARGET_IP}"
echo "[nmap_scan] TOOL_ARGS=${TOOL_ARGS}"
echo "[nmap_scan] OUT_DIR=${OUT_DIR}"

unset NMAP_ARGS

ARGS_CLEAN="$(printf "%s" "$TOOL_ARGS" | tr -d '\r')"
read -r -a ARGS <<< "$ARGS_CLEAN"

NMAP_BIN=$(command -v nmap 2>/dev/null || echo "nmap")

if ! command -v "$NMAP_BIN" &>/dev/null; then
    echo "[nmap_scan] ERROR: nmap not found in PATH"
    exit 1
fi

printf '[nmap_scan] CMD: %s' "$NMAP_BIN"
for a in "${ARGS[@]}"; do printf ' %q' "$a"; done
printf ' -oA %q %q\n' "${OUT_DIR}/scan" "$TARGET_IP"

trap 'echo "[nmap_scan] Interrupted"; exit 130' INT TERM

set +e
"$NMAP_BIN" "${ARGS[@]}" -oA "${OUT_DIR}/scan" "$TARGET_IP"
EXIT_CODE=$?
set -e

if [[ $EXIT_CODE -eq 130 ]]; then
    echo "[nmap_scan] Interrupted"
elif [[ $EXIT_CODE -eq 0 ]]; then
    echo "[nmap_scan] Completed"
else
    echo "[nmap_scan] Exit code: $EXIT_CODE"
fi

exit $EXIT_CODE