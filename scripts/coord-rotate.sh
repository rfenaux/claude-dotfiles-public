#!/usr/bin/env bash
# coord-rotate.sh - Rotate coordination log when it exceeds threshold
# Part of Multi-Session Coordination System (Phase 2)
#
# Usage: coord-rotate.sh <project_path> [--force] [--check]
#
# Options:
#   --force   Rotate even if below threshold
#   --check   Only check if rotation needed (don't rotate)
#   --json    Output as JSON
#
# Log rotation preserves recent history while preventing unbounded growth:
# - Default threshold: 1000 events
# - Keeps: coord.log (current) and coord.log.1 (previous)
# - Older logs are deleted

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

DEFAULTS_FILE="$HOME/.claude/coordination-defaults.json"

if [[ -f "$DEFAULTS_FILE" ]]; then
  MAX_EVENTS=$(jq -r '.log.max_events // 1000' "$DEFAULTS_FILE")
  KEEP_ROTATED=$(jq -r '.log.keep_rotated // 1' "$DEFAULTS_FILE")
else
  MAX_EVENTS=1000
  KEEP_ROTATED=1
fi

# ─────────────────────────────────────────────────────────────────────────────
# Argument parsing
# ─────────────────────────────────────────────────────────────────────────────

FORCE=false
CHECK_ONLY=false
JSON_OUTPUT=false

POSITIONAL=()
while [[ $# -gt 0 ]]; do
  case $1 in
    --force)
      FORCE=true
      shift
      ;;
    --check)
      CHECK_ONLY=true
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
  echo "Usage: coord-rotate.sh <project_path> [--force] [--check]" >&2
  exit 1
fi

PROJECT_PATH="$1"

# ─────────────────────────────────────────────────────────────────────────────
# Setup
# ─────────────────────────────────────────────────────────────────────────────

COORD_DIR="$PROJECT_PATH/.agent-workspaces"
LOG_FILE="$COORD_DIR/coord.log"
LOCK_FILE="$COORD_DIR/coord.log.lock"

if [[ ! -f "$LOG_FILE" ]]; then
  if [[ "$JSON_OUTPUT" == true ]]; then
    jq -nc '{status: "no_log", message: "No coordination log found"}'
  else
    echo "No coordination log found"
  fi
  exit 0
fi

# ─────────────────────────────────────────────────────────────────────────────
# Check current state
# ─────────────────────────────────────────────────────────────────────────────

EVENT_COUNT=$(wc -l < "$LOG_FILE" | tr -d ' ')
LOG_SIZE=$(du -h "$LOG_FILE" | cut -f1)

NEEDS_ROTATION=false
if [[ $EVENT_COUNT -ge $MAX_EVENTS || "$FORCE" == true ]]; then
  NEEDS_ROTATION=true
fi

# ─────────────────────────────────────────────────────────────────────────────
# Check only mode
# ─────────────────────────────────────────────────────────────────────────────

if [[ "$CHECK_ONLY" == true ]]; then
  if [[ "$JSON_OUTPUT" == true ]]; then
    jq -nc \
      --argjson event_count "$EVENT_COUNT" \
      --argjson max_events "$MAX_EVENTS" \
      --arg log_size "$LOG_SIZE" \
      --argjson needs_rotation "$NEEDS_ROTATION" \
      '{
        event_count: $event_count,
        max_events: $max_events,
        log_size: $log_size,
        needs_rotation: $needs_rotation,
        utilization_pct: (($event_count / $max_events) * 100 | floor)
      }'
  else
    UTIL=$(( (EVENT_COUNT * 100) / MAX_EVENTS ))
    echo "Log status:"
    echo "  Events: $EVENT_COUNT / $MAX_EVENTS ($UTIL%)"
    echo "  Size: $LOG_SIZE"
    if [[ "$NEEDS_ROTATION" == true ]]; then
      echo "  Status: ROTATION NEEDED"
    else
      echo "  Status: OK"
    fi
  fi
  exit 0
fi

# ─────────────────────────────────────────────────────────────────────────────
# Perform rotation
# ─────────────────────────────────────────────────────────────────────────────

if [[ "$NEEDS_ROTATION" != true ]]; then
  if [[ "$JSON_OUTPUT" == true ]]; then
    jq -nc \
      --argjson event_count "$EVENT_COUNT" \
      --argjson max_events "$MAX_EVENTS" \
      '{status: "not_needed", event_count: $event_count, max_events: $max_events}'
  else
    echo "Rotation not needed ($EVENT_COUNT / $MAX_EVENTS events)"
  fi
  exit 0
fi

# Acquire exclusive lock for rotation
(
  if ! flock -x -w 30 200; then
    echo "Error: Could not acquire lock for rotation" >&2
    exit 1
  fi

  # Delete old rotated logs beyond keep limit
  for i in $(seq $((KEEP_ROTATED + 1)) 10); do
    rm -f "$COORD_DIR/coord.log.$i"
  done

  # Rotate existing logs
  for i in $(seq $KEEP_ROTATED -1 1); do
    if [[ -f "$COORD_DIR/coord.log.$i" ]]; then
      if [[ $i -ge $KEEP_ROTATED ]]; then
        rm -f "$COORD_DIR/coord.log.$i"
      else
        mv "$COORD_DIR/coord.log.$i" "$COORD_DIR/coord.log.$((i + 1))"
      fi
    fi
  done

  # Move current log to .1
  mv "$LOG_FILE" "$COORD_DIR/coord.log.1"

  # Create new empty log
  touch "$LOG_FILE"

  # Rebuild snapshot from new (empty) log
  # Note: We keep the old snapshot as a reference, rebuild will create minimal new one

) 200>"$LOCK_FILE"

# Rebuild snapshot for new log state
"$SCRIPT_DIR/coord-rebuild.sh" "$PROJECT_PATH" --force >/dev/null 2>&1 || true

# ─────────────────────────────────────────────────────────────────────────────
# Output
# ─────────────────────────────────────────────────────────────────────────────

if [[ "$JSON_OUTPUT" == true ]]; then
  jq -nc \
    --argjson rotated_events "$EVENT_COUNT" \
    --arg rotated_to "coord.log.1" \
    '{
      status: "rotated",
      rotated_events: $rotated_events,
      rotated_to: $rotated_to,
      new_log: "coord.log"
    }'
else
  echo "Log rotated:"
  echo "  Moved $EVENT_COUNT events to coord.log.1"
  echo "  Created new coord.log"
fi
