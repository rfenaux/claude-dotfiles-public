# Hooks Directory

Registered hooks in `settings.json` and utility scripts.

## Registered Hooks (25 total)

### UserPromptSubmit

| Hook | Purpose |
|------|---------|
| `global-privacy-guard.sh` | Prevent PII/credential leakage |
| `csb-approve-handler.py` | Content Security Buffer approval |
| _(inline)_ | Timestamp injection, enhance mode |

### PreToolUse

| Hook | Matcher | Purpose |
|------|---------|---------|
| `csb-write-guard.py` | Write | Guard file writes |
| `csb-edit-guard.py` | Edit | Guard file edits |
| `outgoing-data-guard.py` | Bash | Guard outbound data |
| `csb-bash-guard.py` | Bash | Security buffer for bash |
| `search-routing-reminder.sh` | Grep, Glob | Search tool guidance |
| `csb-pretool-defense.sh` | Read, WebFetch | Pre-read defense |

### PostToolUse

| Hook | Matcher | Purpose |
|------|---------|---------|
| `observation-logger.sh` | _(all)_ | Session observation capture |
| `pattern-tracker.sh` | _(all)_ | Usage pattern tracking |
| `rag-index-on-write.sh` | Write, Edit | Real-time RAG indexing |
| `csb-posttool-scanner.py` | Read, WebFetch | Post-read security scan |
| `csb-webfetch-cache.py` | WebFetch | Cache web fetches |

### PreCompact

| Hook | Purpose |
|------|---------|
| `memory-flush-precompact.sh` | Extract decisions/learnings |
| `save-conversation.sh` | Save transcript to history |
| `ctm/ctm-pre-compact.sh` | CTM checkpoint |

### SessionStart

| Hook | Purpose |
|------|---------|
| `ctm/ctm-session-start.sh` | CTM briefing + task resume |
| `proactive-rag-surfacer.sh` | Surface relevant context |
| _(inline scripts)_ | Memory sync, project enrichment |

### SessionEnd

| Hook | Purpose |
|------|---------|
| `save-conversation.sh` | Save transcript |
| `ctm/ctm-session-end.sh` | CTM checkpoint |
| `claude-config-backup.sh` | Backup config to git |
| `session-compressor.sh` | Compress observations |

### Stop

| Hook | Purpose |
|------|---------|
| `session-compressor.sh` | Compress observations |

## Utility Scripts (not registered)

| Script | Referenced By | Purpose |
|--------|--------------|---------|
| `setup.sh` | Multiple scripts | Hook installation wizard |
| `lesson-extractor.sh` | save-conversation.sh | Extract lessons from conversations |
| `lesson-surfacer.sh` | proactive-rag-surfacer.sh | Surface relevant lessons |
| `device-check.sh` | validate-setup.sh | Device fingerprint check |
| `git-post-commit-rag.sh` | Git hooks | Index on commit |

## CSB Library (imported by guards)

| Script | Purpose |
|--------|---------|
| `csb_taint_manager.py` | Taint tracking for security |
| `csb-sanitizer.py` | Content sanitization |

## CTM Subdirectory

Contains CTM-specific hooks: `ctm-session-start.sh`, `ctm-session-end.sh`, `ctm-pre-compact.sh`, `ctm-user-prompt.sh`.

---
*Last updated: 2026-02-07*
