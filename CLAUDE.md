# Claude Code Configuration

> v2.0 | Behavioral rules: auto-loaded from `rules/` | Full config: `CONFIGURATION_GUIDE.md`

## How I Work

**Default to action.** Start executing within the first response.

| Task Type | Tool Budget | Pattern |
|-----------|-------------|---------|
| Simple edit/fix | 1 Read + 1 Edit | Read → Edit → Done |
| Feature addition | 1-2 Read + implement | Read target + related → Write/Edit |
| Investigation/debug | 2 Grep/Read + act | 2 searches → hypothesis → fix |
| Uncertain/ambiguous | 1 AskUserQuestion | Ask > explore (1 call > 5 calls guessing) |

- **2-attempt pivot rule:** Approach fails? Try ONE variation. Fails again? Pivot. Announce: what failed, why switching.
- **80/20 always.** Quick wins before structural changes.
- **Phasing:** MVP → Phase 2 → Future. Never monolithic.
- **ADHD support:** Detect drift → offer to park or re-anchor. `/focus` commands.
- **External files:** Copy into project — don't rely on external paths.
- **Decision recording:** When decision made, offer: "Record to DECISIONS.md?"
- **Git commits:** `git status` + `git diff` → Draft WHY message → Confirm → Execute with Co-Authored-By.

---

## Memory

4 layers with explicit precedence (higher wins):

| Layer | Source | Use |
|-------|--------|-----|
| 1 (highest) | Project Memory `.claude/context/` | Decisions, sessions, stakeholders |
| 2 | CTM `~/.claude/ctm/` | Task state, blockers, progress |
| 3 | RAG `project/.rag/` | Semantic search over project docs |
| 4 | Global Memory `~/.claude/memory/` + lessons | Patterns, learned knowledge |

Built-in auto-memory supplements but never overrides the above.

**RAG first:** If `.rag/` exists → `rag_search` FIRST for any project question.

**CTM auto-use:** Major new task → `ctm spawn`. "Work on X" → `ctm switch`. "Done" → `ctm complete`. Before breaks → `ctm checkpoint`.

**RAG search order:** lessons → config → project → observations.

Guides: `CTM_GUIDE.md` | `RAG_GUIDE.md` | `PROJECT_MEMORY_GUIDE.md`

---

## Agents & Routing

138 agents in clusters. Registry: `AGENTS_INDEX.md` (full catalog).

Route by cluster prefix: `hubspot-impl-*` → HubSpot Implementation | `hubspot-api-*` → HubSpot API | `salesforce-mapping-*` → Salesforce | `reasoning-*` → Multi-model reasoning

**Auto-invoke triggers:** deliverable-reviewer (before client delivery), decision-memo-generator (2+ options with trade-offs), bpmn-specialist (process diagrams), comparable-project-finder (new domain), proposal-orchestrator (SOW/RFP), codex-delegate (bulk code >20 files), reasoning-duo (architecture/strategy or 2+ failures).

Full routing table: `CONFIGURATION_GUIDE.md#agent-routing`

---

## Model Selection

| Model | Use For |
|-------|---------|
| Haiku 4.5 | Explore agents, file lookups, light synthesis |
| Sonnet 4.6 | Code, reviews, Plan agents, docs |
| Opus 4.6 | Solution architecture, complex multi-system integration |

Announce: `[Using {model} for: {reason}]`

**Token cascade:** codex-delegate (bulk) → gemini-delegate (>1M context only) → Claude (≤1M native).

---

## Key Commands

`ctm status` | `ctm brief` | `ctm spawn` | `ctm checkpoint` | `rag search` | `rag reindex`
`/dispatch` | `/enhance` | `/focus` | `/context` | `/config-audit` | `/decision-sync`

---

## Timestamps

**Default ON.** When `[TIMESTAMP: ...]` in context → start response with `_HH:MM:SS_`

---

## Prompt Enhancement

**Default ON.** `/enhance` status | `go`/`y` execute enhanced | `original` execute as-is

Excluded: single-word approvals, `/commands`, messages <10 chars.

---

## Operational

**Dashboard:** http://localhost:8420 (RAG search UI)

**Slack MCP:** Check for `slack_*` tools at session start. If unavailable, restart session.

---

## Guides Index

| Topic | Guide |
|-------|-------|
| Full config, routing, commands | `CONFIGURATION_GUIDE.md` |
| Task management | `CTM_GUIDE.md` |
| Semantic search | `RAG_GUIDE.md` |
| Agent delegation | `CDP_PROTOCOL.md` |
| Memory & decisions | `PROJECT_MEMORY_GUIDE.md` |
| Async agent routing | `ASYNC_ROUTING.md` |
| Slack MCP | `docs/SLACK_MCP_GUIDE.md` |
| CSB | `docs/CONTENT_SECURITY_BUFFER.md` |
| Self-healing | `docs/SELF_HEALING_SYSTEM.md` |
| Process management | `docs/process-management.md` |
| Hook development | `docs/hook-development.md` |

---

## Quality Gates

Before finalizing output:
1. Derived data matches primary sources
2. Architectural claims cite specific files: `[VERIFIED: file:line]` or `[ASSUMED: needs verification]`
3. Decisions include: VALID IF / REVISIT IF / DEPENDS ON
4. Sub-agent returns use structured output contracts
5. Bulk edits confirmed via grep (zero old pattern instances)
6. Context confirmed ("Test portal, correct?") before execution
