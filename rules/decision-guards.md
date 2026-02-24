# Decision Guards

If/then rules to prevent recurring wrong-approach patterns (addresses 85 friction events from usage insights).

## Pre-Edit Target Confirmation (#1 friction source: 85 wrong-approach instances)

**Before ANY file edit, state in 1 line:** `Editing [filename] because [reason]`

This catches wrong-file targeting (index.html vs index-v2.html), wrong-tool usage (direct git vs chezmoi), and wrong-scope assumptions before they waste time.

## Conditional Guards

| Condition | Guard |
|-----------|-------|
| Dotfile changes in `~/.claude/` | Be cautious with git operations from `~` — use targeted paths |
| Files >1000 lines | Targeted Edit with unique `old_string` (5+ chars context), never full-file Write |
| Killing stuck Python processes | `kill -9 <pid>` directly + check stale `.lock`/`.pid` files after |
| Hook changes (`.sh`, `.mjs` in hooks/) | Validate JSON output before deploying; test hook manually with sample stdin first |
| Versioned files exist (e.g., `index.html` vs `index-v2.html`) | Confirm which variant is actively served before editing |
| Dashboard edits | Always target `index-v2.html` in `~/.claude/rag-dashboard/` |
| DECISIONS.md edits | Known large file (2700+ lines) — targeted Edit only, never Write |
| Infrastructure files (`settings.json`, `CLAUDE.md`, hooks) | Read current state first, confirm intent, then edit |
| Multiple files share similar names | List candidates, confirm correct target before proceeding |

**Recovery:** If wrong approach taken, announce pivot immediately per 2-attempt rule.
