#!/usr/bin/env bash
# coord-wrapper.sh - High-level coordination wrapper for agents
# Part of Multi-Session Coordination System (Phase 1)
#
# This script provides a simple interface for agents to coordinate file access.
# It handles the full lifecycle: register → read → edit → write → complete
#
# Usage:
#   coord-wrapper.sh <project_path> <agent_id> <command> [args...]
#
# Commands:
#   register <file1> [file2...] [--task "description"]
#       Register intent to modify files
#
#   read <file_path>
#       Read file and capture hash (returns file content)
#
#   write <file_path> <content_file>
#       Write file with CAS check (content_file contains new content)
#
#   write-inline <file_path>
#       Write file from stdin with CAS check
#
#   complete [--status success|failed]
#       Mark agent as complete
#
#   status
#       Show current coordination status

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ─────────────────────────────────────────────────────────────────────────────
# Argument parsing
# ─────────────────────────────────────────────────────────────────────────────

if [[ $# -lt 3 ]]; then
  echo "Usage: coord-wrapper.sh <project_path> <agent_id> <command> [args...]" >&2
  echo "" >&2
  echo "Commands:" >&2
  echo "  register <file1> [file2...] [--task \"description\"]" >&2
  echo "  read <file_path>" >&2
  echo "  write <file_path> <content_file>" >&2
  echo "  write-inline <file_path>  (reads content from stdin)" >&2
  echo "  complete [--status success|failed]" >&2
  echo "  status" >&2
  exit 1
fi

PROJECT_PATH="$1"
AGENT_ID="$2"
COMMAND="$3"
shift 3

export COORD_AGENT_ID="$AGENT_ID"

# State directory for this agent's hash cache
STATE_DIR="$PROJECT_PATH/.agent-workspaces/$AGENT_ID"
HASH_CACHE="$STATE_DIR/hash-cache.json"

mkdir -p "$STATE_DIR"

# Initialize hash cache if needed
if [[ ! -f "$HASH_CACHE" ]]; then
  echo '{}' > "$HASH_CACHE"
fi

# ─────────────────────────────────────────────────────────────────────────────
# Commands
# ─────────────────────────────────────────────────────────────────────────────

case "$COMMAND" in

  # ───────────────────────────────────────────────────────────────────────────
  # REGISTER: Declare intent to modify files
  # ───────────────────────────────────────────────────────────────────────────
  register)
    FILES=()
    TASK_SUMMARY=""

    while [[ $# -gt 0 ]]; do
      case $1 in
        --task)
          TASK_SUMMARY="$2"
          shift 2
          ;;
        *)
          FILES+=("$1")
          shift
          ;;
      esac
    done

    if [[ ${#FILES[@]} -eq 0 ]]; then
      echo "Error: At least one file required" >&2
      exit 1
    fi

    # Generate intent ID
    INTENT_ID="intent-$(date +%s)-$(openssl rand -hex 4 2>/dev/null || echo $$)"

    # Build event data
    FILES_JSON=$(printf '%s\n' "${FILES[@]}" | jq -R . | jq -s .)

    EVENT_DATA=$(jq -nc \
      --argjson files "$FILES_JSON" \
      --arg task_summary "$TASK_SUMMARY" \
      --arg intent_id "$INTENT_ID" \
      '{files: $files, task_summary: $task_summary, intent_id: $intent_id}')

    "$SCRIPT_DIR/coord-append.sh" "$PROJECT_PATH" "register_intent" "$EVENT_DATA"

    echo "Registered intent: $INTENT_ID"
    echo "Files: ${FILES[*]}"
    ;;

  # ───────────────────────────────────────────────────────────────────────────
  # READ: Read file and capture hash
  # ───────────────────────────────────────────────────────────────────────────
  read)
    if [[ $# -lt 1 ]]; then
      echo "Error: File path required" >&2
      exit 1
    fi

    FILE_PATH="$1"
    FULL_PATH="$PROJECT_PATH/$FILE_PATH"

    # Capture hash
    HASH=$("$SCRIPT_DIR/coord-check-hash.sh" --capture "$FULL_PATH")

    # Store in hash cache
    jq --arg file "$FILE_PATH" --arg hash "$HASH" \
      '.[$file] = $hash' "$HASH_CACHE" > "$HASH_CACHE.tmp"
    mv "$HASH_CACHE.tmp" "$HASH_CACHE"

    # Log hash capture event
    EVENT_DATA=$(jq -nc \
      --arg file_path "$FILE_PATH" \
      --arg hash "$HASH" \
      --arg stage "pre-edit" \
      '{file_path: $file_path, hash: $hash, stage: $stage}')

    "$SCRIPT_DIR/coord-append.sh" "$PROJECT_PATH" "file_hash_capture" "$EVENT_DATA" >/dev/null

    # Output file content
    if [[ -f "$FULL_PATH" ]]; then
      cat "$FULL_PATH"
    fi
    ;;

  # ───────────────────────────────────────────────────────────────────────────
  # WRITE: Write file with CAS check
  # ───────────────────────────────────────────────────────────────────────────
  write|write-inline)
    if [[ $# -lt 1 ]]; then
      echo "Error: File path required" >&2
      exit 1
    fi

    FILE_PATH="$1"
    FULL_PATH="$PROJECT_PATH/$FILE_PATH"

    # Get content
    if [[ "$COMMAND" == "write-inline" ]]; then
      CONTENT=$(cat)
    else
      if [[ $# -lt 2 ]]; then
        echo "Error: Content file required" >&2
        exit 1
      fi
      CONTENT=$(cat "$2")
    fi

    # Get expected hash from cache
    EXPECTED_HASH=$(jq -r --arg file "$FILE_PATH" '.[$file] // "UNKNOWN"' "$HASH_CACHE")

    if [[ "$EXPECTED_HASH" == "UNKNOWN" ]]; then
      echo "Warning: No cached hash for $FILE_PATH, capturing now" >&2
      EXPECTED_HASH=$("$SCRIPT_DIR/coord-check-hash.sh" --capture "$FULL_PATH")
    fi

    # Acquire lock
    echo "Acquiring lock..." >&2
    LOCK_ID=$("$SCRIPT_DIR/coord-acquire.sh" "$PROJECT_PATH" "$AGENT_ID" "$FILE_PATH")

    if [[ -z "$LOCK_ID" || "$LOCK_ID" == "BLOCKED"* || "$LOCK_ID" == "TIMEOUT"* ]]; then
      echo "Error: Could not acquire lock" >&2
      exit 1
    fi

    echo "Lock acquired: $LOCK_ID" >&2

    # CAS check
    if ! "$SCRIPT_DIR/coord-check-hash.sh" "$FULL_PATH" "$EXPECTED_HASH" >/dev/null 2>&1; then
      echo "Error: File modified by another agent (hash mismatch)" >&2

      # Log conflict
      EVENT_DATA=$(jq -nc \
        --arg path "$FILE_PATH" \
        --arg hash_before "$EXPECTED_HASH" \
        '{files: [{path: $path, hash_before: $hash_before}], status: "conflict"}')

      "$SCRIPT_DIR/coord-append.sh" "$PROJECT_PATH" "write_commit" "$EVENT_DATA" >/dev/null

      # Release lock
      "$SCRIPT_DIR/coord-release.sh" "$PROJECT_PATH" "$LOCK_ID" >/dev/null 2>&1

      exit 1
    fi

    # Write file
    mkdir -p "$(dirname "$FULL_PATH")"
    echo "$CONTENT" > "$FULL_PATH"

    # Capture new hash
    NEW_HASH=$("$SCRIPT_DIR/coord-check-hash.sh" --capture "$FULL_PATH")

    # Update hash cache
    jq --arg file "$FILE_PATH" --arg hash "$NEW_HASH" \
      '.[$file] = $hash' "$HASH_CACHE" > "$HASH_CACHE.tmp"
    mv "$HASH_CACHE.tmp" "$HASH_CACHE"

    # Log write commit
    EVENT_DATA=$(jq -nc \
      --arg path "$FILE_PATH" \
      --arg hash_before "$EXPECTED_HASH" \
      --arg hash_after "$NEW_HASH" \
      '{files: [{path: $path, hash_before: $hash_before, hash_after: $hash_after}], status: "success"}')

    "$SCRIPT_DIR/coord-append.sh" "$PROJECT_PATH" "write_commit" "$EVENT_DATA" >/dev/null

    # Release lock
    "$SCRIPT_DIR/coord-release.sh" "$PROJECT_PATH" "$LOCK_ID" >/dev/null 2>&1

    echo "Written: $FILE_PATH"
    echo "Hash: $NEW_HASH"
    ;;

  # ───────────────────────────────────────────────────────────────────────────
  # COMPLETE: Mark agent as complete
  # ───────────────────────────────────────────────────────────────────────────
  complete)
    STATUS="success"
    SUMMARY=""

    while [[ $# -gt 0 ]]; do
      case $1 in
        --status)
          STATUS="$2"
          shift 2
          ;;
        --summary)
          SUMMARY="$2"
          shift 2
          ;;
        *)
          shift
          ;;
      esac
    done

    EVENT_DATA=$(jq -nc \
      --arg status "$STATUS" \
      --arg summary "$SUMMARY" \
      '{status: $status, summary: $summary}')

    "$SCRIPT_DIR/coord-append.sh" "$PROJECT_PATH" "agent_complete" "$EVENT_DATA"

    echo "Agent marked as complete (status: $STATUS)"
    ;;

  # ───────────────────────────────────────────────────────────────────────────
  # STATUS: Show coordination status
  # ───────────────────────────────────────────────────────────────────────────
  status)
    "$SCRIPT_DIR/coord-status.sh" "$PROJECT_PATH" "$@"
    ;;

  # ───────────────────────────────────────────────────────────────────────────
  # Unknown command
  # ───────────────────────────────────────────────────────────────────────────
  *)
    echo "Unknown command: $COMMAND" >&2
    exit 1
    ;;

esac
