# Session Summaries

> Auto-generated summaries of key sessions. Claude uses this to quickly recall what was discussed without searching full conversation history.
>
> **Rule**: Add a summary after significant sessions (architecture discussions, decision-making, major implementations).

---

## Recent Sessions

### 2026-01-07 — Example Session
**Focus**: Initial project setup and architecture decisions
**Key Outcomes**:
- Chose PostgreSQL over MongoDB for database
- Defined initial entity model (Users, Projects, Tasks)
- Agreed on HubSpot as CRM integration target

**Decisions Made**:
- See DECISIONS.md: "Database Choice - PostgreSQL"

**Open Questions**:
- Authentication approach TBD (OAuth vs Magic Links)
- Hosting platform not yet decided

**Next Steps**:
- [ ] Create detailed ERD
- [ ] Draft integration specification

---

## Session Template

```markdown
### YYYY-MM-DD — [Session Focus]
**Focus**: Brief description of main topic
**Key Outcomes**:
- Bullet points of what was accomplished

**Decisions Made**:
- Link to DECISIONS.md entries

**Open Questions**:
- Items still needing resolution

**Next Steps**:
- [ ] Action items from this session
```

---

## How to Add Sessions

**Option 1**: Ask Claude at end of session:
> "Summarize this session for SESSIONS.md"

**Option 2**: Auto-capture via PreCompact hook (already configured)

**Option 3**: Manual entry when you notice important context was established
