#!/bin/bash
# SessionStart hook: Quick config health check
# Runs audit-config-chain.sh --quick and reports summary

# Run quick audit
audit_output=$("$HOME/.claude/scripts/audit-config-chain.sh" --quick 2>/dev/null)

# Extract metrics
health_score=$(echo "$audit_output" | grep -o 'Health Score: [0-9]*' | grep -o '[0-9]*')
criticals=$(echo "$audit_output" | grep -o 'Critical: [0-9]*' | grep -o '[0-9]*')
warnings=$(echo "$audit_output" | grep -o 'Warnings: [0-9]*' | grep -o '[0-9]*')

# Default values
health_score=${health_score:-100}
criticals=${criticals:-0}
warnings=${warnings:-0}

# Color output based on health
if [ "$health_score" -ge 90 ]; then
    status="✓"
    color="\033[32m"  # Green
elif [ "$health_score" -ge 70 ]; then
    status="⚠"
    color="\033[33m"  # Yellow
else
    status="✗"
    color="\033[31m"  # Red
fi

reset="\033[0m"

# Always output summary (concise for context)
echo -e "[Config Health] ${color}${health_score}/100 ${status}${reset}"

# Only show details if issues exist
if [ "$criticals" -gt 0 ] || [ "$warnings" -gt 0 ]; then
    echo "  Critical: $criticals | Warnings: $warnings"

    # Show first few issues
    echo "$audit_output" | grep -E "^(Critical|Warning):" | head -3 | sed 's/^/  /'

    echo "  Run '/audit' for full report"
fi

exit 0
