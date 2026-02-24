#!/bin/bash
# restart-rag-server.sh - Restart the RAG MCP server
#
# Used by rag-search-agent for auto-reconnection on failure.
# Can also be run manually: ~/.claude/scripts/restart-rag-server.sh
#
# Exit codes:
#   0 - Server restarted and healthy
#   1 - Server failed to restart
#   2 - Ollama not running (prerequisite)

set -euo pipefail

# Configuration
UV_PATH="$HOME/.local/bin/uv"
MCP_SERVER_DIR="$HOME/.claude/mcp-servers/rag-server"
OLLAMA_URL="http://localhost:11434"
MAX_RETRIES=3
RETRY_DELAY=2

log() {
    echo "[$(date '+%H:%M:%S')] $1" >&2
}

# Check Ollama is running (prerequisite)
check_ollama() {
    if ! curl -s --max-time 2 "$OLLAMA_URL/api/tags" > /dev/null 2>&1; then
        log "ERROR: Ollama not responding at $OLLAMA_URL"
        log "Start Ollama first: brew services start ollama"
        return 2
    fi
    log "Ollama: OK"
    return 0
}

# Kill existing rag-server processes
kill_existing() {
    local pids
    pids=$(pgrep -f "rag_server" 2>/dev/null || true)

    if [[ -n "$pids" ]]; then
        log "Killing existing rag-server processes: $pids"
        echo "$pids" | xargs kill -9 2>/dev/null || true
        sleep 1
    else
        log "No existing rag-server processes found"
    fi
}

# Start the MCP server (in background, detached)
start_server() {
    log "Starting RAG MCP server..."

    # Set environment
    export OLLAMA_BASE_URL="$OLLAMA_URL"
    export OLLAMA_MODEL="mxbai-embed-large"

    # Start server in background
    nohup "$UV_PATH" run --directory "$MCP_SERVER_DIR" python -m rag_server \
        > /tmp/rag-server.log 2>&1 &

    local pid=$!
    log "Started server with PID: $pid"

    # Give it time to initialize
    sleep 2

    # Check if still running
    if kill -0 "$pid" 2>/dev/null; then
        log "Server process running"
        return 0
    else
        log "ERROR: Server process died immediately"
        log "Check /tmp/rag-server.log for details"
        return 1
    fi
}

# Verify server is responding (via test connection)
verify_server() {
    local attempt=1

    while [[ $attempt -le $MAX_RETRIES ]]; do
        log "Verification attempt $attempt/$MAX_RETRIES..."

        # MCP servers don't have HTTP endpoints - check process exists
        if pgrep -f "rag_server" > /dev/null 2>&1; then
            log "SUCCESS: RAG server is running"
            return 0
        fi

        log "Server not responding, waiting ${RETRY_DELAY}s..."
        sleep "$RETRY_DELAY"
        ((attempt++))
    done

    log "ERROR: Server verification failed after $MAX_RETRIES attempts"
    return 1
}

# Main
main() {
    log "=== RAG Server Restart ==="

    # Check prerequisites
    if ! check_ollama; then
        exit 2
    fi

    # Kill existing
    kill_existing

    # Start fresh
    if ! start_server; then
        log "Failed to start server"
        exit 1
    fi

    # Verify
    if ! verify_server; then
        log "Server started but verification failed"
        exit 1
    fi

    log "=== Restart Complete ==="
    exit 0
}

main "$@"
