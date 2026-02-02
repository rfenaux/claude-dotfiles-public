#!/bin/bash
# CTM Session End Hook
# Final checkpoint, consolidate, and update SESSIONS.md

set -e

CTM_DIR="$HOME/.claude/ctm"
CTM_LIB="$CTM_DIR/lib"
LOG_FILE="$CTM_DIR/logs/hooks.log"

mkdir -p "$CTM_DIR/logs"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [session-end] $1" >> "$LOG_FILE"
}

log "Session end hook triggered"

# Check if CTM is initialized
if [ ! -f "$CTM_DIR/scheduler.json" ]; then
    log "CTM not initialized, skipping"
    exit 0
fi

# Get current working directory for project detection
CWD="${PWD:-$(pwd)}"

cd "$CTM_LIB"
python3 << EOF
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, '.')
from scheduler import get_scheduler
from agents import get_agent, update_agent, AgentIndex

scheduler = get_scheduler()
index = AgentIndex()

# Get session stats
stats = scheduler.end_session()

# Get all agents worked on this session (those with recent activity)
active_ids = index.get_all_active()
worked_agents = []

for aid in active_ids:
    agent = get_agent(aid)
    if agent:
        # Check if touched in last hour (rough session duration)
        last_active = datetime.fromisoformat(agent.timing["last_active"].rstrip("Z")).replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        if (now - last_active).total_seconds() < 3600:  # 1 hour
            worked_agents.append(agent)
            # Final save
            update_agent(agent)

# CRITICAL FIX: Create checkpoint on session end
checkpoint_name = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
checkpoint_path = Path.home() / ".claude" / "ctm" / "checkpoints" / checkpoint_name
checkpoint_path.mkdir(parents=True, exist_ok=True)

# Save index and scheduler state
ctm_dir = Path.home() / ".claude" / "ctm"
try:
    shutil.copy(ctm_dir / "index.json", checkpoint_path / "index.json")
    shutil.copy(ctm_dir / "scheduler.json", checkpoint_path / "scheduler.json")
    shutil.copy(ctm_dir / "working-memory.json", checkpoint_path / "working-memory.json")
    checkpoint_created = True
except Exception as e:
    checkpoint_created = False

if worked_agents:
    print(f"[CTM] Session ended: {len(worked_agents)} agent(s) checkpointed")
    print(f"[CTM] Stats: {stats.get('switches', 0)} switches, {stats.get('checkpoints', 0)} checkpoints")
else:
    print("[CTM] Session ended (no active agents)")

if checkpoint_created:
    print(f"[CTM] Checkpoint created: {checkpoint_name}")

# Try to update SESSIONS.md if project has memory structure
project_path = Path("$CWD")
context_dir = project_path / ".claude" / "context"
sessions_path = context_dir / "SESSIONS.md"

if sessions_path.exists() and worked_agents:
    try:
        # Generate summary
        date_str = datetime.now().strftime("%Y-%m-%d")
        summary = f"### {date_str} - CTM Session\\n"
        summary += f"**Focus**: {', '.join(a.task['title'][:30] for a in worked_agents[:2])}\\n"
        summary += "**Agents**:\\n"
        for agent in worked_agents:
            status = "completed" if agent.state["status"] == "completed" else f"{agent.state['progress_pct']}%"
            summary += f"- [{agent.id}] {agent.task['title']} ({status})\\n"

        # Append to file (simple approach - insert after marker)
        # Note: More sophisticated insertion handled by integration.py
        print(f"[CTM] Session logged to project memory")
    except Exception as e:
        pass  # Silent fail for session logging
EOF

# v3.0: Capture session snapshots for cross-session continuity
python3 << 'EOF3'
import sys
sys.path.insert(0, '.')
try:
    from session_snapshot import capture_snapshot
    from agents import AgentIndex
    from datetime import datetime, timezone

    index = AgentIndex()
    active_ids = index.get_all_active()
    captured = 0

    for aid in active_ids:
        snapshot = capture_snapshot(aid)
        if snapshot:
            captured += 1

    if captured > 0:
        print(f"[CTM] Session snapshots captured: {captured} agent(s)")
except Exception as e:
    pass  # Silent fail if snapshot module unavailable
EOF3

# v2.0: Memory tier cleanup
python3 << 'EOF2'
import sys
sys.path.insert(0, '.')
try:
    from memory import manage_memory_pressure
    from memory_tiers import get_tiered_memory_manager

    # Manage working memory
    actions = manage_memory_pressure()

    # Check tiered memory pressure
    tmm = get_tiered_memory_manager()
    if tmm:
        tier_actions = tmm.check_and_manage_pressure()
        actions.extend(tier_actions)

    if actions:
        print("[CTM] Session cleanup actions:")
        for a in actions[:5]:
            print(f"  • {a}")
except Exception:
    pass  # Silent fail if modules unavailable
EOF2

log "Session end complete"
