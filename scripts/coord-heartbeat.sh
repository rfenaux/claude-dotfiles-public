#!/usr/bin/env bash
# coord-heartbeat.sh - Emit heartbeat and check for stale agents
# Part of Multi-Session Coordination System (Phase 2)
#
# Usage:
#   coord-heartbeat.sh <project_path> <agent_id> [--check-stale] [--cleanup]
#
# Options:
#   --check-stale   Check for stale agents and report
#   --cleanup       Auto-release locks from stale agents
#   --json          Output as JSON
#
# The heartbeat mechanism allows detection of crashed agents:
# - Agents emit heartbeat every 30 seconds
# - Agent is stale if no heartbeat for 2 minutes
# - Stale agent locks can be auto-released

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

DEFAULTS_FILE="$HOME/.claude/coordination-defaults.json"

# Load defaults
if [[ -f "$DEFAULTS_FILE" ]]; then
  HEARTBEAT_INTERVAL=$(jq -r '.heartbeat.interval_sec // 30' "$DEFAULTS_FILE")
  STALE_THRESHOLD=$(jq -r '.heartbeat.stale_threshold_sec // 120' "$DEFAULTS_FILE")
else
  HEARTBEAT_INTERVAL=30
  STALE_THRESHOLD=120
fi

# ─────────────────────────────────────────────────────────────────────────────
# Argument parsing
# ─────────────────────────────────────────────────────────────────────────────

CHECK_STALE=false
CLEANUP=false
JSON_OUTPUT=false
EMIT_HEARTBEAT=true

POSITIONAL=()
while [[ $# -gt 0 ]]; do
  case $1 in
    --check-stale)
      CHECK_STALE=true
      EMIT_HEARTBEAT=false
      shift
      ;;
    --cleanup)
      CLEANUP=true
      CHECK_STALE=true
      EMIT_HEARTBEAT=false
      shift
      ;;
    --json)
      JSON_OUTPUT=true
      shift
      ;;
    --no-emit)
      EMIT_HEARTBEAT=false
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
  echo "Usage: coord-heartbeat.sh <project_path> [agent_id] [--check-stale] [--cleanup]" >&2
  exit 1
fi

PROJECT_PATH="$1"
AGENT_ID="${2:-}"

# ─────────────────────────────────────────────────────────────────────────────
# Setup
# ─────────────────────────────────────────────────────────────────────────────

COORD_DIR="$PROJECT_PATH/.agent-workspaces"
SNAPSHOT_FILE="$COORD_DIR/coord-snapshot.json"

# ─────────────────────────────────────────────────────────────────────────────
# Emit heartbeat
# ─────────────────────────────────────────────────────────────────────────────

if [[ "$EMIT_HEARTBEAT" == true ]]; then
  if [[ -z "$AGENT_ID" ]]; then
    echo "Error: agent_id required for heartbeat" >&2
    exit 1
  fi

  export COORD_AGENT_ID="$AGENT_ID"

  EVENT_DATA=$(jq -nc '{type: "heartbeat"}')
  EVENT_ID=$("$SCRIPT_DIR/coord-append.sh" "$PROJECT_PATH" "heartbeat" "$EVENT_DATA")

  if [[ "$JSON_OUTPUT" == true ]]; then
    jq -nc \
      --arg agent_id "$AGENT_ID" \
      --arg event_id "$EVENT_ID" \
      --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
      '{status: "heartbeat_sent", agent_id: $agent_id, event_id: $event_id, ts: $ts}'
  else
    echo "Heartbeat sent: $AGENT_ID"
  fi
fi

# ─────────────────────────────────────────────────────────────────────────────
# Check for stale agents
# ─────────────────────────────────────────────────────────────────────────────

if [[ "$CHECK_STALE" == true ]]; then
  # Ensure snapshot is current
  "$SCRIPT_DIR/coord-rebuild.sh" "$PROJECT_PATH" >/dev/null 2>&1 || true

  if [[ ! -f "$SNAPSHOT_FILE" ]]; then
    if [[ "$JSON_OUTPUT" == true ]]; then
      jq -nc '{stale_agents: [], stale_locks: [], message: "No coordination data"}'
    else
      echo "No coordination data found"
    fi
    exit 0
  fi

  NOW=$(date +%s)

  # Find stale agents
  STALE_AGENTS=()
  STALE_LOCKS=()

  while IFS= read -r entry; do
    [[ -z "$entry" ]] && continue

    DECODED=$(echo "$entry" | base64 -d)
    AID=$(echo "$DECODED" | jq -r '.key')
    DATA=$(echo "$DECODED" | jq -r '.value')

    STATUS=$(echo "$DATA" | jq -r '.status')
    LAST_SEEN=$(echo "$DATA" | jq -r '.last_seen')

    # Skip completed agents
    [[ "$STATUS" == "completed" ]] && continue

    # Parse last_seen timestamp
    LAST_SEEN_EPOCH=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$LAST_SEEN" +%s 2>/dev/null || \
                      date -d "$LAST_SEEN" +%s 2>/dev/null || echo 0)

    AGE=$((NOW - LAST_SEEN_EPOCH))

    if [[ $AGE -gt $STALE_THRESHOLD ]]; then
      STALE_AGENTS+=("$AID")

      [[ "${COORD_DEBUG:-0}" == "1" ]] && echo "[coord] Stale agent: $AID (last seen ${AGE}s ago)" >&2
    fi
  done < <(jq -r '.agents | to_entries[] | @base64' "$SNAPSHOT_FILE" 2>/dev/null || echo "")

  # Find locks held by stale agents
  while IFS= read -r entry; do
    [[ -z "$entry" ]] && continue

    DECODED=$(echo "$entry" | base64 -d)
    LOCK_ID=$(echo "$DECODED" | jq -r '.key')
    DATA=$(echo "$DECODED" | jq -r '.value')

    OWNER=$(echo "$DATA" | jq -r '.owner_agent')
    FILE_PATH=$(echo "$DATA" | jq -r '.file_path')

    # Check if owner is stale
    for stale in "${STALE_AGENTS[@]}"; do
      if [[ "$OWNER" == "$stale" ]]; then
        STALE_LOCKS+=("$LOCK_ID:$FILE_PATH:$OWNER")
        break
      fi
    done
  done < <(jq -r '.locks | to_entries[] | @base64' "$SNAPSHOT_FILE" 2>/dev/null || echo "")

  # ─────────────────────────────────────────────────────────────────────────────
  # Cleanup stale locks
  # ─────────────────────────────────────────────────────────────────────────────

  RELEASED_LOCKS=()

  if [[ "$CLEANUP" == true && ${#STALE_LOCKS[@]} -gt 0 ]]; then
    for lock_info in "${STALE_LOCKS[@]}"; do
      LOCK_ID="${lock_info%%:*}"

      [[ "${COORD_DEBUG:-0}" == "1" ]] && echo "[coord] Releasing stale lock: $LOCK_ID" >&2

      if "$SCRIPT_DIR/coord-release.sh" "$PROJECT_PATH" "$LOCK_ID" --force >/dev/null 2>&1; then
        RELEASED_LOCKS+=("$LOCK_ID")
      fi
    done
  fi

  # ─────────────────────────────────────────────────────────────────────────────
  # Output
  # ─────────────────────────────────────────────────────────────────────────────

  if [[ "$JSON_OUTPUT" == true ]]; then
    # Build JSON arrays
    STALE_AGENTS_JSON=$(printf '%s\n' "${STALE_AGENTS[@]}" 2>/dev/null | jq -R . | jq -s '.' || echo '[]')
    STALE_LOCKS_JSON=$(printf '%s\n' "${STALE_LOCKS[@]}" 2>/dev/null | jq -R 'split(":") | {lock_id: .[0], file_path: .[1], owner: .[2]}' | jq -s '.' || echo '[]')
    RELEASED_JSON=$(printf '%s\n' "${RELEASED_LOCKS[@]}" 2>/dev/null | jq -R . | jq -s '.' || echo '[]')

    jq -nc \
      --argjson stale_agents "$STALE_AGENTS_JSON" \
      --argjson stale_locks "$STALE_LOCKS_JSON" \
      --argjson released_locks "$RELEASED_JSON" \
      --argjson stale_threshold "$STALE_THRESHOLD" \
      '{
        stale_agents: $stale_agents,
        stale_locks: $stale_locks,
        released_locks: $released_locks,
        stale_threshold_sec: $stale_threshold
      }'
  else
    if [[ ${#STALE_AGENTS[@]} -eq 0 ]]; then
      echo "No stale agents found (threshold: ${STALE_THRESHOLD}s)"
    else
      echo "Stale agents (no heartbeat for ${STALE_THRESHOLD}s):"
      for agent in "${STALE_AGENTS[@]}"; do
        echo "  - $agent"
      done

      if [[ ${#STALE_LOCKS[@]} -gt 0 ]]; then
        echo ""
        echo "Stale locks:"
        for lock_info in "${STALE_LOCKS[@]}"; do
          LOCK_ID="${lock_info%%:*}"
          REST="${lock_info#*:}"
          FILE_PATH="${REST%%:*}"
          OWNER="${REST#*:}"
          echo "  - $LOCK_ID ($FILE_PATH) owned by $OWNER"
        done

        if [[ ${#RELEASED_LOCKS[@]} -gt 0 ]]; then
          echo ""
          echo "Released locks:"
          for lock in "${RELEASED_LOCKS[@]}"; do
            echo "  - $lock"
          done
        elif [[ "$CLEANUP" != true ]]; then
          echo ""
          echo "Run with --cleanup to auto-release stale locks"
        fi
      fi
    fi
  fi
fi
