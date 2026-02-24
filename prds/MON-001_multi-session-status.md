# PRD: MON-001 — Multi-Session Status Monitoring

## Overview

### Problem Statement
The menu bar app (`claude-menubar.py`) and `status.json` support only one active Claude Code session. When running parallel sessions (e.g., main + background agent, or two project windows), each session's PostToolUse hook overwrites the same `~/.claude/status.json`, causing the menu bar to flicker between sessions and display stale/incorrect data.

### Proposed Solution
Switch from a single `status.json` to per-session status files in `~/.claude/status/`, with an aggregator that produces a combined view for the menu bar and dashboard. The dashboard's session discovery layer is already multi-session aware — this PRD bridges the status reporting layer to match.

### Success Metrics
- Menu bar correctly shows 2+ concurrent sessions without flickering
- Stale session files auto-cleaned within 5 minutes of session end
- Zero performance regression on PostToolUse hook (<100ms budget maintained)
- Dashboard shows live status for all active sessions

---

## Requirements

### Functional Requirements

**FR-1: Per-Session Status Files**
- Each session writes to `~/.claude/status/<session_id>.json` instead of `~/.claude/status.json`
- Same schema as current status.json (v1.0.0), no field changes
- Atomic write pattern preserved (`.tmp` + `mv`)

**FR-2: Status Aggregator**
- New `~/.claude/status/index.json` file aggregated from all per-session files
- Schema: `{ "sessions": [...], "summary": { "total": N, "active": N, "total_agents": N, "max_context_pct": N, "load": {...} } }`
- Updated by the hook after writing per-session file (lightweight — just reads dir + builds summary)

**FR-3: Menu Bar Multi-Session Display**
- Title format changes from `☁️ Claude: [task] | Ctx:22% | 2a | ✓` to:
  - Single session: `☁️ [task] | Ctx:22% | 0a | ✓` (same as now, no "Claude:" prefix to save space)
  - Multi-session: `☁️ 2s | Ctx:22%/65% | 3a | ✓` (session count, top-2 context %, total agents)
- Dropdown shows expandable per-session details
- Each session entry shows: task name, context %, agent count, last updated

**FR-4: Stale Session Cleanup**
- Sessions not updated in >5 minutes marked as stale
- Sessions not updated in >30 minutes auto-removed from status dir
- Cleanup runs as part of the aggregator (no separate process)

**FR-5: Dashboard Integration**
- New API endpoint `GET /api/status/live` returns aggregated status for all active sessions
- Dashboard "Overview" tab shows live session cards alongside existing RAG/Ollama status
- Reuses existing `/api/sessions` for historical data

### Non-Functional Requirements

**NFR-1: Performance**
- Per-session write + aggregation must stay under 100ms total (PostToolUse hook budget)
- Menu bar poll interval stays at 5s

**NFR-2: Backward Compatibility**
- If only one session active, behavior identical to current single-session mode
- Legacy `~/.claude/status.json` maintained as symlink to most-recent session file (for any external tools reading it)

---

## Technical Design

### Architecture

```
PostToolUse Hook (update-status.sh)
  │
  ├── Write: ~/.claude/status/<session_id>.json
  │
  └── Aggregate: ~/.claude/status/index.json
        │
        ├── claude-menubar.py (polls index.json every 5s)
        │
        └── Dashboard API /api/status/live (reads index.json)
```

### Files to Modify

1. **`~/.claude/hooks/update-status.sh`** (~20 lines changed)
   - Change output path from `~/.claude/status.json` to `~/.claude/status/<session_id>.json`
   - Add aggregator: scan `~/.claude/status/*.json`, build `index.json`
   - Add cleanup: remove files older than 30 minutes
   - Maintain backward-compat symlink

2. **`~/.claude/scripts/claude-menubar.py`** (~60 lines changed)
   - Read `index.json` instead of `status.json`
   - Multi-session title rendering logic
   - Per-session dropdown entries
   - Fallback: if `index.json` missing, try legacy `status.json`

3. **`~/.claude/rag-dashboard/server.py`** (~30 lines added)
   - New endpoint `GET /api/status/live` reading `index.json`

4. **`~/.claude/rag-dashboard/index-v2.html`** (~50 lines added)
   - Live session cards in Overview tab

### Data Model

**Per-session file** (`~/.claude/status/<session_id>.json`):
```json
{
  "version": "1.1.0",
  "updated_at": "2026-02-14T20:30:00Z",
  "session_id": "dba15d59-...",
  "task": { "name": "Log analysis", "id": "abc123", "progress": 45, "status": "active" },
  "context": { "current_tokens": 44000, "total_tokens": 200000, "percentage": 22 },
  "agents": { "active": 2, "names": ["researcher", "coder"] },
  "load": { "profile": "balanced", "status": "OK", "load_avg": 3.2 }
}
```

**Aggregated index** (`~/.claude/status/index.json`):
```json
{
  "updated_at": "2026-02-14T20:30:00Z",
  "sessions": [
    { "session_id": "dba15d59-...", "task": "Log analysis", "context_pct": 22, "agents": 2, "status": "active", "updated_at": "..." },
    { "session_id": "f7c23a01-...", "task": "Code review", "context_pct": 65, "agents": 1, "status": "active", "updated_at": "..." }
  ],
  "summary": {
    "total_sessions": 2,
    "active_sessions": 2,
    "stale_sessions": 0,
    "total_agents": 3,
    "max_context_pct": 65,
    "load": { "profile": "balanced", "status": "OK", "load_avg": 3.2 }
  }
}
```

---

## Implementation Plan

### Phase 1: Per-Session Status + Aggregator (~3h)
1. Create `~/.claude/status/` directory structure
2. Modify `update-status.sh` to write per-session + aggregate + cleanup
3. Add backward-compat symlink for legacy `status.json`
4. Test: run two `echo` hooks manually with different session IDs, verify two files + index

### Phase 2: Menu Bar Multi-Session (~2h)
1. Update `claude-menubar.py` to read `index.json`
2. Multi-session title rendering
3. Per-session dropdown entries
4. Fallback to legacy `status.json`
5. Test: simulate 2 sessions, verify menu bar shows both

### Phase 3: Dashboard Integration (~2h)
1. Add `/api/status/live` endpoint to `server.py`
2. Add live session cards to `index-v2.html` Overview tab
3. Test: open dashboard, verify live status alongside RAG metrics

**Total: ~7 hours**

---

## Verification Criteria
- [ ] Two concurrent sessions each write separate status files
- [ ] `index.json` aggregates correctly with session count and summary
- [ ] Menu bar shows `2s | Ctx:22%/65% | 3a` format when 2 sessions active
- [ ] Menu bar falls back to single-session format with 1 session
- [ ] Stale files (>30 min) auto-cleaned on next hook fire
- [ ] Legacy `status.json` symlink works for backward compat
- [ ] Dashboard `/api/status/live` returns all active sessions
- [ ] Hook execution stays under 100ms with aggregation

---

## Risks
- **File system overhead**: Many parallel sessions could create many status files → mitigated by 30-min cleanup
- **Race condition on index.json**: Two hooks writing aggregate simultaneously → mitigated by atomic write pattern (`.tmp` + `mv`)
- **Hook performance**: Aggregation adds ~10ms (dir scan + JSON build) → well within 100ms budget

---

## Timeline
Phase 1: 3h | Phase 2: 2h | Phase 3: 2h | **Total: ~7h**

---

## PRD Index Update
Add to `PRD_INDEX.md` as:
`| MON-001 | Multi-Session Status Monitoring | Medium | Medium | 📋 Specified |`
