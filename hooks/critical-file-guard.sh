#!/usr/bin/env bash
# critical-file-guard.sh - Pre-edit validation for critical config files
# Hook: PreToolUse on Write|Edit
# Blocks edits that would introduce structural errors in load-bearing files
# Fail-silent for non-critical files

set +e  # fail-silent: hooks must not abort on error

# Circuit breaker: skip if too many recent failures
. "$HOME/.claude/hooks/lib/circuit-breaker.sh" 2>/dev/null
check_circuit "critical-file-guard" || exit 0

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null || echo "")
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null || echo "")
NEW_CONTENT=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin).get('tool_input',{}); print(d.get('content', d.get('new_string','')))" 2>/dev/null || echo "")

case "$TOOL_NAME" in
  Write|Edit) ;;
  *) exit 0 ;;
esac

CLAUDE_DIR="$HOME/.claude"

case "$FILE_PATH" in
  */.claude/settings.json)
    # For Write: validate the new content is valid JSON
    if [[ "$TOOL_NAME" == "Write" && -n "$NEW_CONTENT" ]]; then
      if ! echo "$NEW_CONTENT" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
        echo '{"decision": "block", "reason": "settings.json Write blocked: new content is not valid JSON. Fix syntax before writing."}'
        exit 0
      fi
    fi
    ;;

  */.claude/config/agent-clusters.json)
    # For Write: validate JSON + check all members exist
    if [[ "$TOOL_NAME" == "Write" && -n "$NEW_CONTENT" ]]; then
      GHOSTS=$(echo "$NEW_CONTENT" | python3 -c "
import sys, json, os
try:
    data = json.load(sys.stdin)
    clusters = data if isinstance(data, list) else data.get('clusters', [])
    for c in clusters:
        if not isinstance(c, dict): continue
        for m in c.get('members', []):
            name = m if isinstance(m, str) else str(m)
            if not os.path.exists(os.path.expanduser(f'~/.claude/agents/{name}.md')):
                print(name)
except json.JSONDecodeError:
    print('INVALID_JSON')
" 2>/dev/null || echo "")
      if [[ "$GHOSTS" == *"INVALID_JSON"* ]]; then
        echo '{"decision": "block", "reason": "agent-clusters.json Write blocked: not valid JSON."}'
        exit 0
      elif [[ -n "$GHOSTS" ]]; then
        echo "{\"feedback\": \"[Guard] agent-clusters.json contains ghost members: $GHOSTS\"}"
      fi
    fi
    ;;

  *)
    exit 0
    ;;
esac

exit 0
