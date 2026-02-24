---
name: pm-gh-sync
description: Bidirectional sync between CTM tasks and GitHub Issues. Push tasks to GitHub, pull issues into CTM, sync status. Use after /pm-decompose or for GitHub tracking.
async:
  mode: auto
  prefer_background:
    - bulk push of many tasks
    - full bidirectional sync
  require_sync:
    - interactive pull selection
    - conflict resolution
context: fork
---

# PM-GH-Sync - GitHub Issues Sync

Bidirectional synchronization between CTM tasks and GitHub Issues with label management, dependency mapping, and status tracking.

## Trigger

Invoke this skill when:
- User says "/pm-gh-sync", "push to github", "sync issues", "import issue"
- After decomposing tasks with `/pm-decompose`
- User wants GitHub tracking for CTM tasks
- User wants to import GitHub issues into CTM

## Description

PM-GH-Sync maintains bidirectional sync between CTM and GitHub Issues:
- **Push**: Create GitHub issues from CTM tasks with labels and dependencies
- **Pull**: Import GitHub issues into CTM as tasks
- **Status Sync**: Keep CTM and GitHub issue states aligned
- **Label Management**: Auto-create and apply standard labels

### Key Features
- **Auto Label Creation**: Creates standard labels (priority, effort, status) if missing
- **Dependency Mapping**: "Blocked by #N" in issue body for GitHub task lists
- **Metadata Tracking**: Stores mapping in `.claude/gh-sync-map.json`
- **Conflict Detection**: Warns when CTM and GitHub states diverge
- **Spec Filtering**: Push only tasks from specific specs

## Commands

```bash
# Push (CTM -> GitHub)
/pm-gh-sync --push                     # Push all unsynced CTM tasks
/pm-gh-sync --push --filter {spec-id}  # Push tasks from specific spec
/pm-gh-sync --push --tag {tag}         # Push tasks with specific tag

# Pull (GitHub -> CTM)
/pm-gh-sync --pull                     # Interactive - list issues, user picks
/pm-gh-sync --pull {issue-number}      # Import specific issue

# Sync
/pm-gh-sync --status                   # Bidirectional status sync
/pm-gh-sync --map                      # Show current mapping

# Utilities
/pm-gh-sync --labels                   # Show/create labels
/pm-gh-sync --help                     # Usage guide
```

## Workflow: Push (CTM -> GitHub)

1. **Detect Repo** - Get repo from `git remote get-url origin`
   - Parse owner/repo from URL
   - Verify gh CLI is authenticated

2. **Find Unsynced Tasks** - Query CTM for tasks without `metadata.source.github_url`
   - Apply filters (spec_id, tag) if specified
   - Show count to user

3. **Ensure Labels Exist** - Check/create labels via `gh label create`
   - Status labels: `in-progress`, `blocked`, `on-hold`
   - Priority labels: `priority:critical`, `priority:high`, `priority:normal`, `priority:low`
   - Effort labels: `effort:S`, `effort:M`, `effort:L`, `effort:XL`
   - Use colors from `~/.claude/config/gh-sync-labels.json`

4. **Create Issues** - For each task:
   ```bash
   gh issue create \
     --title "{task-title}" \
     --body "{formatted-body}" \
     --label "{priority-label}" \
     --label "{effort-label}" \
     --label "{status-label}"
   ```

5. **Format Issue Body**:
   ```markdown
   **Spec**: {spec_id}
   **CTM Task**: {task_id}
   **Effort**: {S|M|L|XL}
   **Priority**: {critical|high|normal|low}

   {task-description}

   ## Context
   {task-context}

   ## Acceptance Criteria
   {criteria}

   ## Dependencies
   - Blocked by #{issue-number} ({task-title})
   ```

6. **Map Dependencies** - Convert CTM task dependencies to GitHub issue references

7. **Update CTM** - Add GitHub metadata to task:
   ```json
   "metadata": {
     "source": {
       "type": "ctm-task",
       "github_url": "https://github.com/owner/repo/issues/42",
       "github_issue": 42,
       "synced_at": "2026-02-07T14:30:00Z"
     }
   }
   ```

8. **Save Mapping** - Update `project/.claude/gh-sync-map.json`

9. **Summary** - Report created issues with links

## Workflow: Pull (GitHub -> CTM)

1. **List Issues** - Run `gh issue list --state open --limit 50`
   - Display: issue number, title, labels, assignee

2. **User Picks** - Interactive selection or specific issue number

3. **Create CTM Tasks** - For each selected issue:
   ```bash
   ctm spawn "{issue-title}" --priority {priority} --metadata source.type=github-issue
   ```

4. **Extract Metadata**:
   - Priority from `priority:*` label
   - Effort from `effort:*` label
   - Description from issue body

5. **Update CTM** - Add GitHub metadata:
   ```json
   "metadata": {
     "source": {
       "type": "github-issue",
       "github_url": "https://github.com/owner/repo/issues/42",
       "github_issue": 42,
       "imported_at": "2026-02-07T14:30:00Z"
     }
   }
   ```

6. **Save Mapping** - Update mapping file

7. **Summary** - Report imported tasks

## Workflow: Status Sync

1. **Read Mapping** - Load `project/.claude/gh-sync-map.json`

2. **Compare States**:
   - CTM completed + GitHub open → Offer to close issue
   - GitHub closed + CTM active → Ask user to mark CTM complete or reopen issue
   - CTM blocked + GitHub in-progress → Suggest label update

3. **Apply Changes**:
   ```bash
   # Close issue
   gh issue close {issue-number} --comment "Completed in CTM task {task-id}"

   # Reopen issue
   gh issue reopen {issue-number} --comment "Reopened from CTM"

   # Update labels
   gh issue edit {issue-number} --add-label "blocked" --remove-label "in-progress"
   ```

4. **Update Mapping** - Sync timestamps

5. **Summary** - Report synced tasks

## Mapping File

**Location**: `project/.claude/gh-sync-map.json`

```json
{
  "repo": "owner/repo",
  "synced_at": "2026-02-07T14:30:00Z",
  "tasks": [
    {
      "ctm_id": "abc123",
      "github_issue": 42,
      "spec_id": "user-authentication",
      "direction": "push|pull",
      "last_synced": "2026-02-07T14:30:00Z",
      "status_synced": true
    }
  ]
}
```

## Label Configuration

**Location**: `~/.claude/config/gh-sync-labels.json`

```json
{
  "status_labels": {
    "active": { "name": "in-progress", "color": "0E8A16" },
    "blocked": { "name": "blocked", "color": "D93F0B" },
    "paused": { "name": "on-hold", "color": "FBCA04" }
  },
  "priority_labels": {
    "critical": { "name": "priority:critical", "color": "B60205" },
    "high": { "name": "priority:high", "color": "D93F0B" },
    "normal": { "name": "priority:normal", "color": "0075CA" },
    "low": { "name": "priority:low", "color": "E4E669" }
  },
  "effort_labels": {
    "S": { "name": "effort:S", "color": "C2E0C6" },
    "M": { "name": "effort:M", "color": "BFD4F2" },
    "L": { "name": "effort:L", "color": "D4C5F9" },
    "XL": { "name": "effort:XL", "color": "F9D0C4" }
  }
}
```

## Integration with CTM

PM-GH-Sync uses CTM metadata:
- `metadata.source.type`: "ctm-task" (pushed) or "github-issue" (pulled)
- `metadata.source.github_url`: Issue URL
- `metadata.source.github_issue`: Issue number
- `metadata.source.synced_at`: Last sync timestamp

## Best Practices

1. **Push after decompose** - Immediately push tasks to GitHub for visibility
2. **Filter by spec** - Push related tasks together
3. **Sync regularly** - Run `--status` to keep states aligned
4. **Review conflicts** - Don't auto-resolve divergent states
5. **Use labels** - Standard labels enable filtering and reporting

## Files

| Path | Purpose |
|------|---------|
| `project/.claude/gh-sync-map.json` | Task-issue mapping |
| `~/.claude/config/gh-sync-labels.json` | Label definitions |
| `~/.claude/ctm/agents/*.json` | CTM tasks with GitHub metadata |

## Example Workflow

```bash
# After decomposing a spec
/pm-decompose user-authentication

# Push tasks to GitHub
/pm-gh-sync --push --filter user-authentication

# Created 8 issues:
# - #42 auth-001 Setup scaffolding
# - #43 auth-002 Database schema
# - #44 auth-003 JWT service (blocked by #43)
# - #45 auth-004 API endpoints (blocked by #43)
# - #46 auth-005 Frontend components
# - #47 auth-006 Error handling (blocked by #44, #45)
# - #48 auth-007 Integration tests (blocked by #44, #45, #46)
# - #49 auth-008 Documentation

# Later: sync status
/pm-gh-sync --status

# Detected: CTM task auth-001 completed, GitHub #42 still open
# Action: Close #42? [y/n]
```

## Error Handling

- **No git repo**: Warn user, suggest `git init` or `git remote add`
- **gh CLI not authenticated**: Show `gh auth login` instructions
- **Label creation fails**: Warn but continue (issue creation may fail)
- **Mapping file conflicts**: Show diff, ask user to resolve
- **Duplicate issues**: Warn if task already has GitHub URL

## Async Behavior

- **Bulk push** (>5 tasks): Prefer background execution
- **Full sync**: Prefer background execution
- **Interactive pull**: Require sync (user selection needed)
- **Conflict resolution**: Require sync (user decisions needed)
