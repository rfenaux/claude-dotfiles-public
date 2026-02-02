#!/bin/bash
# review-agent-drift.sh - Monthly review of agent self-improvement drift
# Usage: ./review-agent-drift.sh [--since YYYY-MM-DD] [--agent agent-name]

set -e

AGENTS_DIR="$HOME/.claude/agents"
SINCE=""
AGENT=""
VERBOSE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --since)
            SINCE="$2"
            shift 2
            ;;
        --agent)
            AGENT="$2"
            shift 2
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--since YYYY-MM-DD] [--agent agent-name] [--verbose]"
            echo ""
            echo "Monthly review of agent self-improvement drift"
            echo ""
            echo "Options:"
            echo "  --since DATE    Show changes since DATE (default: 30 days ago)"
            echo "  --agent NAME    Review specific agent only"
            echo "  --verbose       Show full diffs"
            echo ""
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Default to 30 days ago
if [ -z "$SINCE" ]; then
    SINCE=$(date -v-30d +%Y-%m-%d 2>/dev/null || date -d "30 days ago" +%Y-%m-%d)
fi

echo "=============================================="
echo "  AGENT DRIFT REVIEW"
echo "  Since: $SINCE"
echo "=============================================="
echo ""

# Check if in git repo
cd "$AGENTS_DIR"
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Warning: Agents directory is not in a git repository."
    echo "Drift tracking requires git history."
    echo ""
    echo "Falling back to static analysis..."
    echo ""
fi

# Count agents with learned patterns
echo "=== Agents with Learned Patterns ==="
echo ""

agents_with_patterns=0
agents_with_proposals=0
total_patterns=0
total_proposals=0

if [ -n "$AGENT" ]; then
    files="$AGENT.md"
else
    files="*.md"
fi

for agent_file in $files; do
    if [ ! -f "$agent_file" ]; then
        continue
    fi

    agent_name=$(basename "$agent_file" .md)

    # Count approved patterns (not placeholder text)
    pattern_count=$(grep -c "^#### [0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}" "$agent_file" 2>/dev/null || echo "0")

    # Check for pending proposals
    has_proposals=$(grep -A5 "### Proposed Improvements" "$agent_file" 2>/dev/null | grep -v "No pending proposals" | grep -c "^####" 2>/dev/null || echo "0")

    if [ "$pattern_count" -gt 0 ] || [ "$has_proposals" -gt 0 ]; then
        echo "  $agent_name:"

        if [ "$pattern_count" -gt 0 ]; then
            echo "    Approved patterns: $pattern_count"
            ((agents_with_patterns++))
            ((total_patterns += pattern_count))
        fi

        if [ "$has_proposals" -gt 0 ]; then
            echo "    Pending proposals: $has_proposals"
            ((agents_with_proposals++))
            ((total_proposals += has_proposals))
        fi

        echo ""
    fi
done

if [ "$agents_with_patterns" -eq 0 ] && [ "$agents_with_proposals" -eq 0 ]; then
    echo "  No agents have learned patterns or pending proposals yet."
    echo ""
fi

echo "=== Summary ==="
echo ""
echo "  Agents with approved patterns: $agents_with_patterns"
echo "  Total approved patterns:       $total_patterns"
echo "  Agents with pending proposals: $agents_with_proposals"
echo "  Total pending proposals:       $total_proposals"
echo ""

# Git-based drift analysis (if available)
if git rev-parse --git-dir > /dev/null 2>&1; then
    echo "=== Git Change Analysis (since $SINCE) ==="
    echo ""

    changed_agents=$(git log --since="$SINCE" --name-only --pretty=format: -- "*.md" 2>/dev/null | sort -u | grep -v "^$" || true)

    if [ -z "$changed_agents" ]; then
        echo "  No agent files changed in this period."
    else
        echo "  Modified agents:"
        for agent_file in $changed_agents; do
            if [ -f "$agent_file" ]; then
                commit_count=$(git log --since="$SINCE" --oneline -- "$agent_file" 2>/dev/null | wc -l | tr -d ' ')
                echo "    - $agent_file ($commit_count commits)"

                if $VERBOSE; then
                    echo ""
                    git log --since="$SINCE" --oneline -- "$agent_file" 2>/dev/null | head -5 | sed 's/^/      /'
                    echo ""
                fi
            fi
        done
    fi
    echo ""
fi

# Check for potential conflicts
echo "=== Potential Cross-Agent Conflicts ==="
echo ""

# Look for model preferences that might conflict
opus_agents=$(grep -l "prefer.*opus\|use.*opus" $files 2>/dev/null | xargs -I{} basename {} .md 2>/dev/null || true)
haiku_agents=$(grep -l "prefer.*haiku\|use.*haiku" $files 2>/dev/null | xargs -I{} basename {} .md 2>/dev/null || true)

conflict_found=false

if [ -n "$opus_agents" ] && [ -n "$haiku_agents" ]; then
    echo "  Model preference patterns detected (review for conflicts):"
    echo "    Opus preference: $opus_agents"
    echo "    Haiku preference: $haiku_agents"
    conflict_found=true
fi

if ! $conflict_found; then
    echo "  No obvious cross-agent conflicts detected."
fi
echo ""

# Agents with high pattern counts (potential drift)
echo "=== High Pattern Count (Potential Drift) ==="
echo ""

drift_warning=false
for agent_file in $files; do
    if [ ! -f "$agent_file" ]; then
        continue
    fi

    pattern_count=$(grep -c "^#### [0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}" "$agent_file" 2>/dev/null || echo "0")

    if [ "$pattern_count" -gt 5 ]; then
        agent_name=$(basename "$agent_file" .md)
        echo "  WARNING: $agent_name has $pattern_count patterns - review for drift"
        drift_warning=true
    fi
done

if ! $drift_warning; then
    echo "  No agents with excessive pattern accumulation."
fi
echo ""

echo "=============================================="
echo "  Review complete"
echo "=============================================="
echo ""
echo "Actions:"
echo "  - Review pending proposals: cc improvements review"
echo "  - View specific agent: $0 --agent <name> --verbose"
echo "  - Approve/revert via Command Center: http://localhost:8420"
echo ""
