#!/bin/bash
# CTM Session Start Hook
# Generates a briefing for the user at session start

set +e  # fail-silent: hooks must not abort on error

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

# Auto-enable CTM for project paths (configurable via PROJECTS_DIR)
AUTO_ENABLE_PATHS=(
    "${PROJECTS_DIR:-${HOME}/Projects}"
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

    # Find-or-reuse: look for existing canonical task for this project
    cd "$CTM_LIB"
    FIND_RESULT=$(python3 << PYEOF
import sys, os, json, glob
sys.path.insert(0, '.')
try:
    from agents import AgentIndex, get_agent, create_agent
    from scheduler import get_scheduler

    index = AgentIndex()
    scheduler = get_scheduler()
    project_path = "$PROJECT_CONTEXT"
    project_dir = project_path.split('/')[-1].lower()

    # Strategy 1: Check index by project path (fast, exact match)
    found_id = None
    active = index.get_all_active()
    for aid in active:
        info = index.get_info(aid)
        if not info:
            continue
        # Match by project path (exact or suffix)
        agent_project = info.get('project', '')
        if agent_project == project_path or agent_project.endswith('/' + project_path.split('/')[-1]):
            found_id = aid
            break
        # Fallback: match by title containing directory name
        if project_dir in info.get('title', '').lower():
            found_id = aid
            break

    # Strategy 2: Check agent files on disk (fallback)
    if not found_id:
        agents_dir = os.path.expanduser("~/.claude/ctm/agents")
        for fpath in glob.glob(os.path.join(agents_dir, "*.json")):
            try:
                with open(fpath) as f:
                    agent_data = json.load(f)
                agent_project = agent_data.get('context', {}).get('project', '')
                status = agent_data.get('state', {}).get('status', '')
                if status in ('cancelled', 'completed'):
                    continue
                if agent_project == project_path or agent_project.endswith('/' + project_path.split('/')[-1]):
                    found_id = os.path.basename(fpath).replace('.json', '')
                    break
            except (json.JSONDecodeError, IOError):
                continue

    if found_id:
        # Reuse existing task - just switch to it
        scheduler.switch_to(found_id)
        agent = get_agent(found_id)
        title = agent.task['title'] if agent else found_id
        print(f"REUSED:{found_id}:{title}")
    else:
        # Genuinely new project - spawn one task
        agent = create_agent(
            title="$PROJECT_CONTEXT".split('/')[-1],
            goal="Project tracker for: $PROJECT_CONTEXT".split('/')[-1],
            project="$PROJECT_CONTEXT",
            priority="high"
        )
        scheduler.switch_to(agent.id)
        print(f"SPAWNED:{agent.id}:{agent.task['title']}")

except Exception as e:
    print(f"ERROR:{e}")
PYEOF
2>/dev/null) || true

    if [[ "$FIND_RESULT" == REUSED:* ]]; then
        AGENT_INFO="${FIND_RESULT#REUSED:}"
        AGENT_ID="${AGENT_INFO%%:*}"
        AGENT_TITLE="${AGENT_INFO#*:}"
        log "Reused existing CTM task: $AGENT_ID ($AGENT_TITLE)"
    elif [[ "$FIND_RESULT" == SPAWNED:* ]]; then
        AGENT_INFO="${FIND_RESULT#SPAWNED:}"
        AGENT_ID="${AGENT_INFO%%:*}"
        AGENT_TITLE="${AGENT_INFO#*:}"
        echo ""
        echo "[CTM] New project task created: $AGENT_TITLE (ID: $AGENT_ID)"
        log "New CTM task spawned: $AGENT_ID ($AGENT_TITLE)"
    else
        log "Find-or-reuse failed: $FIND_RESULT"
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

# F2: Auto-resume suggestion — show highest-priority unfinished task
if [ -f "$HOME/.claude/ctm/config.json" ]; then
    AUTO_RESUME_ENABLED=$(python3 -c "
import json, sys
try:
    cfg = json.load(open('$HOME/.claude/ctm/config.json'))
    print('true' if cfg.get('auto_resume', {}).get('enabled', False) else 'false')
except: print('false')
" 2>/dev/null)

    if [ "$AUTO_RESUME_ENABLED" = "true" ]; then
        PROJECT_DIR_RESUME=""
        if git rev-parse --git-dir > /dev/null 2>&1; then
            PROJECT_DIR_RESUME=$(git rev-parse --show-toplevel 2>/dev/null)
        fi
        RESUME=$(python3 "$HOME/.claude/ctm/lib/auto_resume.py" "$PROJECT_DIR_RESUME" 2>/dev/null) || true
        if [ -n "$RESUME" ]; then
            echo ""
            echo "$RESUME"
            log "Auto-resume suggestion shown"
        fi
    fi
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
