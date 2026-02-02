#!/bin/bash
# assumption-validator.sh - Surface assumptions before multi-step tasks
#
# Triggered by: PreToolUse hook on "Task" (agent spawning)
# Injects context reminding Claude to validate assumptions
#
# Purpose: Catch misunderstandings early, before spawning agents that
# may do significant work based on wrong assumptions.

# Read hook input from stdin
HOOK_INPUT=$(cat)
TOOL_NAME=$(echo "$HOOK_INPUT" | jq -r '.tool_name // empty')
TOOL_INPUT=$(echo "$HOOK_INPUT" | jq -r '.tool_input // empty')

# Only trigger on Task tool (agent spawning)
[ "$TOOL_NAME" != "Task" ] && exit 0

# Extract task description from tool input
TASK_DESC=$(echo "$TOOL_INPUT" | jq -r '.prompt // .description // empty' 2>/dev/null)
[ -z "$TASK_DESC" ] && exit 0

# ============================================
# DETECT TASK COMPLEXITY/RISK LEVEL
# ============================================

TASK_LOWER=$(echo "$TASK_DESC" | tr '[:upper:]' '[:lower:]')
RISK_LEVEL="low"
ASSUMPTIONS=""

# Multi-file indicators
if echo "$TASK_LOWER" | grep -qE "(all files|multiple files|across|everywhere|entire|whole|refactor|migrate|overhaul)"; then
    RISK_LEVEL="high"
    ASSUMPTIONS="extensive scope (multiple files)"
fi

# Production indicators
if echo "$TASK_LOWER" | grep -qE "(production|prod|live|deploy|publish|release)"; then
    RISK_LEVEL="high"
    if [ -n "$ASSUMPTIONS" ]; then
        ASSUMPTIONS="$ASSUMPTIONS, production environment"
    else
        ASSUMPTIONS="production environment"
    fi
fi

# Destructive indicators
if echo "$TASK_LOWER" | grep -qE "(delete|remove|drop|clean|clear|reset|wipe)"; then
    RISK_LEVEL="high"
    if [ -n "$ASSUMPTIONS" ]; then
        ASSUMPTIONS="$ASSUMPTIONS, destructive action"
    else
        ASSUMPTIONS="destructive action"
    fi
fi

# Integration indicators
if echo "$TASK_LOWER" | grep -qE "(integration|sync|connect|api|webhook|external)"; then
    RISK_LEVEL="medium"
    if [ -n "$ASSUMPTIONS" ]; then
        ASSUMPTIONS="$ASSUMPTIONS, external system involvement"
    else
        ASSUMPTIONS="external system involvement"
    fi
fi

# Skip low-risk tasks (no extra context needed)
[ "$RISK_LEVEL" = "low" ] && exit 0

# ============================================
# INJECT PREFLIGHT CHECK CONTEXT
# ============================================

# Load recent decisions if available
DECISIONS_HINT=""
if [ -f "$HOME/.claude/ctm/context/decisions.json" ]; then
    RECENT=$(jq -r '.decisions[-1].summary // empty' "$HOME/.claude/ctm/context/decisions.json" 2>/dev/null)
    if [ -n "$RECENT" ]; then
        DECISIONS_HINT="Recent decision: $RECENT"
    fi
fi

# Output preflight context
cat << EOF
<preflight-check>
## Pre-Flight Assumptions (auto-detected)

Before proceeding with this ${RISK_LEVEL}-complexity task, verify:
- **Scope:** ${ASSUMPTIONS:-minimal changes}
- **Target:** Confirm correct environment/files
${DECISIONS_HINT:+- **Context:** $DECISIONS_HINT}

If any assumption is wrong, clarify before executing.
</preflight-check>
EOF

exit 0
