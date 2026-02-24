#!/usr/bin/env bash
# PostToolUse hook: validate JSON/Python syntax after Write/Edit
# Always exits 0 — advisory only, never blocks

# Circuit breaker: skip if too many recent failures
. "$HOME/.claude/hooks/lib/circuit-breaker.sh" 2>/dev/null
check_circuit "validate-syntax" || exit 0

INPUT=$(cat)
FILE=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null)

[ -z "$FILE" ] && exit 0

case "$FILE" in
  *.json)
    python3 -c "import json; json.load(open('$FILE'))" 2>/dev/null || \
      echo "[SYNTAX] Invalid JSON: $FILE" >&2
    ;;
  *.py)
    python3 -c "import ast; ast.parse(open('$FILE').read())" 2>/dev/null || \
      echo "[SYNTAX] Python syntax error: $FILE" >&2
    ;;
esac
exit 0
