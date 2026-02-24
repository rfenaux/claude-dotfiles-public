#!/usr/bin/env bash
# auto-fix-imports.sh - Detect and fix broken imports in CLAUDE.md
# Trigger: Manual via `validate-setup.sh --fix` or standalone
# Safety: Dry-run by default, --apply flag for changes, backup before edit

set -euo pipefail

CLAUDE_MD="$HOME/.claude/CLAUDE.md"
SEARCH_ROOT="$HOME/.claude"
LOG_FILE="$HOME/.claude/logs/self-healing/import-fixes.jsonl"
BACKUP_DIR="$HOME/.claude/logs/self-healing/backups"
MODE="dry-run"

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply) MODE="apply" ;;
    --help|-h)
      echo "Usage: auto-fix-imports.sh [--apply]"
      echo "  Default: dry-run (show what would change)"
      echo "  --apply: Actually fix broken imports (creates backup first)"
      exit 0
      ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
  shift
done

[[ -f "$CLAUDE_MD" ]] || { echo "CLAUDE.md not found"; exit 1; }

echo "=== Import Auto-Fix (mode: $MODE) ==="

# Find all "Auto-loaded from" references
IMPORTS=$(grep -n '> Auto-loaded from' "$CLAUDE_MD" 2>/dev/null || true)

if [[ -z "$IMPORTS" ]]; then
  echo "No imports found in CLAUDE.md"
  exit 0
fi

BROKEN=0
FIXED=0
TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Backup if applying
if [[ "$MODE" == "apply" ]]; then
  mkdir -p "$BACKUP_DIR"
  cp "$CLAUDE_MD" "$BACKUP_DIR/CLAUDE.md.$(date +%Y%m%d_%H%M%S).bak"
  echo "Backup created in $BACKUP_DIR"
fi

echo "$IMPORTS" | while IFS= read -r line; do
  LINE_NUM=$(echo "$line" | cut -d: -f1)
  IMPORT_PATH=$(echo "$line" | grep -oE '`[^`]+`' | tr -d '`' | head -1)

  [[ -z "$IMPORT_PATH" ]] && continue

  # Expand ~ to HOME
  EXPANDED="${IMPORT_PATH/#\~/$HOME}"

  if [[ -f "$EXPANDED" ]]; then
    continue  # Import is valid
  fi

  BROKEN=$((BROKEN + 1))
  BASENAME=$(basename "$EXPANDED")

  echo "  BROKEN: line $LINE_NUM -> $IMPORT_PATH"

  # Search for the file by name
  FOUND=$(find "$SEARCH_ROOT" -name "$BASENAME" -type f 2>/dev/null | head -1)

  if [[ -n "$FOUND" ]]; then
    # Convert back to ~ path
    NEW_PATH="${FOUND/#$HOME/\~}"
    echo "    FOUND: $NEW_PATH"

    if [[ "$MODE" == "apply" ]]; then
      # Replace the old path with the new one
      sed -i '' "s|$(echo "$IMPORT_PATH" | sed 's|/|\\/|g')|$NEW_PATH|" "$CLAUDE_MD" 2>/dev/null
      FIXED=$((FIXED + 1))

      printf '{"ts":"%s","action":"fixed","line":%d,"old":"%s","new":"%s"}\n' \
        "$TS" "$LINE_NUM" "$IMPORT_PATH" "$NEW_PATH" >> "$LOG_FILE" 2>/dev/null
    fi
  else
    echo "    NOT FOUND: would comment out"

    if [[ "$MODE" == "apply" ]]; then
      # Comment out the broken import
      sed -i '' "${LINE_NUM}s|^|<!-- BROKEN: |; ${LINE_NUM}s|$| -->|" "$CLAUDE_MD" 2>/dev/null
      FIXED=$((FIXED + 1))

      printf '{"ts":"%s","action":"commented_out","line":%d,"path":"%s"}\n' \
        "$TS" "$LINE_NUM" "$IMPORT_PATH" >> "$LOG_FILE" 2>/dev/null
    fi
  fi
done

echo ""
echo "=== Results ==="
echo "  Total imports: $(echo "$IMPORTS" | wc -l | tr -d ' ')"
echo "  Broken: $BROKEN"
if [[ "$MODE" == "apply" ]]; then
  echo "  Fixed: $FIXED"
else
  echo "  Run with --apply to fix"
fi
