# Claude Code Skills Index

Master catalog of **57 native skills** + **7 enabled plugin sets** available at `~/.claude/skills/`.

> Auto-generated: 2026-02-13 | Skills are invoked via `/skill-name` or trigger phrases.

---

## Quick Reference

| Skill | Trigger | Use Case |
|-------|---------|----------|
| **Core Consulting (2)** |||
| `solution-architect` | "architect mode", "SA mode" | CRM architecture, system design |
| `project-discovery` | "discovery", "assess project" | Requirements gathering |
| **HubSpot (3)** |||
| `hubspot-specialist` | "HubSpot API", "Hub features" | HubSpot platform expertise |
| `hubspot-api-specialist` | "API v3/v4", "hs CLI", "SDK" | HubSpot API, CLI, SDK patterns |
| `hubspot-crm-card-specialist` | "CRM card", "UI extension" | CRM cards, serverless functions |
| **Task Management (10)** |||
| `ctm` | "ctm", "tasks", "working on" | Cognitive task management |
| `pm-spec` | "/pm-spec", "create a spec" | Interactive spec creation |
| `pm-decompose` | "/pm-decompose", "break down" | Task decomposition with deps |
| `pm-gh-sync` | "/pm-gh-sync", "push to github" | CTM ↔ GitHub Issues sync |
| `deviate` | "/deviate", "found bug" | Deviation handling |
| `progress` | "/progress", "what's next" | Unified status + routing |
| `quick` | "/quick" | Ad-hoc tasks without CTM |
| `focus` | "/focus", "what was I doing" | ADHD focus anchor |
| `checkpoint` | "/checkpoint" | Manual session checkpointing |
| `plan-check` | "/plan-check" | Verify work against task plan |
| `mem-search` | "/mem-search", "session history" | Observation memory search |
| **Documentation (4)** |||
| `pptx` | "create presentation", "PPTX" | PowerPoint creation/editing |
| `doc-coauthoring` | "write a doc", "draft spec" | Collaborative documentation |
| `uat-generate` | "/uat-generate", "create UAT" | UAT document generation |
| `flowchart` | "/flowchart" | Interactive HTML flowcharts |
| **Decision Management (2)** |||
| `decision-tracker` | "record decision", "we decided" | Decision management |
| `decision-sync` | "/decision-sync" | Reconcile decisions vs docs |
| **Project Setup (5)** |||
| `init-project` | "init project", "enable RAG" | Full project onboarding |
| `client-onboard` | "onboard client", "new client" | Client project setup |
| `memory-init` | "initialize memory" | Project memory setup |
| `rag-batch-index` | "batch index", "full RAG" | Systematic RAG indexing |
| `reindex` | "reindex", "refresh RAG" | Quick fire-and-forget reindex |
| **Meeting & Content (3)** |||
| `action-extractor` | "extract tasks", Fathom calls | Task extraction from meetings |
| `brand-extract` | "/brand-extract", "brand kit" | Brand identity extraction |
| `file-inbox-organizer` | "/inbox", "sort inbox" | Auto-route dropped files |
| **Security (7)** |||
| `security/tob-semgrep` | "/semgrep" | Semgrep static analysis |
| `security/tob-codeql` | "/codeql" | CodeQL deep analysis |
| `security/tob-sharp-edges` | "/sharp-edges" | Dangerous API patterns |
| `security/tob-audit-context` | "/audit-context" | Architectural context for vuln hunting |
| `security/tob-variant-analysis` | "/find-variants" | Similar vulnerability search |
| `security/tob-fix-review` | "/fix-review" | Bug fix regression check |
| `security/tob-differential-review` | "/security-review" | Security code review |
| **Meta & Utilities (9)** |||
| `config-audit` | "/audit", "check setup" | Config validation |
| `enhance` | "/enhance" | Prompt enhancement |
| `rename-smart` | "/rename-smart" | Smart session renaming |
| `cdp-delegate` | (internal) | CDP enforcement |
| `context-inspector` | "/context" | Context window inspection |
| `session-retro` | "/session-retro" | Session retrospective |
| `tmux-teams` | "/tmux-teams" | Agent Teams visual mode |
| `brightness` | "/brightness" | Display brightness control |
| `trust` | "/trust" | Trust/security management |
| **Status & Scope (3)** |||
| `status-bundle-update` | "/status-bundle", "update status" | Bundle CTM + report + tasks + checkpoint |
| `scope-defense-bundle` | "/scope-defense", "SOW said X" | SOW delta matrix + effort + defense comms |
| `project-completeness-audit` | "/completeness-audit", "are we done?" | Requirement-to-deliverable tracing |
| **Retrospective (2)** |||
| `slack-sync-ritual` | "/slack-sync", "sync Slack" | Sync Slack decisions/blockers to CTM |
| `post-mortem-analyzer` | "/post-mortem", "what went wrong?" | Project failure analysis + lessons |
| **Research & Refactoring (3)** |||
| `research-loop` | "/research", "investigate X" | Self-directed RAG → Web → Clarify research loop |
| `refactor` | "/refactor rename X Y" | Multi-file refactoring with dep analysis + git safety |
| `team` | "/team spawn template name" | Agent Teams from templates with health monitoring |

---

## CORE CONSULTING (2)

### solution-architect
**Trigger:** "architect mode", "SA mode", "act as solution architect", ERD/BPMN requests

Embodies a Senior CRM Solutions Architect persona. Use for:
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

## TASK MANAGEMENT (10)

### ctm
**Trigger:** "ctm", "show tasks", "what am I working on", "spawn task", "switch task"

Bio-inspired task management for multi-task context across sessions. Provides session briefings, task switching, checkpoints, and decision extraction.

**Commands:** `ctm status`, `ctm brief`, `ctm spawn`, `ctm switch`, `ctm complete`, `ctm checkpoint`

---

### pm-spec
**Trigger:** "/pm-spec", "create a spec", "spec out", "scope this"

Interactive specification creation for features, implementations, or integrations. Guided brainstorming producing structured specs with requirements and technical approach.

**Commands:** `/pm-spec`, `/pm-spec {name}`, `/pm-spec {name} --type dev|hubspot|integration`, `/pm-spec --list`

---

### pm-decompose
**Trigger:** "/pm-decompose", "break this down", "decompose", "create subtasks"

Break specs or CTM tasks into dependency-aware sub-tasks. Creates CTM tasks with dependencies, deadlines, and parallel flags. Use after /pm-spec or when a task needs breaking down.

**Commands:** `/pm-decompose {spec-name}`, `/pm-decompose {ctm-task-id}`, `/pm-decompose --dry-run`, `/pm-decompose --todo`

---

### pm-gh-sync
**Trigger:** "/pm-gh-sync", "push to github", "sync issues", "import issue"

Bidirectional sync between CTM tasks and GitHub Issues. Push tasks to GitHub, pull issues into CTM, sync status. Use after /pm-decompose or for GitHub tracking.

**Commands:** `/pm-gh-sync --push`, `/pm-gh-sync --pull`, `/pm-gh-sync --status`, `/pm-gh-sync --map`

---

### mem-search
**Trigger:** "/mem-search", "session history", "what did I work on", "past sessions"

Search session observation summaries with progressive disclosure. Shows recent session activity, searches past sessions semantically, and displays system health stats.

**Commands:** `/mem-search`, `/mem-search recent`, `/mem-search "query"`, `/mem-search detail`, `/mem-search stats`

---

### deviate
**Trigger:** "/deviate", "found bug", "need to rethink", "scope creep", "blocked by"

Handle work deviations gracefully with 4 types: bug (fix or spawn), architectural (pause/escalate), scope_creep (park), blocker (log/switch). GSD-inspired.

**Commands:** `/deviate`, `/deviate bug --fix`, `/deviate architectural`, `/deviate scope`

---

### progress
**Trigger:** "/progress", "where am I", "what's next", "status"

Unified progress view with intelligent routing. Shows CTM status, task details (files/verify/done), and suggests next actions based on context.

**Commands:** `/progress`, `/progress [task-id]`, `/progress --verify`

---

### quick
**Trigger:** "/quick", "just quickly", "small fix"

Ad-hoc task execution without CTM ceremony. For small, self-contained tasks under 5 minutes. Optional tracking with `--track`.

**Commands:** `/quick "task"`, `/quick --track "task"`, `/quick --done`

---

### focus
**Trigger:** "/focus", "what was I doing", "where was I", "I'm lost"

ADHD focus anchor - shows current task, parked ideas, and next action. Helps re-center when feeling scattered.

**Commands:** `/focus` (show anchor), `/focus park <topic>` (quick park), `/focus clear` (review parked)

**Auto-invokes when:** User asks "what were we doing?", returns after break, or 3+ topic switches without completion.

---

### checkpoint
**Trigger:** "/checkpoint", "save checkpoint", "checkpoint session"

Manual session checkpointing for CTM. Captures current state, decisions, and learnings mid-session. Auto-invoked at SessionEnd hook.

**Commands:** `/checkpoint`, `/checkpoint --message "note"`

---

### plan-check
**Trigger:** "/plan-check", "am I on track", "check plan"

Verify current work against task plan. Warns when editing files not in the task's files list or missing verification criteria.

**Commands:** `/plan-check`, `/plan-check files`, `/plan-check [file]`

---

## DOCUMENTATION (4)

### pptx
**Trigger:** "create presentation", "edit slides", "PPTX", "PowerPoint"

Presentation creation, editing, and analysis. Creates new presentations, modifies existing PPTX files, extracts content from presentations.

**References:** `~/.claude/skills/pptx/references/`

---

### doc-coauthoring
**Trigger:** "write a doc", "draft spec", "proposal", "document together"

Guides users through structured workflow for co-authoring documentation: proposals, technical specs, reports, guides.

---

### uat-generate
**Trigger:** "/uat-generate", "create UAT", "UAT scenarios", "acceptance testing"

Generates professional UAT documents following established patterns from 45+ past implementations. Interactive wizard or targeted generation:
- `/uat-generate sales` - Sales Hub UAT template
- `/uat-generate service` - Service Hub UAT template
- `/uat-generate integration <system>` - Integration UAT template
- `/uat-generate migration` - Data migration UAT template

**Related Agents:** `uat-sales-hub`, `uat-service-hub`, `uat-integration`, `uat-migration`
**Knowledge source:** `~/.claude/knowledge/uat-narrative-patterns.md`

---

### flowchart
**Trigger:** "/flowchart", "create flowchart", "process diagram"

Creates interactive HTML flowcharts with Mermaid.js. Supports process flows, decision trees, and system diagrams with live editing.

**Commands:** `/flowchart "description"`, `/flowchart --from-file [path]`

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

### reindex
**Trigger:** "reindex", "refresh RAG index", "reindex this project"

Quick fire-and-forget RAG reindex for current project. Pre-flight check, background execution, exclusions. Unlike `/rag-batch-index`, skips discovery/audit — just refreshes already-tracked files.

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

## STATUS & SCOPE (3)

### status-bundle-update
**Trigger:** "/status-bundle", "update status", "ship update", "end of day update"

Consolidate 4 manual status update steps into 1 command: CTM progress, project status report, task list, and CTM checkpoint. Saves 5-10 minutes per work block.

**Workflow:** CTM progress update → Status report → Task list sync → Checkpoint

---

### scope-defense-bundle
**Trigger:** "/scope-defense", "scope creep", "SOW said X", "defend scope"

Commercial scope defense evidence bundle: SOW delta matrix, effort quantification for out-of-scope work, and draft defense communication. For when scope creep threatens project margins.

**Workflow (7 steps):** Read SOW → Inventory deliverables → Delta matrix → Identify additions → Calculate effort → Draft communication → Package bundle

---

### project-completeness-audit
**Trigger:** "/completeness-audit", "are we done?", "go-live ready?", "what's missing?"

End-of-project requirement-to-deliverable tracing. Coverage matrix showing delivered/partial/missing status. Sweeps open items from DECISIONS.md and CTM.

**Workflow (6 steps):** Extract requirements → Trace to deliverables → Coverage matrix → Sweep open items → Validate configs → Produce report

---

## RETROSPECTIVE (2)

### slack-sync-ritual
**Trigger:** "/slack-sync", "sync Slack", "check Slack", "what happened on Slack?"

Sync decisions, blockers, and actions from Slack channels into CTM context. Must run in main session (requires Slack MCP).

**Workflow:** Search Slack → Extract decisions → Extract blockers → Update CTM → Flag unconfirmed

---

### post-mortem-analyzer
**Trigger:** "/post-mortem", "post-mortem", "what went wrong?", "retrospective"

Analyze archived project conversations for failure points, root causes, and actionable lessons. Compares against successful project patterns.

**Workflow:** Read history → Identify failures → Extract root causes → Compare patterns → Generate lessons report

---

## SECURITY (7)

### security/tob-semgrep
**Trigger:** "/semgrep", "run semgrep", "static analysis"

Runs Semgrep static analysis with Trail of Bits rulesets. Fast, pattern-based vulnerability detection for common security issues.

**Rulesets:** OWASP Top 10, CWE Top 25, framework-specific rules

---

### security/tob-codeql
**Trigger:** "/codeql", "deep analysis", "data flow analysis"

Runs CodeQL deep semantic analysis. Tracks data flows, finds complex vulnerabilities missed by pattern matching.

**Use for:** SQL injection, XSS, authentication bypasses, complex logic flaws

---

### security/tob-sharp-edges
**Trigger:** "/sharp-edges", "dangerous APIs", "unsafe patterns"

Identifies dangerous API patterns and sharp edges in code: unsafe deserialization, command injection vectors, cryptographic misuse.

---

### security/tob-audit-context
**Trigger:** "/audit-context", "vulnerability context", "architecture for security"

Generates architectural context for vulnerability hunting. Maps attack surfaces, trust boundaries, and data flows.

---

### security/tob-variant-analysis
**Trigger:** "/find-variants", "similar vulnerabilities", "pattern search"

Searches codebase for variants of a known vulnerability pattern. Uses semantic search to find similar security issues.

---

### security/tob-fix-review
**Trigger:** "/fix-review", "review bug fix", "regression check"

Reviews security bug fixes for completeness and regressions. Ensures fixes address root cause without introducing new issues.

---

### security/tob-differential-review
**Trigger:** "/security-review", "code review security", "diff review"

Security-focused code review of diffs/PRs. Identifies security implications of changes, privilege escalations, input validation gaps.

---

## META & UTILITIES (9)

### config-audit
**Trigger:** "/audit", "check setup", "validate config", "health check"

Audit Claude Code configuration - validates imports, checks settings, generates capability manifests. Use for health checks and troubleshooting.

---

### enhance
**Trigger:** "/enhance", "/enhance on", "/enhance off"

Prompt enhancement system - rewrites and improves user prompts before execution for better clarity, specificity, and edge case coverage.

**Commands:** `/enhance` (status), `/enhance on`, `/enhance off`

---

### rename-smart
**Trigger:** "/rename-smart"

Smart session renaming with timestamp + AI-generated title. Auto-invoked after N messages, at PreCompact, SessionEnd, or manually.

---

### cdp-delegate
**Trigger:** (internal - auto-invoked)

Enforces the Cognitive Delegation Protocol when spawning sub-agents. Internal helper skill that ensures proper handoff semantics.

---

### context-inspector
**Trigger:** "/context", "inspect context", "context window"

Context window inspection tool. Shows usage breakdown, top consumers, pruning opportunities.

**Commands:** `/context` (summary), `/context list`, `/context detail`, `/context trim`

---

### session-retro
**Trigger:** "/session-retro", "session retrospective", "what did we accomplish"

Generates session retrospective: what was accomplished, decisions made, open questions, next steps. Auto-invoked at SessionEnd.

---

### tmux-teams
**Trigger:** "/tmux-teams", "team visual mode", "tmux layout"

Agent Teams visual mode using tmux layouts. Shows team members, task assignments, and message flow in split-pane view.

**Requires:** `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`

---

### brightness
**Trigger:** "/brightness", "set brightness", "dim screen"

Display brightness control via DDC. Useful for reducing eye strain during long sessions.

**Commands:** `/brightness [0-100]`, `/brightness --dim`, `/brightness --bright`

---

### trust
**Trigger:** "/trust", "trust domain", "security settings"

Trust/security management for external resources. Manages trusted domains, API endpoints, and security policies.

**Commands:** `/trust add [domain]`, `/trust list`, `/trust remove [domain]`

---

## ENABLED PLUGINS (6 plugin sets)

### visual-documentation-skills (mhattingpete)
**Skills:** `architecture-diagram-creator`, `dashboard-creator`, `flowchart-creator`, `technical-doc-creator`, `timeline-creator`

Visual documentation generation with Mermaid.js, D3.js, and custom renderers.

---

### doc-tools (cc-skills)
**Skills:** `pandoc-pdf-generation`, `documentation-standards`, `latex-tables`, `latex-build`, `latex-setup`, `ascii-diagram-validator`, `terminal-print`

Document conversion, LaTeX toolchain, ASCII diagrams, and terminal formatting.

---

### itp (cc-skills)
**Skills:** `go`, `setup`, `release`, `hooks`, `code-hardcode-audit`, `mise-tasks`, `graph-easy`, `implement-plan-preflight`, `bootstrap-monorepo`, `pypi-doppler`, `semantic-release`, `mise-configuration`, `adr-code-traceability`, `impl-standards`, `adr-graph-easy-architect`

Internal tooling platform: project scaffolding, release automation, monorepo management, ADR workflows, and implementation standards.

---

### dotfiles-tools (cc-skills)
**Skills:** `chezmoi-workflows`, `hooks`

Dotfiles management with chezmoi: templating, machine-specific configs, and sync workflows.

---

### statusline-tools (cc-skills)
**Skills:** `setup`, `ignore`, `hooks`, `session-info`

Shell statusline integration: session context in prompt, ignore patterns, and git hooks.

---

### iterm2-layout-config (cc-skills)
**Skills:** `iterm2-layout`

iTerm2 window layout management for project-specific workspace configurations.

---

## Model Distribution

| Model | Skills | Use Cases |
|-------|--------|-----------|
| **sonnet** | All 41 native + plugins | Default for all skills |
| **haiku** | Optional for lightweight tasks | Fast config checks, simple lookups |
| **opus** | Optional for complex architecture | Multi-system integration design |

---

## See Also

- Agents Index: `~/.claude/AGENTS_INDEX.md`
- Skill Standards: `~/.claude/SKILL_STANDARDS.md`
- Inventory: `~/.claude/inventory.json`
- Plugin Development: `~/.claude/docs/PLUGIN_DEVELOPMENT.md`
