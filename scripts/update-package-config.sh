#!/bin/bash
# =============================================================================
# Update Package Configuration
# =============================================================================
# Automatically scans the Claude infrastructure and suggests config updates
# when new components are discovered.
#
# Usage: ./update-package-config.sh [OPTIONS]
#
# Options:
#   --auto-update      Apply discovered changes automatically
#   --report           Only generate report, don't modify config
#   --diff             Show what would change
#   --backup           Create backup before modifying
#   --validate         Validate config after update
#   --help             Show this help
# =============================================================================

set -euo pipefail

VERSION="1.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
PACKAGE_CONFIG="$CLAUDE_DIR/.package-config.json"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Options
AUTO_UPDATE=false
REPORT_ONLY=false
SHOW_DIFF=false
CREATE_BACKUP=false
VALIDATE_AFTER=false

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
        --auto-update) AUTO_UPDATE=true; shift ;;
        --report) REPORT_ONLY=true; shift ;;
        --diff) SHOW_DIFF=true; shift ;;
        --backup) CREATE_BACKUP=true; shift ;;
        --validate) VALIDATE_AFTER=true; shift ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Updates .package-config.json based on discovered components"
            exit 0
            ;;
        *) shift ;;
    esac
done

# Utility functions
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

# Main logic
print_header "Package Configuration Updater v${VERSION}"

# Check prerequisites
if [[ ! -f "$PACKAGE_CONFIG" ]]; then
    error "Package config not found: $PACKAGE_CONFIG"
    exit 1
fi

if ! command -v jq &> /dev/null; then
    error "jq is required but not installed"
    exit 1
fi

print_section "Scanning infrastructure"

# Get configured directories
CONFIGURED_DIRS=$(jq -r '.directory_rules[].path' "$PACKAGE_CONFIG" 2>/dev/null | sort)
info "Configured directories:"
echo "$CONFIGURED_DIRS" | while read dir; do
    echo "    - $dir"
done

# Get actual directories
print_section "Discovering actual components"

ACTUAL_DIRS=$(find "$CLAUDE_DIR" -maxdepth 1 -type d -not -name ".*" | xargs -I {} basename {} | sort)
info "Actual directories:"
echo "$ACTUAL_DIRS" | while read dir; do
    echo "    - $dir"
done

# Find differences
print_section "Analyzing differences"

MISSING_FROM_CONFIG=$(comm -23 <(echo "$ACTUAL_DIRS") <(echo "$CONFIGURED_DIRS") || true)
OBSOLETE_IN_CONFIG=$(comm -13 <(echo "$ACTUAL_DIRS") <(echo "$CONFIGURED_DIRS") || true)

if [[ -z "$MISSING_FROM_CONFIG" && -z "$OBSOLETE_IN_CONFIG" ]]; then
    success "Configuration is in sync with actual structure"
    exit 0
fi

# Report findings
if [[ -n "$MISSING_FROM_CONFIG" ]]; then
    warn "Components not in config (discovered but not configured):"
    echo "$MISSING_FROM_CONFIG" | while read dir; do
        echo "    - $dir"
    done
fi

if [[ -n "$OBSOLETE_IN_CONFIG" ]]; then
    warn "Obsolete rules in config (configured but not found):"
    echo "$OBSOLETE_IN_CONFIG" | while read dir; do
        echo "    - $dir"
    done
fi

if [[ "$REPORT_ONLY" == true ]]; then
    info "Report-only mode: no changes made"
    exit 0
fi

if [[ "$CREATE_BACKUP" == true ]]; then
    print_section "Creating backup"
    BACKUP_FILE="$PACKAGE_CONFIG.backup-$TIMESTAMP"
    cp "$PACKAGE_CONFIG" "$BACKUP_FILE"
    success "Backup created: $BACKUP_FILE"
fi

if [[ "$AUTO_UPDATE" == true ]]; then
    print_section "Updating configuration"

    # For missing components, add template rules
    if [[ -n "$MISSING_FROM_CONFIG" ]]; then
        info "Adding template rules for discovered components..."

        TEMP_FILE=$(mktemp)
        cp "$PACKAGE_CONFIG" "$TEMP_FILE"

        echo "$MISSING_FROM_CONFIG" | while read dir; do
            # Determine type based on directory name
            local type="$dir"
            case "$dir" in
                mcp-servers) type="mcp-servers" ;;
                agents) type="agents" ;;
                skills) type="skills" ;;
                hooks) type="hooks" ;;
                templates) type="templates" ;;
                lessons) type="lessons" ;;
                *) type="generic" ;;
            esac

            info "Adding rule for: $dir (type: $type)"

            # Add template rule
            jq ".directory_rules += [{
                \"path\": \"$dir\",
                \"type\": \"$type\",
                \"include\": true,
                \"pattern\": \"**/*\",
                \"exclude_dirs\": [\".git\", \"__pycache__\"],
                \"exclude_files\": [\".DS_Store\", \"*.pyc\"],
                \"description\": \"Auto-discovered component: $dir\"
            }]" "$TEMP_FILE" > "$TEMP_FILE.new"

            mv "$TEMP_FILE.new" "$TEMP_FILE"
        done

        cp "$TEMP_FILE" "$PACKAGE_CONFIG"
        rm "$TEMP_FILE"
    fi

    # Remove obsolete rules
    if [[ -n "$OBSOLETE_IN_CONFIG" ]]; then
        info "Removing obsolete rules..."

        TEMP_FILE=$(mktemp)
        cp "$PACKAGE_CONFIG" "$TEMP_FILE"

        echo "$OBSOLETE_IN_CONFIG" | while read dir; do
            info "Removing rule for: $dir"
            jq ".directory_rules |= map(select(.path != \"$dir\"))" "$TEMP_FILE" > "$TEMP_FILE.new"
            mv "$TEMP_FILE.new" "$TEMP_FILE"
        done

        cp "$TEMP_FILE" "$PACKAGE_CONFIG"
        rm "$TEMP_FILE"
    fi

    # Update the generated timestamp
    jq ".generated = \"$(date +%Y-%m-%d)\"" "$PACKAGE_CONFIG" > "$PACKAGE_CONFIG.new"
    mv "$PACKAGE_CONFIG.new" "$PACKAGE_CONFIG"

    success "Configuration updated"
fi

# Validate if requested
if [[ "$VALIDATE_AFTER" == true ]]; then
    print_section "Validating updated configuration"

    if jq empty "$PACKAGE_CONFIG" 2>/dev/null; then
        success "Configuration JSON is valid"
    else
        error "Configuration JSON is invalid"
        exit 1
    fi
fi

if [[ "$SHOW_DIFF" == true && "$CREATE_BACKUP" == true ]]; then
    print_section "Changes"
    diff -u "$BACKUP_FILE" "$PACKAGE_CONFIG" || true
fi

print_header "Update complete"
success "Package configuration is now synchronized"
echo ""
