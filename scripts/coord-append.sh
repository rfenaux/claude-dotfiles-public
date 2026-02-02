#!/usr/bin/env bash
# coord-append.sh - Atomically append events to coordination log
# Part of Multi-Session Coordination System (Phase 1)
#
# Usage: coord-append.sh <project_path> <event_type> [event_data_json]
# Example: coord-append.sh /path/to/project register_intent '{"files":["src/auth.py"]}'
#
# Environment:
#   COORD_DEBUG=1    Enable debug output
#   COORD_DISABLED=1 Skip coordination (no-op)

set -euo pipefail

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULTS_FILE="$HOME/.claude/coordination-defaults.json"

# ─────────────────────────────────────────────────────────────────────────────
# Argument parsing
# ─────────────────────────────────────────────────────────────────────────────

if [[ $# -lt 2 ]]; then
  echo "Usage: coord-append.sh <project_path> <event_type> [event_data_json]" >&2
  echo "" >&2
  echo "Event types:" >&2
  echo "  register_intent   - Agent declares files it will modify" >&2
  echo "  file_hash_capture - Capture file hash at read time" >&2
  echo "  lock_acquire      - Request exclusive write lock" >&2
  echo "  write_commit      - Record successful write" >&2
  echo "  lock_release      - Release write lock" >&2
  echo "  heartbeat         - Agent health signal" >&2
  echo "  agent_complete    - Agent finished work" >&2
  exit 1
fi

PROJECT_PATH="${1}"
EVENT_TYPE="${2}"
# Note: Can't use ${3:-{}} because bash parameter expansion with braces is tricky
if [[ -n "${3:-}" ]]; then
  EVENT_DATA="$3"
else
  EVENT_DATA="{}"
fi

# ─────────────────────────────────────────────────────────────────────────────
# Skip if coordination disabled
# ─────────────────────────────────────────────────────────────────────────────

if [[ "${COORD_DISABLED:-0}" == "1" ]]; then
  [[ "${COORD_DEBUG:-0}" == "1" ]] && echo "[coord] Coordination disabled, skipping" >&2
  exit 0
fi

# ─────────────────────────────────────────────────────────────────────────────
# Validate project path
# ─────────────────────────────────────────────────────────────────────────────

if [[ ! -d "$PROJECT_PATH" ]]; then
  echo "Error: Project path does not exist: $PROJECT_PATH" >&2
  exit 1
fi

# ─────────────────────────────────────────────────────────────────────────────
# Setup coordination directory
# ─────────────────────────────────────────────────────────────────────────────

COORD_DIR="$PROJECT_PATH/.agent-workspaces"
LOG_FILE="$COORD_DIR/coord.log"
LOCK_FILE="$COORD_DIR/coord.log.lock"

mkdir -p "$COORD_DIR"

# ─────────────────────────────────────────────────────────────────────────────
# Generate event metadata
# ─────────────────────────────────────────────────────────────────────────────

# Generate ULID-like event ID (timestamp + random)
TIMESTAMP=$(date -u +%Y%m%d%H%M%S)
RANDOM_SUFFIX=$(openssl rand -hex 4 2>/dev/null || head -c 8 /dev/urandom | xxd -p)
EVENT_ID="${TIMESTAMP}-${RANDOM_SUFFIX}"

# ISO 8601 timestamp with milliseconds
TS=$(date -u +%Y-%m-%dT%H:%M:%S.000Z)

# Get agent ID from environment or generate
AGENT_ID="${COORD_AGENT_ID:-${AGENT_WORKSPACE_ID:-unknown}}"

# Get session ID
SESSION_ID="${CLAUDE_SESSION_ID:-sess-$(date +%Y%m%d)-unknown}"

# Get sequence number (count of events + 1)
if [[ -f "$LOG_FILE" ]]; then
  SEQ=$(( $(wc -l < "$LOG_FILE" | tr -d ' ') + 1 ))
else
  SEQ=1
fi

# ─────────────────────────────────────────────────────────────────────────────
# Build event JSON
# ─────────────────────────────────────────────────────────────────────────────

# Merge common fields with event-specific data
EVENT_JSON=$(jq -c \
  --arg event_id "$EVENT_ID" \
  --arg ts "$TS" \
  --arg agent_id "$AGENT_ID" \
  --arg session_id "$SESSION_ID" \
  --argjson seq "$SEQ" \
  --arg event_type "$EVENT_TYPE" \
  '. + {
    event_id: $event_id,
    ts: $ts,
    agent_id: $agent_id,
    session_id: $session_id,
    seq: $seq,
    event_type: $event_type
  }' <<< "$EVENT_DATA")

# ─────────────────────────────────────────────────────────────────────────────
# Atomic append with portable locking
# ─────────────────────────────────────────────────────────────────────────────

# Use mkdir-based lock (atomic on all POSIX systems including macOS)
# O_APPEND ensures atomic append even without lock on most filesystems

acquire_lock() {
  local lock_dir="$LOCK_FILE.d"
  local max_wait=30
  local waited=0

  while ! mkdir "$lock_dir" 2>/dev/null; do
    if [[ $waited -ge $max_wait ]]; then
      echo "Error: Could not acquire log lock after ${max_wait}s" >&2
      return 1
    fi
    sleep 0.1
    waited=$((waited + 1))
  done

  # Store PID for stale lock detection
  echo $$ > "$lock_dir/pid"
  return 0
}

release_lock() {
  local lock_dir="$LOCK_FILE.d"
  rm -rf "$lock_dir" 2>/dev/null || true
}

# Ensure lock is released on exit
trap release_lock EXIT

# Acquire lock
if ! acquire_lock; then
  exit 1
fi

# Append event
echo "$EVENT_JSON" >> "$LOG_FILE"

# Release lock
release_lock
trap - EXIT

# ─────────────────────────────────────────────────────────────────────────────
# Output
# ─────────────────────────────────────────────────────────────────────────────

if [[ "${COORD_DEBUG:-0}" == "1" ]]; then
  echo "[coord] Appended event: $EVENT_TYPE (id: $EVENT_ID)" >&2
fi

# Return the event ID for reference
echo "$EVENT_ID"
