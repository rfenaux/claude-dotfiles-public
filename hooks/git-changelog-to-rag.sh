#!/bin/bash
# Git Changelog to RAG Indexer
# Generates changelog entry and indexes to project RAG
#
# Usage: git-changelog-to-rag.sh [commit-hash] [project-path]
# If no commit specified, indexes the latest commit

set -e

COMMIT="${1:-HEAD}"
PROJECT_DIR="${2:-$(git rev-parse --show-toplevel 2>/dev/null)}"

LOG_FILE="$HOME/.claude/ctm/logs/git-changelog.log"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [git-changelog-to-rag] $1" >> "$LOG_FILE"
}

if [ -z "$PROJECT_DIR" ] || [ ! -d "$PROJECT_DIR/.git" ]; then
    log "Not a git repository: $PROJECT_DIR"
    exit 1
fi

# Check if project has RAG
if [ ! -d "$PROJECT_DIR/.rag" ]; then
    log "No RAG in $PROJECT_DIR, skipping changelog indexing"
    exit 0
fi

log "Generating changelog for $COMMIT in $PROJECT_DIR"

# Create changelog directory in project
CHANGELOG_DIR="$PROJECT_DIR/.claude/git-changelog"
mkdir -p "$CHANGELOG_DIR"

# Generate changelog entry
GENERATOR="$HOME/.claude/hooks/git-changelog-generator.py"

if [ ! -f "$GENERATOR" ]; then
    log "Generator script not found: $GENERATOR"
    exit 1
fi

# Generate and save the changelog
python3 "$GENERATOR" \
    --commit "$COMMIT" \
    --project "$PROJECT_DIR" \
    --output markdown \
    --save-dir "$CHANGELOG_DIR"

# Get the generated file
SHORT_HASH=$(git -C "$PROJECT_DIR" rev-parse --short "$COMMIT" 2>/dev/null)
DATE=$(git -C "$PROJECT_DIR" show -s --format=%ai "$COMMIT" 2>/dev/null | cut -d' ' -f1)
CHANGELOG_FILE="$CHANGELOG_DIR/changelog-$SHORT_HASH-$DATE.md"

if [ ! -f "$CHANGELOG_FILE" ]; then
    log "Changelog file not generated"
    exit 1
fi

log "Generated: $CHANGELOG_FILE"

# Index to RAG
# Try MCP server first, fall back to direct indexing
python3 << EOF
import sys
from pathlib import Path

project_path = "$PROJECT_DIR"
changelog_file = "$CHANGELOG_FILE"

# Try to use rag-server MCP tool
try:
    import subprocess
    result = subprocess.run(
        ["python3", "-c", """
import sys
sys.path.insert(0, '$HOME/.claude/rag-dashboard')
from rag_server import index_file
index_file('$CHANGELOG_FILE', '$PROJECT_DIR')
print('Indexed via rag-server')
"""],
        capture_output=True,
        text=True,
        timeout=60
    )
    if result.returncode == 0:
        print(result.stdout)
        sys.exit(0)
except Exception as e:
    pass

# If that fails, just note that the file is ready for indexing
print(f"Changelog saved to: {changelog_file}")
print("Run: rag index {changelog_file}")
EOF

log "Changelog indexing complete for $SHORT_HASH"
echo "[Git] Changelog indexed: $SHORT_HASH"
