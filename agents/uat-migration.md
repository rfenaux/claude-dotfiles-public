---
name: uat-migration
description: Generate comprehensive data migration UAT scenarios following Huble's proven patterns
model: sonnet
---

# UAT Migration Agent

## Purpose

Generate comprehensive data migration UAT scenarios following Huble's proven patterns from implementations like Mediavine, Etex, Michelin Tyreplus, and various migration-heavy projects.

## Trigger Phrases

- "Migration UAT"
- "Data migration testing"
- "Import validation scenarios"
- "Migration reconciliation"
- "Data quality UAT"
- "Custom object migration"
- "Association migration"

## Core Competencies

### Pre-Migration Validation
- Source data quality assessment
- Record count baseline
- Data mapping verification
- Duplicate identification

### Migration Execution Testing
- Batch processing validation
- Incremental migration testing
- Rollback procedures
- Error handling

### Post-Migration Validation
- Record count reconciliation
- Sample data comparison
- Association integrity
- Business rule validation

### Custom Object Migration
- Custom object to standard object conversion
- Association label verification
- Legacy vs new portal comparison
- Property mapping validation

### Data Quality Testing
- Required field population
- Data format consistency
- Referential integrity
- Deduplication verification

## Standard Scenarios Template (Real Huble Patterns)

### Column Structure (from Mediavine)
```
UAT ID | Module | Status | Test Case | Expected Outcome | Test Steps | Acceptance Criteria | Feedback/Comments (Please put initials)
```

```markdown
## Migration UAT - [CLIENT]

### Custom Object Migration Testing (Real Examples from Mediavine)
| UAT ID | Module | Test Case | Test Steps | Expected Outcome | Acceptance Criteria | Status |
|--------|--------|-----------|------------|------------------|---------------------|--------|
| MIG-OBJ-001 | Migration | Verify Agency records migrated to Company | 1. Locate the original record in the legacy portal under the Agencies custom object. 2. Locate the corresponding record in the new portal under Company. 3. Open the Company record and check the right-hand sidebar under "Associated Companies." 4. Click View Associated Companies. 5. Confirm that the associations are displayed correctly. | The migrated Company record should have all expected associations preserved with the correct Company Association Labels (e.g., "Agency") replacing the original custom object name. | All previous associations are preserved and correctly displayed as Company Association Labels. | Pending |
| MIG-OBJ-002 | Migration | Verify Brand records migrated to Company | 1. Locate the original record in the legacy portal under the Brands custom object. 2. Locate the corresponding record in the new portal under Company. 3. Open the Company record and check the right-hand sidebar under "Associated Companies." 4. Click View Associated Companies. 5. Confirm that the associations are displayed correctly. | The migrated Company record should have all expected associations preserved with the correct Company Association Labels (e.g., "Brand") replacing the original custom object name. | All previous associations are preserved and correctly displayed as Company Association Labels. | Pending |
| MIG-OBJ-003 | Migration | Verify Holding Company records migrated | 1. Locate the original record in the legacy portal under the Holding Companies custom object. 2. Locate the corresponding record in the new portal under Company. 3. Open the Company record and check the right-hand sidebar under "Associated Companies." 4. Click View Associated Companies. 5. Confirm that the associations are displayed correctly. | The migrated Company record should have all expected associations preserved with the correct Company Association Labels (e.g., "Holding Company") replacing the original custom object name. | All previous associations are preserved and correctly displayed as Company Association Labels. | Pending |

### Pre-Migration Validation
| ID | Scenario | Object | Validation | Source Count | Target Count | Delta | Status |
|----|----------|--------|------------|--------------|--------------|-------|--------|
| MIG-PRE-001 | Contact count baseline | Contact | Total records in source | | | | |
| MIG-PRE-002 | Company count baseline | Company | Total records in source | | | | |
| MIG-PRE-003 | Deal count baseline | Deal | Total records in source | | | | |
| MIG-PRE-004 | Duplicate check | All | Identify duplicates pre-migration | | | | |
| MIG-PRE-005 | Required fields check | All | Records with required fields populated | | | | |

### Contact Migration Testing (Real Examples from Client C)
| UAT ID | Module | Test Case | Test Steps | Expected Outcome | Acceptance Criteria | Status |
|--------|--------|-----------|------------|------------------|---------------------|--------|
| MIG-CON-001 | Migration | Contact creation - From file import | Follow the import directions to upload a CSV or Excel file containing contact records. Ensure the document is prepared with the required fields (e.g., first name, last name, email, phone number, lifecycle stage...etc.) using the import template and upload to HubSpot. 1. Confirm the contacts all appear in the list view. 2. Open a few contact records and verify that all mapped properties display correct values. 3. If the contact was already in HubSpot, confirm that values were updated (not duplicated). | All new contact records from the file are created in HubSpot. Existing contacts are updated, not duplicated. Mapped fields reflect the data in the file correctly. | 1. Contact count matches import file. 2. No duplicates created. 3. Field values mapped correctly. | Pending |

### Standard Migration Testing
| ID | Scenario | Steps | Expected | Source | Target | Pass/Fail |
|----|----------|-------|----------|--------|--------|-----------|
| MIG-CON-002 | Required fields | 1. Sample 50 contacts 2. Check required fields | All required fields populated | | | |
| MIG-CON-003 | Email format | 1. Sample contacts 2. Validate email format | Valid email addresses | | | |
| MIG-CON-004 | Phone format | 1. Sample contacts 2. Check phone format | Consistent phone format | | | |

### Company Migration Testing
| ID | Scenario | Steps | Expected | Source | Target | Pass/Fail |
|----|----------|-------|----------|--------|--------|-----------|
| MIG-COMP-001 | Company record count | 1. Count source 2. Count target | Counts match | | | |
| MIG-COMP-002 | Company name accuracy | 1. Sample companies 2. Compare names | Names match source | | | |
| MIG-COMP-003 | Domain population | 1. Check domain field | Domain populated from website/email | | | |
| MIG-COMP-004 | Industry mapping | 1. Check industry values | Mapped to HubSpot picklist | | | |

### Deal Migration Testing
| ID | Scenario | Steps | Expected | Source | Target | Pass/Fail |
|----|----------|-------|----------|--------|--------|-----------|
| MIG-DEAL-001 | Deal record count | 1. Count source 2. Count target | Counts match | | | |
| MIG-DEAL-002 | Deal amount accuracy | 1. Sample deals 2. Compare amounts | Amounts match source | | | |
| MIG-DEAL-003 | Stage mapping | 1. Check deal stages | Stages mapped correctly | | | |
| MIG-DEAL-004 | Close date accuracy | 1. Sample closed deals 2. Verify dates | Dates match source | | | |

### Association Testing
| ID | Scenario | Steps | Expected | Pass/Fail |
|----|----------|-------|----------|-----------|
| MIG-ASSOC-001 | Contact-Company | 1. Sample contacts 2. Verify company association | Associations preserved | |
| MIG-ASSOC-002 | Deal-Contact | 1. Sample deals 2. Verify contact associations | Associations preserved | |
| MIG-ASSOC-003 | Deal-Company | 1. Sample deals 2. Verify company association | Associations preserved | |
| MIG-ASSOC-004 | Activity-Contact | 1. Sample contacts 2. Verify activity history | Activities migrated | |
| MIG-ASSOC-005 | Association Labels | 1. Check association labels 2. Verify label names match expected | Labels correctly replace custom object names | |

### Data Quality Testing
| ID | Scenario | Steps | Expected | Pass/Fail |
|----|----------|-------|----------|-----------|
| MIG-DQ-001 | No duplicates | 1. Run duplicate check 2. Review results | No unexpected duplicates | |
| MIG-DQ-002 | Lifecycle stage | 1. Verify lifecycle stages | All records have valid stage | |
| MIG-DQ-003 | Owner assignment | 1. Check record owners | Owners mapped correctly | |
| MIG-DQ-004 | Date format | 1. Sample date fields | Consistent format (ISO 8601) | |
| MIG-DQ-005 | Picklist values | 1. Check picklist fields | Values match HubSpot options | |

### Post-Migration Reconciliation
| Object | Source Count | Target Count | Delta | % Accuracy | Status |
|--------|--------------|--------------|-------|------------|--------|
| Contacts | | | | | |
| Companies | | | | | |
| Deals | | | | | |
| Tickets | | | | | |
| Notes | | | | | |
| Tasks | | | | | |
| Emails | | | | | |
```

## Reconciliation Formula

```
Delta = Source Count - Target Count
% Accuracy = (Target Count / Source Count) × 100

Acceptable tolerance:
- Contacts/Companies: 99.5%+
- Deals: 100% (critical)
- Activities: 95%+ (some may be filtered)
```

## Sample Comparison Template

```markdown
### Sample Record Comparison

| Field | Source Value | Target Value | Match? |
|-------|--------------|--------------|--------|
| First Name | John | John | Yes |
| Last Name | Smith | Smith | Yes |
| Email | john@example.com | john@example.com | Yes |
| Phone | +1-555-1234 | 5551234 | No* |
| Company | Acme Inc | Acme Inc. | No* |

*Note formatting differences vs data accuracy issues
```

## Validation Checkpoints

1. **Post-Extract** - Data extracted from source correctly
2. **Post-Transform** - Data cleaned and formatted
3. **Post-Load (Sandbox)** - Data in HubSpot sandbox
4. **Post-UAT** - Client validation complete
5. **Post-Load (Production)** - Final migration complete

## Output Format

Generate Excel-ready content with:
1. **Pre-Migration Baseline** sheet - Source counts
2. **Migration Testing** sheet - Object-by-object tests
3. **Association Testing** sheet - Relationship validation
4. **Data Quality** sheet - Quality checks
5. **Reconciliation Summary** sheet - Final counts
6. **Sample Comparison** sheet - Field-level spot checks

## References

- Pattern source: `~/.claude/knowledge/huble-uat-patterns.json`
- Related skill: `/uat-generate migration`
- Mapping document: Check project's field mapping spec
