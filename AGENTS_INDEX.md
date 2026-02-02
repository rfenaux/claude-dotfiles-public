# Claude Code Agents Index

Master catalog of **125 specialized agents** available at `~/.claude/agents/`.

> Total Agents: 125 | Auto-generated: 2026-01-27 | Regenerate: `~/.claude/scripts/generate-inventory.sh`

---

## Quick Reference by Task

| Need | Agent(s) |
|------|----------|
| ERD / Data Model | `erd-generator` |
| BPMN / Process Flow | `bpmn-specialist`, `lucidchart-generator` |
| Architecture Diagram | `system-architecture-visualizer` |
| Presentation | `slide-deck-creator`, `board-presentation-designer`, `pitch-deck-optimizer` |
| Specification | `solution-spec-writer`, `fsd-generator`, `technical-brief-compiler` |
| Executive Summary | `executive-summary-creator` |
| Risk Assessment | `risk-analyst-[PROJECT]`, `<REMOVED>` |
| ROI / Commercial | `commercial-analyst-[PROJECT]`, `roi-calculator` |
| Discovery | `discovery-questionnaire-generator`, `discovery-audit-analyzer` |
| Health Check | `technology-auditor` |
| Quick Wins | `80-20-recommender` |
| Process PDF | `pdf-processor-unlimited` |
| HubSpot Platform | `hubspot-specialist` |
| HubSpot API (general) | `hubspot-api-specialist` |
| HubSpot API (domain) | `hubspot-api-router` → 14 domain agents |
| HubSpot Config | `hubspot-config-specialist` |
| CRM Cards / UI Extensions | `hubspot-crm-card-specialist` |
| HubSpot Implementation | `hubspot-implementation-runbook` → 14 sub-agents |
| Integration Code | `integration-code-writer` |
| Field Mapping | `property-mapping-builder` |
| Salesforce-HubSpot Mapping | `salesforce-mapping-contacts`, `salesforce-mapping-companies`, `salesforce-mapping-deals`, `salesforce-mapping-tickets` |
| Migration | `migration-planner` |
| UAT / Testing | `uat-sales-hub`, `uat-service-hub`, `uat-integration`, `uat-migration` |
| Token Optimization | `codex-delegate`, `gemini-delegate` |
| Multi-Model Reasoning | `reasoning-duo`, `reasoning-duo-cg`, `reasoning-trio` |
| RAG Setup | `rag-integration-expert` |
| Knowledge Base | `kb-query-agent`, `kb-synthesizer` |
| Meeting Processing | `meeting-indexer` |
| Task Management | `ctm-expert` |
| Agent Creation | `agent-creation-expert`, `skill-creation-expert` |
| Generic Delegation | `worker` |

---

## HUBSPOT SPECIALISTS (34 agents)

### Platform & Configuration (4 agents)

| Agent | Model | Async | Description |
|-------|-------|-------|-------------|
| `hubspot-specialist` | sonnet | auto | Platform expertise, features, pricing, "Can HubSpot do X?" |
| `hubspot-config-specialist` | sonnet | auto | Config specs (custom objects, workflows, properties) |
| `hubspot-crm-card-specialist` | sonnet | auto | CRM cards, UI Extensions, serverless functions |
| `hubspot-api-specialist` | sonnet | auto | General API patterns: SDK, CLI, auth, pagination, rate limits |

### API Domain Specialists (15 agents) — OpenAPI-backed

| Agent | Model | Domain |
|-------|-------|--------|
| `hubspot-api-router` | sonnet | Routes requests to correct domain agent |
| `hubspot-api-crm` | sonnet | Contacts, deals, companies, tickets, associations (60 specs) |
| `hubspot-api-cms` | sonnet | Pages, blogs, HubDB, templates (10 specs) |
| `hubspot-api-marketing` | sonnet | Forms, emails, campaigns (5 specs) |
| `hubspot-api-automation` | sonnet | Workflows, sequences - v4 API (3 specs) |
| `hubspot-api-conversations` | sonnet | Chat, visitor ID, custom channels |
| `hubspot-api-events` | haiku | Behavioral events |
| `hubspot-api-files` | haiku | File uploads, management |
| `hubspot-api-webhooks` | haiku | Webhook subscriptions |
| `hubspot-api-auth` | haiku | OAuth flows |
| `hubspot-api-account` | haiku | Audit logs, account info |
| `hubspot-api-settings` | haiku | User provisioning, multicurrency |
| `hubspot-api-business-units` | haiku | Multi-brand management |
| `hubspot-api-communication-preferences` | haiku | Opt-outs, subscriptions |
| `hubspot-api-scheduler` | haiku | Meeting scheduling |

### Implementation Specialists (15 agents)

| Agent | Model | Async | Description |
|-------|-------|-------|-------------|
| `hubspot-implementation-runbook` | sonnet | auto | Master orchestrator for implementations |
| `hubspot-impl-discovery` | sonnet | auto | Discovery phase, stakeholder mapping |
| `hubspot-impl-marketing-hub` | sonnet | auto | Email, automation, forms, campaigns |
| `hubspot-impl-sales-hub` | sonnet | auto | Pipelines, deals, sequences, forecasting |
| `hubspot-impl-service-hub` | sonnet | auto | Tickets, help desk, knowledge base, SLAs |
| `hubspot-impl-operations-hub` | sonnet | auto | Data sync, programmable automation |
| `hubspot-impl-content-hub` | sonnet | auto | CMS, website pages, blogs, SEO |
| `hubspot-impl-commerce-hub` | sonnet | auto | Quotes, payments, subscriptions |
| `hubspot-impl-data-migration` | sonnet | auto | Legacy assessment, ETL, data mapping |
| `hubspot-impl-integrations` | sonnet | auto | ERP, accounting, payment gateways |
| `hubspot-impl-governance` | sonnet | auto | Permissions, GDPR, security, audit |
| `hubspot-impl-change-management` | sonnet | auto | Training, adoption, communication |
| `hubspot-impl-b2b2c` | sonnet | auto | Franchise, dealer, distributor models |
| `hubspot-impl-customer-portal` | sonnet | auto | Self-service portals, authentication |
| `hubspot-impl-subscriptions` | sonnet | auto | Recurring revenue, billing, dunning |

---

## SALESFORCE-HUBSPOT MAPPING (5 agents)

Specialized agents for data mapping between HubSpot and Salesforce via the HubSpot Salesforce Connector app.

| Agent | Model | Async | Description |
|-------|-------|-------|-------------|
| `salesforce-mapping-router` | haiku | never | **Orchestrator** - Routes to correct mapping specialist by object type |
| `salesforce-mapping-contacts` | sonnet | auto | Contact ↔ Contact/Lead mapping, includes Person Account handling |
| `salesforce-mapping-companies` | sonnet | auto | Account ↔ Company mapping, Person Accounts, parent-child hierarchy |
| `salesforce-mapping-deals` | sonnet | auto | Opportunity ↔ Deal mapping, pipeline/stage sync, line items |
| `salesforce-mapping-tickets` | sonnet | auto | Case ↔ Ticket mapping, SLA alignment, status/priority mapping |

**Embedded Knowledge:**
- HubSpot native properties for each object
- Salesforce standard fields for each object
- HubSpot Salesforce Connector sync rules and limitations
- Field type compatibility matrices
- SSOT designation recommendations

---

## DIAGRAMS & VISUALIZATION (7 agents)

| Agent | Model | Async | Description |
|-------|-------|-------|-------------|
| `erd-generator` | sonnet | never | Entity-Relationship Diagrams for CRM |
| `bpmn-specialist` | sonnet | never | Business Process Mapping for Lucidchart |
| `lucidchart-generator` | sonnet | never | Production-quality Lucidchart via API |
| `system-architecture-visualizer` | sonnet | auto | Integration and architecture diagrams |
| `gantt-builder` | sonnet | auto | Project timelines with dependencies |
| `mermaid-converter` | haiku | always | Mermaid to Lucidchart/HTML/code |
| `raci-builder` | sonnet | always | RACI matrices for governance |

---

## PRESENTATIONS (3 agents)

| Agent | Model | Async | Description |
|-------|-------|-------|-------------|
| `slide-deck-creator` | sonnet | never | Professional presentations |
| `board-presentation-designer` | sonnet | never | 10-15 slide executive presentations |
| `pitch-deck-optimizer` | sonnet | never | Executive-optimized decks |

---

## DOCUMENTATION & SPECS (11 agents)

| Agent | Model | Async | Description |
|-------|-------|-------|-------------|
| `solution-spec-writer` | **opus** | never | 15-20 page solution architecture |
| `fsd-generator` | sonnet | never | Functional Specification Documents |
| `functional-spec-generator` | sonnet | never | Detailed solution design docs |
| `technical-brief-compiler` | sonnet | auto | 8-12 page developer handover |
| `executive-summary-creator` | sonnet | auto | 1-page business-focused summaries |
| `api-documentation-generator` | sonnet | auto | API docs with endpoints & examples |
| `training-creator` | sonnet | auto | Admin guides, user guides, video scripts |
| `handover-packager` | sonnet | auto | Comprehensive handover bundles |
| `document-merger` | sonnet | auto | Merges versions, handles continuation |
| `<REMOVED>` | haiku | always | <PROJECT> 70+ file corpus navigation |
| `status-reporter` | haiku | always | Weekly/bi-weekly status reports |

---

## DISCOVERY & ANALYSIS (9 agents)

| Agent | Model | Async | Description |
|-------|-------|-------|-------------|
| `discovery-questionnaire-generator` | sonnet | never | 25+ question discovery questionnaires |
| `discovery-audit-analyzer` | sonnet | auto | Discovery completeness, Go/No-Go |
| `technology-auditor` | **opus** | always | Tech stack assessment, capability gaps |
| `options-analyzer` | **opus** | never | 2-3 alternative comparison matrices |
| `decision-memo-generator` | **opus** | never | Structured decision memos |
| `80-20-recommender` | sonnet | auto | Lite vs Full solution paths |
| `mvp-scoper` | sonnet | auto | MVP boundaries, phased plans |
| `testing-designer` | sonnet | auto | Test scenarios, acceptance criteria |
| `rfa-framework-validator` | sonnet | auto | RFA × RF-Δ methodology validation |

---

## COMMERCIAL & ROI (5 agents)

| Agent | Model | Async | Description |
|-------|-------|-------|-------------|
| `roi-calculator` | sonnet | auto | ROI models, cost-of-doing-nothing |
| `commercial-analyst-[PROJECT]` | sonnet | auto | Project-specific commercial analysis |
| `<REMOVED>` | sonnet | auto | <PROJECT> £2.2-2.8M ROI modeling |
| `sales-enabler` | sonnet | auto | Pre-sales docs, gap analysis, POC specs |
| `<REMOVED>` | sonnet | auto | EU/Asia/MEA/LATAM CRM comparison |

---

## RISK & QA (5 agents)

| Agent | Model | Async | Description |
|-------|-------|-------|-------------|
| `risk-analyst-[PROJECT]` | sonnet | auto | P0/P1/P2/P3 risk framework |
| `<REMOVED>` | sonnet | auto | <PROJECT> 27-risk register |
| `deliverable-reviewer` | sonnet | auto | QA against knowledge base |
| `error-corrector` | sonnet | always | Fixes mistakes in diagrams/specs/code |
| `playbook-advisor` | sonnet | auto | Phase guidance, readiness assessment |

---

## UAT & TESTING (4 agents)

| Agent | Model | Async | Description |
|-------|-------|-------|-------------|
| `uat-sales-hub` | sonnet | auto | Sales Hub UAT scenarios (deals, quotes, sequences) |
| `uat-service-hub` | sonnet | auto | Service Hub UAT (tickets, SLAs, health scoring, surveys) |
| `uat-integration` | sonnet | auto | Integration UAT (bi-directional sync, multi-system) |
| `uat-migration` | sonnet | auto | Migration UAT (data validation, association labels) |

**Trigger phrases:** "Create UAT", "UAT scenarios", "testing spreadsheet", "acceptance testing"
**Related skill:** `/uat-generate`
**Knowledge source:** `~/.claude/knowledge/<company>-uat-narrative-patterns.md`

---

## INTEGRATION & MIGRATION (5 agents)

| Agent | Model | Async | Description |
|-------|-------|-------|-------------|
| `integration-code-writer` | sonnet | auto | Production Node.js integration code |
| `property-mapping-builder` | sonnet | auto | Field-by-field mapping tables |
| `migration-planner` | sonnet | auto | Data migration plans, rollback strategies |
| `custom-event-specifier` | sonnet | auto | Behavioral event tracking specs |
| `context-enricher` | sonnet | auto | Progressive spec enhancement |

---

## RAG & KNOWLEDGE (8 agents)

| Agent | Model | Async | Description |
|-------|-------|-------|-------------|
| `rag-integration-expert` | sonnet | auto | RAG setup, indexing, semantic search |
| `rag-search-agent` | sonnet | auto | Multi-phase semantic search |
| `kb-query-agent` | sonnet | auto | Natural language KB Q&A |
| `kb-synthesizer` | sonnet | always | KB curation, deduplication |
| `knowledge-base-query` | sonnet | auto | Semantic search with citations |
| `knowledge-base-synthesizer` | sonnet | always | KB synthesis, executive summaries |
| `lesson-analyzer` | **opus** | always | Extract lessons from conversations |
| `comparable-project-finder` | **opus** | always | Find similar past projects |

---

## REASONING & DELEGATION (8 agents)

| Agent | Model | Async | Description |
|-------|-------|-------|-------------|
| `reasoning-duo` | sonnet | never | Claude + Codex collaborative reasoning |
| `reasoning-duo-cg` | sonnet | never | Claude + Gemini (2M context) |
| `reasoning-duo-xg` | haiku | auto | Codex + Gemini (zero Claude tokens) |
| `reasoning-trio` | sonnet | never | Claude + Codex + Gemini consensus |
| `codex-delegate` | haiku | always | Delegate to OpenAI Codex |
| `gemini-delegate` | haiku | always | Delegate to Google Gemini |
| `worker` | sonnet | always | General-purpose task delegation |
| `notebooklm-verifier` | sonnet | auto | NotebookLM verification queries |

---

## CLAUDE CODE INFRASTRUCTURE (12 agents)

| Agent | Model | Async | Description |
|-------|-------|-------|-------------|
| `agent-creation-expert` | sonnet | auto | Create custom agents |
| `skill-creation-expert` | sonnet | auto | Create custom skills and slash commands |
| `agent-coordination-expert` | sonnet | auto | Multi-agent coordination, CDP |
| `claude-md-expert` | sonnet | auto | CLAUDE.md best practices |
| `context-audit-expert` | sonnet | auto | Config validation, capability manifests |
| `memory-management-expert` | sonnet | auto | CTM, project memory, sessions |
| `ctm-expert` | sonnet | never | Cognitive Task Management system |
| `rag-integration-expert` | sonnet | auto | RAG setup and optimization |
| `performance-expert` | haiku | auto | Resource profiles, token management |
| `directory-organization-expert` | haiku | auto | Directory structure, file organization |
| `file-indexing-expert` | haiku | auto | Search patterns, codebase navigation |
| `config-migration-specialist` | sonnet | auto | Infrastructure migration between machines |

---

## MEETINGS & WORKFLOWS (4 agents)

| Agent | Model | Async | Description |
|-------|-------|-------|-------------|
| `meeting-indexer` | haiku | always | Process transcripts, extract decisions |
| `weekly-digest-generator` | sonnet | always | Weekly project digests |
| `demo-data-generator` | haiku | always | Realistic CRM demo datasets |
| `pdf-processor-unlimited` | sonnet | always | Process PDFs of any size |

---

## BRAND & PROPOSALS (4 agents)

| Agent | Model | Async | Description |
|-------|-------|-------|-------------|
| `brand-kit-extractor` | sonnet | auto | Master orchestrator for brand extraction |
| `brand-extract-web` | sonnet | auto | Extract from websites (CSS, logos) |
| `brand-extract-docs` | sonnet | auto | Extract from documents (PDF, DOCX, PPTX) |
| `brand-kit-compiler` | sonnet | never | Compile into BRAND_KIT.md |
| `proposal-orchestrator` | sonnet | auto | Complete proposal package creation |

---

## PROJECT-SPECIFIC (1 agent)

| Agent | Model | Async | Description |
|-------|-------|-------|-------------|
| `solarc-argent` | **opus** | never | Main agent for solarc-argent project |

---

## Model Distribution

| Model | Count | Use Cases |
|-------|-------|-----------|
| **haiku** | 12 | Fast lookups, delegation, file indexing, routing |
| **sonnet** | 87 | Implementation, code, docs, most tasks |
| **opus** | 7 | Architecture, complex decisions, lessons |

---

## Async Modes

| Mode | Count | Behavior |
|------|-------|----------|
| `auto` | 66 | System decides based on task |
| `always` | 22 | Always runs in background |
| `never` | 18 | Always runs synchronously (includes routers) |

---

## Auto-Invoke Triggers

These agents are invoked automatically based on context:

| Situation | Agent |
|-----------|-------|
| ERD/data model request | `erd-generator` |
| Process diagram request | `bpmn-specialist`, `lucidchart-generator` |
| HubSpot implementation | `hubspot-implementation-runbook` |
| Brand extraction | `brand-kit-extractor` |
| Proposal creation | `proposal-orchestrator` |
| Complex reasoning | `reasoning-duo` (auto-escalates) |
| Token optimization | `codex-delegate`, `gemini-delegate` |
| Meeting transcript | `meeting-indexer` |
| RAG issues | `rag-integration-expert` |
| Config problems | `context-audit-expert` |
| Error in output | `error-corrector` |
| QA needed | `deliverable-reviewer` |
| Salesforce-HubSpot mapping | `salesforce-mapping-router` |

---

## See Also

- Skills Index: `~/.claude/SKILLS_INDEX.md`
- Agent Standards: `~/.claude/AGENT_STANDARDS.md`
- CDP Protocol: `~/.claude/CDP_PROTOCOL.md`
- Inventory: `~/.claude/inventory.json`
