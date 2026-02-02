#!/bin/bash
# Git Post-Commit RAG Reindex Hook
# Triggers RAG reindexing of changed files after git commit
#
# Integration: git commit → RAG reindex
# Install: Copy to .git/hooks/post-commit in each project

set -e

LOG_FILE="$HOME/.claude/ctm/logs/rag-integration.log"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [git-post-commit-rag] $1" >> "$LOG_FILE"
}

PROJECT_DIR="$(git rev-parse --show-toplevel 2>/dev/null)"

if [ -z "$PROJECT_DIR" ]; then
    log "Not in a git repository"
    exit 0
fi

# Check if project has RAG
if [ ! -d "$PROJECT_DIR/.rag" ]; then
    log "No RAG in $PROJECT_DIR, skipping"
    exit 0
fi

log "RAG reindex triggered for $PROJECT_DIR"

# Get list of changed files in last commit
CHANGED_FILES=$(git diff-tree --no-commit-id --name-only -r HEAD 2>/dev/null || echo "")

if [ -z "$CHANGED_FILES" ]; then
    log "No changed files detected"
    exit 0
fi

# Filter to indexable files (markdown, text, etc.)
INDEXABLE_EXTENSIONS="md|txt|html|pdf|docx"
INDEXABLE_FILES=""

for file in $CHANGED_FILES; do
    if echo "$file" | grep -qE "\.($INDEXABLE_EXTENSIONS)$"; then
        if [ -f "$PROJECT_DIR/$file" ]; then
            INDEXABLE_FILES="$INDEXABLE_FILES $file"
        fi
    fi
done

if [ -z "$INDEXABLE_FILES" ]; then
    log "No indexable files changed"
    exit 0
fi

# Reindex changed files via rag-server
# Uses the MCP server endpoint
log "Reindexing files:$INDEXABLE_FILES"

# Call RAG index for each file (background, non-blocking)
for file in $INDEXABLE_FILES; do
    FULL_PATH="$PROJECT_DIR/$file"
    log "Indexing: $FULL_PATH"

    # Try to call rag index via Python (MCP client)
    python3 << EOF &
import sys
sys.path.insert(0, "$HOME/.claude/rag-dashboard")
try:
    from pathlib import Path
    import subprocess
    # Use the rag-server's direct indexing if available
    result = subprocess.run(
        ["python3", "-m", "rag_server.index", "--path", "$FULL_PATH", "--project", "$PROJECT_DIR"],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode == 0:
        print(f"Indexed: $file")
except Exception as e:
    print(f"Index skipped: {e}")
EOF
done

wait
log "RAG reindex complete"
echo "[RAG] Reindexed ${#INDEXABLE_FILES[@]} files"
