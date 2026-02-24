---
name: pm-spec
description: Interactive specification creation for features, implementations, or integrations. Guided brainstorming producing structured specs with requirements + technical approach.
async:
  mode: never
  require_sync:
    - interactive brainstorming
    - user decisions on scope
    - architecture choices
context: fork
---

# PM-Spec - Interactive Specification Generator

Creates structured specification documents through guided brainstorming. Integrates with CTM task management and provides foundation for task decomposition.

## Trigger

Invoke this skill when:
- User says "/pm-spec", "create a spec", "spec out", "scope this"
- User wants to formalize requirements for a feature, integration, or implementation
- Starting a new project phase that needs documentation
- Converting informal requirements into structured specs

## Description

PM-Spec generates structured specification documents through interactive Q&A. Detects context from project files, loads appropriate templates, and guides users through defining scope, requirements, technical approach, and acceptance criteria.

### Key Features
- **Context Detection**: Infers spec type from project structure (package.json → dev, hubspot.config.yaml → hubspot)
- **Three Spec Types**: dev-feature, hubspot-impl, integration
- **Interactive Brainstorming**: 5-8 focused questions to extract requirements
- **CTM Integration**: Optional task creation with link to spec
- **Template-Driven**: Consistent format across all specs

## Commands

```bash
# Interactive Mode
/pm-spec                                    # Ask for name + type
/pm-spec {name}                             # Create spec with given name (auto-detect type)
/pm-spec {name} --type dev|hubspot|integration  # Typed spec creation

# Management
/pm-spec --list                             # List existing specs
/pm-spec --show {name}                      # Display spec content
/pm-spec --edit {name}                      # Open spec for editing
```

## Workflow

1. **Detect Context** - Scan project files to infer spec type
   - `package.json`, `*.ts`, `*.js` → dev
   - `hubspot.config.yaml`, `hs-*` → hubspot
   - `integration*`, `sync-*` → integration

2. **Load Template** - From `~/.claude/templates/specs/{type}.md`

3. **Interactive Brainstorming** - 5-8 questions:
   - What problem does this solve?
   - Who are the users/stakeholders?
   - What are the key requirements?
   - What's the technical approach?
   - What are the acceptance criteria?
   - What's explicitly out of scope?
   - What are the risks/dependencies?

4. **Write Spec** - Save to:
   - `project/.claude/specs/{name}.md` if in a project
   - `~/.claude/specs/{name}.md` if global

5. **Record Decisions** - Offer to log architecture decisions to DECISIONS.md

6. **Create CTM Task** (optional) - Ask: "Create CTM task for implementing this spec?"
   - If yes: `ctm spawn "Implement {name}" --switch false`
   - Update spec frontmatter with `ctm_task: {task-id}`

7. **Chain** - Suggest next step: `/pm-decompose {name}`

## Spec File Format

```markdown
---
spec_id: {name}
type: dev|hubspot|integration
status: draft|approved|in-progress|completed
created: {ISO datetime}
updated: {ISO datetime}
ctm_task: {task-id or null}
---

# Spec: {Title}

## Problem Statement
<!-- What problem does this solve? Who is affected? -->

## User Stories / Requirements
<!-- As a [role], I want [feature], so that [benefit] -->

## Technical Approach
<!-- High-level architecture, key components -->

## Architecture Decisions
<!-- Key choices: libraries, patterns, trade-offs -->

## Implementation Phases
### Phase 1: MVP
### Phase 2: Enhancement
### Future

## Dependencies & Risks
<!-- External deps, potential blockers -->

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Out of Scope
<!-- Explicitly excluded -->
```

## Integration with Project Memory

PM-Spec integrates with project memory:
- **DECISIONS.md**: Architecture decisions from spec are recorded
- **CTM**: Specs link to tasks, tasks link back to specs
- **RAG**: Specs are indexed for semantic search

## Best Practices

1. **Start early** - Spec before coding to clarify requirements
2. **Be specific** - Vague specs lead to scope creep
3. **Define out-of-scope** - Explicit boundaries prevent drift
4. **Phase the work** - Always MVP → Phase 2 → Future
5. **Link to CTM** - Track implementation progress

## Files

| Path | Purpose |
|------|---------|
| `project/.claude/specs/{name}.md` | Project-specific specs |
| `~/.claude/specs/{name}.md` | Global specs |
| `~/.claude/templates/specs/dev-feature.md` | Dev template |
| `~/.claude/templates/specs/hubspot-impl.md` | HubSpot template |
| `~/.claude/templates/specs/integration.md` | Integration template |

## Example Workflow

```bash
# User starts new feature
/pm-spec user-authentication --type dev

# Interactive Q&A
# Q: What problem does this solve?
# A: Users need secure login...

# Q: What are the key requirements?
# A: Email/password login, JWT tokens, password reset...

# Spec created: project/.claude/specs/user-authentication.md
# CTM task created: task-abc123
# Suggested: /pm-decompose user-authentication
```
