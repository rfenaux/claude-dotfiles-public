---
name: file-inbox-organizer
description: Process files dropped in 00-inbox/ and route them to appropriate project folders based on configurable rules.
trigger: /inbox
context: fork
agent: general-purpose
model: sonnet
tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
async:
  mode: never
  require_sync:
    - user confirmation for suggestions
    - interactive routing decisions
---

# File Inbox Organizer Skill

Intelligent file routing from a drop-inbox (00-inbox/) to standardized project folders.

## Triggers

Invoke when user says:
- `/inbox` — Process all files in inbox
- `/inbox sort` — Same as /inbox
- `/inbox sort <file>` — Process specific file
- `/inbox dry-run` — Preview routing without moving
- `/inbox rules` — Show current routing rules
- `/inbox log` — Show recent actions from .inbox_log.json
- `/inbox init` — Initialize inbox in current project

## Prerequisites

- Project should have the standard 00-06 folder structure
- `00-inbox/INBOX_RULES.md` should exist (use `/inbox init` to create)

## Workflow

### Phase 1: Discovery

1. **Locate inbox folder:**
```bash
# Check if 00-inbox/ exists
if [ -d "00-inbox" ]; then
    echo "Inbox found: 00-inbox/"
else
    echo "No inbox found. Run /inbox init to create one."
    exit 1
fi
```

2. **Scan for files:**
```bash
# List files in inbox (excluding INBOX_RULES.md and hidden files)
find 00-inbox -maxdepth 1 -type f ! -name "INBOX_RULES.md" ! -name ".*" 2>/dev/null
```

3. **Load rules:**
   - Read `00-inbox/INBOX_RULES.md`
   - Parse YAML configuration blocks
   - Build rule matching order: patterns → extensions → content

### Phase 2: Classification

For each file in inbox:

1. **Extract file info:**
   - Filename
   - Extension
   - Size (skip content analysis if > 10MB)
   - Is text-readable?

2. **Match against rules in order:**

   a. **Pattern matching:**
   ```python
   # Use fnmatch for glob patterns
   import fnmatch
   for rule in patterns:
       if fnmatch.fnmatch(filename, rule['pattern']):
           return rule, rule['confidence']
   ```

   b. **Extension matching:**
   ```python
   ext = os.path.splitext(filename)[1].lower()
   for rule in extensions:
       if ext in rule['extensions']:
           return rule, rule['confidence']
   ```

   c. **Content matching (text files only, < 10MB):**
   ```python
   if is_text_file and size < 10_000_000:
       content = read_file(filepath)
       for rule in content_rules:
           if any(kw.lower() in content.lower() for kw in rule['contains']):
               # Boost confidence of best matching rule
               best_rule.confidence += rule['confidence_boost']
   ```

3. **Determine action:**
   - If `confidence >= threshold` AND `action == auto_move`: Auto-move
   - If `action == suggest`: Add to suggestions list
   - If no match: Use fallback (06-staging/to-review/)

### Phase 3: Execution

**For auto-move files:**
```python
def auto_move(file, destination):
    # Ensure destination exists
    os.makedirs(destination, exist_ok=True)

    # Handle filename conflicts
    dest_path = os.path.join(destination, filename)
    if os.path.exists(dest_path):
        # Append timestamp
        base, ext = os.path.splitext(filename)
        timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        filename = f"{base}_{timestamp}{ext}"
        dest_path = os.path.join(destination, filename)

    # Move file
    shutil.move(file, dest_path)

    # Log action
    log_action(file, dest_path, 'auto_move', confidence)
```

**For suggestions:**
Present to user:
```
Found 3 files in inbox:

1. AUTO-MOVED: Transcript - Discovery - Client - Jan 23.txt
   → 01-client-inputs/transcripts/ (95% confidence)

2. SUGGESTION: budget_proposal.xlsx
   → 01-client-inputs/data-exports/ (75% confidence)
   [Y]es / [N]o / [O]ther path / [S]kip

3. UNKNOWN: random_notes.txt
   → 06-staging/to-review/ (fallback)
   [Y]es / [O]ther path / [S]kip
```

Wait for user input on each suggestion.

### Phase 4: Logging

Append to `00-inbox/.inbox_log.json`:
```json
{
  "timestamp": "2026-01-23T10:35:00Z",
  "file": "budget_proposal.xlsx",
  "source": "00-inbox/budget_proposal.xlsx",
  "destination": "01-client-inputs/data-exports/budget_proposal.xlsx",
  "rule_matched": "extension:.xlsx",
  "confidence": 0.75,
  "action": "user_confirmed",
  "status": "success"
}
```

### Phase 5: Summary

Output final summary:
```
═══ Inbox Processed ═══

Auto-moved: 2 files
  • Transcript - Discovery.txt → 01-client-inputs/transcripts/
  • screenshot.png → 05-working-drafts/assets/

User-confirmed: 1 file
  • budget_proposal.xlsx → 01-client-inputs/data-exports/

Skipped: 0 files
Fallback: 1 file
  • random_notes.txt → 06-staging/to-review/

Inbox is now empty.
```

## Dry-Run Mode

When `/inbox dry-run`:
- Run all classification logic
- Display what WOULD happen
- Do NOT move any files
- Do NOT update log

Output:
```
DRY RUN - No files will be moved

1. Transcript - Discovery.txt
   Rule: pattern:Transcript - *
   Action: auto_move (95% confidence)
   Would move to: 01-client-inputs/transcripts/

2. budget_proposal.xlsx
   Rule: extension:.xlsx
   Action: suggest (75% confidence)
   Would suggest: 01-client-inputs/data-exports/

Run `/inbox` to execute.
```

## Rules Command

When `/inbox rules`:
```
═══ Current Inbox Rules ═══

Source: 00-inbox/INBOX_RULES.md
Auto-move threshold: 90%

Pattern Rules (8):
  • Transcript - * → 01-client-inputs/transcripts/ (auto_move)
  • SOW* → 01-client-inputs/sow/ (auto_move)
  • DRAFT_* → 05-working-drafts/ (auto_move)
  ...

Extension Rules (12):
  • .pdf → 01-client-inputs/ (suggest)
  • .xlsx, .csv → 01-client-inputs/data-exports/ (suggest)
  ...

Content Rules (4):
  • [HubSpot, workflow] → confidence +15%
  ...

Fallback: 06-staging/to-review/
```

## Init Command

When `/inbox init`:

1. Create `00-inbox/` directory
2. Copy template from `~/.claude/templates/INBOX_RULES_TEMPLATE.md`
3. Create empty `.inbox_log.json`
4. Optionally add `.gitignore` for temp files

```bash
mkdir -p 00-inbox
cp ~/.claude/templates/INBOX_RULES_TEMPLATE.md 00-inbox/INBOX_RULES.md
echo '{"version":"1.0","entries":[]}' > 00-inbox/.inbox_log.json
```

Output:
```
═══ Inbox Initialized ═══

Created: 00-inbox/
  • INBOX_RULES.md (default rules)
  • .inbox_log.json (action log)

Next steps:
1. Drop files into 00-inbox/
2. Run /inbox to process them
3. Edit INBOX_RULES.md to customize routing
```

## Global Inbox (Claude Config)

For global Claude configuration files, use `~/.claude/inbox/`:

```
~/.claude/inbox/
├── INBOX_RULES.md    # Global rules
└── [dropped files]
```

Global routing destinations:
| Pattern | Destination |
|---------|-------------|
| `*-agent.md`, `*_agent.md` | ~/.claude/agents/ |
| `SKILL.md`, `*-skill/` | ~/.claude/skills/ |
| `*.sh` (hooks) | ~/.claude/hooks/ |
| `PRD-*.md` | ~/.claude/prds/ |
| `*_TEMPLATE.md` | ~/.claude/templates/ |
| `*_GUIDE.md` | ~/.claude/docs/ |

## Error Handling

| Error | Handling |
|-------|----------|
| No inbox folder | Suggest `/inbox init` |
| Empty inbox | Report "Inbox is empty" |
| Rule parse error | Warn, continue with defaults |
| Move fails | Log error, leave file in inbox |
| Destination doesn't exist | Create it automatically |

## Related Skills

- `init-project` — Full project initialization (includes inbox setup option)
- `rag-batch-index` — Index moved files to RAG
- `directory-organization-expert` — Audit folder structure

## MCP Integration

After successful moves, optionally trigger RAG indexing:
```python
# If .rag/ exists and file is indexable
if os.path.exists('.rag') and is_rag_indexable(file):
    mcp__rag-server__rag_index(path=dest_path, project_path=project_root)
```
