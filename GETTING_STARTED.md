# Getting Started

You've installed the config. Here's what to do next.

## Step 1: Verify Installation (2 minutes)

Start a Claude session and run:

```
/config-audit
```

This checks that settings.json is valid, hooks are executable, and core files are present. Fix anything it flags before continuing.

**Check Ollama** (needed for RAG semantic search):
```bash
ollama serve &          # start if not running
ollama list             # should show mxbai-embed-large
```

If mxbai-embed-large isn't listed: `ollama pull mxbai-embed-large`

## Step 2: Learn Core Commands

These are the commands you'll use most:

| Command | What it does | When to use |
|---------|-------------|-------------|
| `/ctm spawn "task"` | Start tracking a task | Beginning of any new work |
| `/ctm brief` | See where you left off | Start of every session |
| `/ctm status` | Full task dashboard | Check progress |
| `/ctm complete` | Mark task done | When finished |
| `/enhance` | Toggle prompt enhancement | On by default |
| `/config-audit` | Health check | When things feel broken |
| `/init-project` | Set up Claude for a project | First time in any repo |
| `/mem-search` | Search past sessions | "What did I do last week?" |

## Step 3: Set Up Your First Project

Navigate to any project and initialize:

```bash
cd /your/project
claude
```

Then in the session:

```
/init-project
```

This creates:
- `.claude/context/DECISIONS.md` — Architecture decisions
- `.claude/context/SESSIONS.md` — Session summaries
- `.rag/` — Semantic search index (if Ollama is running)

**Index your existing docs:**
```
rag index .
```

Now you can ask questions like "what did we decide about authentication?" and get answers from your project files.

## Adoption Tiers

### Tier 1: Essential (active after install)

**What's working:**
- 20 rules auto-loaded every session (decision guards, verification, scope transparency)
- CLAUDE.md directing session behavior (execution directness, 2-attempt pivot rule)
- Project memory templates available (`/memory-init`)

**How to verify:** Start a session. Claude should follow the rules — e.g., asking before making assumptions, offering to record decisions.

**What to try:**
```
"We decided to use JWT for auth"
```
Claude should offer: "Want me to record this to DECISIONS.md?"

### Tier 2: Recommended (CTM + hooks + key agents)

**What's working (in addition to Tier 1):**
- CTM tracks tasks across sessions
- 57 hooks automate common patterns (auto-index, decision capture, session logging)
- Key agents available: `reasoning-duo`, `deliverable-reviewer`, `config-oracle`

**Setup:**
```bash
# Add CTM to your PATH
echo 'export PATH="$HOME/.claude/ctm/scripts:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

**What to try:**
```
/ctm spawn "implement auth module"
# ... work on it ...
/ctm checkpoint
# ... next session ...
/ctm brief    # Claude remembers where you left off
```

### Tier 3: Power User (RAG + full agents + CDP)

**What's working (in addition to Tier 2):**
- RAG semantic search across all indexed projects
- 139 agents auto-route based on context
- CDP enables multi-agent parallel work
- Observability scripts track skill effectiveness and preference violations

**Setup:**
```bash
# Ensure Ollama is running
ollama serve &
ollama pull mxbai-embed-large

# Index a project
cd /your/project
python3 -m rag_mcp_server.cli index .
```

**What to try:**
```
"What did we decide about the database schema?"     # RAG search
"Create an ERD for the user management system"       # Auto-routes to erd-generator
"Review this spec for completeness"                  # Auto-routes to deliverable-reviewer
```

## Customization

### Adding your own rules
Create a `.md` file in `~/.claude/rules/`. It's auto-loaded every session.

### Adding your own agents
Create a `.md` file in `~/.claude/agents/` with frontmatter:
```yaml
---
name: my-agent
model: sonnet
---
```
See `AGENT_STANDARDS.md` for the full specification.

### Modifying CLAUDE.md
Edit freely, but understand the sections:
- **Partnership** — Your working style preferences (customize this)
- **Execution Directness** — Universal patterns (keep as-is unless you disagree)
- **Features/Memory/Rules** — Reference sections (update if you add/remove subsystems)

### What NOT to touch
- `settings.json` hook structure — use `settings.example.json` as reference
- Hook scripts in `hooks/` — they have circuit breaker patterns; editing carelessly can break the chain

## FAQ

**Q: Hooks not running?**
A: `chmod +x ~/.claude/hooks/*.sh ~/.claude/scripts/*.sh`

**Q: RAG returns nothing?**
A: Check: `ollama list` (model present?), `python3 -m rag_mcp_server.cli status` (index exists?)

**Q: Too many agents? Can I disable some?**
A: Delete agent `.md` files you don't need from `~/.claude/agents/`. They're standalone.

**Q: How do I update?**
A: `git pull` the repo, then `bash install.sh --yes` (merge mode preserves your customizations).

**Q: Can I use this on Linux?**
A: Yes. macOS is the primary platform but everything works on Linux except brightness control.
