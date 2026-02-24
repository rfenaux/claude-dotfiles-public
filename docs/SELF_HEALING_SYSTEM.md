# Self-Healing, Self-Monitoring & Self-Improving System

> Architecture reference for Claude Code's autonomous configuration management.
> Built: 2026-02-11 to 2026-02-13 | 3 phases, 15+ files

---

## Overview

The system operates in three layers:

```
Layer 1: HEAL    — Detect failures, restart services, auto-fix known issues
Layer 2: ANALYZE — Weekly/monthly reports, tool effectiveness, agent routing
Layer 3: IMPROVE — Config auto-tuning, predictive optimization, routing learning
```

All components are fail-silent, rate-limited, and non-destructive by default.

---

## Layer 1: Self-Healing (Auto-Heal)

### Service Health & Auto-Restart

| Component | File | Trigger |
|-----------|------|---------|
| Service checker | `hooks/auto-heal-services.sh` | SessionStart (once) |
| RAG reindexer | `hooks/auto-reindex-stale.sh` | SessionStart (once) |
| Healing summary | `hooks/healing-summary.sh` | SessionStart (once) |
| Failure learning | `hooks/failure-learning.sh` | PostToolUseFailure |

**Behavior:**
- Checks Ollama, RAG MCP, Dashboard on every session start
- Restarts dead services automatically
- Logs restarts to `logs/self-healing/service-restarts.jsonl`
- Reindexes stale RAG documents (>7 days since last index)
- Surfaces healing summary: "Services restarted: X; Failures escalated: Y"

### Failure Pattern Detection

| Component | File | Trigger |
|-----------|------|---------|
| Failure logger | `hooks/failure-learning.sh` | PostToolUseFailure |
| Failure escalation | `scripts/escalate-failures.py` | SessionStart (once) |

**Behavior:**
- Every tool failure is logged with signature hash to `logs/self-healing/failure-catalog.jsonl`
- Signatures group identical failures (same tool + truncated input)
- `escalate-failures.py` checks: if signature repeats >5x in 7 days, writes to escalation log
- Escalated failures surface in weekly report recommendations

---

## Layer 2: Self-Monitoring (Analyze)

### Weekly Analysis Report

**File:** `scripts/analyze-weekly.py`
**Output:** `metrics/weekly-{date}.md`
**Trigger:** `hooks/auto-weekly-report.sh` (SessionStart, once, rate-limited 1/day)

**Sections generated:**

| Section | What it shows |
|---------|---------------|
| Tool Usage | Top 15 tools by call count and percentage |
| Agent Routing | Agent spawn counts, distribution |
| Repeat Failures | Top 5 failure signatures with counts |
| Hot Files | Top 10 most-accessed files |
| Self-Healing Activity | Service restarts, failure escalations |
| Session Metrics | Avg tool calls, duration, agent spawns per session |
| **Tool Effectiveness** | Success rate x log2(frequency) score per tool |
| **Agent Routing Analysis** | Co-occurrence pairs, model distribution |
| **Config Suggestions** | Data-driven tuning recommendations |
| **Failure Trends** | Week-over-week acceleration/resolution |
| **Session Anomalies** | Statistical outliers (>2 sigma) |

Sections in **bold** were added in Phase 2B/3.

### Monthly Health Report

**File:** `scripts/monthly-health-report.py`
**Output:** `metrics/monthly-{YYYY-MM}.md`
**Trigger:** `hooks/auto-monthly-report.sh` (SessionStart, once, rate-limited 1/day, >30 days between reports)

**Sections generated:**

| Section | What it shows |
|---------|---------------|
| Agent Utilization | Defined vs used agents, utilization %, never-spawned list |
| Hook Performance | Hook counts per event, SessionStart budget estimate |
| Lesson Health | Confidence distribution (high/medium/low), average |
| Storage Audit | Size per directory (agents, ctm, lessons, logs, etc.) |
| Config Coherence | Cross-config conflict detection |

### Session Metrics Collection

**File:** `hooks/session-metrics-collector.sh`
**Trigger:** SessionEnd
**Output:** `logs/session-metrics.jsonl`

Captures per-session: tool call counts, duration, agent spawns, files modified.

### Observation Memory

**File:** `hooks/observation-logger.sh`
**Trigger:** PostToolUse, PostToolUseFailure
**Output:** `observations/active-session.jsonl` -> compressed at SessionEnd

---

## Layer 3: Self-Improving (Optimize)

### Config Auto-Tuner

**File:** `scripts/auto-tune-config.py`
**Usage:** Manual only — `python3 auto-tune-config.py [--apply]`

**Behavior:**
- Reads "Config Suggestions" table from latest weekly report
- Validates each suggestion against `config/self-improvement.json`:
  - Must be a listed `tunable_param`
  - Change must not exceed `max_change_percent` (50%)
- `--dry-run` (default): Shows proposed changes
- `--apply`: Backs up config, applies changes, logs to `logs/self-healing/config-tuning.jsonl`

**Tunable parameters:** pruning TTLs, observation retention, self-healing rate limits.

### Agent Routing Learning

| Component | File | Purpose |
|-----------|------|---------|
| Tracker | `lib/intent_predictor.py` | Records agent spawns with context keywords |
| Logger hook | `hooks/subagent-logger.sh` | Feeds spawns to tracker (async, fire-and-forget) |
| Pattern store | `intent-agent-patterns.json` | Context keywords, co-occurrence, type mapping |

**Behavior:**
- Every agent spawn is logged with: agent_type, context keywords, model, timestamp
- Co-occurrence tracked in 10-minute windows (proxy for same session)
- `get_agent_recommendations(context)` scores agents by keyword overlap + frequency
- Data feeds into weekly report "Agent Routing Analysis" section

### Predictive Pre-Warming

**File:** `hooks/pre-warm-context.sh`
**Trigger:** SessionStart (once)

**Behavior:**
- Reads hot files from latest weekly report
- Checks CTM working memory for active task's project path
- If active task found: filters hot files to that project (task-aware pre-warming)
- Falls back to global hot files if no task match
- Output: `[Pre-warm] Task files: file1, file2, ...`

### Lesson Confidence Decay

**File:** `lessons/scripts/confidence.py decay`
**Trigger:** SessionStart (once)

- SONA decay: -0.01/week, floor 0.50
- Keeps lesson corpus fresh — unused lessons gradually fade
- Recurrence (SONA success) boosts back: `min(0.99, c + 0.05*(1-c))`

### Proactive Agent Routing (CLAUDE.md)

All 26 auto-invoke agents now have specific trigger phrases in the Proactive Agent Routing table, grouped into 7 clusters:

1. **Quality & Review** — deliverable-reviewer, error-corrector, executive-summary-creator
2. **Decisions & Strategy** — decision-memo-generator, 80-20-recommender, playbook-advisor
3. **Visualization & Diagrams** — bpmn-specialist, erd-generator, lucidchart-generator
4. **Discovery & Research** — comparable-project-finder, meeting-indexer, notebooklm-verifier, rag-search-agent
5. **Deliverables & Proposals** — proposal-orchestrator, brand-kit-extractor
6. **Infrastructure & Context** — memory-management-expert, rag-integration-expert, context-audit-expert, ctm-expert, debugger-agent, hubspot-implementation-runbook
7. **Token Optimization** — codex-delegate, gemini-delegate, reasoning-duo, reasoning-duo-cg, reasoning-trio

---

## Configuration Files

| File | Purpose |
|------|---------|
| `config/self-improvement.json` | Thresholds, tunable params, max change limits |
| `config/observation-config.json` | Observation capture feature flags, retention |
| `config/pruning.json` | Tool result TTLs for context management |

---

## Data Flow

```
SessionStart
  ├── auto-heal-services.sh     → restart dead services
  ├── auto-reindex-stale.sh     → reindex stale RAG docs
  ├── escalate-failures.py      → check failure patterns
  ├── confidence.py decay       → decay lesson scores
  ├── pre-warm-context.sh       → surface hot files (task-aware)
  ├── auto-weekly-report.sh     → generate weekly report (if stale)
  └── auto-monthly-report.sh    → generate monthly report (if >30d)

During Session
  ├── observation-logger.sh     → log every tool use
  ├── failure-learning.sh       → log + learn from failures
  ├── subagent-logger.sh        → log agent spawns → intent_predictor
  └── pattern-tracker.sh        → track tool usage patterns

SessionEnd
  ├── session-metrics-collector.sh → capture session stats
  └── session-compressor.sh        → compress observations

Manual
  └── auto-tune-config.py --apply  → apply config suggestions
```

---

## Key Design Principles

1. **Fail-silent** — Every component uses `set -euo pipefail` with `|| true` fallbacks
2. **Rate-limited** — Lock files in `/tmp/` prevent over-execution (1/day for reports)
3. **Non-destructive** — Auto-tuner requires explicit `--apply`; default is dry-run
4. **Graceful degradation** — Reports show "Collecting data (N/10 sessions)" below threshold
5. **Async** — Agent tracking is fire-and-forget background process
6. **Append-only logging** — All logs are JSONL append; no overwrites
7. **Single integration point** — All analysis flows through `analyze-weekly.py`
