#!/usr/bin/env bash
# coord-release.sh - Release write lock
# Part of Multi-Session Coordination System (Phase 1)
#
# Usage: coord-release.sh <project_path> <lock_id> [--force]
#
# Options:
#   --force   Release lock even if not owned by current agent (admin override)
#   --json    Output result as JSON
#
# Exit codes:
#   0 - Lock released successfully
#   1 - Lock not found
#   2 - Not authorized to release (not owner)
#   3 - Invalid arguments

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ─────────────────────────────────────────────────────────────────────────────
# Argument parsing
# ─────────────────────────────────────────────────────────────────────────────

FORCE=false
JSON_OUTPUT=false

POSITIONAL=()
while [[ $# -gt 0 ]]; do
  case $1 in
    --force)
      FORCE=true
      shift
      ;;
    --json)
      JSON_OUTPUT=true
      shift
      ;;
    -*)
      echo "Unknown option: $1" >&2
      exit 3
      ;;
    *)
      POSITIONAL+=("$1")
      shift
      ;;
  esac
done

set -- "${POSITIONAL[@]}"

if [[ $# -lt 2 ]]; then
  echo "Usage: coord-release.sh <project_path> <lock_id> [--force]" >&2
  exit 3
fi

PROJECT_PATH="$1"
LOCK_ID="$2"

# ─────────────────────────────────────────────────────────────────────────────
# Setup
# ─────────────────────────────────────────────────────────────────────────────

COORD_DIR="$PROJECT_PATH/.agent-workspaces"
SNAPSHOT_FILE="$COORD_DIR/coord-snapshot.json"

AGENT_ID="${COORD_AGENT_ID:-${AGENT_WORKSPACE_ID:-unknown}}"

# ─────────────────────────────────────────────────────────────────────────────
# Find and validate lock
# ─────────────────────────────────────────────────────────────────────────────

if [[ ! -f "$SNAPSHOT_FILE" ]]; then
  if [[ "$JSON_OUTPUT" == true ]]; then
    jq -nc --arg lock_id "$LOCK_ID" '{status: "not_found", lock_id: $lock_id}'
  else
    echo "Lock not found: $LOCK_ID" >&2
  fi
  exit 1
fi

# Get lock info from snapshot
LOCK_INFO=$(jq -r --arg lock_id "$LOCK_ID" '.locks[$lock_id] // empty' "$SNAPSHOT_FILE")

if [[ -z "$LOCK_INFO" ]]; then
  if [[ "$JSON_OUTPUT" == true ]]; then
    jq -nc --arg lock_id "$LOCK_ID" '{status: "not_found", lock_id: $lock_id}'
  else
    echo "Lock not found: $LOCK_ID" >&2
  fi
  exit 1
fi

# Check ownership
OWNER=$(echo "$LOCK_INFO" | jq -r '.owner_agent')
FILE_PATH=$(echo "$LOCK_INFO" | jq -r '.file_path')

if [[ "$OWNER" != "$AGENT_ID" && "$FORCE" != true ]]; then
  if [[ "$JSON_OUTPUT" == true ]]; then
    jq -nc \
      --arg lock_id "$LOCK_ID" \
      --arg owner "$OWNER" \
      --arg agent_id "$AGENT_ID" \
      '{
        status: "not_authorized",
        lock_id: $lock_id,
        owner: $owner,
        requester: $agent_id,
        message: "Lock owned by different agent. Use --force to override."
      }'
  else
    echo "Not authorized: Lock owned by $OWNER (you are $AGENT_ID)" >&2
    echo "Use --force to override" >&2
  fi
  exit 2
fi

# ─────────────────────────────────────────────────────────────────────────────
# Release lock
# ─────────────────────────────────────────────────────────────────────────────

OUTCOME="released"
if [[ "$FORCE" == true && "$OWNER" != "$AGENT_ID" ]]; then
  OUTCOME="force_released"
fi

# Append lock_release event
EVENT_DATA=$(jq -nc \
  --arg lock_id "$LOCK_ID" \
  --arg file_path "$FILE_PATH" \
  --arg outcome "$OUTCOME" \
  --arg previous_owner "$OWNER" \
  '{
    lock_id: $lock_id,
    file_path: $file_path,
    outcome: $outcome,
    previous_owner: $previous_owner
  }')

export COORD_AGENT_ID="$AGENT_ID"
"$SCRIPT_DIR/coord-append.sh" "$PROJECT_PATH" "lock_release" "$EVENT_DATA" >/dev/null

# Rebuild snapshot
"$SCRIPT_DIR/coord-rebuild.sh" "$PROJECT_PATH" >/dev/null 2>&1 || true

# ─────────────────────────────────────────────────────────────────────────────
# Output
# ─────────────────────────────────────────────────────────────────────────────

if [[ "$JSON_OUTPUT" == true ]]; then
  jq -nc \
    --arg lock_id "$LOCK_ID" \
    --arg file_path "$FILE_PATH" \
    --arg outcome "$OUTCOME" \
    '{
      status: "released",
      lock_id: $lock_id,
      file_path: $file_path,
      outcome: $outcome
    }'
else
  echo "Released: $LOCK_ID ($FILE_PATH)"
fi

exit 0
