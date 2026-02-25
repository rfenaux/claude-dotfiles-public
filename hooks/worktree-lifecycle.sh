#!/usr/bin/env bash
set +e  # Never use set -e in hooks — non-zero exits kill the hook
# worktree-lifecycle.sh - Track worktree create/remove events (v2.1.50)
# Audit trail for agent isolation via git worktrees

source ~/.claude/hooks/lib/circuit-breaker.sh 2>/dev/null || true
check_circuit "worktree-lifecycle" 2>/dev/null || exit 0

input=$(cat)
event=$(echo "$input" | jq -r '.hook_event_name // "unknown"' 2>/dev/null)
worktree_path=$(echo "$input" | jq -r '.worktree_path // "unknown"' 2>/dev/null)

log_dir="$HOME/.claude/logs"
mkdir -p "$log_dir"
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Worktree ${event}: $worktree_path" >> "$log_dir/worktree-events.log"

echo "{}"

exit 0
