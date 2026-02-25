# Agent Routing

## HubSpot Implementation Routing

When user mentions HubSpot implementation, invoke `hubspot-implementation-runbook` orchestrator:

| Context | Route To |
|---------|----------|
| Marketing automation, email, forms | `hubspot-impl-marketing-hub` |
| Pipeline, deals, sequences | `hubspot-impl-sales-hub` |
| Tickets, help desk, SLAs | `hubspot-impl-service-hub` |
| Data sync, Operations Hub | `hubspot-impl-operations-hub` |
| Website, CMS, blogs | `hubspot-impl-content-hub` |
| Quotes, payments | `hubspot-impl-commerce-hub` |
| Discovery, requirements | `hubspot-impl-discovery` |
| Data migration, ETL | `hubspot-impl-data-migration` |
| ERP, QuickBooks integration | `hubspot-impl-integrations` |
| Permissions, GDPR, security | `hubspot-impl-governance` |
| Training, adoption | `hubspot-impl-change-management` |
| Reporting, dashboards | `hubspot-impl-reporting-analytics` |
| Franchise, dealer, B2B2C | `hubspot-impl-b2b2c` |

## HubSpot API Routing

`hubspot-api-specialist` -> `hubspot-api-router` -> 30+ specialized API agents.

## Salesforce-HubSpot Mapping

`salesforce-mapping-router` routes to: `salesforce-mapping-contacts`, `salesforce-mapping-companies`, `salesforce-mapping-deals`, `salesforce-mapping-tickets`, `salesforce-mapping-activities`.

## Proactive Agent Routing

Invoke proactively when situational triggers match:

| Trigger | Route To |
|---------|----------|
| Before sending client-facing deliverable | `deliverable-reviewer` |
| Generated code/specs may have errors | `error-corrector` |
| Need 1-page exec summary | `executive-summary-creator` |
| Decision with 2+ options and trade-offs | `decision-memo-generator` |
| Budget/timeline constraints, 80/20 needed | `80-20-recommender` |
| Multi-phase project sequencing | `playbook-advisor` |
| Process map, workflow, BPMN diagram | `bpmn-specialist` |
| Entity-relationship diagram | `erd-generator` |
| Lucidchart-compatible diagram | `lucidchart-generator` |
| "Have we done this before?" | `comparable-project-finder` |
| Meeting transcript to process | `meeting-indexer` |
| SOW/RFP/proposal creation | `proposal-orchestrator` |
| Brand extraction from site/docs | `brand-kit-extractor` |
| Cross-session memory issues | `memory-management-expert` |
| RAG quality poor, stale data | `rag-integration-expert` |
| Config wrong, capability check | `context-audit-expert` |
| CTM task management | `ctm-expert` |
| Complex multi-session bug | `debugger-agent` |
| "what depends on", impact analysis | `config-oracle` |
| "orphan detection", "unused agents" | `config-oracle` |
| SOW vs delivery delta | `scope-delta-analyzer` |
| Rescued/inherited project | `rescue-project-assessor` |
| Go-live readiness check | `completeness-auditor` |
| "audit workflows", inherited portal | `workflow-auditor` |
| Slack decisions into CTM | `slack-ctm-sync` |
| Bulk code analysis (>20 files) | `codex-delegate` |
| Bulk summarization, >1M content | `gemini-delegate` |
| Architecture decision, 2+ failures | `reasoning-duo` |
| Research + long-context (2M) | `reasoning-duo-cg` |
| High-stakes 3-model consensus | `reasoning-trio` |

## Organization Wiki Routing

When user asks about internal processes/methodology:

| Context | Route To |
|---------|----------|
| Implementation methodology, BPM, badges | `huble-methodology` |
| Battlecards, quoting, sales | `huble-sales` |
| TLO, expenses, compliance | `huble-operations` |
| Employee guides, HR, leave | `huble-employee-guide` |
| HubSpot product updates | `huble-hubspot-updates` |
| Dev SDLC, QA, email dev | `huble-dev` |

Set `ORG_WIKI_PATH` to enable. Skip if not applicable.

## Configuration Audit Routing

| Context | Route To |
|---------|----------|
| "audit config", "check setup" | `context-audit-expert` |
| "list capabilities" | `generate-capability-manifest.sh` |
| "CLAUDE.md best practices" | `claude-md-expert` |
| "dependency map", "what references X" | `config-oracle` |
| "orphan scan", "what breaks if" | `config-oracle` |
