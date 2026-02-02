#!/bin/bash
# Migrate existing projects to hierarchical context architecture
# Usage: migrate-to-hierarchy.sh [--dry-run] [--add-frontmatter] [path]

set -e

CLAUDE_DIR="$HOME/.claude"
CLIENTS_DIR="$HOME/clients"
CONTEXT_DIR="$CLAUDE_DIR/context"
CONTEXT_LIB="$CONTEXT_DIR/lib/context_manager.py"

DRY_RUN=false
ADD_FRONTMATTER=false
TARGET_PATH=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --add-frontmatter)
            ADD_FRONTMATTER=true
            shift
            ;;
        *)
            TARGET_PATH="$1"
            shift
            ;;
    esac
done

echo "=================================="
echo "Hierarchy Migration Tool v1.0"
echo "=================================="
echo ""

if $DRY_RUN; then
    echo "[DRY RUN MODE - No changes will be made]"
    echo ""
fi

# Check prerequisites
echo "Checking prerequisites..."

if [ ! -f "$CONTEXT_LIB" ]; then
    echo "ERROR: Context library not found at $CONTEXT_LIB"
    echo "Please ensure the hierarchical context system is installed."
    exit 1
fi

if ! python3 -c "import yaml" 2>/dev/null; then
    echo "ERROR: PyYAML not installed. Run: pip install pyyaml"
    exit 1
fi

echo "  Context library: OK"
echo "  PyYAML: OK"
echo ""

# Ensure clients directory exists
if [ ! -d "$CLIENTS_DIR" ]; then
    if $DRY_RUN; then
        echo "[DRY RUN] Would create: $CLIENTS_DIR"
    else
        echo "Creating clients directory: $CLIENTS_DIR"
        mkdir -p "$CLIENTS_DIR"
    fi
fi

# If a specific path is provided, migrate that project
if [ -n "$TARGET_PATH" ]; then
    if [ ! -d "$TARGET_PATH" ]; then
        echo "ERROR: Path does not exist: $TARGET_PATH"
        exit 1
    fi

    echo "Migrating single project: $TARGET_PATH"

    # Check if already under clients/
    if [[ "$TARGET_PATH" == "$CLIENTS_DIR"* ]]; then
        echo "  Project is already under ~/clients/"
    else
        PROJECT_NAME=$(basename "$TARGET_PATH")
        echo "  Project name: $PROJECT_NAME"

        # Determine client name (parent directory or project name)
        read -p "  Enter client name (default: $PROJECT_NAME): " CLIENT_NAME
        CLIENT_NAME="${CLIENT_NAME:-$PROJECT_NAME}"

        NEW_PATH="$CLIENTS_DIR/$CLIENT_NAME"

        if $DRY_RUN; then
            echo "[DRY RUN] Would move $TARGET_PATH to $NEW_PATH"
        else
            if [ -d "$NEW_PATH" ]; then
                echo "  WARNING: $NEW_PATH already exists"
                read -p "  Merge into existing? (y/n): " MERGE
                if [ "$MERGE" != "y" ]; then
                    echo "  Skipping..."
                    exit 0
                fi
            fi

            echo "  Moving to: $NEW_PATH"
            mkdir -p "$NEW_PATH"
            cp -r "$TARGET_PATH"/* "$NEW_PATH/" 2>/dev/null || true
            echo "  Moved successfully."
            echo ""
            echo "  NOTE: Original files remain at $TARGET_PATH"
            echo "  Delete manually after verifying migration."
        fi
    fi
else
    echo "Scanning for CLAUDE.md files under $CLIENTS_DIR..."
    echo ""
fi

# Add front-matter to CLAUDE.md files if requested
if $ADD_FRONTMATTER; then
    echo "Adding front-matter to CLAUDE.md files..."

    find "$CLIENTS_DIR" -name "CLAUDE.md" -type f 2>/dev/null | while read -r claude_md; do
        # Check if already has front-matter
        if head -1 "$claude_md" | grep -q "^---"; then
            echo "  [SKIP] Already has front-matter: $claude_md"
            continue
        fi

        # Extract path info
        rel_path="${claude_md#$CLIENTS_DIR/}"
        dir_path=$(dirname "$rel_path")
        depth=$(echo "$dir_path" | tr '/' '\n' | wc -l | tr -d ' ')

        # Determine type
        if [ "$depth" -eq 1 ]; then
            NODE_TYPE="client"
        elif [ "$depth" -eq 2 ]; then
            NODE_TYPE="project"
        elif [ "$depth" -eq 3 ]; then
            NODE_TYPE="sub_project"
        else
            NODE_TYPE="milestone"
        fi

        # Get node name
        NODE_NAME=$(basename "$dir_path")

        # Create front-matter
        FRONTMATTER="---
type: $NODE_TYPE
id: $dir_path
tags: [$NODE_NAME]
---

"

        if $DRY_RUN; then
            echo "[DRY RUN] Would add front-matter to: $claude_md"
            echo "  Type: $NODE_TYPE, ID: $dir_path"
        else
            echo "  Adding front-matter to: $claude_md"

            # Create temp file with front-matter + original content
            TEMP_FILE=$(mktemp)
            echo "$FRONTMATTER" > "$TEMP_FILE"
            cat "$claude_md" >> "$TEMP_FILE"
            mv "$TEMP_FILE" "$claude_md"
        fi
    done

    echo ""
fi

# Rebuild context index
echo "Rebuilding context index..."

if $DRY_RUN; then
    echo "[DRY RUN] Would run: python3 $CONTEXT_LIB discover"
else
    python3 "$CONTEXT_LIB" discover
fi

echo ""

# Summary
echo "=================================="
echo "Migration Summary"
echo "=================================="

if [ -f "$CONTEXT_DIR/index.json" ]; then
    NODE_COUNT=$(python3 -c "import json; print(len(json.loads(open('$CONTEXT_DIR/index.json').read()).get('nodes', [])))")
    echo "Nodes indexed: $NODE_COUNT"
else
    echo "Nodes indexed: 0 (index not created)"
fi

echo ""
echo "Next steps:"
echo "  1. Review CLAUDE.md files and add router_summary fields"
echo "  2. Run 'context tree' to view the hierarchy"
echo "  3. Initialize RAG for clients: rag init ~/clients/<client>"
echo "  4. Restart Claude Code to pick up hierarchy changes"
echo ""
echo "Documentation: ~/.claude/docs/adr/2026-01-17-hierarchical-context-architecture.md"
