---
name: brand-kit-compiler
description: Compiles extracted brand data into actionable brand kit - clusters colors, calculates accessibility, generates BRAND_KIT.md, brand-tokens.json, and preview.html
model: sonnet
self_improving: true
config_file: ~/.claude/agents/brand-kit-compiler.md
tools:
  - Write
  - Edit
async:
  mode: never
  require_sync:
    - always (needs human review of final output)
async_instructions: |
  When running asynchronously, write output to OUTPUT.md with:
  - Summary of findings/changes
  - Key decisions made  
  - Any blockers or questions
cdp:
  version: 1.0
  input_requirements:
    - merged extraction data (from orchestrator)
    - project output path
    - extracted assets location
  output_includes:
    - BRAND_KIT.md
    - brand-tokens.json
    - preview.html
    - organized assets/
---

# Brand Kit Compiler - Analysis & Output Generation

## Purpose

Take raw extraction data from `brand-extract-web` and `brand-extract-docs`, then:
1. **Cluster** similar colors
2. **Classify** colors by role (primary, secondary, accent, neutral)
3. **Calculate** accessibility (WCAG contrast ratios)
4. **Deduplicate** and merge fonts
5. **Generate** all output files

## Input Format

Receives merged extraction data from orchestrator:

```json
{
  "sources": [
    {"url": "https://example.com", "type": "website"},
    {"path": "/docs/brand.pdf", "type": "pdf"}
  ],
  "extractions": [
    { /* EXTRACTION.json from brand-extract-web */ },
    { /* EXTRACTION.json from brand-extract-docs */ }
  ],
  "assets_path": "/workspace/extracted-assets/"
}
```

## Processing Pipeline

### Step 1: Color Clustering

Group similar colors to reduce noise:

```python
from sklearn.cluster import KMeans
import numpy as np

def cluster_colors(colors, n_clusters=8):
    """Cluster similar colors, return representative colors"""

    # Convert hex to RGB
    rgb_values = [hex_to_rgb(c['hex']) for c in colors]

    # Cluster in RGB space
    kmeans = KMeans(n_clusters=min(n_clusters, len(rgb_values)))
    kmeans.fit(rgb_values)

    # Get cluster centers
    centers = kmeans.cluster_centers_

    # Map original colors to clusters
    clustered = []
    for center in centers:
        # Find original color closest to center
        closest = min(colors, key=lambda c: color_distance(hex_to_rgb(c['hex']), center))
        closest['cluster_members'] = sum(1 for c in colors if
            color_distance(hex_to_rgb(c['hex']), center) < 30)
        clustered.append(closest)

    return clustered

def color_distance(c1, c2):
    """Euclidean distance in RGB space"""
    return np.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))
```

### Step 2: Role Classification

Classify colors by their brand role:

```python
def classify_color_roles(colors):
    """Assign roles: primary, secondary, accent, neutral, text, background"""

    roles = {
        "primary": None,
        "secondary": None,
        "accent": None,
        "neutrals": [],
        "text": None,
        "background": None
    }

    for color in colors:
        hex_val = color['hex']
        contexts = color.get('context', [])
        lightness = get_lightness(hex_val)  # 0-100

        # Background detection (very light colors)
        if lightness > 95:
            if roles['background'] is None:
                roles['background'] = color
            continue

        # Text detection (very dark colors)
        if lightness < 25:
            if roles['text'] is None:
                roles['text'] = color
            continue

        # Neutral detection (low saturation)
        saturation = get_saturation(hex_val)
        if saturation < 10:
            roles['neutrals'].append(color)
            continue

        # Primary: header/nav contexts, highest frequency
        if any(ctx in str(contexts) for ctx in ['header', 'nav', 'primary', 'accent1']):
            if roles['primary'] is None:
                roles['primary'] = color
                continue

        # Accent: CTA/button contexts, high saturation
        if any(ctx in str(contexts) for ctx in ['cta', 'button', 'accent', 'action']):
            if roles['accent'] is None:
                roles['accent'] = color
                continue

        # Secondary: everything else with saturation
        if roles['secondary'] is None and saturation > 20:
            roles['secondary'] = color

    return roles
```

### Step 3: Accessibility Analysis

Calculate WCAG contrast ratios:

```python
def calculate_contrast_ratio(color1, color2):
    """Calculate WCAG contrast ratio between two colors"""
    l1 = get_relative_luminance(color1)
    l2 = get_relative_luminance(color2)

    lighter = max(l1, l2)
    darker = min(l1, l2)

    return (lighter + 0.05) / (darker + 0.05)

def get_relative_luminance(hex_color):
    """Calculate relative luminance per WCAG 2.1"""
    r, g, b = hex_to_rgb(hex_color)

    def adjust(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * adjust(r) + 0.7152 * adjust(g) + 0.0722 * adjust(b)

def wcag_compliance(ratio):
    """Return WCAG compliance levels"""
    return {
        "ratio": round(ratio, 2),
        "AA_normal": ratio >= 4.5,
        "AA_large": ratio >= 3.0,
        "AAA_normal": ratio >= 7.0,
        "AAA_large": ratio >= 4.5
    }

def build_accessibility_matrix(colors):
    """Build full accessibility matrix for all color combinations"""
    matrix = []

    foregrounds = [c for c in colors if c.get('role') in ['text', 'primary', 'accent']]
    backgrounds = [c for c in colors if c.get('role') in ['background', 'primary', 'secondary']]

    for fg in foregrounds:
        for bg in backgrounds:
            if fg['hex'] != bg['hex']:
                ratio = calculate_contrast_ratio(fg['hex'], bg['hex'])
                matrix.append({
                    "foreground": fg['hex'],
                    "background": bg['hex'],
                    "fg_role": fg.get('role'),
                    "bg_role": bg.get('role'),
                    **wcag_compliance(ratio)
                })

    return matrix
```

### Step 4: Typography Deduplication

Merge and normalize font data:

```python
def normalize_typography(fonts):
    """Deduplicate and normalize font data"""

    # Group by family name (case-insensitive)
    families = {}
    for font in fonts:
        family = font['family'].strip()
        key = family.lower()

        if key not in families:
            families[key] = {
                "family": family,
                "weights": set(),
                "sizes": set(),
                "contexts": set(),
                "sources": []
            }

        families[key]['weights'].update(font.get('weights', []))
        families[key]['sizes'].update(font.get('sizes', []))
        families[key]['contexts'].update(font.get('context', []))
        families[key]['sources'].append(font.get('source_location'))

    # Convert sets to sorted lists
    result = []
    for data in families.values():
        result.append({
            "family": data['family'],
            "weights": sorted(list(data['weights'])),
            "sizes": sorted(list(data['sizes']), key=lambda x: int(x.replace('px', '')) if x else 0),
            "contexts": list(data['contexts']),
            "category": detect_font_category(data['family'])
        })

    return result

def detect_font_category(family):
    """Detect font category (serif, sans-serif, mono, display)"""
    family_lower = family.lower()

    sans_serif = ['arial', 'helvetica', 'open sans', 'roboto', 'montserrat', 'lato',
                  'source sans', 'nunito', 'poppins', 'inter', 'calibri']
    serif = ['times', 'georgia', 'garamond', 'merriweather', 'playfair', 'lora']
    mono = ['consolas', 'monaco', 'courier', 'fira code', 'jetbrains', 'source code']

    for s in sans_serif:
        if s in family_lower:
            return "sans-serif"
    for s in serif:
        if s in family_lower:
            return "serif"
    for s in mono:
        if s in family_lower:
            return "monospace"

    return "sans-serif"  # Default
```

### Step 5: Asset Organization

Organize extracted assets:

```python
def organize_assets(extracted_assets, output_path):
    """Organize assets into standard structure"""
    import shutil
    from pathlib import Path

    assets_dir = Path(output_path) / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    organized = []

    for asset in extracted_assets:
        asset_type = asset.get('type', 'unknown')
        variant = asset.get('variant', 'primary')
        ext = asset.get('format', 'png')

        # Standard naming
        if asset_type == 'logo':
            new_name = f"logo-{variant}.{ext}"
        elif asset_type == 'favicon':
            new_name = f"favicon.{ext}"
        elif asset_type == 'icon':
            new_name = f"icon-{variant}.{ext}"
        else:
            new_name = f"{asset_type}-{variant}.{ext}"

        # Copy to organized location
        src = asset.get('local_path') or asset.get('original_url')
        dst = assets_dir / new_name

        if src and Path(src).exists():
            shutil.copy(src, dst)
            organized.append({
                **asset,
                "organized_path": str(dst.relative_to(output_path))
            })

    return organized
```

## Output Generation

### BRAND_KIT.md (Main Deliverable)

```python
def generate_brand_kit_md(data, output_path):
    """Generate Claude-consumable BRAND_KIT.md"""

    md = f"""# Brand Kit: {data['company_name']}

> **Extracted:** {data['extracted_at']}
> **Sources:** {', '.join(data['sources'])}
> **Confidence:** {data['confidence']:.0%}

---

## Color Palette

### Primary Colors

| Role | Name | Hex | RGB | HSL | Usage |
|------|------|-----|-----|-----|-------|
"""

    # Add primary colors
    for role in ['primary', 'secondary', 'accent']:
        color = data['colors'].get(role)
        if color:
            md += f"| {role.title()} | {color.get('name', role.title())} | `{color['hex']}` | `rgb({color['rgb'][0]},{color['rgb'][1]},{color['rgb'][2]})` | `hsl({color['hsl'][0]},{color['hsl'][1]}%,{color['hsl'][2]}%)` | {', '.join(color.get('usage', []))} |\n"

    md += """
### Neutral Colors

| Role | Hex | RGB | Usage |
|------|-----|-----|-------|
"""

    # Add neutrals
    for i, neutral in enumerate(data['colors'].get('neutrals', [])):
        md += f"| Neutral {i+1} | `{neutral['hex']}` | `rgb({neutral['rgb'][0]},{neutral['rgb'][1]},{neutral['rgb'][2]})` | {', '.join(neutral.get('usage', ['backgrounds', 'borders']))} |\n"

    md += f"""
### Accessibility Matrix

| Foreground | Background | Contrast | WCAG AA | WCAG AAA |
|------------|------------|----------|---------|----------|
"""

    # Add accessibility data
    for combo in data['accessibility'][:10]:  # Top 10 combinations
        aa = "✓" if combo['AA_normal'] else "✗"
        aaa = "✓" if combo['AAA_normal'] else "✗"
        md += f"| `{combo['foreground']}` | `{combo['background']}` | {combo['ratio']}:1 | {aa} | {aaa} |\n"

    md += """
---

## Typography

| Role | Font Family | Weights | Fallback Stack |
|------|-------------|---------|----------------|
"""

    # Add typography
    for font in data['typography']:
        weights = ', '.join(str(w) for w in font['weights'])
        fallback = f"{font['family']}, {font['category']}"
        contexts = ', '.join(font['contexts']) if font['contexts'] else 'general'
        md += f"| {contexts.title()} | {font['family']} | {weights} | `{fallback}` |\n"

    md += """
---

## Assets

| Asset | Path | Usage | Dimensions |
|-------|------|-------|------------|
"""

    # Add assets
    for asset in data['assets']:
        dims = f"{asset['dimensions'][0]}x{asset['dimensions'][1]}" if asset.get('dimensions') else "—"
        md += f"| {asset['type'].title()} ({asset.get('variant', 'primary')}) | `{asset['organized_path']}` | {asset.get('context', 'general')} | {dims} |\n"

    md += """
---

## Application Guidelines

### Do's
- Use primary color for main CTAs and headers
- Maintain minimum contrast ratios (4.5:1 for body text)
- Use accent color sparingly for emphasis

### Don'ts
- Don't place primary on secondary (low contrast)
- Don't use accent color for large text blocks
- Don't modify logo colors

### Color Combinations (Recommended)

| Use Case | Foreground | Background |
|----------|------------|------------|
| Body text | Text color | Background |
| CTA buttons | White | Primary |
| Links | Primary | Background |
| Alerts | White | Accent |

---

## Quick Reference for Claude

When generating documents, use these values:

```
Primary Color: {data['colors']['primary']['hex']}
Secondary Color: {data['colors'].get('secondary', {}).get('hex', 'N/A')}
Accent Color: {data['colors'].get('accent', {}).get('hex', 'N/A')}
Heading Font: {data['typography'][0]['family'] if data['typography'] else 'sans-serif'}
Body Font: {data['typography'][-1]['family'] if len(data['typography']) > 1 else 'sans-serif'}
Logo Path: {data['assets'][0]['organized_path'] if data['assets'] else 'N/A'}
```
"""

    return md
```

### brand-tokens.json (Programmatic Access)

```json
{
  "version": "1.0",
  "generated": "2026-01-15T13:41:00Z",
  "colors": {
    "primary": {
      "hex": "#1E3A5F",
      "rgb": [30, 58, 95],
      "hsl": [214, 52, 25]
    },
    "secondary": {
      "hex": "#5A7FA8",
      "rgb": [90, 127, 168],
      "hsl": [212, 35, 51]
    },
    "accent": {
      "hex": "#E94E1B",
      "rgb": [233, 78, 27],
      "hsl": [15, 84, 51]
    },
    "background": {
      "hex": "#FFFFFF",
      "rgb": [255, 255, 255],
      "hsl": [0, 0, 100]
    },
    "text": {
      "hex": "#333333",
      "rgb": [51, 51, 51],
      "hsl": [0, 0, 20]
    },
    "neutrals": [
      {"hex": "#F5F5F5", "role": "light-gray"},
      {"hex": "#E0E0E0", "role": "border"},
      {"hex": "#666666", "role": "muted-text"}
    ]
  },
  "typography": {
    "heading": {
      "family": "Montserrat",
      "weights": [600, 700],
      "fallback": "Montserrat, sans-serif"
    },
    "body": {
      "family": "Open Sans",
      "weights": [400, 600],
      "fallback": "Open Sans, sans-serif"
    }
  },
  "assets": {
    "logo_primary": "assets/logo-primary.svg",
    "logo_monochrome": "assets/logo-monochrome.png",
    "favicon": "assets/favicon.ico"
  },
  "accessibility": {
    "primary_on_white": {"ratio": 8.4, "AA": true, "AAA": true},
    "accent_on_white": {"ratio": 4.6, "AA": true, "AAA": false},
    "white_on_primary": {"ratio": 8.4, "AA": true, "AAA": true}
  }
}
```

### preview.html (Visual Preview)

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Brand Kit Preview - {company_name}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: system-ui, sans-serif; padding: 40px; background: #f5f5f5; }
        h1 { margin-bottom: 30px; }
        .section { background: white; border-radius: 12px; padding: 24px; margin-bottom: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .section h2 { margin-bottom: 16px; font-size: 18px; color: #333; }
        .color-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 16px; }
        .color-swatch { border-radius: 8px; overflow: hidden; }
        .color-swatch .swatch { height: 80px; }
        .color-swatch .info { padding: 12px; background: white; border: 1px solid #eee; border-top: none; }
        .color-swatch .hex { font-family: monospace; font-size: 14px; }
        .color-swatch .role { font-size: 12px; color: #666; margin-top: 4px; }
        .font-sample { padding: 16px; border: 1px solid #eee; border-radius: 8px; margin-bottom: 12px; }
        .font-name { font-size: 12px; color: #666; margin-bottom: 8px; }
        .font-preview { font-size: 24px; }
        .asset-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; }
        .asset-card { border: 1px solid #eee; border-radius: 8px; padding: 16px; text-align: center; }
        .asset-card img { max-width: 100%; max-height: 80px; margin-bottom: 12px; }
        .contrast-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 12px; }
        .contrast-sample { padding: 16px; border-radius: 8px; text-align: center; font-weight: 600; }
        .pass { border: 2px solid #22c55e; }
        .fail { border: 2px solid #ef4444; }
    </style>
</head>
<body>
    <h1>Brand Kit: {company_name}</h1>

    <div class="section">
        <h2>Color Palette</h2>
        <div class="color-grid">
            <!-- Generated color swatches -->
        </div>
    </div>

    <div class="section">
        <h2>Typography</h2>
        <!-- Generated font samples -->
    </div>

    <div class="section">
        <h2>Assets</h2>
        <div class="asset-grid">
            <!-- Generated asset cards -->
        </div>
    </div>

    <div class="section">
        <h2>Contrast Check</h2>
        <div class="contrast-grid">
            <!-- Generated contrast samples -->
        </div>
    </div>
</body>
</html>
```

## Error Handling

| Issue | Action |
|-------|--------|
| No colors extracted | Fail with clear error |
| No typography found | Use system defaults, warn |
| No assets found | Continue without assets, note |
| Low confidence (<0.5) | Warn user, suggest manual review |

## Quality Checklist

Before returning, verify:

- [ ] `BRAND_KIT.md` exists and is valid markdown
- [ ] `brand-tokens.json` is valid JSON
- [ ] `preview.html` renders correctly
- [ ] At least primary color defined
- [ ] Accessibility matrix calculated
- [ ] Assets organized in `assets/` folder

## Integration

This agent is called by `brand-kit-extractor` orchestrator after extraction phase.

Runs **synchronously** (async: never) because output requires human review.

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
