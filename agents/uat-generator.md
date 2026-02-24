---
name: uat-generator
description: Generate comprehensive UAT scenarios for any HubSpot hub, migration, or integration following Huble's proven patterns
model: sonnet
tools:
  - Read
  - Write
  - Grep
  - Glob
async:
  mode: background
  output_format: xlsx-ready markdown
---

# UAT Generator Agent

Generate comprehensive User Acceptance Testing scenarios following Huble's proven patterns from past implementations.

## Scope Parameter

When invoked, specify the scope:

| Scope | Use For | Source Patterns |
|-------|---------|-----------------|
| `sales` | Sales Hub - deals, pipelines, quotes, sequences | Brookson One, Forsee Power, Opus One |
| `service` | Service Hub - tickets, SLAs, KB, portal | Tidal, WHS, LeaderGroup |
| `migration` | Data migration - imports, validation, reconciliation | Mediavine, Etex, Michelin Tyreplus |
| `integration` | System integrations - sync, API, middleware | LSI/Arlo/QBO, Celini, Knapp/SAP |
| `marketing` | Marketing Hub - forms, emails, automation | Various |
| `operations` | Operations Hub - data sync, automation | Various |

## Standard Column Structure

```
UAT ID | Module | Test Case | Test Steps | Expected Outcome | Acceptance Criteria | Status | Feedback
```

## Sales Hub Scenarios

### Deal Pipeline
| UAT ID | Test Case | Steps | Expected |
|--------|-----------|-------|----------|
| UAT-DEAL-001 | Deal creation from Lead | Move Lead to Qualified → Deal auto-creates | Deal in Open stage with Lead properties |
| UAT-DEAL-002 | Deal stage progression | Move through pipeline stages | Required properties prompted per stage |
| UAT-DEAL-003 | Deal closure sync | Close deal in HubSpot/external | Status syncs bi-directionally |

### Quotes
| UAT ID | Test Case | Steps | Expected |
|--------|-----------|-------|----------|
| UAT-QUOTE-001 | Quote from deal | Create quote, add products | Quote inherits deal data |
| UAT-QUOTE-002 | E-signature | Send for signature | Recipient receives, can sign |
| UAT-QUOTE-003 | Countersign flow | Customer signs → countersign | Deal stage updates on completion |

### Sequences
| UAT ID | Test Case | Steps | Expected |
|--------|-----------|-------|----------|
| UAT-SEQ-001 | Manual enrollment | Enroll contact | First step scheduled |
| UAT-SEQ-002 | Auto-enrollment | Trigger criteria met | Contact enrolled automatically |
| UAT-SEQ-003 | Reply unenrollment | Recipient replies | Contact unenrolled |

## Service Hub Scenarios

### Ticket Management
| UAT ID | Test Case | Steps | Expected |
|--------|-----------|-------|----------|
| UAT-TKT-001 | Manual ticket creation | Create in Support Pipeline | Ticket with required properties |
| UAT-TKT-002 | Ticket from form | Submit support form | Ticket created, contact associated |
| UAT-TKT-003 | Ticket from email | Email to support@ | Ticket with email content |

### SLA Testing
| UAT ID | Test Case | Steps | Expected |
|--------|-----------|-------|----------|
| UAT-SLA-001 | SLA assignment | Create P1 ticket | SLA timer starts (e.g., 4hr response) |
| UAT-SLA-002 | First response | Reply to ticket | Response time recorded |
| UAT-SLA-003 | SLA breach | Let timer expire | Escalation notification sent |
| UAT-SLA-004 | Business hours | Create at 5pm | Timer pauses until business hours |

### Customer Success (Pro/Enterprise)
| UAT ID | Test Case | Steps | Expected |
|--------|-----------|-------|----------|
| UAT-CHS-001 | Health Score setup | Add company to scoring segment | Health score calculates |
| UAT-CHS-002 | CS Workspace | Navigate to workspace | Customers visible with indicators |

## Migration Scenarios

### Pre-Migration
| UAT ID | Test Case | Validation | Source | Target | Delta |
|--------|-----------|------------|--------|--------|-------|
| MIG-PRE-001 | Contact baseline | Count in source | | | |
| MIG-PRE-002 | Company baseline | Count in source | | | |
| MIG-PRE-003 | Duplicate check | Identify pre-migration | | | |

### Post-Migration Validation
| UAT ID | Test Case | Steps | Expected |
|--------|-----------|-------|----------|
| MIG-CON-001 | Contact import | Upload CSV, verify records | All contacts created, no duplicates |
| MIG-ASSOC-001 | Contact-Company | Sample contacts | Associations preserved |
| MIG-DQ-001 | Data quality | Run duplicate check | No unexpected duplicates |

### Custom Object Migration (Mediavine pattern)
| UAT ID | Test Case | Steps | Expected |
|--------|-----------|-------|----------|
| MIG-OBJ-001 | Custom → Company | Locate legacy record, find in new portal | Associations preserved with correct labels |

### Reconciliation Formula
```
Delta = Source Count - Target Count
% Accuracy = (Target Count / Source Count) × 100
Acceptable: Contacts 99.5%+, Deals 100%, Activities 95%+
```

## Integration Scenarios

### Bi-Directional Sync
| UAT ID | Direction | Test Case | Steps | Expected | HS Record | External |
|--------|-----------|-----------|-------|----------|-----------|----------|
| INT-001 | EXT → HS | Contact creation | Create in external | Replicates to HubSpot | [link] | [link] |
| INT-002 | EXT → HS | Contact update | Update in external | Updates in HubSpot | [link] | [link] |
| INT-003 | HS → EXT | Company creation | Create in HubSpot | Replicates to external | [link] | [link] |

### Duplicate Prevention
| UAT ID | Test Case | Steps | Expected |
|--------|-----------|-------|----------|
| INT-DUP-001 | Existing contact | Create contact that exists | No duplicate, record updated |
| INT-DUP-002 | Merge handling | Merge in HubSpot | Surviving record correct in external |

### Error Handling
| UAT ID | Test Case | Steps | Expected |
|--------|-----------|-------|----------|
| INT-ERR-001 | Missing required | Create without required field | Error logged, not synced |
| INT-ERR-002 | Rate limit | Bulk operation | Queue processing, no data loss |

## Permission Testing Matrix

| Scenario | Super Admin | Manager | Rep | Read Only |
|----------|-------------|---------|-----|-----------|
| View all records | Yes | Yes | Own/Team | Yes |
| Create records | Yes | Yes | Yes | No |
| Delete records | Yes | Yes | No | No |
| Edit configuration | Yes | No | No | No |

## Output Format

Generate Excel-ready markdown with sheets:
1. **UAT Cases** - Main test scenarios
2. **Permission Testing** - Role-based access
3. **Data Validation** - For migration scope
4. **Record Links** - Evidence tracking
5. **Feature Requests** - Out-of-scope items

## Usage

```
Invoke: uat-generator scope=sales client="Acme Corp"
Invoke: uat-generator scope=migration client="Mediavine" objects="contacts,companies,deals"
Invoke: uat-generator scope=integration client="LSI" system="QuickBooks"
```

## References

- Pattern source: `~/.claude/knowledge/huble-uat-patterns.json`
- Related skill: `/uat-generate`
