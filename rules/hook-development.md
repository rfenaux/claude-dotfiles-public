# Hook Development

Quality rules for creating and modifying hooks in `~/.claude/hooks/`.

| Rule | Details |
|------|---------|
| Execution time | Keep hooks under 1s — they run on every tool use |
| Subprocess spawning | Never spawn per-line; batch operations in single pass |
| JSON processing | Prefer `python3 -c` over complex `jq` pipelines for reliability |
| Error handling | Always fail-silent (`exit 0` on error) — broken hooks block all tool use |
| Iteration limit | If hook fails after 2 fix attempts, consider removing it entirely |
| Testing | Run hook manually with sample stdin before adding to settings.json |
| `set -euo pipefail` | **NEVER** use in hooks — non-zero exit codes propagate and kill the hook. Use `set +e` instead |
| Circuit breaker | **REQUIRED** for all PostToolUse/PreToolUse hooks — source `lib/circuit-breaker.sh` + `check_circuit` |
| `record_failure` | **ALWAYS** call in error paths when using circuit breaker (e.g., `cmd || record_failure "hook-name"`) |
| Archive imports | **NEVER** import from `hooks/archive/` — move needed modules to `~/.claude/security/` or `hooks/lib/` |
| Hot-path performance | PostToolUse hooks **MUST** stay under 100ms — use `start_timing`/`end_timing` from circuit-breaker.sh |

**Hook output contract:**
- `{}` or empty = allow (no feedback)
- `{"decision": "block", "reason": "..."}` = block + show reason
- Any non-JSON output = hook error (treated as allow)

**Before deploying:** Validate JSON output separately: `echo '{"test":true}' | bash hook.sh | python3 -c "import sys,json; json.load(sys.stdin)"`
