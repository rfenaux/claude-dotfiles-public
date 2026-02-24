---
name: services
description: Check health of Claude Code background services (Ollama, Dashboard, RAG MCP)
user_invocable: true
---

# /services - Service Health Check

Quick health check for all Claude Code background services.

## Instructions

When the user invokes `/services`, check each service and report status:

1. **Ollama** — `curl -s --max-time 2 http://localhost:11434/api/tags`
   - UP if HTTP 200, show model count
   - DOWN if unreachable

2. **Command Center Dashboard** — `curl -s --max-time 2 http://localhost:8420/api/config-score`
   - UP if returns valid JSON with "success": true
   - DOWN if unreachable

3. **RAG MCP Server** — Check if process is running via `pgrep -f "rag_server"`
   - UP if process found
   - DOWN if not running

4. **LaunchAgents** — `launchctl list | grep com.claude`
   - Show registered agents and their PIDs

## Output Format

```
Service Health
  Ollama:        UP (3 models loaded)
  Dashboard:     UP (port 8420)
  RAG MCP:       UP (pid 12345)
  LaunchAgents:  2 registered

All services healthy.
```

If any service is down, suggest the fix command (e.g., `launchctl start com.claude.rag-dashboard`).
