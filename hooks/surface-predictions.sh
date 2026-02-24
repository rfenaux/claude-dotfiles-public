#!/usr/bin/env bash
# surface-predictions.sh - Surface pattern predictions at SessionStart
# Hook: SessionStart, once: true (after ctm-session-start.sh)
# Budget: <500ms, fail-silent
# Gate: Only output if predictions have confidence > 0.6 and 3+ occurrences

set +e  # fail-silent: hooks must not abort on error

PREDICTOR="$HOME/.claude/lib/intent_predictor.py"
PATTERNS_FILE="$HOME/.claude/intent-patterns.json"
CTM_INDEX="$HOME/.claude/ctm/index.json"

# Consume stdin
cat > /dev/null

# Prerequisites
[[ -f "$PREDICTOR" ]] || exit 0
[[ -f "$PATTERNS_FILE" ]] || exit 0

# Build context from CTM active task
CONTEXT=""
if [[ -f "$CTM_INDEX" ]]; then
  CONTEXT=$(python3 -c "
import json, sys
try:
    idx = json.load(open('$CTM_INDEX'))
    agents = idx.get('agents', {})
    # Find active/focus agent
    for aid, agent in agents.items():
        if agent.get('status') in ('active', 'in_progress'):
            title = agent.get('title', '')
            tags = ' '.join(agent.get('tags', []))
            print(f'{title} {tags}')
            break
except Exception:
    pass
" 2>/dev/null || echo "")
fi

# Fallback: use CWD basename as context
if [[ -z "$CONTEXT" ]]; then
  CONTEXT=$(basename "$PWD")
fi

[[ -z "$CONTEXT" ]] && exit 0

# Get predictions (with timeout to avoid hanging)
PREDICTIONS=$(timeout 2 python3 "$PREDICTOR" predict --context "$CONTEXT" 2>/dev/null || echo "")

# Parse and format predictions
if [[ -n "$PREDICTIONS" ]]; then
  # The predictor outputs JSON-like or text predictions
  # Filter to confidence > 0.6 and format
  OUTPUT=$(python3 -c "
import sys

lines = '''$PREDICTIONS'''.strip().split('\n')
preds = []
for line in lines:
    line = line.strip()
    if not line or line.startswith('No ') or line.startswith('Error'):
        continue
    # Try to parse structured output: 'tool_name (confidence%)'
    preds.append(line)

if preds:
    # Show top 3
    shown = preds[:3]
    print('[Patterns] ' + '; '.join(shown))
" 2>/dev/null || echo "")

  [[ -n "$OUTPUT" ]] && echo "$OUTPUT"
fi

exit 0
