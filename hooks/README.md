# Hooks Directory

Organization of Claude Code hooks.

## Session Hooks (in settings.json)

| Hook | Trigger | Purpose |
|------|---------|---------|
| `ctm/ctm-session-start.sh` | SessionStart | CTM briefing, task resume |
| `ctm/ctm-session-end.sh` | SessionEnd | CTM checkpoint |
| `ctm/ctm-pre-compact.sh` | PreCompact | Save state before context compaction |
| `ctm/ctm-user-prompt.sh` | UserPromptSubmit | Timestamp injection |
| `context-preflight.sh` | SessionStart:preflight | Context validation |
| `decision-drift-check.sh` | SessionStart:resume | Detect decision drift |
| `device-check.sh` | SessionStart:resume | Device fingerprint check |
| `lesson-surfacer.sh` | SessionStart:resume | Surface relevant lessons |
| `pretool-context.sh` | PreToolUse | Context injection |
| `save-conversation.sh` | SessionEnd, PreCompact | Save conversation to file |

## File Hooks

| Hook | Trigger | Purpose |
|------|---------|---------|
| `rag-index-on-write.sh` | PostToolUse:Write,Edit | Real-time RAG indexing |
| `inbox-watcher.sh` | PostToolUse:Write | Auto-process files added to inbox |
| `copy-external-files.sh` | PostToolUse:Read | Copy external files to project |
| `track-external-files.sh` | PostToolUse:Read | Track external file references |

## Git Hooks (for install in repos)

| Hook | Purpose |
|------|---------|
| `git-changelog-generator.py` | Generate changelog from commits |
| `git-changelog-to-rag.sh` | Index changelog to RAG |
| `git-context.py` | Git context extraction |
| `git-post-commit-rag.sh` | Index on commit |
| `install-git-hooks.sh` | Install hooks to repo |

## CTM Directory

Contains all CTM-specific hooks. See `ctm/` subdirectory.

## Utility

| Script | Purpose |
|--------|---------|
| `setup.sh` | Hook installation wizard |
| `agent-complete.sh` | Agent completion handler |
| `lesson-extractor.sh` | Extract lessons from conversations |

---
*Last updated: 2026-01-22*
