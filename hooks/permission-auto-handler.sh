#!/bin/bash
set +e  # fail-silent: hooks must not abort on error

# PermissionRequest hook - auto-approve safe tools, auto-deny destructive commands
# Receives JSON on stdin with tool request details

# Read the full JSON input
input=$(cat)

# Extract tool name (with fallback if jq not available)
if command -v jq &>/dev/null; then
    tool=$(echo "$input" | jq -r '.tool // empty')
else
    tool=$(echo "$input" | grep -o '"tool"[[:space:]]*:[[:space:]]*"[^"]*"' | cut -d'"' -f4 || echo "")
fi

# Auto-approve MCP tools for rag-server and dashboard-api
if [[ "$tool" == rag_* ]] || [[ "$tool" == dashboard_* ]]; then
    echo '{"hookSpecificOutput": {"hookEventName": "PermissionRequest", "decision": {"behavior": "allow"}}}'
    exit 0
fi

# Auto-deny destructive Bash commands
if echo "$input" | grep -qE '(rm[[:space:]]+-rf[[:space:]]+/|DROP[[:space:]]+DATABASE|git[[:space:]]+push[[:space:]]+--force.*main|git[[:space:]]+push.*--force.*master)'; then
    echo '{"hookSpecificOutput": {"hookEventName": "PermissionRequest", "decision": {"behavior": "deny", "reason": "Destructive command blocked by auto-handler"}}}'
    exit 0
fi

# Fall through - no output means defer to user
exit 0
