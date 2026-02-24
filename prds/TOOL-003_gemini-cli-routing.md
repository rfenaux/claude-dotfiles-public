# PRD: TOOL-003 - Gemini CLI Auto-Routing Hook

> **STATUS: SCOPE SIMPLIFIED** - Query classification already exists (see GAP_ANALYSIS.md)

## Overview

### What Already Exists (from RAG_GUIDE.md)

```
✅ Query Classification: Categorizes queries by intent
   - where_is → Skip RAG, use Grep
   - how_to → Lessons first
   - decision → DECISIONS.md
   - bulk_analysis → (can route to Gemini!)
✅ Query Prefix Overrides: grep:, rag:, decision: prefixes
```

### Opportunity
The existing query classifier can be EXTENDED to detect Gemini delegation scenarios.
Instead of building classification from scratch, we hook into existing infrastructure.

### Problem Statement (Simplified)
Manual Gemini delegation misses optimization opportunities. But query classification already exists - we just need to:
1. Add delegation triggers to the classifier
2. Route detected scenarios to gemini-delegate

### Proposed Solution (Leveraging Existing)
Extend the existing query classifier with Gemini routing rules:
- Add `bulk_analysis` intent detection
- Add `large_context` intent detection
- Route matches to gemini-delegate

### Success Metrics
- 80%+ of delegable tasks auto-detected
- Zero false negatives on security-sensitive operations
- Hook execution time <50ms
- 30% reduction in Claude token usage for bulk work

## Requirements

### Functional Requirements

**FR-1: Extend Query Classifier** (LEVERAGE EXISTING)
Add delegation intents to existing classifier:
- `bulk_analysis` - "analyze all", "summarize files", "explore codebase"
- `large_context` - >50K tokens in context
- `multi_file_read` - 5+ file operations in sequence

**FR-2: Auto-Routing Logic**
When delegation intent detected:
1. Query classifier returns `intent: bulk_analysis`
2. Hook checks safety guardrails
3. Inject: `[AUTO-ROUTE: gemini-delegate for {reason}]`
4. Log decision

**FR-3: Safety Guardrails** (UNCHANGED)
NEVER auto-route if:
- Pattern matches security keywords
- Tool is Write, Edit, or Bash
- File paths contain sensitive patterns

**FR-4: Override Mechanism** (UNCHANGED)
- Environment variable: `CLAUDE_GEMINI_AUTOROUTE=off`
- Config setting: `~/.claude/config/gemini-routing.json`
- Inline override: "use Claude only"

**FR-5: Transparency** (UNCHANGED)
- Display routing decision before execution
- Log all decisions for audit

### Non-Functional Requirements

**NFR-1: Performance**
- Hook execution time: <50ms (target <25ms)
- No blocking on Gemini CLI availability check
- Async agent spawning (don't wait for completion)

**NFR-2: Reliability**
- Hook failures must not break tool execution
- Fallback to Claude if routing fails
- Retry logic if Gemini CLI unavailable (max 1 retry)

**NFR-3: Security**
- Whitelist-based approach (only route safe patterns)
- Log all routing decisions for audit
- Privacy mode: never log file paths or content

**NFR-4: Maintainability**
- Routing rules in JSON config (easily updatable)
- Clear logging for debugging
- Self-documenting routing reasons

### Out of Scope
- Auto-routing for Write/Edit operations (security risk)
- Cross-model result comparison (Gemini vs Claude)
- User preference learning (static rules only for MVP)
- Integration with codex-delegate (separate system)
- Routing to other LLMs beyond Gemini

## Technical Design

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Claude Code (Primary Conversation)                         │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ About to use tool (Read/Grep/Glob)
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  PreToolUse Hook: gemini-routing-hook.py                    │
│  1. Analyze tool + context                                  │
│  2. Check routing rules + safety                            │
│  3. If match → inject routing suggestion                    │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Claude sees: [AUTO-ROUTE: bulk analysis → gemini-delegate] │
│  Decision: Accept suggestion or proceed normally            │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼ (if accepted)
┌─────────────────────────────────────────────────────────────┐
│  gemini-delegate Agent (async:always)                       │
│  Executes via Gemini CLI, returns results                   │
└─────────────────────────────────────────────────────────────┘
```

### Data Model

**Routing Rules Config** (`~/.claude/config/gemini-routing.json`):
```json
{
  "enabled": true,
  "version": "1.0.0",
  "triggers": [
    {
      "name": "bulk_file_read",
      "tool": "Read",
      "threshold": {
        "file_count": 5,
        "time_window_seconds": 10
      },
      "confidence": 0.9,
      "reason": "Multiple file reads detected"
    },
    {
      "name": "large_grep_result",
      "tool": "Grep",
      "threshold": {
        "output_lines": 100,
        "output_mode": "content"
      },
      "confidence": 0.85,
      "reason": "Large grep result set"
    },
    {
      "name": "exploratory_glob",
      "tool": "Glob",
      "threshold": {
        "pattern_scope": "**/*",
        "expected_matches": 20
      },
      "confidence": 0.8,
      "reason": "Broad codebase exploration"
    },
    {
      "name": "user_intent_bulk",
      "tool": "*",
      "keywords": ["analyze all", "summarize files", "bulk", "explore codebase"],
      "confidence": 0.95,
      "reason": "User requested bulk operation"
    },
    {
      "name": "large_context_operation",
      "tool": "*",
      "threshold": {
        "input_tokens": 50000
      },
      "confidence": 0.75,
      "reason": "High token context detected"
    }
  ],
  "safety": {
    "blacklist_keywords": [
      "password", "token", "secret", "key", "credential",
      "auth", "api_key", "private", "confidential"
    ],
    "blacklist_paths": [
      ".env", ".ssh", ".aws", "credentials", "secrets",
      ".password", ".key"
    ],
    "blacklist_tools": ["Write", "Edit", "Bash"],
    "blacklist_directories": ["~/", "/Users/*/"]
  },
  "logging": {
    "enabled": true,
    "log_file": "~/.claude/logs/gemini-routing.log",
    "log_level": "info"
  }
}
```

**Routing Decision Log Entry**:
```json
{
  "timestamp": "2026-02-03T14:26:50Z",
  "session_id": "abc123",
  "tool": "Read",
  "trigger": "bulk_file_read",
  "confidence": 0.9,
  "files_count": 12,
  "decision": "routed",
  "reason": "Multiple file reads detected",
  "safety_check": "passed"
}
```

### API/Interface Changes

**New Hook in `~/.claude/settings.json`**:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Read",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/gemini-routing-hook.py --tool Read"
          }
        ]
      },
      {
        "matcher": "Grep",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/gemini-routing-hook.py --tool Grep"
          }
        ]
      },
      {
        "matcher": "Glob",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/gemini-routing-hook.py --tool Glob"
          }
        ]
      }
    ]
  }
}
```

**Hook Script Output** (injected into context):
```
[AUTO-ROUTE: Consider gemini-delegate for bulk file analysis (12 files, 85K tokens). Reason: Multiple file reads detected. Confidence: 90%]
```

### Dependencies

- Python 3.8+ (for hook script)
- `~/.claude/config/gemini-routing.json` (routing rules)
- Gemini CLI installed and accessible (`which gemini`)
- `gemini-delegate` agent present in `~/.claude/agents/`
- `jq` for JSON parsing (already installed)

## Implementation Plan

### Phase 1 (MVP) - 4-5 hours (REDUCED from 6h)

**Goal:** Extend existing query classifier with Gemini routing

1. **Add Delegation Intents to Classifier** (1.5h)
   - Locate existing query classification code
   - Add `bulk_analysis`, `large_context`, `multi_file_read` intents
   - Add detection patterns

2. **Create Routing Hook** (1.5h)
   - Hook checks classifier output
   - If delegation intent → check safety → suggest route
   - Simpler than building classification from scratch

3. **Add Safety Guardrails** (0.5h)
   - Blacklist patterns (existing patterns from config)
   - Tool restrictions (Read/Grep/Glob only)

4. **Wire Up to settings.json** (0.5h)
   - Add PreToolUse hook
   - Test integration

5. **Testing** (1h)
   - Test bulk operations route correctly
   - Test security blocks work
   - Measure latency

### Phase 2 (Enhancement) - 3 hours (REDUCED from 4h)

**Goal:** Feedback and monitoring

1. **Logging** (1h)
   - Log routing decisions
   - Track acceptance rate

2. **Override Mechanism** (1h)
   - Session-level disable
   - Config-level disable

3. **Dashboard Integration** (1h)
   - Add routing stats to dashboard
   - Token savings estimation

### Future Considerations
- Machine learning model for routing prediction (replace static rules)
- Cross-model result quality comparison (Gemini vs Claude)
- User preference profiles (per-project routing rules)
- Integration with codex-delegate (multi-model routing)
- Real-time token cost estimation before routing
- A/B testing framework for routing strategies

## Verification Criteria

### Unit Tests
- `gemini-routing-hook.py` loads config correctly
- Trigger detection logic matches expected patterns
- Safety checks block blacklisted keywords/paths
- Hook execution completes in <50ms
- Log entries written correctly

### Integration Tests
- PreToolUse hook invoked before Read/Grep/Glob
- Routing suggestion appears in Claude context
- gemini-delegate receives auto-routed tasks
- Safety guardrails prevent sensitive data routing
- Override mechanism disables routing correctly

### UAT Scenarios

**Scenario 1: Bulk File Analysis**
1. User: "Summarize all markdown files in docs/"
2. Claude about to use multiple Read calls
3. Hook detects bulk operation
4. Routing suggestion injected
5. gemini-delegate executes
6. Results returned to Claude

**Scenario 2: Security Block**
1. User: "Analyze .env file"
2. Claude about to Read .env
3. Hook detects blacklisted path
4. Routing blocked (safety)
5. Claude proceeds normally with Read

**Scenario 3: Single File (No Route)**
1. User: "Read config.json"
2. Claude about to Read single file
3. Hook evaluates: below threshold
4. No routing suggestion
5. Claude proceeds normally

**Scenario 4: User Override**
1. User: "Analyze files using Claude only"
2. Session override flag set
3. Claude about to use multiple Reads
4. Hook detects bulk but sees override
5. No routing suggestion

**Scenario 5: Performance Check**
1. Trigger hook 100 times in rapid succession
2. Measure average execution time
3. Verify <50ms per invocation
4. Verify no tool execution delays

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Hook adds latency to tool use | High | Medium | Profile hook; cache config; optimize rule evaluation |
| False positives waste agent spawns | Medium | Medium | Tune confidence thresholds; add user feedback loop |
| False negatives miss optimization | Low | Medium | Log near-misses; analyze patterns; adjust triggers |
| Security breach via blacklist bypass | High | Low | Whitelist approach; multi-layer safety checks; audit logs |
| Gemini CLI unavailable | Medium | Low | Fallback to Claude; retry logic; offline detection |
| Config file corruption breaks routing | Medium | Low | Validate JSON on load; fall back to defaults; backup config |

## Timeline Estimate

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| MVP (Phase 1) | 4-5 hours | Existing query classifier |
| Enhancement (Phase 2) | 3 hours | Phase 1 complete |
| Testing + Documentation | 1 hour | Phase 1 complete |
| **Total** | **8-9 hours** | - |

**EFFORT REDUCTION:** 12h → 8-9h (savings: ~3 hours)

**Reason:** Query classification infrastructure already exists:
- Intent detection patterns exist
- Routing logic exists (where_is → Grep)
- Just need to add delegation intents

**Priority:** High (quick win)
**Effort:** Low (extend existing classifier)
**Impact:** High (saves tokens, reduces cognitive load)

**Recommendation:** Implement immediately. Leverage existing classifier rather than building from scratch.

---

*PRD Version: 2.0 (Revised after GAP_ANALYSIS.md)*
*Created: 2026-02-03*
*Revised: 2026-02-03*
*Author: Claude (Worker Agent)*
