# Discovery Output Templates

Templates for consolidating discovery findings into actionable deliverables.

## Discovery Summary Report

```markdown
# Project Discovery Summary

**Project**: [Project Name]
**Client**: [Client Name]
**Date**: [Discovery Date]
**Version**: [Version Number]

---

## 1. Executive Overview

[2-3 sentence summary: What is this project? Why now? What's the desired outcome?]

**Project Type**: [Migration / Integration / Greenfield / Optimization]
**Timeline**: [Start Date] → [Go-Live Date] ([X] months)
**Functions in Scope**: [Marketing, Sales, Service, Operations]

---

## 2. Project Triggers & Success Criteria

### Business Triggers
- [Trigger 1]
- [Trigger 2]

### Success Criteria
| Metric | Current State | Target State | Measurement |
|--------|---------------|--------------|-------------|
| | | | |

---

## 3. Scope Definition

### In Scope
- [Item 1]
- [Item 2]

### Out of Scope
- [Item 1]
- [Item 2]

### Divisions/Regions
| Division | Region | Key Variations |
|----------|--------|----------------|
| | | |

---

## 4. Stakeholder Map

| Role | Name | Involvement | Decision Authority |
|------|------|-------------|-------------------|
| Executive Sponsor | | | |
| Project Manager | | | |
| Technical Lead | | | |
| Business Lead | | | |

---

## 5. Systems Landscape

### Current State
[Diagram or table of current systems]

### Future State
[Diagram or table of planned systems]

### Integration Requirements
| Source | Target | Direction | Data/Triggers | Priority |
|--------|--------|-----------|---------------|----------|
| | | | | |

### Data Migration Summary
| Object | Volume | Source | Historical Depth | Complexity |
|--------|--------|--------|------------------|------------|
| | | | | |

---

## 6. Requirements by Function

### [Function: Marketing/Sales/Service/Operations]

#### Key Processes
| Process | Current State | Future State | Gap |
|---------|---------------|--------------|-----|
| | | | |

#### User Requirements
| Role | Count | Key Needs |
|------|-------|-----------|
| | | |

#### Automation Requirements
- [Requirement 1]
- [Requirement 2]

---

## 7. Technical Requirements

### Compliance & Security
- [Requirement 1]
- [Requirement 2]

### Data Quality
- [Requirement 1]
- [Requirement 2]

### Documentation Deliverables
| Artifact | Detail Level | Priority |
|----------|--------------|----------|
| | Basic/Comprehensive | |

---

## 8. Project Approach

### Governance
- Steering Committee: [Frequency]
- Working Sessions: [Frequency]
- Status Reporting: [Frequency]

### Testing Approach
- Sandbox: [Yes/No] - Components: [List]
- UAT: [Approach]

### Training Approach
- [Approach and documentation types]

---

## 9. Risks & Dependencies

| ID | Risk/Dependency | Likelihood | Impact | Mitigation | Owner |
|----|-----------------|------------|--------|------------|-------|
| R1 | | H/M/L | H/M/L | | |
| D1 | | | | | |

---

## 10. Open Questions

| ID | Question | Owner | Due Date | Status |
|----|----------|-------|----------|--------|
| Q1 | | | | Open/Closed |

---

## 11. Next Steps

1. [Action item] - Owner - Due Date
2. [Action item] - Owner - Due Date

---

## Appendices

- A: Detailed Requirements Matrix
- B: Integration Specifications
- C: Data Mapping
- D: Meeting Notes
```

---

## Requirements Matrix Template

```markdown
# Requirements Matrix

**Project**: [Project Name]
**Last Updated**: [Date]

## Legend
- **Priority**: Must Have (MH) | Should Have (SH) | Nice to Have (NH)
- **Complexity**: Low (L) | Medium (M) | High (H)
- **Status**: Identified | Confirmed | In Progress | Complete | Deferred

---

| ID | Category | Requirement | Priority | Complexity | Phase | Status | Notes |
|----|----------|-------------|----------|------------|-------|--------|-------|
| REQ-001 | | | | | | | |
| REQ-002 | | | | | | | |
```

---

## Integration Blueprint Template

```markdown
# Integration Blueprint

**Project**: [Project Name]
**Integration**: [Source System] ↔ [Target System]
**Last Updated**: [Date]

---

## 1. Overview

**Purpose**: [Why this integration exists]
**Direction**: [Unidirectional / Bidirectional]
**Pattern**: [Real-time / Batch / Event-driven]
**Middleware**: [Tool name or Native]

---

## 2. System Diagram

```
[ASCII or reference to diagram]
```

---

## 3. Object Mapping

| Source Object | Target Object | Sync Direction | Trigger |
|---------------|---------------|----------------|---------|
| | | | |

---

## 4. Field Mapping

### [Object Name]

| Source Field | Target Field | Transformation | Required | Notes |
|--------------|--------------|----------------|----------|-------|
| | | | | |

---

## 5. Sync Rules

### Creation
- [Rule 1]

### Update
- [Rule 1]

### Deletion
- [Rule 1]

### Conflict Resolution
- [Rule 1]

---

## 6. Error Handling

| Error Type | Handling | Notification | Retry |
|------------|----------|--------------|-------|
| | | | |

---

## 7. Testing Scenarios

| ID | Scenario | Expected Result | Status |
|----|----------|-----------------|--------|
| T1 | | | |
```

---

## Data Migration Checklist

```markdown
# Data Migration Checklist

**Project**: [Project Name]
**Migration Date**: [Date]

## Pre-Migration

- [ ] Source data audit complete
- [ ] Data cleansing complete
- [ ] Field mapping documented
- [ ] Transformation rules defined
- [ ] Validation rules defined
- [ ] Sandbox test migration complete
- [ ] Volume estimates confirmed
- [ ] Rollback plan documented
- [ ] Stakeholder sign-off obtained

## Migration Execution

- [ ] Source system read-only or snapshot taken
- [ ] Data extracted
- [ ] Transformations applied
- [ ] Data loaded to target
- [ ] Record counts validated
- [ ] Sample records spot-checked
- [ ] Relationships/associations verified
- [ ] Historical data verified

## Post-Migration

- [ ] Validation report generated
- [ ] Exceptions documented
- [ ] Stakeholder verification complete
- [ ] Source system archived/decommissioned
- [ ] Documentation updated
```

---

## RACI Template

```markdown
# Project RACI Matrix

**R** = Responsible | **A** = Accountable | **C** = Consulted | **I** = Informed

| Activity | [Role 1] | [Role 2] | [Role 3] | [Role 4] |
|----------|----------|----------|----------|----------|
| Project Planning | | | | |
| Requirements Gathering | | | | |
| Solution Design | | | | |
| Configuration | | | | |
| Data Migration | | | | |
| Integration Development | | | | |
| Testing | | | | |
| Training | | | | |
| Go-Live | | | | |
| Hypercare | | | | |
```
