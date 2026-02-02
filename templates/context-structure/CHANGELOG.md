# Project Changelog

> Tracks significant changes to the project. Different from git commits — this captures *why* things changed at a higher level.
>
> **Use**: When you need to know what evolved and when, especially for context that affects multiple files.

---

## 2026-01

### 2026-01-07
- **Initial Setup**: Created project structure with `.claude/context/` memory system
- **Architecture**: Selected PostgreSQL + Prisma stack
- **Integration**: Defined HubSpot as primary CRM target

---

## Changelog Categories

| Prefix | Meaning |
|--------|---------|
| `[ARCH]` | Architecture changes |
| `[DATA]` | Data model changes |
| `[SCOPE]` | Scope additions/removals |
| `[DECISION]` | Major decisions |
| `[PIVOT]` | Direction changes |

---

## How Claude Uses This

1. When asked "what changed since [date]" — scan this first
2. When context seems stale — check for recent changes
3. Before making assumptions — verify current state here
