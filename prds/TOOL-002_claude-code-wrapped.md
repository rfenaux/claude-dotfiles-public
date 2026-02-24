# PRD: TOOL-002 - claude-code-wrapped Stats Plugin

**Status:** Draft | **Version:** 1.0 | **Date:** 2026-02-03 | **Tier:** 1 (Quick Win)

---

## Executive Summary

The claude-code-wrapped Stats Plugin provides historical visibility into Claude Code usage patterns, token consumption, and cost trends. This tool enables data-driven decisions about model selection, session optimization, and budget forecasting.

**Target Users:** Individual developers, teams with shared Claude Code instances
**Priority:** Medium | **Timeline:** 1-2 weeks (MVP)

---

## Overview

### Problem Statement
- No aggregated view of Claude Code usage over time
- Token consumption invisible until billing arrives
- Difficult to identify cost drivers or optimization opportunities
- No model performance comparison data

**Impact:**
- Reactive cost management (post-incident)
- Suboptimal model selection (default rather than informed)
- Missed optimization patterns

### Proposed Solution
Historical usage analytics with weekly/monthly trends, token forecasting, and cost breakdown by model/task type.

### Success Metrics
| Metric | Target |
|--------|--------|
| Usability | Generate report in <30 seconds |
| Insight Depth | Identify top 3 cost drivers within 5 min |
| Cost Impact | 15-20% reduction via model optimization |

---

## Requirements

### Functional Requirements
1. Display token usage trends (daily/weekly/monthly)
2. Show model distribution (Haiku/Sonnet/Opus breakdown)
3. Calculate cost breakdown per model and task type
4. Export data in CSV, JSON, and HTML formats
5. Generate reports via `/2025-compiled:generate` command

### Non-Functional Requirements
- All processing local to device (no remote transmission)
- Report generation < 30 seconds
- Compatible with existing usage logs

### Out of Scope
- Real-time monitoring (use Barista for that)
- Cross-user comparison
- Automatic optimization actions

---

## Technical Design

### Installation & Activation

```bash
# Install package
pip install claude-code-wrapped

# Register plugin (one-time)
/plugin marketplace add miguelrios/2025-compiled

# Generate stats
/2025-compiled:generate [--period=monthly] [--export=json|csv|html]
```

### Stats Provided

| Metric | Granularity | Use Case |
|--------|-------------|----------|
| **Token Usage** | Daily/Weekly/Monthly | Trend analysis, forecasting |
| **Model Distribution** | By model | Cost optimization |
| **Cost Breakdown** | Per-model, per-task-type | Budget planning |
| **Session Duration** | Average, peak times | Workflow optimization |
| **Context Window Utilization** | Percentile distribution | Context efficiency |

### Data Model
- Reads from `~/.claude/usage-logs/` (existing)
- Aggregates without storing prompt content
- Supports data retention policy (--purge-before flag)

### Dependencies
- Python 3.8+
- Existing Claude Code usage logs

---

## Implementation Plan

### Phase 1: MVP (Week 1)
- [ ] Package installation & plugin registration
- [ ] Basic dashboard: token trends, model distribution
- [ ] CSV export for historical data
- [ ] Documentation & setup guide

### Phase 2: Enhanced Analytics (Week 2+)
- [ ] Cost forecasting (next 30 days)
- [ ] Anomaly detection (spike alerts)
- [ ] Per-project usage segmentation

### Future Considerations
- Comparison benchmarking (team average)
- Automated recommendations
- Integration with CTM for task cost tracking

---

## Verification Criteria

### Installation Test
- [ ] `pip install claude-code-wrapped` completes without errors
- [ ] Plugin registers successfully

### Functional Tests
- [ ] Dashboard displays last 30 days of usage
- [ ] Cost breakdown matches monthly bill (±5%)
- [ ] CSV export parseable and complete

### UAT Scenarios
1. Generate monthly report and identify top cost driver
2. Export data to CSV, import to spreadsheet
3. Compare Haiku vs Sonnet usage ratio

---

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|------------|-----------|
| Log file corruption | Low | Snapshot on read, rollback flag |
| Large log size impact | Medium | Incremental indexing, compression |
| Privacy concerns | Low | Full transparency, local-only processing |

---

## Timeline Estimate

| Milestone | Target | Effort |
|-----------|--------|--------|
| MVP Release | +1 week | 4 hours |
| Phase 2 | +2 weeks | 8 hours |

**Total Effort:** ~12 hours (Tier 1 - Quick Win)
