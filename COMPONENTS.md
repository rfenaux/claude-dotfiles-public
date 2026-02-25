# Component Manifest

Quick reference of everything included in this configuration.

## Core Systems

| System | Description | Key Files |
|--------|-------------|-----------|
| **CTM** | Cognitive Task Management — tracks work across sessions | `ctm/` |
| **RAG** | Local semantic search using Ollama embeddings | `.rag/`, `rag-dashboard/` |
| **Memory** | Auto-injected context from `memory/MEMORY.md` | `memory/` |
| **Observations** | Auto-captured session tool usage | `observations/` |
| **Lessons** | Auto-extracted domain knowledge with SONA scoring | `lessons/` |
| **CDP** | Cognitive Delegation Protocol for agent spawning | `CDP_PROTOCOL.md` |

## Agents (140+)

Specialized sub-agents invoked via the Task tool. Organized by domain:

| Category | Count | Examples |
|----------|-------|---------|
| HubSpot Implementation | 14 | `hubspot-impl-sales-hub`, `hubspot-impl-marketing-hub` |
| HubSpot API | 15+ | `hubspot-api-crm`, `hubspot-api-marketing` |
| Salesforce Mapping | 5 | `salesforce-mapping-contacts`, `salesforce-mapping-deals` |
| Visualization | 5 | `bpmn-specialist`, `erd-generator`, `lucidchart-generator` |
| Proposals & Docs | 8 | `proposal-orchestrator`, `solution-spec-writer` |
| Quality & Review | 5 | `deliverable-reviewer`, `error-corrector` |
| Infrastructure | 10 | `config-oracle`, `rag-integration-expert`, `ctm-expert` |
| Reasoning | 3 | `reasoning-duo`, `reasoning-duo-cg`, `reasoning-trio` |
| Token Optimization | 2 | `codex-delegate`, `gemini-delegate` |
| General | 20+ | `worker`, `slide-deck-creator`, `brand-kit-extractor` |

Full list: `ls ~/.claude/agents/`
Master catalog: `AGENTS_INDEX.md`

## Skills (50+)

Slash commands invoked with `/skill-name`. Key skills:

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `/ctm` | Task management | Manage cross-session tasks |
| `/enhance` | Prompt rewriting | Improve prompts before execution |
| `/config-audit` | Health check | Validate installation |
| `/score` | Config scoring | Check your configuration tier |
| `/brand-extract` | Brand extraction | Extract colors, fonts, logos |
| `/pptx` | Presentations | Create/edit PowerPoint files |
| `/rag-search` | Semantic search | Search project knowledge base |
| `/mem-search` | Observation search | Search past session summaries |
| `/init-project` | Project setup | Initialize full project infrastructure |
| `/pm-spec` | Spec creation | Interactive specification builder |
| `/decision-tracker` | Decision management | Record/supersede decisions |

Full list: `ls ~/.claude/skills/`
Master catalog: `SKILLS_INDEX.md`

## Hooks (50+)

Automation scripts triggered by Claude Code events:

| Event | Example Hooks |
|-------|--------------|
| **PostToolUse** | `observation-logger`, `rag-index-on-write`, `pattern-tracker` |
| **PreToolUse** | `csb-pretool-defense`, `global-privacy-guard`, `validate-syntax` |
| **SessionStart** | `ctm-session-start`, `device-check`, `mcp-preflight` |
| **SessionEnd** | `session-compressor`, `ctm-session-end`, `save-conversation` |
| **Stop** | `stop-safety-review`, `healing-summary` |
| **PreCompact** | `memory-flush-precompact`, `ctm-pre-compact` |
| **Notification** | `notification-sound`, `permission-auto-handler` |

Full list: `ls ~/.claude/hooks/`

## Rules (20)

Auto-loaded behavioral rules from `rules/`:

| Rule | Purpose |
|------|---------|
| `critical-rules.md` | Hard constraints (NEVER do X) |
| `memory-system.md` | Memory stack, CTM rules, RAG search order |
| `agent-routing.md` | When to invoke which agent |
| `context-management.md` | MCP scope, token optimization, CDP |
| `resource-management-rule.md` | Load-aware spawning, model selection |
| `decision-auto-capture.md` | Detect and record decisions |
| `sub-agent-delegation.md` | Agents explore, main session edits |
| `mcp-fast-fail.md` | 1-attempt only for MCP tools |
| `hook-development.md` | Quality rules for hook scripts |

## Config Files

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Main configuration (159 lines, links to rules) |
| `settings.json` | Hook registrations, permissions, UI settings |
| `config/paths.sh` | Configurable path defaults |
| `config/accounts.example.json` | Multi-account configuration template |
| `config/rag-exclusions.json` | RAG indexing exclusion patterns |
| `config/agent-clusters.json` | Agent cross-reference cluster definitions |
| `config/category-decay.json` | Lesson confidence decay rates |
| `config/preference-rules.json` | User preference violation rules |
| `config/surfacing-weights.json` | Proactive agent surfacing weights |

## Scripts

| Script | Purpose |
|--------|---------|
| `validate-setup.sh` | Installation health check |
| `generate-inventory.sh` | Component inventory generation |
| `check-load.sh` | System load check before spawning agents |
| `detect-device.sh` | Machine profile generation |
| `standardize-agent-frontmatter.py` | Agent quality standardization |
| `standardize-hooks.py` | Hook quality standardization |
| `dotfiles-install-deps.sh` | Dependency installer |
| `analyze-skill-effectiveness.py` | Skill usage analytics |
| `check-hook-health.py` | Hook health validation |
| `counter-pattern-detector.py` | Preference violation detection |
| `surfacing-feedback.py` | Proactive content effectiveness |
| `sync-routing-from-patterns.py` | Auto-routing from usage patterns |

## Personas

Stakeholder interaction guides in `personas/`:

`client-admin`, `project-manager`, `developer`, `executive`, `external-partner`, `predecessor`
