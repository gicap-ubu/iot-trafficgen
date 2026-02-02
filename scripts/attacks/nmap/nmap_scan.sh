#!/usr/bin/env bash
set -euo pipefail

: "${TARGET_IP:?TARGET_IP is required}"

# Preferimos TOOL_ARGS. (Compat: si viene NMAP_ARGS, lo aceptamos.)
TOOL_ARGS="${TOOL_ARGS:-${NMAP_ARGS:-}}"
: "${TOOL_ARGS:?TOOL_ARGS is required}"

RUN_ID="${RUN_ID:-run_unknown}"
OUT_DIR="${OUT_DIR:-runs/${RUN_ID}/nmap}"
mkdir -p "$OUT_DIR"

echo "[nmap_scan] TARGET=${TARGET_IP}"
echo "[nmap_scan] TOOL_ARGS=${TOOL_ARGS}"
echo "[nmap_scan] OUT_DIR=${OUT_DIR}"

# IMPORTANT: evitar que nmap lea NMAP_ARGS del entorno
unset NMAP_ARGS

# Limpia CRLF y construye argv
ARGS_CLEAN="$(printf "%s" "$TOOL_ARGS" | tr -d '\r')"
read -r -a ARGS <<< "$ARGS_CLEAN"

# Detectar binario de nmap automáticamente
NMAP_BIN=$(command -v nmap 2>/dev/null || echo "nmap")

printf '[nmap_scan] CMD: %s' "$NMAP_BIN"
for a in "${ARGS[@]}"; do printf ' %q' "$a"; done
printf ' -oA %q %q\n' "${OUT_DIR}/scan" "$TARGET_IP"

# Ejecutar nmap
"$NMAP_BIN" "${ARGS[@]}" -oA "${OUT_DIR}/scan" "$TARGET_IP"

echo "[nmap_scan] Completed"