#!/bin/bash
# Migrate project to Temporal RAG + Context Management System
# Usage: migrate-to-temporal-rag.sh /path/to/project [--reindex]

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

TEMPLATE_DIR="$HOME/.claude/templates/context-structure"
REINDEX=false

# Parse arguments
PROJECT_PATH=""
for arg in "$@"; do
    case $arg in
        --reindex)
            REINDEX=true
            ;;
        *)
            if [ -z "$PROJECT_PATH" ]; then
                PROJECT_PATH="$arg"
            fi
            ;;
    esac
done

if [ -z "$PROJECT_PATH" ]; then
    echo -e "${RED}Error: Project path required${NC}"
    echo "Usage: $0 /path/to/project [--reindex]"
    exit 1
fi

# Resolve to absolute path
PROJECT_PATH=$(cd "$PROJECT_PATH" 2>/dev/null && pwd)

if [ ! -d "$PROJECT_PATH" ]; then
    echo -e "${RED}Error: Directory does not exist: $PROJECT_PATH${NC}"
    exit 1
fi

PROJECT_NAME=$(basename "$PROJECT_PATH")
echo -e "${BLUE}=== Migrating: ${PROJECT_NAME} ===${NC}"
echo "Path: $PROJECT_PATH"
echo ""

# Track what we did
CHANGES=()

# 1. Create .claude directory if needed
if [ ! -d "$PROJECT_PATH/.claude" ]; then
    mkdir -p "$PROJECT_PATH/.claude"
    CHANGES+=("Created .claude/ directory")
fi

# 2. Create context directory structure
CONTEXT_DIR="$PROJECT_PATH/.claude/context"
if [ ! -d "$CONTEXT_DIR" ]; then
    mkdir -p "$CONTEXT_DIR"
    CHANGES+=("Created .claude/context/ directory")
fi

# 3. Copy template files (only if they don't exist)
copy_if_missing() {
    local filename="$1"
    local src="$TEMPLATE_DIR/$filename"
    local dst="$CONTEXT_DIR/$filename"

    if [ ! -f "$dst" ]; then
        if [ -f "$src" ]; then
            cp "$src" "$dst"
            # Update dates to today
            TODAY=$(date '+%Y-%m-%d')
            sed -i '' "s/2026-01-07/$TODAY/g" "$dst" 2>/dev/null || true
            CHANGES+=("Created $filename")
            echo -e "  ${GREEN}✓${NC} Created $filename"
        else
            echo -e "  ${YELLOW}⚠${NC} Template missing: $filename"
        fi
    else
        echo -e "  ${YELLOW}○${NC} Skipped $filename (already exists)"
    fi
}

echo -e "${BLUE}Context files:${NC}"
copy_if_missing "DECISIONS.md"
copy_if_missing "SESSIONS.md"
copy_if_missing "CHANGELOG.md"
copy_if_missing "STAKEHOLDERS.md"

# Don't copy README.md to context folder (it's for the template)

# 4. Check/Initialize RAG
echo ""
echo -e "${BLUE}RAG System:${NC}"

if [ ! -d "$PROJECT_PATH/.rag" ]; then
    echo -e "  ${YELLOW}○${NC} No .rag/ folder - RAG not initialized"
    echo -e "  ${YELLOW}  Run: cd $PROJECT_PATH && rag init${NC}"
else
    echo -e "  ${GREEN}✓${NC} RAG already initialized"

    if [ "$REINDEX" = true ]; then
        echo -e "  ${BLUE}↻${NC} Reindexing for temporal capabilities..."
        # Use the rag CLI if available, otherwise show command
        if command -v rag &> /dev/null; then
            cd "$PROJECT_PATH" && rag reindex
            CHANGES+=("Reindexed RAG database")
        else
            echo -e "  ${YELLOW}  Run manually: cd $PROJECT_PATH && rag reindex${NC}"
        fi
    else
        echo -e "  ${YELLOW}  Tip: Run with --reindex to update RAG with temporal features${NC}"
    fi
fi

# 5. Summary
echo ""
echo -e "${BLUE}=== Migration Summary ===${NC}"

if [ ${#CHANGES[@]} -eq 0 ]; then
    echo -e "${GREEN}Project already up to date!${NC}"
else
    echo -e "${GREEN}Changes made:${NC}"
    for change in "${CHANGES[@]}"; do
        echo "  • $change"
    done
fi

echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Edit STAKEHOLDERS.md with actual team members"
echo "  2. Review DECISIONS.md and add any existing decisions"
echo "  3. Run 'rag reindex' if you haven't already"
echo "  4. Add memory section to project's CLAUDE.md (if exists)"
