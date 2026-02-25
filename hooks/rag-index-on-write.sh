#!/bin/bash
set +e  # Never use set -e in hooks — non-zero exits kill the hook
# Real-time RAG indexing for files created/modified during conversation
# Triggered by PostToolUse hook on Write and Edit tools

# Read hook input from stdin
# Circuit breaker: skip if too many recent failures
. "$HOME/.claude/hooks/lib/circuit-breaker.sh" 2>/dev/null
check_circuit "rag-index-on-write" || exit 0

HOOK_INPUT=$(cat)
TOOL_NAME=$(echo "$HOOK_INPUT" | jq -r '.tool_name // empty')
TOOL_INPUT=$(echo "$HOOK_INPUT" | jq -r '.tool_input // empty')
CWD=$(echo "$HOOK_INPUT" | jq -r '.cwd // empty')

# Only process Write and Edit tools
case "$TOOL_NAME" in
    Write|Edit)
        ;;
    *)
        exit 0
        ;;
esac

# Get the file path from tool input
FILE_PATH=$(echo "$TOOL_INPUT" | jq -r '.file_path // empty')

# Skip if no file path
[ -z "$FILE_PATH" ] || [ "$FILE_PATH" = "null" ] && exit 0

# Determine project path (CWD or parent of file)
if [ -n "$CWD" ] && [ "$CWD" != "null" ]; then
    PROJECT_PATH="$CWD"
else
    PROJECT_PATH=$(dirname "$FILE_PATH")
fi

# Only index for project directories with RAG enabled (check for .rag/ folder)
# No path restriction — any project with .rag/ initialized gets indexed

# Find the .rag folder (might be in parent directories)
RAG_DIR=""
CHECK_PATH="$PROJECT_PATH"
while [ "$CHECK_PATH" != "/" ]; do
    if [ -d "$CHECK_PATH/.rag" ]; then
        RAG_DIR="$CHECK_PATH/.rag"
        PROJECT_PATH="$CHECK_PATH"
        break
    fi
    CHECK_PATH=$(dirname "$CHECK_PATH")
done

# Skip if no RAG folder found
[ -z "$RAG_DIR" ] && exit 0

# Check if file extension is indexable
EXT="${FILE_PATH##*.}"
EXT_LOWER=$(echo "$EXT" | tr '[:upper:]' '[:lower:]')

case "$EXT_LOWER" in
    md|txt|json|pdf|docx|html|py|js|ts|tsx|jsx)
        ;;
    *)
        exit 0  # Skip non-indexable extensions
        ;;
esac

# Skip files in excluded directories
case "$FILE_PATH" in
    */.git/*|*/.rag/*|*/node_modules/*|*/__pycache__/*|*/.venv/*|*/venv/*|*/.claude/*)
        exit 0
        ;;
esac

# Submit to queue instead of spawning a direct Python process.
# The queue worker ensures only one indexing job runs at a time.
SUBMIT="$HOME/.claude/mcp-servers/rag-server/queue/submit.sh"
if [ -x "$SUBMIT" ]; then
    "$SUBMIT" index "$FILE_PATH" "$PROJECT_PATH" 8 2>/dev/null || record_failure "rag-index-on-write" &
fi

exit 0
