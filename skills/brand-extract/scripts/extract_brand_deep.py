#!/usr/bin/env python3
"""
Deep brand extraction using Playwright browser automation.
Renders JavaScript and extracts computed styles.

Usage:
    python extract_brand_deep.py <url> [output_dir]

Example:
    python extract_brand_deep.py https://huble.com ./workspace

Requirements:
    pip install playwright colorthief Pillow
    playwright install chromium
"""

import asyncio
import json
import re
import sys
from pathlib import Path


def rgb_to_hex(rgb_value):
    """Convert RGB tuple or string to hex"""
    if isinstance(rgb_value, (tuple, list)):
        r, g, b = rgb_value[:3]
        return f'#{int(r):02x}{int(g):02x}{int(b):02x}'
    elif isinstance(rgb_value, str):
        match = re.match(r'rgba?\((\d+),\s*(\d+),\s*(\d+)', rgb_value)
        if match:
            r, g, b = map(int, match.groups())
            return f'#{r:02x}{g:02x}{b:02x}'
    return rgb_value


def hex_to_rgb(hex_color):
    """Convert hex to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def get_color_lightness(hex_color):
    """Get perceived lightness (0-100)"""
    r, g, b = hex_to_rgb(hex_color)
    # Using relative luminance formula
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255 * 100


async def extract_brand_deep(url: str, output_dir: Path):
    """Extract brand elements using headless browser"""
    from playwright.async_api import async_playwright

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = output_dir / 'assets'
    assets_dir.mkdir(exist_ok=True)

    async with async_playwright() as p:
        print(f"[Deep Extract] Launching browser for {url}")
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Navigate and wait for full render
        print("[Deep Extract] Loading page...")
        await page.goto(url, wait_until='networkidle', timeout=30000)

        # Wait a bit more for any lazy-loaded content
        await asyncio.sleep(2)

        # Extract all computed colors
        print("[Deep Extract] Extracting colors...")
        colors = await page.evaluate('''
            () => {
                const colors = new Map();
                const elements = document.querySelectorAll('*');

                elements.forEach(el => {
                    const style = window.getComputedStyle(el);
                    const tagName = el.tagName.toLowerCase();
                    const className = el.className || '';

                    // Background colors
                    const bgColor = style.backgroundColor;
                    if (bgColor && bgColor !== 'rgba(0, 0, 0, 0)' && bgColor !== 'transparent') {
                        const key = bgColor;
                        if (!colors.has(key)) {
                            colors.set(key, {
                                value: bgColor,
                                contexts: new Set(),
                                count: 0,
                                type: 'background'
                            });
                        }
                        colors.get(key).count++;
                        colors.get(key).contexts.add(tagName);
                    }

                    // Text colors
                    const textColor = style.color;
                    if (textColor && textColor !== 'rgba(0, 0, 0, 0)') {
                        const key = textColor + '_text';
                        if (!colors.has(key)) {
                            colors.set(key, {
                                value: textColor,
                                contexts: new Set(),
                                count: 0,
                                type: 'text'
                            });
                        }
                        colors.get(key).count++;
                        colors.get(key).contexts.add(tagName);
                    }

                    // Border colors
                    const borderColor = style.borderTopColor;
                    if (borderColor && borderColor !== 'rgba(0, 0, 0, 0)' &&
                        borderColor !== 'rgb(0, 0, 0)' && style.borderWidth !== '0px') {
                        const key = borderColor + '_border';
                        if (!colors.has(key)) {
                            colors.set(key, {
                                value: borderColor,
                                contexts: new Set(),
                                count: 0,
                                type: 'border'
                            });
                        }
                        colors.get(key).count++;
                    }
                });

                return Array.from(colors.values())
                    .map(c => ({
                        ...c,
                        contexts: Array.from(c.contexts)
                    }))
                    .sort((a, b) => b.count - a.count)
                    .slice(0, 30);
            }
        ''')

        # Extract typography
        print("[Deep Extract] Extracting typography...")
        typography = await page.evaluate('''
            () => {
                const fonts = new Map();
                const elements = document.querySelectorAll('h1, h2, h3, h4, h5, h6, p, a, span, button, nav, header, footer');

                elements.forEach(el => {
                    const style = window.getComputedStyle(el);
                    const family = style.fontFamily.split(',')[0].trim().replace(/['"]/g, '');
                    const weight = style.fontWeight;
                    const size = style.fontSize;
                    const tag = el.tagName.toLowerCase();

                    if (family && family !== 'inherit') {
                        if (!fonts.has(family)) {
                            fonts.set(family, {
                                family,
                                weights: new Set(),
                                sizes: new Set(),
                                contexts: new Set()
                            });
                        }
                        fonts.get(family).weights.add(weight);
                        fonts.get(family).sizes.add(size);
                        fonts.get(family).contexts.add(tag);
                    }
                });

                return Array.from(fonts.values()).map(f => ({
                    family: f.family,
                    weights: Array.from(f.weights).map(w => parseInt(w) || w),
                    sizes: Array.from(f.sizes),
                    contexts: Array.from(f.contexts)
                }));
            }
        ''')

        # Extract CSS variables from :root
        print("[Deep Extract] Extracting CSS variables...")
        css_variables = await page.evaluate('''
            () => {
                const root = document.documentElement;
                const style = getComputedStyle(root);
                const vars = {};

                // Get all CSS custom properties
                const allStyles = document.styleSheets;
                for (let sheet of allStyles) {
                    try {
                        for (let rule of sheet.cssRules) {
                            if (rule.selectorText === ':root') {
                                for (let prop of rule.style) {
                                    if (prop.startsWith('--')) {
                                        vars[prop] = rule.style.getPropertyValue(prop).trim();
                                    }
                                }
                            }
                        }
                    } catch (e) {
                        // Cross-origin stylesheets
                    }
                }

                // Also check computed style for common variable names
                const commonVars = [
                    '--color-primary', '--primary-color', '--brand-color', '--main-color',
                    '--color-secondary', '--secondary-color',
                    '--color-accent', '--accent-color', '--highlight-color',
                    '--color-background', '--bg-color', '--background-color',
                    '--color-text', '--text-color', '--body-color',
                    '--font-family', '--font-heading', '--font-body', '--font-primary'
                ];

                commonVars.forEach(name => {
                    const value = style.getPropertyValue(name).trim();
                    if (value && !vars[name]) {
                        vars[name] = value;
                    }
                });

                return vars;
            }
        ''')

        # Screenshot for color analysis fallback
        print("[Deep Extract] Taking screenshot...")
        screenshot_path = output_dir / 'screenshot.png'
        await page.screenshot(path=str(screenshot_path), full_page=False)

        # Find logos
        print("[Deep Extract] Finding logos...")
        logos = await page.evaluate('''
            () => {
                const logos = [];
                const selectors = [
                    'header img',
                    'nav img',
                    '[class*="logo"]',
                    '[id*="logo"]',
                    'img[alt*="logo" i]',
                    'img[src*="logo" i]',
                    '.header img',
                    '#header img',
                    'a[href="/"] img',
                    '.navbar-brand img',
                    '.site-logo img'
                ];

                const seen = new Set();

                selectors.forEach(selector => {
                    document.querySelectorAll(selector).forEach(img => {
                        if (img.src && !seen.has(img.src)) {
                            seen.add(img.src);
                            logos.push({
                                url: img.src,
                                alt: img.alt || '',
                                width: img.naturalWidth || img.width,
                                height: img.naturalHeight || img.height,
                                selector: selector
                            });
                        }
                    });
                });

                // Also check for SVG logos
                document.querySelectorAll('svg[class*="logo"], header svg, nav svg').forEach(svg => {
                    const serializer = new XMLSerializer();
                    logos.push({
                        type: 'inline-svg',
                        selector: 'svg logo',
                        width: svg.getBoundingClientRect().width,
                        height: svg.getBoundingClientRect().height
                    });
                });

                return logos;
            }
        ''')

        # Get favicon
        print("[Deep Extract] Finding favicon...")
        favicon = await page.evaluate('''
            () => {
                const links = document.querySelectorAll('link[rel*="icon"]');
                const favicons = [];
                links.forEach(link => {
                    favicons.push({
                        href: link.href,
                        rel: link.rel,
                        sizes: link.sizes ? link.sizes.value : null,
                        type: link.type
                    });
                });
                return favicons.length > 0 ? favicons : [{ href: window.location.origin + '/favicon.ico' }];
            }
        ''')

        # Get page metadata
        metadata = await page.evaluate('''
            () => {
                return {
                    title: document.title,
                    description: document.querySelector('meta[name="description"]')?.content,
                    themeColor: document.querySelector('meta[name="theme-color"]')?.content,
                    ogImage: document.querySelector('meta[property="og:image"]')?.content
                };
            }
        ''')

        await browser.close()

        # Process and normalize colors
        processed_colors = []
        for color in colors:
            hex_val = rgb_to_hex(color['value'])
            if hex_val.startswith('#'):
                processed_colors.append({
                    'hex': hex_val.upper(),
                    'rgb': list(hex_to_rgb(hex_val)),
                    'original': color['value'],
                    'type': color['type'],
                    'contexts': color['contexts'],
                    'frequency': color['count']
                })

        # Deduplicate by hex
        seen_hex = set()
        unique_colors = []
        for c in processed_colors:
            if c['hex'] not in seen_hex:
                seen_hex.add(c['hex'])
                unique_colors.append(c)

        result = {
            'source': url,
            'source_type': 'website',
            'extraction_mode': 'deep',
            'browser': 'chromium',
            'metadata': metadata,
            'colors': unique_colors,
            'typography': typography,
            'css_variables': css_variables,
            'logos': logos,
            'favicon': favicon,
            'screenshot': str(screenshot_path)
        }

        # Write EXTRACTION.json
        extraction_path = output_dir / 'EXTRACTION.json'
        with open(extraction_path, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"[Deep Extract] Results saved to {extraction_path}")

        return result


def analyze_screenshot_colors(screenshot_path):
    """Extract dominant colors from screenshot using colorthief"""
    try:
        from colorthief import ColorThief
        ct = ColorThief(str(screenshot_path))

        dominant = ct.get_color(quality=1)
        palette = ct.get_palette(color_count=8, quality=1)

        return {
            'dominant': rgb_to_hex(dominant),
            'palette': [rgb_to_hex(c) for c in palette]
        }
    except Exception as e:
        print(f"[Warning] Could not analyze screenshot: {e}")
        return None


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python extract_brand_deep.py <url> [output_dir]")
        print("Example: python extract_brand_deep.py https://huble.com ./workspace")
        sys.exit(1)

    url = sys.argv[1]
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('.')

    print(f"\n{'='*60}")
    print(f"Deep Brand Extraction")
    print(f"URL: {url}")
    print(f"Output: {output_dir}")
    print(f"{'='*60}\n")

    result = asyncio.run(extract_brand_deep(url, output_dir))

    # Try screenshot analysis as supplement
    screenshot_path = output_dir / 'screenshot.png'
    if screenshot_path.exists():
        screenshot_colors = analyze_screenshot_colors(screenshot_path)
        if screenshot_colors:
            result['screenshot_colors'] = screenshot_colors
            # Update EXTRACTION.json with screenshot colors
            extraction_path = output_dir / 'EXTRACTION.json'
            with open(extraction_path, 'w') as f:
                json.dump(result, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Extraction Complete!")
    print(f"Colors found: {len(result['colors'])}")
    print(f"Fonts found: {len(result['typography'])}")
    print(f"CSS variables: {len(result['css_variables'])}")
    print(f"Logos found: {len(result['logos'])}")
    print(f"{'='*60}\n")
