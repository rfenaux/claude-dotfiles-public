# Process Management

Rules for killing and managing stuck processes.

| Scenario | Action |
|----------|--------|
| Known-stuck Python worker | `kill -9 <pid>` directly (SIGTERM often ignored by long-running workers) |
| After killing any process | Check for stale lock files: `.lock`, `.pid`, `celerybeat-schedule` |
| RAG indexers, queue workers | `ps aux | grep <name>` before assuming stuck |
| Lock files older than 30 min | Safe to delete |
| Port already in use | `lsof -i :<port>` to find PID, then kill |
| Multiple stuck processes | Kill parent process first, then orphans |

**Lock file locations:**
- RAG: `<project>/.rag/*.lock`
- Dashboard: `/tmp/dashboard-*.pid`
- Ollama: Check via `ollama ps`
