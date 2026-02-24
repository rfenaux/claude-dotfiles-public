#!/bin/bash
# Claude Code Setup Validator
# Checks configuration consistency and compliance
# Run: ~/.claude/scripts/validate-setup.sh
# Run: ~/.claude/scripts/validate-setup.sh --quick  (fast mode for hooks)

# Don't exit on error - we want to continue checking
set +e

CLAUDE_DIR="$HOME/.claude"
QUICK_MODE=false

# Parse arguments
if [ "$1" = "--quick" ] || [ "$1" = "-q" ]; then
    QUICK_MODE=true
fi
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Counters
ERRORS=0
WARNINGS=0
PASSED=0

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

pass() {
    echo -e "  ${GREEN}✓${NC} $1"
    ((PASSED++))
}

warn() {
    echo -e "  ${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

fail() {
    echo -e "  ${RED}✗${NC} $1"
    ((ERRORS++))
}

info() {
    echo -e "  ${BLUE}ℹ${NC} $1"
}

# ============================================================================
# 1. AGENT VALIDATION
# ============================================================================
validate_agents() {
    print_section "Agents"

    # Count actual agents
    AGENT_COUNT=$(ls "$CLAUDE_DIR/agents/"*.md 2>/dev/null | wc -l | tr -d ' ')

    pass "Agents installed: $AGENT_COUNT agents"

    # Check for async frontmatter
    MISSING_ASYNC=()
    while IFS= read -r agent; do
        if ! grep -q "^async:" "$agent" 2>/dev/null; then
            MISSING_ASYNC+=("$(basename "$agent")")
        fi
    done < <(find "$CLAUDE_DIR/agents" -name "*.md" -type f 2>/dev/null)

    if [ ${#MISSING_ASYNC[@]} -eq 0 ]; then
        pass "All agents have async: frontmatter"
    else
        warn "${#MISSING_ASYNC[@]} agents missing async: frontmatter"
        for a in "${MISSING_ASYNC[@]:0:5}"; do
            info "  - $a"
        done
        [ ${#MISSING_ASYNC[@]} -gt 5 ] && info "  ... and $((${#MISSING_ASYNC[@]} - 5)) more"
    fi

    # Check for CDP compliance declaration
    MISSING_CDP=()
    while IFS= read -r agent; do
        if ! grep -q "cdp:" "$agent" 2>/dev/null && ! grep -q "CDP" "$agent" 2>/dev/null; then
            MISSING_CDP+=("$(basename "$agent")")
        fi
    done < <(find "$CLAUDE_DIR/agents" -name "*.md" -type f 2>/dev/null)

    if [ ${#MISSING_CDP[@]} -eq 0 ]; then
        pass "All agents reference CDP"
    else
        info "${#MISSING_CDP[@]} agents don't explicitly declare CDP (may inherit from standards)"
    fi
}

# ============================================================================
# 2. SKILLS VALIDATION
# ============================================================================
validate_skills() {
    print_section "Skills"

    # Count actual skills
    SKILL_COUNT=$(ls -d "$CLAUDE_DIR/skills/"*/ 2>/dev/null | wc -l | tr -d ' ')

    pass "Skills installed: $SKILL_COUNT skills"

    # Check each skill has SKILL.md
    MISSING_SKILLMD=()
    for skill_dir in "$CLAUDE_DIR/skills/"*/; do
        if [ ! -f "${skill_dir}SKILL.md" ]; then
            MISSING_SKILLMD+=("$(basename "$skill_dir")")
        fi
    done

    if [ ${#MISSING_SKILLMD[@]} -eq 0 ]; then
        pass "All skills have SKILL.md"
    else
        warn "${#MISSING_SKILLMD[@]} skills missing SKILL.md"
        for s in "${MISSING_SKILLMD[@]}"; do
            info "  - $s"
        done
    fi
}

# ============================================================================
# 3. HOOKS VALIDATION
# ============================================================================
validate_hooks() {
    print_section "Hooks"

    SETTINGS_FILE="$CLAUDE_DIR/settings.json"

    if [ ! -f "$SETTINGS_FILE" ]; then
        fail "settings.json not found"
        return
    fi

    # Check required hooks exist
    REQUIRED_HOOKS=("SessionStart" "PreCompact" "SessionEnd" "PostToolUse" "UserPromptSubmit")

    for hook in "${REQUIRED_HOOKS[@]}"; do
        if grep -q "\"$hook\"" "$SETTINGS_FILE"; then
            pass "Hook configured: $hook"
        else
            warn "Hook not configured: $hook"
        fi
    done

    # DYNAMIC: Extract and validate ALL hook scripts from settings.json
    if command -v jq &> /dev/null; then
        # Extract commands, then get just the script path (first token) for validation
        HOOK_SCRIPTS_FROM_SETTINGS=$(jq -r '
            .hooks | to_entries[] | .value[] | .hooks[]? |
            select(.type == "command") | .command |
            select(startswith("/"))
        ' "$SETTINGS_FILE" 2>/dev/null | awk '{print $1}' | sort -u)

        EXEC_ISSUES=0
        MISSING_ISSUES=0

        while IFS= read -r script; do
            [ -z "$script" ] && continue
            if [ -x "$script" ]; then
                pass "Hook executable: $(basename "$script")"
            elif [ -f "$script" ]; then
                warn "Hook NOT executable: $script"
                ((EXEC_ISSUES++))
            else
                fail "Hook script missing: $script"
                ((MISSING_ISSUES++))
            fi
        done <<< "$HOOK_SCRIPTS_FROM_SETTINGS"

        if [ $EXEC_ISSUES -gt 0 ]; then
            info "Fix with: chmod +x <script>"
        fi
        if [ $MISSING_ISSUES -gt 0 ]; then
            fail "$MISSING_ISSUES hook script(s) referenced in settings.json but missing from disk"
        fi
    else
        # Fallback: static list when jq unavailable
        HOOK_SCRIPTS=(
            "$CLAUDE_DIR/hooks/ctm/ctm-session-start.sh"
            "$CLAUDE_DIR/hooks/ctm/ctm-pre-compact.sh"
            "$CLAUDE_DIR/hooks/ctm/ctm-session-end.sh"
            "$CLAUDE_DIR/hooks/ctm/ctm-user-prompt.sh"
            "$CLAUDE_DIR/hooks/save-conversation.sh"
            "$CLAUDE_DIR/hooks/rag-index-on-write.sh"
            "$CLAUDE_DIR/hooks/context-preflight.sh"
        )

        for script in "${HOOK_SCRIPTS[@]}"; do
            if [ -x "$script" ]; then
                pass "Hook script executable: $(basename "$script")"
            elif [ -f "$script" ]; then
                warn "Hook script not executable: $(basename "$script")"
            else
                warn "Hook script missing: $(basename "$script")"
            fi
        done
        warn "Install jq for dynamic hook validation from settings.json"
    fi
}

# ============================================================================
# 4. CTM VALIDATION
# ============================================================================
validate_ctm() {
    print_section "CTM (Cognitive Task Manager)"

    CTM_DIR="$CLAUDE_DIR/ctm"

    if [ ! -d "$CTM_DIR" ]; then
        fail "CTM directory not found"
        return
    fi

    # Check required files
    CTM_FILES=("config.json" "index.json" "scheduler.json")
    for file in "${CTM_FILES[@]}"; do
        if [ -f "$CTM_DIR/$file" ]; then
            pass "CTM file exists: $file"
        else
            warn "CTM file missing: $file"
        fi
    done

    # Check CTM script
    if [ -x "$CTM_DIR/scripts/ctm" ]; then
        pass "CTM CLI executable"
    else
        fail "CTM CLI not executable or missing"
    fi

    # Check agent count
    AGENT_COUNT=$(ls "$CTM_DIR/agents/"*.json 2>/dev/null | wc -l | tr -d ' ')
    info "CTM has $AGENT_COUNT task agents"
}

# ============================================================================
# 5. RAG VALIDATION
# ============================================================================
validate_rag() {
    print_section "RAG System"

    # Check MCP server
    if [ -d "$CLAUDE_DIR/mcp-servers/rag-server" ]; then
        pass "RAG MCP server directory exists"
    else
        warn "RAG MCP server directory not found"
    fi

    # Check Ollama is running
    if pgrep -x "ollama" > /dev/null 2>&1; then
        pass "Ollama is running"
    else
        warn "Ollama not running (RAG won't work)"
    fi

    # Check dashboard
    if curl -s "http://localhost:8420" > /dev/null 2>&1; then
        pass "RAG dashboard accessible at :8420"
    else
        info "RAG dashboard not running (optional)"
    fi
}

# ============================================================================
# 5b. FATHOM MCP SERVER VALIDATION
# ============================================================================
validate_fathom() {
    print_section "Fathom Video MCP Server"

    # Check server directory
    if [ -d "$CLAUDE_DIR/mcp-servers/fathom" ]; then
        pass "Fathom MCP server directory exists"
    else
        info "Fathom MCP server not installed (optional)"
        return
    fi

    # Check venv exists
    if [ -d "$CLAUDE_DIR/mcp-servers/fathom/.venv" ]; then
        pass "Fathom Python venv exists"
    else
        warn "Fathom venv missing - run: python3 -m venv ~/.claude/mcp-servers/fathom/.venv"
    fi

    # Check server.py exists
    if [ -f "$CLAUDE_DIR/mcp-servers/fathom/server.py" ]; then
        pass "Fathom server.py exists"
    else
        fail "Fathom server.py missing"
    fi

    # Check mcp package installed
    if "$CLAUDE_DIR/mcp-servers/fathom/.venv/bin/python" -c "import mcp" 2>/dev/null; then
        pass "MCP package installed in Fathom venv"
    else
        warn "MCP package missing - run: ~/.claude/mcp-servers/fathom/.venv/bin/pip install mcp httpx"
    fi

    # Check README exists
    if [ -f "$CLAUDE_DIR/mcp-servers/fathom/README.md" ]; then
        pass "Fathom README.md exists"
    else
        info "Fathom README.md missing (recommended)"
    fi
}

# ============================================================================
# 6. DOCUMENTATION VALIDATION
# ============================================================================
validate_docs() {
    print_section "Documentation"

    REQUIRED_DOCS=(
        "CLAUDE.md"
        "AGENT_STANDARDS.md"
        "CTM_GUIDE.md"
        "CDP_PROTOCOL.md"
        "AGENT_CONTEXT_PROTOCOL.md"
        "RAG_GUIDE.md"
    )

    for doc in "${REQUIRED_DOCS[@]}"; do
        if [ -f "$CLAUDE_DIR/$doc" ]; then
            pass "Doc exists: $doc"
        else
            warn "Doc missing: $doc"
        fi
    done

    # Check cross-references
    DOCS_WITH_CROSSREF=0
    CROSSREF_DOCS=("CTM_GUIDE.md" "CDP_PROTOCOL.md" "AGENT_CONTEXT_PROTOCOL.md" "RAG_GUIDE.md")
    for doc in "${CROSSREF_DOCS[@]}"; do
        if grep -q "## Cross-References" "$CLAUDE_DIR/$doc" 2>/dev/null; then
            ((DOCS_WITH_CROSSREF++))
        fi
    done

    if [ "$DOCS_WITH_CROSSREF" -eq ${#CROSSREF_DOCS[@]} ]; then
        pass "All system docs have cross-references"
    else
        warn "Only $DOCS_WITH_CROSSREF/${#CROSSREF_DOCS[@]} system docs have cross-references"
    fi
}

# ============================================================================
# 7. INVENTORY VALIDATION
# ============================================================================
validate_inventory() {
    print_section "Inventory Manifest"

    INVENTORY_FILE="$CLAUDE_DIR/inventory.json"

    if [ ! -f "$INVENTORY_FILE" ]; then
        warn "inventory.json not found - run: ~/.claude/scripts/generate-inventory.sh"
        return
    fi

    # Check freshness (should be regenerated within 24h)
    INVENTORY_AGE=$(( ($(date +%s) - $(stat -f %m "$INVENTORY_FILE")) / 3600 ))
    if [ "$INVENTORY_AGE" -lt 24 ]; then
        pass "inventory.json is fresh (${INVENTORY_AGE}h old)"
    else
        warn "inventory.json is stale (${INVENTORY_AGE}h old) - regenerate with generate-inventory.sh"
    fi

    # Validate counts match actual
    if command -v jq &> /dev/null; then
        INV_AGENTS=$(jq -r '.counts.agents' "$INVENTORY_FILE" 2>/dev/null || echo "0")
        INV_SKILLS=$(jq -r '.counts.skills' "$INVENTORY_FILE" 2>/dev/null || echo "0")
        INV_HOOKS=$(jq -r '.counts.hooks' "$INVENTORY_FILE" 2>/dev/null || echo "0")

        ACTUAL_AGENTS=$(ls "$CLAUDE_DIR/agents/"*.md 2>/dev/null | wc -l | tr -d ' ')
        ACTUAL_SKILLS=$(find "$CLAUDE_DIR/skills" -name "SKILL.md" -type f 2>/dev/null | wc -l | tr -d ' ')
        ACTUAL_HOOKS=$(find "$CLAUDE_DIR/hooks" -name "*.sh" -type f 2>/dev/null | wc -l | tr -d ' ')

        if [ "$INV_AGENTS" -eq "$ACTUAL_AGENTS" ] && [ "$INV_SKILLS" -eq "$ACTUAL_SKILLS" ]; then
            pass "Inventory counts match: $INV_AGENTS agents, $INV_SKILLS skills, $INV_HOOKS hooks"
        else
            warn "Inventory drift detected!"
            info "  Agents: inventory=$INV_AGENTS actual=$ACTUAL_AGENTS"
            info "  Skills: inventory=$INV_SKILLS actual=$ACTUAL_SKILLS"
            info "  Hooks:  inventory=$INV_HOOKS actual=$ACTUAL_HOOKS"
        fi

        # Check CONFIGURATION_GUIDE matches inventory
        CONFIG_GUIDE="$CLAUDE_DIR/CONFIGURATION_GUIDE.md"
        if [ -f "$CONFIG_GUIDE" ]; then
            GUIDE_AGENTS=$(grep -o '[0-9]* Agents' "$CONFIG_GUIDE" 2>/dev/null | head -1 | grep -o '[0-9]*' || echo "0")
            if [ "$GUIDE_AGENTS" -eq "$INV_AGENTS" ]; then
                pass "CONFIGURATION_GUIDE matches inventory ($GUIDE_AGENTS agents)"
            else
                fail "CONFIGURATION_GUIDE mismatch: $GUIDE_AGENTS vs inventory $INV_AGENTS"
            fi
        fi

        # Show model distribution
        HAIKU=$(jq -r '.model_distribution.haiku' "$INVENTORY_FILE" 2>/dev/null || echo "0")
        SONNET=$(jq -r '.model_distribution.sonnet' "$INVENTORY_FILE" 2>/dev/null || echo "0")
        OPUS=$(jq -r '.model_distribution.opus' "$INVENTORY_FILE" 2>/dev/null || echo "0")
        info "Model distribution: haiku=$HAIKU sonnet=$SONNET opus=$OPUS"
    else
        warn "jq not installed - cannot validate inventory contents"
    fi
}

# ============================================================================
# 8. PERMISSIONS VALIDATION
# ============================================================================
validate_permissions() {
    print_section "Permissions"

    SETTINGS_LOCAL="$CLAUDE_DIR/settings.local.json"

    if [ ! -f "$SETTINGS_LOCAL" ]; then
        info "settings.local.json not found (using defaults)"
        return
    fi

    if command -v jq &> /dev/null; then
        PERM_COUNT=$(jq -r '.permissions.allow | length' "$SETTINGS_LOCAL" 2>/dev/null || echo "0")

        if [ "$PERM_COUNT" -lt 100 ]; then
            pass "Permissions manageable: $PERM_COUNT entries"
        elif [ "$PERM_COUNT" -lt 200 ]; then
            warn "Permissions sprawling: $PERM_COUNT entries (consider cleanup)"
        else
            fail "Permissions bloated: $PERM_COUNT entries (audit recommended)"
        fi

        # Check for dangerous patterns
        DANGEROUS_PATTERNS=("rm -rf" "sudo" "chmod 777" "> /dev/" "mkfs")
        for pattern in "${DANGEROUS_PATTERNS[@]}"; do
            if jq -r '.permissions.allow[]' "$SETTINGS_LOCAL" 2>/dev/null | grep -q "$pattern"; then
                warn "Dangerous permission pattern found: $pattern"
            fi
        done
    fi
}

# ============================================================================
# 9. PLUGINS VALIDATION
# ============================================================================
validate_plugins() {
    print_section "Plugins"

    PLUGINS_DIR="$CLAUDE_DIR/plugins"

    if [ -d "$PLUGINS_DIR" ]; then
        # Count enabled plugins from settings
        ENABLED=$(grep -c '"true"' "$CLAUDE_DIR/settings.json" 2>/dev/null | head -1 || echo "0")
        info "Plugins directory exists"

        # List marketplace plugins
        if [ -d "$PLUGINS_DIR/marketplaces" ]; then
            MARKETPLACE_COUNT=$(ls -d "$PLUGINS_DIR/marketplaces/"*/ 2>/dev/null | wc -l | tr -d ' ')
            pass "$MARKETPLACE_COUNT marketplace(s) installed"
        fi

        # Count cached plugins (actual installed)
        if [ -d "$PLUGINS_DIR/cache" ]; then
            CACHED_PLUGINS=0
            SUB_SKILLS=0
            for marketplace in "$PLUGINS_DIR/cache/"*/; do
                if [ -d "$marketplace" ]; then
                    for plugin in "$marketplace"*/; do
                        if [ -d "$plugin" ]; then
                            ((CACHED_PLUGINS++))
                            # Count sub-skills
                            if [ -d "${plugin}skills" ]; then
                                SUB_COUNT=$(ls -d "${plugin}skills/"*/ 2>/dev/null | wc -l | tr -d ' ')
                                SUB_SKILLS=$((SUB_SKILLS + SUB_COUNT))
                            fi
                        fi
                    done
                fi
            done
            pass "$CACHED_PLUGINS plugin(s) cached with $SUB_SKILLS sub-skills"
        fi
    else
        info "No plugins directory"
    fi
}

# ============================================================================
# 10. LESSONS SYSTEM VALIDATION
# ============================================================================
validate_lessons() {
    print_section "Lessons System"

    LESSONS_DIR="$CLAUDE_DIR/lessons"

    if [ ! -d "$LESSONS_DIR" ]; then
        warn "Lessons directory not found"
        return
    fi

    pass "Lessons directory exists"

    # Check lessons.jsonl
    if [ -f "$LESSONS_DIR/lessons.jsonl" ]; then
        APPROVED_COUNT=$(wc -l < "$LESSONS_DIR/lessons.jsonl" | tr -d ' ')
        pass "$APPROVED_COUNT approved lessons"
    else
        info "No approved lessons yet"
    fi

    # Check pending lessons
    if [ -d "$LESSONS_DIR/review" ]; then
        PENDING_COUNT=$(ls "$LESSONS_DIR/review/"*.json 2>/dev/null | wc -l | tr -d ' ')
        if [ "$PENDING_COUNT" -gt 0 ]; then
            info "$PENDING_COUNT lesson(s) pending review"
        else
            pass "No pending reviews"
        fi
    fi

    # Check extraction pipeline
    if [ -f "$CLAUDE_DIR/hooks/lesson-surfacer.sh" ]; then
        if [ -x "$CLAUDE_DIR/hooks/lesson-surfacer.sh" ]; then
            pass "Lesson surfacing hook executable"
        else
            warn "Lesson surfacing hook not executable"
        fi
    else
        warn "Lesson surfacing hook missing"
    fi

    # Check RAG index for lessons
    if [ -d "$LESSONS_DIR/.rag" ]; then
        pass "Lessons RAG indexed"
    else
        info "Lessons not RAG indexed (optional)"
    fi
}

# ============================================================================
# 11. STATUSLINE VALIDATION
# ============================================================================
validate_statusline() {
    print_section "StatusLine"

    if grep -q '"statusLine"' "$CLAUDE_DIR/settings.json" 2>/dev/null; then
        pass "StatusLine configured in settings.json"

        # Check if statusline script exists
        if [ -f "$CLAUDE_DIR/statusline.sh" ]; then
            if [ -x "$CLAUDE_DIR/statusline.sh" ]; then
                pass "statusline.sh executable"
            else
                warn "statusline.sh not executable"
            fi
        else
            info "Using inline statusLine command"
        fi
    else
        info "StatusLine not configured (optional)"
    fi
}

# ============================================================================
# 12. ADVANCED FEATURES VALIDATION
# ============================================================================
validate_advanced() {
    print_section "Advanced Features"

    # Token delegation agents
    if [ -f "$CLAUDE_DIR/agents/codex-delegate.md" ]; then
        pass "codex-delegate agent exists"
    else
        info "codex-delegate not installed"
    fi

    if [ -f "$CLAUDE_DIR/agents/gemini-delegate.md" ]; then
        pass "gemini-delegate agent exists"
    else
        info "gemini-delegate not installed"
    fi

    # Reasoning duo
    if [ -f "$CLAUDE_DIR/agents/reasoning-duo.md" ]; then
        pass "reasoning-duo agent exists"
    else
        info "reasoning-duo not installed"
    fi

    # Git integration
    if [ -f "$CLAUDE_DIR/hooks/git-post-commit-rag.sh" ]; then
        if [ -x "$CLAUDE_DIR/hooks/git-post-commit-rag.sh" ]; then
            pass "Git-RAG integration configured"
        else
            warn "git-post-commit-rag.sh not executable"
        fi
    else
        info "Git-RAG integration not configured"
    fi

    # CDP/ACP protocols
    if [ -f "$CLAUDE_DIR/CDP_PROTOCOL.md" ] && [ -f "$CLAUDE_DIR/AGENT_CONTEXT_PROTOCOL.md" ]; then
        pass "CDP and ACP protocols documented"
    elif [ -f "$CLAUDE_DIR/CDP_PROTOCOL.md" ]; then
        pass "CDP protocol documented"
    else
        info "Delegation protocols not documented"
    fi

    # Brand extraction
    if [ -f "$CLAUDE_DIR/agents/brand-kit-extractor.md" ]; then
        pass "Brand extraction pipeline available"
    else
        info "Brand extraction not installed"
    fi
}

# ============================================================================
# 13. RESOURCE MANAGEMENT VALIDATION (NEW v3.1)
# ============================================================================
validate_resource_management() {
    print_section "Resource Management"

    # Machine profile
    if [ -f "$CLAUDE_DIR/machine-profile.json" ]; then
        FINGERPRINT=$(jq -r '.hardware.fingerprint // empty' "$CLAUDE_DIR/machine-profile.json" 2>/dev/null)
        CHIP=$(jq -r '.hardware.chip // "unknown"' "$CLAUDE_DIR/machine-profile.json" 2>/dev/null)
        PROFILE=$(jq -r '.active_profile // "balanced"' "$CLAUDE_DIR/machine-profile.json" 2>/dev/null)
        if [ -n "$FINGERPRINT" ]; then
            pass "Machine profile: $CHIP [$PROFILE]"
        else
            warn "Machine profile exists but missing fingerprint"
        fi
    else
        warn "Machine profile not found (run: detect-device.sh --generate)"
    fi

    # Device detection hook
    if grep -q "device-check.sh" "$CLAUDE_DIR/settings.json" 2>/dev/null; then
        pass "Device detection hook in SessionStart"
    else
        info "Device detection hook not configured"
    fi

    # Profile scripts
    local SCRIPTS_OK=0
    if [ -x "$CLAUDE_DIR/scripts/check-load.sh" ]; then
        ((SCRIPTS_OK++))
    fi
    if [ -x "$CLAUDE_DIR/scripts/switch-profile.sh" ]; then
        ((SCRIPTS_OK++))
    fi
    if [ -x "$CLAUDE_DIR/scripts/detect-device.sh" ]; then
        ((SCRIPTS_OK++))
    fi

    if [ $SCRIPTS_OK -eq 3 ]; then
        pass "All resource scripts executable (3/3)"
    elif [ $SCRIPTS_OK -gt 0 ]; then
        warn "Some resource scripts missing ($SCRIPTS_OK/3)"
    else
        info "Resource management scripts not installed"
    fi

    # Ollama config
    if [ -f "$HOME/.ollama/ollama.env" ]; then
        pass "Ollama environment config exists"
    else
        info "Ollama config not found (~/.ollama/ollama.env)"
    fi

    # Current load status (informational)
    if [ -x "$CLAUDE_DIR/scripts/check-load.sh" ]; then
        LOAD_STATUS=$("$CLAUDE_DIR/scripts/check-load.sh" --status-only 2>/dev/null || echo "UNKNOWN")
        case "$LOAD_STATUS" in
            OK)
                pass "Current system load: OK"
                ;;
            CAUTION)
                info "Current system load: CAUTION"
                ;;
            HIGH_LOAD)
                warn "Current system load: HIGH_LOAD"
                ;;
            *)
                info "Could not determine system load"
                ;;
        esac
    fi
}

# ============================================================================
# 14. MCP SERVERS VALIDATION (expanded)
# ============================================================================
validate_mcp_servers() {
    print_section "MCP Servers"

    MCP_DIR="$CLAUDE_DIR/mcp-servers"

    # RAG server
    if [ -d "$MCP_DIR/rag-server" ]; then
        pass "RAG MCP server installed"
        # Check both settings.json and settings.local.json (enabledMcpjsonServers)
        if grep -q '"rag-server"' "$CLAUDE_DIR/settings.json" 2>/dev/null || \
           grep -q '"rag-server"' "$CLAUDE_DIR/settings.local.json" 2>/dev/null; then
            pass "RAG server configured in settings"
        else
            warn "RAG server not in settings.json"
        fi
    else
        warn "RAG MCP server not installed"
    fi

    # Fathom
    if [ -d "$MCP_DIR/fathom" ]; then
        pass "Fathom MCP server installed"
    else
        info "Fathom MCP server not installed (optional)"
    fi

    # GitHub (check settings)
    if grep -q '"github"' "$CLAUDE_DIR/settings.json" 2>/dev/null; then
        pass "GitHub MCP server configured"
    else
        info "GitHub MCP server not configured (optional)"
    fi
}

# ============================================================================
# QUICK VALIDATION (for SessionStart hook)
# ============================================================================
quick_validate() {
    QUICK_ISSUES=()

    # 1. Agent count sanity check
    AGENT_COUNT=$(ls "$CLAUDE_DIR/agents/"*.md 2>/dev/null | wc -l | tr -d ' ')
    if [ "$AGENT_COUNT" -lt 10 ]; then
        QUICK_ISSUES+=("Low agent count: only $AGENT_COUNT agents found")
    fi

    # 2. Ollama running (if RAG likely used)
    if [ -d "$CLAUDE_DIR/mcp-servers/rag-server" ]; then
        if ! pgrep -x "ollama" > /dev/null 2>&1; then
            QUICK_ISSUES+=("Ollama not running")
        fi
    fi

    # 3. CTM index exists
    if [ ! -f "$CLAUDE_DIR/ctm/index.json" ]; then
        QUICK_ISSUES+=("CTM not initialized")
    fi

    # 4. Inventory drift (if inventory.json exists)
    if [ -f "$CLAUDE_DIR/inventory.json" ]; then
        INV_AGENTS=$(jq -r '.counts.agents' "$CLAUDE_DIR/inventory.json" 2>/dev/null || echo "0")
        if [ "$AGENT_COUNT" != "$INV_AGENTS" ]; then
            QUICK_ISSUES+=("Inventory stale: $AGENT_COUNT agents vs $INV_AGENTS in inventory")
        fi
    fi

    # 5. Critical hooks executable
    if [ -f "$CLAUDE_DIR/hooks/context-preflight.sh" ] && [ ! -x "$CLAUDE_DIR/hooks/context-preflight.sh" ]; then
        QUICK_ISSUES+=("context-preflight.sh not executable")
    fi

    # Output
    if [ ${#QUICK_ISSUES[@]} -eq 0 ]; then
        echo "[Health] ✓ All systems OK"
        exit 0
    else
        echo "[Health] ⚠ Issues detected:"
        for issue in "${QUICK_ISSUES[@]}"; do
            echo "  • $issue"
        done
        echo "  Run: ~/.claude/scripts/validate-setup.sh"
        exit 1
    fi
}

# ============================================================================
# 13. CONFIGURATION CHAIN VALIDATION
# ============================================================================
validate_config_chain() {
    print_section "Configuration Chain"

    # Run the audit script in quick mode
    if [ -x "$CLAUDE_DIR/scripts/audit-config-chain.sh" ]; then
        # Capture output
        AUDIT_OUTPUT=$("$CLAUDE_DIR/scripts/audit-config-chain.sh" --quick 2>&1 || true)

        # Parse results
        AUDIT_CRITICAL=$(echo "$AUDIT_OUTPUT" | grep -c "CRITICAL:" 2>/dev/null || echo "0")
        AUDIT_CRITICAL=$(echo "$AUDIT_CRITICAL" | head -1 | tr -d ' \n')
        AUDIT_WARNINGS=$(echo "$AUDIT_OUTPUT" | grep -c "WARNING:" 2>/dev/null || echo "0")
        AUDIT_WARNINGS=$(echo "$AUDIT_WARNINGS" | head -1 | tr -d ' \n')

        if [ "$AUDIT_CRITICAL" -gt 0 ] 2>/dev/null; then
            fail "Configuration audit found $AUDIT_CRITICAL critical issue(s)"
            ((ERRORS += AUDIT_CRITICAL))
        else
            pass "No critical configuration issues"
        fi

        if [ "$AUDIT_WARNINGS" -gt 0 ] 2>/dev/null; then
            warn "Configuration audit found $AUDIT_WARNINGS warning(s)"
            info "Run: ~/.claude/scripts/audit-config-chain.sh for details"
        fi

        # Check import validation
        if [ -x "$CLAUDE_DIR/scripts/validate-imports.sh" ]; then
            IMPORT_OUTPUT=$("$CLAUDE_DIR/scripts/validate-imports.sh" "$PWD" 2>&1 || true)
            BROKEN_IMPORTS=$(echo "$IMPORT_OUTPUT" | grep -c "NOT FOUND" 2>/dev/null || echo "0")
            BROKEN_IMPORTS=$(echo "$BROKEN_IMPORTS" | head -1 | tr -d ' \n')

            if [ "$BROKEN_IMPORTS" -gt 0 ] 2>/dev/null; then
                warn "$BROKEN_IMPORTS broken import(s) detected"
            else
                pass "All @imports resolve correctly"
            fi
        else
            info "Import validator not available"
        fi
    else
        info "audit-config-chain.sh not available"
    fi
}

# ============================================================================
# MAIN
# ============================================================================

# Quick mode for hooks
if [ "$QUICK_MODE" = true ]; then
    quick_validate
    exit 0
fi

print_header "Claude Code Setup Validator v2.0"
echo "  Checking: $CLAUDE_DIR"
echo "  Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "  Scoring: Holistic 10-category system"

# Core Infrastructure
validate_agents
validate_skills
validate_docs
validate_config_chain

# Memory Systems
validate_ctm
validate_rag
validate_lessons

# Automation
validate_hooks
validate_statusline

# MCP & Advanced
validate_mcp_servers
validate_advanced

# System Health
validate_inventory
validate_permissions
validate_plugins
validate_resource_management

# Summary
print_header "Summary"
echo ""
echo -e "  ${GREEN}Passed:${NC}   $PASSED"
echo -e "  ${YELLOW}Warnings:${NC} $WARNINGS"
echo -e "  ${RED}Errors:${NC}   $ERRORS"
echo ""

if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}${BOLD}Some checks failed. Review errors above.${NC}"
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}${BOLD}Setup valid with warnings.${NC}"
    exit 0
else
    echo -e "${GREEN}${BOLD}All checks passed!${NC}"
    exit 0
fi
