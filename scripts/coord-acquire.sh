#!/usr/bin/env bash
# coord-acquire.sh - Acquire exclusive write lock for file(s)
# Part of Multi-Session Coordination System (Phase 1)
#
# Usage: coord-acquire.sh <project_path> <agent_id> <file_path> [--ttl <seconds>]
#
# Options:
#   --ttl <seconds>  Lock time-to-live (default: 300 = 5 minutes)
#   --no-wait        Fail immediately if locked (don't retry)
#   --json           Output result as JSON
#
# Exit codes:
#   0 - Lock acquired (outputs lock_id)
#   1 - Lock contention (another agent holds lock)
#   2 - Timeout waiting for lock
#   3 - Invalid arguments

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ─────────────────────────────────────────────────────────────────────────────
# Configuration defaults
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_TTL=300
BACKOFF_BASE=5
BACKOFF_MAX=120
MAX_ATTEMPTS=5

# ─────────────────────────────────────────────────────────────────────────────
# Argument parsing
# ─────────────────────────────────────────────────────────────────────────────

TTL="$DEFAULT_TTL"
NO_WAIT=false
JSON_OUTPUT=false

POSITIONAL=()
while [[ $# -gt 0 ]]; do
  case $1 in
    --ttl)
      TTL="$2"
      shift 2
      ;;
    --no-wait)
      NO_WAIT=true
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

if [[ $# -lt 3 ]]; then
  echo "Usage: coord-acquire.sh <project_path> <agent_id> <file_path> [--ttl <seconds>]" >&2
  exit 3
fi

PROJECT_PATH="$1"
AGENT_ID="$2"
FILE_PATH="$3"

# ─────────────────────────────────────────────────────────────────────────────
# Setup
# ─────────────────────────────────────────────────────────────────────────────

COORD_DIR="$PROJECT_PATH/.agent-workspaces"
SNAPSHOT_FILE="$COORD_DIR/coord-snapshot.json"

# Generate lock ID
LOCK_ID="lock-$(date +%s)-$(openssl rand -hex 4 2>/dev/null || head -c 8 /dev/urandom | xxd -p)"

# ─────────────────────────────────────────────────────────────────────────────
# Check for existing lock
# ─────────────────────────────────────────────────────────────────────────────

check_lock() {
  if [[ ! -f "$SNAPSHOT_FILE" ]]; then
    # No snapshot = no locks
    return 0
  fi

  # Check if file is locked by another agent
  local existing_lock
  existing_lock=$(jq -r --arg file "$FILE_PATH" '
    .locks | to_entries[] |
    select(.value.file_path == $file) |
    .value
  ' "$SNAPSHOT_FILE" 2>/dev/null || echo "")

  if [[ -z "$existing_lock" || "$existing_lock" == "null" ]]; then
    # No lock on this file
    return 0
  fi

  # Check if lock has expired
  local expires_at
  expires_at=$(echo "$existing_lock" | jq -r '.expires_at')
  local now
  now=$(date -u +%Y-%m-%dT%H:%M:%SZ)

  if [[ "$now" > "$expires_at" ]]; then
    # Lock expired
    [[ "${COORD_DEBUG:-0}" == "1" ]] && echo "[coord] Found expired lock, proceeding" >&2
    return 0
  fi

  # Check if we already own the lock
  local owner
  owner=$(echo "$existing_lock" | jq -r '.owner_agent')

  if [[ "$owner" == "$AGENT_ID" ]]; then
    # We already own this lock
    [[ "${COORD_DEBUG:-0}" == "1" ]] && echo "[coord] Already own lock on $FILE_PATH" >&2
    return 0
  fi

  # Lock held by another agent
  echo "$existing_lock"
  return 1
}

# ─────────────────────────────────────────────────────────────────────────────
# Acquire lock with retry and backoff
# ─────────────────────────────────────────────────────────────────────────────

acquire_lock() {
  local attempt=0
  local delay=$BACKOFF_BASE

  while [[ $attempt -lt $MAX_ATTEMPTS ]]; do
    # Check for existing lock
    local blocking_lock
    if blocking_lock=$(check_lock); then
      # No blocking lock, acquire it

      # Calculate expiry time
      local acquired_at
      acquired_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)
      local expires_at
      expires_at=$(date -u -v+${TTL}S +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || \
                   date -u -d "+${TTL} seconds" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || \
                   echo "")

      # Fallback for expires_at calculation
      if [[ -z "$expires_at" ]]; then
        local expires_epoch=$(($(date +%s) + TTL))
        expires_at=$(date -u -r "$expires_epoch" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || \
                     date -u --date="@$expires_epoch" +%Y-%m-%dT%H:%M:%SZ)
      fi

      # Append lock_acquire event
      local event_data
      event_data=$(jq -nc \
        --arg file_path "$FILE_PATH" \
        --arg lock_id "$LOCK_ID" \
        --argjson ttl_sec "$TTL" \
        --arg acquired_at "$acquired_at" \
        --arg expires_at "$expires_at" \
        '{
          file_path: $file_path,
          lock_id: $lock_id,
          ttl_sec: $ttl_sec,
          acquired_at: $acquired_at,
          expires_at: $expires_at,
          outcome: "granted"
        }')

      export COORD_AGENT_ID="$AGENT_ID"
      "$SCRIPT_DIR/coord-append.sh" "$PROJECT_PATH" "lock_acquire" "$event_data" >/dev/null

      # Rebuild snapshot to include new lock
      "$SCRIPT_DIR/coord-rebuild.sh" "$PROJECT_PATH" >/dev/null 2>&1 || true

      # Output result
      if [[ "$JSON_OUTPUT" == true ]]; then
        jq -nc \
          --arg lock_id "$LOCK_ID" \
          --arg file_path "$FILE_PATH" \
          --arg acquired_at "$acquired_at" \
          --arg expires_at "$expires_at" \
          --argjson ttl_sec "$TTL" \
          '{
            status: "granted",
            lock_id: $lock_id,
            file_path: $file_path,
            acquired_at: $acquired_at,
            expires_at: $expires_at,
            ttl_sec: $ttl_sec
          }'
      else
        echo "$LOCK_ID"
      fi

      return 0
    fi

    # Lock is held by another agent
    if [[ "$NO_WAIT" == true ]]; then
      if [[ "$JSON_OUTPUT" == true ]]; then
        local owner
        owner=$(echo "$blocking_lock" | jq -r '.owner_agent')
        jq -nc \
          --arg file_path "$FILE_PATH" \
          --arg owner "$owner" \
          '{
            status: "blocked",
            file_path: $file_path,
            blocking_agent: $owner,
            message: "File is locked by another agent"
          }'
      else
        echo "BLOCKED: $FILE_PATH is locked by another agent" >&2
      fi
      return 1
    fi

    # Retry with backoff
    ((attempt++))

    if [[ $attempt -lt $MAX_ATTEMPTS ]]; then
      # Add jitter (0-30% of delay)
      local jitter
      jitter=$(( (RANDOM % 30) * delay / 100 ))
      local sleep_time=$((delay + jitter))

      [[ "${COORD_DEBUG:-0}" == "1" ]] && echo "[coord] Lock contention, waiting ${sleep_time}s (attempt $attempt/$MAX_ATTEMPTS)" >&2

      sleep "$sleep_time"

      # Exponential backoff
      delay=$((delay * 2))
      if [[ $delay -gt $BACKOFF_MAX ]]; then
        delay=$BACKOFF_MAX
      fi
    fi
  done

  # Timeout
  if [[ "$JSON_OUTPUT" == true ]]; then
    jq -nc \
      --arg file_path "$FILE_PATH" \
      --argjson attempts "$MAX_ATTEMPTS" \
      '{
        status: "timeout",
        file_path: $file_path,
        attempts: $attempts,
        message: "Timed out waiting for lock"
      }'
  else
    echo "TIMEOUT: Could not acquire lock after $MAX_ATTEMPTS attempts" >&2
  fi
  return 2
}

# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

acquire_lock
