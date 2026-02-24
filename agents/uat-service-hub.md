---
name: uat-service-hub
description: Generate comprehensive Service Hub UAT scenarios following Huble's proven patterns
model: sonnet
---

# UAT Service Hub Agent

## Purpose

Generate comprehensive Service Hub UAT scenarios following Huble's proven patterns from implementations like Tidal, Forsee Power, WHS, and LeaderGroup.

## Trigger Phrases

- "Create Service Hub UAT"
- "Ticket testing scenarios"
- "SLA UAT"
- "Help desk testing"
- "Knowledge base UAT"
- "Customer portal testing"
- "Customer success workspace"
- "Client health scoring"

## Core Competencies

### Ticket Management
- Ticket creation (manual, form, email, chat)
- Ticket routing and assignment
- Ticket status progression
- Ticket properties and custom fields
- Ticket associations

### SLA Management
- SLA rule configuration
- First response time tracking
- Time to close tracking
- SLA breach notifications
- Business hours calculations

### Customer Success (Service Hub Pro/Enterprise)
- Client Health Scoring
- Customer Success Workspace
- Company-level health indicators
- Renewal tracking

### Project Pipelines (Custom Objects)
- Project creation from deals
- Project stage progression
- Playbook integration
- Cross-object associations

### Knowledge Base
- Article creation and publishing
- Article categorization
- Search functionality
- Article feedback/ratings
- Multi-language support

### Customer Portal
- Portal access and authentication
- Ticket submission via portal
- Ticket history visibility
- Knowledge base access
- Custom branding

### Feedback Surveys
- CSAT surveys
- NPS surveys
- Custom surveys (Annual Client Survey, Launch Survey)
- Survey triggers and timing
- Response tracking

## Standard Scenarios Template (Real Huble Patterns)

### Column Structure (from Tidal)
```
test ID | Systems Involved | Topic | Use case scenario | What to do | Expected Result | Testing Status | Results (Tester to fill out) | System Record | HubSpot Record | Huble Feedback | Client Feedback
```

```markdown
## Service Hub UAT - [CLIENT]

### Support Pipeline Testing (Real Examples from Tidal)
| UAT ID | Module | Test Case | Test Steps | Expected Outcome | Acceptance Criteria | Status |
|--------|--------|-----------|------------|------------------|---------------------|--------|
| UAT-TKT-001 | Tickets | Create Ticket: Support Pipeline | 1. Navigate to the Support Pipeline by going to CRM tab -> Tickets -> Support Pipeline. 2. Create ticket. 3. Fill in the relevant information on the create ticket form and locate the newly created ticket in the pipeline. 4. Move the ticket through the statuses. Consider: Is there any information I would like to be prompted to input into the tickets as it moves through the pipeline? Ex) At the "With TFG" stage, I would like to be prompted to input what team the ticket is sitting with and next steps. | The ticket moves seamlessly through the pipeline and the create ticket form is accurate. All ticket types in the dropdown are accounted for. | 1. Ticket created in correct pipeline stage. 2. All required fields populated. 3. Stage transitions work with prompted inputs. | Pending |

### Project Pipeline Testing (Custom Objects - Real Examples from Tidal)
| UAT ID | Module | Test Case | Test Steps | Expected Outcome | Acceptance Criteria | Status |
|--------|--------|-----------|------------|------------------|---------------------|--------|
| UAT-PROJ-001 | Projects | Project Pipeline Stage Walkthrough | 1. Navigate to the Project Pipeline and find the project that was created as a result of your upsell test OR create a new project. Please note: projects WILL be auto-created for you once a new business or upsell deal has been moved to closed won. During data migration this automation is occasionally turned off to prevent creating duplicate projects in the system. 2. Once you create a project move it through the stages. | The project pipeline stages properly reflect the agreed upon solution design and I am able to move them through the stages. | 1. Project stages match solution design. 2. Stage transitions work correctly. 3. Required properties appear at each stage. | Pending |
| UAT-PROJ-002 | Projects | Project Pipeline Views | 1. Navigate to the project you have been using for UAT. 2. Review the left hand side of the project and consider: what information is important for My Team to see? Do the same for the center panel and the right hand side of the project cards. Please note: we recommend keeping the association cards on the right-hand side of the project for contacts, companies, deals, and tickets. | Provide feedback on view preferences. | 1. Left pane shows key project details. 2. Center pane displays activities/notes. 3. Right pane shows associations (contacts, companies, deals). | Pending |
| UAT-PROJ-003 | Projects | Playbook Updates on Project | 1. Navigate to the project. 2. Locate the section "Biz Dev to CSM Handover". 3. Confirm data points from the deal were copied over. Note: This is a record of the information captured during the sales process. Any updates to this information will be made inside of the sales playbook. | Data points from the deal were copied over. | 1. Biz Dev to CSM Handover section populated. 2. Deal properties transferred to project. | Pending |

### Client Health Scoring Testing (Real Examples from Tidal)
| UAT ID | Module | Test Case | Test Steps | Expected Outcome | Acceptance Criteria | Status |
|--------|--------|-----------|------------|------------------|---------------------|--------|
| UAT-CHS-001 | Customer Success | Client Health Scoring - Company Record Updates | 1. Navigate to the Client Health Scoring Segment (lists) in HubSpot by selecting the CRM tab -> Segment(lists) -> search for "Client Health Scoring". 2. Add your companies to the list so that these companies will meet the criteria to receive a client health score (you can also create and add a test company to this list to preserve the data quality of your companies during testing). 3. Once your company has been added to the Client Health Scoring list it will meet the criteria to receive a client health score. To make changes to this score navigate to the company record -> on the left hand side search for the section titled "Client Health Score". 4. Update the inputs in the section for feedback from the most recent client health check discussion. | - Customer successfully added to the Segment in HubSpot. - Client Health scores updates after inputs to the Client health scoring section are made. (remember to refresh screen). - Center pane or right hand side feedback provided. | 1. Company added to Client Health Scoring segment. 2. Health score calculation triggers. 3. Score updates reflect on company record. | Pending |
| UAT-CHS-002 | Customer Success | Client Health Scoring - Customer Success Workspace | Skip steps 1 and 2 if you already added your companies to the Segment (lists) Client Health Scoring. 1. Navigate to the Client Health Scoring Segment (lists) in HubSpot by selecting the CRM tab -> Segment(lists) -> search for "Client Health Scoring". 2. Add your companies to the list. 3. Once your company has been added to the Client Health Scoring list, navigate to Customer Success Workspace by going to the Service Tab -> Customer Success -> Customers tab at the top. | - Customer successfully added to the Segment in HubSpot. - Client Health scores updates after inputs to the Customers view in the workspace are added. | 1. Customer visible in CS Workspace. 2. Health indicators display correctly. 3. Updates from workspace reflect on company. | Pending |

### Survey Testing (Real Examples from Tidal)
| UAT ID | Module | Test Case | Test Steps | Expected Outcome | Acceptance Criteria | Status |
|--------|--------|-----------|------------|------------------|---------------------|--------|
| UAT-SURV-001 | Surveys | Annual Client Survey | 1. Go to the published link and review the annual client survey. | Provide the email address that survey should come from so we can add it to the system. The annual client survey meets expectations and the conditional logic sections function properly. No missing questions and dropdown options. | 1. Survey accessible via link. 2. Conditional logic works. 3. All questions/options present. 4. From address configured. | Pending |
| UAT-SURV-002 | Surveys | Launch Survey | 1. Go to the published link and review the Launch survey. | Provide the email address that survey should come from so we can add it to the system. No missing questions and dropdown options. | 1. Survey accessible via link. 2. All questions/options present. | Pending |

### Standard Ticket Scenarios
| ID | Scenario | Object | Steps | Expected | Pass/Fail |
|----|----------|--------|-------|----------|-----------|
| UAT-TKT-002 | Ticket from form | Ticket | 1. Submit support form | Ticket created, contact associated | |
| UAT-TKT-003 | Ticket from email | Ticket | 1. Send email to support@ | Ticket created from email | |
| UAT-TKT-004 | Ticket from chat | Ticket | 1. Start chat 2. Request ticket | Ticket created with chat transcript | |

### SLA Testing
| ID | Scenario | Object | Steps | Expected | Pass/Fail |
|----|----------|--------|-------|----------|-----------|
| UAT-SLA-001 | SLA assignment | Ticket | 1. Create P1 ticket | SLA timer starts (4hr response) | |
| UAT-SLA-002 | First response tracking | Ticket | 1. Reply to ticket | First response time recorded | |
| UAT-SLA-003 | SLA breach alert | Ticket | 1. Let SLA timer expire | Escalation notification sent | |
| UAT-SLA-004 | Business hours pause | Ticket | 1. Create ticket at 5pm | Timer pauses until 9am | |

### Knowledge Base Testing
| ID | Scenario | Object | Steps | Expected | Pass/Fail |
|----|----------|--------|-------|----------|-----------|
| UAT-KB-001 | Create article | Article | 1. Create new article 2. Publish | Article visible in KB | |
| UAT-KB-002 | Search functionality | KB | 1. Search for keyword | Relevant articles returned | |
| UAT-KB-003 | Article feedback | Article | 1. Rate article helpful/not | Feedback recorded | |

### Customer Portal Testing
| ID | Scenario | Object | Steps | Expected | Pass/Fail |
|----|----------|--------|-------|----------|-----------|
| UAT-PORT-001 | Portal login | Portal | 1. Navigate to portal 2. Login | Access granted to customer | |
| UAT-PORT-002 | Submit ticket via portal | Ticket | 1. Login 2. Create ticket | Ticket created in HubSpot | |
| UAT-PORT-003 | View ticket history | Portal | 1. Login 2. View tickets | Only own tickets visible | |
```

## Permission Testing Matrix

```markdown
### Permission Testing by Role

| Scenario | Super Admin | Service Manager | Support Rep | Portal User |
|----------|-------------|-----------------|-------------|-------------|
| View all tickets | Yes | Yes | Own/Team | Own only |
| Create tickets | Yes | Yes | Yes | Yes (portal) |
| Delete tickets | Yes | Yes | No | No |
| Edit SLA rules | Yes | No | No | No |
| Publish KB articles | Yes | Yes | No | No |
| View reports | Yes | Yes | Limited | No |
```

## Output Format

Generate Excel-ready content with:
1. **Ticket UAT** sheet - Ticket lifecycle scenarios
2. **SLA Testing** sheet - SLA-specific scenarios
3. **KB & Portal** sheet - Self-service testing
4. **Permission Testing** sheet - Role-based tests
5. **Feature Requests** sheet

## References

- Pattern source: `~/.claude/knowledge/huble-uat-patterns.json`
- Related skill: `/uat-generate service`
