#!/usr/bin/env python3
"""
Standardize agent frontmatter — adds missing required fields.

Usage:
  python3 scripts/standardize-agent-frontmatter.py --check    # Report only
  python3 scripts/standardize-agent-frontmatter.py --fix      # Apply fixes
"""

import argparse
import re
import sys
from pathlib import Path

AGENTS_DIR = Path(__file__).parent.parent / "agents"
EXCLUDE_DIRS = {"examples", "references"}

# Tool assignments by agent name pattern
TOOL_CATEGORIES = {
    # HubSpot API agents — read + web lookup
    "hubspot-api": ["Read", "Grep", "Glob", "WebFetch"],
    # HubSpot implementation agents — full authoring
    "hubspot-impl": ["Read", "Write", "Edit"],
    # Salesforce mapping agents
    "salesforce-mapping": ["Read", "Grep", "Glob", "WebFetch"],
    # Generators/creators/builders — full authoring + shell
    "generator": ["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
    "creator": ["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
    "builder": ["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
    "writer": ["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
    "compiler": ["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
    "packager": ["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
    "designer": ["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
    "converter": ["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
    "optimizer": ["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
    # Analyzers/auditors/reviewers — read-only
    "analyzer": ["Read", "Glob", "Grep"],
    "auditor": ["Read", "Glob", "Grep"],
    "reviewer": ["Read", "Glob", "Grep"],
    "checker": ["Read", "Glob", "Grep"],
    "validator": ["Read", "Glob", "Grep"],
    "assessor": ["Read", "Glob", "Grep"],
    "comparator": ["Read", "Glob", "Grep"],
    "finder": ["Read", "Glob", "Grep"],
    "advisor": ["Read", "Glob", "Grep"],
    "recommender": ["Read", "Glob", "Grep"],
    # Specialists — read + web
    "specialist": ["Read", "Grep", "Glob", "WebFetch"],
    # Sync/indexer agents — read + write + bash
    "sync": ["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
    "indexer": ["Read", "Write", "Edit", "Bash"],
    # Delegates — full access
    "delegate": ["Read", "Write", "Edit", "Bash"],
    # Reasoning agents
    "reasoning": ["Read", "Write", "Edit", "Bash"],
    # Workers
    "worker": ["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
}

# Specific overrides for agents that don't match patterns
SPECIFIC_TOOLS = {
    "pdf-processor-unlimited": ["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
    "demo-data-generator": ["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
    "document-merger": ["Read", "Write", "Edit", "Glob", "Grep"],
    "context-enricher": ["Read", "Write", "Edit", "Glob", "Grep"],
    "custom-event-specifier": ["Read", "Write", "Edit", "Glob", "Grep"],
    "error-corrector": ["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
    "playbook-advisor": ["Read", "Glob", "Grep"],
    "mvp-scoper": ["Read", "Glob", "Grep"],
    "options-analyzer": ["Read", "Glob", "Grep"],
    "sales-enabler": ["Read", "Write", "Edit", "Glob", "Grep"],
    "status-reporter": ["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
    "slide-deck-creator": ["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
    "solution-spec-writer": ["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
    "bpmn-specialist": ["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
    "erd-generator": ["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
    "lucidchart-generator": ["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
    "slack-ctm-sync": ["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
    "comparable-project-finder": ["Read", "Glob", "Grep"],
    "risk-analyst-meetings": ["Read", "Write", "Edit", "Glob", "Grep"],
    "roi-calculator": ["Read", "Write", "Edit", "Glob", "Grep"],
    "technology-auditor": ["Read", "Glob", "Grep"],
    "testing-designer": ["Read", "Write", "Edit", "Glob", "Grep"],
    "team-coordinator": ["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
    "refactoring-orchestrator": ["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
    "consistency-checker": ["Read", "Glob", "Grep"],
}


def get_tools_for_agent(name: str) -> list[str]:
    """Determine appropriate tools list for an agent by name."""
    if name in SPECIFIC_TOOLS:
        return SPECIFIC_TOOLS[name]
    for pattern, tools in TOOL_CATEGORIES.items():
        if pattern in name:
            return tools
    # Default: read-only
    return ["Read", "Glob", "Grep"]


def parse_frontmatter(content: str) -> tuple[dict, str, str]:
    """Parse YAML frontmatter from content. Returns (fields, frontmatter_str, body)."""
    match = re.match(r'^---\n(.*?)\n---\n(.*)$', content, re.DOTALL)
    if not match:
        return {}, "", content

    fm_str = match.group(1)
    body = match.group(2)

    fields = {}
    for line in fm_str.split('\n'):
        if ':' in line and not line.startswith(' ') and not line.startswith('-'):
            key = line.split(':')[0].strip()
            val = ':'.join(line.split(':')[1:]).strip()
            fields[key] = val

    # Check for async block
    if 'async' in fm_str:
        fields['async'] = True
    # Check for tools block
    if 'tools' in fm_str and re.search(r'tools:\s*\n\s+-', fm_str):
        fields['tools'] = True

    return fields, fm_str, body


def add_missing_fields(content: str, name_from_file: str) -> tuple[str, list[str]]:
    """Add missing required fields to frontmatter. Returns (new_content, changes_made)."""
    fields, fm_str, body = parse_frontmatter(content)
    if not fm_str:
        return content, []

    changes = []
    additions = []

    # Missing name
    if 'name' not in fields:
        additions.append(f"name: {name_from_file}")
        changes.append(f"added name: {name_from_file}")

    # Missing async
    if 'async' not in fields:
        additions.append("async:\n  mode: auto")
        changes.append("added async: mode: auto")

    # Missing tools
    if 'tools' not in fields:
        tools = get_tools_for_agent(name_from_file)
        tools_yaml = "tools:\n" + "\n".join(f"  - {t}" for t in tools)
        additions.append(tools_yaml)
        changes.append(f"added tools: [{', '.join(tools)}]")

    if not additions:
        return content, []

    # Insert additions before closing ---
    new_fm = fm_str.rstrip() + "\n" + "\n".join(additions)
    new_content = f"---\n{new_fm}\n---\n{body}"
    return new_content, changes


def main():
    parser = argparse.ArgumentParser(description="Standardize agent frontmatter")
    parser.add_argument("--check", action="store_true", help="Report only, don't modify")
    parser.add_argument("--fix", action="store_true", help="Apply fixes")
    args = parser.parse_args()

    if not args.check and not args.fix:
        print("Usage: --check (report) or --fix (apply)")
        sys.exit(1)

    agent_files = sorted(
        f for f in AGENTS_DIR.glob("*.md")
        if not any(exc in str(f) for exc in EXCLUDE_DIRS)
    )

    total = len(agent_files)
    issues = {"name": [], "async": [], "tools": [], "no_frontmatter": []}
    fixed = 0

    for fpath in agent_files:
        content = fpath.read_text()
        name_from_file = fpath.stem
        fields, fm_str, _ = parse_frontmatter(content)

        if not fm_str:
            issues["no_frontmatter"].append(fpath.name)
            continue

        if "name" not in fields:
            issues["name"].append(fpath.name)
        if "async" not in fields:
            issues["async"].append(fpath.name)
        if "tools" not in fields:
            issues["tools"].append(fpath.name)

        if args.fix:
            new_content, changes = add_missing_fields(content, name_from_file)
            if changes:
                fpath.write_text(new_content)
                fixed += 1
                print(f"  FIXED {fpath.name}: {'; '.join(changes)}")

    # Summary
    print(f"\n{'='*60}")
    print(f"Agent Frontmatter {'Report' if args.check else 'Fix Summary'}")
    print(f"{'='*60}")
    print(f"Total agents: {total}")
    print(f"Missing name:  {len(issues['name'])} — {', '.join(issues['name']) or 'none'}")
    print(f"Missing async: {len(issues['async'])} — {', '.join(issues['async']) or 'none'}")
    print(f"Missing tools: {len(issues['tools'])} — {len(issues['tools'])} files")
    print(f"No frontmatter: {len(issues['no_frontmatter'])} — {', '.join(issues['no_frontmatter']) or 'none'}")
    if args.fix:
        print(f"\nFixed: {fixed} files")


if __name__ == "__main__":
    main()
