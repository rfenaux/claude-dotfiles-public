#!/bin/bash
# CTM Pre-Compact Hook
# Creates checkpoints and consolidates memory before context compaction
# Optimized: single Python invocation instead of 4 separate ones

set +e  # fail-silent: hooks must not abort on error

CTM_DIR="$HOME/.claude/ctm"
CTM_LIB="$CTM_DIR/lib"
LOG_FILE="$CTM_DIR/logs/hooks.log"

mkdir -p "$CTM_DIR/logs"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [pre-compact] $1" >> "$LOG_FILE"
}

log "Pre-compact hook triggered"

# Idempotency guard: skip if already ran within TTL (5 min)
source "$HOME/.claude/hooks/lib/idempotency.sh" 2>/dev/null || true
if ! check_idempotency "ctm-pre-compact" "$PWD" 2>/dev/null; then
    log "Skipping: idempotency guard (duplicate within TTL)"
    exit 0
fi

# Check if CTM is initialized
if [ ! -f "$CTM_DIR/scheduler.json" ]; then
    log "CTM not initialized, skipping"
    exit 0
fi

# Single Python invocation for all CTM operations
cd "$CTM_LIB"
python3 << 'EOF'
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, '.')

from scheduler import get_scheduler
from agents import get_agent, update_agent
from config import get_ctm_dir

scheduler = get_scheduler()
active_id = scheduler.get_active()

if not active_id:
    print("[CTM] No active agent to checkpoint")
    sys.exit(0)

agent = get_agent(active_id)
if not agent:
    sys.exit(0)

# --- 1. Create checkpoint ---
agent.timing["session_count"] += 1
agent.timing["last_active"] = datetime.now(timezone.utc).isoformat()

checkpoint_dir = Path.home() / ".claude" / "ctm" / "checkpoints"
checkpoint_dir.mkdir(parents=True, exist_ok=True)

checkpoint = {
    "agent_id": agent.id,
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "type": "pre_compact",
    "state": agent.state.copy(),
    "context_summary": {
        "decisions_count": len(agent.context.get("decisions", [])),
        "learnings_count": len(agent.context.get("learnings", [])),
        "files_count": len(agent.context.get("key_files", []))
    }
}

checkpoint_path = checkpoint_dir / f"{agent.id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
with open(checkpoint_path, 'w') as f:
    json.dump(checkpoint, f, indent=2)

update_agent(agent)
print(f"[CTM] Checkpoint created for [{agent.id}]")

# --- 2. Increment checkpoint counter ---
try:
    scheduler_path = get_ctm_dir() / 'scheduler.json'
    with open(scheduler_path, 'r') as f:
        data = json.load(f)
    data['session']['checkpoints'] = data['session'].get('checkpoints', 0) + 1
    with open(scheduler_path, 'w') as f:
        json.dump(data, f, indent=2)
except Exception:
    pass

# --- 3. Memory pressure management ---
try:
    from memory import manage_memory_pressure
    actions = manage_memory_pressure()
    if actions:
        print("[CTM] Memory pressure managed:")
        for a in actions[:3]:
            print(f"  - {a}")
except Exception:
    pass

# --- 4. Enhanced session snapshot ---
try:
    from session_snapshot import capture_snapshot
    snapshot = capture_snapshot(active_id)
    if snapshot:
        print(f"[CTM] Enhanced snapshot captured for [{active_id}]")
except Exception:
    pass

# --- 5. Auto-compress if context exceeds threshold ---
try:
    from compress import compress_agent_context
    context_size = len(json.dumps(agent.context or {})) // 4
    if context_size > 4000:
        result = compress_agent_context(active_id)
        if result and result.get("status") == "compressed":
            print(f"[CTM] Auto-compressed [{active_id}] ({context_size} tokens)")
except Exception:
    pass
EOF

# Git auto-commit after checkpoint
HOOKS_DIR="$HOME/.claude/hooks/ctm"
if [ -x "$HOOKS_DIR/git-auto-commit.sh" ]; then
    log "Triggering git auto-commit"
    "$HOOKS_DIR/git-auto-commit.sh" "$(pwd)" 2>/dev/null || true
fi

log "Pre-compact complete"
