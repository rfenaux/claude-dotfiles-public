#!/usr/bin/env bash
# coord-rebuild.sh - Rebuild snapshot from event log
# Part of Multi-Session Coordination System (Phase 1)
#
# Usage: coord-rebuild.sh <project_path> [--force]
#
# Options:
#   --force   Rebuild even if snapshot is up-to-date
#   --json    Output snapshot to stdout instead of file
#
# The snapshot is a derived cache of the current coordination state,
# rebuilt from the append-only event log. Corruption is non-fatal.
#
# Compatible with bash 3.2+ (macOS default)

set -euo pipefail

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
      exit 1
      ;;
    *)
      POSITIONAL+=("$1")
      shift
      ;;
  esac
done

set -- "${POSITIONAL[@]}"

if [[ $# -lt 1 ]]; then
  echo "Usage: coord-rebuild.sh <project_path> [--force]" >&2
  exit 1
fi

PROJECT_PATH="$1"

# ─────────────────────────────────────────────────────────────────────────────
# Setup
# ─────────────────────────────────────────────────────────────────────────────

COORD_DIR="$PROJECT_PATH/.agent-workspaces"
LOG_FILE="$COORD_DIR/coord.log"
SNAPSHOT_FILE="$COORD_DIR/coord-snapshot.json"
TEMP_SNAPSHOT="$COORD_DIR/coord-snapshot.json.tmp"

if [[ ! -f "$LOG_FILE" ]]; then
  # No log file, create empty snapshot
  EMPTY_SNAPSHOT=$(jq -nc '{
    version: "1.0",
    generated_at: (now | todate),
    log_position: {byte_offset: 0, last_event_id: null, event_count: 0},
    agents: {},
    locks: {},
    files: {},
    stats: {total_events: 0, total_conflicts: 0, total_successful_writes: 0}
  }')

  if [[ "$JSON_OUTPUT" == true ]]; then
    echo "$EMPTY_SNAPSHOT"
  else
    echo "$EMPTY_SNAPSHOT" > "$SNAPSHOT_FILE"
    [[ "${COORD_DEBUG:-0}" == "1" ]] && echo "[coord] Created empty snapshot" >&2
  fi
  exit 0
fi

# ─────────────────────────────────────────────────────────────────────────────
# Check if rebuild needed
# ─────────────────────────────────────────────────────────────────────────────

LOG_SIZE=$(wc -c < "$LOG_FILE" | tr -d ' ')
LOG_LINES=$(wc -l < "$LOG_FILE" | tr -d ' ')

if [[ -f "$SNAPSHOT_FILE" && "$FORCE" != true ]]; then
  CURRENT_OFFSET=$(jq -r '.log_position.byte_offset // 0' "$SNAPSHOT_FILE" 2>/dev/null || echo 0)
  if [[ "$CURRENT_OFFSET" == "$LOG_SIZE" ]]; then
    [[ "${COORD_DEBUG:-0}" == "1" ]] && echo "[coord] Snapshot up-to-date" >&2
    if [[ "$JSON_OUTPUT" == true ]]; then
      cat "$SNAPSHOT_FILE"
    fi
    exit 0
  fi
fi

# ─────────────────────────────────────────────────────────────────────────────
# Process event log using jq (bash 3.2 compatible)
# ─────────────────────────────────────────────────────────────────────────────

# Use jq to process the entire log and build the snapshot
# This is more efficient and bash-version-independent

SNAPSHOT=$(jq -s '
  # Initialize state
  reduce .[] as $event (
    {
      agents: {},
      locks: {},
      files: {},
      stats: {total_events: 0, total_conflicts: 0, total_successful_writes: 0},
      last_event_id: null
    };

    # Update stats
    .stats.total_events += 1 |
    .last_event_id = $event.event_id |

    # Process by event type
    if $event.event_type == "register_intent" then
      .agents[$event.agent_id] = {
        registered_at: $event.ts,
        last_seen: $event.ts,
        status: "active",
        task_summary: ($event.task_summary // ""),
        current_intent_id: ($event.intent_id // ""),
        files_intent: ($event.files // [])
      }
    elif $event.event_type == "file_hash_capture" then
      # Update agent last_seen
      (if .agents[$event.agent_id] then
        .agents[$event.agent_id].last_seen = $event.ts
      else . end) |
      # Track file state
      .files[$event.file_path] = {
        last_hash: $event.hash,
        last_reader: $event.agent_id,
        last_read_ts: $event.ts
      }
    elif $event.event_type == "lock_acquire" then
      # Update agent last_seen
      (if .agents[$event.agent_id] then
        .agents[$event.agent_id].last_seen = $event.ts
      else . end) |
      # Add lock if granted
      if ($event.outcome // "granted") == "granted" then
        .locks[$event.lock_id] = {
          file_path: $event.file_path,
          owner_agent: $event.agent_id,
          acquired_at: ($event.acquired_at // $event.ts),
          expires_at: ($event.expires_at // ""),
          ttl_sec: ($event.ttl_sec // 300)
        }
      else . end
    elif $event.event_type == "lock_release" then
      # Update agent last_seen
      (if .agents[$event.agent_id] then
        .agents[$event.agent_id].last_seen = $event.ts
      else . end) |
      # Remove lock
      del(.locks[$event.lock_id])
    elif $event.event_type == "write_commit" then
      # Update agent last_seen
      (if .agents[$event.agent_id] then
        .agents[$event.agent_id].last_seen = $event.ts
      else . end) |
      # Update stats
      if ($event.status // "success") == "success" then
        .stats.total_successful_writes += 1 |
        # Update file hashes
        reduce ($event.files // [])[] as $f (.;
          .files[$f.path] = {
            last_hash: $f.hash_after,
            last_writer: $event.agent_id,
            last_write_ts: $event.ts
          }
        )
      else
        .stats.total_conflicts += 1
      end
    elif $event.event_type == "heartbeat" then
      # Update agent last_seen
      if .agents[$event.agent_id] then
        .agents[$event.agent_id].last_seen = $event.ts
      else . end
    elif $event.event_type == "agent_complete" then
      # Update agent status
      if .agents[$event.agent_id] then
        .agents[$event.agent_id].last_seen = $event.ts |
        .agents[$event.agent_id].status = "completed"
      else . end
    else . end
  ) |

  # Build final snapshot
  {
    version: "1.0",
    generated_at: (now | todate),
    log_position: {
      byte_offset: '"$LOG_SIZE"',
      last_event_id: .last_event_id,
      event_count: .stats.total_events
    },
    agents: .agents,
    locks: .locks,
    files: .files,
    stats: .stats
  }
' "$LOG_FILE" 2>/dev/null) || {
  # If jq fails (e.g., malformed JSON), create minimal snapshot
  echo "[coord] Warning: Some log entries may be malformed" >&2
  SNAPSHOT=$(jq -nc '{
    version: "1.0",
    generated_at: (now | todate),
    log_position: {byte_offset: '"$LOG_SIZE"', last_event_id: null, event_count: 0},
    agents: {},
    locks: {},
    files: {},
    stats: {total_events: 0, total_conflicts: 0, total_successful_writes: 0},
    warning: "Rebuilt with errors - some events may be missing"
  }')
}

# ─────────────────────────────────────────────────────────────────────────────
# Output
# ─────────────────────────────────────────────────────────────────────────────

if [[ "$JSON_OUTPUT" == true ]]; then
  echo "$SNAPSHOT" | jq .
else
  # Write atomically
  echo "$SNAPSHOT" > "$TEMP_SNAPSHOT"
  mv "$TEMP_SNAPSHOT" "$SNAPSHOT_FILE"

  AGENT_COUNT=$(echo "$SNAPSHOT" | jq '.agents | length')
  LOCK_COUNT=$(echo "$SNAPSHOT" | jq '.locks | length')
  EVENT_COUNT=$(echo "$SNAPSHOT" | jq '.stats.total_events')

  [[ "${COORD_DEBUG:-0}" == "1" ]] && echo "[coord] Rebuilt snapshot: $EVENT_COUNT events, $LOCK_COUNT locks, $AGENT_COUNT agents" >&2
fi

exit 0
