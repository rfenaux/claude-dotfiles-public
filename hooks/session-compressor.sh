#!/usr/bin/env bash
# Session Compressor - Stop/SessionEnd hook
# Compresses active-session.jsonl into structured markdown summary.
# Strategy A: Ollama llama3.2:3b structured summary
# Strategy B (fallback): jq/python rule-based extraction
# Output: summaries/{DATE}_{SESSION_ID}.md with YAML frontmatter

set +e  # fail-silent: hooks must not abort on error

# Circuit breaker: skip if too many recent failures
. "$HOME/.claude/hooks/lib/circuit-breaker.sh" 2>/dev/null
check_circuit "session-compressor" || exit 0

OBS_DIR="$HOME/.claude/observations"
ACTIVE_FILE="$OBS_DIR/active-session.jsonl"
ARCHIVE_DIR="$OBS_DIR/archive"
SUMMARIES_DIR="$OBS_DIR/summaries"
CONFIG_FILE="$HOME/.claude/config/observation-config.json"

# Ensure directories exist
mkdir -p "$ARCHIVE_DIR" "$SUMMARIES_DIR"

# Skip if no active session file or empty
[[ -f "$ACTIVE_FILE" ]] || exit 0
[[ -s "$ACTIVE_FILE" ]] || exit 0

# Read config
COMPRESSION_MODEL="llama3.2:3b"
RETENTION_DAYS=30
if [[ -f "$CONFIG_FILE" ]]; then
  COMPRESSION_MODEL=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE')).get('compression_model', 'llama3.2:3b'))" 2>/dev/null || echo "llama3.2:3b")
  RETENTION_DAYS=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE')).get('retention_days', 30))" 2>/dev/null || echo "30")
fi

# Generate session metadata
SESSION_DATE=$(date -u +"%Y-%m-%d")
SESSION_ID=$(date -u +"%H%M%S")-$$
SUMMARY_FILE="$SUMMARIES_DIR/${SESSION_DATE}_${SESSION_ID}.md"
ENTRY_COUNT=$(wc -l < "$ACTIVE_FILE" | tr -d ' ')

# Write structured data to temp file (avoids shell variable escaping issues)
TEMP_DATA=$(mktemp)
trap "rm -f '$TEMP_DATA'" EXIT

python3 << 'PYEOF' > "$TEMP_DATA"
import json, sys
from collections import defaultdict
from pathlib import Path

obs_file = Path.home() / ".claude" / "observations" / "active-session.jsonl"
if not obs_file.exists():
    sys.exit(0)

tools = defaultdict(int)
files_written = set()
files_read = set()
commands = []
web_urls = []
projects = set()

for line in obs_file.read_text().strip().split("\n"):
    if not line.strip():
        continue
    try:
        entry = json.loads(line)
    except Exception:
        continue

    tool = entry.get("tool", "")
    inp = entry.get("input", "")
    files = entry.get("files", [])
    project = entry.get("project", "")

    tools[tool] += 1
    if project:
        projects.add(project)

    if tool in ("Write", "Edit"):
        for f in files:
            files_written.add(f)
    elif tool == "Read":
        for f in files:
            files_read.add(f)
    elif tool == "Bash":
        if inp:
            commands.append(inp[:100])
    elif tool == "WebFetch":
        if inp:
            web_urls.append(inp[:150])

result = {
    "tool_counts": dict(tools),
    "files_written": sorted(files_written)[:30],
    "files_read": sorted(files_read)[:30],
    "commands": commands[:20],
    "web_urls": web_urls[:10],
    "projects": sorted(projects),
    "total_entries": sum(tools.values()),
}
print(json.dumps(result))
PYEOF

# Exit if no data extracted
[[ -s "$TEMP_DATA" ]] || exit 0

# Strategy A: Try Ollama compression
OLLAMA_SUCCESS=false
if curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
  # Check if model is available
  if curl -sf http://localhost:11434/api/tags | python3 -c "import sys,json; models=[m['name'] for m in json.load(sys.stdin).get('models',[])]; sys.exit(0 if any('$COMPRESSION_MODEL' in m for m in models) else 1)" 2>/dev/null; then

    # Build Ollama request JSON safely via Python reading from file
    OLLAMA_REQUEST=$(python3 -c "
import json, sys
data = open(sys.argv[1]).read().strip()
prompt = 'Analyze this session activity data and create a structured summary.\n\nSession data:\n' + data + '\n\nCreate a concise summary with these sections:\n1. INVESTIGATED: What files/topics were explored\n2. LEARNED: Key patterns or discoveries\n3. COMPLETED: What was accomplished\n4. NEXT_STEPS: Likely next actions based on unfinished work\n\nKeep each section to 2-4 bullet points max. Be specific about file paths and tool usage.'
print(json.dumps({'model': sys.argv[2], 'prompt': prompt, 'stream': False, 'options': {'temperature': 0.3, 'num_predict': 500}}))
" "$TEMP_DATA" "$COMPRESSION_MODEL" 2>/dev/null || echo "")

    if [[ -n "$OLLAMA_REQUEST" ]]; then
      RESPONSE=$(echo "$OLLAMA_REQUEST" | curl -sf --max-time 30 http://localhost:11434/api/generate -d @- 2>/dev/null \
        | python3 -c "import sys,json; print(json.load(sys.stdin).get('response',''))" 2>/dev/null || echo "")

      if [[ -n "$RESPONSE" && ${#RESPONSE} -gt 50 ]]; then
        OLLAMA_SUCCESS=true
      fi
    fi
  fi
fi

# Strategy B: Rule-based fallback (read from temp file, not shell variable)
if [[ "$OLLAMA_SUCCESS" != "true" ]]; then
  RESPONSE=$(python3 -c "
import json, sys

data = json.load(open(sys.argv[1]))
lines = []

read_files = data.get('files_read', [])
if read_files:
    lines.append('## INVESTIGATED')
    for f in read_files[:10]:
        lines.append(f'- Read: \`{f}\`')
    lines.append('')

written = data.get('files_written', [])
if written:
    lines.append('## COMPLETED')
    for f in written[:10]:
        lines.append(f'- Modified: \`{f}\`')
    lines.append('')

tools = data.get('tool_counts', {})
if tools:
    lines.append('## TOOL USAGE')
    for tool, count in sorted(tools.items(), key=lambda x: -x[1]):
        lines.append(f'- {tool}: {count}x')
    lines.append('')

cmds = data.get('commands', [])
if cmds:
    lines.append('## COMMANDS')
    for cmd in cmds[:10]:
        lines.append(f'- \`{cmd}\`')
    lines.append('')

print('\n'.join(lines))
" "$TEMP_DATA" 2>/dev/null || echo "No observations to summarize.")
fi

# Extract projects list safely from temp file
PROJECTS_JSON=$(python3 -c "import json,sys; print(json.dumps(json.load(open(sys.argv[1])).get('projects',[])))" "$TEMP_DATA" 2>/dev/null || echo "[]")

# Write summary with YAML frontmatter
cat > "$SUMMARY_FILE" << EOF
---
date: $SESSION_DATE
session_id: $SESSION_ID
entry_count: $ENTRY_COUNT
compression: $([ "$OLLAMA_SUCCESS" = "true" ] && echo "ollama" || echo "rule-based")
projects: $PROJECTS_JSON
---

# Session Summary: $SESSION_DATE ($SESSION_ID)

$RESPONSE
EOF

# Index summary to RAG (if RAG is initialized for observations)
if [[ -d "$OBS_DIR/.rag" ]]; then
  ~/.local/bin/uv run --directory ~/.claude/mcp-servers/rag-server python -c "
import sys
sys.path.insert(0, '${HOME}/.claude/mcp-servers/rag-server/src')
from rag_server.server import rag_index
try:
    rag_index('$SUMMARY_FILE', '$OBS_DIR')
except Exception:
    pass
" 2>/dev/null &
fi

# Archive the raw session file
mv "$ACTIVE_FILE" "$ARCHIVE_DIR/${SESSION_DATE}_${SESSION_ID}.jsonl" || record_failure "session-compressor"

# Cleanup: remove archives older than retention period
find "$ARCHIVE_DIR" -name "*.jsonl" -mtime +${RETENTION_DAYS} -delete 2>/dev/null || true
find "$SUMMARIES_DIR" -name "*.md" -mtime +${RETENTION_DAYS} -delete 2>/dev/null || true

exit 0
