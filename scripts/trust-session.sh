#!/bin/bash
# trust-session.sh - Manage trusted session mode
# Usage: trust-session.sh [on|off|status|log]

set -euo pipefail

# Configuration
LOG_FILE="${HOME}/.claude/logs/trusted-sessions.log"
MARKER_DIR="/tmp"

# Use a stable session identifier:
# 1. CLAUDE_SESSION_ID if available (future-proofing)
# 2. Otherwise use a simple marker (one active trust session at a time)
if [[ -n "${CLAUDE_SESSION_ID:-}" ]]; then
    SESSION_ID="$CLAUDE_SESSION_ID"
    MARKER_FILE="${MARKER_DIR}/claude-trusted-session-${SESSION_ID}"
else
    # Simple mode: single marker file
    SESSION_ID="active"
    MARKER_FILE="${MARKER_DIR}/claude-trusted-session"
fi

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

log_event() {
    local event="$1"
    echo "$(date -Iseconds)|${PWD}|${SESSION_ID}|${event}" >> "$LOG_FILE"
}

cmd_on() {
    if [[ -f "$MARKER_FILE" ]]; then
        echo "⚠️  Trust mode already enabled for this session"
        return 0
    fi

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "⚠️  TRUSTED SESSION MODE"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "This will allow credential handling in THIS session only."
    echo ""
    echo "ALLOWED:"
    echo "  ✓ Receive credentials in chat"
    echo "  ✓ Store in environment variables"
    echo "  ✓ Use in local commands"
    echo ""
    echo "STILL BLOCKED:"
    echo "  ✗ WebFetch with credentials"
    echo "  ✗ External API calls with secrets"
    echo ""
    echo "Session ID: ${SESSION_ID}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "TRUST_CONFIRM_REQUIRED"
}

cmd_confirm() {
    touch "$MARKER_FILE"
    log_event "enabled"
    echo ""
    echo "🔓 [TRUSTED SESSION ENABLED]"
    echo "   Credential handling allowed until session end"
    echo "   Run '/trust off' to disable early"
}

cmd_off() {
    if [[ -f "$MARKER_FILE" ]]; then
        rm "$MARKER_FILE"
        log_event "disabled"
        echo "🔒 [TRUSTED SESSION DISABLED]"
        echo "   Privacy guard re-enabled"
    else
        echo "Trust mode was not enabled"
    fi
}

cmd_status() {
    if [[ -f "$MARKER_FILE" ]]; then
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "🔓 TRUSTED SESSION ACTIVE"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "Credential handling: ENABLED"
        echo "External calls: BLOCKED"
        echo "Session ID: ${SESSION_ID}"
        echo "Marker: ${MARKER_FILE}"
    else
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "🔒 STANDARD MODE"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "Privacy guard: ACTIVE"
    fi
}

cmd_log() {
    if [[ -f "$LOG_FILE" ]]; then
        echo "Recent trust session events:"
        echo ""
        tail -20 "$LOG_FILE" | while IFS='|' read -r ts dir sid event; do
            printf "%-25s %-10s %s\n" "$ts" "$event" "$sid"
        done
    else
        echo "No trust session history"
    fi
}

cmd_cleanup() {
    # Called by SessionEnd hook
    if [[ -f "$MARKER_FILE" ]]; then
        rm "$MARKER_FILE"
        log_event "session_end_cleanup"
    fi
    # Also clean any stale markers (older than 24h)
    find "$MARKER_DIR" -name "claude-trusted-session-*" -mtime +1 -delete 2>/dev/null || true
}

cmd_check() {
    # Silent check - returns 0 if trusted, 1 if not
    [[ -f "$MARKER_FILE" ]]
}

# Main
case "${1:-status}" in
    on)      cmd_on ;;
    confirm) cmd_confirm ;;
    off)     cmd_off ;;
    status)  cmd_status ;;
    log)     cmd_log ;;
    cleanup) cmd_cleanup ;;
    check)   cmd_check ;;
    *)
        echo "Usage: trust-session.sh [on|off|status|log|cleanup|check]"
        exit 1
        ;;
esac
