# Agent Dependency Graph

> Auto-generated visualization of agent orchestration and delegation patterns.

## Orchestrator Agents

These agents coordinate multiple sub-agents:

```mermaid
graph TB
    subgraph "HubSpot Implementation"
        HS[hubspot-implementation-runbook] --> HS_D[hubspot-impl-discovery]
        HS --> HS_M[hubspot-impl-marketing-hub]
        HS --> HS_S[hubspot-impl-sales-hub]
        HS --> HS_SV[hubspot-impl-service-hub]
        HS --> HS_O[hubspot-impl-operations-hub]
        HS --> HS_C[hubspot-impl-content-hub]
        HS --> HS_CM[hubspot-impl-commerce-hub]
        HS --> HS_DM[hubspot-impl-data-migration]
        HS --> HS_I[hubspot-impl-integrations]
        HS --> HS_G[hubspot-impl-governance]
        HS --> HS_CH[hubspot-impl-change-management]
        HS --> HS_B2B[hubspot-impl-b2b2c]
        HS --> HS_SUB[hubspot-impl-subscriptions]
        HS --> HS_CP[hubspot-impl-customer-portal]
    end

    subgraph "Brand Extraction"
        BK[brand-kit-extractor] --> BK_W[brand-extract-web]
        BK --> BK_D[brand-extract-docs]
        BK --> BK_C[brand-kit-compiler]
    end

    subgraph "Proposal Creation"
        PO[proposal-orchestrator] --> BK
        PO --> SD[solution-spec-writer]
        PO --> ROI[roi-calculator]
        PO --> SLIDE[slide-deck-creator]
        PO --> DISC[project-discovery]
    end

    subgraph "Token Optimization"
        CODEX[codex-delegate] -.-> |"delegates to"| CODEX_CLI[Codex CLI]
        GEMINI[gemini-delegate] -.-> |"delegates to"| GEMINI_CLI[Gemini CLI]
        WORKER[worker] --> |"general tasks"| CDP[CDP Protocol]
    end

    subgraph "Reasoning"
        RD[reasoning-duo] --> CODEX
        RD --> CLAUDE[Claude]
    end

    style HS fill:#667eea,color:#fff
    style BK fill:#06d6a0,color:#000
    style PO fill:#764ba2,color:#fff
    style RD fill:#f59e0b,color:#000
```

## Utility Agents

These agents are called by multiple orchestrators:

```mermaid
graph LR
    subgraph "Documentation"
        ERD[erd-generator]
        BPMN[bpmn-specialist]
        LUCID[lucidchart-generator]
        FSD[functional-spec-generator]
    end

    subgraph "Analysis"
        RISK[risk-analyst-*]
        ROI[roi-calculator]
        AUDIT[technology-auditor]
        MVP[mvp-scoper]
    end

    subgraph "Content"
        SLIDE[slide-deck-creator]
        EXEC[executive-summary-creator]
        TRAIN[training-creator]
        API_DOC[api-documentation-generator]
    end

    subgraph "Data"
        PROP[property-mapping-builder]
        MIG[migration-planner]
        DEMO[demo-data-generator]
    end
```

## Agent Categories by Model

| Model | Agents | Use Case |
|-------|--------|----------|
| **Opus** | solution-architect, reasoning-duo | Complex architecture, multi-system design |
| **Sonnet** | Most implementation agents | Code, specs, detailed analysis |
| **Haiku** | Explore agents, meeting-indexer, worker | Quick lookups, bulk processing |

## Async Mode Distribution

```mermaid
pie title Agent Async Modes
    "always (background)" : 15
    "never (sync only)" : 25
    "auto (context-dependent)" : 37
```

## Call Patterns

### Sequential Chain
```
User Request
    → discovery-audit-analyzer
    → solution-spec-writer
    → erd-generator
    → deliverable-reviewer
    → Final Output
```

### Parallel Fan-Out
```
User Request
    → brand-extract-web ─────┐
    → brand-extract-docs ────┼─→ brand-kit-compiler
    → image analysis ────────┘
```

### Hub-and-Spoke
```
hubspot-implementation-runbook (Hub)
    ├─→ discovery
    ├─→ marketing-hub
    ├─→ sales-hub
    ├─→ service-hub
    └─→ ... (13 more spokes)
```

## Key Dependencies

| Agent | Requires | Optional |
|-------|----------|----------|
| `proposal-orchestrator` | `solution-spec-writer`, `roi-calculator` | `brand-kit-extractor`, `slide-deck-creator` |
| `brand-kit-extractor` | `brand-extract-web` OR `brand-extract-docs` | `brand-kit-compiler` |
| `reasoning-duo` | `codex-delegate` | - |
| `hubspot-implementation-runbook` | `hubspot-impl-discovery` | All other hub agents |

## CDP Workspace Flow

All delegated agents follow the Cognitive Delegation Protocol:

```
PRIMARY CONVERSATION
    │
    │ 1. Creates HANDOFF.md
    │
    ├────────────────────────► SUB-AGENT WORKSPACE
    │                              │
    │                              │ 2. Executes task
    │                              │
    │                              │ 3. Writes OUTPUT.md
    │                              │
    │ ◄────────────────────────────┘
    │
    │ 4. Reads OUTPUT.md (summary only)
    │
    ▼
CONTINUES WITH RESULTS
```

## Agent Count by Domain

| Domain | Count | Examples |
|--------|-------|----------|
| HubSpot Implementation | 15 | hubspot-impl-*, hubspot-specialist |
| Documentation | 12 | functional-spec-generator, erd-generator, bpmn-specialist |
| Analysis | 8 | risk-analyst, roi-calculator, technology-auditor |
| Token Optimization | 3 | codex-delegate, gemini-delegate, worker |
| Brand | 3 | brand-kit-extractor, brand-extract-web, brand-extract-docs |
| Commercial | 5 | commercial-analyst-*, 80-20-recommender |
| Other Specialized | 31 | Various domain-specific agents |

**Total: 77 agents**

---

*Last updated: 2026-01-15*
*Regenerate with: `~/.claude/scripts/generate-agent-graph.sh`*
