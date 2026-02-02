#!/bin/bash
# lesson-extractor.sh - Queue conversations for lesson extraction
#
# Called by: save-conversation.sh (after file save)
# Creates markers for high-value conversations that Claude will analyze on next session.
#
# Usage: lesson-extractor.sh <conversation-jsonl-path> <session-id>

set -e

CONVERSATION_FILE="$1"
SESSION_ID="$2"

# Validate inputs
[ -z "$CONVERSATION_FILE" ] && exit 0
[ ! -f "$CONVERSATION_FILE" ] && exit 0
[ -z "$SESSION_ID" ] && SESSION_ID="unknown"

PENDING_DIR="$HOME/.claude/lessons/pending"
mkdir -p "$PENDING_DIR"

# Skip short conversations (less than 20 turns = likely trivial)
TURN_COUNT=$(wc -l < "$CONVERSATION_FILE" | tr -d ' ')
if [ "$TURN_COUNT" -lt 20 ]; then
    exit 0
fi

# Check for lesson patterns (quick heuristics)
PATTERN_SCORE=0
PATTERNS_FOUND=""

# Check for error/retry patterns (iteration struggles)
if grep -qiE "(error|failed|didn.?t work|trying again|let me try|that didn.?t)" "$CONVERSATION_FILE" 2>/dev/null; then
    PATTERN_SCORE=$((PATTERN_SCORE + 2))
    PATTERNS_FOUND="${PATTERNS_FOUND}iteration,"
fi

# Check for clarification patterns
if grep -qiE "(I meant|to clarify|actually|I prefer|not quite|misunderstand)" "$CONVERSATION_FILE" 2>/dev/null; then
    PATTERN_SCORE=$((PATTERN_SCORE + 2))
    PATTERNS_FOUND="${PATTERNS_FOUND}clarification,"
fi

# Check for learning/breakthrough signals
if grep -qiE "(works!|that.?s it|perfect|figured out|the trick is|turns out)" "$CONVERSATION_FILE" 2>/dev/null; then
    PATTERN_SCORE=$((PATTERN_SCORE + 3))
    PATTERNS_FOUND="${PATTERNS_FOUND}breakthrough,"
fi

# Check for multi-attempt tool calls (same tool called 3+ times)
TOOL_REPEATS=$(grep -o '"tool"[[:space:]]*:[[:space:]]*"[^"]*"' "$CONVERSATION_FILE" 2>/dev/null | sort | uniq -c | awk '$1 >= 3 {print $1}' | wc -l | tr -d ' ')
if [ "$TOOL_REPEATS" -gt 0 ]; then
    PATTERN_SCORE=$((PATTERN_SCORE + 2))
    PATTERNS_FOUND="${PATTERNS_FOUND}tool_retry,"
fi

# Check for preference expressions
if grep -qiE "(I always|I never|I prefer|my style|I like to|I don.?t like)" "$CONVERSATION_FILE" 2>/dev/null; then
    PATTERN_SCORE=$((PATTERN_SCORE + 1))
    PATTERNS_FOUND="${PATTERNS_FOUND}preference,"
fi

# Skip if no lesson signals detected (threshold: 3)
if [ "$PATTERN_SCORE" -lt 3 ]; then
    exit 0
fi

# Remove trailing comma
PATTERNS_FOUND="${PATTERNS_FOUND%,}"

echo "[lesson-extractor] Score: $PATTERN_SCORE patterns=[$PATTERNS_FOUND] - extracting lessons..." >&2

# Run the API-based lesson extractor in background
# This calls Anthropic API directly, no Claude Code session needed
ANALYZER="$HOME/.claude/scripts/analyze-lessons.py"

if [ -x "$ANALYZER" ]; then
    # Run in background, detached from terminal
    nohup python3 "$ANALYZER" "$CONVERSATION_FILE" "$SESSION_ID" \
        >> "$HOME/.claude/lessons/extraction.log" 2>&1 &
    echo "[lesson-extractor] Background extraction started (PID: $!)" >&2
else
    # Fallback: create marker for manual extraction
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    MARKER_FILE="$PENDING_DIR/${TIMESTAMP}_${SESSION_ID:0:8}.json"

    cat > "$MARKER_FILE" << EOF
{
  "conversation_file": "$CONVERSATION_FILE",
  "session_id": "$SESSION_ID",
  "timestamp": "$(date -Iseconds)",
  "turn_count": $TURN_COUNT,
  "pattern_score": $PATTERN_SCORE,
  "patterns_detected": "$(echo "$PATTERNS_FOUND" | tr ',' ', ')",
  "status": "pending"
}
EOF
    echo "[lesson-extractor] Queued for manual analysis (analyzer not found)" >&2
fi

exit 0
