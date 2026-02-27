# Changelog

All notable changes to the Claude Code Power Config public release.

## [2026-02-27] — v2.0 Sync

### Changed
- `CLAUDE.md` rewritten to v2.0: modular structure, 4-layer memory table, model selection table (Haiku/Sonnet/Opus), quality gates section, removed legacy flat layout
- `AGENTS_INDEX.md` count corrected to 138 (public-safe agents only)

## [2026-02-25] — Sync & Documentation Update

### Added
- `AGENTS_INDEX.md` — Master catalog of all 139 agents with model, async mode, and descriptions
- `SKILLS_INDEX.md` — Master catalog of all 57 skills with triggers and commands
- `GETTING_STARTED.md` — Post-install guide with tier-based walkthrough
- `CLAUDE_ADOPTION_GUIDE.md` — Claude-to-Claude adoption document for LLM-driven selective setup
- `CHANGELOG.md` — This file
- 5 observability scripts: `analyze-skill-effectiveness.py`, `check-hook-health.py`, `counter-pattern-detector.py`, `surfacing-feedback.py`, `sync-routing-from-patterns.py`
- 3 config templates: `category-decay.json`, `preference-rules.json`, `surfacing-weights.json`

### Changed
- `README.md` rewritten with architecture diagram, 3 install methods (full/selective/Claude-to-Claude), and adoption tiers
- `COMPONENTS.md` updated with accurate counts and new file references

## [2026-02-12] — Initial Public Release

### Added
- 121 agents, 57 skills, 57 hooks, 20 rules
- Interactive installer (`install.sh`) with `--check`, `--yes`, `--prefix` modes
- CTM, RAG, CDP, project memory, lessons, and observation systems
- `settings.example.json` with full hook configuration
- Documentation: CLAUDE.md, CTM_GUIDE.md, RAG_GUIDE.md, CONFIGURATION_GUIDE.md, CDP_PROTOCOL.md
