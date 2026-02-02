#!/bin/bash
# validate-agent-crossrefs.sh - Validate agent cross-references
# Checks: orphan references, missing delegates_to, cyclic delegations

set -e

AGENTS_DIR="$HOME/.claude/agents"
ERRORS=0
WARNINGS=0

# Colors
RED='\033[0;31m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
NC='\033[0m'

error() { echo -e "${RED}ERROR:${NC} $1"; ((ERRORS++)); }
warn() { echo -e "${YELLOW}WARN:${NC} $1"; ((WARNINGS++)); }
pass() { echo -e "${GREEN}PASS:${NC} $1"; }

echo "=== Agent Cross-Reference Validation ==="
echo ""

# Get all agent names
AGENT_NAMES=$(find "$AGENTS_DIR" -name "*.md" -type f -exec basename {} .md \; | sort)

# 1. Check for orphan delegates_to references
echo "1. Checking for orphan delegates_to references..."
orphans_found=0

for agent_file in "$AGENTS_DIR"/*.md; do
    agent_name=$(basename "$agent_file" .md)

    # Extract delegates_to list from frontmatter
    delegates=$(sed -n '/^delegates_to:/,/^[a-z_]*:/p' "$agent_file" 2>/dev/null | grep "^  - " | sed 's/^  - //')

    for delegate in $delegates; do
        if [ ! -f "$AGENTS_DIR/${delegate}.md" ]; then
            error "[$agent_name] delegates_to non-existent agent: $delegate"
            ((orphans_found++))
        fi
    done
done

if [ $orphans_found -eq 0 ]; then
    pass "No orphan delegates_to references"
fi
echo ""

# 2. Check known orchestrators have delegates_to
echo "2. Checking orchestrators have delegates_to..."
orchestrators_checked=0

# Known orchestrators (explicit list - internal delegators only)
# Excludes external delegates, generators, and specialists
KNOWN_ORCHESTRATORS=(
    "hubspot-implementation-runbook"
    "proposal-orchestrator"
    "brand-kit-extractor"
    "reasoning-trio"
    "reasoning-duo"
    "reasoning-duo-cg"
    "reasoning-duo-xg"
    "kb-synthesizer"
    "rag-integration-expert"
)

for agent_name in "${KNOWN_ORCHESTRATORS[@]}"; do
    agent_file="$AGENTS_DIR/${agent_name}.md"
    if [ -f "$agent_file" ]; then
        ((orchestrators_checked++))
        if ! grep -q "^delegates_to:" "$agent_file" 2>/dev/null; then
            warn "[$agent_name] is an orchestrator but missing delegates_to"
        fi
    fi
done

pass "Checked $orchestrators_checked orchestrators"
echo ""

# 3. Check for cyclic delegations
echo "3. Checking for cyclic delegations..."
cycles_found=0

# Build delegation graph and check for cycles
for agent_file in "$AGENTS_DIR"/*.md; do
    agent_name=$(basename "$agent_file" .md)
    delegates=$(sed -n '/^delegates_to:/,/^[a-z_]*:/p' "$agent_file" 2>/dev/null | grep "^  - " | sed 's/^  - //')

    for delegate in $delegates; do
        # Check if delegate delegates back to this agent (direct cycle)
        if [ -f "$AGENTS_DIR/${delegate}.md" ]; then
            if sed -n '/^delegates_to:/,/^[a-z_]*:/p' "$AGENTS_DIR/${delegate}.md" 2>/dev/null | grep -q "^  - $agent_name$"; then
                error "Cyclic delegation: $agent_name <-> $delegate"
                ((cycles_found++))
            fi
        fi
    done
done

if [ $cycles_found -eq 0 ]; then
    pass "No cyclic delegations found"
fi
echo ""

# 4. Summary
echo "=== Summary ==="
total_agents=$(echo "$AGENT_NAMES" | wc -l | tr -d ' ')
agents_with_delegates=$(grep -l "^delegates_to:" "$AGENTS_DIR"/*.md 2>/dev/null | wc -l | tr -d ' ')
agents_with_related=$(grep -l "## Related Agents" "$AGENTS_DIR"/*.md 2>/dev/null | wc -l | tr -d ' ')

echo "Total agents: $total_agents"
echo "Agents with delegates_to: $agents_with_delegates"
echo "Agents with Related Agents: $agents_with_related"
echo ""

if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}FAILED:${NC} $ERRORS errors, $WARNINGS warnings"
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}PASSED:${NC} $WARNINGS warnings"
    exit 0
else
    echo -e "${GREEN}PASSED:${NC} All checks passed"
    exit 0
fi
