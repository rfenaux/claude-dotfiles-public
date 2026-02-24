#!/usr/bin/env bash
# auto-regen-inventory.sh - Auto-regenerate inventory.json when config changes
# Hook: PostToolUse on Write|Edit to agents, skills, hooks, rules, settings
# Budget: <50ms inline, regen in background
# Rate limit: 1 regen per 30s, debounce 2s

# Circuit breaker: skip if too many recent failures
. "$HOME/.claude/hooks/lib/circuit-breaker.sh" 2>/dev/null
check_circuit "auto-regen-inventory" || exit 0

set +e  # fail-silent: hooks must not abort on error

INVENTORY_SCRIPT="$HOME/.claude/scripts/generate-inventory.sh"
LOCK_FILE="/tmp/claude-inventory-regen.lock"
DEBOUNCE_FILE="/tmp/claude-inventory-pending"
RATE_LIMIT_S=30

# Read hook input
INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null || echo "")
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null || echo "")

# Only process Write/Edit to config files
case "$TOOL_NAME" in
  Write|Edit) ;;
  *) exit 0 ;;
esac

case "$FILE_PATH" in
  */.claude/agents/*.md) ;;
  */.claude/skills/*/SKILL.md) ;;
  */.claude/hooks/*.sh) ;;
  */.claude/rules/*.md) ;;
  */.claude/settings.json) ;;
  *) exit 0 ;;
esac

# Check inventory script exists
[[ -x "$INVENTORY_SCRIPT" ]] || exit 0

# Rate limit check
if [[ -f "$LOCK_FILE" ]]; then
  LOCK_AGE=$(( $(date +%s) - $(stat -f %m "$LOCK_FILE" 2>/dev/null || echo 0) ))
  [[ $LOCK_AGE -lt $RATE_LIMIT_S ]] && exit 0
fi

# Debounce: mark pending, wait, then check if still pending
{
  touch "$DEBOUNCE_FILE"
  sleep 2

  # If debounce file still exists (no other run cleared it), proceed
  if [[ -f "$DEBOUNCE_FILE" ]]; then
    rm -f "$DEBOUNCE_FILE"
    touch "$LOCK_FILE"
    "$INVENTORY_SCRIPT" > /dev/null 2>&1 || record_failure "auto-regen-inventory"
    echo "[Self-Heal] Inventory regenerated after config change: $(basename "$FILE_PATH")" >&2
  fi
} &

exit 0
