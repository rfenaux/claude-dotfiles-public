# Context Discovery Rule (Prevent Documentation Drift)

Before reporting project status, blockers, or remaining tasks:

1. **Check conversation files** - Scan `*.txt` in project root for recent Claude sessions
2. **Search for resolutions** - Grep for "resolved", "decided", "confirmed", "yes all" in text files
3. **Compare dates** - If DECISIONS.md shows "PENDING" but a conversation file says "resolved", trust the newer source
4. **Invoke `/decision-sync`** - When in doubt, run the skill to reconcile documentation

**Pattern:** Conversation files often contain decisions that weren't back-propagated to DECISIONS.md.

```bash
# Quick check for resolved decisions in project
grep -l "resolved\|decided\|confirmed" "$PROJECT_DIR"/*.txt 2>/dev/null
```
