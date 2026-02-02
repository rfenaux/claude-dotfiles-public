#!/bin/bash
# ctm-context.sh - Extract current CTM task context for RAG searches
# Returns JSON with active task details (task_id, title, tags, project)

set -e

CTM_INDEX="$HOME/.claude/ctm/index.json"

# Exit silently if no CTM data
if [ ! -f "$CTM_INDEX" ]; then
    exit 0
fi

# Check if jq is available
if ! command -v jq &> /dev/null; then
    exit 0
fi

# Get active task (prefer "active" status, fallback to "paused")
TASK_DATA=$(jq -r '
    .agents | to_entries[] |
    select(.value.status == "active" or .value.status == "paused") |
    {
        task_id: .key,
        title: .value.title,
        tags: (.value.tags // []),
        project: .value.project,
        status: .value.status
    }
' "$CTM_INDEX" 2>/dev/null | jq -s 'sort_by(.status != "active") | .[0]' 2>/dev/null)

# If no active/paused tasks, get most recently active one
if [ -z "$TASK_DATA" ] || [ "$TASK_DATA" = "null" ]; then
    TASK_DATA=$(jq -r '
        [.agents | to_entries[] |
        {
            task_id: .key,
            title: .value.title,
            tags: (.value.tags // []),
            project: .value.project,
            last_active: .value.last_active
        }] |
        sort_by(.last_active) | reverse | .[0]
    ' "$CTM_INDEX" 2>/dev/null)
fi

# Exit silently if still no task found
if [ -z "$TASK_DATA" ] || [ "$TASK_DATA" = "null" ]; then
    exit 0
fi

# Output JSON
echo "$TASK_DATA"
