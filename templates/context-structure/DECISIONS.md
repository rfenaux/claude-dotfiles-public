# Architecture Decisions Log

> This file tracks key decisions made during the project. Claude uses this to avoid repeating past discussions and to understand the current state of decisions.
>
> **Format**: Newest decisions at top. Superseded decisions move to the "Superseded" section with a link to what replaced them.

---

## Active Decisions

<!-- Template for new decisions:

### [Decision Title]
- **Decided**: YYYY-MM-DD
- **Context**: Why this decision was needed
- **Choice**: What was decided
- **Alternatives considered**: What was rejected and why
- **Supersedes**: [Previous decision if any]
- **References**: Session dates, document names, stakeholders

-->

### Example: Database Choice - PostgreSQL
- **Decided**: 2026-01-07
- **Context**: Need relational database for CRM data with complex relationships
- **Choice**: PostgreSQL with Prisma ORM
- **Alternatives considered**:
  - MongoDB: Rejected due to relational integrity requirements
  - MySQL: PostgreSQL has better JSON support for flexible fields
- **Supersedes**: Initial MongoDB consideration (2025-12-15)
- **References**: Architecture workshop 2026-01-05, Technical spec v2.1

---

## Superseded Decisions

<!-- Decisions that have been replaced. Keep for historical context. -->

### ~~MongoDB for Primary Database~~ → PostgreSQL (2026-01-07)
- **Original decision**: 2025-12-15
- **Why superseded**: Relational requirements emerged during discovery
- **Replaced by**: PostgreSQL decision above

---

## Decision Categories

Use these tags in your decisions for easier searching:

| Category | Use For |
|----------|---------|
| `architecture` | System design, tech stack |
| `integration` | Third-party connections |
| `data-model` | Schema, entities, relationships |
| `security` | Auth, permissions, compliance |
| `process` | Workflows, business logic |
| `scope` | What's in/out of project |
| `timeline` | Milestones, deadlines |

---

## How Claude Should Use This File

1. **Before proposing architecture**: Check if a decision already exists
2. **When user references "we decided"**: Search here first
3. **When conflicts arise**: Prefer decisions with newer dates
4. **After making new decisions**: Ask user if they want to add to this log
