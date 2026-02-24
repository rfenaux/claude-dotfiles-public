# PRD: CTM-003 - VERIFICATION.md Auto-Generation

> Automatically generate verification checklists from task plans to ensure thorough completion validation

## Overview

### Problem Statement

Current CTM workflow requires manual creation of verification criteria:
- Users must manually think through what "done" means
- Verification steps are often forgotten or incomplete
- No standard template for verification across task types
- Test scenarios, rollback procedures scattered across files

This leads to:
- Inconsistent verification rigor across tasks
- Missing edge cases in testing
- No rollback plan when things break
- Tedious manual creation of verification docs

**Current state:**
User must manually create verification checklist in agent workspace or project docs.

**Desired state:**
System auto-generates comprehensive `VERIFICATION.md` from task description, plan files, and task type.

### Proposed Solution

Implement **VERIFICATION.md auto-generation**: analyze task description, extract verification requirements, generate structured verification document.

**New behavior:**
```bash
$ ctm spawn "Implement OAuth2 login" --template feature

Task: Implement OAuth2 login
Goal: Add OAuth2 login to the app

Generating VERIFICATION.md...
  ✓ Extracted 4 test scenarios
  ✓ Identified 3 edge cases
  ✓ Generated rollback procedure
  ✓ Created acceptance checklist

VERIFICATION.md created at:
  ~/.claude/ctm/agents/auth2026/VERIFICATION.md

Preview:
  # Verification Plan: OAuth2 Login

  ## Acceptance Criteria
  - [ ] OAuth2 provider configured (GitHub)
  - [ ] Login route responds with 302 redirect
  - [ ] Token validation passes tests
  - [ ] Documentation updated

  ## Test Scenarios
  ### Happy Path
  1. User clicks "Login with GitHub"
  2. Redirects to GitHub OAuth consent
  3. Returns with valid token
  4. User authenticated in app

  ### Edge Cases
  1. OAuth consent denied → show error
  2. Invalid token → reject authentication
  3. Expired token → refresh flow

  ## Rollback Procedure
  1. Revert OAuth config changes
  2. Restore previous auth method
  3. Clear OAuth-related DB entries
  4. Verify existing users unaffected
```

### Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Auto-generation adoption | >70% of spawned tasks | Check if VERIFICATION.md exists |
| Verification coverage | >80% of critical paths | Manual audit sample |
| Rollback success rate | >95% when invoked | Track rollback executions |
| User satisfaction | "Saves time, catches issues" | Qualitative feedback |

---

## Requirements

### Functional Requirements

**FR-1: Auto-Generation Triggers**

Generate `VERIFICATION.md` when:
- `ctm spawn <task> --template <type>` (with template)
- `ctm spawn <task> --verify` (explicit flag)
- `ctm verify generate <agent-id>` (manual generation)

**FR-2: Verification Document Structure**

Standard structure for all generated `VERIFICATION.md`:

```markdown
# Verification Plan: {Task Title}

> Auto-generated: {timestamp}
> Agent: {agent-id}
> Template: {template-type}

## Overview
- **Goal**: {task goal}
- **Acceptance Criteria**: {count} items
- **Test Scenarios**: {count} scenarios
- **Edge Cases**: {count} cases

## Acceptance Criteria
- [ ] {criterion 1}
- [ ] {criterion 2}
...

## Test Scenarios

### Happy Path
1. {step 1}
2. {step 2}
...

### Alternative Paths
1. {scenario 1}
2. {scenario 2}

### Edge Cases
1. {edge case 1}
2. {edge case 2}

## Integration Points
- {system 1} → {interaction}
- {system 2} → {interaction}

## Rollback Procedure
1. {step 1}
2. {step 2}
...

## Verification Commands
```bash
# Automated checks
{check command 1}
{check command 2}
```

## Manual Verification
- [ ] {manual check 1}
- [ ] {manual check 2}

## Success Indicators
- {metric 1}: {target value}
- {metric 2}: {target value}
```

**FR-3: Template-Based Generation**

Different templates produce different verification content:

| Template | Focus Areas |
|----------|-------------|
| `feature` | User workflows, UI tests, edge cases |
| `integration` | API contracts, error handling, retry logic |
| `migration` | Data integrity, rollback, dual-write validation |
| `bugfix` | Regression tests, root cause validation |
| `performance` | Load tests, benchmarks, monitoring |

**FR-4: Intelligent Content Extraction**

Extract verification requirements from:

1. **Task description**: Keywords like "must", "should", "critical"
2. **Template plan files**: Existing `PLAN.md` or `SPEC.md` in agent workspace
3. **Project context**: Integration points from `03-solution-design/`
4. **Past learnings**: Common failure patterns from completed agents

**FR-5: Verification Command Generation**

Auto-generate executable verification commands:

```markdown
## Verification Commands
```bash
# Check OAuth config exists
grep -q 'GITHUB_CLIENT_ID' .env || echo "MISSING"

# Test login endpoint
curl -s http://localhost:3000/auth/login | grep -q '302'

# Run auth tests
npm test -- auth.test.ts

# Verify deployment
kubectl get pods -n auth | grep -q 'Running'
```
```

**FR-6: Rollback Procedure Generation**

Generate rollback steps based on task type:

- **Code changes**: `git revert <commit>`
- **Database migrations**: Rollback SQL script
- **Config changes**: Restore previous config
- **Deployments**: Rollback to previous version

**FR-7: Verification Management Commands**

```bash
# Generate VERIFICATION.md
$ ctm verify generate auth2026

# Regenerate (update existing)
$ ctm verify regenerate auth2026

# Show verification status
$ ctm verify status auth2026

# Mark verification item complete
$ ctm verify check auth2026 "OAuth config exists"
```

### Non-Functional Requirements

**NFR-1: Performance**

- Generation time: <5 seconds for typical task
- No external API calls (rule-based, not LLM)

**NFR-2: Backward Compatibility**

- Agents without VERIFICATION.md continue to work
- Manual verification files not overwritten

**NFR-3: Customization**

- Allow project-specific verification templates
- Support custom verification sections

**NFR-4: Maintainability**

- Template-driven content (easy to update)
- Clear separation: generation logic vs. templates

### Out of Scope

- **AI-powered content generation** - Uses heuristics, not LLM (Phase 2)
- **Automated test execution** - Generates commands, doesn't run them (Phase 2)
- **Verification result tracking** - No execution history (Phase 2)
- **Integration with CI/CD** - Local verification only (Phase 3)

---

## Technical Design

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              ctm spawn <task> --template <type>             │
└────────────────┬────────────────────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────────────────────┐
│            VERIFICATION.md Generator                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 1. Load template verification rules                  │   │
│  │ 2. Parse task description for verification keywords  │   │
│  │ 3. Load PLAN.md if exists in workspace              │   │
│  │ 4. Extract:                                          │   │
│  │    - Acceptance criteria                             │   │
│  │    - Test scenarios (happy + edge)                   │   │
│  │    - Integration points                              │   │
│  │    - Rollback steps                                  │   │
│  │ 5. Generate verification commands                    │   │
│  │ 6. Render VERIFICATION.md from template             │   │
│  │ 7. Write to agent workspace                          │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────────────────────┐
│   ~/.claude/ctm/agents/{agent-id}/VERIFICATION.md          │
└─────────────────────────────────────────────────────────────┘
```

### Data Model

**Verification Template Schema:**

```yaml
# ~/.claude/ctm/templates/verification/feature.yaml
name: Feature Verification Template
description: Verification plan for feature implementations

sections:
  acceptance_criteria:
    enabled: true
    source: task.acceptance_criteria
    format: checklist

  test_scenarios:
    enabled: true
    include:
      - happy_path
      - alternative_paths
      - edge_cases
    heuristics:
      - keyword: "user can"
        scenario: happy_path
      - keyword: "error|fail|invalid"
        scenario: edge_cases

  integration_points:
    enabled: true
    extract_from: project.solution_design

  rollback:
    enabled: true
    steps:
      - "Revert code changes: git revert {commit}"
      - "Restore DB: Run rollback migration"
      - "Clear cache: redis-cli FLUSHDB"

  verification_commands:
    enabled: true
    include:
      - type: test
        command: "npm test"
      - type: lint
        command: "npm run lint"
      - type: endpoint_check
        command: "curl -s {endpoint}"
```

**Generated Document Metadata:**

Stored in `agent.metadata.verification`:

```json
{
  "verification": {
    "generated_at": "2026-02-03T10:15:00Z",
    "template": "feature",
    "file_path": "~/.claude/ctm/agents/auth2026/VERIFICATION.md",
    "criteria_count": 4,
    "scenario_count": 6,
    "command_count": 3,
    "last_regenerated": null,
    "completion_status": {
      "acceptance_criteria": "2/4",
      "test_scenarios": "4/6",
      "rollback_tested": false
    }
  }
}
```

### API/Interface Changes

**New Module:** `~/.claude/ctm/lib/verification_gen.py`

```python
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class VerificationContent:
    acceptance_criteria: List[str]
    test_scenarios: Dict[str, List[str]]
    edge_cases: List[str]
    integration_points: List[str]
    rollback_steps: List[str]
    verification_commands: List[str]
    manual_checks: List[str]

def generate_verification_md(agent: Agent, template: str) -> str:
    """Generate VERIFICATION.md content from agent + template"""
    pass

def extract_criteria_from_task(task_description: str) -> List[str]:
    """Extract acceptance criteria using heuristics"""
    pass

def extract_test_scenarios(task: Dict, template_rules: Dict) -> Dict[str, List[str]]:
    """Generate test scenarios from task description"""
    pass

def generate_rollback_procedure(agent: Agent, template: str) -> List[str]:
    """Generate rollback steps based on task type"""
    pass

def render_verification_template(content: VerificationContent, template: str) -> str:
    """Render final VERIFICATION.md from content + template"""
    pass
```

**Modified Module:** `~/.claude/ctm/lib/agents.py`

```python
def create_agent(..., generate_verification: bool = True):
    """Create agent and optionally generate VERIFICATION.md"""

    agent = Agent.create(...)

    if generate_verification and template:
        verification_md = generate_verification_md(agent, template)
        write_verification_file(agent.id, verification_md)
        agent.metadata["verification"] = {
            "generated_at": now(),
            "template": template,
            "file_path": verification_path(agent.id)
        }

    return agent
```

### Dependencies

**Python Standard Library:**
- `re` - Keyword extraction
- `jinja2` - Template rendering (optional)

**CTM Modules:**
- `agents.py` - Agent data
- `templates.py` - Template loading
- `config.py` - Verification settings

---

## Implementation Plan

### Phase 1 (MVP) - Estimated: 8 hours

**Goal:** Basic auto-generation with template support

**Deliverables:**
- [ ] `verification_gen.py` module
- [ ] Verification template system (YAML)
- [ ] Feature template with standard sections
- [ ] Acceptance criteria extraction (rule-based)
- [ ] Rollback procedure generation
- [ ] `ctm verify generate` command
- [ ] Integration with `ctm spawn --template`

**Testing:**
- Generate VERIFICATION.md for "feature" template
- Verify all sections present
- Check acceptance criteria extracted
- Validate rollback steps included

### Phase 2 (Enhancement) - Estimated: 6 hours

**Goal:** Advanced extraction and customization

**Deliverables:**
- [ ] Test scenario generation (happy + edge)
- [ ] Integration point extraction from project files
- [ ] Verification command auto-generation
- [ ] Project-specific template overrides
- [ ] Regeneration with merge (preserve manual edits)
- [ ] Verification status tracking

**Testing:**
- Generate for integration template
- Verify integration points extracted from project
- Test regeneration preserves manual changes

### Phase 3 (Future Considerations)

- AI-powered content generation (use LLM for scenarios)
- Execute verification commands and track results
- CI/CD integration (verify on commit)
- Verification coverage reports

---

## Verification Criteria

### Unit Tests

**`test_verification_gen.py`:**
- `test_extract_criteria_from_task()` - Keyword extraction
- `test_generate_rollback_procedure()` - Rollback steps
- `test_render_verification_template()` - Template rendering
- `test_extract_test_scenarios()` - Scenario generation
- `test_generate_verification_commands()` - Command generation

### Integration Tests

**Scenario 1: Feature Template**
1. Spawn task with feature template
2. Verify VERIFICATION.md generated
3. Check all sections present
4. Validate acceptance criteria extracted

**Scenario 2: Integration Template**
1. Create project with integration points defined
2. Spawn integration task
3. Verify integration points extracted
4. Check API contract verification included

**Scenario 3: Regeneration**
1. Generate VERIFICATION.md
2. User adds manual section
3. Regenerate
4. Verify manual section preserved

### UAT Scenarios

**UAT-1: First-Time User**
- User spawns feature task with template
- System generates VERIFICATION.md
- User reviews generated content
- User uses checklist for completion

**UAT-2: Power User**
- User creates custom verification template
- Spawns task with custom template
- Verifies custom sections included
- Regenerates after template update

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Generated content too generic | Medium | High | Template customization, project-specific overrides |
| Manual edits lost on regeneration | High | Medium | Merge logic, preserve user sections |
| Missing edge cases | Medium | Medium | Learn from completed tasks, expand heuristics |
| Rollback steps incorrect | High | Low | Conservative defaults, user review required |
| Template maintenance burden | Low | Medium | Small set of core templates, community contributions |

---

## Timeline Estimate

| Phase | Effort | Duration |
|-------|--------|----------|
| Phase 1 (MVP) | 8 hours | 1-2 days |
| Phase 2 (Enhancement) | 6 hours | 1 day |
| Testing & Polish | 4 hours | 0.5 day |
| **Total** | **18 hours** | **2-3 days** |

**Priority:** Medium impact, Medium effort
**Recommendation:** Implement Phase 1 within 1 month, Phase 2 based on user feedback

---

*PRD Version: 1.0*
*Created: 2026-02-03*
*Author: Claude (Worker Agent)*
