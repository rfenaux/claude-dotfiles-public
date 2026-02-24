#!/usr/bin/env bash
# config-integrity-check.sh - Check reference integrity on config changes
# Hook: PostToolUse on Write|Edit to agents, hooks, skills, config, rules, scripts
# Budget: <100ms inline check, warnings only
# Rate limit: 1 check per 30s, debounce 2s
# Runs AFTER auto-regen-inventory.sh and auto-update-crossrefs.sh

set +e  # fail-silent: hooks must not abort on error

# Circuit breaker: skip if too many recent failures
. "$HOME/.claude/hooks/lib/circuit-breaker.sh" 2>/dev/null
check_circuit "config-integrity-check" || exit 0

CLAUDE_DIR="$HOME/.claude"
LOCK_FILE="/tmp/claude-integrity-check.lock"
DEBOUNCE_FILE="/tmp/claude-integrity-pending"
RATE_LIMIT_S=30

# Read hook input
INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null || echo "")
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null || echo "")

# Only process Write/Edit to config directories
case "$TOOL_NAME" in
  Write|Edit) ;;
  *) exit 0 ;;
esac

case "$FILE_PATH" in
  */.claude/agents/*.md) COMPONENT_TYPE="agent" ;;
  */.claude/skills/*/SKILL.md) COMPONENT_TYPE="skill" ;;
  */.claude/hooks/*.sh|*/.claude/hooks/*.py) COMPONENT_TYPE="hook" ;;
  */.claude/hooks/*.mjs) COMPONENT_TYPE="hook" ;;
  */.claude/rules/*.md) COMPONENT_TYPE="rule" ;;
  */.claude/scripts/*) COMPONENT_TYPE="script" ;;
  */.claude/config/*.json) COMPONENT_TYPE="config" ;;
  */.claude/settings.json) COMPONENT_TYPE="settings" ;;
  */.claude/CLAUDE.md) COMPONENT_TYPE="claude_md" ;;
  *) exit 0 ;;
esac

# Rate limit check
if [[ -f "$LOCK_FILE" ]]; then
  LOCK_AGE=$(( $(date +%s) - $(stat -f %m "$LOCK_FILE" 2>/dev/null || echo 0) ))
  [[ $LOCK_AGE -lt $RATE_LIMIT_S ]] && exit 0
fi

# Debounce + background check
{
  touch "$DEBOUNCE_FILE"
  sleep 2

  if [[ -f "$DEBOUNCE_FILE" ]]; then
    rm -f "$DEBOUNCE_FILE"
    touch "$LOCK_FILE"

    WARNINGS=""
    BASENAME=$(basename "$FILE_PATH" .md)
    BASENAME_NO_EXT=$(basename "$FILE_PATH" | sed 's/\.[^.]*$//')

    case "$COMPONENT_TYPE" in
      agent)
        # Check: if agent was deleted (file doesn't exist), check for ghost references
        if [[ ! -f "$FILE_PATH" ]]; then
          # Check agent-clusters.json for ghost member
          if grep -q "\"$BASENAME\"" "$CLAUDE_DIR/config/agent-clusters.json" 2>/dev/null; then
            WARNINGS="${WARNINGS}Ghost reference: '$BASENAME' still in agent-clusters.json but file deleted. "
          fi
          # Check CLAUDE.md routing tables
          if grep -q "\`$BASENAME\`" "$CLAUDE_DIR/CLAUDE.md" 2>/dev/null; then
            WARNINGS="${WARNINGS}Ghost reference: '$BASENAME' still in CLAUDE.md routing table but file deleted. "
          fi
        fi

        # Check: if agent has delegates_to, verify those agents exist
        if [[ -f "$FILE_PATH" ]]; then
          DELEGATES=$(python3 -c "
import sys, re
content = open('$FILE_PATH').read()
# Extract delegates_to from frontmatter
m = re.search(r'delegates_to:\s*\n((?:\s+-\s+\S+\n)*)', content)
if m:
    for line in m.group(1).strip().split('\n'):
        name = line.strip().lstrip('- ').strip()
        if name: print(name)
" 2>/dev/null || true)
          for delegate in $DELEGATES; do
            if [[ ! -f "$CLAUDE_DIR/agents/${delegate}.md" ]]; then
              WARNINGS="${WARNINGS}Broken delegates_to: '$delegate' in $BASENAME does not exist. "
            fi
          done
        fi
        ;;

      hook)
        # Check: is this hook registered in settings.json?
        if [[ -f "$FILE_PATH" ]] && ! grep -q "$FILE_PATH" "$CLAUDE_DIR/settings.json" 2>/dev/null; then
          # Also check without full path (just filename)
          if ! grep -q "$BASENAME_NO_EXT" "$CLAUDE_DIR/settings.json" 2>/dev/null; then
            WARNINGS="${WARNINGS}Unregistered hook: '$BASENAME_NO_EXT' exists but not found in settings.json. "
          fi
        fi
        ;;

      settings)
        # Check: all hook paths in settings.json point to existing files
        MISSING_HOOKS=$(python3 -c "
import json, os
try:
    with open('$CLAUDE_DIR/settings.json') as f:
        settings = json.load(f)
    for event, entries in settings.get('hooks', {}).items():
        for entry in entries:
            for hook in entry.get('hooks', []):
                cmd = hook.get('command', '')
                # Extract the script path (first word, expand ~)
                script = cmd.split()[0] if cmd else ''
                script = os.path.expanduser(script)
                if script and not os.path.exists(script):
                    print(script)
except: pass
" 2>/dev/null || true)
        for missing in $MISSING_HOOKS; do
          WARNINGS="${WARNINGS}Missing hook script: '$missing' referenced in settings.json but not found. "
        done
        ;;

      claude_md)
        # Check: routing table refs point to existing agents/skills
        GHOST_ROUTES=$(python3 -c "
import re, os
claude_dir = os.path.expanduser('~/.claude')
with open(os.path.join(claude_dir, 'CLAUDE.md')) as f:
    content = f.read()
# Extract routing sections
sections = re.findall(r'###[^#]*(?:Routing|Auto-Invoke)[^#]*\n((?:.*\n)*?)(?=\n##|\n---|\Z)', content)
routing = '\n'.join(sections)
for m in re.finditer(r'\|\s*\x60([a-z][a-z0-9_-]+)\x60\s*\|', routing):
    name = m.group(1)
    if not os.path.exists(os.path.join(claude_dir, 'agents', name + '.md')) and \
       not os.path.exists(os.path.join(claude_dir, 'skills', name, 'SKILL.md')):
        print(name)
" 2>/dev/null || true)
        for ghost in $GHOST_ROUTES; do
          WARNINGS="${WARNINGS}Ghost routing: '$ghost' in CLAUDE.md routing table but no agent/skill found. "
        done
        ;;

      config)
        # Check: if config file deleted, check for consumers
        if [[ ! -f "$FILE_PATH" ]]; then
          CONSUMERS=$(grep -rl "$BASENAME_NO_EXT" "$CLAUDE_DIR/hooks/" "$CLAUDE_DIR/scripts/" 2>/dev/null | head -3 || true)
          if [[ -n "$CONSUMERS" ]]; then
            WARNINGS="${WARNINGS}Deleted config '$BASENAME_NO_EXT.json' is referenced by: $(echo "$CONSUMERS" | xargs -I{} basename {} | tr '\n' ', '). "
          fi
        fi
        ;;
    esac

    # Output warning if any found
    if [[ -n "$WARNINGS" ]]; then
      echo "{\"feedback\": \"[Config Integrity] ${WARNINGS}\"}"
    fi
  fi
} &

exit 0
