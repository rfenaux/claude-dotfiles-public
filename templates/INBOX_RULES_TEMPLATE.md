# Inbox Rules Configuration

> Project-specific file routing rules for the 00-inbox/ drop zone.
> Copy this template to `project/00-inbox/INBOX_RULES.md` and customize.

---

## Configuration

```yaml
# Enable automatic moving for high-confidence matches
auto_move: true

# Minimum confidence required for auto-move (0.0 - 1.0)
confidence_threshold: 0.9

# Log all actions to .inbox_log.json
logging: true
```

## Smart Renaming (Phase 2)

```yaml
renaming:
  enabled: true
  date_prefix: true           # Add YYYY-MM-DD prefix for chronological sorting
  normalize_case: kebab       # kebab-case (default), snake_case, or none
  semantic_prefix: true       # Add TRANSCRIPT-, SPEC-, etc. based on content
```

**Semantic Prefixes (auto-detected):**
| Content Type | Prefix | Keywords |
|--------------|--------|----------|
| Transcripts | `TRANSCRIPT-` | transcript, attendees, fathom, zoom |
| Specifications | `SPEC-` | specification, system design, architecture |
| Requirements | `REQ-` | requirements, user story, FR-, NFR- |
| Meeting Notes | `NOTES-` | meeting notes, minutes, agenda |
| Data Exports | `DATA-` | export, report, analytics, KPI |
| SOW | `SOW-` | statement of work, deliverables, milestones |
| Integrations | `INT-` | integration, api, webhook, sync |

**Example Renames:**
- `notes from client call.txt` → `2026-01-23-NOTES-client-call.txt`
- `Transcript - Discovery - Rescue.txt` → `2026-01-23-TRANSCRIPT-discovery-rescue.txt`
- `budget v2 FINAL.xlsx` → `2026-01-23-budget-v2.xlsx`

**Disable renaming:** Set `renaming.enabled: false` or use `--no-rename` flag.

---

## Rules

Rules are evaluated in order: pattern > extension > content > fallback.
First matching rule wins.

### Pattern Rules (Highest Priority)

Match by filename glob pattern. Most specific, highest confidence.

```yaml
patterns:
  # Meeting transcripts (Fathom, Zoom, etc.)
  - pattern: "Transcript - *"
    destination: 01-client-inputs/transcripts/
    action: auto_move
    confidence: 0.95

  # SOW and contracts
  - pattern: "SOW*"
    destination: 01-client-inputs/sow/
    action: auto_move
    confidence: 0.95

  - pattern: "Statement of Work*"
    destination: 01-client-inputs/sow/
    action: auto_move
    confidence: 0.95

  - pattern: "Contract*"
    destination: 01-client-inputs/sow/
    action: auto_move
    confidence: 0.95

  # Invoices and receipts
  - pattern: "Invoice*"
    destination: 01-client-inputs/finance/
    action: auto_move
    confidence: 0.90

  - pattern: "Receipt*"
    destination: 01-client-inputs/finance/
    action: auto_move
    confidence: 0.90

  # Explicit drafts
  - pattern: "DRAFT_*"
    destination: 05-working-drafts/
    action: auto_move
    confidence: 0.95

  # Experiments and temporary files
  - pattern: "temp_*"
    destination: 05-working-drafts/experiments/
    action: auto_move
    confidence: 0.90

  - pattern: "exp_*"
    destination: 05-working-drafts/experiments/
    action: auto_move
    confidence: 0.90

  # Versioned deliverables
  - pattern: "*_V[0-9]*"
    destination: 04-client-deliverables/current/
    action: suggest
    confidence: 0.75
```

### Extension Rules (Medium Priority)

Match by file extension. Broader categories.

```yaml
extensions:
  # Documents - likely client inputs
  - extensions: [.pdf]
    destination: 01-client-inputs/
    action: suggest
    confidence: 0.70

  - extensions: [.docx, .doc]
    destination: 01-client-inputs/
    action: suggest
    confidence: 0.70

  # Spreadsheets - data exports
  - extensions: [.xlsx, .xls, .csv]
    destination: 01-client-inputs/data-exports/
    action: suggest
    confidence: 0.70

  # Images - screenshots and assets
  - extensions: [.png, .jpg, .jpeg, .gif, .webp]
    destination: 05-working-drafts/assets/
    action: auto_move
    confidence: 0.85

  # Markdown - knowledge base or drafts
  - extensions: [.md]
    destination: 02-knowledge-base/
    action: suggest
    confidence: 0.60

  # Code files - implementation
  - extensions: [.py]
    destination: 03-solution-design/implementation/
    action: suggest
    confidence: 0.65

  - extensions: [.js, .ts]
    destination: 03-solution-design/implementation/
    action: suggest
    confidence: 0.65

  # JSON - could be schemas or data
  - extensions: [.json]
    destination: 03-solution-design/implementation/
    action: suggest
    confidence: 0.55

  # YAML - config or workflow
  - extensions: [.yaml, .yml]
    destination: 03-solution-design/implementation/
    action: suggest
    confidence: 0.55

  # Presentations
  - extensions: [.pptx, .ppt]
    destination: 04-client-deliverables/presentations/
    action: suggest
    confidence: 0.70

  # Archives
  - extensions: [.zip, .tar, .gz]
    destination: 06-staging/to-review/
    action: suggest
    confidence: 0.50
```

### Content Rules (Lower Priority)

Match by keywords in file content (text files only).

```yaml
content:
  # HubSpot-related
  - contains: ["HubSpot", "workflow", "automation", "custom object"]
    destination: 03-solution-design/implementation/
    action: suggest
    confidence_boost: 0.15

  # ERD and data modeling
  - contains: ["ERD", "entity", "relationship", "cardinality"]
    destination: 03-solution-design/current/
    action: suggest
    confidence_boost: 0.15

  # Requirements
  - contains: ["requirement", "FR-", "NFR-", "user story"]
    destination: 02-knowledge-base/
    action: suggest
    confidence_boost: 0.10

  # Meeting notes
  - contains: ["action item", "attendees", "agenda", "minutes"]
    destination: 01-client-inputs/transcripts/
    action: suggest
    confidence_boost: 0.10
```

---

## Fallback

Files that don't match any rule go to staging for manual review.

```yaml
fallback:
  destination: 06-staging/to-review/
  action: move_to_staging
  message: "No matching rule found. Moved to staging for manual review."
```

---

## Actions Reference

| Action | Behavior |
|--------|----------|
| `auto_move` | Move immediately if confidence >= threshold |
| `suggest` | Present suggestion, wait for user confirmation |
| `move_to_staging` | Move to fallback location |
| `skip` | Leave file in inbox (for rules that exclude files) |

---

## Customization Examples

### Add project-specific patterns

```yaml
# Example: Client uses specific naming convention
patterns:
  - pattern: "ACME-*"
    destination: 01-client-inputs/
    action: auto_move
    confidence: 0.95
```

### Exclude certain files

```yaml
# Example: Never auto-process large media files
extensions:
  - extensions: [.mp4, .mov, .avi]
    action: skip
    message: "Large media files require manual handling"
```

### Override default destination

```yaml
# Example: PDFs should go to a specific folder for this project
extensions:
  - extensions: [.pdf]
    destination: 01-client-inputs/legal/  # Override default
    action: suggest
    confidence: 0.75
```

---

## File Naming on Move

When moving files, the organizer may rename to avoid conflicts:

| Scenario | Behavior |
|----------|----------|
| File exists at destination | Append timestamp: `file_2026-01-23_103459.pdf` |
| Invalid characters | Replace with underscore |
| Spaces in filename | Keep as-is (spaces are allowed) |

---

## Version

Template version: 1.0
Compatible with: file-inbox-organizer skill v1.0+
