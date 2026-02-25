# Memory System

## Memory Stack

```
AUTO MEMORY  - ~/.claude/memory/                Global patterns (auto-injected, first 200 lines)
             + enrich-project-memory.sh         CTM + lessons -> per-project context (SessionStart)
CTM          - ~/.claude/ctm/                   Cognitive task management
RAG          - project/.rag/                    Semantic search + tree navigation + knowledge graph
OBSERVATIONS - ~/.claude/observations/          Session observation memory (auto-captured)
PROJECT MEM  - project/.claude/context/         Decisions, sessions
```

## Quick Commands

- Setup: `claude --init` (new project) | `claude --maintenance` (health check)
- CTM: `ctm status` | `ctm brief` | `ctm spawn "task"` | `ctm complete` | `ctm checkpoint`
- CTM v3: `ctm deadline <id> +3d` | `ctm block <id> --by <blocker>` | `ctm progress <id>`
- RAG: `rag init` | `rag index <path>` | `rag reindex` | `rag search "query"` | `rag status`
- Observations: `/mem-search` | `/mem-search "query"` | `/mem-search stats`
- PM: `/pm-spec` | `/pm-decompose` | `/pm-gh-sync`

## CTM Auto-Use Rules

| Situation | Action |
|-----------|--------|
| User starts major new task | `ctm spawn "<task>" --switch` |
| User says "work on X" / "switch to" | `ctm switch` to matching task |
| User says "done" / "complete" / "finished" | `ctm complete` with auto-extraction |
| Significant decision made | `ctm context add --decision "..."` |
| Before long break / session end | `ctm checkpoint` |
| Task has deadline mentioned | `ctm deadline <id> +Nd` or ISO date |
| Task depends on another | `ctm spawn "task" --blocked-by <id>` |
| Starting implementation project | `ctm spawn "Project" --template hubspot-impl` |

**Trigger phrases:** "Let's work on...", "Switch to...", "Pause this", "This is done", "What was I working on?"

## RAG Rules

**If `.rag/` exists in project -> use `rag_search` FIRST for any question about the project.**

| When | Action |
|------|--------|
| Questions about project (requirements, decisions, context) | `rag_search` first |
| "How/what/where/why" questions about project | `rag_search` first |
| References to past meetings, docs, specs | `rag_search` first |
| Direct file edits, running commands | Skip RAG |

**Search Order:**
1. Lessons (`~/.claude/lessons`) — domain knowledge
2. Config (`~/.claude`) — agents, skills
3. Org wiki (optional — set `ORG_WIKI_PATH`) — methodology
4. Project-specific — current project `.rag/`
5. Observations (`~/.claude/observations`) — session memory

**Chronology:** Prefer most recent `content_date` when conflicts exist.

**Pre-flight (before indexing):**
```bash
curl -sf http://localhost:11434/api/tags | python3 -c "import sys,json; models=[m['name'] for m in json.load(sys.stdin)['models']]; assert any('mxbai-embed-large' in m for m in models)" || echo "FAIL: Ollama/model not ready"
```

## Auto Memory

MEMORY.md auto-injected from project memory directories (first 200 lines).

| Location | Path | Scope |
|----------|------|-------|
| Global SSOT | `~/.claude/memory/MEMORY.md` | Synced to all projects |
| Per-project | `~/.claude/projects/<path>/memory/MEMORY.md` | Auto-injected |

## Project Memory

```
project/.claude/context/
├── DECISIONS.md     # Architecture decisions (A/T/P/S taxonomy)
├── SESSIONS.md      # Session summaries
├── CHANGELOG.md     # Project evolution
└── STAKEHOLDERS.md  # Key people
```

**Supersession:** New decision supersedes old → old gets strikethrough, new links via `**Supersedes**: [old ID]`

## Learned Lessons

Auto-extracted knowledge. Score >=0.8 always surfaced, 0.70 when relevant, <0.5 not surfaced.

```bash
rag_search "query" --project_path ~/.claude/lessons
```

**Full guides:** `CTM_GUIDE.md` | `RAG_GUIDE.md` | `LESSONS_GUIDE.md` | `PROJECT_MEMORY_GUIDE.md`
