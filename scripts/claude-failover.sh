#!/bin/bash
# Claude Account Auto-Failover
# Switches to alternate account when rate limited or quota exceeded
#
# Usage: claude-failover [args...]
# Or source this and use: claude-with-failover [args...]

set -euo pipefail

# Account configurations — read from config or use defaults
ACCOUNTS_CONFIG="${CLAUDE_ACCOUNTS_CONFIG:-$HOME/.claude/config/accounts.json}"
if [ -f "$ACCOUNTS_CONFIG" ]; then
    # Read account dirs from JSON config
    mapfile -t ACCOUNTS < <(python3 -c "
import json
accts=json.load(open('$ACCOUNTS_CONFIG'))
for a in accts: print(a.get('config_dir',''))
" 2>/dev/null | grep -v '^$')
fi
# Fallback to primary only if no config
if [ ${#ACCOUNTS[@]} -eq 0 ]; then
    ACCOUNTS=("$HOME/.claude")
fi

# Current account (default to primary)
CURRENT_CONFIG="${CLAUDE_CONFIG_DIR:-${ACCOUNTS[0]}}"

# Rate limit patterns to detect
RATE_LIMIT_PATTERNS=(
    "rate limit"
    "Rate limit"
    "quota exceeded"
    "too many requests"
    "429"
    "capacity"
    "overloaded"
)

# Log file for failover events
FAILOVER_LOG="$HOME/.claude/logs/failover.log"

log_failover() {
    local msg="$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $msg" >> "$FAILOVER_LOG"
    echo "🔄 $msg" >&2
}

get_account_name() {
    local config="$1"
    # Try reading from accounts.json first
    if [ -f "$ACCOUNTS_CONFIG" ]; then
        local name
        name=$(python3 -c "
import json
accts=json.load(open('$ACCOUNTS_CONFIG'))
for a in accts:
    if a.get('config_dir','') and '$config'.endswith(a['config_dir'].replace('~/.claude','').replace('~','')):
        print(a.get('name','')); break
" 2>/dev/null)
        [ -n "$name" ] && echo "$name" && return
    fi
    echo "${CLAUDE_ACCOUNT_NAME:-Primary}"
}

get_next_config() {
    local current="$1"
    local found=false
    for acct in "${ACCOUNTS[@]}"; do
        if $found; then
            echo "$acct"
            return
        fi
        [[ "$acct" == "$current" ]] && found=true
    done
    # Wrap around to first
    echo "${ACCOUNTS[0]}"
}

switch_account() {
    local new_config="$1"
    local old_name=$(get_account_name "$CURRENT_CONFIG")
    local new_name=$(get_account_name "$new_config")

    log_failover "Switching from $old_name to $new_name (rate limit detected)"

    export CLAUDE_CONFIG_DIR="$new_config"
    CURRENT_CONFIG="$new_config"

    # Update shell for subsequent commands
    echo "export CLAUDE_CONFIG_DIR=\"$new_config\"" > "$HOME/.claude/cache/current-account.sh"
}

check_rate_limit() {
    local output="$1"
    for pattern in "${RATE_LIMIT_PATTERNS[@]}"; do
        if echo "$output" | grep -qi "$pattern"; then
            return 0  # Rate limited
        fi
    done
    return 1  # Not rate limited
}

# Main wrapper function
claude_with_failover() {
    local max_retries=${#ACCOUNTS[@]}
    local retry=0

    while [[ $retry -lt $max_retries ]]; do
        # Capture output while also displaying it
        local output
        output=$(CLAUDE_CONFIG_DIR="$CURRENT_CONFIG" claude "$@" 2>&1 | tee /dev/tty) || true

        if check_rate_limit "$output"; then
            local next_config=$(get_next_config "$CURRENT_CONFIG")
            switch_account "$next_config"
            ((retry++))
            log_failover "Retry $retry with $(get_account_name "$CURRENT_CONFIG")"
        else
            return 0
        fi
    done

    log_failover "All accounts rate limited. Try again later."
    return 1
}

# Quick status check
failover_status() {
    echo "=== Claude Failover Status ==="
    echo "Accounts (failover order):"
    for acct in "${ACCOUNTS[@]}"; do
        local marker=""
        [[ "$acct" == "$CURRENT_CONFIG" ]] && marker=" ← active"
        echo "  $(get_account_name "$acct"): $acct$marker"
    done
    echo ""
    if [[ -f "$FAILOVER_LOG" ]]; then
        echo "Recent failover events:"
        tail -5 "$FAILOVER_LOG" 2>/dev/null || echo "  (none)"
    fi
}

# If run directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    case "${1:-}" in
        --status|-s)
            failover_status
            ;;
        --help|-h)
            echo "Usage: claude-failover [--status] [claude args...]"
            echo ""
            echo "Runs Claude with automatic account failover on rate limits."
            echo ""
            echo "Options:"
            echo "  --status, -s   Show failover configuration and recent events"
            echo "  --help, -h     Show this help"
            echo ""
            echo "Environment:"
            echo "  CLAUDE_CONFIG_DIR  Override default account"
            ;;
        *)
            claude_with_failover "$@"
            ;;
    esac
fi
