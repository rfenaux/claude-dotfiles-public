# PRD: File Inbox Organizer

> Auto-organize dropped files into standardized project structure

## Problem Statement

When working on projects, files arrive from multiple sources:
- Client emails (PDFs, spreadsheets, documents)
- Fathom transcripts
- Screenshots and screen recordings
- Downloaded resources
- Generated exports

Currently, these files land in Downloads or project root, requiring manual sorting. This breaks the standardized 00-06 folder structure and creates clutter.

## Solution Overview

A **drop-inbox pattern** with intelligent file routing:

```
project/
├── 00-inbox/                    # NEW: Drop zone for incoming files
│   ├── INBOX_RULES.md           # Project-specific routing rules
│   └── [dropped files...]
│
├── 00-project-meta/             # Existing structure unchanged
├── 01-client-inputs/
├── 02-knowledge-base/
├── 03-solution-design/
├── 04-client-deliverables/
├── 05-working-drafts/
└── 06-staging/
```

## Design Principles

### 1. Human-in-the-Loop (Not Fully Automatic)

Following [Dropbox's Smart Move research](https://dropbox.tech/machine-learning/smart-move-ml-ai-file-organization-automation):
- **Suggest** destination with confidence level
- **Auto-move** only when confidence ≥ 90% AND rule explicitly allows
- **Ask for confirmation** otherwise

### 2. Rule-Based + Pattern Matching

Priority order:
1. **Explicit rules** in `INBOX_RULES.md`
2. **File type mapping** (PDF → 01-client-inputs/, .md → 02-knowledge-base/)
3. **Name pattern matching** (Transcript - * → 01-client-inputs/transcripts/)
4. **Content analysis** (if readable text, detect keywords)

### 3. Project-Specific Customization

Each project defines its own `INBOX_RULES.md`:

```yaml
# 00-inbox/INBOX_RULES.md

auto_move: true  # Enable auto-move for high-confidence matches
confidence_threshold: 0.9  # 90% confidence required for auto-move

rules:
  # By filename pattern (highest priority)
  - pattern: "Transcript - *"
    destination: 01-client-inputs/transcripts/
    action: auto_move

  - pattern: "SOW*|Statement of Work*"
    destination: 01-client-inputs/sow/
    action: auto_move

  - pattern: "Invoice*|Receipt*"
    destination: 01-client-inputs/finance/
    action: auto_move

  # By file extension
  - extension: [.pdf, .docx]
    destination: 01-client-inputs/
    action: suggest  # Needs human confirmation

  - extension: [.xlsx, .csv]
    destination: 01-client-inputs/data-exports/
    action: suggest

  - extension: [.png, .jpg, .gif]
    destination: 05-working-drafts/assets/
    action: auto_move

  - extension: [.py, .js, .ts]
    destination: 03-solution-design/implementation/
    action: suggest

  # By content keywords (only for text-readable files)
  - contains: ["HubSpot", "workflow", "automation"]
    destination: 03-solution-design/implementation/workflows/
    action: suggest

  - contains: ["ERD", "entity", "relationship"]
    destination: 03-solution-design/current/
    action: suggest

# Fallback for unmatched files
fallback:
  destination: 06-staging/to-review/
  action: move_to_staging
```

## Components

### 1. `file-inbox-organizer` Skill

**Location:** `~/.claude/skills/file-inbox-organizer/`

**Triggers:**
- `/inbox` - Process all files in 00-inbox/
- `/inbox sort <file>` - Sort specific file
- `/inbox rules` - Show/edit current rules
- `/inbox dry-run` - Preview without moving

**Workflow:**
```
1. Scan 00-inbox/ for files
2. For each file:
   a. Load INBOX_RULES.md
   b. Match against rules (pattern → extension → content)
   c. Calculate confidence score
   d. If confidence ≥ threshold AND action=auto_move:
      - Move file to destination
      - Log action to 00-inbox/.inbox_log.json
   e. Else:
      - Present suggestion with confidence
      - Wait for user confirmation
3. Report summary
```

### 2. `inbox-watcher` Hook (Optional)

**Location:** `~/.claude/hooks/PostToolUse/inbox-watcher.sh`

**Trigger:** After Write tool creates file in project

**Behavior:**
- If file created in 00-inbox/, trigger skill automatically
- Light-touch: only runs for inbox folder

### 3. `inbox-init` Command

**Purpose:** Initialize inbox structure in a project

**Creates:**
- `00-inbox/` folder
- `00-inbox/INBOX_RULES.md` (from template)
- `00-inbox/.inbox_log.json` (action history)
- `00-inbox/.gitignore` (optional: ignore staging files)

### 4. Updates to `directory-organization-expert`

Add inbox awareness:
- Include 00-inbox/ in standard structure
- Validate INBOX_RULES.md syntax
- Audit for orphaned files

## File Routing Matrix (Defaults)

| Pattern / Extension | Default Destination | Action | Notes |
|---------------------|---------------------|--------|-------|
| `Transcript - *` | 01-client-inputs/transcripts/ | auto_move | Fathom exports |
| `SOW*`, `Contract*` | 01-client-inputs/sow/ | auto_move | Legal docs |
| `*.pdf`, `*.docx` | 01-client-inputs/ | suggest | Client materials |
| `*.xlsx`, `*.csv` | 01-client-inputs/data-exports/ | suggest | Data files |
| `*.png`, `*.jpg`, `*.gif` | 05-working-drafts/assets/ | auto_move | Screenshots |
| `*.md` | 02-knowledge-base/ | suggest | Documentation |
| `*.py`, `*.js`, `*.ts` | 03-solution-design/implementation/ | suggest | Code |
| `*.json` (schema) | 03-solution-design/implementation/custom-objects/ | suggest | HubSpot schemas |
| `DRAFT_*` | 05-working-drafts/ | auto_move | Explicit drafts |
| `temp_*`, `exp_*` | 05-working-drafts/experiments/ | auto_move | Experiments |
| `*_V[0-9]*` | 04-client-deliverables/ | suggest | Versioned deliverables |
| Unmatched | 06-staging/to-review/ | fallback | Manual review |

## Global vs Project-Level

| Scope | Location | Purpose |
|-------|----------|---------|
| Global defaults | `~/.claude/templates/INBOX_RULES_TEMPLATE.md` | Default rules for new projects |
| Project overrides | `project/00-inbox/INBOX_RULES.md` | Project-specific customization |

Global rules provide sensible defaults; project rules can:
- Override destinations
- Add project-specific patterns
- Disable certain auto-moves
- Define custom categories

## Smart File Renaming (Phase 2)

Files are renamed during organization for better RAG indexing and retrieval.

### Renaming Rules

| Original Pattern | Renamed Pattern | Example |
|------------------|-----------------|---------|
| Generic names | Date prefix + kebab-case | `notes.pdf` → `2026-01-23-notes.pdf` |
| Transcripts | Date + TRANSCRIPT prefix | `Transcript - Discovery - Client.txt` → `2026-01-23-TRANSCRIPT-client-discovery.txt` |
| Versioned files | Normalize version suffix | `budget v2 FINAL.xlsx` → `2026-01-23-budget-v2.xlsx` |
| Spaces & special chars | Kebab-case | `My File (1).pdf` → `2026-01-23-my-file.pdf` |

### Configuration

```yaml
# In INBOX_RULES.md
renaming:
  enabled: true
  date_prefix: true           # Add YYYY-MM-DD prefix
  normalize_case: kebab       # kebab-case, snake_case, or none
  semantic_prefix: auto       # Add TRANSCRIPT-, SPEC-, etc.
  preserve_original: log      # 'log' saves to .inbox_log.json, 'metadata' adds to file
```

### Semantic Prefixes

| Detected Content | Prefix |
|------------------|--------|
| Transcripts (Fathom, Zoom) | `TRANSCRIPT-` |
| Specifications | `SPEC-` |
| Requirements | `REQ-` |
| Meeting notes | `NOTES-` |
| Data exports | `DATA-` |
| Images/Screenshots | (no prefix, just date) |

### Opt-Out

- Per-file: Use `--no-rename` flag
- Per-rule: Add `rename: false` to rule definition
- Global: Set `renaming.enabled: false` in INBOX_RULES.md

## Edge Cases

### 1. Duplicate Filenames
- Append timestamp: `Report.pdf` → `Report_2026-01-23_101023.pdf`
- Log warning in .inbox_log.json

### 2. Large Files (>10MB)
- Skip content analysis
- Rely on pattern/extension only
- Log for manual review

### 3. Binary Files
- No content analysis
- Pattern + extension only

### 4. Immutable Folders
- `01-client-inputs/` receives files but user must confirm
- Never auto-modify existing files in 01-

### 5. Conflicts with Existing Files
- Don't overwrite
- Rename with suffix
- Alert user

## Logging & Audit Trail

`00-inbox/.inbox_log.json`:
```json
{
  "version": "1.0",
  "entries": [
    {
      "timestamp": "2026-01-23T10:15:30Z",
      "file": "Transcript - Discovery - Client - Jan 23.txt",
      "source": "00-inbox/",
      "destination": "01-client-inputs/transcripts/",
      "rule_matched": "pattern:Transcript - *",
      "confidence": 0.95,
      "action": "auto_move",
      "status": "success"
    },
    {
      "timestamp": "2026-01-23T10:16:45Z",
      "file": "requirements.xlsx",
      "source": "00-inbox/",
      "destination": "01-client-inputs/data-exports/",
      "rule_matched": "extension:.xlsx",
      "confidence": 0.75,
      "action": "user_confirmed",
      "status": "success"
    }
  ]
}
```

## User Experience Flow

### Happy Path
```
User: *drops file into 00-inbox/*
User: /inbox

Claude: Found 3 files in inbox:

1. ✅ AUTO-MOVED: Transcript - Discovery - Rescue - Jan 23.txt
   → 01-client-inputs/transcripts/ (95% confidence)

2. 📋 SUGGESTION: budget_proposal.xlsx
   → 01-client-inputs/data-exports/ (75% confidence)
   Confirm? [Y/n/other]

3. ❓ UNKNOWN: misc_notes.txt
   → 06-staging/to-review/ (fallback)
   Where should this go?
```

### Dry Run
```
User: /inbox dry-run

Claude: DRY RUN - No files will be moved

1. Transcript - Discovery.txt → 01-client-inputs/transcripts/ (auto_move)
2. budget.xlsx → 01-client-inputs/data-exports/ (suggest)
3. notes.txt → 06-staging/to-review/ (fallback)

Run `/inbox` to execute.
```

## Implementation Phases

### Phase 1: MVP (Core Functionality)
- [ ] Create skill: `file-inbox-organizer`
- [ ] Implement rule parser for INBOX_RULES.md
- [ ] Pattern matching (glob-style)
- [ ] Extension-based routing
- [ ] Manual confirmation flow
- [ ] Basic logging

### Phase 2: Intelligence
- [ ] Content keyword detection (text files)
- [ ] Confidence scoring algorithm
- [ ] Auto-move for high-confidence matches
- [ ] Dry-run mode

### Phase 3: Automation
- [ ] PostToolUse hook for inbox watching
- [ ] Integration with RAG indexing (index after move)
- [ ] Batch processing for multiple files

### Phase 4: Polish
- [ ] `inbox-init` command
- [ ] Global template management
- [ ] Audit trail visualization
- [ ] Weekly staging cleanup reminder

## Success Metrics

| Metric | Target |
|--------|--------|
| Files auto-sorted correctly | >90% |
| User confirmations required | <30% of files |
| Time from drop to organized | <5 seconds (auto) |
| Inbox cleanup frequency | Daily or per-session |

## Non-Goals

- **Full automation without oversight** - Human always has final say
- **Cross-project organization** - Each project is independent
- **File content modification** - Only moves/renames, never edits
- **Cloud sync integration** - Local filesystem only

## Dependencies

- Existing 00-06 folder structure in projects
- `directory-organization-expert` agent for structure validation
- RAG system for post-move indexing (optional)

## Decisions Made

1. **Folder naming: `00-inbox/`** ✅
   - Consistent with 00-06 numbering scheme
   - Sorts first alphabetically

2. **Scope: Both project-level AND global** ✅
   - Project: `project/00-inbox/` for client files
   - Global: `~/.claude/inbox/` for Claude config files (agents, skills, templates)

3. **Nested inbox folders** — Deferred to Phase 4
   - Keep MVP simple with flat inbox

4. **Finder integration** — Out of scope for MVP

---

## References

- [Dropbox Automation Options](https://help.dropbox.com/organize/dropbox-automations)
- [Dropbox Smart Move ML Research](https://dropbox.tech/machine-learning/smart-move-ml-ai-file-organization-automation)
- [File Organization Best Practices 2025](https://thedrive.ai/blog/best-file-organization-software-2025)
- Existing: `~/.claude/agents/directory-organization-expert.md`
- Existing: Project structure in Tool-Presale-Claude, ISMS-Claude

---

*PRD Version: 1.0*
*Created: 2026-01-23*
*Author: Claude + Raphael*
