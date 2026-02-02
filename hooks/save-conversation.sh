#!/bin/bash
# Save Claude Code conversation to project folder and optionally RAG-index it
# Used by PreCompact and SessionEnd hooks

set -e

# Read hook input from stdin
HOOK_INPUT=$(cat)
TRANSCRIPT_PATH=$(echo "$HOOK_INPUT" | jq -r '.transcript_path')
SESSION_ID=$(echo "$HOOK_INPUT" | jq -r '.session_id')
CWD=$(echo "$HOOK_INPUT" | jq -r '.cwd')
HOOK_EVENT=$(echo "$HOOK_INPUT" | jq -r '.hook_event_name')
TRIGGER=$(echo "$HOOK_INPUT" | jq -r '.trigger // .reason // "unknown"')

# Skip if no transcript or CWD
[ -z "$TRANSCRIPT_PATH" ] || [ "$TRANSCRIPT_PATH" = "null" ] && exit 0
[ -z "$CWD" ] || [ "$CWD" = "null" ] && exit 0
[ ! -f "$TRANSCRIPT_PATH" ] && exit 0

# Determine history folder based on directory type
# Project directories: save to project folder
# Other directories: save to global ~/.claude/conversation-history/
if [[ "$CWD" =~ ^~/Documents/(Projects|Docs) ]]; then
    HISTORY_DIR="$CWD/conversation-history"
    IS_PROJECT=true
else
    HISTORY_DIR="$HOME/.claude/conversation-history"
    IS_PROJECT=false
fi
mkdir -p "$HISTORY_DIR"

# Generate filename: YYYY-MM-DD_HHMMSS_event_trigger.jsonl
TIMESTAMP=$(date +%Y-%m-%d_%H%M%S)
SHORT_SESSION=$(echo "$SESSION_ID" | cut -c1-8)
FILENAME="${TIMESTAMP}_${SHORT_SESSION}_${HOOK_EVENT}_${TRIGGER}.jsonl"
DEST_FILE="$HISTORY_DIR/$FILENAME"

# Copy transcript
cp "$TRANSCRIPT_PATH" "$DEST_FILE"

# Optional: Create human-readable markdown version
MD_FILE="${DEST_FILE%.jsonl}.md"
{
    echo "# Conversation: $TIMESTAMP"
    echo ""
    echo "- **Session**: $SESSION_ID"
    echo "- **Event**: $HOOK_EVENT ($TRIGGER)"
    echo "- **Project**: $CWD"
    echo ""
    echo "---"
    echo ""

    # Parse JSONL and extract messages
    while IFS= read -r line; do
        TYPE=$(echo "$line" | jq -r '.type // empty')

        case "$TYPE" in
            "human"|"user")
                echo "## 👤 User"
                echo ""
                echo "$line" | jq -r '.message.content // .content // empty' 2>/dev/null | head -500
                echo ""
                ;;
            "assistant")
                echo "## 🤖 Assistant"
                echo ""
                # Extract text content from assistant messages
                echo "$line" | jq -r '
                    if .message.content then
                        if (.message.content | type) == "array" then
                            [.message.content[] | select(.type == "text") | .text] | join("\n")
                        else
                            .message.content
                        end
                    elif .content then
                        if (.content | type) == "array" then
                            [.content[] | select(.type == "text") | .text] | join("\n")
                        else
                            .content
                        end
                    else
                        empty
                    end
                ' 2>/dev/null | head -1000
                echo ""
                ;;
        esac
    done < "$DEST_FILE"
} > "$MD_FILE" 2>/dev/null || true

# Optional: Auto-index with RAG if .rag folder exists
if [ -d "$CWD/.rag" ]; then
    # Track last index time for incremental indexing
    LAST_INDEX_FILE="$CWD/.rag/.last_index_time"
    CURRENT_TIME=$(date +%s)

    # Get time of last index (default to 24 hours ago if not set)
    if [ -f "$LAST_INDEX_FILE" ]; then
        LAST_INDEX_TIME=$(cat "$LAST_INDEX_FILE")
    else
        LAST_INDEX_TIME=$((CURRENT_TIME - 86400))  # 24 hours ago
    fi

    # Calculate minutes since last index for find command
    MINS_SINCE_LAST=$(( (CURRENT_TIME - LAST_INDEX_TIME) / 60 + 1 ))

    # Find and index all recently modified indexable files
    ~/.local/bin/uv run --directory ~/.claude/mcp-servers/rag-server python -c "
import sys
import os
import subprocess
from datetime import datetime
sys.path.insert(0, '~/.claude/mcp-servers/rag-server/src')
from rag_server.server import rag_index

project_path = '$CWD'
mins = $MINS_SINCE_LAST
rag_dir = project_path + '/.rag'

# Extensions to index
INDEXABLE = {'.md', '.txt', '.json', '.pdf', '.docx', '.html', '.py', '.js', '.ts'}

# Folders to skip
SKIP_DIRS = {'.git', '.rag', 'node_modules', '__pycache__', '.venv', 'venv', '.claude'}

indexed_files = []

# Find recently modified files
result = subprocess.run(
    ['find', project_path, '-type', 'f', '-mmin', '-{}'.format(mins)],
    capture_output=True, text=True
)

for filepath in result.stdout.strip().split('\n'):
    if not filepath:
        continue

    # Skip excluded directories
    rel_path = os.path.relpath(filepath, project_path)
    if any(skip in rel_path.split(os.sep) for skip in SKIP_DIRS):
        continue

    # Check extension
    ext = os.path.splitext(filepath)[1].lower()
    if ext not in INDEXABLE:
        continue

    try:
        rag_index(filepath, project_path)
        indexed_files.append(rel_path)
    except Exception:
        pass  # Silent fail per file

# Update last index time
with open('$LAST_INDEX_FILE', 'w') as f:
    f.write(str($CURRENT_TIME))

# Log to activity file
if indexed_files:
    log_file = os.path.join(rag_dir, '.index_activity.log')
    timestamp = datetime.now().isoformat()

    # Read existing, keep last entries
    lines = []
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            lines = f.readlines()[-(100 - len(indexed_files)):]

    with open(log_file, 'w') as f:
        f.writelines(lines)
        for rel_path in indexed_files:
            f.write(f'{timestamp}|batch|{rel_path}\n')

    sys.stderr.write(f'RAG: indexed {len(indexed_files)} modified files\n')
" 2>/dev/null &
fi

# Call lesson extractor for all conversations (not just projects)
LESSON_EXTRACTOR="$HOME/.claude/hooks/lesson-extractor.sh"
if [ -x "$LESSON_EXTRACTOR" ]; then
    "$LESSON_EXTRACTOR" "$DEST_FILE" "$SESSION_ID" &
fi

echo "Conversation saved: $FILENAME" >&2
exit 0
