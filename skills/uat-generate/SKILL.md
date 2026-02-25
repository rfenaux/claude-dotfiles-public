---
name: uat-generate
description: Generate UAT documents following best practice patterns. Use when creating UAT spreadsheets, test cases, or acceptance criteria for HubSpot implementations.
context: fork
---

# /uat-generate - UAT Document Generator

Creates professional UAT documents following best practice patterns from HubSpot implementations.

## Commands

| Command | Action |
|---------|--------|
| `/uat-generate` | Interactive UAT generation wizard |
| `/uat-generate sales` | Generate Sales Hub UAT template |
| `/uat-generate service` | Generate Service Hub UAT template |
| `/uat-generate marketing` | Generate Marketing Hub UAT template |
| `/uat-generate integration <system>` | Generate integration UAT template |
| `/uat-generate migration` | Generate data migration UAT template |

## UAT Standard Schema

Based on analysis of 45+ UAT documents from HubSpot implementations (189 sheets, 340 unique columns):

### Core Columns (Required)

| Column | Purpose | Format |
|--------|---------|--------|
| Test Case ID | Unique identifier | `UAT-[MODULE]-[###]` |
| Scenario | Test name/title | Short descriptive title |
| Object | HubSpot object | Contact, Company, Deal, etc. |
| Testing Steps | How to execute | Numbered steps |
| Expected Result | Success criteria | Specific outcome |
| Pass/Fail | Execution result | Pass / Fail / Blocked / Not Started |

### Extended Columns (Recommended)

| Column | Purpose |
|--------|---------|
| Tested By | Person who executed test |
| Date Tested | When test was executed |
| HubSpot Record | Link to actual record |
| Screenshot | Visual evidence |
| Findings | Issues discovered |
| Changes Made | Remediation actions |
| Client Response | Client feedback field |

## Sheet Organization Patterns

### By User Role (Permission Testing)
```
- Super Admin
- Sales Manager
- Territory Sales
- Marketing Rep
- Service Rep
```

### By Functional Area
```
- Sales UAT Scenarios
- Service Hub Testing
- Marketing Automation
- Integration Testing
- Migration Validation
```

### Standard Support Sheets
```
- Feature Requests (separate from UAT)
- Development Status
- Client Status
- QA Status
```

## Scenario Writing Guide (From Real UATs)

### Test Case Naming Pattern

**Format: Action + Object + Context (parenthetical)**

Real examples from past implementations:
- "Newsletter Subscription Form Submission"
- "Manual Lead Creation (Round Robin)"
- "Deal Progression through Pipeline"
- "Contact creation - Existing in HubSpot" (integration)
- "Upsell Deal Creation (Same Agency)"

### Test Steps Format

**Pattern A: Numbered steps with line breaks**
```
1. Navigate to a Contact record
2. Update the "Create a Lead?" property to "Yes" and fill in the required properties (Service Line and Lead Channel)
3. Refresh the page and check for a newly created Lead
```

**Pattern B: Numbered steps with lettered sub-items**
```
1. Create deal in HubSpot
2. Add the items for the private class
   a. Choose the line items in the Private Class view
3. Update the details in each line item, including:
   a. Start/End Dates
   b. Facilitator
   c. Quantity
```

**Key rules:**
- Always use numbered steps (1. 2. 3.)
- Include specific property names in quotes ("Create a Lead?")
- Include refresh/wait instructions for async operations
- End with verification step ("check for...", "confirm that...")

### Expected Outcome Format

**Pattern A: Simple declarative**
```
Contact is replicated to HubSpot, with all necessary information
```

**Pattern B: Numbered list of expected states**
```
A Lead record is created, and the following values have been set based on the Contact:
1. Lead Owner
2. Service Line
3. Lead Channel
```

**Pattern C: Multi-system chain (integration)**
```
Deal is created in HubSpot.
Line items are added to Deal in HubSpot.
Deal is closed in HubSpot.
Event is created in Arlo.
Event is replicated to HubSpot.
Deal is associated to the Event record in HubSpot.
```

**Pattern D: Negative assertion**
```
Contact in HubSpot is Updated with the information from Arlo.
No duplicate is created
```

### Acceptance Criteria Format

**Pattern A: Bulleted checklist with specific values**
```
- New contact created or updated
- Subscription Type = [Brand] Newsletter
- Lifecycle Stage = Subscriber
```

**Pattern B: Numbered checklist**
```
1. The Deal was created in the appropriate pipeline and stage
2. Ownership is carried over from the Company to the Deal
3. The Deal and Company records are associated properly
```

**Key rules:**
- Use dashes (-) for bullet points, not asterisks
- Include specific property = value assertions
- Reference pipeline/stage names explicitly
- Include association checks

### Integration Style (Multi-System)

**Column structure:**
```
test ID | Systems Involved | Use case scenario | What to do | Expected Result | Results | Arlo Record | HubSpot Record | QBO Record
```

**Always include:**
- Record link columns for each system
- Iterative feedback columns (dated: "6/12/2025 Results", "LSI Feedback 6/12")
- Separate implementation team and client feedback columns

## Status Taxonomy

### Execution Status
- **Not Started** - Test not yet attempted
- **In Progress** - Test currently being executed
- **Blocked** - Cannot proceed due to dependency
- **Completed** - Test execution finished

### Result Status
- **Pass** - Met all acceptance criteria
- **Fail** - Did not meet acceptance criteria
- **Partial Pass** - Some criteria met (see comments)
- **Not Applicable** - Test not relevant for this scope

## Generation Process

When generating UAT documents:

1. **Gather Context**
   - What Hub(s) are being implemented?
   - What integrations are involved?
   - Who are the user roles/personas?
   - What's the testing timeline?

2. **Determine Structure**
   - Single sheet vs multi-sheet workbook
   - By user role vs by functional area
   - Include permission testing?

3. **Generate Scenarios**
   - Cover CRUD operations for each object
   - Include workflow/automation triggers
   - Test edge cases and error handling
   - Validate integrations bi-directionally

4. **Add Supporting Sheets**
   - Feature Requests (separate tracking)
   - Status dashboards (Dev/Client/QA)
   - Instructions/README sheet

## Example: Sales Hub UAT

```markdown
## Sales Hub UAT Scenarios

### Deal Management
| ID | Scenario | Steps | Expected | Status |
|----|----------|-------|----------|--------|
| UAT-DEAL-001 | Create deal from contact | 1. Open contact 2. Click Create Deal 3. Fill required fields 4. Save | Deal created with correct pipeline/stage | Not Started |
| UAT-DEAL-002 | Move deal through stages | 1. Open deal 2. Change stage 3. Save | Stage updates, workflow triggers | Not Started |
| UAT-DEAL-003 | Associate products | 1. Open deal 2. Add line items 3. Save | Products associated, amount calculated | Not Started |

### Automation Testing
| ID | Scenario | Steps | Expected | Status |
|----|----------|-------|----------|--------|
| UAT-WF-001 | Deal stage workflow | 1. Move deal to Qualified 2. Wait 5 min | Task created for owner | Not Started |
| UAT-SEQ-001 | Sales sequence enrollment | 1. Enroll contact 2. Wait for first email | Email sent per schedule | Not Started |
```

## Integration with Project Workflow

1. **Discovery Phase**: Use FSD to identify UAT scenarios
2. **Development Phase**: Create UAT document with scenarios
3. **UAT Phase**: Client executes tests, fills results
4. **Remediation Phase**: Track Changes Made, retest
5. **Sign-off Phase**: All Pass = Go-Live ready

## Related Agents

- `uat-sales-hub` - Deep Sales Hub scenario generation
- `uat-service-hub` - Service Hub specific patterns
- `uat-integration` - Multi-system integration testing
- `uat-migration` - Data migration validation

## Pattern References

- Schema: `~/.claude/knowledge/huble-uat-patterns.json`
- Templates: `~/.claude/templates/uat/`
