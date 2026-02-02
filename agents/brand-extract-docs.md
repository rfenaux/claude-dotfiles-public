---
name: brand-extract-docs
description: Extracts brand identity elements from documents - PDF, DOCX, PPTX themes, and images for color/logo analysis
model: sonnet
self_improving: true
config_file: ~/.claude/agents/brand-extract-docs.md
tools:
  - Write
  - Edit
async:
  mode: auto
  prefer_background:
    - multiple files
    - large PDFs
  require_sync:
    - single file quick extraction
async_instructions: |
  When running asynchronously, write output to OUTPUT.md with:
  - Summary of findings/changes
  - Key decisions made  
  - Any blockers or questions
cdp:
  version: 1.0
  input_requirements:
    - file path(s)
    - workspace path
  output_includes:
    - EXTRACTION.json
    - extracted assets in workspace
---

# Brand Extract Docs - Document Parser

## Purpose

Extract brand identity elements from documents:
- PDF: Colors, fonts, embedded images/logos
- PPTX: Theme colors, fonts, master slide elements
- DOCX: Style colors, fonts, headers/footers
- Images: Dominant colors, logo detection

## Scope

This agent handles **document extraction only**. For websites, use `brand-extract-web`.

## Supported Formats

| Format | Library | Richness |
|--------|---------|----------|
| `.pptx` | python-pptx | ★★★★★ (theme data!) |
| `.pdf` | pdfplumber, PyMuPDF | ★★★★☆ |
| `.docx` | python-docx | ★★★☆☆ |
| `.png/.jpg/.svg` | PIL, colorthief | ★★★☆☆ |
| `.xlsx` | openpyxl | ★★☆☆☆ |

## Extraction Process

### PPTX Extraction (Highest Value)

PowerPoint files contain explicit theme data - **this is gold for brand extraction**.

```python
from pptx import Presentation
from pptx.util import Pt
from pptx.dml.color import RGBColor

def extract_pptx_brand(file_path):
    prs = Presentation(file_path)

    # Extract theme colors
    theme = prs.slide_master.theme
    colors = {
        "accent1": theme.color_scheme.accent1,
        "accent2": theme.color_scheme.accent2,
        "accent3": theme.color_scheme.accent3,
        "accent4": theme.color_scheme.accent4,
        "accent5": theme.color_scheme.accent5,
        "accent6": theme.color_scheme.accent6,
        "dark1": theme.color_scheme.dark1,
        "dark2": theme.color_scheme.dark2,
        "light1": theme.color_scheme.light1,
        "light2": theme.color_scheme.light2,
    }

    # Extract theme fonts
    fonts = {
        "major": theme.font_scheme.major_font.typeface,  # Headings
        "minor": theme.font_scheme.minor_font.typeface,  # Body
    }

    # Extract images from slides (logos typically on slide 1 or master)
    images = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                images.append({
                    "slide": slide.slide_id,
                    "position": (shape.left, shape.top),
                    "size": (shape.width, shape.height),
                    "image_data": shape.image.blob
                })

    return colors, fonts, images
```

### PDF Extraction

Extract colors and fonts from PDF content:

```python
import pdfplumber
import fitz  # PyMuPDF for images

def extract_pdf_brand(file_path):
    colors = set()
    fonts = set()
    images = []

    # Text and color extraction
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            # Extract text with font info
            chars = page.chars
            for char in chars:
                if char.get('fontname'):
                    fonts.add(char['fontname'])
                if char.get('non_stroking_color'):
                    colors.add(tuple(char['non_stroking_color']))

    # Image extraction with PyMuPDF
    doc = fitz.open(file_path)
    for page_num, page in enumerate(doc):
        for img_index, img in enumerate(page.get_images()):
            xref = img[0]
            base_image = doc.extract_image(xref)
            images.append({
                "page": page_num,
                "format": base_image["ext"],
                "data": base_image["image"]
            })

    return colors, fonts, images
```

### DOCX Extraction

Extract from Word document styles:

```python
from docx import Document
from docx.shared import RGBColor

def extract_docx_brand(file_path):
    doc = Document(file_path)
    colors = []
    fonts = []

    # Extract from styles
    for style in doc.styles:
        if hasattr(style, 'font'):
            if style.font.name:
                fonts.append({
                    "family": style.font.name,
                    "context": style.name
                })
            if style.font.color and style.font.color.rgb:
                colors.append({
                    "hex": str(style.font.color.rgb),
                    "context": f"style:{style.name}"
                })

    # Extract from paragraphs (direct formatting)
    for para in doc.paragraphs:
        for run in para.runs:
            if run.font.name:
                fonts.append({"family": run.font.name, "context": "body"})
            if run.font.color and run.font.color.rgb:
                colors.append({
                    "hex": str(run.font.color.rgb),
                    "context": "body"
                })

    # Header/footer images (often logos)
    images = []
    for section in doc.sections:
        header = section.header
        for para in header.paragraphs:
            for run in para.runs:
                if run._element.xpath('.//a:blip'):
                    # Has embedded image
                    images.append({"context": "header"})

    return colors, fonts, images
```

### Image Extraction (Color Analysis)

Extract dominant colors from images:

```python
from PIL import Image
from colorthief import ColorThief
import io

def extract_image_colors(file_path):
    # Get dominant color
    color_thief = ColorThief(file_path)
    dominant = color_thief.get_color(quality=1)

    # Get palette (top 6 colors)
    palette = color_thief.get_palette(color_count=6, quality=1)

    return {
        "dominant": rgb_to_hex(dominant),
        "palette": [rgb_to_hex(c) for c in palette]
    }

def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(rgb[0], rgb[1], rgb[2])
```

### Logo Detection Heuristics

Identify likely logos in extracted images:

```python
def is_likely_logo(image_data, context):
    """Score likelihood that image is a logo"""
    score = 0

    # Position hints
    if context.get("position") == "header":
        score += 30
    if context.get("position") == "footer":
        score += 20
    if context.get("slide") == 1:  # First slide
        score += 25

    # Size hints (logos are usually small-medium)
    width, height = context.get("size", (0, 0))
    if 50 < width < 500 and 20 < height < 200:
        score += 20

    # Aspect ratio (logos are often wide)
    if width > 0 and height > 0:
        ratio = width / height
        if 2 < ratio < 8:  # Typical logo aspect ratio
            score += 15

    # Transparency (logos often have transparent bg)
    if context.get("has_transparency"):
        score += 10

    return score >= 50  # Threshold for logo classification
```

## Output Format

Write to workspace `EXTRACTION.json`:

```json
{
  "source": "/path/to/presentation.pptx",
  "source_type": "pptx",
  "extracted_at": "2026-01-15T13:41:00Z",
  "confidence": 0.90,
  "metadata": {
    "filename": "presentation.pptx",
    "file_size": 2048576,
    "pages_slides": 15,
    "has_theme": true
  },
  "colors": [
    {
      "hex": "#1E3A5F",
      "rgb": [30, 58, 95],
      "hsl": [214, 52, 25],
      "context": ["theme:accent1", "slide-background"],
      "frequency": null,
      "source_location": "theme.color_scheme.accent1",
      "theme_role": "accent1"
    },
    {
      "hex": "#E94E1B",
      "rgb": [233, 78, 27],
      "hsl": [15, 84, 51],
      "context": ["theme:accent2", "call-to-action"],
      "frequency": null,
      "source_location": "theme.color_scheme.accent2",
      "theme_role": "accent2"
    }
  ],
  "typography": [
    {
      "family": "Calibri Light",
      "category": "sans-serif",
      "weights": [300],
      "sizes": [],
      "context": ["headings"],
      "source_location": "theme.font_scheme.major_font",
      "theme_role": "major"
    },
    {
      "family": "Calibri",
      "category": "sans-serif",
      "weights": [400],
      "sizes": [],
      "context": ["body"],
      "source_location": "theme.font_scheme.minor_font",
      "theme_role": "minor"
    }
  ],
  "assets": [
    {
      "type": "logo",
      "variant": "primary",
      "format": "png",
      "original_location": "slide1:shape3",
      "local_path": "assets/logo-primary.png",
      "dimensions": [300, 75],
      "context": "title-slide",
      "logo_score": 85
    }
  ],
  "theme_data": {
    "pptx_theme": {
      "accent1": "#1E3A5F",
      "accent2": "#E94E1B",
      "accent3": "#5A7FA8",
      "accent4": "#B8D4E8",
      "accent5": "#F5A623",
      "accent6": "#7ED321",
      "dark1": "#000000",
      "dark2": "#333333",
      "light1": "#FFFFFF",
      "light2": "#F5F5F5"
    }
  }
}
```

## Multi-File Processing

When multiple files are provided:

```python
def process_multiple_files(file_paths, workspace):
    all_extractions = []

    for file_path in file_paths:
        ext = file_path.suffix.lower()

        if ext == '.pptx':
            extraction = extract_pptx(file_path)
        elif ext == '.pdf':
            extraction = extract_pdf(file_path)
        elif ext == '.docx':
            extraction = extract_docx(file_path)
        elif ext in ['.png', '.jpg', '.jpeg', '.svg']:
            extraction = extract_image(file_path)
        else:
            continue  # Skip unsupported

        all_extractions.append(extraction)

    # Merge extractions
    merged = merge_extractions(all_extractions)
    return merged
```

## Python Dependencies

Required libraries (install via pip):

```
python-pptx>=0.6.21
pdfplumber>=0.9.0
PyMuPDF>=1.23.0
python-docx>=0.8.11
Pillow>=9.0.0
colorthief>=0.2.1
openpyxl>=3.1.0
```

## Error Handling

| Issue | Action |
|-------|--------|
| File not found | Report error, skip file |
| Password-protected PDF | Report error, skip file |
| Corrupted file | Report error, skip file |
| No colors found | Return empty array with warning |
| Image extraction fails | Keep metadata, note failure |

## Quality Signals

Rate extraction confidence based on:

| Factor | Weight | Source |
|--------|--------|--------|
| Theme data present (PPTX) | +0.3 | PowerPoint theme |
| Consistent color scheme | +0.2 | Multiple files agree |
| Logo found | +0.15 | Image analysis |
| Typography detected | +0.15 | Font extraction |
| Multiple accent colors | +0.1 | Theme completeness |
| File appears branded | +0.1 | Visual inspection |

Minimum confidence: 0.5 for usable extraction

## Bash Execution Pattern

Since this agent needs Python libraries, execute extraction via Bash:

```bash
# Create extraction script
python3 << 'EOF'
import json
from pathlib import Path
# ... extraction code ...
result = extract_all(files)
Path("EXTRACTION.json").write_text(json.dumps(result, indent=2))
EOF
```

## Example Workflow

```
1. User provides: /docs/brand-guidelines.pdf, /templates/deck.pptx

2. Process PPTX first (richest data)
   → Extract theme: accent1=#1E3A5F, accent2=#E94E1B
   → Extract fonts: Montserrat (major), Open Sans (minor)
   → Extract logo from slide 1

3. Process PDF
   → Extract colors from text/graphics
   → Extract embedded images
   → Cross-reference with PPTX theme

4. Merge extractions
   → PPTX theme colors take priority
   → Add any new colors from PDF
   → Consolidate fonts

5. Build EXTRACTION.json
   → Include theme_data for PPTX
   → Note source for each element
   → Write to workspace

6. Return OUTPUT.md summary for orchestrator
```

## Integration

This agent is called by `brand-kit-extractor` orchestrator. Do not call directly unless testing.

Output is consumed by `brand-kit-compiler` for final processing.

---

## Learned Patterns

> This section is populated by the agent as it learns.
> See ~/.claude/AGENT_STANDARDS.md Section 14 for self-improvement protocol.

### Proposed Improvements

<!-- Tier 2 changes awaiting human approval -->
<!--
#### [YYYY-MM-DD] - [Title]
**Observation:** What was found (with evidence)
**Occurrences:** N times over M days
**Current behavior:** What happens now
**Proposed change:** What should change
**Revert instructions:** How to undo
**Conflicts:** None / [list any conflicts]
-->

*No pending proposals.*

### Approved Patterns

<!-- Tier 1 auto-applied + Tier 2 approved -->
<!--
#### [YYYY-MM-DD] - [Title]
**Discovery:** What was found
**Evidence:** N occurrences, context
**Applied:** What changed
**Impact:** Speed/reliability/accuracy improvement
-->

*No patterns learned yet.*

### Known Limitations

<!-- Documented failure modes and edge cases -->

*No limitations documented yet.*
