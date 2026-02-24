#!/usr/bin/env bash
# mcp-preflight.sh - SessionStart hook (once: true)
# Checks RAG MCP server availability and outputs advisory warning.
# Budget: <2s | Fail-silent | No circuit breaker needed (runs once per session)

set +e  # fail-silent: hooks must not abort on error

MCP_STATUS=""
WARNINGS=""

# --- Check 1: Ollama (RAG embedding backend) ---
OLLAMA_OK=false
if curl -sf --max-time 2 http://localhost:11434/api/tags >/dev/null 2>&1; then
  # Check if embedding model is available
  if curl -sf --max-time 2 http://localhost:11434/api/tags | python3 -c "
import sys, json
models = [m['name'] for m in json.load(sys.stdin).get('models', [])]
sys.exit(0 if any('mxbai-embed-large' in m for m in models) else 1)
" 2>/dev/null; then
    OLLAMA_OK=true
  else
    WARNINGS="${WARNINGS}  - Ollama running but mxbai-embed-large not loaded (run: ollama pull mxbai-embed-large)\n"
  fi
else
  WARNINGS="${WARNINGS}  - Ollama not responding (RAG indexing/search unavailable)\n"
fi

# --- Check 2: RAG MCP Server ---
RAG_MCP_OK=false
if pgrep -f "rag_mcp_server" >/dev/null 2>&1; then
  RAG_MCP_OK=true
else
  WARNINGS="${WARNINGS}  - RAG MCP server not running (CLI fallback: python3 -m rag_mcp_server.cli)\n"
fi

# --- Check 3: Dashboard ---
DASHBOARD_OK=false
if curl -sf --max-time 2 http://localhost:8420/health >/dev/null 2>&1; then
  DASHBOARD_OK=true
else
  # Try base URL
  if curl -sf --max-time 2 http://localhost:8420/ >/dev/null 2>&1; then
    DASHBOARD_OK=true
  else
    WARNINGS="${WARNINGS}  - Dashboard not responding on :8420\n"
  fi
fi

# --- Output ---
if [ -n "$WARNINGS" ]; then
  echo "[MCP Pre-flight] Service warnings:"
  printf "$WARNINGS"
  echo "  Use CLI fallbacks where available. Do NOT retry MCP tools — pivot immediately."
else
  echo "[MCP Pre-flight] All services OK (Ollama, RAG MCP, Dashboard)"
fi

exit 0
