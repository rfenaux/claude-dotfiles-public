#!/usr/bin/env bash
# Quick count of all configuration components
set -euo pipefail
echo "=== Claude Code Configuration ==="
echo "Agents:      $(ls ~/.claude/agents/*.md 2>/dev/null | wc -l | tr -d ' ')"
echo "Skills:      $(ls ~/.claude/skills/*/SKILL.md 2>/dev/null | wc -l | tr -d ' ')"
echo "Hooks:       $(python3 -c "import json; h=json.load(open('$HOME/.claude/settings.json')).get('hooks',{}); print(sum(len(e.get('hooks',[])) for el in h.values() if isinstance(el,list) for e in el if isinstance(e,dict)))" 2>/dev/null || echo 0)"
echo "Scripts:     $(ls ~/.claude/scripts/*.sh 2>/dev/null | wc -l | tr -d ' ')"
echo "MCP Servers: $(python3 -c "import json; print(len(json.load(open('$HOME/.mcp.json')).get('mcpServers',{})))" 2>/dev/null || echo 0)"
echo "RAG Projects:$(python3 -c "import json; print(len(json.load(open('$HOME/.claude/rag-projects.json')).get('projects',[])))" 2>/dev/null || echo 0)"
echo "Lessons:     $(wc -l < ~/.claude/lessons/lessons.jsonl 2>/dev/null | tr -d ' ' || echo 0)"
echo "CTM Tasks:   $(python3 -c "import json; print(json.load(open('$HOME/.claude/ctm/index.json')).get('total_agents',0))" 2>/dev/null || echo 0)"
