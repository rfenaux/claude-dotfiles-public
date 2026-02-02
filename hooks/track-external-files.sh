#!/bin/bash
# Track external files accessed via Read tool
# Logs paths to a session manifest for later copying
# Triggered by PostToolUse hook on Read

HOOK_INPUT=$(cat)
TOOL_NAME=$(echo "$HOOK_INPUT" | jq -r '.tool_name // empty')
TOOL_INPUT=$(echo "$HOOK_INPUT" | jq -r '.tool_input // empty')
CWD=$(echo "$HOOK_INPUT" | jq -r '.cwd // empty')
SESSION_ID=$(echo "$HOOK_INPUT" | jq -r '.session_id // empty')

# Only process Read tool
[ "$TOOL_NAME" != "Read" ] && exit 0

# Get the file path
FILE_PATH=$(echo "$TOOL_INPUT" | jq -r '.file_path // empty')
[ -z "$FILE_PATH" ] || [ "$FILE_PATH" = "null" ] && exit 0

# Skip if file doesn't exist
[ ! -f "$FILE_PATH" ] && exit 0

# Determine project root from CWD
PROJECT_ROOT=""
if [ -n "$CWD" ] && [ "$CWD" != "null" ]; then
    # Check if CWD is under Projects
    if [[ "$CWD" =~ ^~/Documents/Projects ]]; then
        # Extract project root (first two levels under Projects)
        PROJECT_ROOT=$(echo "$CWD" | sed -E 's|^(~/Documents/Projects[^/]*/[^/]+).*|\1|')
    fi
fi

# Skip if no project context
[ -z "$PROJECT_ROOT" ] && exit 0

# Check if file is external to the project
if [[ "$FILE_PATH" == "$PROJECT_ROOT"* ]]; then
    # File is inside project - nothing to track
    exit 0
fi

# Skip system/config files that shouldn't be copied
case "$FILE_PATH" in
    ~/.claude/*|~/.config/*|~/.local/*|/tmp/*|/var/*)
        exit 0
        ;;
esac

# Skip binary files (we only want to copy text-based files)
EXT="${FILE_PATH##*.}"
EXT_LOWER=$(echo "$EXT" | tr '[:upper:]' '[:lower:]')
case "$EXT_LOWER" in
    md|txt|json|pdf|docx|xlsx|pptx|html|py|js|ts|tsx|jsx|csv|yaml|yml|xml|sql|sh|env|toml|ini|cfg)
        ;;
    *)
        exit 0
        ;;
esac

# Create manifest directory
MANIFEST_DIR="/tmp/claude-external-files"
mkdir -p "$MANIFEST_DIR"

# Manifest file for this session (or project if no session)
if [ -n "$SESSION_ID" ] && [ "$SESSION_ID" != "null" ]; then
    MANIFEST_FILE="$MANIFEST_DIR/$SESSION_ID.manifest"
else
    # Fallback: use project name hash
    PROJECT_HASH=$(echo "$PROJECT_ROOT" | md5 -q)
    MANIFEST_FILE="$MANIFEST_DIR/$PROJECT_HASH.manifest"
fi

# Format: project_root|source_file_path
ENTRY="$PROJECT_ROOT|$FILE_PATH"

# Append if not already tracked (avoid duplicates)
if ! grep -qF "$ENTRY" "$MANIFEST_FILE" 2>/dev/null; then
    echo "$ENTRY" >> "$MANIFEST_FILE"
fi

exit 0
