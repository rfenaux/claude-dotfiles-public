#!/bin/bash
# Stop hook: Check if the last assistant turn contained destructive actions.
# Exit 0 = allow, Exit 2 = block (with reason on stdout)

# Read stdin
INPUT=$(cat)

# Extract tool calls from last assistant turn
TOOLS=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    messages = data.get('messages', [])
    for msg in reversed(messages):
        if msg.get('role') == 'assistant':
            content = msg.get('content', [])
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get('type') == 'tool_use':
                        name = block.get('name', '')
                        inp = json.dumps(block.get('input', {}))
                        print(f'{name}:{inp}')
            break
except Exception:
    pass
" 2>/dev/null)

# No tools = safe
[ -z "$TOOLS" ] && exit 0

# Check dangerous patterns
if echo "$TOOLS" | grep -qi 'git push\|rm -rf\|drop table\|drop database\|truncate table\|git reset --hard\|\-\-force'; then
    echo "Destructive action detected without explicit user request"
    exit 2
fi

exit 0
