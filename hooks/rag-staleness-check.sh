#!/usr/bin/env bash
# RAG Staleness Checker - SessionStart hook (once: true)
# Checks RAG index freshness and warns if stale.
# Budget: <200ms, fail-silent.

set +e  # fail-silent: hooks must not abort on error

# Get CWD from stdin JSON or fallback
CWD=$(cat | python3 -c "import sys,json; print(json.load(sys.stdin).get('cwd',''))" 2>/dev/null || echo "$PWD")
[[ -z "$CWD" ]] && CWD="$PWD"

RAG_DIR="$CWD/.rag"
ACTIVITY_LOG="$RAG_DIR/.index_activity.log"

# No .rag/ = no check needed
[[ -d "$RAG_DIR" ]] || exit 0
[[ -f "$ACTIVITY_LOG" ]] || exit 0

# Get last index timestamp from activity log
LAST_LINE=$(tail -1 "$ACTIVITY_LOG" 2>/dev/null || echo "")
[[ -z "$LAST_LINE" ]] && exit 0

# Extract date - try common formats
LAST_TS=$(echo "$LAST_LINE" | python3 -c "
import sys, re
from datetime import datetime, timezone
line = sys.stdin.read().strip()
# Try ISO format first
for pattern in [r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}']:
    m = re.search(pattern, line)
    if m:
        try:
            dt = datetime.fromisoformat(m.group().replace('T',' '))
            print(int(dt.replace(tzinfo=timezone.utc).timestamp()))
            sys.exit(0)
        except Exception: pass
# Fallback: use file mtime
import os
print(int(os.path.getmtime('$ACTIVITY_LOG')))
" 2>/dev/null || stat -f %m "$ACTIVITY_LOG" 2>/dev/null || echo 0)

[[ "$LAST_TS" == "0" ]] && exit 0

NOW=$(date +%s)
DAYS_OLD=$(( (NOW - LAST_TS) / 86400 ))
WARNINGS=""

# Check staleness (>7 days)
if [[ $DAYS_OLD -gt 7 ]]; then
  WARNINGS="Index is ${DAYS_OLD} days old."
fi

# Count modified files since last index (maxdepth 3 + timeout to stay within budget)
MODIFIED_COUNT=$(timeout 1 find "$CWD" -maxdepth 3 -newer "$ACTIVITY_LOG" \
  \( -name "*.md" -o -name "*.txt" -o -name "*.json" -o -name "*.py" -o -name "*.js" -o -name "*.ts" \) \
  ! -path "*/.git/*" ! -path "*/.rag/*" ! -path "*/node_modules/*" ! -path "*/__pycache__/*" \
  2>/dev/null | wc -l | tr -d ' ') || MODIFIED_COUNT=0

if [[ $MODIFIED_COUNT -gt 5 ]]; then
  if [[ -n "$WARNINGS" ]]; then
    WARNINGS="$WARNINGS ${MODIFIED_COUNT} files modified since last index."
  else
    WARNINGS="${MODIFIED_COUNT} files modified since last index."
  fi
fi

# Output warning if any issues found
if [[ -n "$WARNINGS" ]]; then
  echo "[RAG Staleness Warning] $WARNINGS Consider running: rag reindex"
fi

exit 0
