---
name: project-completeness-audit
description: End-of-project or end-of-phase exhaustive requirement-to-deliverable tracing with coverage matrix and gap report.
async:
  mode: never
  require_sync:
    - gap review
    - handover checklist approval
---

# /completeness-audit - Project Completeness Audit

Go-live readiness verification that traces every requirement to a concrete deliverable. Produces a coverage matrix showing what's delivered, what's partial, and what's missing. Found in 4+ Rescue late sessions and 2+ ISMS sessions as a critical quality gate.

## Trigger

Invoke this skill when:
- User says `/completeness-audit`, "are we done?", "go-live ready?", "what's missing?"
- End-of-phase milestone review
- Before handover documentation preparation
- Client asks for delivery confirmation
- "Making sure nothing fell through the cracks"

## Why This Exists

Projects accumulate dozens of requirements across discovery, SOW, and ongoing conversations. At go-live, manually verifying nothing was missed is error-prone and time-consuming. A systematic trace from requirement to deliverable catches gaps that manual review misses.

## Commands

| Command | Action |
|---------|--------|
| `/completeness-audit` | Full 6-step audit |
| `/completeness-audit --quick` | Requirements count + coverage % only |
| `/completeness-audit --gaps` | Show gaps only (skip fully-delivered items) |
| `/completeness-audit --handover` | Generate handover checklist from audit |

## Workflow

### Step 1: Extract Requirements
Parse SOW, discovery docs, and FSD for all requirements:
- Functional (features, workflows, automations)
- Technical (integrations, APIs, custom code)
- Data (migration, quality, field mapping)
- Training (admin guides, user training, documentation)

### Step 2: Trace to Deliverables
For each requirement, identify deliverable(s) that address it:
- `DELIVERED` — Fully met by identified deliverable
- `PARTIAL` — Partially met (detail what's missing)
- `MISSING` — Not addressed (no matching deliverable found)
- `OUT-OF-SCOPE` — Explicitly excluded in SOW

### Step 3: Generate Coverage Matrix
Visual table: requirement, source document, matched deliverable, status, notes.

### Step 4: Sweep Open Items
Cross-reference for unresolved items:
- DECISIONS.md PENDING items
- CTM open/incomplete tasks
- Conversation files with [OPEN] or [MISSING] markers

### Step 5: Validate Configurations
Spot-check technical requirements:
- Property counts match spec
- Workflow states correct
- Integration endpoints configured
- Data migration counts reconciled

### Step 6: Produce Report
Completeness report: overall score, coverage matrix, gaps by severity, open items, handover checklist.

## Output Format

```
Completeness Audit Results:
  Requirements traced: [N] total
    Delivered: [M] (X%)
    Partial: [K] (Y%)
    Missing: [J] (Z%)
    Out-of-scope: [L]
  Open items: [O] from DECISIONS.md, [P] from CTM
  Overall score: [S]%
  Report saved to: [path]
```

## Integration

- **`completeness-auditor` agent**: Detailed analysis engine
- **`handover-packager`**: Packages deliverables after audit passes
- **`deliverable-reviewer`**: Per-document quality (this skill = project-wide)
- **DECISIONS.md**: Source of pending items
