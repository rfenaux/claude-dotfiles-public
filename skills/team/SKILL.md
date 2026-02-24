---
name: team
description: "Spawn and manage Agent Teams from predefined templates with health monitoring"
triggers:
  - "/team"
  - "team spawn"
  - "spawn a team"
---

# Team Skill

Spawn and manage Agent Teams using predefined templates.

## Commands

| Command | Description |
|---------|-------------|
| `/team spawn <template> <name>` | Spawn a team from template |
| `/team status [name]` | Show team status |
| `/team shutdown [name]` | Gracefully shut down a team |
| `/team health [name]` | Run health check on team |
| `/team templates` | List available templates |

## Available Templates

| Template | Agents | Use For |
|----------|--------|---------|
| `research-team` | 3 (2 researchers + 1 synthesizer) | Research, analysis, knowledge gaps |
| `implementation-team` | 4 (1 architect + 2 workers + 1 reviewer) | Feature implementation |
| `refactoring-team` | 4 (1 orchestrator + 2 workers + 1 checker) | Multi-file refactoring (requires F3) |

## Workflow: `/team spawn <template> <name>`

### Step 1: Load Template
```python
# Read template from config
template = json.load(open("~/.claude/config/team-templates.json"))["templates"][template_name]
```

### Step 2: Pre-flight Checks
1. **Load check**: Run `~/.claude/scripts/check-load.sh --can-spawn`
   - If HIGH_LOAD, warn user and offer to wait or proceed with fewer agents
2. **Agent limit**: Verify `active_agents + template.team_size <= MAX_PARALLEL`
3. **Dependencies**: If template has `requires`, verify agent files exist
4. **Existing team**: Check if a team with this name already exists

### Step 3: Create Team
```
TeamCreate(team_name=<name>, description=<template.description>)
```

### Step 4: Create Tasks
Based on user's request, create tasks appropriate for the template's workflow:
- `research-team`: Create parallel research tasks + synthesis task
- `implementation-team`: Create plan task → implementation tasks → review task
- `refactoring-team`: Create analysis task → rename tasks → validation task

### Step 5: Spawn Teammates
For each member in the template:
```
Task(
    subagent_type=member.subagent_type,
    model=member.model,
    name=member.name,
    team_name=<name>,
    prompt=<role-specific instructions>
)
```

### Step 6: Start Health Monitor (background)
```bash
TEAM_NAME=<name> ~/.claude/scripts/check-team-health.sh &
```

### Step 7: Assign Tasks
Use `TaskUpdate` to set `owner` for each initial task.

## Workflow: `/team status`

Read team config and task list:
```
~/.claude/teams/<name>/config.json  → members
TaskList                              → tasks + status
```

Output:
```
Team: <name> (<template>)
Members: <count> active
Tasks: <completed>/<total> complete
  - [done] Task 1 (owner: researcher-1)
  - [in_progress] Task 2 (owner: worker-1)
  - [pending] Task 3 (blocked by: Task 2)
```

## Workflow: `/team shutdown`

1. Send `shutdown_request` to each teammate
2. Wait for confirmations
3. Stop health monitor: `~/.claude/scripts/check-team-health.sh --stop <name>`
4. Call `TeamDelete`

## Workflow: `/team health`

```bash
~/.claude/scripts/check-team-health.sh --check-once <name>
```

## Error Handling

- **Template not found**: List available templates
- **Load too high**: Suggest waiting or using smaller team
- **Agent limit reached**: Show current usage, suggest freeing slots
- **Teammate spawn fails**: Log error, try spawning replacement, warn user
- **All tasks complete unexpectedly**: Verify results, initiate shutdown

## Notes

- Teams require `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` environment variable
- Teams are token-intensive — use for complex tasks only
- Health monitoring runs in background, logs to `~/.claude/logs/team-health.log`
- Team configs stored at `~/.claude/teams/<name>/config.json`
- Task lists stored at `~/.claude/tasks/<name>/`
