# PRD Index - Claude Code Infrastructure Improvements

> Generated: 2026-02-03
> **Revised: 2026-02-14** (post-implementation audit)
> Source: Community patterns analysis (49 patterns → 12 PRDs)
> Status: 12/12 implemented or already done

## Quick Reference

| ID | Title | Priority | Effort | Status |
|----|-------|----------|--------|--------|
| **Tier 1: Quick Wins** |
| TOOL-003 | Gemini CLI Auto-Routing | High | Low | ✅ Implemented (gemini-routing-hook.py) |
| MEM-001 | Append System Prompt | High | Low | ✅ Implemented (session-context via rules/ injection) |
| TOOL-002 | claude-code-wrapped | Medium | Low | ✅ Already Done (stats plugin exists) |
| **Tier 2: High-Value Medium Effort** |
| RAG-001 | Staged Pre-Filtering | High | **LOW** | ✅ Implemented (vectordb.py BM25→vector staged mode) |
| CTM-001 | Goal-Backward Verification | High | Medium | ✅ Already Done (ctm verify CLI) |
| CTM-002 | Wave-Based Parallelism | Medium | Medium | ✅ Already Done (ctm waves CLI) |
| **Tier 3: Strategic Investments** |
| RAG-002 | Metadata Index Enhancement | High | **Medium** | ✅ Already Done (LanceDB catalog + SQLite graphdb) |
| RAG-003 | Section-Aware Chunking | Medium | Medium | ✅ Already Done (section chunking in server) |
| RAG-004 | LLM Synthesis Pass | Medium | **Medium** | ✅ Already Done (LLM synthesis in server) |
| CTM-003 | VERIFICATION.md Auto-Gen | Medium | Medium | ✅ Already Done (ctm verify --generate) |
| TOOL-001 | Barista Status Bar | Low | Medium | ✅ Implemented (rumps menu bar + launchd) |
| **Tier 4: Future Exploration** |
| MEM-002 | Claude Persistent Space | Medium | High | ✅ Implemented Phase 1+2 (daemon + time triggers + levels 1-3 + approval gate) |
| **Tier 5: New PRDs** |
| MON-001 | Multi-Session Status Monitoring | Medium | Medium | ✅ Implemented (per-session status + aggregator + multi-session menubar) |

---

## PRDs by Category

### Category A: RAG System Enhancements

| File | Description | Timeline |
|------|-------------|----------|
| [RAG-001_staged-hybrid-filtering.md](RAG-001_staged-hybrid-filtering.md) | **v2.0** Staged pre-filter optimization. BM25 narrows first, then vector. **Leverages existing hybrid.** | **3-5 hours** |
| [RAG-002_triple-index-storage.md](RAG-002_triple-index-storage.md) | **v2.0** Metadata index enhancement. Vector+BM25 exist, add SQLite if missing. | **6-7 hours** |
| [RAG-003_section-aware-chunking.md](RAG-003_section-aware-chunking.md) | Parse document structure, chunk by semantic boundaries, preserve hierarchy. | 10-14 hours |
| [RAG-004_two-pass-summarization.md](RAG-004_two-pass-summarization.md) | **v2.0** LLM synthesis pass only. **Citation tracking already exists.** | **6-8 hours** |

### Category B: Task Management Enhancements

| File | Description | Timeline |
|------|-------------|----------|
| [CTM-001_goal-backward-verification.md](CTM-001_goal-backward-verification.md) | Define success criteria upfront, verify backwards from goal before completion. | 18 hours |
| [CTM-002_wave-based-parallelism.md](CTM-002_wave-based-parallelism.md) | Organize agents into dependency waves, spawn in parallel while respecting limits. | 20 hours |
| [CTM-003_verification-md-autogen.md](CTM-003_verification-md-autogen.md) | Auto-generate VERIFICATION.md from task descriptions and templates. | 18 hours |

### Category C: Tooling & Monitoring

| File | Description | Timeline |
|------|-------------|----------|
| [TOOL-001_barista-status-bar.md](TOOL-001_barista-status-bar.md) | macOS menu bar integration showing task, tokens, agents, load status. | 9 hours |
| [TOOL-002_claude-code-wrapped.md](TOOL-002_claude-code-wrapped.md) | Stats plugin for usage analytics (already exists). | - |
| [TOOL-003_gemini-cli-routing.md](TOOL-003_gemini-cli-routing.md) | **v2.0** Extend existing query classifier with Gemini routing. | **8-9 hours** |

### Category D: Context & Memory

| File | Description | Timeline |
|------|-------------|----------|
| [MEM-001_append-system-prompt.md](MEM-001_append-system-prompt.md) | `--append-system-prompt` flag to ADD context without replacing CLAUDE.md. | 5-8 days |
| [MEM-002_claude-persistent-space.md](MEM-002_claude-persistent-space.md) | Autonomous sessions with deferred task queue and scheduled execution. | 4-6 weeks |

---

## Implementation Roadmap

### This Week (Quick Wins)
```
┌─────────────────────────────────────────────────────────────┐
│  TOOL-003: Gemini CLI Auto-Routing                          │
│  MEM-001: Append System Prompt                              │
│  Combined: ~18 hours → Immediate token savings              │
└─────────────────────────────────────────────────────────────┘
```

### This Month (High-Value)
```
┌─────────────────────────────────────────────────────────────┐
│  RAG-001: Staged Pre-Filtering (3-5h) ← REDUCED             │
│  CTM-001: Goal-Backward Verification (18h)                  │
│  CTM-002: Wave-Based Parallelism (20h)                      │
│  Combined: ~41 hours → Faster queries + better completion   │
└─────────────────────────────────────────────────────────────┘
```

### Q1 2026 (Strategic)
```
┌─────────────────────────────────────────────────────────────┐
│  RAG-002: Metadata Index (6-7h) ← REDUCED                   │
│  RAG-003: Section-Aware Chunking (10-14h)                   │
│  RAG-004: LLM Synthesis Pass (6-8h) ← REDUCED               │
│  CTM-003: VERIFICATION.md Auto-Gen (18h)                    │
│  Combined: ~45 hours → Advanced RAG + verification          │
└─────────────────────────────────────────────────────────────┘
```

### Future (Exploration)
```
┌─────────────────────────────────────────────────────────────┐
│  MEM-002: Claude Persistent Space (4-6 weeks)               │
│  TOOL-001: Barista Status Bar (9h)                          │
│  Combined: Autonomous AI + nice-to-have monitoring          │
└─────────────────────────────────────────────────────────────┘
```

---

## Dependency Graph

```
                    MEM-001
                       │
                       ▼
    ┌─────────────────────────────────────┐
    │          TOOL-003                    │
    │   (can use MEM-001 for context)     │
    └─────────────────────────────────────┘

    ┌─────────────────────────────────────┐
    │          RAG-001                     │
    │   (staged filtering foundation)     │
    └──────────────┬──────────────────────┘
                   │
                   ▼
    ┌─────────────────────────────────────┐
    │          RAG-002                     │
    │   (builds on RAG-001 BM25)          │
    └──────────────┬──────────────────────┘
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
    ┌──────────┐       ┌──────────┐
    │ RAG-003  │       │ RAG-004  │
    │ chunking │       │ synthesis│
    └──────────┘       └──────────┘

    ┌─────────────────────────────────────┐
    │          CTM-001                     │
    │   (verification foundation)         │
    └──────────────┬──────────────────────┘
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
    ┌──────────┐       ┌──────────┐
    │ CTM-002  │       │ CTM-003  │
    │ waves    │       │ auto-gen │
    └──────────┘       └──────────┘
```

---

## Success Metrics Summary

| Category | Key Metric | Target |
|----------|------------|--------|
| **RAG** | Query latency | P95 <100ms |
| **RAG** | Retrieval relevance | +15% MRR |
| **CTM** | False completions | <5% |
| **CTM** | Time savings | >40% vs sequential |
| **Tooling** | Token savings | 30% reduction |
| **Memory** | Adoption rate | 30% migration |

---

## Notes

- All PRDs follow standard template with Overview, Requirements, Technical Design, Implementation Plan, Verification Criteria, Risks, and Timeline
- Each PRD is self-contained and can be implemented independently (respecting dependencies)
- Tier 1 quick wins recommended for immediate implementation
- Security considerations included in all PRDs touching file access or autonomous execution

---

*Index Version: 3.0 (Post-implementation audit)*
*Created: 2026-02-03*
*Revised: 2026-02-14*
*Total PRDs: 12 (12/12 implemented or already done)*
*Audit: Config Enhancement Backlog task 9e58d685 — All waves + deferred items complete*
