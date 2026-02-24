---
name: client-onboard
description: Onboard a new client project with full Claude Code infrastructure - RAG, memory, brand kit, CTM task, and templates. One command to start a new engagement.
trigger: /client-onboard
context: fork
agent: general-purpose
model: sonnet
tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
async:
  mode: never
  require_sync:
    - user input for client details
    - interactive setup choices
---

# Client Onboarding Skill

Streamlined onboarding for new consulting engagements. Creates complete project infrastructure in one command.

## Triggers

Invoke when user says:
- "/client-onboard", "client onboard", "onboard client"
- "new client: [name]", "start engagement for [client]"
- "set up [client] project"

## Syntax

```bash
/client-onboard "Client Name" [--industry "Industry"] [--crm "Platform"] [--quick]
```

**Examples:**
- `/client-onboard "Acme Corp"`
- `/client-onboard "GlobalTech" --industry "Manufacturing" --crm "HubSpot"`
- `/client-onboard "StartupXYZ" --quick`

## Workflow

### Phase 1: Gather Client Information

If not provided via arguments, ask:

1. **Client Name** (required)
2. **Industry** (optional but recommended)
3. **CRM Platform** (HubSpot, Salesforce, Zoho, None)
4. **Engagement Type** (Implementation, Optimization, Migration, Audit)
5. **Project Location** (default: `~/Documents/Projects - Pro/Huble/{client-slug}/`)

**Default paths by type:**

| Type | Base Path |
|------|-----------|
| **Pro (Huble)** (default for client-onboard) | `~/Documents/Projects - Pro/Huble/{client-slug}/` |
| **Private** | `~/Documents/Projects - Private/{client-slug}/` |

Since `/client-onboard` is for consulting engagements, default to Pro/Huble path unless `--private` flag is used.

**Slug generation:** Lowercase, spaces→hyphens, strip special chars (e.g., "Forsee Power" → `forsee-power`)

### Phase 2: Create Project Structure

```
{client-slug}/
├── .claude/
│   └── context/
│       ├── DECISIONS.md
│       ├── SESSIONS.md
│       ├── STAKEHOLDERS.md
│       └── CLIENT_BRIEF.md      # New: Client-specific context
├── .rag/                        # RAG index
├── .brand/                      # Brand assets (from extraction)
│   └── BRAND_KIT.md
├── deliverables/                # Output documents
├── discovery/                   # Discovery materials
└── README.md                    # Project overview
```

**Commands:**
```bash
mkdir -p {project-path}/.claude/context
mkdir -p {project-path}/.brand
mkdir -p {project-path}/deliverables
mkdir -p {project-path}/discovery
```

### Phase 3: Initialize RAG

```bash
cd {project-path}
# Use MCP tool
rag_init project_path={project-path}
```

### Phase 4: Create Memory Files

**CLIENT_BRIEF.md:**
```markdown
# Client Brief: {Client Name}

> Created: {DATE} | Industry: {Industry} | CRM: {Platform}

## Overview

| Attribute | Value |
|-----------|-------|
| **Client** | {Client Name} |
| **Industry** | {Industry} |
| **CRM Platform** | {Platform} |
| **Engagement Type** | {Type} |
| **Start Date** | {DATE} |

## Business Context

_Document key business context here._

## Technical Landscape

| System | Purpose | Integration Priority |
|--------|---------|---------------------|
| | | |

## Success Criteria

_What does success look like for this engagement?_

## Constraints

_Budget, timeline, technical, or organizational constraints._

## Key Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| | | |
```

**DECISIONS.md:**
```markdown
# Architecture Decisions: {Client Name}

> Created: {DATE} | Project: {client-slug}

## Active Decisions

_No decisions recorded yet._

## Superseded Decisions

_None._

---

## Decision Format

### [Decision Title]
- **Decided**: YYYY-MM-DD
- **Decision**: What was decided
- **Context**: Why this choice
- **Alternatives**: What was considered
- **Supersedes**: (if replacing another decision)
```

**SESSIONS.md:**
```markdown
# Session Log: {Client Name}

> Project: {client-slug}

## Sessions

### {DATE} - Project Kickoff
- **Focus**: Initial setup and onboarding
- **Outcomes**: Project infrastructure created
- **Next**: Discovery session
```

**STAKEHOLDERS.md:**
```markdown
# Stakeholders: {Client Name}

## Key People

| Name | Role | Email | Communication Preference |
|------|------|-------|-------------------------|
| _TBD_ | Project Sponsor | | |
| _TBD_ | Technical Lead | | |
| _TBD_ | Business SME | | |

## RACI Notes

_Document decision-making authority and escalation paths._
```

### Phase 5: Create README

**README.md:**
```markdown
# {Client Name} Engagement

> Industry: {Industry} | Platform: {CRM Platform} | Started: {DATE}

## Quick Links

- [Client Brief](.claude/context/CLIENT_BRIEF.md)
- [Decisions](.claude/context/DECISIONS.md)
- [Sessions](.claude/context/SESSIONS.md)
- [Stakeholders](.claude/context/STAKEHOLDERS.md)

## Project Structure

- `deliverables/` - Final client-facing documents
- `discovery/` - Discovery materials and notes
- `.brand/` - Brand kit and assets
- `.claude/context/` - Project memory files

## RAG Commands

```bash
# Search project documents
rag search "query" --project-path .

# Index new files
rag index discovery/

# Check status
rag status
```

## CTM Commands

```bash
# Show project tasks
ctm status

# Create new task
ctm spawn "{Client Name}: Task description"
```
```

### Phase 6: Spawn CTM Task

Create initial CTM task for the engagement:

```bash
ctm spawn "{Client Name}: Discovery & Onboarding" --project {client-slug} --switch
```

This creates the task and switches to it automatically.

### Phase 7: Brand Extraction (Optional)

Ask user:
> "Do you have the client's website URL for brand extraction?"

If yes:
```bash
/brand-extract {url}
# Copy results to .brand/ directory
```

If no, skip and inform user they can run `/brand-extract` later.

### Phase 8: Index Initial Files

```bash
# Index memory files
rag_index path=".claude/context/" project_path={project-path}

# Index brand kit if exists
rag_index path=".brand/" project_path={project-path}
```

### Phase 9: Summary

Output completion summary:

```
═══════════════════════════════════════════════════════════
  Client Onboarded: {Client Name}
═══════════════════════════════════════════════════════════

✓ Project Created
  └─ {project-path}

✓ Memory System
  ├─ CLIENT_BRIEF.md
  ├─ DECISIONS.md
  ├─ SESSIONS.md
  └─ STAKEHOLDERS.md

✓ RAG Initialized
  └─ 4 files indexed

✓ CTM Task Created
  └─ "{Client Name}: Discovery & Onboarding" (active)

{if brand extracted}
✓ Brand Kit
  └─ .brand/BRAND_KIT.md
{/if}

───────────────────────────────────────────────────────────
Next Steps:
───────────────────────────────────────────────────────────

1. Review CLIENT_BRIEF.md and fill in details
2. Add stakeholders to STAKEHOLDERS.md
3. Run discovery: /project-discovery
4. Start documenting decisions as they're made

Quick commands:
  • cd {project-path}
  • rag search "test query"
  • ctm status

═══════════════════════════════════════════════════════════
```

## Quick Mode

If `--quick` flag is provided:
- Skip all prompts
- Use defaults for everything
- Don't ask about brand extraction
- Just create the structure silently

## Error Handling

| Scenario | Action |
|----------|--------|
| Project directory exists | Warn and ask to overwrite or use different name |
| Ollama not running | Create structure, warn about RAG, continue |
| CTM not available | Skip task creation, inform user |
| Brand extraction fails | Continue without brand kit |

## Integration Points

After onboarding, the following are automatically available:

1. **RAG searches** will include client context
2. **CTM task** is active for tracking work
3. **Decision tracker** will record to client's DECISIONS.md
4. **HubSpot agents** (if CRM = HubSpot) have client context
5. **CDP workspace** uses client project path

## Chaining

After onboarding, suggest next skills:
- `/project-discovery` - Run full discovery questionnaire
- `/brand-extract {url}` - Extract brand identity
- `/solution-architect` - Start solution design
