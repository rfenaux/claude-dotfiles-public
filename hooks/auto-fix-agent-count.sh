#!/bin/bash
# PostToolUse hook: Auto-update agent count in AGENTS_INDEX.md
# Triggers on Write/Edit to ~/.claude/agents/*.md

# Read tool input from stdin
input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // .tool_input.path // ""')

# Exit early if not an agent file
[[ "$file_path" != *"/.claude/agents/"*.md ]] && exit 0

AGENTS_INDEX="$HOME/.claude/AGENTS_INDEX.md"
[ ! -f "$AGENTS_INDEX" ] && exit 0

# Count actual agents
actual_count=$(find "$HOME/.claude/agents" -name "*.md" -type f 2>/dev/null | wc -l | tr -d ' ')

# Get current documented count
current_line=$(grep "^\\*\\*Total Agents:" "$AGENTS_INDEX" 2>/dev/null)

if [ -n "$current_line" ]; then
    current_count=$(echo "$current_line" | grep -o '[0-9]*')

    # Only update if count changed
    if [ "$actual_count" != "$current_count" ]; then
        # Update the count in place
        sed -i '' "s/^\\*\\*Total Agents: [0-9]*\\*\\*/**Total Agents: ${actual_count}**/" "$AGENTS_INDEX"
        echo "[Auto-fix] AGENTS_INDEX.md: $current_count → $actual_count agents"
    fi
else
    # No Total Agents line exists - add it after the title
    sed -i '' "s/^# Claude Code Agents Index$/# Claude Code Agents Index\\
\\
**Total Agents: ${actual_count}**/" "$AGENTS_INDEX"
    echo "[Auto-fix] Added agent count to AGENTS_INDEX.md: $actual_count"
fi

exit 0
