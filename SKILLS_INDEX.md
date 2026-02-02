# Claude Code Skills Index

Master catalog of **23 custom skills** available at `~/.claude/skills/`.

> Auto-generated: 2026-01-24 | Skills are invoked via `/skill-name` or trigger phrases.

---

## Quick Reference

| Skill | Trigger | Use Case |
|-------|---------|----------|
| `solution-architect` | "architect mode", "SA mode" | CRM architecture, system design |
| `project-discovery` | "discovery", "assess project" | Requirements gathering |
| `hubspot-specialist` | "HubSpot API", "Hub features" | HubSpot platform expertise |
| `hubspot-api-specialist` | "API v3/v4", "hs CLI", "SDK" | HubSpot API, CLI, SDK patterns |
| `hubspot-crm-card-specialist` | "CRM card", "UI extension" | CRM cards, serverless functions |
| `pptx` | "create presentation", "PPTX" | PowerPoint creation/editing |
| `doc-coauthoring` | "write a doc", "draft spec" | Collaborative documentation |
| `decision-tracker` | "record decision", "we decided" | Decision management |
| `decision-sync` | "/decision-sync" | Reconcile decisions vs docs |
| `ctm` | "ctm", "tasks", "working on" | Task management |
| `init-project` | "init project", "enable RAG" | Full project onboarding |
| `client-onboard` | "onboard client", "new client" | Client project setup |
| `memory-init` | "initialize memory" | Project memory setup |
| `brand-extract` | "/brand-extract", "brand kit" | Brand identity extraction |
| `rag-batch-index` | "batch index", "full RAG" | Systematic RAG indexing |
| `file-inbox-organizer` | "/inbox", "sort inbox" | Auto-route dropped files |
| `action-extractor` | "extract tasks", Fathom calls | Task extraction from meetings |
| `config-audit` | "/audit", "check setup" | Config validation |
| `uat-generate` | "/uat-generate", "create UAT" | UAT document generation |
| `enhance` | "/enhance" | Prompt enhancement |
| `focus` | "/focus", "what was I doing" | ADHD focus anchor + parking lot |
| `rename-smart` | "/rename-smart" | Smart session renaming |
| `cdp-delegate` | (internal) | CDP enforcement |

---

## HUBSPOT SKILLS (3)

### hubspot-specialist
**Trigger:** "HubSpot API", "Hub features", "tier pricing", "what can HubSpot do"

Comprehensive HubSpot platform expertise including all Hubs (Marketing, Sales, Service, Content, Operations, Commerce), API v3/v4, Breeze AI, and pricing tiers.

**References:** `~/.claude/skills/hubspot-specialist/references/`

---

### hubspot-api-specialist
**Trigger:** "API v3", "API v4", "hs CLI", "SDK", "@hubspot/api-client", "rate limit"

Deep technical expertise for HubSpot API integration: v3/v4 endpoints, CLI commands, Node.js SDK patterns, authentication, rate limits, batch operations.

**References:** `~/.claude/skills/hubspot-api-specialist/references/`

---

### hubspot-crm-card-specialist
**Trigger:** "CRM card", "custom card", "UI extension", "serverless function HubSpot", "hs project"

Creates CRM cards (UI Extensions) and serverless functions via Developer Projects or CMS. Working boilerplate, 2025.2 platform version.

**References:** `~/.claude/skills/hubspot-crm-card-specialist/references/`

---

## ARCHITECTURE & CONSULTING (2)

### solution-architect
**Trigger:** "architect mode", "SA mode", "act as solution architect", ERD/BPMN requests

Embodies Raphaël Fenaux, Senior CRM Solutions Architect. Use for:
- Solution design and system architecture
- CRM implementations (HubSpot, Salesforce)
- Integration planning and discovery workshops
- ERD/BPMN diagrams and integration specs

**References:** `~/.claude/skills/solution-architect/references/`

---

### project-discovery
**Trigger:** "assess a project", "validate scope", "review requirements", "discovery questions"

Structured project discovery and requirements assessment framework. Generates discovery questionnaires, validates scope, identifies risks.

**References:** `~/.claude/skills/project-discovery/`

---

## DOCUMENTATION (2)

### pptx
**Trigger:** "create presentation", "edit slides", "PPTX", "PowerPoint"

Presentation creation, editing, and analysis. Creates new presentations, modifies existing PPTX files, extracts content from presentations.

**References:** `~/.claude/skills/pptx/references/`

---

### doc-coauthoring
**Trigger:** "write a doc", "draft spec", "proposal", "document together"

Guides users through structured workflow for co-authoring documentation: proposals, technical specs, reports, guides.

---

## UAT & TESTING (1)

### uat-generate
**Trigger:** "/uat-generate", "create UAT", "UAT scenarios", "acceptance testing"

Generates professional UAT documents following <COMPANY>'s established patterns from 45+ past implementations. Interactive wizard or targeted generation:
- `/uat-generate sales` - Sales Hub UAT template
- `/uat-generate service` - Service Hub UAT template
- `/uat-generate integration <system>` - Integration UAT template
- `/uat-generate migration` - Data migration UAT template

**Related Agents:** `uat-sales-hub`, `uat-service-hub`, `uat-integration`, `uat-migration`
**Knowledge source:** `~/.claude/knowledge/<company>-uat-narrative-patterns.md`

---

## DECISION MANAGEMENT (2)

### decision-tracker
**Trigger:** "record decision", "supersede", "we decided", "decision made"

Manages architecture decisions with temporal tracking and supersession awareness. Records, checks, and supersedes project decisions using A/T/P/S taxonomy.

---

### decision-sync
**Trigger:** "/decision-sync", "sync decisions", "reconcile decisions"

Reconciles decisions between conversation files and DECISIONS.md to prevent documentation drift. Identifies decisions in chat that weren't recorded.

---

## PROJECT SETUP (4)

### init-project
**Trigger:** "init project", "onboard project", "enable RAG", "set up Claude"

Initialize a new project with RAG, memory system, and git hooks. One command to set up the full Claude Code infrastructure for a project.

---

### client-onboard
**Trigger:** "onboard client", "new client", "set up project"

Onboard a new client project with full Claude Code infrastructure: RAG, memory, brand kit, CTM task, and templates. One command to start a new engagement.

---

### memory-init
**Trigger:** "initialize memory", "set up context", "create DECISIONS.md"

Sets up persistent memory structure for projects enabling Claude to maintain context across conversations. Creates context/ directory with standard files.

---

### rag-batch-index
**Trigger:** "batch index", "index everything", "full RAG indexing"

Batch index a project into RAG with smart folder discovery, exclusions, progress tracking, and post-index audit.

---

## TASK MANAGEMENT (1)

### ctm
**Trigger:** "ctm", "show tasks", "what am I working on", "spawn task", "switch task"

Bio-inspired task management for multi-task context across sessions. Provides session briefings, task switching, checkpoints, and decision extraction.

**Commands:** `ctm status`, `ctm brief`, `ctm spawn`, `ctm switch`, `ctm complete`, `ctm checkpoint`

---

## MEETING & CONTENT (3)

### action-extractor
**Trigger:** "extract tasks", "analyze meeting", "process transcript", Fathom MCP tool calls

Use when Fathom MCP tools are called, user says "extract tasks", "analyze meeting", or when emails/transcripts appear. Extracts tasks, decisions, and action items.

---

### brand-extract
**Trigger:** "/brand-extract", "extract brand", "brand kit", "brand colors"

Extract brand identity (colors, typography, logos) from websites and documents. Creates Claude-consumable BRAND_KIT.md for consistent styling.

---

### file-inbox-organizer
**Trigger:** "/inbox", "sort inbox", "process inbox"

Process files dropped in `00-inbox/` and route them to appropriate project folders based on configurable rules. Auto-renames, routes, and indexes to RAG.

---

## UTILITY (4)

### config-audit
**Trigger:** "/audit", "check setup", "validate config", "health check"

Audit Claude Code configuration - validates imports, checks settings, generates capability manifests. Use for health checks and troubleshooting.

---

### enhance
**Trigger:** "/enhance", "/enhance on", "/enhance off"

Prompt enhancement system - rewrites and improves user prompts before execution for better clarity, specificity, and edge case coverage.

**Commands:** `/enhance` (status), `/enhance on`, `/enhance off`

---

### focus
**Trigger:** "/focus", "what was I doing", "where was I", "I'm lost"

ADHD focus anchor - shows current task, parked ideas, and next action. Helps re-center when feeling scattered.

**Commands:** `/focus` (show anchor), `/focus park <topic>` (quick park), `/focus clear` (review parked)

**Auto-invokes when:** User asks "what were we doing?", returns after break, or 3+ topic switches without completion.

---

### rename-smart
**Trigger:** "/rename-smart"

Smart session renaming with timestamp + AI-generated title. Auto-invoked after N messages, at PreCompact, SessionEnd, or manually.

---

### cdp-delegate
**Trigger:** (internal - auto-invoked)

Enforces the Cognitive Delegation Protocol when spawning sub-agents. Internal helper skill that ensures proper handoff semantics.

---

## Model Distribution

| Model | Skills | Use Cases |
|-------|--------|-----------|
| **sonnet** | All 21 | Default for all skills |

---

## See Also

- Agents Index: `~/.claude/AGENTS_INDEX.md`
- Skill Standards: `~/.claude/SKILL_STANDARDS.md`
- Inventory: `~/.claude/inventory.json`
