# Exclusion Patterns

Unified exclusion patterns for RAG indexing, git, and search operations.

---

## Standard Exclusions (All Tools)

```
# Dependencies
node_modules/
__pycache__/
.venv/
venv/
.npm/
.yarn/

# Build outputs
dist/
build/
out/
.next/
.nuxt/

# IDE/Editor
.idea/
.vscode/
*.swp
*.swo
.DS_Store

# Git
.git/

# Logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Test coverage
coverage/
.nyc_output/

# Environment
.env
.env.*
!.env.example

# Secrets (never index)
*.pem
*.key
credentials.json
secrets.json
```

---

## RAG-Specific Exclusions

Used by `rag-index-on-write.sh` and `rag reindex`:

```bash
# RAG internal
.rag/

# Claude internal
.claude/session-env/
.claude/todos/
.claude/paste-cache/
.claude/file-history/
.claude/debug/

# Large binaries (handle separately)
*.zip
*.tar.gz
*.7z
*.dmg
*.iso

# Media (unless explicitly indexed)
*.mp4
*.mov
*.avi
*.mp3
*.wav

# Archives
(do not rag index)*/
```

---

## Git-Specific Exclusions

Standard `.gitignore` additions for Claude projects:

```gitignore
# Claude Code ephemeral
.claude/session-env/
.claude/todos/
.claude/paste-cache/
.claude/file-history/
.claude/debug/
.claude/stats-cache.json

# RAG database (regeneratable)
.rag/

# Agent workspaces (temporary)
.agent-workspaces/

# Conversation history (optional - may want to track)
# conversation-history/
```

---

## Search Exclusions (Grep/Glob)

Common patterns to skip in code search:

```bash
# Skip in Grep
--glob '!node_modules/**'
--glob '!.git/**'
--glob '!dist/**'
--glob '!*.min.js'
--glob '!*.map'
--glob '!package-lock.json'
--glob '!yarn.lock'

# Skip in Glob
!**/node_modules/**
!**/.git/**
!**/dist/**
```

---

## Project-Specific Overrides

Some projects need custom exclusions:

### Fathom Transcripts
```
# Include .txt transcripts
# Exclude raw JSON exports
*.json
```

### Client Projects
```
# Include all docs
# Exclude exported PDFs (duplicates source)
exports/*.pdf
```

---

## Applying Exclusions

### RAG Indexing
Exclusions are hardcoded in `~/.claude/hooks/rag-index-on-write.sh`.

### Git
Add to project `.gitignore` or global `~/.gitignore_global`.

### Grep/Glob
Pass `--glob` patterns or use `--type` filters.

---

## Adding New Exclusions

1. Update this document
2. Update `rag-index-on-write.sh` if RAG-related
3. Update project `.gitignore` if needed
4. Run `rag reindex` to apply to existing index

---

*Last updated: 2026-01-22*
