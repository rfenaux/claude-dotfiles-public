#!/bin/bash
# Claude Code Configuration Chain Auditor
# Comprehensive audit of Claude Code configuration
# Run: ~/.claude/scripts/audit-config-chain.sh [--quick]

set -euo pipefail

CLAUDE_DIR="${HOME}/.claude"
PROJECT_DIR="${PWD}"
QUICK_MODE=false

# Parse arguments
[[ "${1:-}" == "--quick" || "${1:-}" == "-q" ]] && QUICK_MODE=true

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# Counters
CRITICAL=0
WARNINGS=0
INFO=0
PASSED=0

# Score calculation
SCORE=100

print_header() {
    echo ""
    echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${BLUE}  $1${NC}"
    echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
}

section() {
    echo ""
    echo -e "${BOLD}▶ $1${NC}"
}

critical() {
    echo -e "  ${RED}✗ CRITICAL:${NC} $1"
    ((CRITICAL++)) || true
    SCORE=$((SCORE - 10))
}

warn() {
    echo -e "  ${YELLOW}⚠ WARNING:${NC} $1"
    ((WARNINGS++)) || true
    SCORE=$((SCORE - 3))
}

info() {
    echo -e "  ${BLUE}ℹ${NC} $1"
    ((INFO++)) || true
}

pass() {
    echo -e "  ${GREEN}✓${NC} $1"
    ((PASSED++)) || true
}

# ============================================================================
# 1. MEMORY FILE VALIDATION
# ============================================================================
check_memory_files() {
    section "Memory Files"

    # User CLAUDE.md
    if [[ -f "$CLAUDE_DIR/CLAUDE.md" ]]; then
        local lines
        lines=$(wc -l < "$CLAUDE_DIR/CLAUDE.md" | tr -d ' ')
        if [[ $lines -gt 300 ]]; then
            warn "User CLAUDE.md is $lines lines (recommended: <300)"
        elif [[ $lines -gt 60 ]]; then
            info "User CLAUDE.md is $lines lines (optimal: <60)"
        else
            pass "User CLAUDE.md length OK ($lines lines)"
        fi
    else
        info "No user CLAUDE.md (optional)"
    fi

    # Project CLAUDE.md
    local project_md=""
    if [[ -f "$PROJECT_DIR/CLAUDE.md" ]]; then
        project_md="$PROJECT_DIR/CLAUDE.md"
    elif [[ -f "$PROJECT_DIR/.claude/CLAUDE.md" ]]; then
        project_md="$PROJECT_DIR/.claude/CLAUDE.md"
    fi

    if [[ -n "$project_md" ]]; then
        local lines
        lines=$(wc -l < "$project_md" | tr -d ' ')
        pass "Project CLAUDE.md found ($lines lines)"
    else
        info "No project CLAUDE.md in $PROJECT_DIR"
    fi

    # Check for rules directory
    if [[ -d "$PROJECT_DIR/.claude/rules" ]]; then
        local rule_count
        rule_count=$(find "$PROJECT_DIR/.claude/rules" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
        pass "Project rules directory: $rule_count rule files"
    fi
}

# ============================================================================
# 2. IMPORT CHAIN VALIDATION
# ============================================================================
check_imports() {
    section "Import Chain Validation"

    if [[ -x "$CLAUDE_DIR/scripts/validate-imports.sh" ]]; then
        # Run import validator and capture output
        local result
        if result=$("$CLAUDE_DIR/scripts/validate-imports.sh" "$PROJECT_DIR" 2>&1); then
            local broken
            broken=$(echo "$result" | grep -c "NOT FOUND" 2>/dev/null || echo "0")
            broken=$(echo "$broken" | head -1 | tr -d ' ')
            local circular
            circular=$(echo "$result" | grep -c "Circular" 2>/dev/null || echo "0")
            circular=$(echo "$circular" | head -1 | tr -d ' ')

            if [[ "$broken" -gt 0 ]]; then
                warn "Found $broken broken import(s)"
            else
                pass "All imports resolve correctly"
            fi

            if [[ "$circular" -gt 0 ]]; then
                warn "Found $circular circular import chain(s)"
            fi
        else
            pass "Import validation completed (no issues)"
        fi
    else
        info "validate-imports.sh not found or not executable"
    fi
}

# ============================================================================
# 3. SETTINGS VALIDATION
# ============================================================================
check_settings() {
    section "Settings Files"

    # User settings
    if [[ -f "$CLAUDE_DIR/settings.json" ]]; then
        if jq empty "$CLAUDE_DIR/settings.json" 2>/dev/null; then
            pass "User settings.json is valid JSON"

            # Check for common issues
            local hooks_count
            hooks_count=$(jq '.hooks | length // 0' "$CLAUDE_DIR/settings.json" 2>/dev/null || echo "0")
            info "Hooks configured: $hooks_count event types"

            # Check for empty deny list (potential security)
            local deny_count
            deny_count=$(jq '.permissions.deny | length // 0' "$CLAUDE_DIR/settings.json" 2>/dev/null || echo "0")
            if [[ "$deny_count" == "0" ]]; then
                info "Deny list is empty (consider adding safety rules)"
            fi
        else
            critical "User settings.json is invalid JSON"
        fi
    else
        info "No user settings.json"
    fi

    # Project settings
    if [[ -f "$PROJECT_DIR/.claude/settings.json" ]]; then
        if jq empty "$PROJECT_DIR/.claude/settings.json" 2>/dev/null; then
            pass "Project settings.json is valid JSON"
        else
            critical "Project settings.json is invalid JSON"
        fi
    fi
}

# ============================================================================
# 4. AGENT VALIDATION
# ============================================================================
check_agents() {
    section "Agents"

    local agent_count
    agent_count=$(find "$CLAUDE_DIR/agents" -name "*.md" -type f 2>/dev/null | wc -l | tr -d ' ')

    if [[ -f "$CLAUDE_DIR/inventory.json" ]]; then
        local inventory_count
        inventory_count=$(jq '.counts.agents // 0' "$CLAUDE_DIR/inventory.json")

        if [[ "$agent_count" == "$inventory_count" ]]; then
            pass "Agent count matches inventory: $agent_count"
        else
            warn "Agent count mismatch: actual=$agent_count, inventory=$inventory_count"
            info "Run: ~/.claude/scripts/generate-inventory.sh"
        fi
    else
        info "Agent count: $agent_count (no inventory.json to verify)"
    fi

    # Check for auto-invoke agents
    if [[ -f "$CLAUDE_DIR/inventory.json" ]]; then
        local auto_invoke
        auto_invoke=$(jq '[.agents[] | select(.auto_invoke == true)] | length' "$CLAUDE_DIR/inventory.json" 2>/dev/null || echo "0")
        info "Auto-invoke agents: $auto_invoke"
    fi
}

# ============================================================================
# 5. SKILL VALIDATION
# ============================================================================
check_skills() {
    section "Skills"

    local skill_count
    skill_count=$(find "$CLAUDE_DIR/skills" -name "SKILL.md" -type f 2>/dev/null | wc -l | tr -d ' ')
    info "Skills found: $skill_count"

    # Check for skills without descriptions
    while IFS= read -r skill; do
        [[ -z "$skill" ]] && continue
        local has_desc
        has_desc=$(grep -c '^description:' "$skill" 2>/dev/null || echo "0")
        if [[ "$has_desc" == "0" ]]; then
            local name
            name=$(basename "$(dirname "$skill")")
            warn "Skill '$name' missing description"
        fi
    done < <(find "$CLAUDE_DIR/skills" -name "SKILL.md" -type f 2>/dev/null)
}

# ============================================================================
# 6. MCP CONFIGURATION
# ============================================================================
check_mcp() {
    section "MCP Servers"

    if [[ -f "$HOME/.mcp.json" ]]; then
        if jq empty "$HOME/.mcp.json" 2>/dev/null; then
            local server_count
            server_count=$(jq '.mcpServers | length' "$HOME/.mcp.json" 2>/dev/null || echo "0")
            pass ".mcp.json valid with $server_count server(s)"

            # Warn if many servers (context bloat)
            if [[ $server_count -gt 5 ]]; then
                warn "Many MCP servers ($server_count) may cause context bloat"
                info "Consider disabling unused servers in settings.json"
            fi
        else
            critical ".mcp.json is invalid JSON"
        fi
    else
        info "No .mcp.json (MCP not configured)"
    fi
}

# ============================================================================
# 7. STALE REFERENCE CHECK (skip in quick mode)
# ============================================================================
check_stale_refs() {
    [[ "$QUICK_MODE" == "true" ]] && return

    section "Stale References"

    local stale_count=0

    # Check CLAUDE.md for file:line references
    if [[ -f "$CLAUDE_DIR/CLAUDE.md" ]]; then
        while IFS= read -r ref; do
            [[ -z "$ref" ]] && continue
            local path="${ref%:*}"
            local line="${ref#*:}"

            # Skip URLs and common false positives
            [[ "$path" == *"http"* ]] && continue
            [[ "$path" == *"localhost"* ]] && continue

            if [[ -f "$path" ]]; then
                local total
                total=$(wc -l < "$path" 2>/dev/null | tr -d ' ' || echo "0")
                if [[ $line -gt $total ]]; then
                    warn "Stale reference: $ref (file has $total lines)"
                    ((stale_count++)) || true
                fi
            fi
        done < <(grep -oE '[a-zA-Z0-9_./-]+:[0-9]+' "$CLAUDE_DIR/CLAUDE.md" 2>/dev/null || true)
    fi

    if [[ $stale_count -eq 0 ]]; then
        pass "No stale file:line references found"
    fi
}

# ============================================================================
# 8. ANTI-PATTERN DETECTION
# ============================================================================
check_antipatterns() {
    [[ "$QUICK_MODE" == "true" ]] && return

    section "Anti-Pattern Detection"

    if [[ -f "$CLAUDE_DIR/CLAUDE.md" ]]; then
        # Check for style guide content (should use linters)
        if grep -qiE '(indent|spacing|bracket|semicolon).*rule' "$CLAUDE_DIR/CLAUDE.md" 2>/dev/null; then
            info "CLAUDE.md may contain style rules (consider using ESLint/Prettier)"
        fi

        # Check for code snippets (become stale)
        local code_blocks
        code_blocks=$(grep -c '```' "$CLAUDE_DIR/CLAUDE.md" 2>/dev/null || echo "0")
        if [[ $code_blocks -gt 20 ]]; then
            warn "CLAUDE.md has many code blocks ($code_blocks) - may become stale"
        fi

        # Check for task-specific content
        if grep -qiE '(bug #|issue #|ticket #|TODO:)' "$CLAUDE_DIR/CLAUDE.md" 2>/dev/null; then
            warn "CLAUDE.md may contain task-specific content"
        fi

        pass "Anti-pattern scan complete"
    fi
}

# ============================================================================
# MAIN
# ============================================================================
main() {
    print_header "Claude Code Configuration Audit"

    echo ""
    echo "Project: $PROJECT_DIR"
    echo "Mode: $([ "$QUICK_MODE" == "true" ] && echo "Quick" || echo "Full")"
    echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"

    check_memory_files
    check_imports
    check_settings
    check_agents
    check_skills
    check_mcp

    if [[ "$QUICK_MODE" != "true" ]]; then
        check_stale_refs
        check_antipatterns
    fi

    # Clamp score
    [[ $SCORE -lt 0 ]] && SCORE=0
    [[ $SCORE -gt 100 ]] && SCORE=100

    print_header "Audit Results"

    echo ""
    if [[ $SCORE -ge 90 ]]; then
        echo -e "Health Score: ${GREEN}${BOLD}$SCORE/100${NC} ✓"
    elif [[ $SCORE -ge 70 ]]; then
        echo -e "Health Score: ${YELLOW}${BOLD}$SCORE/100${NC}"
    else
        echo -e "Health Score: ${RED}${BOLD}$SCORE/100${NC}"
    fi

    echo ""
    echo -e "Critical: ${RED}$CRITICAL${NC} | Warnings: ${YELLOW}$WARNINGS${NC} | Info: ${BLUE}$INFO${NC} | Passed: ${GREEN}$PASSED${NC}"

    if [[ $CRITICAL -gt 0 ]]; then
        echo ""
        echo -e "${RED}⚠ Critical issues require immediate attention${NC}"
        exit 1
    fi

    exit 0
}

main "$@"
