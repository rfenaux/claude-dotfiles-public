# Configuration Optimization Rollback Guide
**Date:** 2026-01-28
**Session:** Context usage optimization (62% → ~52%)

## Quick Rollback Commands

### Full Rollback (restore everything)
```bash
# Restore all archived agents
mv ~/.claude/agents/_archived/*.md ~/.claude/agents/

# Restore all backups (remove -ignore suffix)
for f in ~/.claude/agents/*-ignore-and-do-not-rag-index.md; do
  mv "$f" "${f%-ignore-and-do-not-rag-index.md}.md"
done

# Delete new consolidated agents
rm ~/.claude/agents/uat-generator.md
rm ~/.claude/agents/hubspot-api-crm-all.md
rm ~/.claude/agents/hubspot-api-content-all.md
```

---

## Changes Made

### P0: Duplicate & Project-Specific Agents

| Archived Agent | Reason | Restore Command |
|----------------|--------|-----------------|
| `kb-query-agent.md` | Duplicate of `knowledge-base-query` | `mv ~/.claude/agents/_archived/kb-query-agent.md ~/.claude/agents/` |
| `kb-synthesizer.md` | Duplicate of `knowledge-base-synthesizer` | `mv ~/.claude/agents/_archived/kb-synthesizer.md ~/.claude/agents/` |
| `functional-spec-generator.md` | Duplicate of `fsd-generator` | `mv ~/.claude/agents/_archived/functional-spec-generator.md ~/.claude/agents/` |
| `<REMOVED>.md` | <PROJECT> project archived | `mv ~/.claude/agents/_archived/<REMOVED>.md ~/.claude/agents/` |
| `<REMOVED>.md` | <PROJECT> project archived | `mv ~/.claude/agents/_archived/<REMOVED>.md ~/.claude/agents/` |
| `<REMOVED>.md` | <PROJECT> project archived | `mv ~/.claude/agents/_archived/<REMOVED>.md ~/.claude/agents/` |
| `<REMOVED>.md` | <PROJECT> project archived | `mv ~/.claude/agents/_archived/<REMOVED>.md ~/.claude/agents/` |

### P1: Slimmed & Consolidated Agents

#### solarc-argent (32KB → 2KB)

**Backup location:** `~/.claude/agents/solarc-argent-ignore-and-do-not-rag-index.md`

**Rollback:**
```bash
mv ~/.claude/agents/solarc-argent.md ~/.claude/agents/solarc-argent-SLIM.md
mv ~/.claude/agents/solarc-argent-ignore-and-do-not-rag-index.md ~/.claude/agents/solarc-argent.md
```

#### UAT Agents (4 agents → 1)

**New agent:** `uat-generator.md` (consolidated)

**Backups:**
- `~/.claude/agents/uat-integration-ignore-and-do-not-rag-index.md`
- `~/.claude/agents/uat-migration-ignore-and-do-not-rag-index.md`
- `~/.claude/agents/uat-sales-hub-ignore-and-do-not-rag-index.md`
- `~/.claude/agents/uat-service-hub-ignore-and-do-not-rag-index.md`

**Archived originals:**
- `~/.claude/agents/_archived/uat-integration.md`
- `~/.claude/agents/_archived/uat-migration.md`
- `~/.claude/agents/_archived/uat-sales-hub.md`
- `~/.claude/agents/_archived/uat-service-hub.md`

**Rollback:**
```bash
# Remove consolidated agent
rm ~/.claude/agents/uat-generator.md

# Restore original agents
mv ~/.claude/agents/_archived/uat-*.md ~/.claude/agents/
```

### P2: HubSpot API Consolidation (16 agents → 4)

**New agents:**
- `hubspot-api-crm-all.md` (consolidated CRM/data)
- `hubspot-api-content-all.md` (consolidated marketing/CMS)

**Updated:**
- `hubspot-api-router.md` (updated to route to 3 agents instead of 16)
- `hubspot-api-specialist.md` (kept as-is)

**Backups (16 files):**
```
~/.claude/agents/hubspot-api-account-ignore-and-do-not-rag-index.md
~/.claude/agents/hubspot-api-auth-ignore-and-do-not-rag-index.md
~/.claude/agents/hubspot-api-automation-ignore-and-do-not-rag-index.md
~/.claude/agents/hubspot-api-business-units-ignore-and-do-not-rag-index.md
~/.claude/agents/hubspot-api-cms-ignore-and-do-not-rag-index.md
~/.claude/agents/hubspot-api-communication-preferences-ignore-and-do-not-rag-index.md
~/.claude/agents/hubspot-api-conversations-ignore-and-do-not-rag-index.md
~/.claude/agents/hubspot-api-crm-ignore-and-do-not-rag-index.md
~/.claude/agents/hubspot-api-events-ignore-and-do-not-rag-index.md
~/.claude/agents/hubspot-api-files-ignore-and-do-not-rag-index.md
~/.claude/agents/hubspot-api-marketing-ignore-and-do-not-rag-index.md
~/.claude/agents/hubspot-api-router-ignore-and-do-not-rag-index.md
~/.claude/agents/hubspot-api-scheduler-ignore-and-do-not-rag-index.md
~/.claude/agents/hubspot-api-settings-ignore-and-do-not-rag-index.md
~/.claude/agents/hubspot-api-specialist-ignore-and-do-not-rag-index.md
~/.claude/agents/hubspot-api-webhooks-ignore-and-do-not-rag-index.md
```

**Archived originals (14 files):**
```
~/.claude/agents/_archived/hubspot-api-account.md
~/.claude/agents/_archived/hubspot-api-auth.md
~/.claude/agents/_archived/hubspot-api-automation.md
~/.claude/agents/_archived/hubspot-api-business-units.md
~/.claude/agents/_archived/hubspot-api-cms.md
~/.claude/agents/_archived/hubspot-api-communication-preferences.md
~/.claude/agents/_archived/hubspot-api-conversations.md
~/.claude/agents/_archived/hubspot-api-crm.md
~/.claude/agents/_archived/hubspot-api-events.md
~/.claude/agents/_archived/hubspot-api-files.md
~/.claude/agents/_archived/hubspot-api-marketing.md
~/.claude/agents/_archived/hubspot-api-scheduler.md
~/.claude/agents/_archived/hubspot-api-settings.md
~/.claude/agents/_archived/hubspot-api-webhooks.md
```

**Rollback:**
```bash
# Remove new consolidated agents
rm ~/.claude/agents/hubspot-api-crm-all.md
rm ~/.claude/agents/hubspot-api-content-all.md

# Restore router backup
mv ~/.claude/agents/hubspot-api-router.md ~/.claude/agents/hubspot-api-router-NEW.md
mv ~/.claude/agents/hubspot-api-router-ignore-and-do-not-rag-index.md ~/.claude/agents/hubspot-api-router.md

# Restore all domain agents
mv ~/.claude/agents/_archived/hubspot-api-*.md ~/.claude/agents/
```

---

### P3: CLAUDE.md Trimming

**Backup location:** `~/.claude/CLAUDE-ignore-and-do-not-rag-index.md`

**Changes:**
- Reduced from 617 lines to 201 lines (67% reduction)
- Reduced from 23KB to 5.7KB (75% reduction)
- Externalized ADHD Support to `~/.claude/docs/ADHD_SUPPORT.md`
- Condensed all sections, kept essential references
- Removed redundant details that have "Full reference" pointers

**Rollback:**
```bash
mv ~/.claude/CLAUDE.md ~/.claude/CLAUDE-SLIM.md
mv ~/.claude/CLAUDE-ignore-and-do-not-rag-index.md ~/.claude/CLAUDE.md
```

---

## Summary Statistics

| Metric | Before | After |
|--------|--------|-------|
| Active agents | 125 | 103 |
| Archived | 0 | 25 |
| CLAUDE.md | 617 lines | 201 lines |
| Estimated context | 62% | ~52% |
| Total bytes saved | - | ~175 KB |

---

## Verification

After rollback, verify:
```bash
# Count agents
ls ~/.claude/agents/*.md | grep -v ignore | wc -l

# Should be 125 after full rollback
```
