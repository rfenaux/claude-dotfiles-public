#!/usr/bin/env bash
# pre-warm-context.sh - Surface hot files at SessionStart (task-aware)
# Hook: SessionStart, once: true
# Budget: <200ms, fail-silent
# Phase 3.4: Enhanced with CTM task context for project-specific pre-warming

set +e  # fail-silent: hooks must not abort on error

METRICS_DIR="$HOME/.claude/metrics"
CTM_DIR="$HOME/.claude/ctm"

# Consume stdin
cat > /dev/null

# Find most recent weekly report
LATEST=$(ls -t "$METRICS_DIR"/weekly-*.md 2>/dev/null | head -1)
[[ -n "$LATEST" ]] || exit 0

# Get CTM active task context (if available)
TASK_PROJECT=""
TASK_TITLE=""
if [[ -d "$CTM_DIR" ]]; then
    # Read active task from CTM working memory
    ACTIVE=$(python3 -c "
import json, sys
from pathlib import Path
wm = Path('$CTM_DIR/working-memory.json')
if not wm.exists():
    sys.exit(0)
data = json.loads(wm.read_text())
agents = data.get('agents', [])
if agents:
    top = max(agents, key=lambda a: a.get('priority', 0))
    project = top.get('project', '')
    title = top.get('title', '')
    if project:
        print(f'{project}|{title}')
" 2>/dev/null || echo "")
    if [[ -n "$ACTIVE" ]]; then
        TASK_PROJECT="${ACTIVE%%|*}"
        TASK_TITLE="${ACTIVE##*|}"
    fi
fi

# Extract hot files section (top 5 file names)
# If we have a task project, filter hot files to that project
HOT_FILES=$(python3 -c "
import re, sys
from pathlib import Path

report = Path('$LATEST').read_text()
task_project = '$TASK_PROJECT'

# Find Hot Files section
match = re.search(r'## Hot Files.*?\n\n?((?:- .*\n)*)', report)
if not match:
    sys.exit(0)

lines = match.group(1).strip().split('\n')
names = []
project_names = []

for line in lines[:10]:  # Read more to filter
    m = re.search(r'\x60([^\x60]+)\x60', line)
    if m:
        path = m.group(1)
        name = path.split('/')[-1]
        names.append(name)
        # Check if file belongs to active task's project
        if task_project and task_project.lower() in path.lower():
            project_names.append(name)

# Prefer project-specific files, fall back to global
if project_names:
    result = project_names[:5]
    prefix = '[Pre-warm] Task files'
else:
    result = names[:5]
    prefix = '[Pre-warm] Hot files'

if result:
    print(f'{prefix}: ' + ', '.join(result))
" 2>/dev/null || echo "")

[[ -n "$HOT_FILES" ]] && echo "$HOT_FILES"

exit 0
