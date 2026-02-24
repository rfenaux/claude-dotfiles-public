#!/bin/bash
# sync-memory.sh - Sync global memory to project-specific memory directories
#
# Called by SessionStart hook to ensure project memory includes global patterns.
# Strategy: Copy global MEMORY.md to project memory if newer or missing.

set -euo pipefail

GLOBAL_MEMORY_DIR="$HOME/.claude/memory"
GLOBAL_MEMORY_FILE="$GLOBAL_MEMORY_DIR/MEMORY.md"
PROJECTS_DIR="$HOME/.claude/projects"

# Get current project's memory directory from environment or derive from PWD
get_project_memory_dir() {
    local pwd_encoded
    pwd_encoded=$(echo "$PWD" | sed 's|/|-|g' | sed 's|^-||')
    echo "$PROJECTS_DIR/-$pwd_encoded/memory"
}

sync_to_project() {
    local project_memory_dir="$1"
    local project_memory_file="$project_memory_dir/MEMORY.md"

    # Create project memory directory if it doesn't exist
    mkdir -p "$project_memory_dir"

    # If project has no MEMORY.md, copy global
    if [[ ! -f "$project_memory_file" ]]; then
        if [[ -f "$GLOBAL_MEMORY_FILE" ]]; then
            cp "$GLOBAL_MEMORY_FILE" "$project_memory_file"
            echo "[Memory] Initialized project memory from global"
        fi
        return
    fi

    # Check if project memory starts with "# Global Memory" (is a pure copy)
    if head -1 "$project_memory_file" | grep -q "^# Global Memory"; then
        # It's a global copy - update if global is newer
        if [[ "$GLOBAL_MEMORY_FILE" -nt "$project_memory_file" ]]; then
            cp "$GLOBAL_MEMORY_FILE" "$project_memory_file"
            echo "[Memory] Updated project memory from global"
        fi
    else
        # Project has custom content - don't overwrite
        # But ensure patterns/ symlink exists for reference
        if [[ ! -L "$project_memory_dir/patterns" ]] && [[ -d "$GLOBAL_MEMORY_DIR/patterns" ]]; then
            ln -sf "$GLOBAL_MEMORY_DIR/patterns" "$project_memory_dir/patterns" 2>/dev/null || true
        fi
    fi
}

main() {
    # Ensure global memory exists
    if [[ ! -f "$GLOBAL_MEMORY_FILE" ]]; then
        echo "[Memory] No global MEMORY.md found at $GLOBAL_MEMORY_FILE"
        exit 0
    fi

    case "${1:-sync}" in
        sync)
            # Sync to current project
            project_memory_dir=$(get_project_memory_dir)
            sync_to_project "$project_memory_dir"
            ;;
        sync-all)
            # Sync to all project memory directories
            for dir in "$PROJECTS_DIR"/*/memory; do
                if [[ -d "$dir" ]] || [[ -d "$(dirname "$dir")" ]]; then
                    sync_to_project "$dir"
                fi
            done
            echo "[Memory] Synced global memory to all projects"
            ;;
        status)
            echo "Global memory: $GLOBAL_MEMORY_FILE"
            if [[ -f "$GLOBAL_MEMORY_FILE" ]]; then
                echo "  Lines: $(wc -l < "$GLOBAL_MEMORY_FILE")"
                echo "  Modified: $(stat -f '%Sm' "$GLOBAL_MEMORY_FILE")"
            fi
            echo ""
            echo "Project memories:"
            find "$PROJECTS_DIR" -path "*/memory/MEMORY.md" -exec sh -c '
                for f; do
                    proj=$(dirname $(dirname "$f") | sed "s|.*/projects/||")
                    lines=$(wc -l < "$f" | tr -d " ")
                    echo "  $proj: $lines lines"
                done
            ' _ {} +
            ;;
        *)
            echo "Usage: $0 [sync|sync-all|status]"
            exit 1
            ;;
    esac
}

main "$@"
