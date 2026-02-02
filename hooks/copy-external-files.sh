#!/bin/bash
# Copy tracked external files into project and RAG index them
# Triggered by PreCompact and SessionEnd hooks
# Runs asynchronously to avoid blocking

HOOK_INPUT=$(cat)
CWD=$(echo "$HOOK_INPUT" | jq -r '.cwd // empty')
SESSION_ID=$(echo "$HOOK_INPUT" | jq -r '.session_id // empty')

MANIFEST_DIR="/tmp/claude-external-files"

# Find the manifest file
MANIFEST_FILE=""
if [ -n "$SESSION_ID" ] && [ "$SESSION_ID" != "null" ] && [ -f "$MANIFEST_DIR/$SESSION_ID.manifest" ]; then
    MANIFEST_FILE="$MANIFEST_DIR/$SESSION_ID.manifest"
elif [ -n "$CWD" ] && [ "$CWD" != "null" ]; then
    # Try project hash fallback
    if [[ "$CWD" =~ ^~/Documents/Projects ]]; then
        PROJECT_ROOT=$(echo "$CWD" | sed -E 's|^(~/Documents/Projects[^/]*/[^/]+).*|\1|')
        PROJECT_HASH=$(echo "$PROJECT_ROOT" | md5 -q)
        [ -f "$MANIFEST_DIR/$PROJECT_HASH.manifest" ] && MANIFEST_FILE="$MANIFEST_DIR/$PROJECT_HASH.manifest"
    fi
fi

# Nothing to process
[ -z "$MANIFEST_FILE" ] || [ ! -f "$MANIFEST_FILE" ] && exit 0

# Process asynchronously
(
    LOG_FILE="$MANIFEST_DIR/copy.log"

    while IFS='|' read -r PROJECT_ROOT SOURCE_PATH; do
        [ -z "$PROJECT_ROOT" ] || [ -z "$SOURCE_PATH" ] && continue
        [ ! -f "$SOURCE_PATH" ] && continue

        # Determine destination folder
        DEST_DIR="$PROJECT_ROOT/external-sources"
        mkdir -p "$DEST_DIR"

        # Preserve some path context in filename to avoid collisions
        # e.g., ~/Downloads/report.pdf -> Downloads_report.pdf
        PARENT_DIR=$(basename "$(dirname "$SOURCE_PATH")")
        FILENAME=$(basename "$SOURCE_PATH")

        # If parent is generic (like Downloads, Desktop), include it
        case "$PARENT_DIR" in
            Downloads|Desktop|Documents|tmp)
                DEST_FILENAME="${PARENT_DIR}_${FILENAME}"
                ;;
            *)
                DEST_FILENAME="$FILENAME"
                ;;
        esac

        DEST_PATH="$DEST_DIR/$DEST_FILENAME"

        # Skip if already exists with same content
        if [ -f "$DEST_PATH" ]; then
            if cmp -s "$SOURCE_PATH" "$DEST_PATH"; then
                echo "$(date -Iseconds) SKIP (identical): $SOURCE_PATH" >> "$LOG_FILE"
                continue
            else
                # File exists but different - add timestamp
                TIMESTAMP=$(date +%Y%m%d_%H%M%S)
                EXT="${FILENAME##*.}"
                NAME="${FILENAME%.*}"
                DEST_FILENAME="${PARENT_DIR}_${NAME}_${TIMESTAMP}.${EXT}"
                DEST_PATH="$DEST_DIR/$DEST_FILENAME"
            fi
        fi

        # Copy the file
        if cp "$SOURCE_PATH" "$DEST_PATH" 2>/dev/null; then
            echo "$(date -Iseconds) COPIED: $SOURCE_PATH -> $DEST_PATH" >> "$LOG_FILE"

            # RAG index if project has RAG enabled
            if [ -d "$PROJECT_ROOT/.rag" ]; then
                ~/.local/bin/uv run --directory ~/.claude/mcp-servers/rag-server python -c "
import sys
sys.path.insert(0, '~/.claude/mcp-servers/rag-server/src')
from rag_server.server import rag_index
try:
    rag_index('$DEST_PATH', '$PROJECT_ROOT')
except Exception as e:
    pass  # Silent fail for RAG indexing
" 2>/dev/null
                echo "$(date -Iseconds) INDEXED: $DEST_PATH" >> "$LOG_FILE"
            fi
        else
            echo "$(date -Iseconds) FAILED: $SOURCE_PATH" >> "$LOG_FILE"
        fi

    done < "$MANIFEST_FILE"

    # Clean up manifest after processing
    rm -f "$MANIFEST_FILE"

    # Clean up old manifests (older than 24h)
    find "$MANIFEST_DIR" -name "*.manifest" -mtime +1 -delete 2>/dev/null

) &

exit 0
