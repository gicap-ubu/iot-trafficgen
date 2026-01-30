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

SQLMAP_BIN="sqlmap"
if ! command -v "$SQLMAP_BIN" &>/dev/null; then
    echo "[sql_injection] ERROR: sqlmap not found in PATH"
    echo "[sql_injection] Install: pip install sqlmap or apt install sqlmap"
    exit 1
fi

read -r -a ARGS <<< "$TOOL_ARGS"

OUTPUT_FILE="${OUT_DIR}/sqlmap_output.txt"

printf '[sql_injection] CMD: %s' "$SQLMAP_BIN"
printf ' -u %q' "$TARGET_URL"
printf ' --batch'
printf ' --output-dir %q' "$SQLMAP_OUTPUT_DIR"
for a in "${ARGS[@]}"; do printf ' %q' "$a"; done
printf ' > %q\n' "$OUTPUT_FILE"

set +e
"$SQLMAP_BIN" \
    -u "$TARGET_URL" \
    --batch \
    --output-dir "$SQLMAP_OUTPUT_DIR" \
    "${ARGS[@]}" \
    > "$OUTPUT_FILE" 2>&1

EXIT_CODE=$?
set -e

echo "[sql_injection] SQLMap exit code: $EXIT_CODE"

if [[ -f "$OUTPUT_FILE" ]]; then
    echo "[sql_injection] Output saved to: $OUTPUT_FILE"
    
    if grep -qE "(sqlmap identified the following injection point|is vulnerable|is injectable|back-end DBMS)" "$OUTPUT_FILE"; then
        echo "[sql_injection] SUCCESS: SQL injection vulnerability found!"
        grep -E "(Parameter.*is vulnerable|injectable|back-end DBMS)" "$OUTPUT_FILE" | head -5
    else
        echo "[sql_injection] No SQL injection vulnerabilities found"
    fi
    
    OUT_LINES=$(wc -l < "$OUTPUT_FILE" 2>/dev/null || echo "0")
    echo "[sql_injection] Output lines: $OUT_LINES"
else
    echo "[sql_injection] WARNING: No output file generated"
fi

echo "[sql_injection] Completed"
exit $EXIT_CODE
