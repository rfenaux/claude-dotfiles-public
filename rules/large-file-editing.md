# Large File Editing

Performance guard for files over 500 lines. Prevents tool freezes and timeouts.

| Rule | Details |
|------|---------|
| Files >1000 lines | Always use targeted Edit with unique `old_string` (include surrounding context) |
| Files >500 lines | Never full-file rewrite via Write tool |
| Edit hangs >2 min | Abort, retry with smaller scope (fewer lines in old_string/new_string) |
| Known large files | DECISIONS.md, CLAUDE.md, settings.json, CONFIGURATION_GUIDE.md, CTM_GUIDE.md |

**Technique:** For multi-site edits in large files, make sequential Edit calls (one per change site). Each `old_string` must be unique within the file.

**Fallback:** If Edit fails on ambiguous `old_string`, add more surrounding lines to make it unique. Never broaden to full-file Write.
