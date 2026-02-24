# PRD: CTM-002 - Wave-Based Parallelism for Agent Spawning

> Maximize parallelism while respecting system load limits through coordinated wave execution

## Overview

### Problem Statement

Current CTM agent spawning has two problematic modes:

**Sequential (Current Default):**
- Agents spawn one at a time via CDP
- Total execution time = sum of all agent durations
- Wastes time when agents have no dependencies
- Example: 5 agents × 2 min each = 10 minutes total

**Uncontrolled Parallel (Manual):**
- User manually spawns multiple agents at once
- No load management
- Can overwhelm system (CPU/memory/token limits)
- Resource profile limits ignored
- Example: Spawning 10 agents on "conservative" profile (max 3)

**The Gap:**
Neither mode provides intelligent parallelism - spawn as many agents as system allows, wait for wave completion, then spawn next wave.

### Proposed Solution

Implement **wave-based parallelism**: organize agents into dependency waves, spawn each wave in parallel while respecting system limits, wait for wave completion before starting next wave.

**New behavior:**
```bash
$ ctm delegate --waves auth2026

Analyzing task graph...

Wave 1 (3 agents - no dependencies):
  ○ design-auth-flow
  ○ review-oauth-providers
  ○ draft-auth-docs
Spawning wave 1... [system load: OK, profile: balanced (max 4)]
  ✓ design-auth-flow started
  ✓ review-oauth-providers started
  ✓ draft-auth-docs started

Waiting for wave 1 completion... [3/3 active]
  ✓ design-auth-flow completed (45s)
  ✓ review-oauth-providers completed (32s)
  ✓ draft-auth-docs completed (28s)

Wave 2 (2 agents - depends on wave 1):
  ○ implement-oauth-routes (blocked_by: design-auth-flow)
  ○ integrate-auth-docs (blocked_by: draft-auth-docs)
Spawning wave 2... [system load: OK]
  ✓ implement-oauth-routes started
  ✓ integrate-auth-docs started

Total: 5 agents in 2 waves (~2.5 min vs 5 min sequential)
```

### Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Time savings | >40% reduction vs sequential | Compare wave execution vs sequential baseline |
| Load violations | 0 spawns exceeding profile limits | Check `check-load.sh` before each spawn |
| Wave coordination accuracy | >95% correct wave assignment | Verify dependency graph correctness |
| User satisfaction | "Faster without overloading system" | Qualitative feedback |

---

## Requirements

### Functional Requirements

**FR-1: Dependency Graph Construction**

Build directed acyclic graph (DAG) from agent `blocked_by` relationships:

```python
# Agent schema
{
  "id": "impl-auth",
  "dependencies": {
    "blocked_by": ["design-auth"],  # Parent dependencies
    "blocks": ["test-auth"]         # Child dependents (derived)
  }
}
```

**FR-2: Wave Assignment Algorithm**

Assign agents to waves using topological sort:

```
Wave N = {agents with no dependencies OR all dependencies in waves 1..N-1}
```

**FR-3: Resource-Aware Wave Spawning**

Before spawning wave:
1. Check system load via `check-load.sh`
2. Check active agent count vs profile limit
3. If load HIGH or limit reached: wait
4. Spawn agents in wave (parallel)

**FR-4: Wave Completion Detection**

Monitor spawned agents until wave completes:
- Poll agent status every 5 seconds
- Wave complete when all agents status ∈ {completed, cancelled, blocked}
- Show progress: `[3/5 active] [2 completed]`

**FR-5: Wave Execution Commands**

```bash
# Delegate with waves (auto-detect dependencies)
$ ctm delegate --waves auth2026

# Delegate with explicit wave definition
$ ctm delegate --waves --wave-file task-waves.yaml

# Dry-run wave analysis
$ ctm waves auth2026 --dry-run
```

**FR-6: Wave Visualization**

Show wave structure before execution:

```
Wave Structure for [auth2026]:

Wave 1 (3 agents - parallel):
  ○ design-auth-flow
  ○ review-oauth-providers
  ○ draft-auth-docs

Wave 2 (2 agents - depends on Wave 1):
  ○ implement-oauth-routes ← design-auth-flow
  ○ integrate-auth-docs ← draft-auth-docs

Wave 3 (1 agent - depends on Wave 2):
  ○ test-auth-integration ← implement-oauth-routes

Estimated time: ~3-4 min (vs 7 min sequential)
```

**FR-7: Resource Profile Integration**

Respect existing resource profiles during wave spawning:

| Profile | Max Parallel | Wave Behavior |
|---------|--------------|---------------|
| `conservative` | 3 | Max 3 agents per wave |
| `balanced` | 4 | Max 4 agents per wave |
| `performance` | 6 | Max 6 agents per wave |

If wave size exceeds limit, split into sub-waves.

**FR-8: Error Handling**

- If agent in wave fails: continue wave, mark dependents as blocked
- If wave has no completions after 10 min: timeout warning
- Allow user to abort wave execution (Ctrl+C)

### Non-Functional Requirements

**NFR-1: Performance**

- Wave assignment algorithm: O(N + E) where N=agents, E=dependencies
- Status polling interval: 5 seconds (configurable)
- Max wave execution time: 30 minutes (timeout)

**NFR-2: Backward Compatibility**

- `ctm delegate` without `--waves` uses sequential mode (existing behavior)
- Wave-based execution is opt-in

**NFR-3: Observability**

- Log wave execution to `~/.claude/ctm/logs/wave-execution.log`
- Track metrics: wave count, agents per wave, time savings

**NFR-4: Resilience**

- Filesystem-based coordination (no external dependencies)
- Survive Claude Code restarts (resume incomplete waves)

### Out of Scope

- **Dynamic wave re-planning** - Won't adjust waves mid-execution (Phase 2)
- **Cross-project wave coordination** - Single project only (Phase 2)
- **Priority-based wave scheduling** - FIFO within wave (Phase 2)
- **Distributed wave execution** - Single machine only (Phase 3)

---

## Technical Design

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  ctm delegate --waves <id>                  │
└────────────────┬────────────────────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────────────────────┐
│              Wave Coordinator                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 1. Build dependency graph from agent.dependencies    │   │
│  │ 2. Topological sort → assign waves                   │   │
│  │ 3. Validate: no cycles, all deps resolvable         │   │
│  │ 4. Display wave structure                            │   │
│  │ 5. For each wave:                                    │   │
│  │    a. Check load (check-load.sh --can-spawn)        │   │
│  │    b. Spawn agents in wave (parallel)               │   │
│  │    c. Poll until wave complete                       │   │
│  │    d. Update dependents (unblock next wave)          │   │
│  │ 6. Report completion metrics                         │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Data Model

**Wave State File:** `~/.claude/ctm/waves/<wave-id>.json`

```json
{
  "wave_id": "wave-abc123",
  "parent_agent": "auth2026",
  "created_at": "2026-02-03T10:00:00Z",
  "status": "running",
  "waves": [
    {
      "wave_number": 1,
      "agents": ["design-auth", "review-oauth", "draft-docs"],
      "status": "completed",
      "started_at": "2026-02-03T10:00:05Z",
      "completed_at": "2026-02-03T10:02:30Z",
      "duration_seconds": 145
    },
    {
      "wave_number": 2,
      "agents": ["impl-oauth", "integrate-docs"],
      "status": "running",
      "started_at": "2026-02-03T10:02:35Z",
      "completed_at": null
    }
  ],
  "metrics": {
    "total_agents": 5,
    "total_waves": 3,
    "estimated_sequential_time": 420,
    "actual_parallel_time": null
  }
}
```

**Agent Schema Extension:**

```json
{
  "dependencies": {
    "blocked_by": ["design-auth-flow"],
    "blocks": ["test-auth"],
    "wave": 2
  }
}
```

### API/Interface Changes

**New Module:** `~/.claude/ctm/lib/waves.py`

```python
from typing import List, Dict, Set
from dataclasses import dataclass

@dataclass
class Wave:
    number: int
    agents: List[str]
    dependencies: Set[str]
    status: str

def build_dependency_graph(agents: List[Agent]) -> Dict[str, Set[str]]:
    """Build adjacency list from agent.dependencies.blocked_by"""
    pass

def topological_sort_waves(graph: Dict[str, Set[str]]) -> List[Wave]:
    """Assign agents to waves using Kahn's algorithm"""
    pass

def validate_graph(graph: Dict[str, Set[str]]) -> bool:
    """Check for cycles and unresolvable dependencies"""
    pass

def can_spawn_wave(wave: Wave, profile: str) -> bool:
    """Check if wave can spawn given system load + profile"""
    pass

def spawn_wave(wave: Wave) -> List[str]:
    """Spawn all agents in wave (parallel), return agent IDs"""
    pass

def wait_for_wave(wave: Wave, timeout_seconds: int = 600) -> bool:
    """Poll agents until wave completes or timeout"""
    pass

def execute_waves(waves: List[Wave], profile: str) -> WaveExecutionResult:
    """Execute all waves sequentially"""
    pass
```

### Dependencies

**Python Standard Library:**
- `subprocess` - Spawn agents, check load
- `time` - Polling intervals
- `json` - Wave state persistence

**CTM Modules:**
- `agents.py` - Load/update agent dependencies
- `scheduler.py` - Check active agent count
- `config.py` - Load resource profile

**External:**
- `~/.claude/scripts/check-load.sh` - System load check

---

## Implementation Plan

### Phase 1 (MVP) - Estimated: 10 hours

**Goal:** Basic wave coordination with manual dependency specification

**Deliverables:**
- [ ] `waves.py` module with graph construction
- [ ] Topological sort algorithm (Kahn's)
- [ ] Wave state persistence
- [ ] `ctm delegate --waves` command
- [ ] Wave completion polling (5s interval)
- [ ] Resource profile integration
- [ ] Basic error handling (agent failure)

**Testing:**
- Create 5 agents with 2-wave dependency structure
- Execute waves with "balanced" profile (max 4)
- Verify parallel execution (wave 1: 3 agents spawn together)
- Verify sequential waves (wave 2 waits for wave 1)

### Phase 2 (Enhancement) - Estimated: 6 hours

**Goal:** Advanced features and optimization

**Deliverables:**
- [ ] Wave visualization with ASCII diagram
- [ ] Dry-run mode (`--dry-run`)
- [ ] Wave file support (YAML definition)
- [ ] Sub-wave splitting for large waves
- [ ] Resume incomplete waves after restart
- [ ] Metrics tracking and reporting

**Testing:**
- Execute 10-agent task with 4 waves
- Test large wave (8 agents) on "conservative" profile (splits into 3+3+2)
- Interrupt mid-execution, verify resume

### Phase 3 (Future Considerations)

- Dynamic wave re-planning based on agent failures
- Priority-based wave scheduling (high-priority agents first)
- Cross-project wave coordination
- Distributed wave execution (multiple machines)

---

## Verification Criteria

### Unit Tests

**`test_waves.py`:**
- `test_build_dependency_graph()` - Graph construction
- `test_topological_sort_simple()` - Linear dependencies
- `test_topological_sort_branching()` - Multiple paths
- `test_validate_graph_cycle()` - Cycle detection
- `test_can_spawn_wave_under_limit()` - Profile limits
- `test_can_spawn_wave_over_limit()` - Load rejection

### Integration Tests

**Scenario 1: Simple Wave Execution**
1. Create 5 agents: 3 in wave 1, 2 in wave 2
2. Execute with `--waves`
3. Verify wave 1 spawns 3 agents in parallel
4. Verify wave 2 waits for wave 1 completion
5. Measure total time < 3 minutes

**Scenario 2: Resource Profile Enforcement**
1. Set profile to "conservative" (max 3)
2. Create wave with 5 agents
3. Execute
4. Verify max 3 agents active at any time

**Scenario 3: Agent Failure Handling**
1. Create 2-wave structure
2. Fail agent in wave 1
3. Verify dependent in wave 2 marked blocked
4. Verify non-dependent in wave 2 still executes

### UAT Scenarios

**UAT-1: First-Time User**
- User has task with 6 subtasks
- Runs `ctm delegate --waves`
- System shows wave structure
- User confirms execution
- Observes parallel execution

**UAT-2: Power User**
- User creates custom wave file (YAML)
- Specifies explicit waves and dependencies
- Executes with `--wave-file`
- Verifies custom wave structure honored

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Cycle in dependency graph | High | Low | Validate graph before execution, clear error message |
| System overload despite checks | Medium | Medium | Conservative load thresholds, allow user abort |
| Wave coordination state corruption | Medium | Low | Atomic writes, backup before execution |
| Agent status polling misses completion | Low | Low | 5s polling + final check before next wave |
| Long wave execution blocks progress | Medium | Medium | 30min timeout, allow abort |

---

## Timeline Estimate

| Phase | Effort | Duration |
|-------|--------|----------|
| Phase 1 (MVP) | 10 hours | 2 days |
| Phase 2 (Enhancement) | 6 hours | 1 day |
| Testing & Polish | 4 hours | 0.5 day |
| **Total** | **20 hours** | **3-4 days** |

**Priority:** Medium impact, Medium effort
**Recommendation:** Implement Phase 1 within 1 month, Phase 2 as demand emerges

---

*PRD Version: 1.0*
*Created: 2026-02-03*
*Author: Claude (Worker Agent)*
