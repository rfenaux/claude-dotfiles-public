#!/bin/bash
# Add self-improvement capability to agents
# Usage: ./add-self-improvement.sh [--dry-run] [agent-name|all]

set -e

AGENTS_DIR="$HOME/.claude/agents"
DRY_RUN=false
TARGET="all"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            TARGET="$1"
            shift
            ;;
    esac
done

# Self-improvement frontmatter to add (after existing tools line or before ---)
FRONTMATTER_ADDITION='self_improving: true
config_file: ~/.claude/agents/AGENT_NAME.md'

# Learned patterns section template
LEARNED_PATTERNS_SECTION='
---

## Learned Patterns

> This section is populated by the agent as it learns.
> See `~/.claude/AGENT_STANDARDS.md` Section 14 for self-improvement protocol.

### Discovered Optimizations

<!--
#### [YYYY-MM-DD] - [Title]
**Discovery:** What was found
**Old approach:** Previous method
**New approach:** Improved method
**Impact:** Speed/reliability/accuracy improvement
-->

*No optimizations discovered yet.*

### Known Shortcuts

*No shortcuts discovered yet.*'

update_agent() {
    local agent_file="$1"
    local agent_name=$(basename "$agent_file" .md)

    # Check if already has self_improving
    if grep -q "self_improving:" "$agent_file"; then
        echo "  ⏭️  $agent_name - already has self_improving"
        return 0
    fi

    # Check if has frontmatter
    if ! head -1 "$agent_file" | grep -q "^---$"; then
        echo "  ⚠️  $agent_name - no frontmatter, skipping"
        return 0
    fi

    if $DRY_RUN; then
        echo "  🔍 $agent_name - would add self-improvement"
        return 0
    fi

    # Create temp file
    local tmp_file=$(mktemp)

    # Add self_improving to frontmatter (before closing ---)
    # Also ensure Write and Edit tools are in tools list
    awk -v agent="$agent_name" '
    /^---$/ && NR > 1 && !added {
        print "self_improving: true"
        print "config_file: ~/.claude/agents/" agent ".md"
        added = 1
    }
    { print }
    ' "$agent_file" > "$tmp_file"

    # Check if Learned Patterns section exists
    if ! grep -q "## Learned Patterns" "$tmp_file"; then
        # Add at end of file
        echo "$LEARNED_PATTERNS_SECTION" >> "$tmp_file"
    fi

    # Replace original
    mv "$tmp_file" "$agent_file"

    echo "  ✅ $agent_name - updated"
}

echo "🔧 Adding self-improvement capability to agents"
echo "   Directory: $AGENTS_DIR"
echo "   Target: $TARGET"
echo "   Dry run: $DRY_RUN"
echo ""

if [[ "$TARGET" == "all" ]]; then
    count=0
    for agent_file in "$AGENTS_DIR"/*.md; do
        update_agent "$agent_file"
        ((count++))
    done
    echo ""
    echo "Processed $count agents"
else
    agent_file="$AGENTS_DIR/$TARGET.md"
    if [[ -f "$agent_file" ]]; then
        update_agent "$agent_file"
    else
        echo "❌ Agent not found: $TARGET"
        exit 1
    fi
fi

if $DRY_RUN; then
    echo ""
    echo "This was a dry run. Run without --dry-run to apply changes."
fi
