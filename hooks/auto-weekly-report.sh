#!/usr/bin/env bash
# auto-weekly-report.sh - Auto-generate weekly analysis if >7 days since last
# Hook: SessionStart, once: true
# Budget: <100ms (just a date check), background for actual generation
# Fail-silent

set +e  # fail-silent: hooks must not abort on error

METRICS_DIR="$HOME/.claude/metrics"
ANALYZER="$HOME/.claude/scripts/analyze-weekly.py"
LOCK_FILE="/tmp/claude-weekly-report.lock"

# Consume stdin
cat > /dev/null

# Prerequisites
[[ -f "$ANALYZER" ]] || exit 0
[[ -d "$METRICS_DIR" ]] || mkdir -p "$METRICS_DIR"

# Rate limit: max 1 per day
if [[ -f "$LOCK_FILE" ]]; then
    LOCK_AGE=$(( $(date +%s) - $(stat -f %m "$LOCK_FILE" 2>/dev/null || echo 0) ))
    [[ "$LOCK_AGE" -lt 86400 ]] && exit 0
fi

# Find most recent weekly report
LATEST=$(ls -t "$METRICS_DIR"/weekly-*.md 2>/dev/null | head -1)

GENERATE=false
if [[ -z "$LATEST" ]]; then
    # No reports exist — generate first one
    GENERATE=true
else
    # Check age of latest report
    REPORT_AGE=$(( $(date +%s) - $(stat -f %m "$LATEST" 2>/dev/null || echo 0) ))
    # 7 days = 604800 seconds
    [[ "$REPORT_AGE" -ge 604800 ]] && GENERATE=true
fi

if [[ "$GENERATE" == "true" ]]; then
    # Generate in background
    {
        touch "$LOCK_FILE"
        python3 "$ANALYZER" 2>/dev/null
    } &
fi

exit 0
