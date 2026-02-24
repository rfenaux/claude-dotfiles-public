#!/usr/bin/env bash
# Quick health check for Claude Code services
set -euo pipefail
echo "=== Service Health ==="
# Ollama
if curl -s --max-time 2 http://localhost:11434/api/tags > /dev/null 2>&1; then
  echo "  Ollama:    UP"
else
  echo "  Ollama:    DOWN"
fi
# Dashboard
if curl -s --max-time 2 http://localhost:8420/ > /dev/null 2>&1; then
  echo "  Dashboard: UP"
else
  echo "  Dashboard: DOWN"
fi
# RAG server
if curl -s --max-time 2 http://localhost:8421/ > /dev/null 2>&1; then
  echo "  RAG MCP:   UP"
else
  echo "  RAG MCP:   DOWN"
fi
echo "=== Done ==="
