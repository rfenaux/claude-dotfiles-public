# Implementation Orchestration Plan

> Master plan for implementing all 12 PRDs
> Generated: 2026-02-03
> **Revised: 2026-02-03** (after GAP_ANALYSIS.md)
> Total estimated effort: **~157 hours** (previously ~180h, **~23h saved**)

## Executive Summary

```
┌─────────────────────────────────────────────────────────────────────────┐
│  IMPLEMENTATION TIMELINE: 5-6 WEEKS (previously 6-8 weeks)             │
│                                                                         │
│  Week 1-2: Quick Wins (TOOL-003, MEM-001)                              │
│  Week 2:   RAG Foundation (RAG-001, RAG-002) ← FASTER due to overlap   │
│  Week 3:   RAG-003, RAG-004, CTM-001 (in parallel)                     │
│  Week 4:   CTM-002, CTM-003                                            │
│  Week 5:   Integration & Polish                                        │
│  Week 6+:  Future (MEM-002, TOOL-001)                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

## Key Insight from GAP_ANALYSIS.md

**Much of RAG infrastructure already exists:**
- ✅ Hybrid Search (70% vector + 30% BM25 with RRF fusion)
- ✅ Query Classification/Routing
- ✅ Citation Tracking (source_file, line numbers)
- ✅ Confidence Scoring
- ✅ Contradiction Detection

**This means:**
- RAG-001: Just add staged pre-filter mode (not build hybrid)
- RAG-002: Just verify/add SQLite metadata (not build triple-index)
- RAG-004: Just add LLM synthesis pass (not build citation system)
- TOOL-003: Extend existing query classifier (not build from scratch)

---

## Dependency Graph (REVISED)

```
                           START
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
         ┌────────┐    ┌────────┐    ┌────────┐
         │TOOL-003│    │MEM-001 │    │RAG-001 │
         │ 8-9h   │    │ 40h    │    │ 3-5h   │ ← REDUCED
         └───┬────┘    └───┬────┘    └───┬────┘
             │             │             │
             ▼             │             ▼
         ┌────────┐        │        ┌────────┐
         │  DONE  │        │        │RAG-002 │
         └────────┘        │        │ 6-7h   │ ← REDUCED
                           │        └───┬────┘
                           │             │
                           │      ┌──────┴──────┐
                           │      ▼             ▼
                           │ ┌────────┐    ┌────────┐
                           │ │RAG-003 │    │RAG-004 │
                           │ │ 12h    │    │ 6-8h   │ ← REDUCED
                           │ └───┬────┘    └───┬────┘
                           │     │             │
                           │     └──────┬──────┘
                           │            ▼
                           │        RAG DONE
                           │
                           ▼
                      ┌────────┐
                      │CTM-001 │ ◄─── Can start after MEM-001 or in parallel
                      │ 18h    │
                      └───┬────┘
                          │
                   ┌──────┴──────┐
                   ▼             ▼
              ┌────────┐    ┌────────┐
              │CTM-002 │    │CTM-003 │
              │ 20h    │    │ 18h    │
              └───┬────┘    └───┬────┘
                  │             │
                  └──────┬──────┘
                         ▼
                     CTM DONE
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
         ┌────────┐            ┌────────┐
         │TOOL-001│            │MEM-002 │
         │ 9h     │            │ 200h   │
         │Optional│            │Future  │
         └────────┘            └────────┘
```

---

## Phase Breakdown

### Phase 0: Preparation (Day 0)
**Duration:** 2-4 hours

```
┌─────────────────────────────────────────────────────────────┐
│  PREPARATION CHECKLIST                                      │
├─────────────────────────────────────────────────────────────┤
│  [ ] Create feature branch: claude-infra-improvements       │
│  [ ] Set up CTM task: ctm spawn "Infrastructure PRDs"       │
│  [ ] Verify dependencies installed:                         │
│      - rank_bm25 (RAG)                                      │
│      - markdown-it-py (RAG-003)                             │
│      - Gemini CLI (TOOL-003)                                │
│  [ ] Create test fixtures directory                         │
│  [ ] Set up CI for new modules                              │
└─────────────────────────────────────────────────────────────┘
```

---

### Phase 1: Quick Wins (Week 1-2)
**Duration:** 5-8 days | **Effort:** ~52 hours

**Goal:** Immediate value with minimal risk

```
┌─────────────────────────────────────────────────────────────┐
│  PARALLEL EXECUTION                                         │
│                                                             │
│  Track A: TOOL-003 (Gemini Auto-Routing)     Track B: MEM-001│
│  ─────────────────────────────────────────   ───────────────│
│  Day 1: Config + hook script (4h)            Day 1-2: CLI   │
│  Day 2: Safety rules + testing (4h)                  parser │
│  Day 3: Integration + docs (4h)              Day 3-4: Merge │
│  ─────────────────────────────────────────          logic   │
│  DONE: Day 3                                 Day 5: Testing │
│                                              Day 6-8: Polish│
│                                              ───────────────│
│                                              DONE: Day 8    │
└─────────────────────────────────────────────────────────────┘
```

**TOOL-003 Tasks:**
| Task | Hours | Dependencies |
|------|-------|--------------|
| Create `gemini-routing.json` config | 1 | None |
| Implement `gemini-routing-hook.py` | 4 | Config |
| Add PreToolUse hooks to settings.json | 0.5 | Hook script |
| Update gemini-delegate agent | 1 | Hook working |
| Write tests | 2 | Implementation |
| Documentation | 1.5 | Tests passing |
| Integration testing | 2 | All above |
| **Total** | **12** | |

**MEM-001 Tasks:**
| Task | Hours | Dependencies |
|------|-------|--------------|
| CLI argument parser extension | 6 | None |
| Prompt merger implementation | 10 | Parser |
| Section markers and formatting | 4 | Merger |
| Unit tests | 6 | Implementation |
| Integration tests | 4 | Unit tests |
| Conflict detection (Phase 2) | 8 | Basic working |
| Documentation | 4 | Tests passing |
| **Total** | **42** | |

**Milestone:** End of Week 2
- ✓ Gemini auto-routing live
- ✓ `--append-system-prompt` available
- ✓ Estimated token savings: 20-30%

---

### Phase 2: RAG Foundation (Week 2) ← FASTER
**Duration:** 3-4 days | **Effort:** ~10-12 hours (previously ~22h)

**Goal:** Faster RAG queries (200ms → 25ms)

**KEY INSIGHT:** Hybrid search + BM25 already exist. Just add staged mode.

```
┌─────────────────────────────────────────────────────────────┐
│  FAST EXECUTION (most already exists!)                      │
│                                                             │
│  RAG-001 (Staged Pre-Filtering) ← LEVERAGES EXISTING       │
│  ─────────────────────────────────                          │
│  Day 1: Add filter param to vector search (1.5h)            │
│  Day 1: Wire up staged mode + config (1h)                   │
│  Day 2: Testing + benchmarks (1.5h)                         │
│  ─────────────────────────────────                          │
│  DONE: Day 2 → Unlocks RAG-002                              │
│                                                             │
│  RAG-002 (Metadata Index) ← VERIFY FIRST                    │
│  ─────────────────────────────────                          │
│  Day 2: Check if SQLite exists (1h)                         │
│  Day 3: Add SQLite IF missing + filters (3-4h)              │
│  Day 4: Testing (1h)                                        │
│  ─────────────────────────────────                          │
│  DONE: Day 4 → Unlocks RAG-003/004                          │
└─────────────────────────────────────────────────────────────┘
```

**RAG-001 Tasks (REVISED):**
| Task | Hours | Dependencies |
|------|-------|--------------|
| ~~Install rank_bm25~~ | ~~0.25~~ | ✅ Already installed |
| ~~BM25 index creation~~ | ~~2~~ | ✅ Already exists |
| Add filter to vector search | 1.5 | None |
| Wire up staged mode | 0.5 | Filter working |
| Config schema update | 0.5 | Staged mode |
| Testing + benchmarks | 1.5 | Implementation |
| **Total** | **4** | (was 10) |

**RAG-002 Tasks (REVISED):**
| Task | Hours | Dependencies |
|------|-------|--------------|
| Investigate current metadata storage | 1 | None |
| Add SQLite IF missing | 3 | Investigation |
| Wire up filter parameters | 1 | SQLite |
| Testing | 1 | Implementation |
| **Total** | **6** | (was 13) |

**Milestone:** End of Week 2
- ✓ RAG queries <50ms P95
- ✓ Staged filtering available
- ✓ Metadata filtering working

---

### Phase 3: CTM Foundation (Week 3-4)
**Duration:** 4-5 days | **Effort:** ~18 hours

**Goal:** Prevent false task completions

```
┌─────────────────────────────────────────────────────────────┐
│  CTM-001 (Goal-Backward Verification)                       │
│                                                             │
│  Day 1: verification.py module (4h)                         │
│  Day 2: Agent schema extension (3h)                         │
│  Day 3: ctm verify command (4h)                             │
│  Day 4: ctm complete integration (4h)                       │
│  Day 5: Testing + docs (3h)                                 │
│  ─────────────────────────────────                          │
│  DONE: Day 5 → Unlocks CTM-002/003                          │
└─────────────────────────────────────────────────────────────┘
```

**CTM-001 Tasks:**
| Task | Hours | Dependencies |
|------|-------|--------------|
| Create verification.py module | 4 | None |
| Extend agent schema for criteria | 2 | Module |
| Implement ctm verify command | 3 | Schema |
| Modify ctm complete flow | 3 | Verify cmd |
| Criterion check execution | 2 | Complete flow |
| Unit tests | 2 | Implementation |
| Integration tests | 1.5 | Unit tests |
| Documentation | 1.5 | Tests |
| **Total** | **19** | |

**Milestone:** End of Week 4
- ✓ Verification criteria on tasks
- ✓ `ctm verify` command available
- ✓ Completion requires verification pass

---

### Phase 4: Parallel Expansion (Week 4-5)
**Duration:** 7-10 days | **Effort:** ~64 hours

**Goal:** Advanced features on both tracks

```
┌─────────────────────────────────────────────────────────────┐
│  PARALLEL EXECUTION (4 workstreams)                         │
│                                                             │
│  RAG-003          RAG-004          CTM-002         CTM-003  │
│  ────────         ────────         ────────        ──────── │
│  Chunking         Synthesis        Waves           Auto-gen │
│  12h              14h              20h             18h      │
│                                                             │
│  Can be done by 4 parallel workers or 2 sequential tracks   │
└─────────────────────────────────────────────────────────────┘
```

**Option A: Maximum Parallelism (4 workers)**
```
Week 4:
  Worker 1: RAG-003 (days 1-3)
  Worker 2: RAG-004 (days 1-4)
  Worker 3: CTM-002 (days 1-5)
  Worker 4: CTM-003 (days 1-4)

All complete by end of Week 4
```

**Option B: Sequential (2 tracks)**
```
Week 4:
  Track A: RAG-003 (days 1-3) → RAG-004 (days 4-7)
  Track B: CTM-002 (days 1-5) → CTM-003 (days 6-9)

All complete by end of Week 5
```

**RAG-003 Tasks:**
| Task | Hours | Dependencies |
|------|-------|--------------|
| Markdown parser integration | 3 | None |
| Document tree builder | 3 | Parser |
| Section-aware chunker | 3 | Tree |
| Metadata enrichment | 2 | Chunker |
| Testing | 2 | Implementation |
| **Total** | **13** | |

**RAG-004 Tasks (REVISED):**
| Task | Hours | Dependencies |
|------|-------|--------------|
| Synthesis prompt template | 1 | None |
| LLM synthesis pipeline | 2 | Template |
| Citation extraction | 1 | Pipeline |
| ~~Source formatting~~ | ~~2~~ | ✅ Use existing citation tracking |
| ~~Confidence scoring~~ | ~~2~~ | ✅ Already exists |
| Testing | 1 | Implementation |
| **Total** | **7** | (was 15) |

**CTM-002 Tasks:**
| Task | Hours | Dependencies |
|------|-------|--------------|
| waves.py module | 4 | None |
| Topological sort algorithm | 3 | Module |
| Wave state persistence | 2 | Algorithm |
| Resource-aware spawning | 3 | Persistence |
| Wave monitoring | 3 | Spawning |
| ctm delegate --waves | 2 | All above |
| Testing | 3 | Implementation |
| **Total** | **20** | |

**CTM-003 Tasks:**
| Task | Hours | Dependencies |
|------|-------|--------------|
| verification_gen.py module | 4 | None |
| Template system (YAML) | 3 | Module |
| Content extraction heuristics | 4 | Templates |
| Rollback procedure generation | 2 | Extraction |
| ctm verify generate | 2 | All above |
| Testing | 3 | Implementation |
| **Total** | **18** | |

**Milestone:** End of Week 5
- ✓ Section-aware RAG chunking
- ✓ Synthesized answers with citations
- ✓ Wave-based agent parallelism
- ✓ Auto-generated VERIFICATION.md

---

### Phase 5: Integration & Polish (Week 6)
**Duration:** 3-5 days | **Effort:** ~20 hours

**Goal:** Cross-system integration, documentation, release prep

```
┌─────────────────────────────────────────────────────────────┐
│  INTEGRATION TASKS                                          │
│                                                             │
│  Day 1-2: Cross-Module Testing                              │
│  - RAG + CTM: Verify search during task completion          │
│  - TOOL-003 + RAG: Gemini routing for large RAG queries     │
│  - MEM-001 + CTM: Append context from CTM task              │
│                                                             │
│  Day 3: Performance Validation                              │
│  - Full benchmark suite                                     │
│  - Memory profiling                                         │
│  - Latency verification                                     │
│                                                             │
│  Day 4: Documentation                                       │
│  - Update CLAUDE.md with new features                       │
│  - Update guides (RAG_GUIDE.md, CTM_GUIDE.md)               │
│  - Create migration notes                                   │
│                                                             │
│  Day 5: Release                                             │
│  - Version bump                                             │
│  - Changelog                                                │
│  - Announcement                                             │
└─────────────────────────────────────────────────────────────┘
```

**Milestone:** End of Week 6
- ✓ All 10 core PRDs implemented
- ✓ Full test coverage
- ✓ Documentation updated
- ✓ Ready for production use

---

### Phase 6: Future/Optional (Week 7+)
**Duration:** Ongoing | **Effort:** ~210 hours

```
┌─────────────────────────────────────────────────────────────┐
│  OPTIONAL / FUTURE WORK                                     │
│                                                             │
│  TOOL-001: Barista Status Bar (9h)                          │
│  - Nice-to-have, implement when time permits                │
│  - No dependencies on other PRDs                            │
│                                                             │
│  MEM-002: Claude Persistent Space (200h)                    │
│  - Major strategic investment                               │
│  - Requires dedicated sprint (4-6 weeks)                    │
│  - Security audit required before release                   │
│  - Target: Q2 2026                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Resource Allocation

### Single Developer Track
```
Week 1:  TOOL-003 ████░░░░░░ (12h)
Week 2:  MEM-001  ████████░░ (40h continues)
Week 3:  RAG-001  ████░░░░░░ + RAG-002 start
Week 4:  RAG-002  ████░░░░░░ + CTM-001 start
Week 5:  CTM-001  ████░░░░░░ + RAG-003/004
Week 6:  CTM-002  ████████░░
Week 7:  CTM-003  ████░░░░░░ + Integration
Week 8:  Polish   ████░░░░░░

Total: 8 weeks
```

### Parallel Team Track (2 developers)
```
         Dev A                    Dev B
Week 1:  TOOL-003 (done!)        MEM-001 ████░░░░░░
Week 2:  RAG-001                 MEM-001 (done!)
Week 3:  RAG-002                 CTM-001
Week 4:  RAG-003 + RAG-004       CTM-002 + CTM-003
Week 5:  Integration             Integration
Week 6:  Polish                  Documentation

Total: 6 weeks
```

### Agent-Assisted Track (with Claude workers)
```
Phase 1: Spawn 2 parallel agents (TOOL-003, MEM-001)
Phase 2: Spawn 2 sequential agents (RAG-001 → RAG-002)
Phase 3: Spawn 1 agent (CTM-001)
Phase 4: Spawn 4 parallel agents (RAG-003, RAG-004, CTM-002, CTM-003)
Phase 5: Human review + integration

Total: 4-5 weeks with agent assistance
```

---

## Risk Management

### High-Risk Items
| PRD | Risk | Mitigation |
|-----|------|------------|
| RAG-001 | BM25 recall degradation | Generous candidate count; fallback |
| CTM-001 | Over-strict verification | Easy skip option; configurable |
| MEM-002 | Security concerns | Defer until audit; sandboxing |

### Rollback Plan
```
Each PRD implemented behind feature flag:

~/.claude/config/features.json
{
  "rag_staged_filtering": true,
  "rag_triple_index": true,
  "rag_section_chunking": true,
  "rag_synthesis": true,
  "ctm_verification": true,
  "ctm_waves": true,
  "ctm_verification_gen": true,
  "tool_gemini_routing": true,
  "mem_append_prompt": true
}

Disable individual features without full rollback.
```

---

## Go/No-Go Checkpoints

### Checkpoint 1: End of Week 2
```
┌─────────────────────────────────────────────────────────────┐
│  GATE: Quick Wins Validation                                │
├─────────────────────────────────────────────────────────────┤
│  [ ] TOOL-003: Gemini routing working without false +/-     │
│  [ ] MEM-001: Append prompt merges correctly                │
│  [ ] No performance regression in baseline operations       │
│  [ ] User acceptance: "feels useful"                        │
├─────────────────────────────────────────────────────────────┤
│  GO → Continue to Phase 2                                   │
│  NO-GO → Debug and fix before proceeding                    │
└─────────────────────────────────────────────────────────────┘
```

### Checkpoint 2: End of Week 3
```
┌─────────────────────────────────────────────────────────────┐
│  GATE: RAG Foundation Validation                            │
├─────────────────────────────────────────────────────────────┤
│  [ ] RAG-001: Query latency <50ms P95                       │
│  [ ] RAG-002: Triple index sync accurate                    │
│  [ ] Recall quality maintained (>95% vs baseline)           │
│  [ ] Memory usage acceptable (<50MB increase)               │
├─────────────────────────────────────────────────────────────┤
│  GO → Continue to Phase 3+4                                 │
│  NO-GO → Tune thresholds, optimize before proceeding        │
└─────────────────────────────────────────────────────────────┘
```

### Checkpoint 3: End of Week 5
```
┌─────────────────────────────────────────────────────────────┐
│  GATE: Full Feature Validation                              │
├─────────────────────────────────────────────────────────────┤
│  [ ] All 10 PRDs implemented                                │
│  [ ] Test coverage >80%                                     │
│  [ ] No critical bugs                                       │
│  [ ] Documentation complete                                 │
│  [ ] Performance benchmarks met                             │
├─────────────────────────────────────────────────────────────┤
│  GO → Release                                               │
│  NO-GO → Fix issues, extend timeline                        │
└─────────────────────────────────────────────────────────────┘
```

---

## CTM Task Structure

```bash
# Create parent task
ctm spawn "Infrastructure PRDs Implementation" --template feature

# Create subtasks (auto-blocked by dependencies)
ctm spawn "TOOL-003: Gemini CLI Routing" --parent infra-prds
ctm spawn "MEM-001: Append System Prompt" --parent infra-prds
ctm spawn "RAG-001: Staged Hybrid Filtering" --parent infra-prds --blocked-by tool-003
ctm spawn "RAG-002: Triple-Index Storage" --parent infra-prds --blocked-by rag-001
ctm spawn "CTM-001: Goal-Backward Verification" --parent infra-prds --blocked-by mem-001
ctm spawn "RAG-003: Section-Aware Chunking" --parent infra-prds --blocked-by rag-002
ctm spawn "RAG-004: Two-Pass Summarization" --parent infra-prds --blocked-by rag-002
ctm spawn "CTM-002: Wave-Based Parallelism" --parent infra-prds --blocked-by ctm-001
ctm spawn "CTM-003: VERIFICATION.md Auto-Gen" --parent infra-prds --blocked-by ctm-001
ctm spawn "Integration & Polish" --parent infra-prds --blocked-by rag-003 rag-004 ctm-002 ctm-003
```

---

## Success Metrics (Post-Implementation)

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| RAG query latency (P95) | 200ms | <50ms | Benchmark suite |
| False task completions | ~15% | <5% | Audit completed tasks |
| Agent spawn time (5 agents) | 5min | <2min | Wave execution timing |
| Claude token usage | 100% | -30% | Gemini routing analytics |
| Context pollution from temp prompts | Common | Rare | User feedback |

---

## Next Action

**Recommended immediate action:**
```bash
# Start Phase 0
git checkout -b feature/infrastructure-prds
ctm spawn "Infrastructure PRDs Implementation" --switch

# Begin Phase 1 - Quick Wins
# Can run in parallel:
claude "Implement TOOL-003 per PRD spec"
claude "Implement MEM-001 per PRD spec"
```

---

*Plan Version: 2.0 (Revised after GAP_ANALYSIS.md)*
*Created: 2026-02-03*
*Revised: 2026-02-03*
*Estimated Total Effort: ~157 hours (was 180h, ~23h saved)*
*Estimated Duration: 5-6 weeks (single dev) / 4 weeks (parallel)*

---

## Effort Savings Summary

| PRD | Original | Revised | Savings | Reason |
|-----|----------|---------|---------|--------|
| RAG-001 | 8-10h | 3-5h | ~5h | BM25 + hybrid exists |
| RAG-002 | 12-16h | 6-7h | ~8h | Vector + BM25 exist |
| RAG-004 | 12-16h | 6-8h | ~7h | Citation tracking exists |
| TOOL-003 | 12h | 8-9h | ~3h | Query classifier exists |
| **Total** | - | - | **~23h** | -
