---
name: flowchart
description: Generate interactive HTML flowcharts from text descriptions. Supports decision trees, process flows, and swimlanes with brand customization.
async:
  mode: optional
  optimal_for:
    - complex multi-stage flows
    - brand-customized output
---

# /flowchart - HTML Flowchart Generator

Create interactive HTML flowcharts from text descriptions. Outputs standalone HTML files with CSS styling and optional brand customization.

## Trigger

Invoke this skill when:
- User says "/flowchart", "create flowchart", "visualize process"
- User provides process steps and says "diagram", "flow", "visualization"
- User wants a decision tree or workflow diagram
- User mentions "swimlane", "process flow", "BPMN"

## Why This Exists

Meta-analysis identified repeated pattern of manual HTML flowchart creation. This skill automates the process with consistent styling and brand support.

## Behavior

### 1. Parse Input
Extract from user description:
- **Stages**: Sequential steps in the process
- **Decisions**: Yes/no branch points
- **Actors**: For swimlane diagrams
- **Connections**: Flow between elements

### 2. Generate Structure
Create flowchart data model:
```javascript
{
  type: "process" | "decision-tree" | "swimlane",
  elements: [
    { id: "1", type: "start", label: "..." },
    { id: "2", type: "process", label: "..." },
    { id: "3", type: "decision", label: "...", yes: "4", no: "5" },
    { id: "4", type: "end", label: "..." }
  ]
}
```

### 3. Apply Styling
Check for brand customization:
- If `BRAND_KIT.md` exists in project → Use brand colors
- If not → Use default professional palette

Default colors:
| Element | Color |
|---------|-------|
| Start/End | #22c55e (green) |
| Process | #3b82f6 (blue) |
| Decision | #f59e0b (amber) |
| Connector | #6b7280 (gray) |

### 4. Generate HTML
Output standalone HTML with:
- Embedded CSS (no external dependencies)
- SVG-based connectors
- Hover states and tooltips
- Print-friendly styling
- Responsive layout

## Commands

```bash
/flowchart                        # Interactive mode - asks for input
/flowchart "Step 1 → Step 2"      # Quick inline flow
/flowchart --swimlane             # Create swimlane diagram
/flowchart --brand                # Force brand colors
/flowchart --output path.html     # Specify output path
```

## Output Structure

```html
<!DOCTYPE html>
<html>
<head>
  <title>Process Flow</title>
  <style>
    /* Embedded styles */
    .flowchart { ... }
    .stage { ... }
    .decision { ... }
    .connector { ... }
  </style>
</head>
<body>
  <div class="flowchart">
    <div class="stage start">Start</div>
    <div class="connector">↓</div>
    <div class="stage process">Process Step</div>
    <div class="connector">↓</div>
    <div class="decision">Decision?</div>
    <!-- ... -->
  </div>
</body>
</html>
```

## Diagram Types

### Process Flow (default)
Linear sequence with optional branches:
```
[Start] → [Step 1] → [Step 2] → [End]
```

### Decision Tree
Binary branches at decision points:
```
[Start] → <Decision?> → Yes → [Action A]
                      → No  → [Action B]
```

### Swimlane
Actors in horizontal lanes:
```
| Sales    | [Lead] → [Qualify] |
| Marketing| [Nurture] → [MQL]  |
| Ops      | [Route] → [Assign] |
```

## Files

| Path | Purpose |
|------|---------|
| `project/BRAND_KIT.md` | Brand colors (optional) |
| Output varies | Generated HTML file |

## Example

```
User: /flowchart

Create a lead qualification flow:
1. New lead received
2. Check if company exists in CRM
3. If yes → Associate contact
4. If no → Create company first
5. Assign to owner
6. Send welcome email

Claude: Creating flowchart...

Generated: lead-qualification-flow.html

Preview:
┌──────────────┐
│  New Lead    │
└──────┬───────┘
       ↓
┌──────────────┐
│ Company in   │
│   CRM?       │◆──No──→ Create Company
└──────┬───────┘              │
       │ Yes                  │
       ↓                      ↓
┌──────────────┐        ┌──────────────┐
│  Associate   │←───────│              │
│   Contact    │        └──────────────┘
└──────┬───────┘
       ↓
┌──────────────┐
│ Assign Owner │
└──────┬───────┘
       ↓
┌──────────────┐
│ Send Welcome │
└──────────────┘

Open in browser? [Y/n]
```

## Integration

- **Brand Kit**: Reads `BRAND_KIT.md` for custom colors
- **BPMN Specialist**: For complex diagrams, may delegate to `bpmn-specialist` agent
- **Lucidchart**: For export, can generate Lucidchart-compatible format
