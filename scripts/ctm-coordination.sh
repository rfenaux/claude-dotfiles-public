#!/usr/bin/env bash
# ctm-coordination.sh - CTM integration for multi-session coordination
# Provides CTM-style commands for coordination management
#
# Usage: ctm-coordination.sh <command> [args...]
#
# Commands:
#   status [project]       Show coordination status
#   health [project]       Run health check
#   locks [project]        List active locks
#   release <lock_id>      Force release a lock
#   stale [--cleanup]      Check for stale agents
#   init <project>         Initialize coordination for project

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ─────────────────────────────────────────────────────────────────────────────
# Colors
# ─────────────────────────────────────────────────────────────────────────────

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ─────────────────────────────────────────────────────────────────────────────
# Help
# ─────────────────────────────────────────────────────────────────────────────

show_help() {
  cat << EOF
${BOLD}CTM Coordination Commands${NC}

${CYAN}Usage:${NC} ctm coordination <command> [args...]

${CYAN}Commands:${NC}
  ${GREEN}status${NC} [project]       Show coordination status for project
  ${GREEN}health${NC} [project]       Run health check (add --fix to auto-repair)
  ${GREEN}locks${NC} [project]        List all active locks
  ${GREEN}release${NC} <lock_id>      Force release a specific lock
  ${GREEN}stale${NC} [--cleanup]      Check for stale agents (--cleanup to release)
  ${GREEN}init${NC} <project>         Initialize coordination for project

${CYAN}Examples:${NC}
  ctm coordination status                 # Status for current project
  ctm coordination status /path/to/proj   # Status for specific project
  ctm coordination health --fix           # Health check with auto-repair
  ctm coordination locks                  # List all locks
  ctm coordination release lock-abc123    # Force release a lock
  ctm coordination stale --cleanup        # Release stale locks

${CYAN}Notes:${NC}
  If no project is specified, uses current working directory.
  All coordination data is stored in project/.agent-workspaces/

${CYAN}See also:${NC}
  ~/.claude/PRD-multi-session-coordination.md  # Full specification
  ~/.claude/CDP_PROTOCOL.md                    # CDP integration details
EOF
}

# ─────────────────────────────────────────────────────────────────────────────
# Detect project
# ─────────────────────────────────────────────────────────────────────────────

detect_project() {
  local provided="$1"

  if [[ -n "$provided" && -d "$provided" ]]; then
    echo "$provided"
    return
  fi

  # Try current directory
  if [[ -d ".agent-workspaces" ]]; then
    pwd
    return
  fi

  # Try to find project root (look for .claude or .git)
  local dir="$PWD"
  while [[ "$dir" != "/" ]]; do
    if [[ -d "$dir/.claude" || -d "$dir/.git" ]]; then
      echo "$dir"
      return
    fi
    dir="$(dirname "$dir")"
  done

  # Fall back to current directory
  pwd
}

# ─────────────────────────────────────────────────────────────────────────────
# Commands
# ─────────────────────────────────────────────────────────────────────────────

if [[ $# -lt 1 ]]; then
  show_help
  exit 0
fi

COMMAND="$1"
shift

case "$COMMAND" in

  # ─────────────────────────────────────────────────────────────────────────
  # STATUS
  # ─────────────────────────────────────────────────────────────────────────
  status)
    PROJECT=$(detect_project "${1:-}")

    echo -e "${BOLD}CTM Coordination Status${NC}"
    echo -e "${CYAN}Project:${NC} $PROJECT"
    echo ""

    "$SCRIPT_DIR/coord-status.sh" "$PROJECT"
    ;;

  # ─────────────────────────────────────────────────────────────────────────
  # HEALTH
  # ─────────────────────────────────────────────────────────────────────────
  health)
    PROJECT=""
    FIX_FLAG=""

    for arg in "$@"; do
      case $arg in
        --fix) FIX_FLAG="--fix" ;;
        *) PROJECT="$arg" ;;
      esac
    done

    PROJECT=$(detect_project "$PROJECT")

    echo -e "${BOLD}CTM Coordination Health Check${NC}"
    echo -e "${CYAN}Project:${NC} $PROJECT"
    echo ""

    "$SCRIPT_DIR/coord-health.sh" "$PROJECT" $FIX_FLAG
    ;;

  # ─────────────────────────────────────────────────────────────────────────
  # LOCKS
  # ─────────────────────────────────────────────────────────────────────────
  locks)
    PROJECT=$(detect_project "${1:-}")

    echo -e "${BOLD}Active Locks${NC}"
    echo -e "${CYAN}Project:${NC} $PROJECT"
    echo ""

    "$SCRIPT_DIR/coord-status.sh" "$PROJECT" --locks
    ;;

  # ─────────────────────────────────────────────────────────────────────────
  # RELEASE
  # ─────────────────────────────────────────────────────────────────────────
  release)
    if [[ $# -lt 1 ]]; then
      echo "Usage: ctm coordination release <lock_id> [project]" >&2
      exit 1
    fi

    LOCK_ID="$1"
    PROJECT=$(detect_project "${2:-}")

    echo -e "${BOLD}Force Releasing Lock${NC}"
    echo -e "${CYAN}Lock ID:${NC} $LOCK_ID"
    echo -e "${CYAN}Project:${NC} $PROJECT"
    echo ""

    "$SCRIPT_DIR/coord-release.sh" "$PROJECT" "$LOCK_ID" --force
    ;;

  # ─────────────────────────────────────────────────────────────────────────
  # STALE
  # ─────────────────────────────────────────────────────────────────────────
  stale)
    PROJECT=""
    CLEANUP_FLAG=""

    for arg in "$@"; do
      case $arg in
        --cleanup) CLEANUP_FLAG="--cleanup" ;;
        *) PROJECT="$arg" ;;
      esac
    done

    PROJECT=$(detect_project "$PROJECT")

    echo -e "${BOLD}Stale Agent Check${NC}"
    echo -e "${CYAN}Project:${NC} $PROJECT"
    echo ""

    "$SCRIPT_DIR/coord-heartbeat.sh" "$PROJECT" --check-stale $CLEANUP_FLAG
    ;;

  # ─────────────────────────────────────────────────────────────────────────
  # INIT
  # ─────────────────────────────────────────────────────────────────────────
  init)
    PROJECT="${1:-$(pwd)}"

    echo -e "${BOLD}Initializing Coordination${NC}"
    echo -e "${CYAN}Project:${NC} $PROJECT"
    echo ""

    # Create coordination directory
    mkdir -p "$PROJECT/.agent-workspaces"

    # Create empty log and snapshot
    touch "$PROJECT/.agent-workspaces/coord.log"
    "$SCRIPT_DIR/coord-rebuild.sh" "$PROJECT" --force >/dev/null

    echo -e "${GREEN}✓${NC} Created .agent-workspaces/"
    echo -e "${GREEN}✓${NC} Created coord.log"
    echo -e "${GREEN}✓${NC} Created coord-snapshot.json"
    echo ""
    echo "Coordination initialized for: $PROJECT"
    ;;

  # ─────────────────────────────────────────────────────────────────────────
  # HELP
  # ─────────────────────────────────────────────────────────────────────────
  help|--help|-h)
    show_help
    ;;

  # ─────────────────────────────────────────────────────────────────────────
  # UNKNOWN
  # ─────────────────────────────────────────────────────────────────────────
  *)
    echo "Unknown command: $COMMAND" >&2
    echo "Run 'ctm coordination help' for usage" >&2
    exit 1
    ;;

esac
