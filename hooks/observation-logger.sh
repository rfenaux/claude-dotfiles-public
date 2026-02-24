#!/usr/bin/env bash
# Observation Logger - PostToolUse hook
# Captures structured observations from tool usage into JSONL.
# Budget: <50ms, async background, fail-silent.
#
# Circuit breaker: skip if too many recent failures
. "$HOME/.claude/hooks/lib/circuit-breaker.sh" 2>/dev/null
check_circuit "observation-logger" || exit 0
start_timing "observation-logger"
# Input: JSON on stdin with tool_name, tool_input, tool_output (from Claude Code hook)

set +e  # fail-silent: hooks must not abort on error

OBS_DIR="$HOME/.claude/observations"
OBS_FILE="$OBS_DIR/active-session.jsonl"
CONFIG_FILE="$HOME/.claude/config/observation-config.json"

# Ensure directory exists (fast check)
[[ -d "$OBS_DIR" ]] || mkdir -p "$OBS_DIR"

# Read hook input from stdin
INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null || echo "")

# Skip if no tool name
[[ -z "$TOOL_NAME" ]] && exit 0

# Skip tools that are high-frequency / low-signal
case "$TOOL_NAME" in
  Glob|Grep|AskUserQuestion|EnterPlanMode|ExitPlanMode|TaskCreate|TaskUpdate|TaskList|TaskGet|TodoWrite|TodoRead|SendMessage|TeamCreate|TeamDelete|TaskStop|TaskOutput)
    exit 0
    ;;
esac

# Extract summaries (truncated for performance)
{
  TOOL_INPUT=$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
ti = d.get('tool_input', '')
if isinstance(ti, dict):
    # Extract most useful field based on tool type
    for key in ('file_path', 'command', 'url', 'query', 'prompt', 'pattern', 'path'):
        if key in ti:
            print(str(ti[key])[:200])
            sys.exit(0)
    print(json.dumps(ti)[:200])
else:
    print(str(ti)[:200])
" 2>/dev/null || echo "")

  TOOL_OUTPUT=$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
to = d.get('tool_output', '')
if isinstance(to, dict):
    # For Read tool, just record success/length, not content
    if 'content' in to:
        print(f'content_length={len(str(to[\"content\"]))}')
    else:
        print(json.dumps(to)[:300])
elif isinstance(to, str):
    print(to[:300])
else:
    print(str(to)[:300])
" 2>/dev/null || echo "")

  # Extract file paths from input
  FILES_TOUCHED=$(echo "$INPUT" | python3 -c "
import sys, json, re
d = json.load(sys.stdin)
ti = d.get('tool_input', {})
files = []
if isinstance(ti, dict):
    for key in ('file_path', 'path', 'notebook_path'):
        if key in ti and isinstance(ti[key], str):
            files.append(ti[key])
print(json.dumps(files))
" 2>/dev/null || echo "[]")

  # Build JSON line (compact)
  TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  PROJECT="${PWD}"

  python3 -c "
import json, sys
obs = {
    'ts': '$TS',
    'tool': '$TOOL_NAME',
    'input': sys.argv[1],
    'output': sys.argv[2],
    'files': json.loads(sys.argv[3]),
    'project': sys.argv[4]
}
print(json.dumps(obs, separators=(',', ':')))
" "$TOOL_INPUT" "$TOOL_OUTPUT" "$FILES_TOUCHED" "$PROJECT" >> "$OBS_FILE" || record_failure "observation-logger"

  # ── R5: AI compression (async, never blocks) ──
  echo "$INPUT" | python3 "$HOME/.claude/scripts/compress-observation.py" 2>/dev/null || true

  # ── Alert checking (inline, same background block) ──
  ALERT_CONFIG="$HOME/.claude/config/alert-rules.json"
  ALERT_FILE="$HOME/.claude/alerts/active.jsonl"
  if [[ -f "$ALERT_CONFIG" ]]; then
    python3 -c "
import json, re, sys
from datetime import datetime
try:
    with open('$ALERT_CONFIG') as f:
        config = json.load(f)
    tool_name = sys.argv[1]
    tool_input = sys.argv[2]
    tool_output = sys.argv[3]
    for rule in config.get('rules', []):
        if not rule.get('enabled', True):
            continue
        tm = rule.get('tool_match', [])
        if tm and tm != ['*'] and tool_name not in tm:
            continue
        field = rule.get('field', 'input')
        text = tool_input if field == 'input' else tool_output
        pattern = rule.get('pattern', '')
        if pattern and re.search(pattern, text):
            m = re.search(pattern, text)
            alert = {
                'ts': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                'rule_id': rule['id'],
                'rule_name': rule.get('name', rule['id']),
                'severity': rule.get('severity', 'INFO'),
                'tool': tool_name,
                'field': field,
                'match_excerpt': m.group(0)[:80] if m else '',
                'dismissed': False
            }
            with open('$ALERT_FILE', 'a') as af:
                af.write(json.dumps(alert, separators=(',',':')) + '\n')
except Exception:
    pass
" "$TOOL_NAME" "$TOOL_INPUT" "$TOOL_OUTPUT" 2>/dev/null || true
  fi
} &

# Fire and forget - background process handles the write
end_timing "observation-logger"
exit 0
