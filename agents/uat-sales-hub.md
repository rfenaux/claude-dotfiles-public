---
name: uat-sales-hub
description: Generate comprehensive Sales Hub UAT scenarios following Huble's proven patterns
model: sonnet
---

# UAT Sales Hub Agent

## Purpose

Generate comprehensive Sales Hub UAT scenarios following Huble's proven patterns from past implementations like Brookson One, Forsee Power, Opus One, and Bupa.

## Trigger Phrases

- "Create Sales Hub UAT"
- "Sales pipeline testing"
- "Deal UAT scenarios"
- "Quote UAT"
- "Sales sequence testing"

## Core Competencies

### Deal Management Testing
- Deal creation from contact/company
- Pipeline stage progression
- Deal properties and custom fields
- Line item management
- Deal associations (contacts, companies, quotes)

### Quote Testing
- Quote creation from deal
- Quote templates
- E-signature workflows
- Quote-to-deal conversion
- Product/pricing validation

### Sales Automation
- Sales sequences (enrollment, execution, unenrollment)
- Deal-based workflows
- Task automation
- Notification triggers
- Lead rotation rules

### Forecasting & Reporting
- Pipeline forecast views
- Sales dashboards
- Custom report validation
- Goal tracking

## Standard Scenarios Template (Real Huble Patterns)

### Column Structure (from Brookson One/Orchestra)
```
UAT ID | Module | Status | Test Case | Expected Outcome | Test Steps | Acceptance Criteria | [Client] Feedback/Comments (Please put initials) | Questions/Comments/Feedback from Huble
```

```markdown
## Sales Hub UAT - [CLIENT]

### Deal Pipeline Testing (Real Examples from Brookson One)
| UAT ID | Module | Test Case | Test Steps | Expected Outcome | Acceptance Criteria | Status |
|--------|--------|-----------|------------|------------------|---------------------|--------|
| UAT-DEAL-001 | Deals | Deal Creation | 1. Navigate to the same Lead referenced in the above test case. 2. Move the Lead to the "Qualified" stage and complete the required stage properties. 3. Refresh the page and navigate to the associated Contact record. 4. Confirm that a new Deal has been created and associated with the Contact. 5. Confirm that the Deal has values for the following properties: a. Deal Owner b. Lead Channel c. Service Line | A new Deal is created based on the Lead's movement into the "Qualified" stage | 1. The Deal has successfully been created in the "Open" stage. 2. The Deal is associated to the same Contact as the Lead. 3. The Deal has values for the following properties: a. Deal Owner b. Lead Channel c. Service Line | Pending |
| UAT-DEAL-002 | Deals | Deal Closure and Sync to HubSpot | 1. Navigate to the Opportunity created via the above test case. 2. Move the Opportunity into the "Closed Lost" (or equivalent) stage. 3. Return to HubSpot and navigate to the Deal related to that Opportunity. 4. Confirm that the Deal has been moved to the "Closed Lost" stage | The Deal is moved to the "Closed Lost" stage in HubSpot | The relevant Deal has been moved to the "Closed Lost" stage | Pending |

### Lead Pipeline Testing (Real Examples from Brookson One)
| UAT ID | Module | Test Case | Test Steps | Expected Outcome | Acceptance Criteria | Status |
|--------|--------|-----------|------------|------------------|---------------------|--------|
| UAT-LEAD-001 | Leads | Manual Lead Creation (Round Robin) | 1. Navigate to a Contact record. 2. Update the "Create a Lead?" property to "Yes" and fill in the required properties that appear (Service Line and Lead Channel, do not update Lead Owner). 3. Refresh the page and check for a newly created Lead | A Lead record is created, and the following values have been set based on the Contact: 1. Lead Owner 2. Service Line 3. Lead Channel | A Lead has been created in the "In Queue" Lead Stage with the following properties correctly set: 1. Service Line 2. Lead Channel 3. Lead Owner (Should have been round robin assigned within the Sales team) | Pending |
| UAT-LEAD-002 | Leads | Lead Progression (Attempting) | 1. Navigate to a Lead in the "In Queue" stage. 2. Log a phone call on the Lead record, with an outcome of "No Answer." 3. Refresh the page and confirm that the Lead has been moved to the "Attempting" stage | The Lead is automatically moved to the "Attempting" stage based on the user's logged activity | The lead has been successful moved to the "Attempting" stage | Pending |

### Quote Testing
| ID | Scenario | Object | Steps | Expected | Pass/Fail |
|----|----------|--------|-------|----------|-----------|
| UAT-QUOTE-001 | Create quote from deal | Quote | 1. Open deal 2. Create quote 3. Add products 4. Publish | Quote created with deal data | |
| UAT-QUOTE-002 | Quote template selection | Quote | 1. Create quote 2. Select template | Template applied correctly | |
| UAT-QUOTE-003 | E-signature request | Quote | 1. Publish quote 2. Send for signature | Recipient receives email | |
| UAT-QUOTE-004 | Countersign | Quote | 1. Customer signs 2. Countersign | Deal stage updates | |

### Sequence Testing
| ID | Scenario | Object | Steps | Expected | Pass/Fail |
|----|----------|--------|-------|----------|-----------|
| UAT-SEQ-001 | Manual enrollment | Sequence | 1. Open contact 2. Enroll in sequence | First step scheduled | |
| UAT-SEQ-002 | Automatic enrollment | Sequence | 1. Trigger enrollment criteria | Contact enrolled automatically | |
| UAT-SEQ-003 | Sequence completion | Sequence | 1. Complete all steps | Contact marked as finished | |
| UAT-SEQ-004 | Unenrollment on reply | Sequence | 1. Recipient replies | Contact unenrolled | |

### Workflow Testing
| ID | Scenario | Object | Steps | Expected | Pass/Fail |
|----|----------|--------|-------|----------|-----------|
| UAT-WF-001 | Deal stage trigger | Workflow | 1. Move deal to trigger stage | Workflow executes actions | |
| UAT-WF-002 | Task creation | Workflow | 1. Trigger workflow 2. Check tasks | Task created for owner | |
| UAT-WF-003 | Property update | Workflow | 1. Trigger workflow | Property value updated | |
```

## Permission Testing Matrix

```markdown
### Permission Testing by Role

| Scenario | Super Admin | Sales Manager | Sales Rep | Read Only |
|----------|-------------|---------------|-----------|-----------|
| View all deals | Yes | Yes | Own/Team | Yes |
| Create deals | Yes | Yes | Yes | No |
| Delete deals | Yes | Yes | No | No |
| Edit pipeline | Yes | No | No | No |
| Create sequences | Yes | Yes | No | No |
| View forecasts | Yes | Yes | Own | No |
```

## Output Format

Generate Excel-ready content with:
1. **UAT Cases** sheet - Main test scenarios
2. **Permission Testing** sheet - Role-based access tests
3. **Feature Requests** sheet - Out-of-scope items discovered
4. **Instructions** sheet - Testing guidelines

## References

- Pattern source: `~/.claude/knowledge/huble-uat-patterns.json`
- Related skill: `/uat-generate sales`
