#!/bin/bash
# Convenience wrapper for RAG index queue operations
# Usage: rag-queue status | drain | cancel <id> | submit <type> <args...>
exec "$HOME/.claude/mcp-servers/rag-server/queue/submit.sh" "$@"
