#!/bin/bash
# Batch migrate all Claude projects to Temporal RAG + Context Management
# Usage: migrate-all-projects.sh [--reindex] [--dry-run]

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_DIR="$HOME/.claude/scripts"
REINDEX=""
DRY_RUN=false

# Parse arguments
for arg in "$@"; do
    case $arg in
        --reindex)
            REINDEX="--reindex"
            ;;
        --dry-run)
            DRY_RUN=true
            ;;
    esac
done

# Find all Claude projects (directories with .claude or .rag folder)
echo -e "${BOLD}${BLUE}=== Discovering Claude Projects ===${NC}"
echo ""

PROJECTS=()

# Search locations
SEARCH_PATHS=(
    "$HOME/Documents/Projects"
    "$HOME/Documents/Projects - Pro"
    "$HOME/Documents/Projects - Private"
    "$HOME/Documents/Docs - Privé"
)

for search_path in "${SEARCH_PATHS[@]}"; do
    if [ -d "$search_path" ]; then
        # Find projects with .rag or .claude folders
        while IFS= read -r project; do
            if [ -n "$project" ]; then
                # Get the parent directory (the project root)
                project_root=$(dirname "$project")
                # Avoid duplicates
                if [[ ! " ${PROJECTS[*]} " =~ " ${project_root} " ]]; then
                    PROJECTS+=("$project_root")
                fi
            fi
        done < <(find "$search_path" -maxdepth 3 -type d \( -name ".rag" -o -name ".claude" \) 2>/dev/null)
    fi
done

# Sort and deduplicate
IFS=$'\n' PROJECTS=($(sort -u <<<"${PROJECTS[*]}")); unset IFS

echo -e "Found ${GREEN}${#PROJECTS[@]}${NC} projects to check:"
echo ""

# Display projects
for project in "${PROJECTS[@]}"; do
    name=$(basename "$project")
    has_rag="○"
    has_context="○"

    [ -d "$project/.rag" ] && has_rag="${GREEN}✓${NC}"
    [ -d "$project/.claude/context" ] && has_context="${GREEN}✓${NC}"

    printf "  %-40s RAG: %b  Context: %b\n" "$name" "$has_rag" "$has_context"
done

echo ""

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}Dry run mode - no changes will be made${NC}"
    exit 0
fi

# Confirm
echo -e "${BOLD}Ready to migrate all projects?${NC}"
echo "This will:"
echo "  • Create .claude/context/ with DECISIONS.md, SESSIONS.md, etc."
[ -n "$REINDEX" ] && echo "  • Reindex RAG databases for temporal features"
echo ""
read -p "Continue? [y/N] " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

# Migrate each project
echo ""
echo -e "${BOLD}${BLUE}=== Running Migrations ===${NC}"

SUCCESS=0
FAILED=0

for project in "${PROJECTS[@]}"; do
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    if "$SCRIPT_DIR/migrate-to-temporal-rag.sh" "$project" $REINDEX; then
        ((SUCCESS++))
    else
        ((FAILED++))
        echo -e "${RED}Failed to migrate: $project${NC}"
    fi
done

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BOLD}${BLUE}=== Final Summary ===${NC}"
echo -e "  ${GREEN}✓ Successful:${NC} $SUCCESS"
[ $FAILED -gt 0 ] && echo -e "  ${RED}✗ Failed:${NC} $FAILED"
echo ""
echo -e "${BLUE}All projects now have context management.${NC}"
echo "Remember to customize STAKEHOLDERS.md and DECISIONS.md for each project."
