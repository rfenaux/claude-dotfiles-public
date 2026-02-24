#!/bin/bash
# MEM-001 Workaround: Session Prompt Manager
#
# Manage temporary session-specific prompts that get injected at session start.
# Alternative to --append-system-prompt CLI flag.

SESSION_DIR="$HOME/.claude/session-prompts"

usage() {
    echo "Usage: session-prompt <command> [args]"
    echo ""
    echo "Commands:"
    echo "  list              List active session prompts"
    echo "  add <file>        Copy file to session prompts"
    echo "  add -m <text>     Create inline prompt from text"
    echo "  remove <name>     Remove a session prompt"
    echo "  clear             Remove all session prompts"
    echo "  show <name>       Show content of a prompt"
    echo "  edit <name>       Edit a prompt (uses \$EDITOR)"
    echo ""
    echo "Examples:"
    echo "  session-prompt add -m 'Focus on API security'"
    echo "  session-prompt add ~/contexts/security-audit.md"
    echo "  session-prompt list"
    echo "  session-prompt clear"
    echo ""
    echo "Session prompts are injected at Claude Code startup via SessionStart hook."
    echo "Files are stored in: $SESSION_DIR"
}

ensure_dir() {
    mkdir -p "$SESSION_DIR"
}

cmd_list() {
    ensure_dir
    local files=$(find "$SESSION_DIR" -maxdepth 1 -name "*.md" -type f 2>/dev/null | sort)

    if [ -z "$files" ]; then
        echo "No active session prompts."
        echo "Add one with: session-prompt add -m 'Your context here'"
        return 0
    fi

    echo "Active session prompts:"
    echo ""
    for file in $files; do
        local name=$(basename "$file")
        local lines=$(wc -l < "$file" | tr -d ' ')
        local words=$(wc -w < "$file" | tr -d ' ')
        echo "  - $name ($lines lines, ~$words tokens)"
    done
    echo ""
    echo "These will be injected at next session start."
}

cmd_add() {
    ensure_dir

    if [ "$1" = "-m" ]; then
        # Inline text mode
        shift
        if [ -z "$1" ]; then
            echo "Error: No text provided"
            echo "Usage: session-prompt add -m 'Your prompt text'"
            return 1
        fi

        local timestamp=$(date +%Y%m%d-%H%M%S)
        local filename="inline-$timestamp.md"
        echo "$@" > "$SESSION_DIR/$filename"
        echo "Created: $filename"

    elif [ -f "$1" ]; then
        # File mode
        local filename=$(basename "$1")
        cp "$1" "$SESSION_DIR/$filename"
        echo "Added: $filename"

    else
        echo "Error: File not found: $1"
        return 1
    fi

    echo "Will be injected at next session start."
}

cmd_remove() {
    local name="$1"
    if [ -z "$name" ]; then
        echo "Error: No name provided"
        echo "Usage: session-prompt remove <name>"
        return 1
    fi

    # Add .md if not present
    [[ "$name" != *.md ]] && name="$name.md"

    local file="$SESSION_DIR/$name"
    if [ -f "$file" ]; then
        rm "$file"
        echo "Removed: $name"
    else
        echo "Not found: $name"
        return 1
    fi
}

cmd_clear() {
    ensure_dir
    local count=$(find "$SESSION_DIR" -maxdepth 1 -name "*.md" -type f 2>/dev/null | wc -l | tr -d ' ')

    if [ "$count" -eq 0 ]; then
        echo "No session prompts to clear."
        return 0
    fi

    rm -f "$SESSION_DIR"/*.md
    echo "Cleared $count session prompt(s)."
}

cmd_show() {
    local name="$1"
    if [ -z "$name" ]; then
        echo "Error: No name provided"
        return 1
    fi

    [[ "$name" != *.md ]] && name="$name.md"
    local file="$SESSION_DIR/$name"

    if [ -f "$file" ]; then
        cat "$file"
    else
        echo "Not found: $name"
        return 1
    fi
}

cmd_edit() {
    local name="$1"
    if [ -z "$name" ]; then
        echo "Error: No name provided"
        return 1
    fi

    [[ "$name" != *.md ]] && name="$name.md"
    local file="$SESSION_DIR/$name"

    ${EDITOR:-vim} "$file"
}

# Main
case "${1:-}" in
    list|ls)
        cmd_list
        ;;
    add)
        shift
        cmd_add "$@"
        ;;
    remove|rm)
        shift
        cmd_remove "$@"
        ;;
    clear)
        cmd_clear
        ;;
    show|cat)
        shift
        cmd_show "$@"
        ;;
    edit)
        shift
        cmd_edit "$@"
        ;;
    -h|--help|help|"")
        usage
        ;;
    *)
        echo "Unknown command: $1"
        usage
        exit 1
        ;;
esac
