#!/bin/bash
# check-team-health.sh - Background health monitor for Agent Teams
#
# Monitors active teams for stuck teammates and deadlocks.
# Runs in a loop (every 30s) while a team is active.
#
# Usage:
#   TEAM_NAME=my-team check-team-health.sh          # Run in foreground
#   TEAM_NAME=my-team check-team-health.sh &         # Run in background
#   check-team-health.sh --check-once my-team        # Single check, no loop
#   check-team-health.sh --stop my-team              # Stop background monitor
#
# Requires: jq

set -euo pipefail

HEALTH_CONFIG="$HOME/.claude/config/team-health-config.json"
LOG_DIR="$HOME/.claude/logs"
LOCK_DIR="/tmp"
STATE_DIR="/tmp"

# Load config
load_config() {
    if [[ -f "$HEALTH_CONFIG" ]] && command -v jq &>/dev/null; then
        STUCK_THRESHOLD=$(jq -r '.stuck_detection.stuck_threshold_seconds // 300' "$HEALTH_CONFIG")
        CHECK_INTERVAL=$(jq -r '.stuck_detection.check_interval_seconds // 30' "$HEALTH_CONFIG")
        DEADLOCK_THRESHOLD=$(jq -r '.deadlock_detection.all_idle_threshold_seconds // 120' "$HEALTH_CONFIG")
    else
        STUCK_THRESHOLD=300
        CHECK_INTERVAL=30
        DEADLOCK_THRESHOLD=120
    fi
}

# Ensure single instance per team
acquire_lock() {
    local team_name="$1"
    local lock_file="$LOCK_DIR/team-${team_name}-health.lock"

    if [[ -f "$lock_file" ]]; then
        local pid
        pid=$(cat "$lock_file" 2>/dev/null || echo "0")
        if kill -0 "$pid" 2>/dev/null; then
            echo "Health monitor already running for team '$team_name' (PID: $pid)" >&2
            return 1
        fi
        # Stale lock
        rm -f "$lock_file"
    fi

    echo $$ > "$lock_file"
    trap "rm -f '$lock_file'" EXIT
    return 0
}

# Log health event
log_health() {
    local team_name="$1"
    local event="$2"
    local details="${3:-}"

    mkdir -p "$LOG_DIR"
    local ts
    ts=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$ts] team=$team_name event=$event $details" >> "$LOG_DIR/team-health.log"
}

# Get team config
get_team_config() {
    local team_name="$1"
    local config_file="$HOME/.claude/teams/${team_name}/config.json"

    if [[ ! -f "$config_file" ]]; then
        echo "Team config not found: $config_file" >&2
        return 1
    fi

    cat "$config_file"
}

# Check for stuck teammates
check_stuck() {
    local team_name="$1"
    local now
    now=$(date +%s)
    local state_file="$STATE_DIR/team-${team_name}-idle-state.json"
    local issues=0

    # Read idle state (maintained by subagent-logger.sh)
    if [[ ! -f "$state_file" ]]; then
        return 0
    fi

    # Check each teammate's idle time
    local members
    members=$(jq -r 'keys[]' "$state_file" 2>/dev/null || echo "")

    for member in $members; do
        local idle_since
        idle_since=$(jq -r ".\"$member\".idle_since // 0" "$state_file" 2>/dev/null || echo "0")
        local has_task
        has_task=$(jq -r ".\"$member\".has_active_task // false" "$state_file" 2>/dev/null || echo "false")

        if [[ "$has_task" == "true" ]] && [[ "$idle_since" -gt 0 ]]; then
            local idle_duration=$((now - idle_since))

            if (( idle_duration > STUCK_THRESHOLD )); then
                log_health "$team_name" "stuck_detected" "member=$member idle_duration=${idle_duration}s"
                echo "STUCK: $member idle for ${idle_duration}s with active task" >&2
                issues=$((issues + 1))
            fi
        fi
    done

    return $issues
}

# Check for deadlock (all idle + all tasks blocked)
check_deadlock() {
    local team_name="$1"
    local state_file="$STATE_DIR/team-${team_name}-idle-state.json"

    if [[ ! -f "$state_file" ]]; then
        return 0
    fi

    local total_members
    total_members=$(jq 'length' "$state_file" 2>/dev/null || echo "0")
    local idle_members
    idle_members=$(jq '[.[] | select(.idle_since > 0)] | length' "$state_file" 2>/dev/null || echo "0")

    if [[ "$total_members" -gt 0 ]] && [[ "$idle_members" -eq "$total_members" ]]; then
        log_health "$team_name" "potential_deadlock" "all_members_idle total=$total_members"
        echo "DEADLOCK: All $total_members members idle" >&2
        return 1
    fi

    return 0
}

# Single health check
check_once() {
    local team_name="$1"
    local issues=0

    # Check team exists
    if ! get_team_config "$team_name" &>/dev/null; then
        echo "Team '$team_name' not found" >&2
        return 1
    fi

    # Run checks
    check_stuck "$team_name" || issues=$((issues + $?))
    check_deadlock "$team_name" || issues=$((issues + 1))

    if (( issues == 0 )); then
        echo "OK: Team '$team_name' healthy"
    else
        echo "WARNING: $issues issue(s) detected for team '$team_name'"
    fi

    return $issues
}

# Main monitoring loop
monitor_loop() {
    local team_name="$1"

    load_config

    if ! acquire_lock "$team_name"; then
        exit 1
    fi

    log_health "$team_name" "monitor_started" "interval=${CHECK_INTERVAL}s stuck_threshold=${STUCK_THRESHOLD}s"

    while true; do
        # Check if team still exists
        if ! get_team_config "$team_name" &>/dev/null; then
            log_health "$team_name" "monitor_stopped" "team_config_removed"
            break
        fi

        check_once "$team_name" || true
        sleep "$CHECK_INTERVAL"
    done
}

# Stop monitor
stop_monitor() {
    local team_name="$1"
    local lock_file="$LOCK_DIR/team-${team_name}-health.lock"

    if [[ -f "$lock_file" ]]; then
        local pid
        pid=$(cat "$lock_file" 2>/dev/null || echo "0")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            echo "Stopped health monitor for team '$team_name' (PID: $pid)"
        fi
        rm -f "$lock_file"
    else
        echo "No active health monitor for team '$team_name'"
    fi
}

# Main
case "${1:-}" in
    --check-once)
        load_config
        check_once "${2:?Team name required}"
        ;;
    --stop)
        stop_monitor "${2:?Team name required}"
        ;;
    *)
        team_name="${TEAM_NAME:-${1:-}}"
        if [[ -z "$team_name" ]]; then
            echo "Usage: TEAM_NAME=x check-team-health.sh" >&2
            echo "   or: check-team-health.sh --check-once <team>" >&2
            echo "   or: check-team-health.sh --stop <team>" >&2
            exit 1
        fi
        monitor_loop "$team_name"
        ;;
esac
