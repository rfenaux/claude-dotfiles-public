#!/usr/bin/env bash
# auto-sync-decisions.sh - Auto-sync resolved decisions from conversations to DECISIONS.md
# Hook: SessionEnd
# Budget: <2s, fail-silent
# Rate limit: 1 sync per session

set +e  # fail-silent: hooks must not abort on error

CONFIG="$HOME/.claude/config/self-healing.json"
LOG_DIR="$HOME/.claude/logs/self-healing"
LOG_FILE="$LOG_DIR/decision-sync.jsonl"
SESSION_LOCK="/tmp/claude-decision-sync-done"

[[ -d "$LOG_DIR" ]] || mkdir -p "$LOG_DIR"

# Rate limit: 1 per session
[[ -f "$SESSION_LOCK" ]] && exit 0

# Read config
if [[ ! -f "$CONFIG" ]]; then
  exit 0
fi

ENABLED=$(python3 -c "import json; c=json.load(open('$CONFIG')); print(c.get('enabled', False))" 2>/dev/null || echo "false")
[[ "$ENABLED" != "True" && "$ENABLED" != "true" ]] && exit 0

SYNC_ENABLED=$(python3 -c "import json; c=json.load(open('$CONFIG')); print(c.get('decision_sync',{}).get('enabled', True))" 2>/dev/null || echo "true")
[[ "$SYNC_ENABLED" != "True" && "$SYNC_ENABLED" != "true" ]] && exit 0

# Get CWD from stdin
INPUT=$(cat)
CWD=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('cwd',''))" 2>/dev/null || echo "$PWD")
[[ -z "$CWD" ]] && CWD="$PWD"

# Find DECISIONS.md (check .claude/context/ first, then project root)
DECISIONS_FILE=""
for candidate in "$CWD/.claude/context/DECISIONS.md" "$CWD/DECISIONS.md"; do
  if [[ -f "$candidate" ]]; then
    DECISIONS_FILE="$candidate"
    break
  fi
done

# No DECISIONS.md = nothing to sync
[[ -z "$DECISIONS_FILE" ]] && exit 0

# Check for PENDING decisions
if ! grep -qi "PENDING\|pending" "$DECISIONS_FILE" 2>/dev/null; then
  exit 0
fi

# Look for resolution signals in recent conversation files (last 24h)
{
  touch "$SESSION_LOCK"
  TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

  # Find conversation files modified in last 24h
  CONV_FILES=$(find "$CWD" -maxdepth 2 -name "*.txt" -mtime -1 2>/dev/null || true)
  [[ -z "$CONV_FILES" ]] && exit 0

  # Extract decision IDs that appear resolved in conversations
  RESOLVED_IDS=$(echo "$CONV_FILES" | while read -r file; do
    [[ -f "$file" ]] || continue
    # Look for patterns like "A-001 resolved", "T-003 decided", "confirmed A-005"
    grep -oiE '([ATPS]-[0-9]+)\s*(resolved|decided|confirmed|approved|done)' "$file" 2>/dev/null \
      | grep -oE '[ATPS]-[0-9]+' || true
    grep -oiE '(resolved|decided|confirmed|approved)\s*([ATPS]-[0-9]+)' "$file" 2>/dev/null \
      | grep -oE '[ATPS]-[0-9]+' || true
  done | sort -u)

  [[ -z "$RESOLVED_IDS" ]] && exit 0

  UPDATED=0
  for id in $RESOLVED_IDS; do
    # Check if this ID exists as PENDING in DECISIONS.md
    if grep -q "${id}.*[Pp][Ee][Nn][Dd][Ii][Nn][Gg]" "$DECISIONS_FILE" 2>/dev/null; then
      # Update status from PENDING to RESOLVED with timestamp
      sed -i '' "s/\(${id}.*\)[Pp][Ee][Nn][Dd][Ii][Nn][Gg]/\1RESOLVED (auto-synced $(date +%Y-%m-%d))/" "$DECISIONS_FILE" 2>/dev/null
      UPDATED=$((UPDATED + 1))
      printf '{"ts":"%s","decision_id":"%s","action":"auto_resolved","file":"%s"}\n' \
        "$TS" "$id" "$DECISIONS_FILE" >> "$LOG_FILE" 2>/dev/null
    fi
  done

  if [[ $UPDATED -gt 0 ]]; then
    printf '{"ts":"%s","total_updated":%d,"file":"%s"}\n' \
      "$TS" "$UPDATED" "$DECISIONS_FILE" >> "$LOG_FILE" 2>/dev/null
  fi
} &

exit 0
