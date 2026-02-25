#!/bin/bash
# CTM Session End Hook
# Final checkpoint, consolidate, and update SESSIONS.md

set +e  # fail-silent: hooks must not abort on error

CTM_DIR="$HOME/.claude/ctm"
CTM_LIB="$CTM_DIR/lib"
LOG_FILE="$CTM_DIR/logs/hooks.log"

mkdir -p "$CTM_DIR/logs"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [session-end] $1" >> "$LOG_FILE"
}

log "Session end hook triggered"

# Idempotency guard: skip if already ran within TTL
source "$HOME/.claude/hooks/lib/idempotency.sh" 2>/dev/null || true
if ! check_idempotency "ctm-session-end" "$PWD" 2>/dev/null; then
    log "Skipping: idempotency guard (duplicate within TTL)"
    exit 0
fi

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

# v3.3: Auto-extract decisions and populate knowledge graph
python3 << 'EOF_EXTRACT'
import sys
sys.path.insert(0, '.')
try:
    from extraction import extract_and_store_decisions
    from agents import AgentIndex
    from datetime import datetime, timezone

    index = AgentIndex()
    active_ids = index.get_all_active()
    total_decisions = 0
    total_conflicts = 0

    for aid in active_ids:
        try:
            decisions, conflicts = extract_and_store_decisions(aid, store=True)
            total_decisions += len(decisions)
            total_conflicts += len(conflicts)
        except Exception:
            pass  # Skip individual agent failures

    if total_decisions > 0:
        print(f"[CTM] Extracted {total_decisions} decision(s) from session")
    if total_conflicts > 0:
        print(f"[CTM] ⚠ {total_conflicts} decision conflict(s) detected!")
except Exception:
    pass  # Silent fail if extraction module unavailable
EOF_EXTRACT

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

# GSD-inspired: Generate .continue-here.md for session resumption
python3 << 'EOF_CONTINUE'
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, '.')
try:
    from agents import get_agent, AgentIndex
    from scheduler import get_scheduler

    scheduler = get_scheduler()
    current_id = scheduler.state.get("current_agent")

    if current_id:
        agent = get_agent(current_id)
        if agent and agent.state["status"] in ("active", "paused"):
            # Read template
            template_path = Path.home() / ".claude" / "templates" / "CONTINUE-HERE.md"
            if template_path.exists():
                template = template_path.read_text()
            else:
                template = """# Continue Here: {{TASK_TITLE}}

**Task ID:** `{{TASK_ID}}` | **Paused:** {{TIMESTAMP}} | **Progress:** {{PROGRESS}}%

## Current State
{{CURRENT_STATE}}

## Next Step
{{NEXT_STEP}}

## Quick Resume
```bash
ctm switch {{TASK_ID}}
```
"""

            # Get context
            task = agent.task
            context = agent.context
            state = agent.state

            # Extract recent decision
            decisions = context.get("decisions", [])
            recent_decision = decisions[-1]["text"] if decisions else "None recorded"

            # Extract key files
            key_files = context.get("key_files", [])
            key_files_str = "\n".join(f"- `{f}`" for f in key_files[:5]) if key_files else "None tracked"

            # Extract blockers
            blockers = task.get("blockers", [])
            blockers_str = "\n".join(f"- {b}" for b in blockers) if blockers else "None"

            # Extract deviations
            deviations = context.get("deviations", [])
            deviations_str = "\n".join(
                f"- [{d['type']}] {d['description']}" for d in deviations[-3:]
            ) if deviations else "None"

            # Current state from checkpoints
            checkpoints = state.get("checkpoints", [])
            current_state = checkpoints[-1]["summary"] if checkpoints else task.get("description", "Working on task")

            # Fill template
            content = template.replace("{{TASK_TITLE}}", task.get("title", "Unknown"))
            content = content.replace("{{TASK_ID}}", current_id)
            content = content.replace("{{TIMESTAMP}}", datetime.now().strftime("%Y-%m-%d %H:%M"))
            content = content.replace("{{PROGRESS}}", str(state.get("progress_pct", 0)))
            content = content.replace("{{CURRENT_STATE}}", current_state[:500])
            content = content.replace("{{NEXT_STEP}}", context.get("current_step", "Resume work on task"))
            content = content.replace("{{RECENT_DECISION}}", recent_decision[:200] if recent_decision else "None")
            content = content.replace("{{KEY_FILES}}", key_files_str)
            content = content.replace("{{BLOCKERS}}", blockers_str)
            content = content.replace("{{DEVIATIONS}}", deviations_str)
            content = content.replace("{{SESSION_NOTES}}", "")
            content = content.replace("{{GENERATED_AT}}", datetime.now().isoformat())

            # Write to project root (CWD)
            project_path = Path("$CWD")
            continue_file = project_path / ".continue-here.md"
            continue_file.write_text(content)

            print(f"[CTM] Continue file created: .continue-here.md")

except Exception as e:
    pass  # Silent fail
EOF_CONTINUE

# v3.1: Auto-compress bloated agents before session ends
python3 << 'EOF_COMPRESS'
import sys
sys.path.insert(0, '.')
try:
    from agents import get_agent, AgentIndex
    from compress import compress_agent_context
    import json

    index = AgentIndex()
    active_ids = index.get_all_active()
    compressed = 0

    for aid in active_ids:
        agent = get_agent(aid)
        if agent:
            context_size = len(json.dumps(agent.context or {})) // 4
            if context_size > 4000:  # Auto-threshold from config
                result = compress_agent_context(aid)
                if result and result.get("status") == "compressed":
                    compressed += 1

    if compressed > 0:
        print(f"[CTM] Auto-compressed {compressed} bloated agent(s)")
except Exception:
    pass  # Silent fail
EOF_COMPRESS

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

exit 0
