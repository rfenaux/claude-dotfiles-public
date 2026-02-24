---
name: validate-hooks
description: Validate all hooks for anti-patterns, fail-silent compliance, circuit breaker coverage, and performance signals.
trigger: /validate-hooks
context: fork
agent: general-purpose
model: haiku
tools:
  - Read
  - Bash
  - Glob
  - Grep
user-invocable: true
---

# Hook Validator

Scans all registered hooks for anti-patterns and quality issues. Run after any hook change.

## Checks

### 1. Fail-Silent Compliance
- **FAIL** if any active hook uses `set -euo pipefail` (or `set -e` without compensating trap)
- **FAIL** if any hook does NOT end with `exit 0` (implicit or explicit)
- **WARN** if any hook uses bare `set -e` without `set +e` after initial checks

### 2. Circuit Breaker Coverage
- **WARN** if any PostToolUse or PreToolUse hook lacks circuit breaker (`. lib/circuit-breaker.sh`)
- **WARN** if any hook sources circuit-breaker.sh but never calls `record_failure`

### 3. Registration Integrity
- **FAIL** if `settings.json` references a hook file that does not exist
- **WARN** if a hook file exists in `hooks/` but is not registered in `settings.json` (exclude `archive/` and `lib/`)

### 4. Archive Orphan Detection
- **WARN** if any active hook imports from `hooks/archive/` (grep for `archive` in sys.path or source)

### 5. Performance Signals
- **WARN** if any hook uses `find` without `-maxdepth` in an inline (non-backgrounded) section
- **WARN** if any hook spawns more than 3 subprocesses inline (count `python3`, `jq`, `curl` calls outside `{ } &`)
- **INFO** if timing telemetry file exists, report slow hooks from `/tmp/claude-hook-timing/slow-hooks.jsonl`

### 6. Error Handling Patterns
- **WARN** if Python hooks use bare `except:` instead of `except Exception:`
- **WARN** if any hook has `set -euo pipefail` in a sourced/imported context

## Workflow

### Step 1: Load settings.json

Read `~/.claude/settings.json` and extract all registered hook commands.

```bash
python3 -c "
import json
with open('$HOME/.claude/settings.json') as f:
    s = json.load(f)
for event, entries in s.get('hooks', {}).items():
    for entry in entries:
        for hook in entry.get('hooks', []):
            cmd = hook.get('command', '')
            print(f'{event}|{cmd.split()[0] if cmd else \"\"}')" 2>/dev/null
```

### Step 2: Scan each hook

For each registered hook file:
1. Read the file content
2. Run all 6 check categories
3. Collect results as pass/warn/fail

### Step 3: Report

Output a table:

```
| Hook | Event | Fail-Silent | Circuit Breaker | record_failure | Registration | Archive | Performance |
|------|-------|-------------|-----------------|----------------|-------------|---------|-------------|
```

With pass/warn/fail per cell. Use colors: pass = no marker, warn = [W], fail = [F]

### Step 4: Slow Hooks Report

If `/tmp/claude-hook-timing/slow-hooks.jsonl` exists, report the slowest hooks:

```bash
if [ -f /tmp/claude-hook-timing/slow-hooks.jsonl ]; then
  echo "## Slow Hooks (>100ms)"
  cat /tmp/claude-hook-timing/slow-hooks.jsonl | python3 -c "
import sys, json
from collections import defaultdict
hooks = defaultdict(list)
for line in sys.stdin:
    d = json.loads(line)
    hooks[d['hook']].append(d['ms'])
for hook, times in sorted(hooks.items(), key=lambda x: -max(x[1])):
    print(f'  {hook}: max={max(times)}ms avg={sum(times)//len(times)}ms ({len(times)} samples)')
"
fi
```

### Step 5: Summary

```
Total hooks: N registered, M files
Passing all checks: N
Warnings: N
Failures: N
```

If any failures, list the top 5 recommended fixes.
