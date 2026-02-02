#!/usr/bin/env python3
"""Add CDP frontmatter to all agents that don't have it."""

import os
import re
from pathlib import Path

AGENTS_DIR = Path.home() / ".claude" / "agents"

CDP_BLOCK = """cdp:
  version: 1.0
  input_requirements:
    - task description
    - context
    - key files
  output_includes:
    - summary
    - deliverables
    - decisions"""

def has_cdp(content: str) -> bool:
    """Check if file already has cdp: block."""
    return bool(re.search(r'^cdp:', content, re.MULTILINE))

def add_cdp_to_frontmatter(content: str) -> str:
    """Add CDP block to YAML frontmatter."""
    # Find the closing --- of frontmatter
    match = re.search(r'^(---\n.*?)(\n---)', content, re.DOTALL)
    if not match:
        return content

    frontmatter = match.group(1)
    rest = content[match.end():]

    # Add CDP block before closing ---
    new_frontmatter = frontmatter + "\n" + CDP_BLOCK + "\n---"

    return new_frontmatter + rest

def process_agents():
    """Process all agent files."""
    updated = []
    skipped = []

    for agent_file in sorted(AGENTS_DIR.glob("*.md")):
        content = agent_file.read_text()

        if has_cdp(content):
            skipped.append(agent_file.name)
            continue

        new_content = add_cdp_to_frontmatter(content)

        if new_content != content:
            agent_file.write_text(new_content)
            updated.append(agent_file.name)
        else:
            skipped.append(agent_file.name)

    return updated, skipped

if __name__ == "__main__":
    updated, skipped = process_agents()

    print(f"✅ Updated {len(updated)} agents with CDP frontmatter:")
    for name in updated:
        print(f"   - {name}")

    print(f"\n⏭️  Skipped {len(skipped)} agents (already have CDP or no frontmatter):")
    for name in skipped:
        print(f"   - {name}")
