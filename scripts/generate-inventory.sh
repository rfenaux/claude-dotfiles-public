#!/bin/bash
# Generate inventory.json - Single source of truth for Claude Code configuration
# Run: ~/.claude/scripts/generate-inventory.sh
# Output: ~/.claude/inventory.json

set -e

CLAUDE_DIR="$HOME/.claude"
OUTPUT_FILE="$CLAUDE_DIR/inventory.json"

echo "Generating Claude Code inventory..."

# Count agents
AGENTS=$(find "$CLAUDE_DIR/agents" -name "*.md" -type f 2>/dev/null | wc -l | tr -d ' ')

# Count skills (folders with SKILL.md)
SKILLS=$(find "$CLAUDE_DIR/skills" -name "SKILL.md" -type f 2>/dev/null | wc -l | tr -d ' ')

# Count hooks
HOOKS=$(find "$CLAUDE_DIR/hooks" -name "*.sh" -type f 2>/dev/null | wc -l | tr -d ' ')

# List agents with metadata
AGENTS_JSON=$(find "$CLAUDE_DIR/agents" -name "*.md" -type f 2>/dev/null | sort | while read -r file; do
    name=$(basename "$file" .md)
    # Extract model from frontmatter (strip spaces and newlines)
    model=$(grep "^model:" "$file" 2>/dev/null | head -1 | sed 's/model: *//' | tr -d ' \n\r')
    [ -z "$model" ] && model="sonnet"
    # Extract async mode (strip spaces and newlines)
    async_mode=$(grep -A2 "^async:" "$file" 2>/dev/null | grep "mode:" | head -1 | sed 's/.*mode: *//' | tr -d ' \n\r')
    [ -z "$async_mode" ] && async_mode="auto"
    # Extract auto_invoke (default to false if not found)
    auto_invoke_raw=$(grep "^auto_invoke:" "$file" 2>/dev/null | head -1 | sed 's/auto_invoke: *//' | tr -d ' \n\r')
    if [ "$auto_invoke_raw" = "true" ]; then
        auto_invoke="true"
    else
        auto_invoke="false"
    fi
    echo "{\"name\":\"$name\",\"model\":\"$model\",\"async\":\"$async_mode\",\"auto_invoke\":$auto_invoke}"
done | jq -s '.')

# List skills
SKILLS_JSON=$(find "$CLAUDE_DIR/skills" -name "SKILL.md" -type f 2>/dev/null | while read -r file; do
    dir=$(dirname "$file")
    name=$(basename "$dir")
    echo "{\"name\":\"$name\"}"
done | jq -s '.')

# List hooks
HOOKS_JSON=$(find "$CLAUDE_DIR/hooks" -name "*.sh" -type f 2>/dev/null | while read -r file; do
    name=$(basename "$file" .sh)
    rel_path=$(echo "$file" | sed "s|$CLAUDE_DIR/||")
    echo "{\"name\":\"$name\",\"path\":\"$rel_path\"}"
done | jq -s '.')

# Get enabled plugins from settings.json
PLUGINS_JSON=$(jq '.enabledPlugins // {}' "$CLAUDE_DIR/settings.json" 2>/dev/null || echo '{}')

# Get MCP servers
MCP_SERVERS=$(ls -d "$CLAUDE_DIR/mcp-servers"/*/ 2>/dev/null | while read -r dir; do
    name=$(basename "$dir")
    echo "\"$name\""
done | paste -sd, - || echo "")
MCP_JSON="[${MCP_SERVERS}]"

# Generate inventory.json
cat > "$OUTPUT_FILE" << EOF
{
  "version": "1.1",
  "generated": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "counts": {
    "agents": $AGENTS,
    "skills": $SKILLS,
    "hooks": $HOOKS
  },
  "agents": $AGENTS_JSON,
  "skills": $SKILLS_JSON,
  "hooks": $HOOKS_JSON,
  "plugins": $PLUGINS_JSON,
  "mcp_servers": $MCP_JSON,
  "model_distribution": {
    "haiku": $(echo "$AGENTS_JSON" | jq '[.[] | select(.model == "haiku")] | length'),
    "sonnet": $(echo "$AGENTS_JSON" | jq '[.[] | select(.model == "sonnet" or .model == "")] | length'),
    "opus": $(echo "$AGENTS_JSON" | jq '[.[] | select(.model == "opus")] | length')
  },
  "async_distribution": {
    "always": $(echo "$AGENTS_JSON" | jq '[.[] | select(.async == "always")] | length'),
    "auto": $(echo "$AGENTS_JSON" | jq '[.[] | select(.async == "auto" or .async == "")] | length'),
    "never": $(echo "$AGENTS_JSON" | jq '[.[] | select(.async == "never")] | length')
  },
  "auto_invoke": {
    "enabled": $(echo "$AGENTS_JSON" | jq '[.[] | select(.auto_invoke == true)] | length'),
    "disabled": $(echo "$AGENTS_JSON" | jq '[.[] | select(.auto_invoke == false or .auto_invoke == null)] | length'),
    "agents": $(echo "$AGENTS_JSON" | jq '[.[] | select(.auto_invoke == true) | .name]')
  }
}
EOF

# Pretty print
jq '.' "$OUTPUT_FILE" > "$OUTPUT_FILE.tmp" && mv "$OUTPUT_FILE.tmp" "$OUTPUT_FILE"

echo "✓ Inventory generated: $OUTPUT_FILE"
echo ""
echo "Summary:"
echo "  Agents: $AGENTS"
echo "  Skills: $SKILLS"
echo "  Hooks:  $HOOKS"
echo ""
echo "Run 'cat ~/.claude/inventory.json' to view full inventory"
