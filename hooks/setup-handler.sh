#!/bin/bash
# setup-handler.sh - Setup hook for --init / --init-only / --maintenance
# Runs automated health checks and initialization tasks
# v2.1.10 feature: Setup hook event

set +e  # fail-silent: hooks must not abort on error

SCRIPT_DIR="$HOME/.claude/scripts"
HOOKS_DIR="$HOME/.claude/hooks"
STATUS=()
ERRORS=()

# --- 1. RAG Pre-flight (Ollama + embedding model) ---
if curl -sf http://localhost:11434/api/tags 2>/dev/null | python3 -c "
import sys,json
models=[m['name'] for m in json.load(sys.stdin)['models']]
assert any('mxbai-embed-large' in m for m in models)
" 2>/dev/null; then
    STATUS+=("RAG: Ollama + mxbai-embed-large ready")
else
    ERRORS+=("RAG: Ollama not running or mxbai-embed-large not loaded. Run: ollama pull mxbai-embed-large")
fi

# --- 2. Memory sync ---
if [ -x "$SCRIPT_DIR/sync-memory.sh" ]; then
    "$SCRIPT_DIR/sync-memory.sh" sync 2>/dev/null && STATUS+=("Memory: synced") || ERRORS+=("Memory: sync failed")
else
    STATUS+=("Memory: sync script not found (skipped)")
fi

# --- 3. Config validation (quick mode) ---
if [ -x "$SCRIPT_DIR/validate-setup.sh" ]; then
    if "$SCRIPT_DIR/validate-setup.sh" --quick 2>/dev/null; then
        STATUS+=("Config: valid")
    else
        ERRORS+=("Config: validation issues found. Run validate-setup.sh for details")
    fi
else
    STATUS+=("Config: validation script not found (skipped)")
fi

# --- 4. CTM workspace health ---
CTM_DIR="$HOME/.claude/ctm"
if [ -d "$CTM_DIR" ]; then
    task_count=$(find "$CTM_DIR" -name "*.json" -maxdepth 2 2>/dev/null | wc -l | tr -d ' ')
    STATUS+=("CTM: $task_count task files found")
else
    STATUS+=("CTM: directory not found")
fi

# --- 5. Dashboard health ---
if curl -sf http://localhost:8420/health 2>/dev/null >/dev/null; then
    STATUS+=("Dashboard: running at :8420")
else
    STATUS+=("Dashboard: not running (optional)")
fi

# --- Output ---
echo "[SETUP CHECK]"
for s in "${STATUS[@]}"; do
    echo "  OK: $s"
done
for e in "${ERRORS[@]}"; do
    echo "  WARN: $e"
done

if [ ${#ERRORS[@]} -eq 0 ]; then
    echo "All systems go."
else
    echo "${#ERRORS[@]} issue(s) need attention."
fi
