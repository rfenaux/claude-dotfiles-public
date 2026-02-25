#!/bin/bash
set +e  # Never use set -e in hooks — non-zero exits kill the hook
# CTM Auto-Decompose Hook
# Triggered at PreCompact and SessionEnd
# Prompts Claude to decompose active tasks that lack subtask depth

CTM_DIR="$HOME/.claude/ctm"
CTM_LIB="$CTM_DIR/lib"

# Skip if CTM not initialized
[ ! -f "$CTM_DIR/scheduler.json" ] && exit 0

# Check for active tasks without children
cd "$CTM_LIB" 2>/dev/null || exit 0
python3 << 'PYEOF'
import json, sys
from pathlib import Path

index_file = Path.home() / ".claude/ctm/index.json"
if not index_file.exists():
    sys.exit(0)

index = json.loads(index_file.read_text())
agents = index.get("agents", {})

if not agents:
    sys.exit(0)

# Index format: agents are flat dicts with top-level "status", "title", "tags"
# Also check nested format (task.blockers, state.blocked_by) for full agent files

# Find tasks that have dependents (something is blocked-by them)
has_children = set()
for aid, agent in agents.items():
    # Flat format
    for b in agent.get("blockers", []):
        has_children.add(b)
    # Nested format (full agent files)
    for b in agent.get("task", {}).get("blockers", []):
        has_children.add(b)
    for b in agent.get("state", {}).get("blocked_by", []):
        has_children.add(b)

# Active/paused tasks with no children = need decomposition
orphan_parents = []
for aid, agent in agents.items():
    # Try flat format first, then nested
    status = agent.get("status", agent.get("state", {}).get("status", ""))
    if status in ("active", "paused") and aid not in has_children:
        title = agent.get("title", agent.get("task", {}).get("title", aid))
        orphan_parents.append(f"  - `{aid}`: {title}")

if not orphan_parents:
    sys.exit(0)

print("[CTM AUTO-DECOMPOSE] These active tasks have no subtasks:")
for t in orphan_parents:
    print(t)
print()
print("Consider decomposing into 2-4 subtasks each:")
print("  ctm spawn \"subtask\" --blocked-by <parent-id>")
PYEOF

exit 0
