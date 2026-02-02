#!/bin/bash
# Claude Code wrapper with --slim/--full mode switching
# Usage: claude-wrapper [--slim|--full] [claude args...]
#
# Main sessions use full CLAUDE.md by default.
# Sub-agents (spawned via Task tool) auto-detect and use slim.

set -euo pipefail

CLAUDE_DIR="$HOME/.claude"
CLAUDE_MD="$CLAUDE_DIR/CLAUDE.md"
CLAUDE_MD_FULL="$CLAUDE_DIR/CLAUDE.md.full"
CLAUDE_MD_SLIM="$CLAUDE_DIR/CLAUDE.md.slim"

# Default mode for main sessions
DEFAULT_MODE="${CLAUDE_DEFAULT_MODE:-full}"
MODE="$DEFAULT_MODE"

# Parse our custom flags
CLAUDE_ARGS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --slim)
            MODE="slim"
            shift
            ;;
        --full)
            MODE="full"
            shift
            ;;
        *)
            CLAUDE_ARGS+=("$1")
            shift
            ;;
    esac
done

# Select the right CLAUDE.md
if [[ "$MODE" == "slim" ]]; then
    if [[ -f "$CLAUDE_MD_SLIM" ]]; then
        cp "$CLAUDE_MD_SLIM" "$CLAUDE_MD"
        echo "[claude-wrapper] Using slim CLAUDE.md (~1.5k tokens)"
    else
        echo "[claude-wrapper] Warning: CLAUDE.md.slim not found, using current" >&2
    fi
elif [[ "$MODE" == "full" ]]; then
    if [[ -f "$CLAUDE_MD_FULL" ]]; then
        cp "$CLAUDE_MD_FULL" "$CLAUDE_MD"
        echo "[claude-wrapper] Using full CLAUDE.md (~8k tokens)"
    else
        echo "[claude-wrapper] Warning: CLAUDE.md.full not found, using current" >&2
    fi
fi

# Export marker so sub-agents can detect they're NOT the main session
# (Sub-agents spawned via Task tool won't have this env var)
export CLAUDE_MAIN_SESSION=true

# Run the real claude binary
# Use ${arr[@]+"${arr[@]}"} idiom to handle empty array with set -u
exec /opt/homebrew/bin/claude ${CLAUDE_ARGS[@]+"${CLAUDE_ARGS[@]}"}
