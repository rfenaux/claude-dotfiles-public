#!/usr/bin/env bash
# config-change-monitor.sh - Log config changes for audit trail (ConfigChange hook, v2.1.49)
# Detects config drift/corruption during sessions

source ~/.claude/hooks/lib/circuit-breaker.sh 2>/dev/null || true
check_circuit "config-change-monitor" 2>/dev/null || exit 0

input=$(cat)
changed_file=$(echo "$input" | jq -r '.file // "unknown"' 2>/dev/null)

log_dir="$HOME/.claude/logs"
mkdir -p "$log_dir"
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Config changed: $changed_file" >> "$log_dir/config-changes.log"

echo "{}"
