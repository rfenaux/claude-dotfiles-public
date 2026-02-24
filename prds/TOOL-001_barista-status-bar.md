# PRD: TOOL-001 - Barista Status Bar Integration

## Overview

### Problem Statement
Users working with Claude Code lack persistent visibility into system state across contexts. Critical information like active task, token usage, agent status, and resource load is only visible within the Claude Code terminal interface. When switching between applications or working across multiple desktops, this context is lost.

macOS users already use Barista or similar menu bar applications for persistent system monitoring. However, Claude Code has no integration with these tools, forcing users to switch to the terminal to check state.

### Proposed Solution
Integrate Claude Code status reporting with Barista macOS menu bar application to provide real-time, persistent visibility into:
- Current CTM task (name + progress)
- Token usage (current/total + percentage)
- Active agents count
- Resource load profile (OK/CAUTION/HIGH_LOAD)
- Session ID

This creates a "heads-up display" that's always visible regardless of focused application.

### Success Metrics
- Status updates in menu bar within 2 seconds of state changes
- Zero performance impact on Claude Code operations
- Clear, scannable format readable at a glance
- Integration requires <50 lines of configuration

## Requirements

### Functional Requirements

**FR-1: Status Reporting**
- Expose Claude Code state via file-based API or HTTP endpoint
- Update state on: tool use, agent spawn/complete, context window changes
- Include: task name, token count, agent list, load profile, session ID

**FR-2: Barista Configuration**
- Provide Barista plugin/script to read Claude Code state
- Format output for menu bar display (max 50 chars)
- Support click-through to dashboard or terminal

**FR-3: Update Frequency**
- Passive monitoring (Barista polls every 5-10 seconds)
- OR event-driven updates via file watch
- Minimize CPU overhead (<0.1% average)

**FR-4: Fallback Behavior**
- If Claude Code not running, display "Idle"
- If state file stale (>30s), display warning indicator
- Graceful degradation if dashboard unavailable

### Non-Functional Requirements

**NFR-1: Performance**
- No measurable impact on Claude Code response time
- State updates should not block tool execution
- Barista polling should not trigger rate limits

**NFR-2: Privacy**
- No sensitive data (file paths, code snippets) in status
- Task names truncated if >30 chars
- Option to disable status reporting

**NFR-3: Compatibility**
- macOS 12+ (Barista minimum version)
- Works with existing Claude Code hooks system
- No changes to core Claude Code behavior

**NFR-4: Maintainability**
- Single configuration file for Barista integration
- State format documented and versioned
- Self-healing if state file corrupted

### Out of Scope
- Windows/Linux menu bar integration (future consideration)
- Real-time streaming updates (polling sufficient for MVP)
- Historical status logs (dashboard already handles this)
- Click actions beyond opening dashboard URL

## Technical Design

### Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────┐
│  Claude Code    │──────▶│  State File      │◀─────│  Barista    │
│  (Hooks)        │writes │  (~/.claude/     │polls │  (Menu Bar) │
│                 │       │   status.json)   │      │             │
└─────────────────┘      └──────────────────┘      └─────────────┘
        │                                                  │
        │                                                  │
        └──────────────────────────────────────────────────┘
                   Optional: Dashboard URL link
```

**State Flow:**
1. PostToolUse hook writes status to `~/.claude/status.json`
2. Barista polls file every 5 seconds
3. Barista formats output and displays in menu bar
4. Click opens dashboard at `http://localhost:8420`

### Data Model

**State File Format** (`~/.claude/status.json`):
```json
{
  "version": "1.0.0",
  "updated_at": "2026-02-03T14:26:50Z",
  "session_id": "abc123",
  "task": {
    "name": "Implement PRD tracking",
    "progress": 65,
    "status": "active"
  },
  "context": {
    "current_tokens": 45000,
    "total_tokens": 200000,
    "percentage": 22
  },
  "agents": {
    "active": 2,
    "names": ["gemini-delegate", "deliverable-reviewer"]
  },
  "load": {
    "profile": "balanced",
    "status": "OK",
    "cpu_percent": 3.2
  }
}
```

**Barista Display Format:**
```
Claude: [task] | Ctx:22% | 2 agents | OK
```

### API/Interface Changes

**New Hook:** `PostToolUse` addition in `~/.claude/settings.json`

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/update-barista-status.sh"
          }
        ]
      }
    ]
  }
}
```

**New Script:** `~/.claude/hooks/update-barista-status.sh`
- Reads CTM status (`ctm status --json`)
- Reads context window from CLI state
- Reads active agents from `~/.agent-workspaces/*/HANDOFF.md`
- Writes to `~/.claude/status.json`
- Total execution time: <100ms

**Barista Plugin:** `~/.barista/plugins/claude-code.sh`
- Polls `~/.claude/status.json`
- Formats output for menu bar
- Handles click to open dashboard

### Dependencies

- Barista macOS app (user must install separately)
- `jq` for JSON processing (already installed)
- Claude Code Dashboard running on port 8420 (optional)
- CTM system (`ctm status --json` available)

## Implementation Plan

### Phase 1 (MVP)
**Goal:** Basic status reporting to file + Barista display

1. Create `update-barista-status.sh` hook script (2 hours)
   - Extract CTM task name/progress
   - Calculate token percentage from statusLine output
   - Count active agents
   - Write JSON to `~/.claude/status.json`

2. Add PostToolUse hook to settings.json (15 mins)
   - Test hook triggers correctly
   - Verify no performance impact

3. Create Barista plugin script (1 hour)
   - Poll status file every 5s
   - Format for menu bar display
   - Add click handler for dashboard URL

4. Test across scenarios (1 hour)
   - Active task with agents
   - Idle state
   - High context usage
   - Agent spawning/completion

**Total Estimate:** 4.5 hours

### Phase 2 (Enhancement)
**Goal:** Richer display options + error handling

1. Add status colors/icons (30 mins)
   - Green: OK load
   - Yellow: CAUTION load
   - Red: HIGH_LOAD
   - Gray: Idle

2. Click menu for quick actions (1 hour)
   - Primary click: Open dashboard
   - Right-click menu: Pause reporting, View logs, Reload config

3. Stale state detection (30 mins)
   - If `updated_at` >30s old, show warning
   - Fallback to "Idle" if file missing

4. Privacy mode (30 mins)
   - Environment variable `CLAUDE_BARISTA_ENABLED=false`
   - Truncate task names to first 20 chars

**Total Estimate:** 2.5 hours

### Future Considerations
- Windows Task Bar integration (via Python script)
- Linux system tray integration (via Python + GTK)
- Real-time updates via WebSocket (eliminate polling)
- Historical status graphs in Barista tooltip
- Deep links to specific tasks (click opens CTM task detail)
- Integration with Raycast or Alfred for quick actions

## Verification Criteria

### Unit Tests
- `update-barista-status.sh` produces valid JSON
- Status file updates within 2s of tool use
- Script handles missing CTM gracefully
- Script handles dashboard unavailability

### Integration Tests
- Barista displays status correctly when Claude Code active
- Barista shows "Idle" when Claude Code not running
- Click opens dashboard in default browser
- Status updates reflected within 10s of state change

### UAT Scenarios

**Scenario 1: Normal Operation**
1. Start Claude Code session with active CTM task
2. Verify Barista shows task name + token %
3. Spawn an agent
4. Verify agent count increments in menu bar
5. Complete agent
6. Verify agent count decrements

**Scenario 2: High Load Warning**
1. Spawn multiple agents to reach load threshold
2. Verify Barista shows "CAUTION" or "HIGH_LOAD"
3. Complete agents
4. Verify status returns to "OK"

**Scenario 3: Idle State**
1. Exit Claude Code
2. Verify Barista shows "Idle" within 30s
3. Restart Claude Code
4. Verify status reappears

**Scenario 4: Privacy Mode**
1. Set `CLAUDE_BARISTA_ENABLED=false`
2. Verify no status updates written
3. Verify Barista shows "Disabled"

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Hook degrades performance | High | Low | Profile hook execution time; skip if >100ms |
| Status file grows unbounded | Medium | Low | Overwrite file atomically (no append) |
| Barista plugin breaks on macOS update | Medium | Medium | Use stable APIs only; document dependencies |
| Users don't have Barista installed | Low | High | Make integration optional; document alternatives |
| Status leaks sensitive data | High | Low | Whitelist only safe fields; add privacy mode |

## Timeline Estimate

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| MVP (Phase 1) | 4.5 hours | Barista installed by user |
| Enhancement (Phase 2) | 2.5 hours | Phase 1 complete |
| Testing + Documentation | 2 hours | Phase 1 complete |
| **Total** | **9 hours** | - |

**Priority:** Low (nice-to-have)
**Effort:** Medium (requires Barista installation + testing)
**Impact:** Medium (improves awareness but not critical to workflow)

**Recommendation:** Implement as weekend project or during low-priority period. Not on critical path for core Claude Code functionality.

---

*PRD Version: 1.0*
*Created: 2026-02-03*
*Author: Claude (Worker Agent)*
