# PRD: CTM-001 - Goal-Backward Verification System

> Ensure task completion means actual goal achievement, not just checking boxes

## Overview

### Problem Statement

Current CTM workflow allows marking tasks complete without verifying actual goal achievement:
- User runs `ctm complete` and agent transitions to "completed" status
- No automated verification that acceptance criteria were met
- Task may be marked complete when blockers still exist or goals unachieved
- No systematic check that deliverables actually exist

This leads to:
- False completion signals in priority queue
- Incomplete work resurfacing weeks later
- Erosion of trust in CTM task tracking
- Manual re-checking required before trusting "completed" status

**Current behavior:**
```bash
$ ctm complete auth2026
✓ Completed [auth2026]: Auth setup
```

**No validation that:**
- Auth tests pass
- OAuth2 config is deployed
- Documentation is updated
- Integration is verified

### Proposed Solution

Implement **goal-backward verification**: define success criteria upfront, verify backwards from goal before allowing completion.

**New behavior:**
```bash
$ ctm complete auth2026

Verifying completion criteria...

Task: Auth setup
Goal: Add OAuth2 login to the app

Acceptance Criteria:
  ✓ 1. OAuth2 provider configured (GitHub)
  ✓ 2. Login route responds with 302 redirect
  ✗ 3. Tests pass for token validation
  ? 4. Deployment verified in staging

3/4 criteria met. Blockers:
  - Tests failing: test_token_validation (auth.test.ts:45)
  - Staging verification skipped

Mark complete anyway? [y/N]
```

### Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| False completions | <5% of completed tasks | Audit completed tasks for reopens within 7 days |
| Verification criteria defined | >80% of spawned tasks | Check `agent.task.acceptance_criteria` |
| Auto-verification success | >60% first-time pass | Check completion attempts vs. successes |
| User satisfaction | "Makes me confident tasks are done" | Qualitative feedback |

---

## Requirements

### Functional Requirements

**FR-1: Criteria Definition at Spawn**

When creating agent via `ctm spawn`, auto-generate acceptance criteria from task description.

**FR-2: Criteria Storage**

Store criteria in `agent.task.acceptance_criteria` as structured JSON with auto-verify commands.

**FR-3: Interactive Verification on Complete**

When user runs `ctm complete`, trigger verification flow with status display and blocker identification.

**FR-4: Manual Verification UI**

For criteria without auto-verify, prompt user for manual confirmation.

**FR-5: Verification Commands**

`ctm verify <agent-id>` - Run verification without completing.

**FR-6: Criteria Management**

Commands to add, edit, mark done, and list criteria.

**FR-7: Template-Based Criteria**

Support criteria templates for common task types (feature, integration, migration).

### Non-Functional Requirements

**NFR-1: Performance**
- Verification checks run in parallel where possible
- Timeout for individual checks: 10 seconds
- Total verification time: <30 seconds for 10 criteria

**NFR-2: Backward Compatibility**
- Agents without acceptance_criteria complete normally (no verification)
- Verification is opt-in via config flag: `verification.enabled: true`

**NFR-3: Extensibility**
- Support custom verification plugins (Python functions)
- Allow project-specific verification scripts

**NFR-4: Audit Trail**
- Log all verification attempts to `agent.metadata.verification_history`

### Out of Scope

- **CI/CD Integration** - Won't trigger external pipelines (Phase 2)
- **Notification system** - No alerts when criteria are met (Phase 2)
- **Rollback on failed verification** - Won't auto-reopen completed tasks (Phase 3)
- **AI-powered criterion generation** - Uses heuristics, not LLM (Phase 3)

---

## Technical Design

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ctm complete <id>                        │
└────────────────┬────────────────────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────────────────────┐
│              Verification Engine                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 1. Load agent.task.acceptance_criteria               │   │
│  │ 2. For each criterion:                               │   │
│  │    - If auto_verify: run check_command              │   │
│  │    - If manual: prompt user                          │   │
│  │ 3. Aggregate results                                 │   │
│  │ 4. Display verification report                       │   │
│  │ 5. If all pass: allow completion                     │   │
│  │ 6. If any fail: show blockers, require confirmation  │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────────────────────┐
│          Update agent.state.status = "completed"            │
│          Log to agent.metadata.verification_history         │
└─────────────────────────────────────────────────────────────┘
```

### Data Model

**Agent Schema Extension:**

```json
{
  "task": {
    "acceptance_criteria": [
      {
        "id": "ac-1",
        "criterion": "OAuth2 provider configured (GitHub)",
        "status": "pending",
        "auto_verify": true,
        "check_command": "grep -q 'GITHUB_CLIENT_ID' .env",
        "expected_output": null,
        "expected_pattern": null,
        "manual_check": null,
        "evidence": null,
        "verified_at": null,
        "verified_by": null
      }
    ]
  },
  "metadata": {
    "verification_history": [
      {
        "timestamp": "2026-02-03T10:15:00Z",
        "trigger": "ctm complete",
        "results": [
          {"criterion_id": "ac-1", "status": "done", "duration_ms": 120}
        ],
        "overall_status": "passed",
        "force_completed": false
      }
    ]
  }
}
```

### API/Interface Changes

**New Module:** `~/.claude/ctm/lib/verification.py`

```python
def verify_agent(agent_id: str, auto_only: bool = False) -> VerificationResult
def run_criterion_check(criterion: AcceptanceCriterion, agent: Agent) -> CriterionResult
def generate_criteria_from_task(task_title: str, task_goal: str) -> List[AcceptanceCriterion]
def prompt_manual_verification(criterion: AcceptanceCriterion) -> bool
```

**Modified Module:** `~/.claude/ctm/lib/ctm.py`

Update `cmd_complete()` to call verification engine before completion.

**Modified Module:** `~/.claude/ctm/lib/agents.py`

Update `create_agent()` to accept and auto-generate acceptance criteria.

### Dependencies

- `subprocess` - Run verification commands
- `re` - Pattern matching for expected output
- CTM modules: `agents.py`, `config.py`, `style.py`

---

## Implementation Plan

### Phase 1 (MVP) - Estimated: 8 hours

**Goal:** Basic verification with manual criteria

**Deliverables:**
- [ ] `verification.py` module with core functions
- [ ] Acceptance criteria storage in agent schema
- [ ] `ctm verify <id>` command
- [ ] Modified `ctm complete` with verification check
- [ ] CLI output for verification results
- [ ] Basic command execution (no pattern matching yet)

### Phase 2 (Enhancement) - Estimated: 6 hours

**Goal:** Auto-generation and templates

**Deliverables:**
- [ ] Criteria auto-generation from task description
- [ ] Template system for common task types
- [ ] Pattern matching for expected output (regex)
- [ ] Criteria management commands
- [ ] Config option to enable/disable verification
- [ ] Parallel execution of checks

### Phase 3 (Future Considerations)

- AI-powered criterion generation using LLM
- CI/CD integration
- Notification system
- Auto-rollback on failed verification

---

## Verification Criteria

### Unit Tests

**`test_verification.py`:**
- `test_verify_agent_all_pass()` - All criteria pass
- `test_verify_agent_some_fail()` - Mixed pass/fail
- `test_verify_agent_no_criteria()` - Backward compat
- `test_run_criterion_check_command()` - Execute shell command
- `test_run_criterion_check_timeout()` - Command timeout

### Integration Tests

**Scenario 1: Feature Implementation**
1. Spawn task with auto-generated criteria
2. Complete task with all passing
3. Verify agent marked complete

**Scenario 2: Partial Completion**
1. Spawn task with 3 criteria
2. Mark 2 done manually
3. Complete with force confirm
4. Verify history logged

### UAT Scenarios

**UAT-1: First-Time User**
- User spawns task without knowing about verification
- System suggests criteria
- User accepts and completes task

**UAT-2: Power User**
- User spawns task with custom criteria template
- Runs `ctm verify` periodically
- Completes when all pass

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Commands fail due to environment | High | Medium | Timeout + graceful error handling |
| User ignores verification results | Medium | High | Make force-complete explicit (loud warning) |
| Criteria too strict (blocks progress) | Medium | Medium | Easy criterion editing + skip option |
| Performance degradation | Low | Medium | Parallel execution + 10s timeout |
| Backward compatibility breaks | High | Low | Verification opt-in via config flag |

---

## Timeline Estimate

| Phase | Effort | Duration |
|-------|--------|----------|
| Phase 1 (MVP) | 8 hours | 1-2 days |
| Phase 2 (Enhancement) | 6 hours | 1 day |
| Testing & Polish | 4 hours | 0.5 day |
| **Total** | **18 hours** | **2-3 days** |

**Priority:** High impact, Medium effort
**Recommendation:** Implement Phase 1 immediately, Phase 2 within 2 weeks

---

*PRD Version: 1.0*
*Created: 2026-02-03*
*Author: Claude (Worker Agent)*
