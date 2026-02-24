---
name: refactor
description: "Multi-file refactoring pipeline with dependency analysis, ordered workers, and consistency checking"
triggers:
  - "/refactor"
  - "refactor rename"
  - "rename across files"
---

# Refactor Skill

Multi-file refactoring with dependency analysis, git branch safety, and consistency validation.

## Commands

| Command | Description |
|---------|-------------|
| `/refactor rename <old> <new> [--scope <dir>]` | Rename identifier across all files |
| `/refactor status` | Show current refactoring state |
| `/refactor rollback` | Abort and return to original branch |

## Workflow: `/refactor rename`

When user invokes `/refactor rename <old_name> <new_name>`:

### Step 1: Safety Check
```bash
# Ensure we're in a git repo with clean state
git status --porcelain
```
If dirty, warn user and offer to stash.

### Step 2: Analyze Dependencies
```bash
python3 ~/.claude/scripts/analyze-dependencies.py <scope> <old_name> --json
```
Parse output to understand:
- Which files reference `<old_name>`
- Dependency order (batches for parallel processing)
- Import graph

Show user a summary:
```
Found <N> files referencing "<old_name>" in <scope>
Batches: <N> (files per batch: <counts>)
Dependencies detected: <list>

Proceed? [y/n]
```

### Step 3: Create Refactoring Branch
```bash
~/.claude/scripts/refactoring-branch.sh create <old_name> <new_name>
```
This creates `refactor/<old>-to-<new>-<timestamp>` branch.

### Step 4: Execute Renames (Batch-Ordered)

For each batch from the dependency analysis (in order):
1. **Within a batch**, files are independent — process them with Edit tool
2. For each file:
   - Read the file
   - Replace `<old_name>` with `<new_name>` using Edit tool (preserve context)
   - Handle special cases:
     - Class definitions: `class OldName` -> `class NewName`
     - Function definitions: `def old_name` -> `def new_name`
     - Imports: update `import` and `from...import` statements
     - String references: update `"OldName"` in JSON, configs
     - Documentation: update references in .md files
3. **Wait for batch to complete** before moving to next batch

### Step 5: Consistency Check

After all batches complete:
1. Search for remaining references to `<old_name>`:
   ```bash
   grep -rn "<old_name>" <scope> --include="*.py" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" --include="*.json" --include="*.md"
   ```
2. If references found in code (not just comments):
   - Show user the remaining references
   - Offer to fix or rollback

### Step 6: Commit or Rollback

If consistency check passes:
```bash
~/.claude/scripts/refactoring-branch.sh commit "refactor: rename <old_name> to <new_name>"
```

If user wants to rollback:
```bash
~/.claude/scripts/refactoring-branch.sh rollback
```

## Workflow: `/refactor status`

```bash
~/.claude/scripts/refactoring-branch.sh status
```

## Workflow: `/refactor rollback`

```bash
~/.claude/scripts/refactoring-branch.sh rollback
```

## Error Handling

- **Not a git repo**: Abort with error message
- **Dirty working tree**: Offer to stash, abort, or proceed with warning
- **No files found**: Report "No references to <old_name> found in <scope>"
- **Consistency check fails**: Show issues, offer fix or rollback
- **Worker fails**: Stop remaining batches, show partial progress, offer rollback

## Notes

- Always works on a separate git branch for safety
- Never modifies files outside the specified scope
- Preserves dependency order to avoid broken intermediate states
- Handles Python (ast-based) and TypeScript/JS (regex-based) imports
