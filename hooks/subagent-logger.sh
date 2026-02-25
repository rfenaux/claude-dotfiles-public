#!/bin/bash
set +e  # fail-silent: hooks must not abort on error

# Subagent activity logger - handles SubagentStart, TeammateIdle, TaskCompleted
# Tries multiple field names to avoid "unknown" types

# Read JSON input
input=$(cat)

LOG_FILE="$HOME/.claude/logs/subagent-activity.log"
mkdir -p "$(dirname "$LOG_FILE")"

# Detect event type from hook context (SubagentStart vs TeammateIdle vs TaskCompleted)
# Extract fields with fallback chain for field names
if command -v jq &>/dev/null; then
    # Try multiple field names for type: subagent_type > agent_type > type
    agent_type=$(echo "$input" | jq -r '
        .subagent_type //
        .agent_type //
        .type //
        .tool_input.subagent_type //
        .tool_input.type //
        "unknown"
    ' 2>/dev/null || echo "unknown")

    agent_id=$(echo "$input" | jq -r '
        .agent_id //
        .subagent_id //
        .id //
        "unknown"
    ' 2>/dev/null || echo "unknown")

    # Extract agent name if available (useful for TeammateIdle/TaskCompleted)
    agent_name=$(echo "$input" | jq -r '
        .agent_name //
        .name //
        .tool_input.name //
        ""
    ' 2>/dev/null || echo "")

    # Extract model if available
    model=$(echo "$input" | jq -r '
        .model //
        .tool_input.model //
        ""
    ' 2>/dev/null || echo "")

    # Extract prompt preview (first 100 chars)
    prompt=$(echo "$input" | jq -r '
        (.tool_input.prompt // .prompt // .description // "")[:100]
    ' 2>/dev/null || echo "")
else
    # Fallback without jq - try multiple field patterns
    agent_type=$(echo "$input" | grep -oE '"(subagent_type|agent_type|type)"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | cut -d'"' -f4 || echo "unknown")
    agent_id=$(echo "$input" | grep -oE '"(agent_id|subagent_id|id)"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | cut -d'"' -f4 || echo "unknown")
    agent_name=""
    model=""
    prompt=""
fi

# Debug logging for unknown types (temporary - remove after 1 week / 2026-02-20)
DEBUG_LOG="$HOME/.claude/logs/subagent-debug.log"
if [[ "$agent_type" == "unknown" ]]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] RAW: ${input:0:300}" >> "$DEBUG_LOG"
fi

# Build log entry with available fields
TS=$(date '+%Y-%m-%d %H:%M:%S')
ENTRY="[$TS] type=$agent_type id=$agent_id"
[[ -n "$agent_name" ]] && ENTRY="$ENTRY name=$agent_name"
[[ -n "$model" ]] && ENTRY="$ENTRY model=$model"
[[ -n "$prompt" ]] && ENTRY="$ENTRY prompt=\"${prompt//\"/\\\"}\""

echo "$ENTRY" >> "$LOG_FILE"

# Feed agent data to intent_predictor for routing learning (fire-and-forget, async)
{
    PYTHONPATH="$HOME/.claude/lib" python3 -c "
import sys
sys.path.insert(0, '$HOME/.claude/lib')
from intent_predictor import track_agent_usage
track_agent_usage(
    agent_type='$agent_type',
    context='${prompt:0:100}',
    model='$model',
    prompt_preview='${prompt:0:100}'
)
" 2>/dev/null || true
} &

# F4: Track idle state for team health monitoring
# When TeammateIdle fires, record idle_since timestamp for stuck detection
{
    # Detect if this is a TeammateIdle event (agent_name present, no prompt = idle notification)
    if [[ -n "$agent_name" ]] && [[ -z "$prompt" ]]; then
        # Find which team this agent belongs to
        for team_config in "$HOME"/.claude/teams/*/config.json; do
            [[ -f "$team_config" ]] || continue
            team_dir=$(dirname "$team_config")
            team_name=$(basename "$team_dir")

            # Check if agent is a member of this team
            if command -v jq &>/dev/null; then
                is_member=$(jq -r --arg name "$agent_name" '.members[]? | select(.name == $name) | .name' "$team_config" 2>/dev/null || echo "")
                if [[ -n "$is_member" ]]; then
                    STATE_FILE="/tmp/team-${team_name}-idle-state.json"

                    # Create or update idle state
                    NOW=$(date +%s)
                    if [[ -f "$STATE_FILE" ]]; then
                        # Update existing state
                        jq --arg name "$agent_name" --arg ts "$NOW" \
                            '.[$name].idle_since = ($ts | tonumber) | .[$name].has_active_task = true' \
                            "$STATE_FILE" > "${STATE_FILE}.tmp" 2>/dev/null && \
                            mv "${STATE_FILE}.tmp" "$STATE_FILE"
                    else
                        # Create new state file
                        echo "{\"$agent_name\": {\"idle_since\": $NOW, \"has_active_task\": true}}" > "$STATE_FILE"
                    fi
                    break
                fi
            fi
        done
    fi
} 2>/dev/null &

exit 0
