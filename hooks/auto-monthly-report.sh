#!/usr/bin/env bash
# auto-monthly-report.sh - Auto-trigger monthly health report
# Hook: SessionStart, once: true
# Rate limit: max 1 per day, only runs if >30 days since last monthly report

set +e  # fail-silent: hooks must not abort on error

METRICS_DIR="$HOME/.claude/metrics"
LOCK_FILE="/tmp/claude-monthly-report.lock"

# Consume stdin
cat > /dev/null

# Rate limit: 1 per day
if [[ -f "$LOCK_FILE" ]]; then
    LOCK_AGE=$(( $(date +%s) - $(stat -f %m "$LOCK_FILE" 2>/dev/null || echo 0) ))
    if [[ $LOCK_AGE -lt 86400 ]]; then
        exit 0
    fi
fi

# Check if latest monthly report is >30 days old
LATEST=$(ls -t "$METRICS_DIR"/monthly-*.md 2>/dev/null | head -1)
if [[ -n "$LATEST" ]]; then
    REPORT_AGE=$(( $(date +%s) - $(stat -f %m "$LATEST" 2>/dev/null || echo 0) ))
    if [[ $REPORT_AGE -lt 2592000 ]]; then  # 30 days
        exit 0
    fi
fi

# Run monthly report in background
touch "$LOCK_FILE"
{
    python3 "$HOME/.claude/scripts/monthly-health-report.py" 2>/dev/null
} &

exit 0
