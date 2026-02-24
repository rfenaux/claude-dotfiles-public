# HubSpot Implementation Runbook Guide

> Comprehensive guide to the 15-agent HubSpot Implementation suite.
> Created: 2026-01-09

---

## Overview

The HubSpot Implementation Runbook is a **modular agent system** for planning and executing HubSpot implementations. It covers all 6 Hubs, implementation phases, and specialized use cases like B2B2C and subscriptions.

```
┌─────────────────────────────────────────────────────────────────────┐
│              HUBSPOT IMPLEMENTATION RUNBOOK SUITE                    │
│                                                                     │
│  Master orchestrator + 14 specialized sub-agents                    │
│  Coverage: All Hubs × All Phases × Specialized Scenarios            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Architecture

```
                    ┌─────────────────────────────┐
                    │ hubspot-implementation-     │
                    │ runbook                     │
                    │ (Orchestrator)              │
                    └──────────────┬──────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
        ▼                          ▼                          ▼
┌───────────────────┐    ┌───────────────────┐    ┌───────────────────┐
│   HUB AGENTS      │    │   PHASE AGENTS    │    │   SPECIALISTS     │
│                   │    │                   │    │                   │
│ • marketing-hub   │    │ • discovery       │    │ • b2b2c           │
│ • sales-hub       │    │ • data-migration  │    │ • customer-portal │
│ • service-hub     │    │ • integrations    │    │ • subscriptions   │
│ • operations-hub  │    │ • governance      │    │                   │
│ • content-hub     │    │ • change-mgmt     │    │                   │
│ • commerce-hub    │    │                   │    │                   │
└───────────────────┘    └───────────────────┘    └───────────────────┘
```

---

## Agent Catalog

### Master Orchestrator

| Agent | Purpose |
|-------|---------|
| `hubspot-implementation-runbook` | Routes to sub-agents, provides methodology overview, coordinates multi-agent tasks |

### Hub-Specific Agents

| Agent | Scope |
|-------|-------|
| `hubspot-impl-marketing-hub` | Email, automation, forms, campaigns, ABM, lead scoring, attribution |
| `hubspot-impl-sales-hub` | Pipelines, deals, sequences, forecasting, playbooks, quotes |
| `hubspot-impl-service-hub` | Tickets, help desk, KB, customer portal, SLAs, feedback surveys |
| `hubspot-impl-operations-hub` | Data sync, programmable automation, custom code, data quality |
| `hubspot-impl-content-hub` | CMS, website pages, blogs, landing pages, SEO, multi-language |
| `hubspot-impl-commerce-hub` | Quotes, payments, invoices, products, payment links |

### Phase Agents

| Agent | Scope |
|-------|-------|
| `hubspot-impl-discovery` | Stakeholder mapping, requirements, current state assessment, risk register |
| `hubspot-impl-data-migration` | ETL design, field mapping, data quality, migration execution |
| `hubspot-impl-integrations` | ERP (NetSuite, SAP), accounting (QuickBooks), payments, iPaaS |
| `hubspot-impl-governance` | Permissions, teams, SSO, GDPR, data retention, audit |
| `hubspot-impl-change-management` | Training programs, adoption strategy, communication, rollout |

### Specialized Agents

| Agent | Scope |
|-------|-------|
| `hubspot-impl-b2b2c` | Franchises, dealer networks, multi-portal, partner management |
| `hubspot-impl-customer-portal` | Self-service portal, ticket visibility, KB integration, SSO |
| `hubspot-impl-subscriptions` | Recurring revenue, billing, dunning, churn management |

---

## When to Use Which Agent

### Decision Tree

```
What's your need?
│
├─ "Full implementation planning"
│   └─ Start with: hubspot-implementation-runbook (orchestrator)
│
├─ "Configure specific Hub"
│   ├─ Marketing automation → hubspot-impl-marketing-hub
│   ├─ Sales pipeline → hubspot-impl-sales-hub
│   ├─ Support/tickets → hubspot-impl-service-hub
│   ├─ Data sync/ops → hubspot-impl-operations-hub
│   ├─ Website/CMS → hubspot-impl-content-hub
│   └─ Payments/quotes → hubspot-impl-commerce-hub
│
├─ "Implementation phase guidance"
│   ├─ Starting project → hubspot-impl-discovery
│   ├─ Moving data → hubspot-impl-data-migration
│   ├─ Connecting systems → hubspot-impl-integrations
│   ├─ Security/compliance → hubspot-impl-governance
│   └─ User adoption → hubspot-impl-change-management
│
└─ "Specialized scenario"
    ├─ Franchise/dealer → hubspot-impl-b2b2c
    ├─ Customer self-service → hubspot-impl-customer-portal
    └─ Subscription business → hubspot-impl-subscriptions
```

### Common Scenarios

| Scenario | Agent(s) to Use |
|----------|-----------------|
| "Implement HubSpot for a SaaS company" | orchestrator → sales-hub + marketing-hub + subscriptions |
| "Set up franchise CRM" | b2b2c + governance |
| "Migrate from Salesforce" | data-migration + integrations |
| "Build customer support portal" | service-hub + customer-portal |
| "Configure lead scoring" | marketing-hub |
| "Set up QuickBooks integration" | integrations |
| "Plan user training" | change-management |
| "Design deal pipeline" | sales-hub |
| "GDPR compliance setup" | governance |

---

## How to Invoke

### Method 1: Direct Read (Recommended for focused tasks)

Ask me to read and apply a specific agent:

```
"Read the hubspot-impl-sales-hub agent and help me design a B2B pipeline"

"Follow the hubspot-impl-discovery methodology for our new project"

"Use the hubspot-impl-data-migration agent to plan our Salesforce migration"
```

### Method 2: Via Orchestrator (For broad implementation questions)

Start with the orchestrator for routing:

```
"Help me implement HubSpot for a franchise business"
→ I'll read orchestrator, then route to b2b2c + governance + relevant hubs

"What's the full implementation methodology?"
→ I'll provide phase overview from orchestrator
```

### Method 3: Via Task Tool (For background/parallel work)

```
Task: subagent_type=worker
Prompt: "Read ~/.claude/agents/hubspot-impl-discovery.md and
        generate a discovery questionnaire for [client name]"
```

### Method 4: Via CTM Delegation

```bash
ctm delegate "Create implementation plan for SaaS company" \
  --context "Read hubspot-implementation-runbook and relevant sub-agents"
```

---

## Integration with Existing Tools

### Relationship to `hubspot-specialist`

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| `hubspot-specialist` | Platform knowledge, API, features, pricing | "Can HubSpot do X?", API questions, tier requirements |
| `hubspot-implementation-runbook` | Implementation methodology | "How do I implement X?", project planning |

**They complement each other:**
- Implementation agents reference `hubspot-specialist` for API/feature details
- `hubspot-specialist` handles capability questions
- Runbook agents handle "how to configure/deploy" questions

### Integration with Other Agents

| Agent | Handoff Scenario |
|-------|------------------|
| `erd-generator` | Data model design for custom objects |
| `bpmn-specialist` | Process mapping for workflows |
| `solution-spec-writer` | Full specification documents |
| `functional-spec-generator` | Functional specifications |
| `discovery-questionnaire-generator` | Discovery workshop questions |
| `training-creator` | User training materials |
| `migration-planner` | General migration methodology |

### RAG Integration

If project has `.rag/` directory:
```
1. Search RAG first for project-specific context
2. Apply agent methodology to project specifics
3. Reference existing decisions/requirements
```

### CTM Integration

```bash
# Spawn as task
ctm spawn "HubSpot Marketing Hub Implementation" --switch

# Add context as you work
ctm context add --decision "Using lead scoring model from agent template"

# Checkpoint progress
ctm checkpoint
```

---

## Agent Content Summary

Each agent contains:

| Section | Description |
|---------|-------------|
| **Scope** | What the agent covers |
| **Tier Feature Matrix** | Feature availability by HubSpot tier |
| **Implementation Checklist** | Phased checklist (Week 1, Week 2, etc.) |
| **Configuration Templates** | Property definitions, workflow logic, pipeline designs |
| **ASCII Diagrams** | Architecture, data flows, process maps |
| **Best Practices** | Recommendations and patterns |
| **Troubleshooting Guide** | Common issues and solutions |
| **Handoff References** | When to delegate to other agents |

---

## Quick Reference Card

### Trigger Phrases

| Say This | Gets You |
|----------|----------|
| "HubSpot implementation" | Orchestrator overview |
| "implement Marketing Hub" | Marketing-specific guidance |
| "set up pipelines" | Sales Hub agent |
| "configure tickets/support" | Service Hub agent |
| "data sync setup" | Operations Hub agent |
| "website/CMS" | Content Hub agent |
| "payments/quotes" | Commerce Hub agent |
| "project discovery" | Discovery phase agent |
| "migrate data" | Data migration agent |
| "ERP/QuickBooks integration" | Integrations agent |
| "permissions/GDPR" | Governance agent |
| "training/adoption" | Change management agent |
| "franchise/dealer" | B2B2C agent |
| "customer portal" | Portal agent |
| "subscriptions/recurring" | Subscriptions agent |

### File Locations

```
~/.claude/agents/
├── hubspot-implementation-runbook.md    # Orchestrator
├── hubspot-impl-marketing-hub.md
├── hubspot-impl-sales-hub.md
├── hubspot-impl-service-hub.md
├── hubspot-impl-operations-hub.md
├── hubspot-impl-content-hub.md
├── hubspot-impl-commerce-hub.md
├── hubspot-impl-discovery.md
├── hubspot-impl-data-migration.md
├── hubspot-impl-integrations.md
├── hubspot-impl-governance.md
├── hubspot-impl-change-management.md
├── hubspot-impl-b2b2c.md
├── hubspot-impl-customer-portal.md
└── hubspot-impl-subscriptions.md
```

---

## Coverage Matrix

### By Hub

| Hub | Agent | Key Topics |
|-----|-------|------------|
| Marketing | `hubspot-impl-marketing-hub` | Email, automation, forms, ABM, attribution |
| Sales | `hubspot-impl-sales-hub` | Pipelines, sequences, forecasting, quotes |
| Service | `hubspot-impl-service-hub` | Tickets, KB, portal, SLAs, CSAT/NPS |
| Operations | `hubspot-impl-operations-hub` | Data sync, custom code, data quality |
| Content | `hubspot-impl-content-hub` | CMS, blogs, landing pages, SEO |
| Commerce | `hubspot-impl-commerce-hub` | Quotes, payments, subscriptions |

### By Implementation Phase

| Phase | Agent | Deliverables |
|-------|-------|--------------|
| Discovery | `hubspot-impl-discovery` | Stakeholder map, requirements, risk register |
| Design | Hub agents | ERD, BPMN, solution architecture |
| Build | Hub agents | Configurations, workflows, integrations |
| Test | `hubspot-impl-governance` | UAT, security review, permissions |
| Launch | `hubspot-impl-change-management` | Training, rollout, communications |
| Optimize | All | Adoption metrics, continuous improvement |

### By Use Case

| Use Case | Primary Agent(s) |
|----------|------------------|
| B2B SaaS | sales-hub, marketing-hub, subscriptions |
| B2C E-commerce | commerce-hub, marketing-hub, service-hub |
| Franchise | b2b2c, governance, service-hub |
| Professional Services | sales-hub, service-hub, operations-hub |
| Manufacturing/Distribution | b2b2c, integrations, operations-hub |

---

## Examples

### Example 1: SaaS Implementation

```
User: "Help me implement HubSpot for our B2B SaaS startup"

Claude reads:
1. hubspot-implementation-runbook (methodology)
2. hubspot-impl-sales-hub (pipeline, sequences)
3. hubspot-impl-marketing-hub (lead scoring, nurturing)
4. hubspot-impl-subscriptions (recurring billing)

Output: Phased implementation plan with specific configurations
```

### Example 2: Franchise Network

```
User: "We're a franchise with 50 locations, how should we set up HubSpot?"

Claude reads:
1. hubspot-impl-b2b2c (multi-portal architecture)
2. hubspot-impl-governance (permissions, partitioning)
3. hubspot-impl-marketing-hub (centralized campaigns)

Output: Hub & Spoke architecture recommendation with implementation steps
```

### Example 3: Data Migration

```
User: "We need to migrate from Dynamics 365 to HubSpot"

Claude reads:
1. hubspot-impl-data-migration (ETL methodology)
2. hubspot-impl-integrations (Dynamics connector options)

Output: Migration plan with field mapping, validation, rollback strategy
```

---

## Maintenance

### Updating Agents

When HubSpot releases new features:
1. Update relevant Hub agent(s)
2. Update tier matrices if pricing changes
3. Add new workflow templates as needed
4. Update this guide if new agents added

### Adding Project-Specific Customizations

For client projects, consider:
1. Creating project-specific risk agent (`risk-analyst-[CLIENT]`)
2. Adding client context to RAG
3. Recording decisions in CTM

---

## Related Documentation

| Document | Location |
|----------|----------|
| Agent Standards | `~/.claude/AGENT_STANDARDS.md` |
| Agents Index | `~/.claude/AGENTS_INDEX.md` |
| HubSpot Specialist Skill | `~/.claude/skills/hubspot-specialist/` |
| CTM Guide | `~/.claude/CTM_GUIDE.md` |
| RAG Guide | `~/.claude/RAG_GUIDE.md` |

---

*Last Updated: 2026-01-09*
*Suite Version: 1.0*
*Total Agents: 15*
