---
name: pm-decompose
description: Break specs or CTM tasks into dependency-aware sub-tasks. Creates CTM tasks with dependencies, deadlines, and parallel flags. Use after /pm-spec or when a task needs breaking down.
async:
  mode: never
  require_sync:
    - task review and confirmation
    - dependency validation
context: fork
---

# PM-Decompose - Task Decomposition Engine

Breaks specifications or CTM tasks into dependency-aware sub-tasks with effort estimates and parallelization guidance.

## Trigger

Invoke this skill when:
- User says "/pm-decompose", "break this down", "decompose", "create subtasks"
- After creating a spec with `/pm-spec`
- User has a large task that needs structuring
- Planning implementation phases for a project

## Description

PM-Decompose analyzes specs or CTM tasks and generates 5-12 sub-tasks with:
- Effort classification (S/M/L/XL)
- Phase grouping (Foundation → Core → Polish)
- Dependency mapping (which tasks block which)
- Parallelization opportunities
- Integration with CTM for automatic task creation

### Key Features
- **Smart Analysis**: Extracts phases from specs automatically
- **Dependency Detection**: Identifies blocking relationships
- **Effort Estimation**: S (1 day), M (2-3 days), L (4-5 days), XL (1+ week)
- **Parallel Groups**: Tags tasks that can run concurrently
- **ASCII Tree**: Visual breakdown for review
- **CTM Integration**: One-command task creation with dependencies

## Commands

```bash
# Decompose Sources
/pm-decompose {spec-name}              # Decompose a spec file
/pm-decompose {ctm-task-id}            # Decompose existing CTM task
/pm-decompose                          # Interactive - pick source

# Options
/pm-decompose {source} --dry-run       # Show breakdown without creating
/pm-decompose {source} --todo          # Use TodoWrite instead of CTM (session-scoped)
/pm-decompose {source} --max-tasks 10  # Limit number of tasks

# Utilities
/pm-decompose --help                   # Show usage
```

## Workflow

1. **Read Source** - Load spec from `.claude/specs/{name}.md` OR CTM task context

2. **Analyze Phases** - Extract implementation phases from spec:
   - Phase 1: Foundation/Setup
   - Phase 2: Core Implementation
   - Phase 3: Polish/Testing

3. **Generate Tasks** - Create 5-12 tasks (max 15), each representing 1-3 days of work
   - Task naming: `{spec-id}-{sequential-number} {descriptive-name}`
   - Example: `auth-001 Setup scaffolding`, `auth-002 Database schema`

4. **Classify Tasks**:
   - **Effort**: S (1d), M (2-3d), L (4-5d), XL (1w+)
   - **Phase**: Phase 1, Phase 2, Phase 3
   - **Parallel Group**: Tasks that can run concurrently
   - **Priority**: Based on phase and dependencies

5. **Identify Dependencies** - Determine blocking relationships:
   - Database schema blocks API endpoints
   - API endpoints block frontend components
   - Core features block tests

6. **Present ASCII Tree** - Show breakdown for user review:
   ```
   Spec: user-auth | 8 tasks | Est: 5 days

   Phase 1: Foundation (parallel group 1)
     [S] auth-001  Setup scaffolding
     [M] auth-002  Database schema + migrations

   Phase 2: Core (group 2, after Phase 1)
     [M] auth-003  JWT service              <- blocked by auth-002
     [L] auth-004  API endpoints            <- blocked by auth-002
     [M] auth-005  Frontend components       (parallel with 003, 004)

   Phase 3: Polish (after Phase 2)
     [S] auth-006  Error handling           <- blocked by 003, 004
     [M] auth-007  Integration tests        <- blocked by 003, 004, 005
     [S] auth-008  Documentation             (parallel with 007)

   Parallelizable: 5/8 | Sequential bottleneck: Phase 1->2->3
   ```

7. **User Confirms** - Before creating tasks, ask for approval:
   - Adjust task breakdown if needed
   - Modify dependencies
   - Change effort estimates

8. **Create CTM Tasks** - Execute task creation:
   ```bash
   ctm spawn "auth-001 Setup scaffolding" --priority medium
   ctm spawn "auth-002 Database schema" --priority high
   ctm spawn "auth-003 JWT service" --priority high --blocked-by auth-002
   ctm spawn "auth-004 API endpoints" --priority high --blocked-by auth-002
   # ... etc
   ```

9. **Update Spec** - Add "## Tasks Created" section to spec with task IDs

10. **Chain** - Suggest next step: `/pm-gh-sync --push --filter {spec-id}`

## Task Breakdown Principles

### Effort Classification

| Size | Duration | Complexity | Example |
|------|----------|------------|---------|
| S | 1 day | Simple, well-defined | Setup config, write tests |
| M | 2-3 days | Moderate, some unknowns | API endpoints, UI components |
| L | 4-5 days | Complex, research needed | Integration layer, migration |
| XL | 1+ week | Very complex, high uncertainty | New subsystem, architecture |

### Dependency Types

- **Sequential**: Task B cannot start until Task A completes
- **Parallel**: Tasks can run concurrently
- **Soft Dependency**: Task B benefits from Task A but not blocked

### Phase Guidelines

- **Phase 1**: Infrastructure, scaffolding, database schema, core configs
- **Phase 2**: Business logic, API endpoints, UI components, integrations
- **Phase 3**: Testing, error handling, documentation, polish

## Integration with CTM

PM-Decompose creates CTM tasks with:
- **Metadata**: Links back to spec (`source.spec_id`)
- **Dependencies**: Uses `ctm block --by` for task relationships
- **Deadlines**: Inferred from phase sequencing
- **Tags**: Spec ID tag for filtering

## Best Practices

1. **Keep tasks atomic** - Each task should be completable in 1-3 days
2. **Identify critical path** - Know which tasks block progress
3. **Enable parallelization** - Tag independent tasks for concurrent work
4. **Review before creating** - Adjust breakdown based on team capacity
5. **Link to spec** - Maintain traceability from spec to tasks

## Files

| Path | Purpose |
|------|---------|
| `project/.claude/specs/{name}.md` | Source spec (updated with task list) |
| `~/.claude/ctm/agents/*.json` | Created CTM tasks |
| `project/.claude/pm-decompose-cache.json` | Cached breakdowns for re-runs |

## Example Workflow

```bash
# Decompose a spec
/pm-decompose user-authentication

# Review ASCII tree
# User approves

# Tasks created in CTM:
# - auth-001 Setup scaffolding (S)
# - auth-002 Database schema (M)
# - auth-003 JWT service (M, blocked by auth-002)
# - auth-004 API endpoints (L, blocked by auth-002)
# - auth-005 Frontend components (M, parallel with auth-003/004)
# - auth-006 Error handling (S, blocked by auth-003/004)
# - auth-007 Integration tests (M, blocked by auth-003/004/005)
# - auth-008 Documentation (S, parallel with auth-007)

# Spec updated with task list
# Suggested: /pm-gh-sync --push --filter user-authentication
```

## Dry Run Mode

Use `--dry-run` to preview breakdown without creating tasks:
```bash
/pm-decompose user-authentication --dry-run
```

Shows ASCII tree and effort estimates without CTM task creation.

## TodoWrite Mode

Use `--todo` for session-scoped task lists instead of CTM:
```bash
/pm-decompose user-authentication --todo
```

Creates TodoWrite checklist instead of CTM tasks. Useful for quick explorations.
