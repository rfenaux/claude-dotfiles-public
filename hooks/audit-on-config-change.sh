#!/bin/bash
# PostToolUse hook: Quick audit after config changes
# Triggers on Write/Edit to ~/.claude/agents/, ~/.claude/skills/, *CLAUDE.md, settings.json

# Read tool input from stdin
input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // .tool_input.path // ""')

# Exit early if no file path
[ -z "$file_path" ] && exit 0

# Check if file matches config paths
is_config_file=false

case "$file_path" in
    */.claude/agents/*.md)          is_config_file=true ;;
    */.claude/skills/*/SKILL.md)    is_config_file=true ;;
    */.claude/skills/*.md)          is_config_file=true ;;
    */CLAUDE.md)                    is_config_file=true ;;
    */CLAUDE.local.md)              is_config_file=true ;;
    */.claude/settings*.json)       is_config_file=true ;;
    */.claude/hooks/*.sh)           is_config_file=true ;;
esac

# Exit if not a config file
[ "$is_config_file" = "false" ] && exit 0

# Run quick audit silently, only output if issues found
audit_output=$("$HOME/.claude/scripts/audit-config-chain.sh" --quick 2>/dev/null)
health_score=$(echo "$audit_output" | grep -o 'Health Score: [0-9]*' | grep -o '[0-9]*')

# Only report if health score dropped below 90 or there are criticals/warnings
criticals=$(echo "$audit_output" | grep -o 'Critical: [0-9]*' | grep -o '[0-9]*')
warnings=$(echo "$audit_output" | grep -o 'Warnings: [0-9]*' | grep -o '[0-9]*')

if [ "${health_score:-100}" -lt 90 ] || [ "${criticals:-0}" -gt 0 ] || [ "${warnings:-0}" -gt 0 ]; then
    echo "[Config Audit] Health: ${health_score}/100 | Critical: ${criticals:-0} | Warnings: ${warnings:-0}"
    echo "Run '/audit' for details"
fi

# If agent file changed, run cross-reference validation
case "$file_path" in
    */.claude/agents/*.md)
        xref_output=$("$HOME/.claude/scripts/validate-agent-crossrefs.sh" 2>/dev/null)
        xref_errors=$(echo "$xref_output" | grep -c "ERROR:" || true)
        xref_warnings=$(echo "$xref_output" | grep -c "WARN:" || true)
        if [ "${xref_errors:-0}" -gt 0 ]; then
            echo "[Agent X-Ref] Errors: $xref_errors - check delegates_to references"
        elif [ "${xref_warnings:-0}" -gt 0 ]; then
            echo "[Agent X-Ref] Warnings: $xref_warnings"
        fi
        ;;
esac

exit 0
