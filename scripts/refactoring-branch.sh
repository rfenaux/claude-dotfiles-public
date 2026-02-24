#!/bin/bash
# refactoring-branch.sh - Git branch lifecycle for multi-file refactoring
#
# Usage:
#   refactoring-branch.sh create <old_name> <new_name>  # Create refactoring branch
#   refactoring-branch.sh commit [message]                # Commit with template message
#   refactoring-branch.sh rollback                        # Return to original branch, delete refactoring branch
#   refactoring-branch.sh status                          # Show current refactoring state
#
# State tracked in /tmp/refactor-state.json

set -euo pipefail

STATE_FILE="/tmp/refactor-state.json"

# Ensure we're in a git repo
ensure_git() {
    if ! git rev-parse --is-inside-work-tree &>/dev/null; then
        echo "ERROR: Not inside a git repository" >&2
        exit 1
    fi
}

# Create refactoring branch
create_branch() {
    local old_name="$1"
    local new_name="$2"
    local scope="${3:-.}"

    ensure_git

    # Check for uncommitted changes
    if ! git diff --quiet || ! git diff --cached --quiet; then
        echo "WARNING: Uncommitted changes detected. Stashing..." >&2
        git stash push -m "refactoring-branch: pre-refactor stash"
    fi

    local original_branch
    original_branch=$(git symbolic-ref --short HEAD 2>/dev/null || git rev-parse --short HEAD)
    local timestamp
    timestamp=$(date '+%Y%m%d-%H%M%S')
    local branch_name="refactor/${old_name}-to-${new_name}-${timestamp}"

    # Create and switch to refactoring branch
    git checkout -b "$branch_name"

    # Write state file
    cat > "$STATE_FILE" <<EOF
{
    "old_name": "$old_name",
    "new_name": "$new_name",
    "scope": "$scope",
    "original_branch": "$original_branch",
    "refactor_branch": "$branch_name",
    "created_at": "$(date -u '+%Y-%m-%dT%H:%M:%SZ')",
    "status": "in_progress",
    "commits": 0
}
EOF

    echo "Created refactoring branch: $branch_name"
    echo "Original branch: $original_branch"
    echo "State: $STATE_FILE"
}

# Commit refactoring changes
commit_changes() {
    ensure_git

    if [[ ! -f "$STATE_FILE" ]]; then
        echo "ERROR: No active refactoring. Run 'create' first." >&2
        exit 1
    fi

    local old_name new_name commits
    old_name=$(python3 -c "import json; print(json.load(open('$STATE_FILE'))['old_name'])")
    new_name=$(python3 -c "import json; print(json.load(open('$STATE_FILE'))['new_name'])")
    commits=$(python3 -c "import json; print(json.load(open('$STATE_FILE'))['commits'])")

    local message="${1:-refactor: rename $old_name to $new_name}"

    # Stage all changes
    git add -A

    # Check if there are changes to commit
    if git diff --cached --quiet; then
        echo "No changes to commit."
        return 0
    fi

    git commit -m "$message

Automated refactoring: $old_name -> $new_name
Commit $((commits + 1)) in refactoring series

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"

    # Update state
    python3 -c "
import json
with open('$STATE_FILE', 'r') as f:
    state = json.load(f)
state['commits'] = state['commits'] + 1
state['last_commit_at'] = '$(date -u '+%Y-%m-%dT%H:%M:%SZ')'
with open('$STATE_FILE', 'w') as f:
    json.dump(state, f, indent=4)
"

    echo "Committed: $message"
}

# Rollback refactoring
rollback() {
    ensure_git

    if [[ ! -f "$STATE_FILE" ]]; then
        echo "ERROR: No active refactoring to rollback." >&2
        exit 1
    fi

    local original_branch refactor_branch
    original_branch=$(python3 -c "import json; print(json.load(open('$STATE_FILE'))['original_branch'])")
    refactor_branch=$(python3 -c "import json; print(json.load(open('$STATE_FILE'))['refactor_branch'])")

    # Switch back to original branch
    git checkout "$original_branch"

    # Delete refactoring branch
    git branch -D "$refactor_branch" 2>/dev/null || true

    # Clean up state
    rm -f "$STATE_FILE"

    echo "Rolled back to: $original_branch"
    echo "Deleted branch: $refactor_branch"
}

# Show current state
show_status() {
    if [[ ! -f "$STATE_FILE" ]]; then
        echo "No active refactoring."
        return 0
    fi

    python3 -c "
import json
state = json.load(open('$STATE_FILE'))
print(f\"Refactoring: {state['old_name']} -> {state['new_name']}\")
print(f\"Branch:      {state['refactor_branch']}\")
print(f\"Original:    {state['original_branch']}\")
print(f\"Scope:       {state['scope']}\")
print(f\"Status:      {state['status']}\")
print(f\"Commits:     {state['commits']}\")
print(f\"Created:     {state['created_at']}\")
"
}

# Get current refactoring info (for scripts)
get_current() {
    if [[ ! -f "$STATE_FILE" ]]; then
        echo "{}"
        return 1
    fi
    cat "$STATE_FILE"
}

# Main
case "${1:-status}" in
    create)
        if [[ $# -lt 3 ]]; then
            echo "Usage: refactoring-branch.sh create <old_name> <new_name> [scope]" >&2
            exit 1
        fi
        create_branch "$2" "$3" "${4:-.}"
        ;;
    commit)
        commit_changes "${2:-}"
        ;;
    rollback)
        rollback
        ;;
    status)
        show_status
        ;;
    get)
        get_current
        ;;
    *)
        echo "Usage: refactoring-branch.sh {create|commit|rollback|status|get}" >&2
        exit 1
        ;;
esac
