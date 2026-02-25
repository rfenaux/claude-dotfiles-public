# Verification Before Delivery

Before finalizing any deliverable:

1. **Source cross-reference** - Verify derived data against primary sources (RAG, conversation files, original docs)
2. **Bulk edit verification** - After find/replace or multi-file edits, grep to confirm zero remaining old pattern instances
3. **Context confirmation** - Verify target environment/portal before execution ("Test portal, correct?")
4. **Freshness check** - Search for pivots/changes in recent transcripts that may invalidate assumptions

5. **Evidence gate** - Before documenting any architectural pattern or technical claim, cite the specific file path + line that supports it. Mark with `[VERIFIED: file:line]` or `[ASSUMED: needs verification]`

**Proactive offers:**
- "Want me to index this transcript to RAG for searchability?"
- "Let me cross-reference this against the original [source]..."
