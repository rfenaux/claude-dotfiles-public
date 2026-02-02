#!/bin/bash
# inbox-watcher.sh - Auto-process files added to inbox directories
# Triggered by PostToolUse hook on Write tool
# Mode: AUTOMATIC - processes files immediately (high-confidence only)

# Read hook input from stdin
HOOK_INPUT=$(cat)
TOOL_NAME=$(echo "$HOOK_INPUT" | jq -r '.tool_name // empty')
TOOL_INPUT=$(echo "$HOOK_INPUT" | jq -r '.tool_input // empty')

# Only process Write tool
[ "$TOOL_NAME" != "Write" ] && exit 0

# Get the file path from tool input
FILE_PATH=$(echo "$TOOL_INPUT" | jq -r '.file_path // empty')

# Skip if no file path
[ -z "$FILE_PATH" ] || [ "$FILE_PATH" = "null" ] && exit 0

# Check if file is in an inbox directory
INBOX_PATH=""
PROJECT_ROOT=""

# Global inbox
if [[ "$FILE_PATH" == "$HOME/.claude/inbox/"* ]]; then
    INBOX_PATH="$HOME/.claude/inbox"
    PROJECT_ROOT="$HOME/.claude"
fi

# Project inbox (00-inbox/)
if [[ "$FILE_PATH" == *"/00-inbox/"* ]]; then
    # Extract the 00-inbox path
    INBOX_PATH="${FILE_PATH%/00-inbox/*}/00-inbox"
    PROJECT_ROOT="${FILE_PATH%/00-inbox/*}"
fi

# Not an inbox file
[ -z "$INBOX_PATH" ] && exit 0

# Get filename
FILENAME=$(basename "$FILE_PATH")

# Skip internal files
case "$FILENAME" in
    INBOX_RULES.md|.inbox_log.json|.gitignore|.*)
        exit 0
        ;;
esac

# Skip if file doesn't exist (might have been moved already)
[ ! -f "$FILE_PATH" ] && exit 0

# ============================================
# AUTO-PROCESS: Run processor for this file
# ============================================

PROCESSOR="$HOME/.claude/scripts/inbox-processor.py"

if [ -x "$PROCESSOR" ] || [ -f "$PROCESSOR" ]; then
    # Process just this file, asynchronously
    (
        # Small delay to ensure file is fully written
        sleep 0.5

        # Run processor for this specific file with force-auto
        # Using python3 explicitly in case shebang issues
        OUTPUT=$(python3 "$PROCESSOR" "$INBOX_PATH" --file "$FILENAME" --force-auto 2>&1)

        # Check if anything was processed
        if echo "$OUTPUT" | grep -q "AUTO-MOVED\|FALLBACK"; then
            # File was processed - output will show in hook result
            echo "[Inbox Auto] Processed: $FILENAME"
            echo "$OUTPUT" | grep -E "(AUTO-MOVED|FALLBACK|Renamed:|→|RAG:)" | head -10
        elif echo "$OUTPUT" | grep -q "SUGGESTION"; then
            # File needs manual confirmation
            echo "[Inbox] Needs review: $FILENAME"
            echo "$OUTPUT" | grep -E "SUGGESTION|→" | head -5
            echo "        Run: /inbox to confirm"
        fi
    ) &

    # Don't wait - let it run in background
    disown 2>/dev/null
fi

exit 0
