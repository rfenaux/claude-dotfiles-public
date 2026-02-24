#!/usr/bin/env bash
# settings-backup.sh - Auto-backup settings.json before edits
# Hook: PreToolUse on Write|Edit
# Creates timestamped backup, keeps last 10

set +e  # fail-silent: hooks must not abort on error

# Circuit breaker: skip if too many recent failures
. "$HOME/.claude/hooks/lib/circuit-breaker.sh" 2>/dev/null
check_circuit "settings-backup" || exit 0

SETTINGS="$HOME/.claude/settings.json"
BACKUP_DIR="$HOME/.claude/config/backups"

# Read hook input
INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null || echo "")
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null || echo "")

# Only trigger on Write/Edit to settings.json
case "$TOOL_NAME" in
  Write|Edit) ;;
  *) exit 0 ;;
esac

case "$FILE_PATH" in
  */.claude/settings.json) ;;
  *) exit 0 ;;
esac

# Create backup (background, fail-silent)
{
  [[ -f "$SETTINGS" ]] || exit 0
  mkdir -p "$BACKUP_DIR"

  TIMESTAMP=$(date +%Y%m%d-%H%M%S)
  cp "$SETTINGS" "$BACKUP_DIR/settings-${TIMESTAMP}.json" || record_failure "settings-backup"

  # Prune: keep last 10 backups
  ls -t "$BACKUP_DIR"/settings-*.json 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null
} &

exit 0
