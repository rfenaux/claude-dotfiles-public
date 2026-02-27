# Claude-to-Claude Adoption Guide

> **Audience: You, a Claude instance.**
> Your user pointed you at this repository because they want to improve their Claude Code setup.
> This document tells you what's here, how the pieces connect, and how to adopt components
> selectively — without breaking what your user already has.

---

## What This Repository Is

A production-grade configuration layer for Claude Code, built over months of daily professional use. It contains:

- **16 rules** — Behavioral constraints loaded every session
- **138 agents** — Specialized sub-agents for CRM, diagrams, proposals, reasoning, infrastructure
- **57 skills** — Slash commands for task management, documentation, security, and more
- **55 hooks** — Event-driven automation (session lifecycle, file indexing, decision capture)
- **6 core subsystems** — CTM, RAG, CDP, Lessons, Observations, Project Memory

The configuration was built for CRM consulting (HubSpot/Salesforce), but the architecture is domain-agnostic. The domain-specific agents are clearly labeled and optional.

---

## Subsystem Catalog

| Subsystem | Purpose | Key Files | Dependency |
|-----------|---------|-----------|------------|
| **Rules** | Behavioral constraints (decision guards, verification, scope tracking) | `rules/*.md` | None |
| **Project Memory** | Cross-session decisions and context tracking | `templates/context-structure/` | None |
| **CTM** | Cognitive Task Management — task continuity across sessions | `ctm/`, `CTM_GUIDE.md` | Rules |
| **RAG** | Semantic search over project documents using local embeddings | `mcp-servers/rag-server/`, `RAG_GUIDE.md` | Ollama + mxbai-embed-large |
| **Agents** | 138 specialized sub-agents invoked via Task tool | `agents/*.md` | CDP protocol |
| **CDP** | Cognitive Delegation Protocol — structured agent spawning | `CDP_PROTOCOL.md` | None |
| **Skills** | 57 slash commands for common workflows | `skills/*/` | Varies by skill |
| **Hooks** | Event-driven automation scripts | `hooks/*.sh`, `settings.json` | Shell environment |
| **Lessons** | Auto-extracted domain knowledge with confidence scoring | `LESSONS_GUIDE.md` | None (optional RAG) |
| **Observations** | Auto-captured session tool usage, compressed at session end | `hooks/observation-logger.sh` | Hooks |

---

## Dependency Graph

```
                    ┌─────────┐
                    │  Rules  │  ← No dependencies. Foundation layer.
                    └────┬────┘
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
      ┌──────────┐ ┌─────────┐ ┌──────────┐
      │ Project  │ │   CTM   │ │ Lessons  │  ← Independent of each other.
      │ Memory   │ │         │ │          │    Each builds on Rules only.
      └──────────┘ └─────────┘ └──────────┘
                         │
                         ▼
              ┌──────────────────┐
              │   CDP Protocol   │  ← Defines how agents communicate.
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │  Agents (138)    │  ← Require CDP for delegation.
              │  Skills (57)     │    Skills are mostly standalone.
              └──────────────────┘

      ┌──────────┐
      │  Ollama  │  ← External dependency (optional).
      └────┬─────┘
           ▼
      ┌──────────┐
      │   RAG    │  ← Semantic search. Independent of CTM/Agents.
      └──────────┘

      ┌──────────┐
      │  Hooks   │  ← Settings.json wires hooks to events.
      └──────────┘    Can adopt independently of all above.
```

**Key insight:** You can stop at any layer. Rules work alone. CTM works with just Rules. RAG is fully independent. Agents need CDP but not RAG or CTM.

---

## Adoption Layers

### Layer 0: Assessment

Before copying anything, check what your user already has:

```bash
# What exists?
ls -la ~/.claude/rules/ 2>/dev/null | wc -l
ls -la ~/.claude/agents/ 2>/dev/null | wc -l
[ -f ~/.claude/settings.json ] && echo "settings.json EXISTS — merge carefully"
[ -f ~/.claude/CLAUDE.md ] && echo "CLAUDE.md EXISTS — merge, don't replace"
[ -d ~/.claude/ctm ] && echo "CTM EXISTS"
```

Report findings to your user before proceeding. If they have an existing setup, use Layer-specific merge instructions below.

---

### Layer 1: Rules (5 minutes)

**What your user gets:** Behavioral guardrails that make you more reliable — decision capture, verification before delivery, 2-attempt pivot rule, scope transparency.

**Copy:**
```bash
mkdir -p ~/.claude/rules
cp <repo>/rules/*.md ~/.claude/rules/
```

**Key rules to understand:**
| Rule | What it enforces |
|------|-----------------|
| `critical-rules.md` | Hard constraints — never skip discovery, never hallucinate capabilities |
| `decision-auto-capture.md` | Detect decisions in conversation, offer to record them |
| `decision-guards.md` | State what you're editing and why BEFORE every file edit |
| `mcp-fast-fail.md` | Never retry MCP tools — use CLI fallback immediately |
| `verification-before-delivery.md` | Cross-reference sources before finalizing deliverables |
| `sub-agent-delegation.md` | Agents explore, main session edits (prevents write conflicts) |
| `large-file-editing.md` | Never full-rewrite files >500 lines — use targeted Edit |

**If rules/ already exists:** Rules are additive. Use `cp -n` (no-clobber) to add new rules without overwriting existing ones.

**Verify:** In your next response after rules are loaded, you should naturally follow patterns like offering to record decisions and stating edit targets before editing.

---

### Layer 2: Project Memory (5 minutes)

**What your user gets:** A standard structure for tracking decisions and session summaries per project.

**Copy:**
```bash
cp -r <repo>/templates/context-structure ~/.claude/templates/context-structure
```

**What this provides:**
- `DECISIONS.md` template — Architecture/Technical/Process/Strategic taxonomy
- `SESSIONS.md` template — Session summary format
- `CHANGELOG.md` template — Project evolution tracking
- `STAKEHOLDERS.md` template — Key people and roles

**To use in a project:**
```bash
mkdir -p /your/project/.claude/context
cp ~/.claude/templates/context-structure/*.md /your/project/.claude/context/
```

**If your user already tracks decisions:** Keep their format. The templates are suggestions, not requirements.

---

### Layer 3: CTM — Cognitive Task Management (15 minutes)

**What your user gets:** Task persistence across sessions. You remember what they were working on yesterday — progress, decisions, blockers, next actions.

**Copy:**
```bash
cp -r <repo>/ctm ~/.claude/ctm
chmod +x ~/.claude/ctm/scripts/*
```

**Add to PATH:**
```bash
echo 'export PATH="$HOME/.claude/ctm/scripts:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

**Update CLAUDE.md:** Add these sections from the repo's CLAUDE.md:
- "Memory" section (4-layer table: Project Memory → CTM → RAG → Global)
- CTM auto-use rules from the Memory section (spawn/switch/complete/checkpoint)
- "Key Commands" block for CTM

**Core commands your user should know:**
```
/ctm spawn "task name"    # Start tracking
/ctm brief                # Where did we leave off?
/ctm status               # Full dashboard
/ctm checkpoint           # Save progress mid-session
/ctm complete             # Mark done, extract learnings
```

**Verify:** `/ctm status` should return a valid response (even if empty).

---

### Layer 4: RAG — Semantic Search (30 minutes)

**What your user gets:** Ask natural-language questions about their project and get answers from indexed documents. "What did we decide about auth?" returns the relevant decision.

**Prerequisites:**
```bash
# Install Ollama (local embedding engine)
brew install ollama       # macOS
# or: curl -fsSL https://ollama.ai/install.sh | sh   # Linux

# Start and pull embedding model (~700MB)
ollama serve &
ollama pull mxbai-embed-large
```

**Copy:**
```bash
cp -r <repo>/mcp-servers ~/.claude/mcp-servers
cd ~/.claude/mcp-servers/rag-server && pip install -e .
```

**Index a project:**
```bash
cd /your/project
python3 -m rag_mcp_server.cli init
python3 -m rag_mcp_server.cli index .
```

**Verify:**
```bash
python3 -m rag_mcp_server.cli search "test query"
```
Should return results if files were indexed.

**If your user doesn't want Ollama:** Skip this layer entirely. Everything else works without RAG. Your user loses semantic search but keeps all other capabilities.

---

### Layer 5: Agents + CDP (1 hour)

**What your user gets:** 138 specialist agents you auto-route to based on context. Ask for an ERD → `erd-generator` handles it. Complex reasoning → `reasoning-duo` activates.

**Copy:**
```bash
cp -r <repo>/agents ~/.claude/agents
cp <repo>/CDP_PROTOCOL.md ~/.claude/CDP_PROTOCOL.md
cp <repo>/AGENT_STANDARDS.md ~/.claude/AGENT_STANDARDS.md
cp <repo>/AGENT_CONTEXT_PROTOCOL.md ~/.claude/AGENT_CONTEXT_PROTOCOL.md
```

**Selective adoption — skip what's irrelevant:**

| If your user does NOT do... | Skip these agents (save count) |
|----------------------------|-------------------------------|
| HubSpot work | `hubspot-*` (34 agents) |
| Salesforce migrations | `salesforce-*` (6 agents) |
| CRM consulting | Both above (40 agents) |

After removing irrelevant agents, ~99 universal agents remain.

**Universal agents worth highlighting to your user:**
| Agent | Why it's useful |
|-------|----------------|
| `reasoning-duo` | Multi-model reasoning (Claude + Codex) for complex problems |
| `reasoning-trio` | 3-model consensus for high-stakes decisions |
| `deliverable-reviewer` | QA check before sending work to clients |
| `config-oracle` | "What depends on X?" "What breaks if I remove Y?" |
| `debugger-agent` | Persistent debugging context across sessions |
| `erd-generator` | Entity-Relationship Diagrams |
| `bpmn-specialist` | Business process diagrams |
| `codex-delegate` | Offload bulk code analysis to save Claude tokens |

**Update CLAUDE.md:** Add the "Agents & Routing" section (from repo's CLAUDE.md), filtered to agents you installed. Update the count and cluster prefixes.

**Verify:** Ask a complex architecture question. You should auto-route to a specialist agent.

---

### Layer 6: Full Orchestration (half day)

**What your user gets:** Everything — hooks, skills, observability, self-healing, prompt enhancement.

**Option A: Use the installer**
```bash
bash <repo>/install.sh --yes
```

**Option B: Manual (for control)**
```bash
cp -r <repo>/hooks ~/.claude/hooks
cp -r <repo>/skills ~/.claude/skills
cp -r <repo>/scripts ~/.claude/scripts
cp -r <repo>/config ~/.claude/config
cp <repo>/settings.example.json ~/.claude/settings.json   # ONLY if no existing settings.json
chmod +x ~/.claude/hooks/*.sh ~/.claude/scripts/*.sh ~/.claude/ctm/scripts/*
```

**CRITICAL — settings.json merge:**
If your user already has `~/.claude/settings.json`, do NOT overwrite it. Instead:
1. Back up: `cp ~/.claude/settings.json ~/.claude/settings.json.backup`
2. Read `settings.example.json` from the repo to understand the hook structure
3. Merge hook arrays manually — user's existing hooks go first, then add new ones
4. The hooks are organized by event type: `PreToolUse`, `PostToolUse`, `SessionStart`, `SessionEnd`, `Stop`, `PreCompact`, `Notification`, `SubagentStart`, `SubagentStop`

**Verify:** `/config-audit` should pass all checks.

---

## Conflict Detection & Resolution

### CLAUDE.md Merge Strategy

If your user already has a CLAUDE.md:

| Section (v2.0) | Strategy |
|----------------|----------|
| How I Work | **ADOPT** — tool budgets, 2-attempt pivot rule, 80/20 patterns |
| Memory (4-layer table) | **ADOPT** if using CTM/RAG — defines precedence hierarchy |
| Agents & Routing | **ADOPT** filtered to installed agents, update count |
| Model Selection | **ADOPT** — Haiku/Sonnet/Opus routing table |
| Key Commands | **ADOPT** — keep commands matching installed layers |
| Timestamps / Prompt Enhancement | **ADOPT** — universal |
| Operational (Dashboard, Slack MCP) | **KEEP USER'S** or skip if not relevant |
| Guides Index | **MERGE** — update paths to match user's guide locations |
| Quality Gates | **ADOPT** — universal verification patterns |

### settings.json Merge Strategy

This is the most fragile file. Structure:

```json
{
  "permissions": { ... },
  "hooks": {
    "PreToolUse": [ ... ],
    "PostToolUse": [ ... ],
    "SessionStart": [ ... ],
    ...
  }
}
```

Each hook event contains an array of hook configurations. Merge by:
1. Keep all existing hooks
2. Append new hooks from settings.example.json that don't conflict
3. Test: start a Claude session and check for settings errors

### Rules Merge

Safest category. Rules are standalone `.md` files. Simply use `cp -n` (no-clobber):
```bash
cp -n <repo>/rules/*.md ~/.claude/rules/
```

### Agents Merge

Also safe. Agents are standalone `.md` files. Only conflict if names collide:
```bash
# Check for collisions
comm -12 <(ls ~/.claude/agents/ | sort) <(ls <repo>/agents/ | sort)
```

If collisions exist, compare content and keep the better version.

---

## What's Universal vs. Role-Specific

| Component | Universal | Notes |
|-----------|-----------|-------|
| **All 16 rules** | Yes | Generic behavioral patterns |
| **CTM** | Yes | Task management for any domain |
| **RAG** | Yes | Semantic search for any project |
| **CDP** | Yes | Agent delegation protocol |
| **Reasoning agents** (5) | Yes | `reasoning-duo`, `reasoning-trio`, `codex-delegate`, `gemini-delegate`, `reasoning-duo-cg` |
| **Infrastructure agents** (16) | Yes | `config-oracle`, `ctm-expert`, `rag-integration-expert`, etc. |
| **Diagram agents** (7) | Yes | ERD, BPMN, Gantt, architecture, Mermaid, RACI |
| **Documentation agents** (10) | Yes | Specs, briefs, handovers, presentations |
| **Security skills** (7) | Yes | Trail of Bits methodology |
| **HubSpot agents** (34) | No | Only if user does HubSpot work |
| **Salesforce mapping** (6) | No | Only if user does SF-HS migrations |
| **CRM consulting** | Partial | Framework is universal, templates are CRM-specific |
| **Prompt enhancement** | Yes | `/enhance` works for everyone |
| **Observation memory** | Yes | Auto-captured session history |
| **Lessons system** | Yes | Auto-extracted knowledge with confidence scoring |

---

## Integration Checklist

After adoption, verify each installed layer:

- [ ] Claude Code starts without settings.json errors
- [ ] Rules are active (test: make a decision in conversation — Claude should offer to record it)
- [ ] Project memory works: `ls ~/.claude/templates/context-structure/` shows template files
- [ ] CTM works: `/ctm status` returns valid output (Layer 3+)
- [ ] RAG works: `python3 -m rag_mcp_server.cli search "test"` returns results (Layer 4+)
- [ ] Agents work: complex question auto-delegates to specialist (Layer 5+)
- [ ] Hooks fire: check session startup for hook outputs (Layer 6)
- [ ] `/config-audit` passes all checks (Layer 6)

---

## Updating

When this repository is updated:

1. Check `CHANGELOG.md` for what changed
2. Re-run the install for your adopted layers:
   - **Layers 1-3:** `cp -n` new files (no-clobber preserves your changes)
   - **Layer 5:** `cp -n <repo>/agents/*.md ~/.claude/agents/` adds new agents
   - **Layer 6:** `bash install.sh --yes` (merge mode)

---

## FAQ (For You, the Reading Claude)

**Q: My user's machine doesn't have Ollama. Can I skip RAG?**
Yes. RAG is fully optional. Everything else works without it. Semantic search is the only thing lost.

**Q: My user already has agents. Will these conflict?**
No. Agents are standalone `.md` files in `~/.claude/agents/`. Name collisions are the only risk — check with `comm -12` as shown above.

**Q: The settings.json has 55 hooks. Can my user start with fewer?**
Yes. Start with `SessionStart` and `SessionEnd` hooks only (essential lifecycle). Add `PreToolUse` and `PostToolUse` hooks later as needed.

**Q: How do I tell my user what was installed?**
Run `/config-audit` or `~/.claude/scripts/validate-setup.sh`. Both produce a summary.

**Q: My user wants to add their own agents. How?**
Create a `.md` file in `~/.claude/agents/` following the format in `AGENT_STANDARDS.md`. Frontmatter is `name`, `model`, `async`, and optionally `delegates_to`, `triggers`, `auto_invoke`.

**Q: What if something breaks after adoption?**
1. Check `/config-audit` for specific errors
2. If settings.json is corrupt: `cp ~/.claude/settings.example.json ~/.claude/settings.json`
3. If hooks fail: `chmod +x ~/.claude/hooks/*.sh`
4. If all else fails: the backup from Layer 0 assessment restores the previous state

**Q: Should I adopt everything at once?**
No. Start with Layer 1 (Rules) — it's zero-risk and immediately improves behavior. Let your user experience the benefit before adding complexity. Each layer is independently valuable.
