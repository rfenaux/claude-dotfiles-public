#!/bin/bash
# =============================================================================
# Claude Code Configuration Archive Creator
# =============================================================================
# Creates a portable distribution package for complete replication of the
# Claude Code infrastructure (RAG, CTM, CDP, agents, skills, hooks, etc.)
#
# This script uses dynamic discovery based on .package-config.json to handle
# evolving configuration structures automatically.
#
# Usage: ./create-archive.sh [OPTIONS]
#
# Options:
#   --output-dir DIR          Output directory (default: ~/Desktop)
#   --validate-config         Only validate config, don't create archive
#   --report-structure        Generate structure report
#   --no-codex                Skip Codex directory
#   --verbose                 Show discovery details
#   --help                    Show this help message
#
# Output: claude-code-config-YYYYMMDD.tar.gz (~20MB)
# =============================================================================

set -euo pipefail

# Configuration
VERSION="2.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
CODEX_DIR="$HOME/.codex"
PACKAGE_CONFIG="$CLAUDE_DIR/.package-config.json"
OUTPUT_DIR="$HOME/Desktop"
DATE_STAMP=$(date +%Y%m%d)
ARCHIVE_NAME="claude-code-config-${DATE_STAMP}.tar.gz"

# Options
VALIDATE_CONFIG_ONLY=false
REPORT_STRUCTURE=false
INCLUDE_CODEX=true
VERBOSE=false

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --validate-config)
            VALIDATE_CONFIG_ONLY=true
            shift
            ;;
        --report-structure)
            REPORT_STRUCTURE=true
            shift
            ;;
        --no-codex)
            INCLUDE_CODEX=false
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << 'HELPEOF'
Usage: $0 [OPTIONS]

Creates a portable Claude Code configuration archive using dynamic discovery.

Options:
  --output-dir DIR          Output directory (default: ~/Desktop)
  --validate-config         Only validate config, don't create archive
  --report-structure        Generate structure report to report.json
  --no-codex                Skip Codex directory
  --verbose                 Show discovery details
  --help                    Show this help message

Examples:
  ./create-archive.sh
  ./create-archive.sh --output-dir /tmp
  ./create-archive.sh --validate-config --verbose
  ./create-archive.sh --report-structure
HELPEOF
            exit 0
            ;;
        *)
            shift
            ;;
    esac
done

print_header() {
    echo ""
    echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${BLUE}  $1${NC}"
    echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
}

print_section() {
    echo ""
    echo -e "${BOLD}▶ $1${NC}"
}

success() { echo -e "  ${GREEN}✓${NC} $1"; }
warn() { echo -e "  ${YELLOW}⚠${NC} $1"; }
error() { echo -e "  ${RED}✗${NC} $1"; }
info() { echo -e "  ${BLUE}ℹ${NC} $1"; }

# =============================================================================
# DYNAMIC DISCOVERY FUNCTIONS
# =============================================================================

load_package_config() {
    if [[ ! -f "$PACKAGE_CONFIG" ]]; then
        error "Package config not found: $PACKAGE_CONFIG"
        return 1
    fi

    if ! command -v jq &> /dev/null; then
        warn "jq not installed - skipping advanced config validation"
        return 0
    fi

    if ! jq empty "$PACKAGE_CONFIG" 2>/dev/null; then
        error "Invalid JSON in package config"
        return 1
    fi

    return 0
}

discover_directories() {
    print_section "Discovering Claude infrastructure components"

    if ! load_package_config; then
        warn "Using fallback discovery (no config validation)"
    fi

    local discovered=()
    local unknown=()

    for dir in "$CLAUDE_DIR"/*; do
        if [[ -d "$dir" ]]; then
            local basename="$(basename "$dir")"

            if command -v jq &> /dev/null; then
                local rule_exists=$(jq ".directory_rules[] | select(.path == \"$basename\") | .include" "$PACKAGE_CONFIG" 2>/dev/null | grep -c "true" || true)

                if [[ $rule_exists -gt 0 ]]; then
                    discovered+=("$basename")
                    [[ "$VERBOSE" == true ]] && info "Discovered (configured): $basename"
                else
                    unknown+=("$basename")
                    [[ "$VERBOSE" == true ]] && warn "Found (not in config): $basename"
                fi
            else
                discovered+=("$basename")
            fi
        fi
    done

    if [[ ${#unknown[@]} -gt 0 ]]; then
        warn "Found ${#unknown[@]} component(s) not in package config:"
        for item in "${unknown[@]}"; do
            echo "    - $item"
        done
        info "Consider adding to .package-config.json if these should be packaged"
    fi

    info "Discovered ${#discovered[@]} configured components"
}

generate_structure_report() {
    local report_file="$1"
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)

    cat > "$report_file" << EOF
{
  "report_version": "1.0",
  "generated": "$timestamp",
  "configuration": {
    "claude_dir": "$CLAUDE_DIR",
    "exists": $([ -d "$CLAUDE_DIR" ] && echo "true" || echo "false"),
    "package_config_exists": $([ -f "$PACKAGE_CONFIG" ] && echo "true" || echo "false")
  },
  "discovered_items": {
    "directories": [
$(ls -1 "$CLAUDE_DIR" 2>/dev/null | while read dir; do
    if [ -d "$CLAUDE_DIR/$dir" ] && [[ "$dir" != "."* ]]; then
        echo "      \"$dir\","
    fi
done | sed '$ s/,$//')
    ]
  }
}
EOF

    success "Structure report generated: $report_file"
}

validate_package_config() {
    print_header "Validating Package Configuration"

    if [[ ! -f "$PACKAGE_CONFIG" ]]; then
        error "Package config not found: $PACKAGE_CONFIG"
        return 1
    fi

    if ! command -v jq &> /dev/null; then
        warn "jq not installed - skipping detailed validation"
        return 0
    fi

    local config_version=$(jq -r '.version' "$PACKAGE_CONFIG")
    info "Config version: $config_version"

    # Perform discovery (create temp staging just for this)
    print_section "Discovering Claude infrastructure components"

    local discovered=()
    local unknown=()

    for dir in "$CLAUDE_DIR"/*; do
        if [[ -d "$dir" ]]; then
            local basename="$(basename "$dir")"

            local rule_exists=$(jq ".directory_rules[] | select(.path == \"$basename\") | .include" "$PACKAGE_CONFIG" 2>/dev/null | grep -c "true" || true)

            if [[ $rule_exists -gt 0 ]]; then
                discovered+=("$basename")
                [[ "$VERBOSE" == true ]] && info "Discovered (configured): $basename"
            else
                unknown+=("$basename")
                [[ "$VERBOSE" == true ]] && warn "Found (not in config): $basename"
            fi
        fi
    done

    if [[ ${#unknown[@]} -gt 0 ]]; then
        warn "Found ${#unknown[@]} component(s) not in package config:"
        for item in "${unknown[@]}"; do
            echo "    - $item"
        done
        info "Consider adding to .package-config.json if these should be packaged"
    fi

    info "Discovered ${#discovered[@]} configured components"
    success "Configuration validation complete"
    return 0
}

# =============================================================================
# MAIN
# =============================================================================

print_header "Claude Code Configuration Archive Creator v${VERSION}"
echo "  Source: $CLAUDE_DIR"
echo "  Config: $PACKAGE_CONFIG"
echo "  Output: $OUTPUT_DIR/$ARCHIVE_NAME"
echo "  Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Handle validation-only mode
if [[ "$VALIDATE_CONFIG_ONLY" == true ]]; then
    echo ""
    validate_package_config
    exit $?
fi

# Handle report-only mode
if [[ "$REPORT_STRUCTURE" == true ]]; then
    echo ""
    generate_structure_report "$OUTPUT_DIR/package-structure-report.json"
    exit $?
fi

# Create staging directory
STAGING_DIR=$(mktemp -d)
trap "rm -rf $STAGING_DIR" EXIT

print_section "Pre-flight checks"

# Check source directories exist
if [[ ! -d "$CLAUDE_DIR" ]]; then
    error "Claude directory not found: $CLAUDE_DIR"
    exit 1
fi
success "Claude directory found"

# Check package config
if [[ ! -f "$PACKAGE_CONFIG" ]]; then
    warn "Package config not found: $PACKAGE_CONFIG"
    warn "Using legacy fallback mode (no dynamic discovery)"
else
    success "Package config found (v$(jq -r '.version // "unknown"' "$PACKAGE_CONFIG" 2>/dev/null || echo "unknown"))"
fi

if [[ "$INCLUDE_CODEX" == false ]]; then
    info "Codex directory will be skipped (--no-codex)"
elif [[ ! -d "$CODEX_DIR" ]]; then
    warn "Codex directory not found: $CODEX_DIR (will skip)"
    INCLUDE_CODEX=false
else
    success "Codex directory found"
    INCLUDE_CODEX=true
fi

# Check for required tools
if ! command -v jq &> /dev/null; then
    warn "jq not installed - using simplified discovery"
fi

# Run discovery
discover_directories "$STAGING_DIR"

# =============================================================================
# STAGE ~/.claude/
# =============================================================================

print_section "Staging ~/.claude/ directory"

mkdir -p "$STAGING_DIR/dot-claude"

# Copy agents (80 agents)
if [[ -d "$CLAUDE_DIR/agents" ]]; then
    cp -R "$CLAUDE_DIR/agents" "$STAGING_DIR/dot-claude/"
    AGENT_COUNT=$(ls "$STAGING_DIR/dot-claude/agents/"*.md 2>/dev/null | wc -l | tr -d ' ')
    success "Copied agents: $AGENT_COUNT agents"
fi

# Copy skills (11 skills)
if [[ -d "$CLAUDE_DIR/skills" ]]; then
    cp -R "$CLAUDE_DIR/skills" "$STAGING_DIR/dot-claude/"
    SKILL_COUNT=$(ls -d "$STAGING_DIR/dot-claude/skills/"*/ 2>/dev/null | wc -l | tr -d ' ')
    success "Copied skills: $SKILL_COUNT skills"
fi

# Copy hooks
if [[ -d "$CLAUDE_DIR/hooks" ]]; then
    cp -R "$CLAUDE_DIR/hooks" "$STAGING_DIR/dot-claude/"
    HOOK_COUNT=$(find "$STAGING_DIR/dot-claude/hooks" -name "*.sh" -o -name "*.py" 2>/dev/null | wc -l | tr -d ' ')
    success "Copied hooks: $HOOK_COUNT files"
fi

# Copy scripts (excluding create-archive.sh itself if running from there)
if [[ -d "$CLAUDE_DIR/scripts" ]]; then
    cp -R "$CLAUDE_DIR/scripts" "$STAGING_DIR/dot-claude/"
    success "Copied scripts"
fi

# Copy CTM (excluding runtime state)
if [[ -d "$CLAUDE_DIR/ctm" ]]; then
    mkdir -p "$STAGING_DIR/dot-claude/ctm"
    # Copy lib (Python code)
    [[ -d "$CLAUDE_DIR/ctm/lib" ]] && cp -R "$CLAUDE_DIR/ctm/lib" "$STAGING_DIR/dot-claude/ctm/"
    # Copy scripts
    [[ -d "$CLAUDE_DIR/ctm/scripts" ]] && cp -R "$CLAUDE_DIR/ctm/scripts" "$STAGING_DIR/dot-claude/ctm/"
    # Copy config files
    [[ -f "$CLAUDE_DIR/ctm/config.json" ]] && cp "$CLAUDE_DIR/ctm/config.json" "$STAGING_DIR/dot-claude/ctm/"
    [[ -f "$CLAUDE_DIR/ctm/MIGRATION.md" ]] && cp "$CLAUDE_DIR/ctm/MIGRATION.md" "$STAGING_DIR/dot-claude/ctm/"
    # Create empty directories for runtime
    mkdir -p "$STAGING_DIR/dot-claude/ctm/agents"
    mkdir -p "$STAGING_DIR/dot-claude/ctm/backups"
    mkdir -p "$STAGING_DIR/dot-claude/ctm/checkpoints"
    mkdir -p "$STAGING_DIR/dot-claude/ctm/context"
    mkdir -p "$STAGING_DIR/dot-claude/ctm/logs"
    mkdir -p "$STAGING_DIR/dot-claude/ctm/metrics"
    # Create empty index.json
    echo '{"tasks": [], "version": "1.0"}' > "$STAGING_DIR/dot-claude/ctm/index.json"
    echo '{"scheduled": []}' > "$STAGING_DIR/dot-claude/ctm/scheduler.json"
    success "Copied CTM (code only, fresh state)"
fi

# Copy RAG dashboard (code only, no logs or conversation dumps)
if [[ -d "$CLAUDE_DIR/rag-dashboard" ]]; then
    mkdir -p "$STAGING_DIR/dot-claude/rag-dashboard"
    # Copy Python files
    cp "$CLAUDE_DIR/rag-dashboard"/*.py "$STAGING_DIR/dot-claude/rag-dashboard/" 2>/dev/null || true
    # Copy HTML/CSS/JS
    cp "$CLAUDE_DIR/rag-dashboard"/*.html "$STAGING_DIR/dot-claude/rag-dashboard/" 2>/dev/null || true
    cp "$CLAUDE_DIR/rag-dashboard"/*.css "$STAGING_DIR/dot-claude/rag-dashboard/" 2>/dev/null || true
    cp "$CLAUDE_DIR/rag-dashboard"/*.js "$STAGING_DIR/dot-claude/rag-dashboard/" 2>/dev/null || true
    # Copy shell scripts
    cp "$CLAUDE_DIR/rag-dashboard"/*.sh "$STAGING_DIR/dot-claude/rag-dashboard/" 2>/dev/null || true
    # Copy docs
    cp "$CLAUDE_DIR/rag-dashboard"/*.md "$STAGING_DIR/dot-claude/rag-dashboard/" 2>/dev/null || true
    success "Copied RAG dashboard (code only)"
fi

# Copy MCP servers (code only, no venvs)
if [[ -d "$CLAUDE_DIR/mcp-servers" ]]; then
    mkdir -p "$STAGING_DIR/dot-claude/mcp-servers"

    # RAG server
    if [[ -d "$CLAUDE_DIR/mcp-servers/rag-server" ]]; then
        mkdir -p "$STAGING_DIR/dot-claude/mcp-servers/rag-server"
        [[ -d "$CLAUDE_DIR/mcp-servers/rag-server/src" ]] && \
            cp -R "$CLAUDE_DIR/mcp-servers/rag-server/src" "$STAGING_DIR/dot-claude/mcp-servers/rag-server/"
        [[ -f "$CLAUDE_DIR/mcp-servers/rag-server/pyproject.toml" ]] && \
            cp "$CLAUDE_DIR/mcp-servers/rag-server/pyproject.toml" "$STAGING_DIR/dot-claude/mcp-servers/rag-server/"
        [[ -f "$CLAUDE_DIR/mcp-servers/rag-server/README.md" ]] && \
            cp "$CLAUDE_DIR/mcp-servers/rag-server/README.md" "$STAGING_DIR/dot-claude/mcp-servers/rag-server/"
        success "Copied RAG MCP server (code only)"
    fi

    # Fathom server
    if [[ -d "$CLAUDE_DIR/mcp-servers/fathom" ]]; then
        mkdir -p "$STAGING_DIR/dot-claude/mcp-servers/fathom"
        [[ -f "$CLAUDE_DIR/mcp-servers/fathom/server.py" ]] && \
            cp "$CLAUDE_DIR/mcp-servers/fathom/server.py" "$STAGING_DIR/dot-claude/mcp-servers/fathom/"
        [[ -f "$CLAUDE_DIR/mcp-servers/fathom/README.md" ]] && \
            cp "$CLAUDE_DIR/mcp-servers/fathom/README.md" "$STAGING_DIR/dot-claude/mcp-servers/fathom/"
        success "Copied Fathom MCP server (code only)"
    fi
fi

# Copy templates
if [[ -d "$CLAUDE_DIR/templates" ]]; then
    cp -R "$CLAUDE_DIR/templates" "$STAGING_DIR/dot-claude/"
    success "Copied templates"
fi

# Copy plugins config (not cache)
if [[ -d "$CLAUDE_DIR/plugins" ]]; then
    mkdir -p "$STAGING_DIR/dot-claude/plugins"
    [[ -f "$CLAUDE_DIR/plugins/installed_plugins.json" ]] && \
        cp "$CLAUDE_DIR/plugins/installed_plugins.json" "$STAGING_DIR/dot-claude/plugins/"
    [[ -f "$CLAUDE_DIR/plugins/known_marketplaces.json" ]] && \
        cp "$CLAUDE_DIR/plugins/known_marketplaces.json" "$STAGING_DIR/dot-claude/plugins/"
    success "Copied plugins config (no cache)"
fi

# Copy brand directory structure
if [[ -d "$CLAUDE_DIR/brand" ]]; then
    mkdir -p "$STAGING_DIR/dot-claude/brand"
    [[ -f "$CLAUDE_DIR/brand/README.md" ]] && \
        cp "$CLAUDE_DIR/brand/README.md" "$STAGING_DIR/dot-claude/brand/"
    success "Copied brand structure"
fi

# Create empty lessons structure
mkdir -p "$STAGING_DIR/dot-claude/lessons/review"
mkdir -p "$STAGING_DIR/dot-claude/lessons/pending"
mkdir -p "$STAGING_DIR/dot-claude/lessons/archive"
touch "$STAGING_DIR/dot-claude/lessons/.gitkeep"
success "Created empty lessons structure"

# Copy documentation files
DOCS=(
    "CLAUDE.md"
    "CLAUDE_TRIMMED.md"
    "AGENTS_INDEX.md"
    "SKILLS_INDEX.md"
    "AGENT_STANDARDS.md"
    "AGENT_CONTEXT_PROTOCOL.md"
    "CDP_PROTOCOL.md"
    "CTM_GUIDE.md"
    "RAG_GUIDE.md"
    "CONFIGURATION_GUIDE.md"
    "BINARY_FILE_REFERENCE.md"
    "PERSONA.md"
    "COMPLETE_REPLICATION_GUIDE.md"
    "HUBSPOT_IMPLEMENTATION_GUIDE.md"
    "DECISIONS.md"
    "inventory.json"
    "statusline.sh"
    "rag-projects.json"
)

DOC_COUNT=0
for doc in "${DOCS[@]}"; do
    if [[ -f "$CLAUDE_DIR/$doc" ]]; then
        cp "$CLAUDE_DIR/$doc" "$STAGING_DIR/dot-claude/"
        ((DOC_COUNT++))
    fi
done
success "Copied $DOC_COUNT documentation files"

# Create settings templates (with path substitution)
print_section "Creating templated configuration files"

# settings.json template
if [[ -f "$CLAUDE_DIR/settings.json" ]]; then
    sed "s|${HOME}|{{HOME}}|g" "$CLAUDE_DIR/settings.json" > \
        "$STAGING_DIR/dot-claude/settings.json.template"
    success "Created settings.json.template"
fi

# settings.local.json template
if [[ -f "$CLAUDE_DIR/settings.local.json" ]]; then
    sed "s|${HOME}|{{HOME}}|g" "$CLAUDE_DIR/settings.local.json" > \
        "$STAGING_DIR/dot-claude/settings.local.json.template"
    success "Created settings.local.json.template"
fi

# =============================================================================
# STAGE ~/.codex/
# =============================================================================

if [[ "$INCLUDE_CODEX" == true ]]; then
    print_section "Staging ~/.codex/ directory"

    mkdir -p "$STAGING_DIR/dot-codex"

    # Copy playbooks (including full/agents/)
    if [[ -d "$CODEX_DIR/playbooks" ]]; then
        cp -R "$CODEX_DIR/playbooks" "$STAGING_DIR/dot-codex/"
        CODEX_AGENT_COUNT=$(ls "$STAGING_DIR/dot-codex/playbooks/full/agents/"*.md 2>/dev/null | wc -l | tr -d ' ')
        success "Copied playbooks: $CODEX_AGENT_COUNT ported agents"
    fi

    # Copy rules
    if [[ -d "$CODEX_DIR/rules" ]]; then
        mkdir -p "$STAGING_DIR/dot-codex/rules"
        if [[ -f "$CODEX_DIR/rules/default.rules" ]]; then
            sed "s|${HOME}|{{HOME}}|g" "$CODEX_DIR/rules/default.rules" > \
                "$STAGING_DIR/dot-codex/rules/default.rules.template"
        fi
        success "Created rules template"
    fi

    # Copy scripts
    if [[ -d "$CODEX_DIR/scripts" ]]; then
        cp -R "$CODEX_DIR/scripts" "$STAGING_DIR/dot-codex/"
        success "Copied scripts"
    fi

    # Copy templates
    if [[ -d "$CODEX_DIR/templates" ]]; then
        cp -R "$CODEX_DIR/templates" "$STAGING_DIR/dot-codex/"
        success "Copied templates"
    fi

    # Copy tools (PPTX with OOXML schemas)
    if [[ -d "$CODEX_DIR/tools" ]]; then
        cp -R "$CODEX_DIR/tools" "$STAGING_DIR/dot-codex/"
        success "Copied tools (including PPTX/OOXML)"
    fi

    # Copy documentation
    CODEX_DOCS=(
        "BINARY_FILE_REFERENCE.md"
        "CONFIGURATION_GUIDE.md"
        "DELEGATION_PROTOCOL.md"
        "HUBSPOT_IMPLEMENTATION_GUIDE.md"
        "PLAYBOOKS_INDEX.md"
        "PROJECTS_INDEX.md"
        "QUALITY_STANDARDS.md"
        "PERSONA.md"
        "TASK_MANAGEMENT_GUIDE.md"
    )

    CODEX_DOC_COUNT=0
    for doc in "${CODEX_DOCS[@]}"; do
        if [[ -f "$CODEX_DIR/$doc" ]]; then
            cp "$CODEX_DIR/$doc" "$STAGING_DIR/dot-codex/"
            ((CODEX_DOC_COUNT++))
        fi
    done
    success "Copied $CODEX_DOC_COUNT documentation files"

    # Create config.toml template
    if [[ -f "$CODEX_DIR/config.toml" ]]; then
        sed "s|${HOME}|{{HOME}}|g" "$CODEX_DIR/config.toml" > \
            "$STAGING_DIR/dot-codex/config.toml.template"
        success "Created config.toml.template"
    fi
fi

# =============================================================================
# STAGE LaunchAgents
# =============================================================================

print_section "Staging LaunchAgents"

mkdir -p "$STAGING_DIR/launchagents"

# Ollama plist
OLLAMA_PLIST="$HOME/Library/LaunchAgents/homebrew.mxcl.ollama.plist"
if [[ -f "$OLLAMA_PLIST" ]]; then
    cp "$OLLAMA_PLIST" "$STAGING_DIR/launchagents/"
    success "Copied Ollama LaunchAgent"
else
    warn "Ollama LaunchAgent not found"
fi

# RAG Dashboard plist (may be disabled)
for plist in "$HOME/Library/LaunchAgents/com.claude.rag-dashboard.plist"*; do
    if [[ -f "$plist" ]]; then
        sed "s|${HOME}|{{HOME}}|g" "$plist" > \
            "$STAGING_DIR/launchagents/com.claude.rag-dashboard.plist.template"
        success "Created RAG Dashboard LaunchAgent template"
        break
    fi
done

# =============================================================================
# CREATE MCP CONFIG TEMPLATE
# =============================================================================

print_section "Creating MCP config template"

# Create mcp.json template with API key placeholder
cat > "$STAGING_DIR/mcp.json.template" << 'MCPEOF'
{
  "mcpServers": {
    "rag-server": {
      "command": "{{HOME}}/.local/bin/uv",
      "args": [
        "run",
        "--directory",
        "{{HOME}}/.claude/mcp-servers/rag-server",
        "python",
        "-m",
        "rag_server"
      ],
      "env": {
        "OLLAMA_BASE_URL": "http://localhost:11434",
        "OLLAMA_MODEL": "mxbai-embed-large"
      }
    },
    "fathom": {
      "command": "{{HOME}}/.claude/mcp-servers/fathom/.venv/bin/python",
      "args": [
        "{{HOME}}/.claude/mcp-servers/fathom/server.py"
      ],
      "env": {
        "FATHOM_API_KEY": "YOUR_FATHOM_API_KEY_HERE",
        "FATHOM_OUTPUT_DIR": "{{HOME}}/Downloads/fathom-exports"
      }
    }
  }
}
MCPEOF
success "Created mcp.json.template (API keys stripped)"

# =============================================================================
# CREATE MANIFEST
# =============================================================================

print_section "Creating manifest"

# Count components
FINAL_AGENT_COUNT=$(ls "$STAGING_DIR/dot-claude/agents/"*.md 2>/dev/null | wc -l | tr -d ' ')
FINAL_SKILL_COUNT=$(ls -d "$STAGING_DIR/dot-claude/skills/"*/ 2>/dev/null | wc -l | tr -d ' ')
FINAL_HOOK_COUNT=$(find "$STAGING_DIR/dot-claude/hooks" -name "*.sh" -o -name "*.py" 2>/dev/null | wc -l | tr -d ' ')
FINAL_CTM_FILES=$(ls "$STAGING_DIR/dot-claude/ctm/lib/"*.py 2>/dev/null | wc -l | tr -d ' ')
FINAL_CODEX_AGENTS=0
if [[ -d "$STAGING_DIR/dot-codex/playbooks/full/agents" ]]; then
    FINAL_CODEX_AGENTS=$(ls "$STAGING_DIR/dot-codex/playbooks/full/agents/"*.md 2>/dev/null | wc -l | tr -d ' ')
fi

cat > "$STAGING_DIR/manifest.json" << EOF
{
  "version": "$VERSION",
  "created": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "source_machine": "$(hostname)",
  "source_user": "$(whoami)",
  "components": {
    "claude": {
      "agents": $FINAL_AGENT_COUNT,
      "skills": $FINAL_SKILL_COUNT,
      "hooks": $FINAL_HOOK_COUNT,
      "ctm_lib_files": $FINAL_CTM_FILES
    },
    "codex": {
      "ported_agents": $FINAL_CODEX_AGENTS
    }
  },
  "dependencies": {
    "homebrew": ["python@3.12", "node", "ollama", "jq", "uv"],
    "npm_global": ["@openai/codex", "ccusage"],
    "ollama_models": ["mxbai-embed-large"],
    "python_packages": {
      "rag-server": "see pyproject.toml",
      "fathom": ["mcp", "httpx"]
    }
  },
  "plugins": [
    "visual-documentation-skills@mhattingpete-claude-skills",
    "doc-tools@cc-skills",
    "itp@cc-skills",
    "feature-dev@claude-code-plugins"
  ],
  "services": {
    "ollama": "http://localhost:11434",
    "rag_dashboard": "http://localhost:8420"
  }
}
EOF
success "Created manifest.json"

# =============================================================================
# CREATE README
# =============================================================================

print_section "Creating README"

cat > "$STAGING_DIR/README.md" << 'READMEEOF'
# Claude Code Infrastructure Package

Complete replication package for Claude Code configuration including RAG, CTM, CDP,
agents, skills, hooks, MCP servers, and Codex integration.

## Quick Start

```bash
chmod +x install.sh
./install.sh
```

## Contents

```
.
├── dot-claude/          → ~/.claude/
├── dot-codex/           → ~/.codex/
├── launchagents/        → ~/Library/LaunchAgents/
├── mcp.json.template    → ~/.mcp.json
├── manifest.json        Component inventory
├── install.sh           Automated installer
└── README.md            This file
```

## Post-Installation

1. **Configure API keys:**
   ```bash
   # Edit ~/.mcp.json and replace YOUR_FATHOM_API_KEY_HERE
   nano ~/.mcp.json
   ```

2. **Authenticate Claude Code:**
   ```bash
   claude auth
   ```

3. **Verify installation:**
   ```bash
   ~/.claude/scripts/validate-setup.sh
   ```

4. **(Optional) Enable RAG Dashboard auto-start:**
   ```bash
   mv ~/Library/LaunchAgents/com.claude.rag-dashboard.plist.disabled \
      ~/Library/LaunchAgents/com.claude.rag-dashboard.plist
   launchctl load ~/Library/LaunchAgents/com.claude.rag-dashboard.plist
   ```

## What's Included

- **80 agents** - Specialized task agents for CRM consulting
- **11 skills** - Workflow skills (solution-architect, doc-coauthoring, etc.)
- **4 plugins** - Marketplace plugins (visual-documentation, doc-tools, itp, feature-dev)
- **CTM system** - Cognitive Task Manager for persistent context
- **RAG system** - Semantic search with Ollama embeddings
- **MCP servers** - RAG server + Fathom video integration
- **Codex integration** - 76 ported agents for token optimization

## Requirements

- macOS 14+
- Homebrew
- ~3GB disk space

## Support

For issues, see ~/.claude/COMPLETE_REPLICATION_GUIDE.md
READMEEOF
success "Created README.md"

# =============================================================================
# CREATE INSTALL SCRIPT
# =============================================================================

print_section "Creating install.sh"

cat > "$STAGING_DIR/install.sh" << 'INSTALLEOF'
#!/bin/bash
# =============================================================================
# Claude Code Infrastructure Installer
# =============================================================================
# Installs the complete Claude Code configuration from the distribution archive.
#
# Usage: ./install.sh [OPTIONS]
#
# Options:
#   --help           Show this help message
#   --skip-homebrew  Skip Homebrew dependency installation
#   --skip-ollama    Skip Ollama setup
#   --skip-plugins   Skip plugin installation
#   --dry-run        Show what would be done without making changes
# =============================================================================

set -euo pipefail

VERSION="1.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIN_MACOS_VERSION="14"
REQUIRED_DISK_SPACE_MB=3000

# Options
SKIP_HOMEBREW=false
SKIP_OLLAMA=false
SKIP_PLUGINS=false
DRY_RUN=false

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --help           Show this help message"
            echo "  --skip-homebrew  Skip Homebrew dependency installation"
            echo "  --skip-ollama    Skip Ollama setup"
            echo "  --skip-plugins   Skip plugin installation"
            echo "  --dry-run        Show what would be done without making changes"
            exit 0
            ;;
        --skip-homebrew) SKIP_HOMEBREW=true; shift ;;
        --skip-ollama) SKIP_OLLAMA=true; shift ;;
        --skip-plugins) SKIP_PLUGINS=true; shift ;;
        --dry-run) DRY_RUN=true; shift ;;
        *) shift ;;
    esac
done

print_header() {
    echo ""
    echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${BLUE}  $1${NC}"
    echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
}

print_section() {
    echo ""
    echo -e "${BOLD}▶ $1${NC}"
}

success() { echo -e "  ${GREEN}✓${NC} $1"; }
warn() { echo -e "  ${YELLOW}⚠${NC} $1"; }
error() { echo -e "  ${RED}✗${NC} $1"; }
info() { echo -e "  ${BLUE}ℹ${NC} $1"; }

run_cmd() {
    if [[ "$DRY_RUN" == true ]]; then
        echo "  [DRY RUN] $*"
    else
        "$@"
    fi
}

# =============================================================================
# PHASE 0: PRE-FLIGHT CHECKS
# =============================================================================

preflight_checks() {
    print_header "Claude Code Infrastructure Installer v${VERSION}"

    print_section "Pre-flight checks"

    # Platform check
    if [[ "$(uname -s)" != "Darwin" ]]; then
        error "This installer is designed for macOS only"
        exit 1
    fi
    success "Platform: macOS ($(uname -m))"

    # macOS version check
    local version=$(sw_vers -productVersion)
    local major=$(echo "$version" | cut -d. -f1)
    if [[ $major -lt $MIN_MACOS_VERSION ]]; then
        warn "macOS $MIN_MACOS_VERSION+ recommended, found: $version"
    else
        success "macOS version: $version"
    fi

    # Disk space check
    local available_mb=$(df -m "$HOME" | awk 'NR==2 {print $4}')
    if [[ $available_mb -lt $REQUIRED_DISK_SPACE_MB ]]; then
        error "Insufficient disk space. Need ${REQUIRED_DISK_SPACE_MB}MB, have ${available_mb}MB"
        exit 1
    fi
    success "Disk space: ${available_mb}MB available"

    # Check for existing installation
    if [[ -d "$HOME/.claude" ]] || [[ -d "$HOME/.codex" ]]; then
        warn "Existing installation detected"
        if [[ "$DRY_RUN" == false ]]; then
            read -p "Backup and continue? (y/n): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                backup_existing
            else
                error "Installation cancelled"
                exit 1
            fi
        else
            info "[DRY RUN] Would backup existing installation"
        fi
    fi

    # Check archive contents
    if [[ ! -d "$SCRIPT_DIR/dot-claude" ]]; then
        error "Archive contents not found. Expected dot-claude/ directory."
        exit 1
    fi
    success "Archive contents verified"
}

backup_existing() {
    local backup_dir="$HOME/.claude-backup-$(date +%Y%m%d-%H%M%S)"
    info "Backing up to $backup_dir..."

    mkdir -p "$backup_dir"

    if [[ -d "$HOME/.claude" ]]; then
        run_cmd mv "$HOME/.claude" "$backup_dir/dot-claude"
    fi
    if [[ -d "$HOME/.codex" ]]; then
        run_cmd mv "$HOME/.codex" "$backup_dir/dot-codex"
    fi
    if [[ -f "$HOME/.mcp.json" ]]; then
        run_cmd cp "$HOME/.mcp.json" "$backup_dir/mcp.json"
    fi

    success "Backup created at $backup_dir"
}

# =============================================================================
# PHASE 1: HOMEBREW DEPENDENCIES
# =============================================================================

install_homebrew_deps() {
    if [[ "$SKIP_HOMEBREW" == true ]]; then
        info "Skipping Homebrew dependencies (--skip-homebrew)"
        return
    fi

    print_section "Installing Homebrew dependencies"

    # Check if Homebrew exists
    if ! command -v brew &> /dev/null; then
        info "Installing Homebrew..."
        run_cmd /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi

    local packages=("python@3.12" "node" "ollama" "jq" "uv")

    for pkg in "${packages[@]}"; do
        if brew list "$pkg" &>/dev/null 2>&1; then
            success "$pkg already installed"
        else
            info "Installing $pkg..."
            run_cmd brew install "$pkg"
        fi
    done
}

# =============================================================================
# PHASE 2: NPM GLOBAL PACKAGES
# =============================================================================

install_npm_packages() {
    print_section "Installing npm global packages"

    local packages=("@openai/codex" "ccusage")

    for pkg in "${packages[@]}"; do
        if npm list -g "$pkg" &>/dev/null 2>&1; then
            success "$pkg already installed"
        else
            info "Installing $pkg..."
            run_cmd npm install -g "$pkg"
        fi
    done
}

# =============================================================================
# PHASE 3: EXTRACT CONFIGURATION
# =============================================================================

process_template() {
    local src="$1"
    local dest="$2"

    # Replace {{HOME}} with actual home directory
    if [[ "$DRY_RUN" == true ]]; then
        echo "  [DRY RUN] Process template: $src -> $dest"
    else
        sed "s|{{HOME}}|$HOME|g" "$src" > "$dest"
    fi
}

extract_config() {
    print_section "Extracting configuration"

    # Copy dot-claude
    if [[ -d "$SCRIPT_DIR/dot-claude" ]]; then
        run_cmd mkdir -p "$HOME/.claude"
        run_cmd cp -R "$SCRIPT_DIR/dot-claude/"* "$HOME/.claude/"

        # Process template files
        for template in "$HOME/.claude/"*.template; do
            if [[ -f "$template" ]]; then
                local target="${template%.template}"
                process_template "$template" "$target"
                run_cmd rm "$template"
            fi
        done

        success "Extracted ~/.claude/"
    fi

    # Copy dot-codex
    if [[ -d "$SCRIPT_DIR/dot-codex" ]]; then
        run_cmd mkdir -p "$HOME/.codex"
        run_cmd cp -R "$SCRIPT_DIR/dot-codex/"* "$HOME/.codex/"

        # Process template files
        for template in "$HOME/.codex/"*.template "$HOME/.codex/rules/"*.template; do
            if [[ -f "$template" ]]; then
                local target="${template%.template}"
                process_template "$template" "$target"
                run_cmd rm "$template"
            fi
        done

        success "Extracted ~/.codex/"
    fi

    # Copy MCP config
    if [[ -f "$SCRIPT_DIR/mcp.json.template" ]]; then
        process_template "$SCRIPT_DIR/mcp.json.template" "$HOME/.mcp.json"
        success "Created ~/.mcp.json"
    fi

    # Make scripts executable
    if [[ "$DRY_RUN" == false ]]; then
        find "$HOME/.claude" -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true
        find "$HOME/.claude" -name "ctm" -exec chmod +x {} \; 2>/dev/null || true
        find "$HOME/.claude" -name "cc" -exec chmod +x {} \; 2>/dev/null || true
        find "$HOME/.claude" -name "acp" -exec chmod +x {} \; 2>/dev/null || true
        find "$HOME/.codex" -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true
    fi
    success "Set executable permissions"
}

# =============================================================================
# PHASE 4: CREATE SYMLINKS
# =============================================================================

create_symlinks() {
    print_section "Creating symlinks"

    run_cmd mkdir -p "$HOME/.local/bin"

    # Add to PATH if not present
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        if [[ -f "$HOME/.zshrc" ]]; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
            warn "Added ~/.local/bin to PATH in .zshrc (restart terminal)"
        fi
    fi

    # Create symlinks
    if [[ -f "$HOME/.claude/scripts/cc" ]]; then
        run_cmd ln -sf "$HOME/.claude/scripts/cc" "$HOME/.local/bin/cc"
        success "Symlink: cc"
    fi

    if [[ -f "$HOME/.claude/ctm/scripts/ctm" ]]; then
        run_cmd ln -sf "$HOME/.claude/ctm/scripts/ctm" "$HOME/.local/bin/ctm"
        success "Symlink: ctm"
    fi
}

# =============================================================================
# PHASE 5: CREATE DIRECTORY STRUCTURE
# =============================================================================

create_directories() {
    print_section "Creating directory structure"

    local claude_dirs=(
        "cache"
        "debug"
        "file-history"
        "paste-cache"
        "plans"
        "projects"
        "session-env"
        "shell-snapshots"
        "statsig"
        "telemetry"
        "todos"
    )

    for dir in "${claude_dirs[@]}"; do
        run_cmd mkdir -p "$HOME/.claude/$dir"
    done

    local codex_dirs=(
        "log"
        "sessions"
        "tmp"
    )

    for dir in "${codex_dirs[@]}"; do
        run_cmd mkdir -p "$HOME/.codex/$dir"
    done

    success "Created runtime directories"
}

# =============================================================================
# PHASE 6: SETUP PYTHON ENVIRONMENTS
# =============================================================================

setup_python_envs() {
    print_section "Setting up Python environments"

    # RAG Server
    if [[ -d "$HOME/.claude/mcp-servers/rag-server" ]]; then
        info "Setting up RAG server environment..."
        if [[ "$DRY_RUN" == false ]]; then
            cd "$HOME/.claude/mcp-servers/rag-server"
            uv venv 2>/dev/null || python3 -m venv .venv
            if [[ -f "pyproject.toml" ]]; then
                uv pip install -e . 2>/dev/null || .venv/bin/pip install -e .
            fi
        fi
        success "RAG server venv ready"
    fi

    # Fathom MCP
    if [[ -d "$HOME/.claude/mcp-servers/fathom" ]]; then
        info "Setting up Fathom MCP environment..."
        if [[ "$DRY_RUN" == false ]]; then
            cd "$HOME/.claude/mcp-servers/fathom"
            uv venv 2>/dev/null || python3 -m venv .venv
            uv pip install mcp httpx 2>/dev/null || .venv/bin/pip install mcp httpx
        fi
        success "Fathom MCP venv ready"
    fi
}

# =============================================================================
# PHASE 7: SETUP LAUNCHAGENTS
# =============================================================================

setup_launchagents() {
    print_section "Setting up LaunchAgents"

    local la_dir="$HOME/Library/LaunchAgents"
    run_cmd mkdir -p "$la_dir"

    # Ollama plist
    if [[ -f "$SCRIPT_DIR/launchagents/homebrew.mxcl.ollama.plist" ]]; then
        run_cmd cp "$SCRIPT_DIR/launchagents/homebrew.mxcl.ollama.plist" "$la_dir/"
        success "Ollama LaunchAgent installed"
    fi

    # RAG Dashboard plist (disabled by default)
    if [[ -f "$SCRIPT_DIR/launchagents/com.claude.rag-dashboard.plist.template" ]]; then
        process_template "$SCRIPT_DIR/launchagents/com.claude.rag-dashboard.plist.template" \
            "$la_dir/com.claude.rag-dashboard.plist.disabled"
        success "RAG Dashboard LaunchAgent installed (disabled)"
    fi
}

# =============================================================================
# PHASE 8: SETUP OLLAMA
# =============================================================================

setup_ollama() {
    if [[ "$SKIP_OLLAMA" == true ]]; then
        info "Skipping Ollama setup (--skip-ollama)"
        return
    fi

    print_section "Setting up Ollama"

    # Start Ollama if not running
    if ! pgrep -x "ollama" > /dev/null 2>&1; then
        info "Starting Ollama..."
        if [[ "$DRY_RUN" == false ]]; then
            brew services start ollama 2>/dev/null || ollama serve &
            sleep 5
        fi
    fi

    # Pull required model
    info "Pulling mxbai-embed-large model..."
    if [[ "$DRY_RUN" == false ]]; then
        ollama pull mxbai-embed-large
    fi

    success "Ollama ready with mxbai-embed-large"
}

# =============================================================================
# PHASE 9: INSTALL PLUGINS
# =============================================================================

install_plugins() {
    if [[ "$SKIP_PLUGINS" == true ]]; then
        info "Skipping plugins (--skip-plugins)"
        return
    fi

    print_section "Installing marketplace plugins"

    if command -v claude &> /dev/null; then
        local plugins=(
            "visual-documentation-skills@mhattingpete-claude-skills"
            "doc-tools@cc-skills"
            "itp@cc-skills"
            "feature-dev@claude-code-plugins"
        )

        for plugin in "${plugins[@]}"; do
            info "Installing plugin: $plugin"
            if [[ "$DRY_RUN" == false ]]; then
                claude plugin install "$plugin" 2>/dev/null || warn "Could not install $plugin"
            fi
        done
    else
        warn "Claude CLI not found - plugins will need manual installation"
        info "After authenticating, run: claude plugin install <plugin-name>"
    fi
}

# =============================================================================
# PHASE 10: VERIFICATION
# =============================================================================

verify_installation() {
    print_section "Verifying installation"

    local errors=0

    # Check critical files
    local critical_files=(
        "$HOME/.claude/CLAUDE.md"
        "$HOME/.claude/settings.json"
        "$HOME/.mcp.json"
    )

    for file in "${critical_files[@]}"; do
        if [[ -f "$file" ]]; then
            success "Found: $file"
        else
            error "Missing: $file"
            ((errors++))
        fi
    done

    # Check symlinks
    if [[ -L "$HOME/.local/bin/cc" ]]; then
        success "Symlink: cc"
    else
        warn "Missing symlink: cc"
    fi

    if [[ -L "$HOME/.local/bin/ctm" ]]; then
        success "Symlink: ctm"
    else
        warn "Missing symlink: ctm"
    fi

    # Check Ollama
    if [[ "$SKIP_OLLAMA" == false ]]; then
        if curl -s http://localhost:11434/api/tags 2>/dev/null | grep -q "mxbai-embed-large"; then
            success "Ollama: mxbai-embed-large model available"
        else
            warn "Ollama: mxbai-embed-large may not be ready"
        fi
    fi

    # Run validation script if available
    if [[ -x "$HOME/.claude/scripts/validate-setup.sh" ]] && [[ "$DRY_RUN" == false ]]; then
        echo ""
        info "Running comprehensive validation..."
        "$HOME/.claude/scripts/validate-setup.sh" --quick || true
    fi

    echo ""
    if [[ $errors -eq 0 ]]; then
        print_header "Installation completed successfully!"
    else
        print_header "Installation completed with $errors errors"
    fi
}

# =============================================================================
# PHASE 11: POST-INSTALL INSTRUCTIONS
# =============================================================================

post_install_instructions() {
    echo ""
    echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${BLUE}  Post-Installation Steps${NC}"
    echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "1. REQUIRED: Configure API keys in ~/.mcp.json"
    echo "   - FATHOM_API_KEY: Get from fathom.video settings"
    echo ""
    echo "2. REQUIRED: Authenticate Claude Code"
    echo "   Run: claude auth"
    echo ""
    echo "3. OPTIONAL: Start RAG Dashboard"
    echo "   cd ~/.claude/rag-dashboard && ./start-dashboard.sh"
    echo ""
    echo "4. OPTIONAL: Enable RAG Dashboard auto-start"
    echo '   mv ~/Library/LaunchAgents/com.claude.rag-dashboard.plist.disabled \'
    echo '      ~/Library/LaunchAgents/com.claude.rag-dashboard.plist'
    echo '   launchctl load ~/Library/LaunchAgents/com.claude.rag-dashboard.plist'
    echo ""
    echo "5. Verify installation:"
    echo "   ~/.claude/scripts/validate-setup.sh"
    echo ""
    echo "6. Start a new terminal session to reload PATH"
    echo ""
}

# =============================================================================
# MAIN
# =============================================================================

main() {
    preflight_checks
    install_homebrew_deps
    install_npm_packages
    extract_config
    create_symlinks
    create_directories
    setup_python_envs
    setup_launchagents
    setup_ollama
    install_plugins
    verify_installation
    post_install_instructions
}

main "$@"
INSTALLEOF

chmod +x "$STAGING_DIR/install.sh"
success "Created install.sh"

# =============================================================================
# CREATE ARCHIVE
# =============================================================================

print_section "Creating archive"

cd "$STAGING_DIR"
tar -czf "$OUTPUT_DIR/$ARCHIVE_NAME" .

# Get archive size
ARCHIVE_SIZE=$(du -h "$OUTPUT_DIR/$ARCHIVE_NAME" | cut -f1)

print_header "Archive created successfully!"
echo ""
echo "  File: $OUTPUT_DIR/$ARCHIVE_NAME"
echo "  Size: $ARCHIVE_SIZE"
echo ""
echo "  Components:"
echo "    - $FINAL_AGENT_COUNT agents"
echo "    - $FINAL_SKILL_COUNT skills"
echo "    - $FINAL_HOOK_COUNT hooks"
echo "    - $FINAL_CTM_FILES CTM lib files"
if [[ "$INCLUDE_CODEX" == true ]]; then
    echo "    - $FINAL_CODEX_AGENTS Codex ported agents"
fi
echo ""
echo "  To install on target machine:"
echo "    1. Copy the archive"
echo "    2. Extract: tar -xzf $ARCHIVE_NAME"
echo "    3. Run: ./install.sh"
echo ""
