# Deliverable Templates

Standard formats for project discovery outputs.

---

## 1. Technical Analysis Structure

```markdown
# [Project Name]: Technical Analysis
## Senior Solutions Architect Review

**Author:** [Name], Senior Solutions Architect
**Date:** [Date]
**Document Type:** Technical Due Diligence
**Status:** INTERNAL — Pre-Contract Validation

---

## Executive Summary

| Assessment Area | Sales Estimate | SolA Assessment | Gap |
|-----------------|----------------|-----------------|-----|
| [Area 1] | [Estimate] | [Assessment] | [Gap indicator] |
| [Area 2] | [Estimate] | [Assessment] | [Gap indicator] |

**Bottom Line:** [One paragraph summary of findings and recommendation]

---

## Module-by-Module Analysis

### [Module Name]

**Stats:** [X] records | [Y] properties | [Z] MB

#### Sales Assessment
> "[What sales/client said]"

#### SolA Technical Review

| Property | Type | Technical Implication |
|----------|------|----------------------|
| [Property 1] | [Type] | [Implication] |
| [Property 2] | [Type] | [Implication] |

**Technical Verdict:** [Your independent assessment]

**Risk Level:** [🔴 Critical / 🟡 Medium / 🟢 Low]

**Effort Adjustment:** [+/- Xh if different from estimate]

---

## Gap Analysis: Sales vs. Technical Reality

### 🔴 Critical Gaps

| Item | Sales Said | Reality | Action Required |
|------|------------|---------|-----------------|
| [Item] | [Assumption] | [Finding] | [Action] |

### 🟡 Medium Gaps

| Item | Sales Said | Reality | Action Required |
|------|------------|---------|-----------------|
| [Item] | [Assumption] | [Finding] | [Action] |

### ✅ Aligned Items

| Item | Sales Said | Reality |
|------|------------|---------|
| [Item] | [Assumption] | Correct |

---

## Dependency Map

```
PHASE 1: [Foundation]
├── [Object 1]
└── [Object 2]

PHASE 2: [Core]
├── [Object 3] — requires [Object 1]
└── [Object 4]

NOT IN SCOPE
├── [Excluded item]
└── [Excluded item]
```

---

## Revised Effort Estimate

| Component | Sales Hours | Adjusted Hours | Reason |
|-----------|-------------|----------------|--------|
| [Component] | [X]h | [Y]h | [Reason] |

### Budget Range

| Scenario | Hours | Estimated € |
|----------|-------|-------------|
| Best Case | [X]h | €[Y] |
| Probable | [X]h | €[Y] |
| Worst Case | [X]h | €[Y] |

---

## SOW Recommendations

### Explicit In-Scope

```
- [Item 1]
- [Item 2]
```

### Explicit Out-of-Scope

```
- [Item 1] — available as Phase 2 add-on
- [Item 2] — recommend archive approach
```

### Change Control Language

```
Any scope additions identified during implementation will be:
1. Documented with effort estimate
2. Submitted for client approval
3. Priced at standard rates
```

---

## Required Actions Before Contract

| # | Action | Owner | Deadline | Impact if Skipped |
|---|--------|-------|----------|-------------------|
| 1 | [Action] | [Owner] | [Date] | [Impact] |
```

---

## 2. Executive Brief Format

```markdown
# [Project Name]: What You Need to Know Before Signing
## A Plain-English Brief from [Author]

**[Recipient],**

[Opening paragraph — context and purpose]

---

## The Short Version

**Can we do this project?** [Yes/No/Maybe]

**At the current price ([€X])?** [Assessment]

**What's the risk?** [One paragraph on main risk]

**What should you do?** [Clear action]

---

## What We're Really Selling

[Reframe the project in terms of actual value/outcome, not technical deliverables]

---

## The [X] Things That Could Blow Up the Budget

### 1. [Risk Name]

**What you were told:** "[Assumption]"

**What I found:** [Reality]

**Why it matters:** [Business impact]

**What to do:** [Specific action]

[Repeat for each major risk]

---

## The [X] Questions to Ask Before Signing

### Question 1: [Topic]
> "[Exact wording of question to send to client]"

**Why it matters:** [Explanation]

[Repeat for each critical question]

---

## The Money Conversation

| Scenario | What It Assumes | Price Range |
|----------|-----------------|-------------|
| Optimistic | [Assumptions] | €[X] |
| Realistic | [Assumptions] | €[X] |
| Pessimistic | [Assumptions] | €[X] |

**Current quote: €[X] — this is the [optimistic/realistic] scenario.**

---

## My Recommendation

[Clear recommendation with specific actions]

---

**Let me know if you want to discuss.**

— [Author]
```

---

## 3. Risk Register Template

```markdown
# [Project Name]: Risk Register

| # | Risk | Category | Likelihood | Impact | Price Impact | Mitigation | Question to Resolve | Status |
|---|------|----------|------------|--------|--------------|------------|---------------------|--------|
| 1 | [Risk description] | 🔴 Critical | High/Med/Low | High/Med/Low | €[X]-[Y] | [Action] | "[Question]" | Open |
| 2 | [Risk description] | 🟡 Medium | High/Med/Low | High/Med/Low | €[X]-[Y] | [Action] | "[Question]" | Open |
| 3 | [Risk description] | 🟢 Low | High/Med/Low | High/Med/Low | €[X]-[Y] | [Action] | N/A | Noted |

## Risk Categories

- 🔴 **Critical:** Must resolve before contract signature
- 🟡 **Medium:** Should resolve before contract; creates uncertainty if not
- 🟢 **Low:** Note for implementation phase; won't significantly impact pricing

## Resolution Tracking

| # | Risk | Resolution | Date | Resolved By |
|---|------|------------|------|-------------|
| 1 | [Risk] | [How resolved] | [Date] | [Person] |
```

---

## 4. SOW Scope Language Templates

### In-Scope Template

```markdown
## IN SCOPE — Phase 1

### Data Migration
- Migration of [object type] records from [source] (records created/modified in last [X] months)
- Property mapping limited to core set defined in Workshop 1 (~[X] properties per object)
- Association recreation for standard and custom object relationships

### Configuration
- [X] deal pipelines with [Y] stages each
- User setup: [X] users across [roles]
- Permission configuration: [model type] access model

### Integrations
- [Integration 1]: [Brief scope description]
- [Integration 2]: [Brief scope description]

### Training & Documentation
- [Training approach] ([X] sessions)
- Documentation: [deliverables]
```

### Out-of-Scope Template

```markdown
## OUT OF SCOPE — Phase 1

### Data Exclusions
- Historical data migration (records >[X] months old) — available as Phase 2 add-on
- [Module] migration — recommend archive approach
- Migration of unused/legacy properties

### Feature Exclusions
- [Feature 1] — [reason / alternative]
- [Feature 2] — [reason / alternative]

### Integration Exclusions
- [System] integration — [reason]
- Custom API development

### Process Exclusions
- 1:1 replication of [old system] logic
- Data cleaning and deduplication (client responsibility)

### Technical Exclusions
- Custom coded solutions
- [Platform]-specific features beyond standard tier
```

### Change Control Template

```markdown
## CHANGE CONTROL

Any scope additions identified during implementation will be:

1. **Documented** with detailed requirements and effort estimate
2. **Submitted** for client approval in writing
3. **Priced** at standard rates (€[X]/hour for [role])
4. **Scheduled** without impacting Phase 1 timeline unless mutually agreed

Items marked as "TBD" or "to be confirmed" in this document that are subsequently confirmed as IN SCOPE will be treated as change requests and priced accordingly.

Unused contingency hours do not roll over or credit toward future work.

Client acknowledges that:
- Scope changes may impact timeline and budget
- Verbal approvals are not binding; written approval required
- The implementation team reserves the right to adjust resource allocation based on scope changes
```

---

## 5. Pre-Contract Checklist

Use this to confirm readiness before contract signature.

```markdown
## Pre-Contract Validation Checklist

### Must Have (Blockers)

| Item | Status | Notes |
|------|--------|-------|
| [ ] All critical questions answered in writing | | |
| [ ] Budget range validated against probable scenario | | |
| [ ] All "TBD" items resolved to IN or OUT | | |
| [ ] Client stakeholder alignment confirmed | | |
| [ ] Timeline validated (or extension confirmed) | | |

### Should Have (Risk Reduction)

| Item | Status | Notes |
|------|--------|-------|
| [ ] Platform/portal access obtained | | |
| [ ] Sample data reviewed | | |
| [ ] Key dependencies documented | | |
| [ ] Internal champion identified | | |
| [ ] Success metrics defined | | |

### SOW Quality

| Item | Status | Notes |
|------|--------|-------|
| [ ] In-scope items explicit and specific | | |
| [ ] Out-of-scope items listed with reasons | | |
| [ ] Change control language included | | |
| [ ] Phase 2 / future options documented | | |
| [ ] Assumptions documented | | |

### Sign-Off

| Role | Name | Approval | Date |
|------|------|----------|------|
| Solutions Architect | | [ ] Approved | |
| Sales Lead | | [ ] Approved | |
| Delivery Manager (if assigned) | | [ ] Approved | |
```
