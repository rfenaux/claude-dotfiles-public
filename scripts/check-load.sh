#!/bin/bash
# check-load.sh - Performance monitor for Claude delegation orchestration
# Returns system load status to inform spawning decisions
#
# Usage:
#   check-load.sh              # Full output with metrics
#   check-load.sh --status-only # Just OK/CAUTION/HIGH_LOAD
#   check-load.sh --json        # JSON output for parsing
#   check-load.sh --can-spawn   # Exit 0 if OK to spawn, 1 otherwise
#
# Reads thresholds from ~/.claude/machine-profile.json if available

set -euo pipefail

PROFILE_FILE="$HOME/.claude/machine-profile.json"

# Load thresholds from profile or use defaults
load_thresholds() {
    if [[ -f "$PROFILE_FILE" ]] && command -v jq &>/dev/null; then
        local profile=$(jq -r '.active_profile // "balanced"' "$PROFILE_FILE")
        THRESHOLD_OK=$(jq -r ".profiles.$profile.load_ok // .thresholds.load_ok // 8.0" "$PROFILE_FILE")
        THRESHOLD_CAUTION=$(jq -r ".thresholds.load_caution // 15.0" "$PROFILE_FILE")
        MAX_PARALLEL=$(jq -r ".profiles.$profile.max_parallel_agents // .limits.max_parallel_agents // 3" "$PROFILE_FILE")
        ACTIVE_PROFILE="$profile"
    else
        # Defaults tuned for M4/16GB
        THRESHOLD_OK=8.0
        THRESHOLD_CAUTION=15.0
        MAX_PARALLEL=3
        ACTIVE_PROFILE="default"
    fi
}

# Get load average (1-minute)
get_load() {
    uptime | awk -F'load averages?: ' '{print $2}' | awk '{print $1}' | tr -d ','
}

# Get memory pressure (macOS)
get_memory_free_percent() {
    if command -v memory_pressure &>/dev/null; then
        memory_pressure 2>/dev/null | grep "System-wide memory free percentage" | awk '{print $NF}' | tr -d '%'
    else
        # Fallback: calculate from vm_stat
        local page_size=$(vm_stat | head -1 | awk '{print $8}')
        local free_pages=$(vm_stat | grep "Pages free" | awk '{print $3}' | tr -d '.')
        local total_pages=$(($(sysctl -n hw.memsize) / ${page_size:-16384}))
        echo $((free_pages * 100 / total_pages))
    fi
}

# Get CPU core count for context
get_cpu_cores() {
    sysctl -n hw.ncpu 2>/dev/null || echo "?"
}

# Count running Claude agent processes (FIXED - PRF-001 v2)
# Uses atomic ps command to avoid race condition between pgrep and ps
# Counts ONLY spawned subagent processes, excluding:
# - The main claude CLI process (parent)
# - MCP server child processes (rag-server, fathom, etc)
get_agent_count() {
    local main_claude=$(pgrep -x "claude" 2>/dev/null | head -1)
    [[ -z "$main_claude" ]] && echo 0 && return 0

    # Atomic count using single ps command with awk filter
    ps -o ppid=,command= 2>/dev/null | awk -v ppid="$main_claude" '
        $1 == ppid && !/mcp-servers|rag-server|fathom|\/bin\/zsh|\/bin\/bash|python|uv/ {count++}
        END {print count+0}
    '
}

# Determine status based on load
get_status() {
    local load=$1
    if (( $(echo "$load < $THRESHOLD_OK" | bc -l) )); then
        echo "OK"
    elif (( $(echo "$load < $THRESHOLD_CAUTION" | bc -l) )); then
        echo "CAUTION"
    else
        echo "HIGH_LOAD"
    fi
}

# Check if spawning is allowed (considers both load and agent count)
can_spawn() {
    local load=$(get_load)
    local status=$(get_status "$load")
    local agent_count=$(get_agent_count)

    if [[ "$status" == "HIGH_LOAD" ]]; then
        return 1
    fi

    if (( agent_count >= MAX_PARALLEL )); then
        return 1
    fi

    return 0
}

# Get spawning recommendation
get_recommendation() {
    local status=$1
    local agent_count=$2

    if (( agent_count >= MAX_PARALLEL )); then
        echo "Agent limit reached ($agent_count/$MAX_PARALLEL) - wait for completion"
        return
    fi

    case $status in
        OK)
            echo "Parallel spawning allowed ($agent_count/$MAX_PARALLEL agents)"
            ;;
        CAUTION)
            echo "Sequential spawning preferred - cascade agents ($agent_count/$MAX_PARALLEL)"
            ;;
        HIGH_LOAD)
            echo "Avoid spawning - work inline or wait"
            ;;
    esac
}

# Main
main() {
    load_thresholds

    local load=$(get_load)
    local mem_free=$(get_memory_free_percent)
    local cores=$(get_cpu_cores)
    local agent_count=$(get_agent_count)
    local status=$(get_status "$load")
    local recommendation=$(get_recommendation "$status" "$agent_count")

    case "${1:-}" in
        --status-only)
            echo "$status"
            ;;
        --can-spawn)
            if can_spawn; then
                exit 0
            else
                exit 1
            fi
            ;;
        --json)
            cat <<EOF
{
  "status": "$status",
  "load_average": $load,
  "memory_free_percent": ${mem_free:-0},
  "cpu_cores": $cores,
  "active_agents": $agent_count,
  "max_parallel_agents": $MAX_PARALLEL,
  "active_profile": "$ACTIVE_PROFILE",
  "thresholds": {
    "ok": $THRESHOLD_OK,
    "caution": $THRESHOLD_CAUTION
  },
  "recommendation": "$recommendation"
}
EOF
            ;;
        *)
            echo "┌─────────────────────────────────────────────────────────────┐"
            echo "│ SYSTEM LOAD CHECK                          [$ACTIVE_PROFILE]"
            echo "├─────────────────────────────────────────────────────────────┤"
            printf "│ Status:      %-46s │\n" "$status"
            printf "│ Load Avg:    %-46s │\n" "$load (cores: $cores)"
            printf "│ Memory Free: %-46s │\n" "${mem_free:-?}%"
            printf "│ Agents:      %-46s │\n" "$agent_count / $MAX_PARALLEL"
            echo "├─────────────────────────────────────────────────────────────┤"
            printf "│ %-59s │\n" "$recommendation"
            echo "└─────────────────────────────────────────────────────────────┘"
            ;;
    esac
}

main "$@"
