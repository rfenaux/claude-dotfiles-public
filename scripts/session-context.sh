#!/usr/bin/env bash
# session-context.sh — Manage session-scoped context injected via ~/.claude/rules/
# Usage: session-context.sh {add|add-file|list|clear|preview|check-conflicts} [args]
set -euo pipefail

CONTEXT_FILE="$HOME/.claude/rules/session-context.md"
CLAUDE_MD="$HOME/.claude/CLAUDE.md"

HEADER="# Session Context (Auto-Injected)

> Managed by session-context.sh. Cleared at SessionEnd. Do not edit manually."

# --- Helpers ---

ensure_file() {
  if [[ ! -f "$CONTEXT_FILE" ]]; then
    echo "$HEADER" > "$CONTEXT_FILE"
  fi
}

count_appends() {
  if [[ ! -f "$CONTEXT_FILE" ]]; then
    echo 0
    return
  fi
  local c
  c=$(grep -c '^## Append #' "$CONTEXT_FILE" 2>/dev/null) || true
  echo "${c:-0}"
}

timestamp() {
  date '+%Y-%m-%d %H:%M:%S'
}

# --- Commands ---

cmd_add() {
  local text="${1:?Usage: session-context.sh add \"text\"}"
  ensure_file
  local n
  n=$(($(count_appends) + 1))

  cat >> "$CONTEXT_FILE" << EOF

---

## Append #${n} - [$(timestamp)]

[Source: inline]

${text}
EOF

  echo "Added append #${n} ($(echo "$text" | wc -c | tr -d ' ') chars)"
}

cmd_add_file() {
  local filepath="${1:?Usage: session-context.sh add-file <path>}"

  if [[ ! -f "$filepath" ]]; then
    echo "Error: File not found: $filepath" >&2
    exit 1
  fi

  ensure_file
  local n
  n=$(($(count_appends) + 1))
  local content
  content=$(cat "$filepath")

  cat >> "$CONTEXT_FILE" << EOF

---

## Append #${n} - [$(timestamp)]

[Source: file:${filepath}]

${content}
EOF

  echo "Added append #${n} from $(basename "$filepath") ($(wc -c < "$filepath" | tr -d ' ') chars)"
}

cmd_list() {
  if [[ ! -f "$CONTEXT_FILE" ]]; then
    echo "No session context active."
    return
  fi

  local count
  count=$(count_appends)
  if [[ "$count" -eq 0 ]]; then
    echo "No session context active."
    return
  fi

  echo "Session context: ${count} append(s)"
  echo ""
  grep '^## Append #' "$CONTEXT_FILE" | while read -r line; do
    echo "  $line"
  done
  echo ""
  echo "Total size: $(wc -c < "$CONTEXT_FILE" | tr -d ' ') chars"
}

cmd_clear() {
  if [[ -f "$CONTEXT_FILE" ]]; then
    rm "$CONTEXT_FILE"
    echo "Session context cleared."
  else
    echo "No session context to clear."
  fi
}

cmd_preview() {
  if [[ ! -f "$CONTEXT_FILE" ]]; then
    echo "No session context active."
    return
  fi
  echo "=== Session Context Preview ==="
  echo ""
  cat "$CONTEXT_FILE"
  echo ""
  echo "=== End Preview ($(wc -c < "$CONTEXT_FILE" | tr -d ' ') chars) ==="
}

cmd_check_conflicts() {
  if [[ ! -f "$CONTEXT_FILE" ]]; then
    echo "No session context to check."
    return
  fi

  if [[ ! -f "$CLAUDE_MD" ]]; then
    echo "Warning: CLAUDE.md not found at $CLAUDE_MD"
    return
  fi

  local conflicts=0

  # Extract NEVER rules from CLAUDE.md
  while IFS= read -r never_line; do
    # Get the action after NEVER (e.g., "skip discovery", "commit without")
    action=$(echo "$never_line" | sed -E 's/.*NEVER[[:space:]]+(.*)/\1/' | tr '[:upper:]' '[:lower:]' | head -c 40)

    # Check if session context contradicts with should/must/always
    if grep -qi "$action" "$CONTEXT_FILE" 2>/dev/null; then
      echo "Warning: Potential conflict detected"
      echo "  Base rule: $never_line"
      echo "  Session context may contradict this rule."
      echo ""
      conflicts=$((conflicts + 1))
    fi
  done < <(grep -i 'NEVER' "$CLAUDE_MD" 2>/dev/null | grep -v '^#' | head -20)

  if [[ "$conflicts" -eq 0 ]]; then
    echo "No conflicts detected."
  else
    echo "$conflicts potential conflict(s) found. Use --force to override."
  fi

  return $conflicts
}

# --- Router ---

case "${1:-help}" in
  add)        shift; cmd_add "$@" ;;
  add-file)   shift; cmd_add_file "$@" ;;
  list)       cmd_list ;;
  clear)      cmd_clear ;;
  preview)    cmd_preview ;;
  check-conflicts) cmd_check_conflicts ;;
  help|--help|-h)
    echo "Usage: session-context.sh {add|add-file|list|clear|preview|check-conflicts}"
    echo ""
    echo "Commands:"
    echo "  add <text>        Append inline text"
    echo "  add-file <path>   Append file contents"
    echo "  list              Show current appends"
    echo "  clear             Clear all appends"
    echo "  preview           Preview injected content"
    echo "  check-conflicts   Check for contradictions with CLAUDE.md"
    ;;
  *)
    echo "Unknown command: $1. Use --help for usage." >&2
    exit 1
    ;;
esac
