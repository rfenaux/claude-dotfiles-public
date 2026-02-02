#!/bin/bash
# Install Git Hooks for Claude Integration
# Sets up post-commit hooks for RAG reindexing in all git-enabled projects
#
# Usage: install-git-hooks.sh [project-path] [--all]
#
# Options:
#   --all       Install in all known projects
#   [path]      Install in specific project
#   (none)      Install in current directory

set -e

HOOK_SOURCE="$HOME/.claude/hooks/git-post-commit-rag.sh"
AGENT_HOOK="$HOME/.claude/hooks/agent-complete.sh"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_success() { echo -e "${GREEN}✓${NC} $1"; }
log_warn() { echo -e "${YELLOW}⚠${NC} $1"; }
log_error() { echo -e "${RED}✗${NC} $1"; }

install_hook() {
    local project_dir="$1"
    local project_name=$(basename "$project_dir")

    if [ ! -d "$project_dir/.git" ]; then
        log_warn "$project_name: Not a git repository"
        return 1
    fi

    local hooks_dir="$project_dir/.git/hooks"
    local post_commit="$hooks_dir/post-commit"

    mkdir -p "$hooks_dir"

    # Check if post-commit already has our hook
    if [ -f "$post_commit" ] && grep -q "git-post-commit-rag.sh" "$post_commit" 2>/dev/null; then
        log_warn "$project_name: Hook already installed"
        return 0
    fi

    # Create or append to post-commit
    if [ -f "$post_commit" ]; then
        # Append to existing hook
        echo "" >> "$post_commit"
        echo "# Claude RAG Integration" >> "$post_commit"
        echo "if [ -x \"$HOOK_SOURCE\" ]; then" >> "$post_commit"
        echo "    \"$HOOK_SOURCE\"" >> "$post_commit"
        echo "fi" >> "$post_commit"
        log_success "$project_name: Hook appended to existing post-commit"
    else
        # Create new hook
        cat > "$post_commit" << EOF
#!/bin/bash
# Git post-commit hook with Claude integrations

# Claude RAG Integration - reindex changed files
if [ -x "$HOOK_SOURCE" ]; then
    "$HOOK_SOURCE"
fi
EOF
        chmod +x "$post_commit"
        log_success "$project_name: Hook installed"
    fi

    return 0
}

# Known project directories
KNOWN_PROJECTS=(
    "$HOME/Documents/Projects/rescue"
    "$HOME/Documents/Projects - Private/faas"
    "$HOME/Documents/Projects - Pro/<COMPANY>/solarc-agent"
    "$HOME/Documents/Projects - Pro/<COMPANY>/project-template"
    "$HOME/Documents/Projects - Pro/<COMPANY>/Spadel-Claude"
    "$HOME/Documents/Projects - Pro/<COMPANY>/<PROJECT>-Claude"
    "$HOME/Documents/Projects - Pro/<COMPANY>/Factoria-Claude"
    "$HOME/Documents/Projects - Pro/<COMPANY>/Forsee-Power-Claude"
    "$HOME/Documents/Projects - Pro/<COMPANY>/Rescue-Claude"
    "$HOME/Documents/Projects - Pro/<COMPANY>/Celini-Claude"
    "$HOME/Documents/Projects - Pro/<COMPANY>/ISMS-Claude"
    "$HOME/Documents/Projects - Pro/<COMPANY>/Personio-Claude"
    "$HOME/Documents/Projects - Pro/<COMPANY>/Assessment-Prospect-Claude"
    "$HOME/Documents/Projects - Pro/<COMPANY>/Functional-Specs-Claude"
    "$HOME/Documents/Projects - Pro/<COMPANY>/Nexant-Prospect-Claude"
    "$HOME/Documents/Projects - Pro/<COMPANY>/Forvia-Claude"
    "$HOME/Documents/Projects - Pro/<COMPANY>/Omron-Claude"
    "$HOME/Documents/Projects - Pro/<COMPANY>/Nexant-Claude"
    "$HOME/Documents/Projects - Pro/<COMPANY>/Lucid-Chart-Claude"
    "$HOME/.claude"
)

if [ "$1" == "--all" ]; then
    echo "Installing git hooks in all known projects..."
    echo ""
    installed=0
    skipped=0

    for project in "${KNOWN_PROJECTS[@]}"; do
        if [ -d "$project" ]; then
            if install_hook "$project"; then
                ((installed++))
            else
                ((skipped++))
            fi
        fi
    done

    echo ""
    echo "Summary: $installed installed, $skipped skipped"

elif [ -n "$1" ] && [ -d "$1" ]; then
    install_hook "$1"

else
    # Current directory
    install_hook "$(pwd)"
fi

echo ""
echo "Integration hooks:"
echo "  • CTM checkpoint → git auto-commit (via pre-compact hook)"
echo "  • Git commit → RAG reindex (via post-commit hook)"
echo "  • Agent complete → commit OUTPUT.md (manual: call $AGENT_HOOK)"
