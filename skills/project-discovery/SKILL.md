---
name: project-discovery
description: Structured project discovery and requirements assessment framework for implementation projects. Use when conducting discovery sessions, gathering project requirements, creating assessment questionnaires, validating sales assumptions, preparing for implementation kickoffs, or reviewing prospect scopes before contract signature. Applicable to CRM implementations (HubSpot, Salesforce, Zoho), system integrations, digital transformations, platform migrations, and any technical implementation project requiring structured requirements gathering. Triggers include requests to "assess a project," "validate scope," "review requirements," "create discovery questions," or "analyze prospect data."
async:
  mode: never
  require_sync:
    - discovery sessions
    - requirements gathering
    - stakeholder interviews
---

# Project Discovery Skill

A framework for conducting rigorous technical discovery and requirements validation on implementation projects.

## Core Philosophy

**Be the expert, not the order-taker.** Challenge requirements. Question assumptions. Validate with data.

The goal is NOT to rubber-stamp sales assumptions. The goal is to:
1. Identify hidden complexity before contract
2. Validate that proposed solutions will work
3. Protect delivery margin by scoping accurately
4. Help clients get what they need (not what they think they want)

> "Separate facts from interpretation."
> - **Fact:** "The module has 61 properties including a Formula field"
> - **Interpretation:** "It's simple, same as the other one"

Always verify. Never assume. Challenge everything.

## The 5-Phase Discovery Process

### Phase 1: Question the Project's Existence

Before analyzing details, establish fundamentals:

| Question | Why It Matters |
|----------|----------------|
| Why are they doing this? | Understand true motivation vs. stated requirement |
| What's broken today? | Identify actual pain points |
| What happens if they do nothing? | Quantify cost of inaction |
| Is the timeline real or artificial? | Test flexibility |
| What does success look like? | Define measurable outcome |

### Phase 2: Analyze Raw Data Independently

**Never trust summaries.** Go to the source data and examine:

- Actual field/property definitions (types, not descriptions)
- Relationships (lookups, multi-selects = complexity)
- Record volumes (sizing implications)
- Formulas and calculated fields (must be rebuilt)
- Auto-numbers and linking modules (often legacy workarounds)

For each component, ask: What does this ACTUALLY contain? How complex is it really? Is it used or legacy? Can it be simplified?

### Phase 3: Challenge Every Assumption

For each "requirement," apply the Challenger Framework:

1. **"Why do they think they need this?"** — Legacy habit? Fear-based? Over-engineering? Political?
2. **"What decision does this enable?"** — If no decision, it's noise
3. **"What breaks if we don't include this?"** — If nothing, it's not essential

See `references/challenger-questions.md` for complete question library.

### Phase 4: Identify and Categorize Risks

| Category | Definition | Action |
|----------|------------|--------|
| 🔴 Critical | Must resolve before contract | Blocker |
| 🟡 Medium | Should resolve before contract | Risk mitigation |
| 🟢 Low | Note for implementation | Documentation |

For each risk, document: what was assumed vs. what might be true, price impact if wrong, question that resolves it.

### Phase 5: Produce Deliverables

Generate three outputs:
1. **Technical Analysis** — Module-by-module findings, gaps, dependencies
2. **Executive Brief** — Plain English for sales, no jargon
3. **Risk Register** — Structured risk documentation

See `references/deliverable-templates.md` for formats.

## Discovery Modules

Select modules based on project scope. Use `references/question-framework.md` for detailed questions per module.

### Core Modules (Always Include)

| Module | Key Areas |
|--------|-----------|
| Scope & Context | Project triggers, goals, timeline, divisions, compliance |
| Project Management | Governance, meetings, tools, budget |
| Systems Inventory | Current state, planned systems, data volumes |
| Integration Architecture | Middleware, iPaaS, data flows, sync patterns |
| Testing & Signoff | UAT approach, sandbox requirements |
| Documentation | Deliverables and detail levels |

### Functional Modules (Include Based on Scope)

| Module | When to Include |
|--------|-----------------|
| Marketing | Marketing automation, campaigns, lead management |
| Sales | CRM, pipeline, quoting, forecasting |
| Service | Support, ticketing, knowledge base |
| Operations | Data quality, automation, platform governance |

## Key Red Flags

### In Data Structures
- 50+ properties per object (bloat)
- Formula fields (can't migrate, must rebuild)
- Auto-number fields (usually workarounds)
- Multi-module lookups (complex dependencies)
- History/audit modules (massive, rarely essential)
- "Linking" modules (junction tables native in HubSpot)

### In Sales Materials
- "TBD" items without resolution plan
- "Same as X" without validation
- Options without recommendations
- Missing dependency mapping

### In Client Conversations
- "We need all our data" (probably don't)
- "We've always done it this way" (not a reason)
- "Just in case" (fear-based)
- "Work exactly like before" (migration, not improvement)

## Budget Validation Framework

Always calculate three scenarios:

| Scenario | Assumption | Typical Variance |
|----------|------------|------------------|
| Optimistic | All simplifications accepted | Base price |
| Probable | Some complexity confirmed | +15-25% |
| Pessimistic | Full complexity materialized | +40-60% |

If sales quote only works in optimistic scenario, flag it.

## Reference Files

| File | Purpose |
|------|---------|
| `references/challenger-questions.md` | Strategic questions: Existence, Scope, Reality, Module-specific |
| `references/question-framework.md` | Comprehensive question bank organized by discovery module |
| `references/deliverable-templates.md` | Technical Analysis, Executive Brief, Risk Register, SOW templates |
| `references/output-templates.md` | Discovery Summary, Requirements Matrix, Integration Blueprint templates |

## Adaptive Questioning

- Start broad, then drill into specifics based on responses
- Probe on "widget" responses (complex data that may need breakdown)
- When answers reference external docs/tools, note for follow-up
- Flag gaps or inconsistencies for clarification

| Type | Use For |
|------|---------|
| Open-ended | Goals, processes, pain points, current state |
| Structured choices | Preferences, priorities, known options |
| Quantitative | Volumes, counts, timelines, budgets |
| Confirmatory | Validating assumptions, summarizing decisions |

## Specialized Discovery Patterns

**Migration Projects**: Emphasize current state documentation, data volume analysis, historical data requirements, cutover planning.

**Integration Projects**: Emphasize API capabilities, sync patterns (real-time vs batch), conflict resolution, error handling.

**Greenfield Implementations**: Emphasize process design, best practices, change management, adoption planning.

**Multi-Region/BU Projects**: Emphasize variations by region/BU, shared vs. unique requirements, governance model.

---

## Discovery Session Facilitation

### Opening the Session (5 minutes)
- Set expectations: "This will feel like 20 questions - we're stress-testing assumptions"
- Explain outcome: "By the end, we'll have a risk register and accurate scope"
- Get permission to challenge: "I'll push back on 'requirements' - it's my job to find gaps"

### During the Session (45 minutes)
- Use open-ended questions first: "Walk me through how you handle X today"
- Then drill into specifics: "You mentioned 61 properties - are these all actively used?"
- Challenge with data: "Formula fields can't migrate - what's your plan for rebuilding?"
- Separate facts from interpretation: "The module has 61 properties (fact). It's simple (interpretation - let's verify)"

### Closing the Session (10 minutes)
- Summarize discoveries: "We found 3 critical gaps: [X, Y, Z]"
- Clarify next steps: "I'll send you 10 follow-up questions by EOD"
- Set expectations: "Budget estimate will shift - I'll show you 3 scenarios"

### After the Session
- Document within 24 hours while fresh
- Send clarifying questions immediately
- Flag urgent blockers to sales/PM within 4 hours

---

## Post-Discovery Decision Matrix

| Risk Level | Budget Variance | Recommendation |
|-----------|----------------|----------------|
| 🔴 Critical risks | Any variance | STOP - Resolve blockers before proceeding |
| 🟡 Medium risks | < 15% increase | PROCEED - Mitigate during design phase |
| 🟡 Medium risks | 15-30% increase | NEGOTIATE - Present options to client |
| 🟡 Medium risks | > 30% increase | RE-SCOPE - Original scope not viable |
| 🟢 Low risks | < 15% increase | PROCEED - Minor adjustments only |
| 🟢 Low risks | > 15% increase | INVESTIGATE - Risk assessment may be incomplete |

For each decision:
- Document rationale in Executive Brief
- Update sales/PM within 24 hours
- Provide revised budget estimates with 3 scenarios
