#!/bin/bash
# Multi-Account Claude Code Setup
# Creates isolated config directories with symlinked shared components
#
# Usage: setup-multi-account.sh <account-name>
# Example: setup-multi-account.sh fow
#
# This creates ~/.claude-<account-name> with:
# - Symlinks to shared components (agents, skills, hooks, etc.)
# - Isolated auth/session data
# - Proper git tracking

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRIMARY_CONFIG="$HOME/.claude"
ACCOUNT_NAME="${1:-}"

if [[ -z "$ACCOUNT_NAME" ]]; then
    echo "Usage: $0 <account-name>"
    echo "Example: $0 fow"
    exit 1
fi

TARGET_DIR="$HOME/.claude-${ACCOUNT_NAME}"

echo "=== Claude Code Multi-Account Setup ==="
echo "Primary config: $PRIMARY_CONFIG"
echo "New account:    $TARGET_DIR"
echo ""

# Check if target exists
if [[ -d "$TARGET_DIR" ]]; then
    echo "⚠️  Directory $TARGET_DIR already exists"
    read -p "Overwrite? (y/N): " confirm
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        echo "Aborted."
        exit 1
    fi
    rm -rf "$TARGET_DIR"
fi

mkdir -p "$TARGET_DIR"

# =============================================================================
# SHARED COMPONENTS (symlinked)
# Everything is shared EXCEPT Anthropic account credentials
# =============================================================================
SHARED_ITEMS=(
    # Core tooling
    "agents"
    "skills"
    "hooks"
    "scripts"
    "lib"
    "mcp-servers"
    "templates"
    "commands"
    "plugins"

    # Documentation
    "docs"
    "CLAUDE.md"
    "CLAUDE.md.full"
    "CLAUDE.md.slim"
    "CONFIGURATION_GUIDE.md"
    "AGENTS_INDEX.md"
    "SKILLS_INDEX.md"
    "CTM_GUIDE.md"
    "RAG_GUIDE.md"
    "CDP_PROTOCOL.md"
    "RESOURCE_MANAGEMENT.md"
    "PROJECT_MEMORY_GUIDE.md"
    "LESSONS_GUIDE.md"
    "BINARY_FILE_REFERENCE.md"
    "HUBSPOT_IMPLEMENTATION_GUIDE.md"
    "HIERARCHY_GUIDE.md"
    "AGENT_CONTEXT_PROTOCOL.md"
    "AGENT_STANDARDS.md"
    "ASYNC_ROUTING.md"
    "RAPHAEL_PERSONA.md"
    "DOTFILES_README.md"
    "README.md"

    # Config files (read-only shared)
    "config"
    "coordination-defaults.json"
    "routing-index.json"
    "raphael-patterns.json"
    "inventory.json"
    "machine-profile.json"
    "keybindings.json"
    ".mcp.json"
    ".package-config.json"

    # Shared knowledge
    "memory"
    "lessons"
    "knowledge"
    "examples"
    "brand"
    "research"

    # Utilities
    "statusline.sh"
    "devices"

    # Hidden dirs that are shared
    ".codex"
    ".gemini"
    ".ollama"
    ".hscli"

    # WORK DATA (shared across accounts)
    "clients"
    "ctm"
    "projects"
    "dev-projects"
    "conversation-history"
    "context"
    "history.jsonl"
    "inbox"
    "intent-patterns.json"

    # SESSION DATA (shared - all local anyway)
    "todos"
    "tasks"
    "plans"
    "file-history"
    "backups"
    "downloads"
)

echo "Creating symlinks for shared components..."
for item in "${SHARED_ITEMS[@]}"; do
    if [[ -e "$PRIMARY_CONFIG/$item" ]]; then
        ln -sf "$PRIMARY_CONFIG/$item" "$TARGET_DIR/$item"
        echo "  ✓ $item"
    else
        echo "  - $item (not found, skipping)"
    fi
done

# =============================================================================
# ISOLATED COMPONENTS (created fresh per-account)
# Only session/cache directories - NO work data
# =============================================================================
echo ""
echo "Creating isolated directories (session/cache only)..."

# Minimal isolated directories (auth/cache only)
mkdir -p "$TARGET_DIR/session-env"
mkdir -p "$TARGET_DIR/session-prompts"
mkdir -p "$TARGET_DIR/shell-snapshots"
mkdir -p "$TARGET_DIR/cache"
mkdir -p "$TARGET_DIR/debug"
mkdir -p "$TARGET_DIR/logs"
mkdir -p "$TARGET_DIR/telemetry"
mkdir -p "$TARGET_DIR/statsig"
mkdir -p "$TARGET_DIR/paste-cache"
mkdir -p "$TARGET_DIR/presence"
mkdir -p "$TARGET_DIR/chrome"
mkdir -p "$TARGET_DIR/ide"
mkdir -p "$TARGET_DIR/.rag"
mkdir -p "$TARGET_DIR/.agent-workspaces"

echo "  ✓ Created isolated directories (session/cache)"

# =============================================================================
# SETTINGS (all symlinked - fully shared)
# =============================================================================
echo ""
echo "Setting up settings files..."

# Symlink settings.json (shared config)
if [[ -f "$PRIMARY_CONFIG/settings.json" ]]; then
    ln -sf "$PRIMARY_CONFIG/settings.json" "$TARGET_DIR/settings.json"
    echo "  ✓ settings.json (symlinked)"
fi

# Symlink settings.local.json (permissions + MCP approvals)
if [[ -f "$PRIMARY_CONFIG/settings.local.json" ]]; then
    ln -sf "$PRIMARY_CONFIG/settings.local.json" "$TARGET_DIR/settings.local.json"
    echo "  ✓ settings.local.json (symlinked)"
fi

# =============================================================================
# NOTE: WORK DATA IS SHARED
# clients/, ctm/, projects/, dev-projects/ are symlinked above
# Only Anthropic credentials (.claude.json) are account-specific
# =============================================================================

# =============================================================================
# GIT SETUP (optional - for tracking account-specific changes)
# =============================================================================
echo ""
read -p "Initialize git for account-specific tracking? (y/N): " init_git
if [[ "$init_git" == "y" || "$init_git" == "Y" ]]; then
    cd "$TARGET_DIR"
    git init

    # Create .gitignore for account-specific repo
    cat > .gitignore << 'EOF'
# Auth & sessions (never commit)
.claude.json
*.local.json
history.jsonl
conversation-history/
session-env/
session-prompts/
shell-snapshots/
stats-cache.json
security_warnings_state_*.json

# Caches
cache/
paste-cache/
.rag/
.agent-workspaces/
telemetry/
statsig/

# Large/temp files
*.log
logs/
debug/
downloads/

# Symlinks (tracked in primary)
agents
skills
hooks
scripts
lib
mcp-servers
templates
commands
plugins
docs
config
memory
lessons
knowledge
examples
brand
research
devices
*.md
*.json
!settings.json
!.gitignore
EOF

    git add .gitignore
    git commit -m "Initial account setup for ${ACCOUNT_NAME}"
    echo "  ✓ Git initialized"
fi

# =============================================================================
# SHELL ALIASES
# =============================================================================
echo ""
echo "=== Add to your ~/.zshrc ==="
echo ""
echo "# Claude Code multi-account aliases"
echo "alias claude-${ACCOUNT_NAME}=\"CLAUDE_CONFIG_DIR=$TARGET_DIR claude\""
echo ""
echo "# Or for explicit switching:"
echo "function claude-switch() {"
echo "  local account=\${1:-huble}"
echo "  case \$account in"
echo "    huble|main) export CLAUDE_CONFIG_DIR=$PRIMARY_CONFIG ;;"
echo "    ${ACCOUNT_NAME}) export CLAUDE_CONFIG_DIR=$TARGET_DIR ;;"
echo "    *) echo \"Unknown account: \$account\" && return 1 ;;"
echo "  esac"
echo "  echo \"Switched to \$account (CLAUDE_CONFIG_DIR=\$CLAUDE_CONFIG_DIR)\""
echo "}"
echo ""

# =============================================================================
# SUMMARY
# =============================================================================
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Add the alias to ~/.zshrc: alias claude-${ACCOUNT_NAME}=\"CLAUDE_CONFIG_DIR=$TARGET_DIR claude\""
echo "2. Run 'source ~/.zshrc'"
echo "3. Run 'claude-${ACCOUNT_NAME}' to authenticate with the new account"
echo ""
echo "Shared components (symlinked from $PRIMARY_CONFIG):"
echo "  - agents/, skills/, hooks/, scripts/, lib/, mcp-servers/"
echo "  - templates/, commands/, plugins/, docs/, config/"
echo "  - memory/, lessons/, knowledge/, examples/, brand/"
echo "  - clients/, ctm/, projects/, dev-projects/ (WORK DATA)"
echo "  - All *.md documentation files"
echo ""
echo "Isolated per-account (credentials only):"
echo "  - .claude.json (Anthropic OAuth tokens)"
echo "  - session-env/, cache/, debug/, telemetry/"
