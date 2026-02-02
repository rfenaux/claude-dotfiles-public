#!/bin/bash
# CTM Session Start Hook
# Generates a briefing for the user at session start

set -e

CTM_DIR="$HOME/.claude/ctm"
CTM_LIB="$CTM_DIR/lib"
LOG_FILE="$CTM_DIR/logs/hooks.log"

# Ensure log directory exists
mkdir -p "$CTM_DIR/logs"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [session-start] $1" >> "$LOG_FILE"
}

log "Session start hook triggered"

# v2.1: Capture project context from current working directory
PROJECT_CONTEXT="${PWD:-$(pwd)}"
log "Project context: $PROJECT_CONTEXT"

# Check if CTM is initialized
if [ ! -f "$CTM_DIR/index.json" ]; then
    log "CTM not initialized, skipping"
    exit 0
fi

# Auto-enable CTM for specific project paths
AUTO_ENABLE_PATHS=(
    "~/Documents/Projects - Pro/<COMPANY>"
)

check_auto_enable() {
    local current_path="$1"
    for pattern in "${AUTO_ENABLE_PATHS[@]}"; do
        if [[ "$current_path" == "$pattern"* ]]; then
            echo "$pattern"
            return 0
        fi
    done
    return 1
}

if matched_path=$(check_auto_enable "$PROJECT_CONTEXT"); then
    log "Auto-enable path matched: $matched_path"

    # Check if there's an active task for this project
    cd "$CTM_LIB"
    HAS_ACTIVE=$(python3 << PYEOF
import sys
sys.path.insert(0, '.')
try:
    from agents import AgentIndex
    index = AgentIndex()
    active = index.get_all_active()
    # Check if any active agent is for this project context
    project_name = "$PROJECT_CONTEXT".split('/')[-1]
    for aid in active:
        agent = index.get(aid)
        if agent and project_name.lower() in agent.get('task', {}).get('title', '').lower():
            print("ACTIVE")
            sys.exit(0)
    print("NONE")
except Exception as e:
    print("NONE")
PYEOF
2>/dev/null) || true

    if [ "$HAS_ACTIVE" = "NONE" ]; then
        # Extract project name from path
        PROJECT_NAME=$(basename "$PROJECT_CONTEXT")
        log "No active CTM task for <COMPANY> project: $PROJECT_NAME - auto-spawning"

        # Auto-spawn CTM task
        cd "$CTM_LIB"
        SPAWN_RESULT=$(python3 << SPAWNEOF
import sys
sys.path.insert(0, '.')
try:
    from agents import AgentIndex, create_agent
    from scheduler import get_scheduler

    # Create new agent for this project
    agent = create_agent(
        title="$PROJECT_NAME",
        goal="Auto-spawned for <COMPANY> project: $PROJECT_NAME",
        priority="high"
    )

    # Switch to it
    scheduler = get_scheduler()
    scheduler.switch_to(agent.id)

    print(f"SPAWNED:{agent.id}")
except Exception as e:
    print(f"ERROR:{e}")
SPAWNEOF
2>/dev/null) || true

        if [[ "$SPAWN_RESULT" == SPAWNED:* ]]; then
            AGENT_ID="${SPAWN_RESULT#SPAWNED:}"
            echo ""
            echo "[CTM] Auto-spawned task for <COMPANY> project: $PROJECT_NAME (ID: $AGENT_ID)"
            log "Auto-spawned CTM task: $AGENT_ID"
        else
            log "Failed to auto-spawn: $SPAWN_RESULT"
            echo ""
            echo "[CTM] Auto-spawn failed for $PROJECT_NAME - run manually: ctm spawn \"$PROJECT_NAME\" --switch"
        fi
    fi
fi

# Start session and generate brief using Python
cd "$CTM_LIB"
BRIEF=$(python3 << EOF
import sys
import os
sys.path.insert(0, '.')

# v2.1: Get project context from environment
PROJECT_CONTEXT = "$PROJECT_CONTEXT"

try:
    from pathlib import Path
    from agents import AgentIndex, get_agent
    from scheduler import get_scheduler
    from briefing import generate_compact_briefing
    from memory import WorkingMemory

    index = AgentIndex()
    scheduler = get_scheduler()
    wm = WorkingMemory()

    # Get active agents
    active_ids = index.get_all_active()
    if not active_ids:
        sys.exit(0)

    # v2.1: Start session with project context
    scheduler.start_session(PROJECT_CONTEXT)

    # CRITICAL FIX: Pre-load top priority agents into working memory
    scheduler.rebuild_queue()
    queue = scheduler.get_queue()

    # Load top 3-5 agents into working memory
    loaded_count = 0
    for item in queue[:5]:
        if wm.load(item['id']):
            loaded_count += 1

    if loaded_count > 0:
        print(f"[CTM] Loaded {loaded_count} agent(s) into working memory")

    # v2.0: Load into tiered memory (L2 working tier)
    try:
        from memory_tiers import get_tiered_memory_manager
        tmm = get_tiered_memory_manager()
        if tmm:
            for item in queue[:3]:  # Top 3 into L2
                tmm.promote(item['id'], 2)  # L2_WORKING
    except Exception:
        pass  # Silent if tiered memory not available

    # v2.1: Generate compact briefing with project context
    brief = generate_compact_briefing(Path(PROJECT_CONTEXT))
    print(brief)

    # Show top priority if we have agents
    if queue:
        top = queue[0]
        agent = get_agent(top['id'])
        if agent:
            pct = agent.state.get('progress_pct', 0)
            step = agent.state.get('current_step', '')
            print(f"  → Top: [{agent.id}] {agent.task['title']} ({pct}%)")
            if step:
                print(f"    Step: {step[:50]}")

except Exception as e:
    # Silent fail - don't interrupt session start
    pass
EOF
2>/dev/null) || true

if [ -n "$BRIEF" ]; then
    echo "$BRIEF"
    log "Briefing generated successfully"
else
    log "No briefing to show"
fi

# Add git context if in a git repo
if git rev-parse --git-dir > /dev/null 2>&1; then
    PROJECT_DIR=$(git rev-parse --show-toplevel 2>/dev/null)
    PROJECT_NAME=$(basename "$PROJECT_DIR")

    # Get recent commits (last 24 hours)
    RECENT=$(git log --since="24 hours ago" --format="%h %s" 2>/dev/null | head -5)

    if [ -n "$RECENT" ]; then
        echo ""
        echo "[Git] Recent changes in $PROJECT_NAME:"
        echo "$RECENT" | while read line; do
            echo "  • $line"
        done
    fi

    # Check for uncommitted changes
    UNCOMMITTED=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
    if [ "$UNCOMMITTED" -gt 0 ]; then
        echo "  ⚠ $UNCOMMITTED uncommitted files"
    fi

    log "Git context added for $PROJECT_NAME"
fi

log "Session start complete"

# Quick health check (silent if OK, shows warnings if issues)
HEALTH=$("$HOME/.claude/scripts/validate-setup.sh" --quick 2>/dev/null) || true
if echo "$HEALTH" | grep -q "⚠"; then
    echo ""
    echo "$HEALTH"
    log "Health check found issues"
fi
