#!/bin/bash
# Save Claude Code conversation to project folder and optionally RAG-index it
# Used by PreCompact and SessionEnd hooks

set +e  # fail-silent: hooks must not abort on error

# Read hook input from stdin
HOOK_INPUT=$(cat)
TRANSCRIPT_PATH=$(echo "$HOOK_INPUT" | jq -r '.transcript_path')
SESSION_ID=$(echo "$HOOK_INPUT" | jq -r '.session_id')
CWD=$(echo "$HOOK_INPUT" | jq -r '.cwd')
HOOK_EVENT=$(echo "$HOOK_INPUT" | jq -r '.hook_event_name')
TRIGGER=$(echo "$HOOK_INPUT" | jq -r '.trigger // .reason // "unknown"')

# Skip if no transcript or CWD
[ -z "$TRANSCRIPT_PATH" ] || [ "$TRANSCRIPT_PATH" = "null" ] && exit 0
[ -z "$CWD" ] || [ "$CWD" = "null" ] && exit 0
[ ! -f "$TRANSCRIPT_PATH" ] && exit 0

# Determine history folder based on directory type
# Project directories: save to project folder
# Other directories: save to global ~/.claude/conversation-history/
if [[ "$CWD" =~ ^${HOME}/Documents/(Projects|Docs) ]]; then
    HISTORY_DIR="$CWD/conversation-history"
    IS_PROJECT=true
else
    HISTORY_DIR="$HOME/.claude/conversation-history"
    IS_PROJECT=false
fi
mkdir -p "$HISTORY_DIR"

# Generate filename: YYYY-MM-DD_HHMMSS_event_trigger.jsonl
TIMESTAMP=$(date +%Y-%m-%d_%H%M%S)
SHORT_SESSION=$(echo "$SESSION_ID" | cut -c1-8)
FILENAME="${TIMESTAMP}_${SHORT_SESSION}_${HOOK_EVENT}_${TRIGGER}.jsonl"
DEST_FILE="$HISTORY_DIR/$FILENAME"

# Copy transcript
cp "$TRANSCRIPT_PATH" "$DEST_FILE"

# Optional: Create human-readable markdown version (backgrounded — not blocking)
MD_FILE="${DEST_FILE%.jsonl}.md"
(
    {
        echo "# Conversation: $TIMESTAMP"
        echo ""
        echo "- **Session**: $SESSION_ID"
        echo "- **Event**: $HOOK_EVENT ($TRIGGER)"
        echo "- **Project**: $CWD"
        echo ""
        echo "---"
        echo ""

        # Single jq pass over entire JSONL (replaces per-line loop that spawned 3x jq per line)
        jq -r '
            if (.type == "human" or .type == "user") then
                "## User\n\n" + (
                    (.message.content // .content // "") |
                    if type == "string" then . else tostring end
                ) + "\n"
            elif .type == "assistant" then
                "## Assistant\n\n" + (
                    if .message.content then
                        if (.message.content | type) == "array" then
                            [.message.content[] | select(.type == "text") | .text] | join("\n")
                        else
                            .message.content | if type == "string" then . else tostring end
                        end
                    elif .content then
                        if (.content | type) == "array" then
                            [.content[] | select(.type == "text") | .text] | join("\n")
                        else
                            .content | if type == "string" then . else tostring end
                        end
                    else
                        ""
                    end
                ) + "\n"
            else
                empty
            end
        ' "$DEST_FILE" 2>/dev/null
    } > "$MD_FILE" 2>/dev/null
) &

# Optional: Submit batch RAG index via queue if .rag folder exists
# Uses the queue system to prevent multiple concurrent indexing processes.
if [ -d "$CWD/.rag" ]; then
    SUBMIT="$HOME/.claude/mcp-servers/rag-server/queue/submit.sh"
    if [ -x "$SUBMIT" ]; then
        "$SUBMIT" batch "$CWD" "$CWD" 5 2>/dev/null &
    fi
fi

# Call lesson extractor for all conversations (not just projects)
LESSON_EXTRACTOR="$HOME/.claude/hooks/lesson-extractor.sh"
if [ -x "$LESSON_EXTRACTOR" ]; then
    "$LESSON_EXTRACTOR" "$DEST_FILE" "$SESSION_ID" &
fi

echo "Conversation saved: $FILENAME" >&2
exit 0
