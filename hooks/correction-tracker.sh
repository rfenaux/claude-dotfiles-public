#!/bin/bash
# correction-tracker.sh - Capture user corrections for learning
#
# Triggered by: UserPromptSubmit hook
# Writes to: ~/.claude/correction-history.jsonl
#
# Detects when Raphael corrects Claude and logs the pattern for:
# 1. Enhanced session briefings (recent mistakes to avoid)
# 2. Periodic extraction to lessons system

set -e

# Read hook input from stdin
HOOK_INPUT=$(cat)
USER_MESSAGE=$(echo "$HOOK_INPUT" | jq -r '.user_prompt // empty')
SESSION_ID=$(echo "$HOOK_INPUT" | jq -r '.session_id // empty')

# Skip if no message
[ -z "$USER_MESSAGE" ] || [ "$USER_MESSAGE" = "null" ] && exit 0

# Convert to lowercase for pattern matching
MSG_LOWER=$(echo "$USER_MESSAGE" | tr '[:upper:]' '[:lower:]')

# ============================================
# CORRECTION DETECTION PATTERNS
# ============================================

CORRECTION_TYPE=""
TRIGGER_PHRASE=""

# Strong correction signals (explicit no)
if echo "$MSG_LOWER" | grep -qE "^no[,.]? (that.?s )?(not|wrong|incorrect)"; then
    CORRECTION_TYPE="explicit_rejection"
    TRIGGER_PHRASE="no, that's wrong"
elif echo "$MSG_LOWER" | grep -qE "^no[,.]? (don.?t|do not|stop)"; then
    CORRECTION_TYPE="stop_action"
    TRIGGER_PHRASE="no, don't"
fi

# Redirect signals (actually I meant)
if [ -z "$CORRECTION_TYPE" ]; then
    if echo "$MSG_LOWER" | grep -qE "(^actually|actually,) (i )?(meant|want|need)"; then
        CORRECTION_TYPE="redirect"
        TRIGGER_PHRASE="actually, I meant"
    elif echo "$MSG_LOWER" | grep -qE "^(i said|i asked for|i meant|i wanted)"; then
        CORRECTION_TYPE="clarification"
        TRIGGER_PHRASE="I said/meant"
    fi
fi

# Preference correction
if [ -z "$CORRECTION_TYPE" ]; then
    if echo "$MSG_LOWER" | grep -qE "(not what i|that.?s not|instead,? (do|use|try))"; then
        CORRECTION_TYPE="preference"
        TRIGGER_PHRASE="not what I wanted"
    elif echo "$MSG_LOWER" | grep -qE "(don.?t .*, do|instead of .*, (use|do))"; then
        CORRECTION_TYPE="preference_redirect"
        TRIGGER_PHRASE="don't X, do Y"
    fi
fi

# Error acknowledgment
if [ -z "$CORRECTION_TYPE" ]; then
    if echo "$MSG_LOWER" | grep -qE "(that.?s )?(still )?(broken|wrong|not working|failing)"; then
        CORRECTION_TYPE="error_report"
        TRIGGER_PHRASE="still broken"
    fi
fi

# Skip if no correction detected
[ -z "$CORRECTION_TYPE" ] && exit 0

# ============================================
# LOG CORRECTION
# ============================================

HISTORY_FILE="$HOME/.claude/correction-history.jsonl"
TIMESTAMP=$(date -Iseconds)

# Extract first 200 chars of message as context
MESSAGE_EXCERPT=$(echo "$USER_MESSAGE" | head -c 200 | tr '\n' ' ' | jq -Rs '.')

# Create JSON entry
ENTRY=$(cat << EOF
{
  "timestamp": "$TIMESTAMP",
  "type": "$CORRECTION_TYPE",
  "trigger_phrase": "$TRIGGER_PHRASE",
  "message_excerpt": $MESSAGE_EXCERPT,
  "session_id": "${SESSION_ID:-unknown}",
  "pattern_hint": ""
}
EOF
)

# Append to history (one line)
echo "$ENTRY" | jq -c '.' >> "$HISTORY_FILE"

# Silent success (per Raphael's preferences)
exit 0
