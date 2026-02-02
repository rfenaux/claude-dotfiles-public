#!/bin/bash
# Claude Code Import Validator
# Validates @import references in CLAUDE.md files
# Run: ~/.claude/scripts/validate-imports.sh [path]

set -euo pipefail

CLAUDE_DIR="${HOME}/.claude"
PROJECT_DIR="${1:-$PWD}"
MAX_DEPTH=5

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Counters
VALID=0
BROKEN=0
WARNINGS=0

log() { echo -e "$1"; }
pass() { log "  ${GREEN}✓${NC} $1"; ((VALID++)); }
fail() { log "  ${RED}✗${NC} $1"; ((BROKEN++)); }
warn() { log "  ${YELLOW}⚠${NC} $1"; ((WARNINGS++)); }

# Extract @imports from a file (excluding code blocks)
extract_imports() {
    local file="$1"

    # Use awk to skip code blocks and extract @imports
    awk '
    /^```/ { in_code = !in_code; next }
    !in_code && /^@[^`]/ {
        # Extract the path after @
        match($0, /^@([^ ]+)/, arr)
        if (arr[1] != "") print arr[1]
    }
    ' "$file" 2>/dev/null || true
}

# Resolve import path to absolute
resolve_path() {
    local import="$1"
    local source_file="$2"
    local source_dir=$(dirname "$source_file")

    if [[ "$import" == ~/* ]]; then
        # Home directory expansion
        echo "${import/#\~/$HOME}"
    elif [[ "$import" == ./* ]]; then
        # Project root relative
        echo "$PROJECT_DIR/${import#./}"
    elif [[ "$import" == /* ]]; then
        # Already absolute
        echo "$import"
    else
        # Relative to source file
        echo "$source_dir/$import"
    fi
}

# Validate a single file's imports
validate_file() {
    local file="$1"
    local depth="${2:-0}"
    local visited="${3:-}"

    if [[ ! -f "$file" ]]; then
        return
    fi

    # Check for circular reference
    if [[ "$visited" == *"|$file|"* ]]; then
        warn "Circular import detected: $file"
        return
    fi

    # Check depth limit
    if [[ $depth -ge $MAX_DEPTH ]]; then
        warn "Import depth limit ($MAX_DEPTH) reached at: $file"
        return
    fi

    visited="${visited}|$file|"

    # Extract and validate each import
    while IFS= read -r import; do
        [[ -z "$import" ]] && continue

        local resolved=$(resolve_path "$import" "$file")

        if [[ -f "$resolved" ]]; then
            pass "$import → $resolved"
            # Recurse into imported file
            validate_file "$resolved" $((depth + 1)) "$visited"
        elif [[ -d "$resolved" ]]; then
            warn "$import → directory (expected file)"
        else
            fail "$import → NOT FOUND (from $file)"
        fi
    done < <(extract_imports "$file")
}

# Find all CLAUDE.md files to validate
find_memory_files() {
    local files=()

    # User CLAUDE.md
    [[ -f "$CLAUDE_DIR/CLAUDE.md" ]] && files+=("$CLAUDE_DIR/CLAUDE.md")

    # Project CLAUDE.md variants
    [[ -f "$PROJECT_DIR/CLAUDE.md" ]] && files+=("$PROJECT_DIR/CLAUDE.md")
    [[ -f "$PROJECT_DIR/.claude/CLAUDE.md" ]] && files+=("$PROJECT_DIR/.claude/CLAUDE.md")
    [[ -f "$PROJECT_DIR/CLAUDE.local.md" ]] && files+=("$PROJECT_DIR/CLAUDE.local.md")

    # Project rules
    if [[ -d "$PROJECT_DIR/.claude/rules" ]]; then
        while IFS= read -r -d '' rule; do
            files+=("$rule")
        done < <(find "$PROJECT_DIR/.claude/rules" -name "*.md" -print0 2>/dev/null)
    fi

    printf '%s\n' "${files[@]}"
}

# Main
main() {
    log "\n${GREEN}═══════════════════════════════════════════════════${NC}"
    log "${GREEN}  Claude Code Import Validator${NC}"
    log "${GREEN}═══════════════════════════════════════════════════${NC}\n"

    log "Project: $PROJECT_DIR"
    log "Max import depth: $MAX_DEPTH\n"

    while IFS= read -r file; do
        [[ -z "$file" ]] && continue
        log "\n▶ Checking: $file"
        validate_file "$file" 0 ""
    done < <(find_memory_files)

    # Summary
    log "\n${GREEN}═══════════════════════════════════════════════════${NC}"
    log "Results: ${GREEN}$VALID valid${NC} | ${RED}$BROKEN broken${NC} | ${YELLOW}$WARNINGS warnings${NC}"

    if [[ $BROKEN -gt 0 ]]; then
        exit 1
    fi
}

main "$@"
