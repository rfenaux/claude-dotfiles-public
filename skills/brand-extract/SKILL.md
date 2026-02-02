---
name: brand-extract
description: "Extract brand identity (colors, typography, logos) from websites and documents. Creates Claude-consumable BRAND_KIT.md for consistent styling across all generated documents. Invoke with /brand-extract <url> or /brand-extract <file-path>."
trigger: /brand-extract
model: sonnet
tools:
  - Read
  - WebFetch
  - Write
context: fork
async:
  mode: auto
  prefer_background:
    - multiple sources
    - bulk extraction
  require_sync:
    - single source review
    - brand kit approval
---

# Brand Extract - Brand Identity Extraction Skill

## Overview

Extract comprehensive brand identity from websites and/or documents to generate a **Claude-consumable brand kit** for consistent styling across all generated documents (PPTX, PDF, HTML, etc.).

## Quick Start

```bash
# From a website
/brand-extract https://example.com

# From a document
/brand-extract /path/to/brand-guidelines.pdf

# From multiple sources
/brand-extract https://example.com /path/to/deck.pptx /path/to/logo.png

# With output location
/brand-extract https://example.com --output /path/to/project
```

## What Gets Extracted

| Source | Elements Extracted |
|--------|-------------------|
| **Website** | CSS colors, typography, logos, favicons, theme colors |
| **PPTX** | Theme colors (accent1-6), fonts (major/minor), logos |
| **PDF** | Colors, fonts, embedded images/logos |
| **DOCX** | Style colors, fonts, header/footer images |
| **Images** | Dominant colors, logo detection |

## Output Structure

Creates `.claude/brand/` in the project directory:

```
.claude/brand/
├── BRAND_KIT.md          # Claude-consumable master reference
├── brand-tokens.json     # Design tokens for programmatic use
├── assets/
│   ├── logo-primary.{png,svg}
│   ├── logo-monochrome.{png,svg}
│   └── favicon.{ico,png}
└── preview.html          # Visual swatch preview
```

## Workflow

### Step 1: Invoke the Skill

When user says `/brand-extract <source>`:

1. Parse the source(s) - URL, file path(s), or both
2. Determine output location (default: current project `.claude/brand/`)
3. Delegate to `brand-kit-extractor` orchestrator agent

### Step 2: Extraction (Automatic)

The orchestrator delegates to specialized sub-agents:

| Source Type | Agent |
|-------------|-------|
| URL | `brand-extract-web` |
| PDF/DOCX/PPTX/images | `brand-extract-docs` |

Agents run in parallel when multiple sources provided.

### Step 3: Compilation

`brand-kit-compiler` processes raw extractions:
- Clusters similar colors
- Classifies color roles (primary, secondary, accent, neutral)
- Calculates WCAG accessibility scores
- Deduplicates typography
- Organizes assets

### Step 4: Output Generation

Generates all output files and presents for user review.

## BRAND_KIT.md Format

The main output file is structured for Claude consumption:

```markdown
# Brand Kit: {Company Name}

> **Extracted:** {date}
> **Sources:** {list}
> **Confidence:** {score}

## Color Palette

### Primary Colors
| Role | Name | Hex | RGB | HSL | Usage |
|------|------|-----|-----|-----|-------|
| Primary | Brand Blue | `#1E3A5F` | rgb(30,58,95) | hsl(214,52%,25%) | Headers, CTAs |

### Accessibility Matrix
| Foreground | Background | Contrast | WCAG AA | WCAG AAA |
|------------|------------|----------|---------|----------|
| `#FFFFFF` | `#1E3A5F` | 8.4:1 | ✓ | ✓ |

## Typography
| Role | Font Family | Weights | Fallback Stack |
|------|-------------|---------|----------------|
| Headings | Montserrat | 600, 700 | `Montserrat, sans-serif` |

## Assets
| Asset | Path | Usage |
|-------|------|-------|
| Logo (Primary) | `assets/logo-primary.svg` | Headers, documents |

## Quick Reference for Claude
Primary Color: #1E3A5F
Heading Font: Montserrat
Logo Path: assets/logo-primary.svg
```

## Integration with Other Skills

Once a brand kit exists, these skills/agents auto-detect and apply it:

| Skill/Agent | How It Uses Brand Kit |
|-------------|----------------------|
| `pptx` | Applies colors to theme, uses logo on title slide |
| `slide-deck-creator` | Full brand application |
| `visual-documentation-skills` | Uses palette in HTML diagrams |
| `pandoc-pdf-generation` | Injects colors into LaTeX |

### Detection Pattern

Skills check for brand kit at startup:

```python
brand_kit_path = f"{project_root}/.claude/brand/BRAND_KIT.md"
if exists(brand_kit_path):
    brand_kit = parse_brand_kit(brand_kit_path)
    apply_brand_colors(brand_kit)
```

## Advanced Options

### Deep Extraction Mode

For JS-heavy websites, use browser automation:

```bash
/brand-extract https://example.com --deep
```

This uses Playwright/Puppeteer to:
- Render JavaScript
- Extract computed styles
- Capture screenshots for color analysis

### Force Refresh

Re-extract even if brand kit exists:

```bash
/brand-extract https://example.com --force
```

### Specific Output Location

```bash
/brand-extract https://example.com --output /path/to/project
```

## Python Dependencies

For document extraction, ensure these are installed:

```bash
pip install python-pptx pdfplumber PyMuPDF python-docx Pillow colorthief
```

For browser automation (optional):

```bash
pip install playwright
playwright install chromium
```

## Error Handling

| Issue | Behavior |
|-------|----------|
| URL unreachable | Report error, continue with other sources |
| File not found | Report error, skip file |
| No colors found | Warn user, suggest manual review |
| Low confidence (<50%) | Warn user, present partial results |

## Examples

### Extract from <COMPANY> website

```
User: /brand-extract https://<company>.com

Claude: Extracting brand identity from https://<company>.com...

[Spawning brand-extract-web agent...]

Brand Kit generated at .claude/brand/

**Colors Found:**
| Role | Hex | Usage |
|------|-----|-------|
| Primary | #1E3A5F | Headers, navigation |
| Accent | #E94E1B | CTAs, buttons |
| Background | #FFFFFF | Page backgrounds |

**Typography:**
- Headings: Montserrat (600, 700)
- Body: Open Sans (400, 600)

**Assets:**
- Logo: assets/logo-primary.svg
- Favicon: assets/favicon.ico

Preview available at .claude/brand/preview.html
```

### Extract from multiple sources

```
User: /brand-extract https://client.com /docs/brand-guide.pdf /templates/deck.pptx

Claude: Extracting brand identity from 3 sources...

[Running brand-extract-web and brand-extract-docs in parallel...]

Merged brand kit from all sources. PPTX theme data used as primary reference.
```

## Troubleshooting

### "No colors found from website"

The website may use external stylesheets or JavaScript. Try:
1. Provide a PPTX or PDF with brand guidelines (more reliable)
2. Use `--deep` flag for browser-based extraction
3. Manually provide hex codes if available

### "Conflicting colors between sources"

The compiler uses this priority:
1. PPTX theme colors (explicit brand definition)
2. PDF/DOCX style colors
3. Website CSS colors (most noisy)

You can manually edit `BRAND_KIT.md` after generation.

## Related Agents

| Agent | Purpose |
|-------|---------|
| `brand-kit-extractor` | Orchestrator (called by this skill) |
| `brand-extract-web` | Website extraction sub-agent |
| `brand-extract-docs` | Document extraction sub-agent |
| `brand-kit-compiler` | Analysis and output sub-agent |
