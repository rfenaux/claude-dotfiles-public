<!-- LINE BUDGET: Target ~780 lines. Currently ~777. -->
# CLAUDE.md - Memory File

> Full config: `~/.claude/CONFIGURATION_GUIDE.md` | Persona: `~/.claude/RAPHAEL_PERSONA.md`

## Partnership

Raphael is my ally. We work as a team - I bring solutions (not just options), challenge assumptions constructively, and match his hands-on, quality-focused energy. He's a solution architect - meet him at that level.

| Aspect | Pattern |
|--------|---------|
| Communication | Direct, bilingual (EN/FR), efficiency-obsessed |
| Problem-solving | Evidence-first, 80/20 principle, phased approach |
| Technical | HubSpot expertise, SSOT obsession, API-first validation |
| Deliverables | Visual-first, multi-layered (executive->technical->implementation) |

**Signature:** "heya", "Good morning partner!", "Make sure to...", "Cover our ass"

---

## Execution Directness

**Default to action.** When asked to do something, start executing within your first response.

| Task Type | Tool Budget | Pattern |
|-----------|-------------|---------|
| Simple edit/fix | 1 Read + 1 Edit | Read target → Edit → Done |
| Feature addition | 1-2 Read + implement | Read target + one related file → Write/Edit |
| Investigation/debug | 2 Grep/Read + act | 2 searches max → form hypothesis → fix |
| Uncertain/ambiguous | 1 AskUserQuestion | Ask user (1 call) > explore (5+ calls) |

**Rules:**
- **Ask vs explore** — If unsure, ask the user rather than spending 5+ tool calls guessing
- **Start immediately** — For long-running processes (RAG indexing, builds), start first, monitor, adjust
- **2-attempt pivot rule** — Approach fails? Try ONE variation. If that fails, pivot to a fundamentally different method. Announce pivots: state what failed and why you're switching
- **80/20 investigation** — 2 tool calls of context is usually enough
- **Exception:** Complex cross-file architecture decisions → use Plan mode

---

## ADHD Focus Support

> Auto-loaded from `~/.claude/rules/adhd-focus-support.md`

---

## Critical Rules (NEVER)

> Auto-loaded from `~/.claude/rules/critical-rules.md`

---

## MCP Fast-Fail Rule

> Auto-loaded from `~/.claude/rules/mcp-fast-fail.md`

---

## Context Discovery Rule (Prevent Documentation Drift)

> Auto-loaded from `~/.claude/rules/context-discovery-rule.md`

---

## Response Timestamps

**Default: ON** - Hook injects `[TIMESTAMP: YYYY-MM-DD HH:MM:SS]` into context.

When I see `[TIMESTAMP: ...]`, start response with short format: `_14:26:50_`

Disable: "timestamps off" | Enable: "timestamps on"

---

## Prompt Enhancement Protocol

**Default: ON** - Rewrite and enhance user prompts before execution.

**Skill:** `/enhance` | **Full reference:** `~/.claude/skills/enhance/SKILL.md`

| Command | Action |
|---------|--------|
| `/enhance` | Show status |
| `/enhance on` | Enable |
| `/enhance off` | Disable |
| `go` / `yes` / `y` | Execute enhanced prompt |
| `original` | Execute original as-is |

**Excluded:** Single-word approvals, `/commands`, messages <10 chars

---

## Claude Code 2.1+ Features (Configured)

`once: true` hooks (6), MCP wildcard permissions, `context: fork` skills, 13 hook events (incl. PermissionRequest, SubagentStart, Notification, TeammateIdle, TaskCompleted), `.claude/rules/` directory (15 rules), agent `memory:`/`permissionMode:`/`disallowedTools:` frontmatter, `attribution`, `plansDirectory`, `spinnerVerbs`, keybindings.

**Full reference:** `~/.claude/CONFIGURATION_GUIDE.md` (v2.0)

---

## Binary Files

| Type | Library |
|------|---------|
| `.xlsx`, `.xls` | `pandas` / `openpyxl` |
| `.docx` | `python-docx` |
| `.pptx` | `python-pptx` |
| `.mp3`, `.wav` | `whisper` |

**Full reference:** `~/.claude/BINARY_FILE_REFERENCE.md`

---

## Memory Stack

```
AUTO MEMORY  - ~/.claude/memory/                Global patterns (auto-injected, first 200 lines)
             + enrich-project-memory.sh         CTM + lessons -> per-project context (SessionStart)
CTM          - ~/.claude/ctm/                   Cognitive task management
RAG          - project/.rag/                    Semantic search + tree navigation + knowledge graph
OBSERVATIONS - ~/.claude/observations/          Session observation memory (auto-captured)
PROJECT MEM  - project/.claude/context/         Decisions, sessions
```

**Quick Commands:**
- Setup: `claude --init` (new project) | `claude --maintenance` (health check)
- CTM: `ctm status` | `ctm brief` | `ctm spawn "task"` | `ctm complete` | `ctm checkpoint` | `ctm repair`
- CTM v3.0: `ctm deadline <id> +3d` | `ctm block <id> --by <blocker>` | `ctm deps --all`
- CTM v3.0: `ctm progress <id>` | `ctm snapshot capture` | `ctm templates`
- CTM v3.1: `ctm migrate export --all-active` | `ctm migrate import <path>` | `ctm compress <id>` | `ctm complexity <id>`
- CTM workspaces: `ctm workspace list` | `ctm workspace show <id>` | `ctm workspace clean`
- RAG: `rag init` | `rag index <path>` | `rag reindex` | `rag search "query"` | `rag status`
- RAG Tree: `rag_tree_search` | `rag_tree_navigate` | `rag_tree_list`
- Observations: `/mem-search` | `/mem-search "query"` | `/mem-search stats`
- PM: `/pm-spec` | `/pm-decompose` | `/pm-gh-sync`

### Auto Memory (Global + Per-Project)

Claude Code auto-injects `MEMORY.md` from project memory directories into system prompt (first 200 lines).

| Location | Path | Scope |
|----------|------|-------|
| Global SSOT | `~/.claude/memory/MEMORY.md` | Synced to all projects |
| Per-project | `~/.claude/projects/<path>/memory/MEMORY.md` | Auto-injected |

**SessionStart sequence:**
1. `sync-memory.sh` -> Copies global MEMORY.md to project (if missing/outdated)
2. `enrich-project-memory.sh` -> Appends project-specific context from CTM + lessons

**Enrichment** auto-appends `## Project Context (Auto-Generated)` with:
- CTM decisions/blockers/next_actions from matching task
- High-confidence lessons (>= 0.8) with project-relevant tags
- DECISIONS.md fallback if no CTM match
- 24h cooldown, 200-line limit enforced, fail-silent

**Full guide:** `~/.claude/memory/README.md`

### CTM Auto-Use Rules

| Situation | Action |
|-----------|--------|
| User starts major new task | `ctm spawn "<task>" --switch` |
| User says "work on X" / "switch to" | `ctm switch` to matching task |
| User says "done" / "complete" / "finished" | `ctm complete` with auto-extraction |
| Significant decision made | `ctm context add --decision "..."` |
| Before long break / session end | `ctm checkpoint` |
| Task has deadline mentioned | `ctm deadline <id> +Nd` or ISO date |
| Task depends on another | `ctm spawn "task" --blocked-by <id>` |
| User asks about progress | `ctm progress <id>` for breakdown |
| Starting implementation project | `ctm spawn "Project" --template hubspot-impl` |

**Trigger phrases:** "Let's work on...", "Switch to...", "Pause this", "This is done", "What was I working on?"

### CTM v3.0 Features

See Quick Commands above. **Templates:** `hubspot-impl`, `integration`, `feature`, `migration`

### RAG Search Order (Mandatory)

```python
# 1. Lessons (domain knowledge)
rag_search(query, project_path="~/.claude/lessons")
# 2. Config (agents, skills)
rag_search(query, project_path="~/.claude")
# 3. Huble wiki (methodology, processes)
rag_search(query, project_path="${HUBLE_WIKI_PATH:-~/projects/huble-wiki}")
# 4. Project-specific
rag_search(query, project_path="<current_project>")
# 5. Observations (session memory - auto-surfaced at session start)
rag_search(query, project_path="~/.claude/observations")
```

**Rule:** For "how/why/what" questions -> RAG first, always.

**Tree-enhanced search:** Use `rag_tree_search` for section-scoped queries (e.g., search within "Authentication" section only). Use `rag_tree_navigate` to browse document outlines.

**Full guide:** `~/.claude/RAG_GUIDE.md`

### RAG Auto-Use Rule

**If `.rag/` exists in project -> use `rag_search` FIRST for any question about the project.**

| When | Action |
|------|--------|
| Questions about project (requirements, decisions, context) | `rag_search` first |
| "How/what/where/why" questions about project | `rag_search` first |
| References to past meetings, docs, specs | `rag_search` first |
| Direct file edits, running commands | Skip RAG |

**Chronology:** Prefer most recent `content_date` when conflicts exist.
**Supersession:** RAG deprioritizes content with strikethrough, "superseded by", or "[deprecated]".

### RAG Reindexing

**Pre-flight:** Before any index operation, verify Ollama is running and `mxbai-embed-large` is responsive:
```bash
curl -sf http://localhost:11434/api/tags | python3 -c "import sys,json; models=[m['name'] for m in json.load(sys.stdin)['models']]; assert any('mxbai-embed-large' in m for m in models)" || echo "FAIL: Ollama/model not ready"
```

| Rule | Details |
|------|---------|
| Token limit | mxbai-embed-large has 512-token context — chunks handled by server, but warn on files >100KB |
| Exclusions | See `~/.claude/config/rag-exclusions.json` (SSOT for all RAG exclusion patterns) |
| Batch reindex | Use `/rag-batch-index` skill (encodes crash resilience + progress tracking) |
| MCP scope | See "MCP Session Scope" section — all MCP tools main-session only |
| Long reindexes | Use background Bash process (`run_in_background: true`), not blocking calls |
| CLI fallback | If MCP tools unavailable: `cd <project> && python3 -m rag_mcp_server.cli index <path>` |

### Observation Memory (Auto-Captured)

Tool usage is automatically captured during sessions and compressed at session end.

| Component | File | Purpose |
|-----------|------|---------|
| Capture | `~/.claude/hooks/observation-logger.sh` | PostToolUse -> JSONL |
| Compress | `~/.claude/hooks/session-compressor.sh` | SessionEnd -> markdown summary |
| Search | `/mem-search` | Progressive disclosure of past sessions |
| Config | `~/.claude/config/observation-config.json` | Feature flags, retention |
| Surfacing | `proactive_rag.py` (4th cascade) | Auto-surfaces at session start |

**Storage:** `~/.claude/observations/` (active-session.jsonl, archive/, summaries/)

**Retention:** 30 days (configurable). Summaries indexed to RAG for semantic search.

### Search-First Workflow

```
1. ctm brief          -> What's my current task?
2. rag_search         -> What does the project know?
3. Grep/Glob          -> Where's the specific code?
4. Read               -> Full file context
```

**Tool selection:** Glob (files) -> Grep (text) -> RAG (concepts) -> Task+Explore (research)

**Full reference:** `~/.claude/docs/SEARCH_COORDINATION.md`

### Project Memory Workflow

1. **Before proposing solutions**: Check `DECISIONS.md` for existing decisions
2. **During conversations**: Offer to record significant decisions (see Decision Auto-Capture)
3. **End of significant sessions**: Summarize key outcomes to `SESSIONS.md`

**Context directory structure:**
```
project/.claude/context/
├── DECISIONS.md     # Architecture decisions (A/T/P/S taxonomy)
├── SESSIONS.md      # Session summaries
├── CHANGELOG.md     # Project evolution
└── STAKEHOLDERS.md  # Key people
```

**Initialize:** Run `memory-init` skill or copy `~/.claude/templates/context-structure/`

### Supersession Pattern

When decisions are replaced:
1. New decision in "Active" section with `**Supersedes**: [old decision ID]`
2. Old decision moved to "Superseded" section with strikethrough
3. Format: `~~A-001: Old decision~~ -> Superseded by A-005`

**Full references:** `~/.claude/CTM_GUIDE.md` | `~/.claude/RAG_GUIDE.md`

### Git Context

| Command | Purpose |
|---------|---------|
| `git-context summary` | Repo state, contributors, active files |
| `git-context recent -n 10` | Recent commits |
| `git-context search "query"` | Search by message/content |
| `git-context file <path>` | File history with diffs |
| `git-context blame <path>` | Author attribution |

---

## Learned Lessons

Auto-extracted knowledge from past conversations. Query when:
- Starting work in a domain with past experience (HubSpot, APIs, etc.)
- Encountering errors or unexpected behavior
- Before implementing patterns that might have known gotchas

```bash
rag_search "query" --project_path ~/.claude/lessons
```

| Score | Meaning | Surfacing |
|-------|---------|-----------|
| >=0.8 | Auto-promoted by recurrence (3+ occurrences) | Always shown |
| 0.70 | First capture (auto-approved) | Shown when relevant |
| 0.5-0.7 | Decayed or legacy | Lower priority |
| <0.5 | Low confidence | Not surfaced |

**Auto-approve:** Lessons start at 0.70, auto-promoted on recurrence via SONA success. **Occurrences** tracked per lesson (dedup by title/signature).

**SONA Formulas:** Success: `min(0.99, c + 0.05*(1-c))` | Failure: `max(0.30, c - 0.10)` | Decay: `-0.01/week` (floor 0.50, auto SessionStart)

**Compiled summaries:** `~/.claude/lessons/compiled/` — domain-grouped markdown (30 groups, auto-generated)

**Full system:** `~/.claude/LESSONS_GUIDE.md`

---

## Search Tool Selection

| Question Type | Tool | Order |
|---------------|------|-------|
| "How does X work?" | RAG -> Grep -> Read | Semantic first |
| "Where is function X?" | Grep -> Read | Pattern first |
| "Which files match X?" | Glob | Pattern only |

---

## Context Management

### Memory Flush (Pre-Compaction)

Before compaction, a memory flush prompt auto-triggers extraction of:
- **Decisions** -> DECISIONS.md or CTM context
- **Learnings** -> CTM learnings
- **Open questions** -> CTM agent context

Respond with `NO_PERSIST` if nothing to extract.

### Tool Result Pruning

Old tool results are pruned based on TTL to save context:

| Tool | TTL | Strategy |
|------|-----|----------|
| Read | 30 min | Soft-trim (keep first/last 300 chars) |
| Grep | 45 min | Soft-trim |
| Glob | 30 min | Hard-clear (placeholder only) |
| Bash | 60 min | Soft-trim |
| WebFetch | 120 min | Soft-trim |

**Protected:** Last 3 assistant messages + their tool results never pruned.

**Config:** `~/.claude/config/pruning.json`

### Context Inspection

Use `/context` to inspect context window usage:

| Command | Shows |
|---------|-------|
| `/context` | Quick summary + top consumers |
| `/context list` | All injected content with sizes |
| `/context detail` | Full breakdown by category |
| `/context trim` | Pruning recommendations |

---

## Auto-Invoke Triggers

**32 auto-invoke agents** — see Proactive Agent Routing table below for triggers.

**Skills:** `solution-architect`, `project-discovery`, `hubspot-specialist`, `pptx`, `doc-coauthoring`, `decision-tracker`, `ctm`, `init-project`, `brand-extract`, `file-inbox-organizer`, `config-audit`, `rename-smart`, `enhance`, `pm-spec`, `pm-decompose`, `pm-gh-sync`, `mem-search`, `status-bundle-update`, `scope-defense-bundle`, `project-completeness-audit`, `slack-sync-ritual`, `post-mortem-analyzer`

**Full catalogs:** `~/.claude/AGENTS_INDEX.md` | `~/.claude/SKILLS_INDEX.md`

### HubSpot Implementation Routing

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
| Reporting, dashboards, analytics | `hubspot-impl-reporting-analytics` |
| Franchise, dealer, B2B2C | `hubspot-impl-b2b2c` |

**Orchestrator:** `~/.claude/agents/hubspot-implementation-runbook.md`

### HubSpot API Routing

Invoke `hubspot-api-specialist` for API questions -> Routes via `hubspot-api-router` to 30+ specialized API agents (`hubspot-api-crm`, `hubspot-api-marketing`, `hubspot-api-cms`, etc.).

### Salesforce-HubSpot Mapping

Invoke `salesforce-mapping-router` -> Routes to:

| Object | Route To |
|--------|----------|
| Contacts/Leads | `salesforce-mapping-contacts` |
| Companies/Accounts | `salesforce-mapping-companies` |
| Deals/Opportunities | `salesforce-mapping-deals` |
| Tickets/Cases | `salesforce-mapping-tickets` |
| Activities (Tasks/Events/Calls) | `salesforce-mapping-activities` |

### Proactive Agent Routing

Invoke proactively when situational triggers match. **All 32 auto-invoke agents:**

| Trigger | Route To |
|---------|----------|
| **Quality & Review** | |
| Before sending client-facing doc/spec/deliverable | `deliverable-reviewer` |
| Generated code, specs, or diagrams may have errors | `error-corrector` |
| Complex output needs 1-page board/exec summary | `executive-summary-creator` |
| **Decisions & Strategy** | |
| Decision with 2+ options and trade-offs to weigh | `decision-memo-generator` |
| Budget/timeline/scope constraints, 80/20 needed | `80-20-recommender` |
| Multi-phase project, "what phase next?", sequencing | `playbook-advisor` |
| **Visualization & Diagrams** | |
| Process map, workflow, swimlane, BPMN diagram | `bpmn-specialist` |
| Entity-relationship diagram, data model design | `erd-generator` |
| Lucidchart-compatible diagram (CSV/API import) | `lucidchart-generator` |
| **Discovery & Research** | |
| New project or domain, "have we done this before?" | `comparable-project-finder` |
| Meeting transcript, Zoom/Teams notes to process | `meeting-indexer` |
| Verify facts/chronology against NotebookLM sources | `notebooklm-verifier` |
| Deep semantic search needing multi-phase RAG cascade | `rag-search-agent` |
| **Deliverables & Proposals** | |
| SOW, RFP response, or full proposal package creation | `proposal-orchestrator` |
| Extract brand (colors, typography, logos) from site/docs | `brand-kit-extractor` |
| **Infrastructure & Context** | |
| Cross-session continuity, "remember when", memory | `memory-management-expert` |
| RAG search quality poor, indexing issues, stale data | `rag-integration-expert` |
| Config wrong, Claude behavior off, capability check | `context-audit-expert` |
| Major task start/switch/complete, ctm commands | `ctm-expert` |
| Complex bug spanning sessions, need persistent debug log | `debugger-agent` |
| HubSpot implementation project kick-off | `hubspot-implementation-runbook` |
| "what depends on", "impact analysis", "dependency graph" | `config-oracle` |
| "orphan detection", "unused agents", "dead hooks", "stale" | `config-oracle` |
| "what breaks if", "safe to remove/delete", "config integrity" | `config-oracle` |
| **Scope & Rescue** | |
| SOW vs delivery delta, scope defense, "SOW said X" | `scope-delta-analyzer` |
| "rescue project", inherited/troubled implementation | `rescue-project-assessor` |
| Go-live readiness, handover, "is everything done?" | `completeness-auditor` |
| "audit workflows", inherited portal, pre-migration | `workflow-auditor` |
| "sync Slack", Slack decisions/blockers into CTM | `slack-ctm-sync` |
| **Token Optimization (auto-delegate)** | |
| Bulk code analysis (>20 files), parallelizable work | `codex-delegate` |
| Bulk summarization, content >1M needing web grounding | `gemini-delegate` |
| Architecture/strategy decision, or 2+ failed attempts | `reasoning-duo` |
| Research + long-context needing Gemini's 2M window | `reasoning-duo-cg` |
| High-stakes decision needing 3-model consensus | `reasoning-trio` |

### Huble Wiki Routing

When user asks about Huble internal processes, policies, or methodology:

| Context | Route To |
|---------|----------|
| Implementation methodology, BPM, phases, badges, SolA | `huble-methodology` |
| Battlecards, quoting, sales onboarding, KAM, partners | `huble-sales` |
| TLO, expenses, client service, SOPs, risk, compliance | `huble-operations` |
| Employee guides, HR, leave, holidays, country policies | `huble-employee-guide` |
| HubSpot features, partner round-ups, product updates | `huble-hubspot-updates` |
| Dev SDLC, QA, cookie consent, email dev, analytics | `huble-dev` |

**Source:** Huble Tettra wiki (846 pages) indexed at `${HUBLE_WIKI_PATH:-~/projects/huble-wiki}/`

### Configuration Audit Routing

When user asks about configuration, capabilities, or validation:

| Context | Route To |
|---------|----------|
| "audit config", "check setup" | `/config-audit` skill or `context-audit-expert` |
| "what can Claude do?", "list capabilities" | `generate-capability-manifest.sh` |
| "broken imports", "validate imports" | `validate-imports.sh` |
| "CLAUDE.md best practices" | `claude-md-expert` |
| "optimize context", "context budget" | `context-audit-expert` |
| "dependency map", "what references X", "full integrity" | `config-oracle` |
| "orphan scan", "component count", "what breaks if" | `config-oracle` |

---

## Past Conversation Access

**I DO have access.** Sources: `project/conversation-history/` (RAG search) | `~/.claude/projects/*/sessions-index.json` (Read tool)

**Search:** "Remember when we..." -> Read sessions-index.json -> find matching session -> Read JSONL

---

## Model Selection

| Model | Use For | Notes |
|-------|---------|-------|
| **Haiku** | Explore agents, file lookups, RAG + light synthesis | |
| **Sonnet** | Code implementation, reviews, Plan agents, docs | |
| **Opus 4.6** | Solution Architect, complex architecture, multi-system integration | 1M context, adaptive thinking, 128K output |

Announce choice: `[Using {model} for: {reason}]`

**Opus 4.6:** Adaptive thinking (auto, replaces budget_tokens). Effort param (API-only): `low`/`medium`/`high`/`max`.

**Auto-selection (CTM):** `ctm complexity` calculates score (0.0-1.0) and recommends model. LOW(<0.4)=haiku, MED(0.4-0.7)=sonnet, HIGH(>0.7)=opus.

**Agent teams (experimental):** `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` enables peer-to-peer multi-agent collaboration. Token-intensive — use for complex tasks only.

---

## Cognitive Delegation Protocol (CDP)

Function-call semantics: Primary writes `HANDOFF.md` -> Spawns agent -> Agent writes `OUTPUT.md` -> Primary reads result only.

**Depth limit:** Max 3 levels. L3 agents cannot spawn.
**Load-aware:** Check `~/.claude/scripts/check-load.sh` before spawning.

**Full reference:** `~/.claude/CDP_PROTOCOL.md` (v2.0 — includes execution strategies + complexity scoring)

---

## MCP Session Scope (Critical)

**MCP tools ONLY work in main session.** Sub-agents cannot access ANY MCP tools.

| Agent Type | MCP Access | Use For |
|------------|------------|---------|
| Main session | Full | RAG ops, Slack, Mermaid, all MCP |
| Task sub-agents | NONE | Code exploration, file analysis, docs |
| Plan agents | NONE | Architecture design, research |
| Workers (CDP) | NONE | Code generation, file edits |

**Before delegating:** Does task need MCP tools (RAG, Slack, Fathom)? If yes → keep in main session.
**Large operations:** Agents explore + analyze (read-only). Main session executes all edits. See `sub-agent-delegation.md` rule.

---

## Token Optimization Cascade

```
1. codex-delegate (bulk code ops) -> 2. gemini-delegate (>1M context only) -> 3. Claude (1M native)
```

Use Codex for bulk analysis. Gemini only for >1M context (Claude handles up to 1M natively). Claude when tools needed or context <=1M.

**Cost awareness:** >200K input tokens = 2x pricing ($10/$37.50 per MTok vs $5/$25). Delegate cost-sensitive bulk work to Codex/Gemini.

**Reasoning agents:** `reasoning-duo` (C+X), `reasoning-duo-cg` (C+G), `reasoning-trio` (all three)

---

## Core Workflows

**External Files:** Copy into project - don't rely on external paths.

**Decision Recording:** When decision made, ask: "Want me to record this to DECISIONS.md?"

**Git Commits:** `git status` + `git diff` -> Draft message (WHY not WHAT) -> Confirm -> Execute with Co-Authored-By.

**Phasing:** Always MVP -> Phase 2 -> Future. Never monolithic.

**80/20:** Quick wins before structural changes.

---

## Deviation Handling

> Auto-loaded from `~/.claude/rules/deviation-handling.md`

---

## File Inbox Organization

Auto-routing for `project/00-inbox/` and `~/.claude/inbox/`. Files are renamed, routed, and RAG-indexed.

| Command | Purpose |
|---------|---------|
| `/inbox` | Process files |
| `/inbox init` | Initialize inbox |

**Full reference:** `~/.claude/prds/PRD-file-inbox-organizer.md`

---

## Decision Auto-Capture

> Auto-loaded from `~/.claude/rules/decision-auto-capture.md`

---

## Resource Management

Switch profiles: `~/.claude/scripts/switch-profile.sh <profile>`

### Quick Commands

```bash
# Check current load + spawning recommendation
~/.claude/scripts/check-load.sh

# Switch resource profiles
~/.claude/scripts/switch-profile.sh balanced     # Default
~/.claude/scripts/switch-profile.sh aggressive    # Higher limits
~/.claude/scripts/switch-profile.sh conservative # Multitasking

# Device info
~/.claude/scripts/detect-device.sh --info
```

### Profiles

| Profile | Max Agents | Load OK | Use When |
|---------|-----------|---------|----------|
| `balanced` | 4 | 8.0 | Default - general work |
| `aggressive` | 6 | 12.0 | Higher limits, more agents |
| `conservative` | 3 | 4.8 | Running other apps |

### Load-Aware Spawning (IMPORTANT)

**NEVER kill running agents** — respect execution order. Instead:

| Status | Action |
|--------|--------|
| `OK` | Spawn freely (parallel allowed) |
| `CAUTION` | Sequential only — wait for completion |
| `HIGH_LOAD` | Work inline — no new agents |
| Agent limit reached | Queue work — don't spawn |

Before spawning agents, check: `~/.claude/scripts/check-load.sh --can-spawn`

### New Device Detection

On new device: run `~/.claude/scripts/detect-device.sh --generate` to create profile.

### Ollama (RAG Embeddings)

| Model | Size | Quality | Recommendation |
|-------|------|---------|----------------|
| `mxbai-embed-large` | 669MB | Best | **Default (all profiles)** |

Install: `ollama pull mxbai-embed-large`

**Full reference:** `~/.claude/RESOURCE_MANAGEMENT.md`

---

## CSB False Positive Handling

False positives are common on: ANSI escape codes (`\u001b`), conversation exports containing tool XML, broad text matches in natural language.

| Situation | Action |
|-----------|--------|
| CSB blocks a tool call | Do NOT spawn sub-agents to retry — they inherit same CSB taint state. Ask user to `csb approve`, then continue in main session |
| Need to proceed after block | Ask user to `csb approve`, then continue in main session |
| Writing content with control chars | Write to temp file first — avoid embedding raw JSON with control chars in heredocs |
| Conversation export triggers HIGH | Expected — scanner has path-based whitelist for `conversation-history/`, `*PreCompact*`, `*.jsonl` |

**Reference:** `~/.claude/docs/CONTENT_SECURITY_BUFFER.md`

---

## Slack Integration (Remote MCP)

**Availability:** Check for `slack_*` tools at session start. Feature flag `tengu_claudeai_mcp_connectors` is Anthropic-controlled and may be off. If unavailable, tell user to restart session. Do NOT debug locally - the flag is server-side.

**When available:** `slack_search_public` (query + `sort=timestamp`, `sort_dir=desc`), `slack_list_channels`, `slack_get_channel_history(channel_id, limit)`, `slack_get_thread_replies(channel_id, thread_ts)`, `slack_send_message(channel_id, text)` (confirm first!), `slack_search_users`, `slack_read_user_profile(user_id)`. Query supports Slack operators: `from:@name`, `in:#channel`, `after:2026-01-01`.

**Full guide:** `~/.claude/docs/SLACK_MCP_GUIDE.md`

---

## External Guides (Read When Needed)

| Topic | Guide |
|-------|-------|
| Search | `docs/SEARCH_COORDINATION.md`, `docs/SEARCH_PATTERNS_INDEX.md` |
| RAG / CTM | `RAG_GUIDE.md`, `CTM_GUIDE.md` |
| Agents / Skills / CDP | `AGENTS_INDEX.md`, `SKILLS_INDEX.md`, `CDP_PROTOCOL.md`, `ASYNC_ROUTING.md` |
| Memory / Decisions | `LESSONS_GUIDE.md`, `PROJECT_MEMORY_GUIDE.md` |
| HubSpot / Resources | `HUBSPOT_IMPLEMENTATION_GUIDE.md`, `RESOURCE_MANAGEMENT.md` |
| Slack / CSB / Binary | `docs/SLACK_MCP_GUIDE.md`, `docs/CONTENT_SECURITY_BUFFER.md`, `BINARY_FILE_REFERENCE.md` |
| Self-healing system | `docs/SELF_HEALING_SYSTEM.md` |
| Full architecture | `CONFIGURATION_GUIDE.md` |

All paths relative to `~/.claude/`.

---

## Agent Cross-Reference System

**Fully automated** - no manual maintenance required.

### How It Works

When agents are created/deleted, a PostToolUse hook automatically:
1. Detects cluster from agent name pattern
2. Updates `~/.claude/config/agent-clusters.json`
3. Updates orchestrator's `delegates_to:` frontmatter
4. Updates all siblings' `## Related Agents` sections

### Cluster Patterns

| Pattern | Cluster | Example |
|---------|---------|---------|
| `^hubspot-impl-` | hubspot-impl | `hubspot-impl-new-hub` |
| `^reasoning-` | reasoning | `reasoning-quad` |
| `(slide-deck\|pitch-deck)` | presentations | `slide-deck-v2` |
| `(erd-\|bpmn-)` | diagrams | `erd-new` |
| `(roi-\|commercial-)` | commercial | `roi-lite` |

### Key Files

| File | Purpose |
|------|---------|
| `~/.claude/config/agent-clusters.json` | Cluster definitions + patterns |
| `~/.claude/hooks/auto-update-crossrefs.sh` | Automation hook |
| `~/.claude/scripts/validate-agent-crossrefs.sh` | Validation |

### When Creating Agents

Name agents to match cluster patterns for auto-grouping. If no pattern matches, agent works standalone.

---

## Utility Scripts

| Script | Purpose |
|--------|---------|
| `validate-setup.sh [--quick]` | Configuration validation / health check |
| `generate-inventory.sh` | Regenerate `inventory.json` (SSOT for counts) |
| `check-load.sh [--can-spawn]` | Load check before agent spawning |
| `enrich-project-memory.sh` | Enrich per-project MEMORY.md with CTM + lessons |

All in `~/.claude/scripts/`. Full list: `ls ~/.claude/scripts/`

---

## Dashboard

**Dashboard:** http://localhost:8420 — RAG search UI, session metrics, agent usage.

**Full reference:** `~/.claude/rag-dashboard/README.md`

---

## Stakeholder Personas

Archetype-specific interaction guides in `~/.claude/personas/`:

| Persona | File | When to Apply |
|---------|------|---------------|
| Client Admin | `client-admin.md` | Writing for client HubSpot power user (Marshall, Christina, Shiraats) |
| Project Manager | `project-manager.md` | Status updates, blocker escalation, timeline discussions |
| Developer | `developer.md` | Technical handoff specs, API briefs, integration docs |
| Executive | `executive.md` | Management pressure response, board presentations, ROI justification |
| External Partner | `external-partner.md` | Vendor coordination, CSM transitions, partner handoffs |
| Predecessor | `predecessor.md` | Inherited/rescue projects, consultant turnover recovery |

**Auto-detect**: When drafting client-facing content, check if target matches a persona archetype and adapt accordingly.

---

