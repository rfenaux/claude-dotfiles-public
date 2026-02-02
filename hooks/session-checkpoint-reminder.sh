#!/bin/bash
# session-checkpoint-reminder.sh
# Reminds user to checkpoint at 2h session duration
# Part of Session Health Protocol (PRD-meta-analysis-config-optimizations)

SESSION_MARKER="/tmp/claude-session-start-$$"
REMINDER_FILE="/tmp/claude-checkpoint-reminded-$$"

# Initialize session start time if not exists
if [ ! -f "$SESSION_MARKER" ]; then
    date +%s > "$SESSION_MARKER"
fi

SESSION_START=$(cat "$SESSION_MARKER")
CURRENT_TIME=$(date +%s)
ELAPSED_SECONDS=$((CURRENT_TIME - SESSION_START))
ELAPSED_HOURS=$((ELAPSED_SECONDS / 3600))

# Check if we've already reminded for this threshold
already_reminded() {
    local threshold=$1
    [ -f "$REMINDER_FILE" ] && grep -q "^${threshold}$" "$REMINDER_FILE"
}

mark_reminded() {
    local threshold=$1
    echo "$threshold" >> "$REMINDER_FILE"
}

# 2 hour mark
if [ $ELAPSED_HOURS -ge 2 ] && [ $ELAPSED_HOURS -lt 4 ]; then
    if ! already_reminded 2; then
        mark_reminded 2
        echo "[SESSION HEALTH: 2 hours. Consider /checkpoint]"
    fi
fi

# 4 hour mark
if [ $ELAPSED_HOURS -ge 4 ] && [ $ELAPSED_HOURS -lt 6 ]; then
    if ! already_reminded 4; then
        mark_reminded 4
        echo "[SESSION HEALTH: 4 hours. Checkpoint strongly recommended.]"
    fi
fi

# 6 hour mark
if [ $ELAPSED_HOURS -ge 6 ]; then
    if ! already_reminded 6; then
        mark_reminded 6
        echo "[SESSION HEALTH: 6 hours. Session health declining. Checkpoint or break advised.]"
    fi
fi

exit 0
