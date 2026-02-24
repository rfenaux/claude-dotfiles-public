# Hook Validation Report

**Generated:** 2026-02-23
**Validator:** `~/.claude-fow/skills/validate-hooks/`

---

## Executive Summary

- **Total Active Hooks:** 59 files
- **Registered but Orphaned:** 2 commands (echo, python3)
- **Passing All Checks:** 17 hooks (28%)
- **Warnings:** 42 hooks (71%)
- **Critical Failures:** 2 invalid registrations

**Status:** Configuration needs stabilization. No production-blocking failures, but 26 high-frequency hooks (PreToolUse/PostToolUse) lack circuit breaker protection, creating cascading failure risk.

---

## Critical Issues

### 1. Invalid Hook Registrations (BLOCKER)

Two shell commands are registered as hooks but have no implementation files:

#### Issue 1: Bare echo command
- **File:** `~/.claude/settings.json` line 63-64
- **Registration:** `echo "[TIMESTAMP: $(date '+%Y-%m-%d %H:%M:%S')]"`
- **Event:** UserPromptSubmit
- **Problem:** This is a shell one-liner, not a proper hook script
- **Impact:** Runs on every user prompt, adds no real value
- **Fix:** Remove these lines from settings.json

#### Issue 2: Orphaned python3 command
- **File:** `~/.claude/settings.json` line 415
- **Registration:** `python3 ~/.claude/lessons/scripts/confidence.py decay 2>/dev/null || true`
- **Event:** SessionStart (once: true)
- **Problem:** Path references lessons/scripts which may not exist or be intended
- **Impact:** Will fail silently or skip lessons decay at session start
- **Fix:** Verify the script path exists and is intentional. If not, remove registration.

---

## Architecture Warnings

### 2. Circuit Breaker Coverage Gap

**Scope:** 26 hooks run on every tool use (PreToolUse/PostToolUse) without circuit breaker protection

#### Problem
These hooks execute on every single tool invocation. If any fails, it can cascade and block subsequent tools. Without circuit breaker protection (`lib/circuit-breaker.sh`), a single buggy hook breaks the entire tool execution chain.

#### PreToolUse Hooks Missing Circuit Breaker (11)
Blocks ALL tool execution if they fail:
- `~/.claude/hooks/csb-bash-guard.py`
- `~/.claude/hooks/csb-edit-guard.py`
- `~/.claude/hooks/csb-fp-preventer.py`
- `~/.claude/hooks/csb-write-guard.py`
- `~/.claude/hooks/csb-pretool-defense.sh`
- `~/.claude/hooks/critical-file-guard.sh`
- `~/.claude/hooks/gemini-routing-hook.py`
- `~/.claude/hooks/outgoing-data-guard.py`
- `~/.claude/hooks/search-routing-reminder.sh`
- `~/.claude/hooks/settings-backup.sh`

#### PostToolUse Hooks Missing Circuit Breaker (15)
Delays or blocks results if they fail:
- `~/.claude/hooks/assumption-validator.sh`
- `~/.claude/hooks/auto-regen-inventory.sh`
- `~/.claude/hooks/config-integrity-check.sh`
- `~/.claude/hooks/csb-posttool-scanner.py`
- `~/.claude/hooks/csb-webfetch-cache.py`
- `~/.claude/hooks/observation-logger.sh`
- `~/.claude/hooks/pattern-tracker.sh`
- `~/.claude/hooks/post-tool-learning.sh`
- `~/.claude/hooks/rag-index-on-write.sh`
- `~/.claude/hooks/update-status.sh`
- `~/.claude/hooks/usage-tracker.sh`
- `~/.claude/hooks/validate-syntax.sh`

#### Recommendation
Add to top of each hook:
```bash
. lib/circuit-breaker.sh
trap 'record_failure "$0" "$?"' EXIT
```

---

### 3. Performance Issues

#### Subprocess Overflow

18 hooks spawn more than 3 external processes, adding significant latency:

**High-Risk (>10 spawns) — immediate optimization needed:**
- `~/.claude/hooks/update-status.sh` (15) — PostToolUse
- `~/.claude/hooks/session-compressor.sh` (12) — SessionEnd
- `~/.claude/hooks/auto-update-crossrefs.sh` (11) — PostToolUse
- `~/.claude/hooks/subagent-logger.sh` (11) — SubagentStart/TaskCompleted

**Medium-Risk (4-10 spawns):**
- `~/.claude/hooks/observation-logger.sh` (7)
- `~/.claude/hooks/auto-heal-services.sh` (8)
- `~/.claude/hooks/auto-reindex-stale.sh` (7)
- `~/.claude/hooks/save-conversation.sh` (8)
- `~/.claude/hooks/failure-learning.sh` (6)
- `~/.claude/hooks/ctm-session-end.sh` (6)
- `~/.claude/hooks/mcp-preflight.sh` (6)
- `~/.claude/hooks/post-tool-learning.sh` (8)

#### Recommendation
Batch subprocess calls: collect work items first, execute once with aggregated data instead of spawning per item.

#### Find Command Safety

7 hooks use `find` without `-maxdepth`, risking deep directory traversals:

- `~/.claude/hooks/auto-reindex-stale.sh`
- `~/.claude/hooks/auto-sync-decisions.sh`
- `~/.claude/hooks/auto-update-crossrefs.sh`
- `~/.claude/hooks/daily-memory-log.sh`
- `~/.claude/hooks/rag-staleness-check.sh`
- `~/.claude/hooks/save-conversation.sh`
- `~/.claude/hooks/session-compressor.sh`
- `~/.claude/hooks/setup-handler.sh`

**Fix:** Add `-maxdepth 3` or `-maxdepth 1` depending on scope.

---

### 4. Fail-Silent Compliance

6 hooks may exit with non-zero status without explicit `exit 0`:
- `~/.claude/hooks/global-privacy-guard.sh`
- `~/.claude/hooks/memory-flush-precompact.sh`
- `~/.claude/hooks/notification-sound.sh`
- `~/.claude/hooks/setup-handler.sh`
- `~/.claude/hooks/subagent-logger.sh`

**Fix:** Verify all end with explicit `exit 0`.

---

### 5. Archive Imports

1 hook imports from archived code:
- `~/.claude/hooks/csb-posttool-scanner.py` references `archive/`

**Fix:** Consolidate to active code, remove dead reference.

---

## Full Hook Validation Table

| Hook | Event | Fail-Silent | Circuit Breaker | Registration | Archive | Performance |
|------|-------|-------------|-----------------|-------------|---------|-------------|
| assumption-validator.sh | PostToolUse | PASS | [W] | PASS | PASS | [W] |
| audience-detector.sh | UserPromptSubmit | PASS | PASS | PASS | PASS | PASS |
| auto-heal-services.sh | SessionStart | PASS | PASS | PASS | PASS | [W] |
| auto-monthly-report.sh | SessionStart | PASS | PASS | PASS | PASS | PASS |
| auto-regen-inventory.sh | PostToolUse | PASS | [W] | PASS | PASS | PASS |
| auto-reindex-stale.sh | SessionStart | PASS | PASS | PASS | PASS | [W] |
| auto-sync-decisions.sh | SessionEnd | PASS | PASS | PASS | PASS | [W] |
| auto-update-crossrefs.sh | PostToolUse | PASS | [W] | PASS | PASS | [W] |
| auto-weekly-report.sh | SessionStart | PASS | PASS | PASS | PASS | PASS |
| claude-config-backup.sh | SessionEnd | PASS | PASS | PASS | PASS | PASS |
| config-integrity-check.sh | PostToolUse | PASS | [W] | PASS | PASS | [W] |
| critical-file-guard.sh | PreToolUse | PASS | [W] | PASS | PASS | [W] |
| csb-approve-handler.py | UserPromptSubmit | PASS | PASS | PASS | PASS | PASS |
| csb-bash-guard.py | PreToolUse | PASS | [W] | PASS | PASS | PASS |
| csb-edit-guard.py | PreToolUse | PASS | [W] | PASS | PASS | PASS |
| csb-fp-preventer.py | PreToolUse | PASS | [W] | PASS | PASS | PASS |
| csb-posttool-scanner.py | PostToolUse | PASS | [W] | PASS | [W] | PASS |
| csb-pretool-defense.sh | PreToolUse | PASS | [W] | PASS | PASS | PASS |
| csb-webfetch-cache.py | PostToolUse | PASS | [W] | PASS | PASS | [W] |
| csb-write-guard.py | PreToolUse | PASS | [W] | PASS | PASS | PASS |
| ctm-message-check.sh | SessionStart | PASS | PASS | PASS | PASS | PASS |
| ctm/ctm-auto-decompose.sh | PreCompact | PASS | PASS | PASS | PASS | PASS |
| ctm/ctm-pre-compact.sh | PreCompact | PASS | PASS | PASS | PASS | PASS |
| ctm/ctm-session-end.sh | SessionEnd | PASS | PASS | PASS | PASS | [W] |
| ctm/ctm-session-start.sh | SessionStart | PASS | PASS | PASS | PASS | [W] |
| daily-memory-log.sh | SessionStart | PASS | PASS | PASS | PASS | [W] |
| device-check.sh | SessionStart | PASS | PASS | PASS | PASS | [W] |
| failure-learning.sh | PostToolUseFailure | PASS | PASS | PASS | PASS | [W] |
| gemini-routing-hook.py | PreToolUse | PASS | [W] | PASS | PASS | PASS |
| global-privacy-guard.sh | UserPromptSubmit | [W] | PASS | PASS | PASS | PASS |
| healing-summary.sh | SessionStart | PASS | PASS | PASS | PASS | PASS |
| log-compaction-event.sh | PreCompact | PASS | PASS | PASS | PASS | PASS |
| mcp-preflight.sh | SessionStart | PASS | PASS | PASS | PASS | [W] |
| memory-flush-precompact.sh | PreCompact | [W] | PASS | PASS | PASS | PASS |
| notification-sound.sh | Notification | [W] | PASS | PASS | PASS | PASS |
| observation-logger.sh | PostToolUse | PASS | [W] | PASS | PASS | [W] |
| outgoing-data-guard.py | PreToolUse | PASS | [W] | PASS | PASS | PASS |
| pattern-tracker.sh | PostToolUse | PASS | [W] | PASS | PASS | [W] |
| permission-auto-handler.sh | PermissionRequest | PASS | PASS | PASS | PASS | PASS |
| post-tool-learning.sh | PostToolUse | PASS | [W] | PASS | PASS | [W] |
| pre-warm-context.sh | SessionStart | PASS | PASS | PASS | PASS | PASS |
| proactive-rag-surfacer.sh | SessionStart | PASS | PASS | PASS | PASS | [W] |
| rag-cascade-inject.sh | UserPromptSubmit | PASS | PASS | PASS | PASS | PASS |
| rag-index-on-write.sh | PostToolUse | PASS | [W] | PASS | PASS | [W] |
| rag-staleness-check.sh | SessionStart | PASS | PASS | PASS | PASS | [W] |
| save-conversation.sh | PreCompact/SessionEnd | PASS | PASS | PASS | PASS | [W] |
| search-routing-reminder.sh | PreToolUse | PASS | [W] | PASS | PASS | PASS |
| session-compressor.sh | SessionEnd | PASS | PASS | PASS | PASS | [W] |
| session-context-cleanup.sh | SessionEnd | PASS | PASS | PASS | PASS | PASS |
| session-metrics-collector.sh | SessionEnd | PASS | PASS | PASS | PASS | PASS |
| settings-backup.sh | PreToolUse | PASS | [W] | PASS | PASS | PASS |
| setup-handler.sh | Setup | [W] | PASS | PASS | PASS | [W] |
| stop-safety-review.sh | Stop | PASS | PASS | PASS | PASS | PASS |
| subagent-logger.sh | SubagentStart/TaskCompleted | [W] | PASS | PASS | PASS | [W] |
| surface-predictions.sh | SessionStart | PASS | PASS | PASS | PASS | PASS |
| update-status.sh | PostToolUse | PASS | [W] | PASS | PASS | [W] |
| usage-tracker.sh | PostToolUse | PASS | [W] | PASS | PASS | PASS |
| validate-syntax.sh | PostToolUse | PASS | [W] | PASS | PASS | PASS |

**Legend:** PASS = no issues, [W] = warning, [F] = failure

---

## Recommended Action Plan

### Phase 1: Critical (2 min)
1. **Fix settings.json registrations**
   - Remove echo command (line 63-64)
   - Fix python3 command path (line 415) or remove

### Phase 2: High Priority (30 min)
2. **Add circuit breaker to 26 hooks**
   - Template: Add `. lib/circuit-breaker.sh` and trap at top
   - Focus on: all PreToolUse and PostToolUse hooks

### Phase 3: Performance (45 min)
3. **Optimize SessionStart hooks**
   - Background long-running hooks
   - Add timeouts for discovery operations

4. **Fix find commands** (15 min)
   - Add `-maxdepth N` to 7 hooks

### Phase 4: Cleanup (60 min)
5. **Batch subprocess calls**
   - Consolidate multiple curl/jq/python3 calls
   - Review: session-compressor.sh, update-status.sh, subagent-logger.sh

---

## Files to Review

- `~/.claude/settings.json` — Register/unregister hooks
- `~/.claude/hooks/lib/circuit-breaker.sh` — Reference implementation
- `~/.claude/hooks/lib/idempotency.sh` — For duplicate-prevention
- All 59 active hook files listed above

---

## Running the Validator

```bash
python3 /tmp/validate_hooks.py
```

Or use the dedicated skill:
```
/validate-hooks
```
