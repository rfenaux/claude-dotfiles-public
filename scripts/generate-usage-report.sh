#!/usr/bin/env bash
# generate-usage-report.sh - Report agent/skill usage from tracked data
# Usage: ./generate-usage-report.sh [--unused-only]

STATS_DIR="$HOME/.claude/stats/usage"
INVENTORY="$HOME/.claude/inventory.json"
UNUSED_ONLY=false
[[ "${1:-}" == "--unused-only" ]] && UNUSED_ONLY=true

echo "# Usage Report ($(date '+%Y-%m-%d %H:%M'))"
echo ""

# Collect all known components from inventory
if [[ -f "$INVENTORY" ]]; then
  AGENTS=$(python3 -c "
import json
with open('$INVENTORY') as f:
    inv = json.load(f)
for a in inv.get('agents', []):
    name = a.get('name', a) if isinstance(a, dict) else a
    print(name)
" 2>/dev/null)
  SKILLS=$(python3 -c "
import json
with open('$INVENTORY') as f:
    inv = json.load(f)
for s in inv.get('skills', []):
    name = s.get('name', s) if isinstance(s, dict) else s
    print(name)
" 2>/dev/null)
fi

echo "## Agents"
echo ""
echo "| Agent | Invocations | Last Used |"
echo "|-------|-------------|-----------|"

USED_AGENTS=0
TOTAL_AGENTS=0

while IFS= read -r agent; do
  [[ -z "$agent" ]] && continue
  TOTAL_AGENTS=$((TOTAL_AGENTS + 1))
  COUNT=0
  LAST="never"
  if [[ -f "$STATS_DIR/agent/${agent}.count" ]]; then
    COUNT=$(cat "$STATS_DIR/agent/${agent}.count" 2>/dev/null || echo 0)
    USED_AGENTS=$((USED_AGENTS + 1))
  fi
  if [[ -f "$STATS_DIR/agent/${agent}.last" ]]; then
    TS=$(cat "$STATS_DIR/agent/${agent}.last" 2>/dev/null || echo 0)
    LAST=$(date -r "$TS" '+%Y-%m-%d' 2>/dev/null || echo "unknown")
  fi
  if $UNUSED_ONLY && [[ $COUNT -gt 0 ]]; then
    continue
  fi
  echo "| $agent | $COUNT | $LAST |"
done <<< "$AGENTS"

echo ""
echo "## Skills"
echo ""
echo "| Skill | Invocations | Last Used |"
echo "|-------|-------------|-----------|"

USED_SKILLS=0
TOTAL_SKILLS=0

while IFS= read -r skill; do
  [[ -z "$skill" ]] && continue
  TOTAL_SKILLS=$((TOTAL_SKILLS + 1))
  COUNT=0
  LAST="never"
  if [[ -f "$STATS_DIR/skill/${skill}.count" ]]; then
    COUNT=$(cat "$STATS_DIR/skill/${skill}.count" 2>/dev/null || echo 0)
    USED_SKILLS=$((USED_SKILLS + 1))
  fi
  if [[ -f "$STATS_DIR/skill/${skill}.last" ]]; then
    TS=$(cat "$STATS_DIR/skill/${skill}.last" 2>/dev/null || echo 0)
    LAST=$(date -r "$TS" '+%Y-%m-%d' 2>/dev/null || echo "unknown")
  fi
  if $UNUSED_ONLY && [[ $COUNT -gt 0 ]]; then
    continue
  fi
  echo "| $skill | $COUNT | $LAST |"
done <<< "$SKILLS"

echo ""
echo "## Summary"
echo "- Agents tracked: $USED_AGENTS / $TOTAL_AGENTS"
echo "- Skills tracked: $USED_SKILLS / $TOTAL_SKILLS"
