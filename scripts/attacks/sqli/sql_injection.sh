#!/usr/bin/env bash
set -euo pipefail

: "${TARGET_URL:?TARGET_URL is required}"
: "${SQLMAP_OUTPUT_DIR:?SQLMAP_OUTPUT_DIR is required}"

TOOL_ARGS="${TOOL_ARGS:-}"
RUN_ID="${RUN_ID:-run_unknown}"
OUT_DIR="${OUT_DIR:-runs/${RUN_ID}/sqli}"

mkdir -p "$OUT_DIR"
mkdir -p "$SQLMAP_OUTPUT_DIR"

echo "[sql_injection] TARGET_URL=${TARGET_URL}"
echo "[sql_injection] TOOL_ARGS=${TOOL_ARGS}"
echo "[sql_injection] OUT_DIR=${OUT_DIR}"
echo "[sql_injection] SQLMAP_OUTPUT_DIR=${SQLMAP_OUTPUT_DIR}"

SQLMAP_BIN=$(command -v sqlmap 2>/dev/null || echo "sqlmap")

if ! command -v "$SQLMAP_BIN" &>/dev/null; then
    echo "[sql_injection] ERROR: sqlmap not found in PATH"
    exit 1
fi

read -r -a ARGS <<< "$TOOL_ARGS"

OUTPUT_FILE="${OUT_DIR}/sqlmap_output.txt"

printf '[sql_injection] CMD: %s -u %q --batch --output-dir %q' \
    "$SQLMAP_BIN" "$TARGET_URL" "$SQLMAP_OUTPUT_DIR"
for a in "${ARGS[@]}"; do printf ' %q' "$a"; done
printf ' > %q\n' "$OUTPUT_FILE"

trap 'echo "[sql_injection] Interrupted"; exit 130' INT TERM

set +e
"$SQLMAP_BIN" \
    -u "$TARGET_URL" \
    --batch \
    --output-dir "$SQLMAP_OUTPUT_DIR" \
    "${ARGS[@]}" \
    > "$OUTPUT_FILE" 2>&1

EXIT_CODE=$?
set -e

if [[ $EXIT_CODE -eq 130 ]]; then
    echo "[sql_injection] Interrupted"
    exit 130
fi

echo "[sql_injection] Exit code: $EXIT_CODE"

if [[ -f "$OUTPUT_FILE" ]]; then
    if grep -qE "(sqlmap identified|is vulnerable|is injectable|back-end DBMS)" "$OUTPUT_FILE"; then
        echo "[sql_injection] SQL injection vulnerability found"
        grep -E "(Parameter.*vulnerable|injectable|back-end DBMS)" "$OUTPUT_FILE" | head -5
    else
        echo "[sql_injection] No vulnerabilities found"
    fi
fi

echo "[sql_injection] Completed"
exit $EXIT_CODE