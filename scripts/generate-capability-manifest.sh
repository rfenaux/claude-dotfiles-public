#!/bin/bash
# Generate Capability Manifest
# Creates CAPABILITIES.md listing all available Claude Code capabilities
# Run: ~/.claude/scripts/generate-capability-manifest.sh [output-file]

set -euo pipefail

CLAUDE_DIR="${HOME}/.claude"
OUTPUT="${1:-$CLAUDE_DIR/CAPABILITIES.md}"
INVENTORY="$CLAUDE_DIR/inventory.json"

# Ensure inventory exists
if [[ ! -f "$INVENTORY" ]]; then
    echo "Generating inventory first..."
    "$CLAUDE_DIR/scripts/generate-inventory.sh" 2>/dev/null || true
fi

# Start manifest
cat > "$OUTPUT" << 'HEADER'
# Capability Manifest

> Complete inventory of Claude Code capabilities in this environment
> Auto-generated - do not edit manually

---

HEADER

# Add generation timestamp
echo "**Generated:** $(date '+%Y-%m-%d %H:%M:%S')" >> "$OUTPUT"
echo "" >> "$OUTPUT"

# Native Tools Section
cat >> "$OUTPUT" << 'NATIVE'
## Native Tools

Always available in Claude Code:

| Tool | Purpose |
|------|---------|
| Read | Read files |
| Write | Create files |
| Edit | Modify files |
| Glob | Find files by pattern |
| Grep | Search file contents |
| Bash | Execute commands |
| WebFetch | Fetch web content |
| WebSearch | Search the web |
| Task | Spawn sub-agents |
| AskUserQuestion | Interactive questions |

---

NATIVE

# Agents Section
echo "## Agents" >> "$OUTPUT"
echo "" >> "$OUTPUT"

if [[ -f "$INVENTORY" ]]; then
    AGENT_COUNT=$(jq '.counts.agents // 0' "$INVENTORY")
    echo "**Total:** $AGENT_COUNT agents" >> "$OUTPUT"
    echo "" >> "$OUTPUT"

    # Auto-invoke agents
    echo "### Auto-Invoke Agents" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    echo "These agents are automatically considered based on context:" >> "$OUTPUT"
    echo "" >> "$OUTPUT"

    jq -r '.agents[] | select(.auto_invoke == true) | "- **\(.name)** (\(.model))"' "$INVENTORY" 2>/dev/null >> "$OUTPUT" || echo "- None configured" >> "$OUTPUT"

    echo "" >> "$OUTPUT"

    # Model distribution
    echo "### By Model" >> "$OUTPUT"
    echo "" >> "$OUTPUT"

    HAIKU=$(jq '.model_distribution.haiku // 0' "$INVENTORY")
    SONNET=$(jq '.model_distribution.sonnet // 0' "$INVENTORY")
    OPUS=$(jq '.model_distribution.opus // 0' "$INVENTORY")

    echo "| Model | Count | Use Case |" >> "$OUTPUT"
    echo "|-------|-------|----------|" >> "$OUTPUT"
    echo "| Haiku | $HAIKU | Quick lookups, delegation |" >> "$OUTPUT"
    echo "| Sonnet | $SONNET | Code, docs, implementation |" >> "$OUTPUT"
    echo "| Opus | $OPUS | Architecture, complex reasoning |" >> "$OUTPUT"

    echo "" >> "$OUTPUT"

    # Full agent list (collapsed for readability)
    echo "<details>" >> "$OUTPUT"
    echo "<summary>Full Agent List ($AGENT_COUNT agents)</summary>" >> "$OUTPUT"
    echo "" >> "$OUTPUT"

    jq -r '.agents | sort_by(.name) | .[] | "- \(.name) (\(.model))"' "$INVENTORY" 2>/dev/null >> "$OUTPUT" || echo "- Error reading agents" >> "$OUTPUT"

    echo "" >> "$OUTPUT"
    echo "</details>" >> "$OUTPUT"
else
    echo "⚠️ inventory.json not found - run generate-inventory.sh first" >> "$OUTPUT"
fi

echo "" >> "$OUTPUT"
echo "---" >> "$OUTPUT"
echo "" >> "$OUTPUT"

# Skills Section
echo "## Skills" >> "$OUTPUT"
echo "" >> "$OUTPUT"

SKILL_COUNT=0
if [[ -d "$CLAUDE_DIR/skills" ]]; then
    echo "Available slash commands:" >> "$OUTPUT"
    echo "" >> "$OUTPUT"

    find "$CLAUDE_DIR/skills" -name "SKILL.md" -type f 2>/dev/null | while read -r skill_file; do
        skill_dir=$(dirname "$skill_file")
        skill_name=$(basename "$skill_dir")

        # Extract description from frontmatter
        description=$(awk '/^---/{p=1;next}/^---/{p=0}p' "$skill_file" | grep -E '^description:' | sed 's/description: *//' | head -1)

        if [[ -z "$description" ]]; then
            description="No description"
        fi

        echo "- **/$skill_name** - ${description:0:80}" >> "$OUTPUT"
        ((SKILL_COUNT++))
    done

    if [[ $SKILL_COUNT -eq 0 ]]; then
        echo "- No custom skills found" >> "$OUTPUT"
    fi
else
    echo "- Skills directory not found" >> "$OUTPUT"
fi

echo "" >> "$OUTPUT"
echo "---" >> "$OUTPUT"
echo "" >> "$OUTPUT"

# Hooks Section
echo "## Hooks" >> "$OUTPUT"
echo "" >> "$OUTPUT"

if [[ -f "$CLAUDE_DIR/settings.json" ]]; then
    echo "Active hooks by event:" >> "$OUTPUT"
    echo "" >> "$OUTPUT"

    for event in SessionStart PreToolUse PostToolUse PreCompact SessionEnd Setup Stop; do
        count=$(jq ".hooks.$event | if . == null then 0 else length end" "$CLAUDE_DIR/settings.json" 2>/dev/null || echo "0")
        if [[ "$count" != "0" && "$count" != "null" ]]; then
            echo "- **$event**: $count hook(s)" >> "$OUTPUT"
        fi
    done
else
    echo "- settings.json not found" >> "$OUTPUT"
fi

echo "" >> "$OUTPUT"
echo "---" >> "$OUTPUT"
echo "" >> "$OUTPUT"

# MCP Servers Section
echo "## MCP Servers" >> "$OUTPUT"
echo "" >> "$OUTPUT"

if [[ -f "$HOME/.mcp.json" ]]; then
    echo "Configured MCP servers:" >> "$OUTPUT"
    echo "" >> "$OUTPUT"

    jq -r '.mcpServers | keys[]' "$HOME/.mcp.json" 2>/dev/null | while read -r server; do
        echo "- **$server**" >> "$OUTPUT"
    done

    if [[ $(jq '.mcpServers | length' "$HOME/.mcp.json" 2>/dev/null) -eq 0 ]]; then
        echo "- No MCP servers configured" >> "$OUTPUT"
    fi
else
    echo "- .mcp.json not found" >> "$OUTPUT"
fi

echo "" >> "$OUTPUT"
echo "---" >> "$OUTPUT"
echo "" >> "$OUTPUT"

# Plugins Section
echo "## Plugins" >> "$OUTPUT"
echo "" >> "$OUTPUT"

if [[ -f "$CLAUDE_DIR/settings.json" ]]; then
    echo "Enabled plugins:" >> "$OUTPUT"
    echo "" >> "$OUTPUT"

    jq -r '.enabledPlugins // {} | to_entries[] | select(.value == true) | "- \(.key)"' "$CLAUDE_DIR/settings.json" 2>/dev/null >> "$OUTPUT"

    if [[ $(jq '.enabledPlugins // {} | to_entries | map(select(.value == true)) | length' "$CLAUDE_DIR/settings.json" 2>/dev/null) -eq 0 ]]; then
        echo "- No plugins enabled" >> "$OUTPUT"
    fi
else
    echo "- settings.json not found" >> "$OUTPUT"
fi

echo "" >> "$OUTPUT"
echo "---" >> "$OUTPUT"
echo "" >> "$OUTPUT"

# Footer
cat >> "$OUTPUT" << 'FOOTER'
## Quick Reference

| Category | Command |
|----------|---------|
| List agents | `ls ~/.claude/agents/` |
| List skills | `ls ~/.claude/skills/` |
| Check hooks | `jq '.hooks' ~/.claude/settings.json` |
| View memory | `/memory` |
| Check context | `/context` |
| Validate setup | `~/.claude/scripts/validate-setup.sh` |

---

*Generated by `generate-capability-manifest.sh`*
FOOTER

echo "✓ Capability manifest written to: $OUTPUT"
