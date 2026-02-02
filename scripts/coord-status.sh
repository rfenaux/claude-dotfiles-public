#!/usr/bin/env bash
# coord-status.sh - Display coordination status
# Part of Multi-Session Coordination System (Phase 1)
#
# Usage: coord-status.sh <project_path> [options]
#
# Options:
#   --json       Output as JSON
#   --agents     Show only agents
#   --locks      Show only locks
#   --files      Show only files
#   --events     Show recent events (last N)
#   -n <count>   Number of recent events (default: 10)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ─────────────────────────────────────────────────────────────────────────────
# Colors
# ─────────────────────────────────────────────────────────────────────────────

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ─────────────────────────────────────────────────────────────────────────────
# Argument parsing
# ─────────────────────────────────────────────────────────────────────────────

JSON_OUTPUT=false
SHOW_AGENTS=false
SHOW_LOCKS=false
SHOW_FILES=false
SHOW_EVENTS=false
EVENT_COUNT=10
SHOW_ALL=true

POSITIONAL=()
while [[ $# -gt 0 ]]; do
  case $1 in
    --json)
      JSON_OUTPUT=true
      shift
      ;;
    --agents)
      SHOW_AGENTS=true
      SHOW_ALL=false
      shift
      ;;
    --locks)
      SHOW_LOCKS=true
      SHOW_ALL=false
      shift
      ;;
    --files)
      SHOW_FILES=true
      SHOW_ALL=false
      shift
      ;;
    --events)
      SHOW_EVENTS=true
      SHOW_ALL=false
      shift
      ;;
    -n)
      EVENT_COUNT="$2"
      shift 2
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
  echo "Usage: coord-status.sh <project_path> [--json] [--agents|--locks|--files|--events]" >&2
  exit 1
fi

PROJECT_PATH="$1"

# ─────────────────────────────────────────────────────────────────────────────
# Setup
# ─────────────────────────────────────────────────────────────────────────────

COORD_DIR="$PROJECT_PATH/.agent-workspaces"
LOG_FILE="$COORD_DIR/coord.log"
SNAPSHOT_FILE="$COORD_DIR/coord-snapshot.json"

# ─────────────────────────────────────────────────────────────────────────────
# Check coordination exists
# ─────────────────────────────────────────────────────────────────────────────

if [[ ! -d "$COORD_DIR" ]]; then
  if [[ "$JSON_OUTPUT" == true ]]; then
    jq -nc '{status: "not_initialized", message: "No coordination directory found"}'
  else
    echo -e "${YELLOW}Coordination not initialized${NC}"
    echo "Run an agent with coordination to initialize."
  fi
  exit 0
fi

# ─────────────────────────────────────────────────────────────────────────────
# Ensure snapshot is current
# ─────────────────────────────────────────────────────────────────────────────

"$SCRIPT_DIR/coord-rebuild.sh" "$PROJECT_PATH" >/dev/null 2>&1 || true

if [[ ! -f "$SNAPSHOT_FILE" ]]; then
  if [[ "$JSON_OUTPUT" == true ]]; then
    jq -nc '{status: "empty", message: "No events recorded"}'
  else
    echo -e "${YELLOW}No coordination events recorded${NC}"
  fi
  exit 0
fi

# ─────────────────────────────────────────────────────────────────────────────
# JSON output
# ─────────────────────────────────────────────────────────────────────────────

if [[ "$JSON_OUTPUT" == true ]]; then
  SNAPSHOT=$(cat "$SNAPSHOT_FILE")

  if [[ "$SHOW_ALL" == true ]]; then
    # Add recent events to output
    if [[ -f "$LOG_FILE" ]]; then
      RECENT_EVENTS=$(tail -n "$EVENT_COUNT" "$LOG_FILE" | jq -s '.')
      echo "$SNAPSHOT" | jq --argjson events "$RECENT_EVENTS" '. + {recent_events: $events}'
    else
      echo "$SNAPSHOT"
    fi
  elif [[ "$SHOW_AGENTS" == true ]]; then
    jq '.agents' "$SNAPSHOT_FILE"
  elif [[ "$SHOW_LOCKS" == true ]]; then
    jq '.locks' "$SNAPSHOT_FILE"
  elif [[ "$SHOW_FILES" == true ]]; then
    jq '.files' "$SNAPSHOT_FILE"
  elif [[ "$SHOW_EVENTS" == true ]]; then
    tail -n "$EVENT_COUNT" "$LOG_FILE" | jq -s '.'
  fi
  exit 0
fi

# ─────────────────────────────────────────────────────────────────────────────
# Human-readable output
# ─────────────────────────────────────────────────────────────────────────────

echo -e "${BOLD}Multi-Session Coordination Status${NC}"
echo -e "${CYAN}Project:${NC} $PROJECT_PATH"
echo ""

# Stats
STATS=$(jq '.stats' "$SNAPSHOT_FILE")
TOTAL_EVENTS=$(echo "$STATS" | jq -r '.total_events')
TOTAL_CONFLICTS=$(echo "$STATS" | jq -r '.total_conflicts')
TOTAL_WRITES=$(echo "$STATS" | jq -r '.total_successful_writes')

echo -e "${BOLD}Statistics${NC}"
echo "  Events: $TOTAL_EVENTS | Writes: $TOTAL_WRITES | Conflicts: $TOTAL_CONFLICTS"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# Active Agents
# ─────────────────────────────────────────────────────────────────────────────

if [[ "$SHOW_ALL" == true || "$SHOW_AGENTS" == true ]]; then
  echo -e "${BOLD}Active Agents${NC}"

  AGENTS=$(jq -r '.agents | to_entries[] | @base64' "$SNAPSHOT_FILE" 2>/dev/null || echo "")

  if [[ -z "$AGENTS" ]]; then
    echo -e "  ${YELLOW}No active agents${NC}"
  else
    printf "  ${CYAN}%-15s %-12s %-20s %s${NC}\n" "AGENT" "STATUS" "LAST SEEN" "TASK"

    while IFS= read -r entry; do
      DECODED=$(echo "$entry" | base64 -d)
      AGENT_ID=$(echo "$DECODED" | jq -r '.key')
      DATA=$(echo "$DECODED" | jq -r '.value')

      STATUS=$(echo "$DATA" | jq -r '.status')
      LAST_SEEN=$(echo "$DATA" | jq -r '.last_seen' | cut -c12-19)
      TASK=$(echo "$DATA" | jq -r '.task_summary // "-"' | cut -c1-30)

      # Color status
      case "$STATUS" in
        active)
          STATUS_COLOR="${GREEN}$STATUS${NC}"
          ;;
        completed)
          STATUS_COLOR="${BLUE}$STATUS${NC}"
          ;;
        *)
          STATUS_COLOR="$STATUS"
          ;;
      esac

      printf "  %-15s %-12b %-20s %s\n" "${AGENT_ID:0:15}" "$STATUS_COLOR" "$LAST_SEEN" "$TASK"
    done <<< "$AGENTS"
  fi
  echo ""
fi

# ─────────────────────────────────────────────────────────────────────────────
# Active Locks
# ─────────────────────────────────────────────────────────────────────────────

if [[ "$SHOW_ALL" == true || "$SHOW_LOCKS" == true ]]; then
  echo -e "${BOLD}Active Locks${NC}"

  LOCKS=$(jq -r '.locks | to_entries[] | @base64' "$SNAPSHOT_FILE" 2>/dev/null || echo "")

  if [[ -z "$LOCKS" ]]; then
    echo -e "  ${GREEN}No active locks${NC}"
  else
    printf "  ${CYAN}%-20s %-15s %-12s %s${NC}\n" "FILE" "OWNER" "EXPIRES" "TTL"

    NOW=$(date +%s)

    while IFS= read -r entry; do
      DECODED=$(echo "$entry" | base64 -d)
      LOCK_ID=$(echo "$DECODED" | jq -r '.key')
      DATA=$(echo "$DECODED" | jq -r '.value')

      FILE_PATH=$(echo "$DATA" | jq -r '.file_path')
      OWNER=$(echo "$DATA" | jq -r '.owner_agent')
      EXPIRES=$(echo "$DATA" | jq -r '.expires_at')
      TTL=$(echo "$DATA" | jq -r '.ttl_sec')

      # Calculate remaining time
      EXPIRES_EPOCH=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$EXPIRES" +%s 2>/dev/null || \
                      date -d "$EXPIRES" +%s 2>/dev/null || echo 0)
      REMAINING=$((EXPIRES_EPOCH - NOW))

      if [[ $REMAINING -lt 0 ]]; then
        REMAINING_STR="${RED}EXPIRED${NC}"
      elif [[ $REMAINING -lt 60 ]]; then
        REMAINING_STR="${YELLOW}${REMAINING}s${NC}"
      else
        REMAINING_STR="${GREEN}$((REMAINING / 60))m${NC}"
      fi

      # Shorten file path
      SHORT_FILE=$(basename "$FILE_PATH")

      printf "  %-20s %-15s %-12b %s\n" "$SHORT_FILE" "${OWNER:0:15}" "$REMAINING_STR" "${TTL}s"
    done <<< "$LOCKS"
  fi
  echo ""
fi

# ─────────────────────────────────────────────────────────────────────────────
# Recent Events
# ─────────────────────────────────────────────────────────────────────────────

if [[ "$SHOW_ALL" == true || "$SHOW_EVENTS" == true ]]; then
  echo -e "${BOLD}Recent Events${NC} (last $EVENT_COUNT)"

  if [[ -f "$LOG_FILE" ]]; then
    tail -n "$EVENT_COUNT" "$LOG_FILE" | while IFS= read -r line; do
      EVENT_TYPE=$(echo "$line" | jq -r '.event_type')
      TS=$(echo "$line" | jq -r '.ts' | cut -c12-19)
      AGENT=$(echo "$line" | jq -r '.agent_id' | cut -c1-12)

      # Color event type
      case "$EVENT_TYPE" in
        register_intent)
          TYPE_COLOR="${BLUE}register${NC}"
          ;;
        lock_acquire)
          TYPE_COLOR="${YELLOW}lock${NC}"
          ;;
        lock_release)
          TYPE_COLOR="${GREEN}unlock${NC}"
          ;;
        write_commit)
          STATUS=$(echo "$line" | jq -r '.status')
          if [[ "$STATUS" == "success" ]]; then
            TYPE_COLOR="${GREEN}write${NC}"
          else
            TYPE_COLOR="${RED}conflict${NC}"
          fi
          ;;
        heartbeat)
          TYPE_COLOR="${CYAN}heartbeat${NC}"
          ;;
        agent_complete)
          TYPE_COLOR="${GREEN}complete${NC}"
          ;;
        *)
          TYPE_COLOR="$EVENT_TYPE"
          ;;
      esac

      printf "  ${CYAN}%s${NC} %-12b %-12s\n" "$TS" "$TYPE_COLOR" "$AGENT"
    done
  else
    echo -e "  ${YELLOW}No events${NC}"
  fi
fi
