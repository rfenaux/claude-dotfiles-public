# Discovery v3.0 JSON Schema

Reference schema for HubSpot Implementation Discovery questionnaires.

## Root Structure

```json
{
  "sessionInfo": {},
  "questionnaire": {},
  "summary": {},
  "sections": []
}
```

## sessionInfo

| Field | Type | Description |
|-------|------|-------------|
| id | number | Session identifier |
| name | string | Project/client name |
| createdAt | ISO date | Creation timestamp |
| email | string | Creator email (nullable) |

## questionnaire

| Field | Type | Description |
|-------|------|-------------|
| id | number | Questionnaire template ID |
| name | string | Template name (e.g., "HubSpot Implementation Discovery v3.0") |
| description | string | Template description |

## summary

| Field | Type | Description |
|-------|------|-------------|
| overallCompletion | string | Percentage complete (e.g., "27%") |
| sectionCompletion | array | Per-section completion status |

### sectionCompletion item

| Field | Type | Description |
|-------|------|-------------|
| sectionId | number | Section ID |
| sectionName | string | Section display name |
| completionPercentage | string | Percentage (e.g., "100%") |

## sections

| Field | Type | Description |
|-------|------|-------------|
| id | number | Section ID |
| name | string | Section name |
| icon | string | Material icon name |
| displayOrder | number | Sort order |
| questions | array | Questions in this section |

### question item

| Field | Type | Description |
|-------|------|-------------|
| id | number | Question ID |
| text | string | Question text |
| subtext | string | Helper text/instructions |
| type | enum | Question type (see below) |
| answer | string | Response value |

## Question Types

| Type | Description | Example Answer |
|------|-------------|----------------|
| `text` | Single-line input | "Project Alpha" |
| `textarea` | Multi-line input | "Long description..." |
| `dropdown` | Single select | "Yes" |
| `checkbox` | Multi-select | "Option1;Option2;Option3" |
| `date` | Date picker | "2026-03-15" |
| `widget` | Complex data entry | "viewed" (indicates widget was opened) |
| `content` | Instructional text | "" (no answer expected) |
| `divider` | Visual separator | "" (no answer expected) |

## Section Icons

| Section | Icon |
|---------|------|
| Scope Details | contacts |
| General Details | work |
| Project Management | school |
| Systems & Data | cloud |
| Middleware/iPaaS | hub |
| Sandbox/Testing | security |
| Documentation | dns |
| Marketing | campaign |
| Sales | currency_exchange |
| Service | support_agent |
| CRM | hub |

## Section IDs

| ID | Section |
|----|---------|
| 267 | Scope Details |
| 268 | General Details |
| 269 | Project Management |
| 270 | Systems & Data Inventory |
| 271 | Middleware and iPaaS |
| 272 | Sandbox, Testing & Signoff |
| 273 | Technical Documentation |
| 274 | Marketing |
| 275 | Sales |
| 276 | Service |
| 277 | CRM |
