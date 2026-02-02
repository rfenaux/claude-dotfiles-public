#!/bin/bash
# enhance-once.sh - Show enhance mode prompt only on first message
# Part of Claude Code 2.1.x Feature Adoption (PRD-claude-code-2.1-feature-adoption)
#
# Uses session marker to avoid per-message overhead

# Get session ID from environment or use PID
SESSION_ID="${CLAUDE_SESSION_ID:-$$}"
MARKER="/tmp/claude-enhance-shown-${SESSION_ID}"

# Check if we've already shown the enhance message this session
if [ -f "$MARKER" ]; then
    # Already shown, exit silently
    exit 0
fi

# First message - show the enhance mode prompt
touch "$MARKER"

echo "[ENHANCE_MODE: ON - Rewrite user prompt for clarity, specificity, edge cases. Present enhanced version, wait for approval (go/yes/original)]"

exit 0
