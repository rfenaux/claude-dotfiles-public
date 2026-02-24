---
name: scope-defense-bundle
description: Generate commercial scope defense evidence - SOW delta matrix, effort quantification, and defense communication package.
async:
  mode: never
  require_sync:
    - scope analysis review
    - communication drafting
    - user approval before sending
---

# /scope-defense - Scope Defense Bundle

Commercial protection workflow for when scope creep threatens project margins. Packages evidence of what was promised vs. delivered, quantifies out-of-scope effort, and drafts defense communications. Found in 5+ Rescue sessions and 3+ ISMS sessions as a critical recurring need.

## Trigger

Invoke this skill when:
- User says `/scope-defense`, "scope creep", "SOW said X", "defend scope"
- End-of-project commercial review
- Client requests work not in SOW
- Change request evaluation needs evidence
- Before commercial conversations about budget or timeline extensions

## Why This Exists

Scope creep is the #1 commercial risk in CRM implementations. Teams deliver out-of-scope work without documenting it, then can't justify additional budget or timeline extensions. By the time the commercial conversation happens, evidence is scattered across months of conversations. This skill creates the evidence trail needed for professional scope defense.

## Commands

| Command | Action |
|---------|--------|
| `/scope-defense` | Full 7-step evidence bundle |
| `/scope-defense --quick` | Delta matrix only (skip communication draft) |
| `/scope-defense --delta` | Generate delta matrix from SOW comparison |
| `/scope-defense --draft` | Draft defense communication from existing delta |

## Workflow

### Step 1: Read SOW Scope
Parse SOW/contract documents for: contracted deliverables, explicit exclusions, assumptions, effort estimates, change management clauses.

### Step 2: Inventory Deliverables
Scan project for all actual deliverables produced: documents, configurations, code, presentations, training materials.

### Step 3: Generate Delta Matrix
Map each item with status:
- `IN-SCOPE` — Delivered as contracted
- `PARTIAL` — Partially delivered (detail what's remaining)
- `MISSING` — Not yet delivered (detail why: blocker, deferred, etc.)
- `ADDITION` — Delivered but NOT in original SOW

### Step 4: Identify Out-of-Scope Additions
For each ADDITION: what it is, when requested, who requested it, why it was done (client request, technical necessity, dependency).

### Step 5: Calculate Effort
Quantify effort invested in out-of-scope work: estimated hours, complexity level, opportunity cost (what contracted work was delayed).

### Step 6: Draft Communication
Generate scope defense document: factual tone, evidence-based, professional. Includes delta matrix summary, effort impact, and options for path forward.

### Step 7: Package Bundle
Create evidence bundle for delivery:
- Delta matrix (full table)
- Effort breakdown (hours by category)
- Timeline of scope additions (when each was added)
- Draft communication (email or document)

## Output Format

```
Scope Defense Bundle Generated:
  SOW items: [N] contracted
    Delivered: [M] (X%)
    Partial: [K] (Y%)
    Missing: [J] (Z%)
  Out-of-scope additions: [L] items
    Estimated effort: [H] hours
    % of total effort: [P]%
  Bundle saved to: [path]
  Draft communication: [path]
```

## Integration

- **`scope-delta-analyzer` agent**: Detailed analysis engine
- **DECISIONS.md**: Records scope decisions (S-category)
- **CTM**: Updates task context with scope status
- **`/deviate scope`**: Links to deviation handler for active scope creep
- **Executive persona**: Defense communications adapted for management audience
