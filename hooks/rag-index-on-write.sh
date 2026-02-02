#!/bin/bash
# Real-time RAG indexing for files created/modified during conversation
# Triggered by PostToolUse hook on Write and Edit tools

# Read hook input from stdin
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

# Only index for project directories with RAG enabled
if [[ ! "$PROJECT_PATH" =~ ^~/Documents/(Projects|Docs) ]]; then
    exit 0
fi

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

# Index the file asynchronously (don't block the conversation)
~/.local/bin/uv run --directory ~/.claude/mcp-servers/rag-server python -c "
import sys
import os
from datetime import datetime
sys.path.insert(0, '~/.claude/mcp-servers/rag-server/src')
from rag_server.server import rag_index

file_path = '$FILE_PATH'
project_path = '$PROJECT_PATH'
rag_dir = '$RAG_DIR'

try:
    result = rag_index(file_path, project_path)

    # Log successful indexing to activity log
    log_file = os.path.join(rag_dir, '.index_activity.log')
    rel_path = os.path.relpath(file_path, project_path)
    timestamp = datetime.now().isoformat()

    # Append to log (keep last 100 entries)
    lines = []
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            lines = f.readlines()[-99:]  # Keep last 99 + new = 100

    with open(log_file, 'w') as f:
        f.writelines(lines)
        f.write(f'{timestamp}|realtime|{rel_path}\n')

    sys.stderr.write(f'RAG: indexed {rel_path}\n')
except Exception as e:
    pass  # Silent fail
" 2>/dev/null &

exit 0
