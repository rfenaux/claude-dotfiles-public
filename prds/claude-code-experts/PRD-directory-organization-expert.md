# PRD: directory-organization-expert

## Overview

**Agent Name:** `directory-organization-expert`
**Purpose:** Technical expert for Claude Code directory structure and file organization
**Model:** Haiku (fast lookups) or Sonnet (complex reorganization)

## Problem Statement

Users need guidance on organizing Claude Code configuration:
- Standard ~/.claude/ directory hierarchy
- Project-level .claude/ organization
- Separation of concerns (config vs runtime vs cache)
- File naming conventions
- Template management

## Key Capabilities

### 1. Directory Structure Audit
- Analyze current ~/.claude/ organization
- Identify misplaced files
- Detect orphaned configurations
- Recommend structural improvements

### 2. Structure Setup
- Initialize proper ~/.claude/ hierarchy
- Set up project-level .claude/ folders
- Create standard subdirectories
- Organize templates

### 3. File Organization
- Apply naming conventions
- Separate global vs project scope
- Manage cache directories
- Organize conversation history

### 4. Best Practices Advisory
- When to use global vs project settings
- Template organization patterns
- Gitignore recommendations
- Backup strategies

## Tools Required

- Read (analyze structure)
- Write (create files)
- Bash (create directories, move files)
- Glob (find files)
- LS (list directories)

## Standard Directory Structure

```
~/.claude/                          # Global Claude Code config
├── CLAUDE.md                       # Global instructions
├── settings.json                   # User settings
├── settings.local.json             # Local overrides
├── agents/                         # Custom agents (.md files)
├── skills/                         # Custom skills (folders with SKILL.md)
├── hooks/                          # Hook scripts
│   ├── PreToolUse/
│   ├── PostToolUse/
│   └── SessionEnd/
├── scripts/                        # Utility scripts
├── templates/                      # Reusable templates
│   └── context-structure/          # Memory file templates
├── ctm/                            # Cognitive Task Management
│   ├── agents/
│   ├── context/
│   └── checkpoints/
├── projects/                       # Project-specific data
│   └── -path-to-project/           # Encoded project paths
├── commands/                       # Global slash commands
├── docs/                           # Documentation
└── prds/                           # Product requirement docs

project/.claude/                    # Project-level config
├── settings.json                   # Project settings (git tracked)
├── settings.local.json             # Local settings (gitignored)
├── context/                        # Project memory
│   ├── DECISIONS.md
│   ├── SESSIONS.md
│   └── CHANGELOG.md
├── commands/                       # Project slash commands
└── agents/                         # Project-specific agents
```

## Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Agents | kebab-case.md | `hubspot-impl-sales-hub.md` |
| Skills | kebab-case/ | `brand-extract/SKILL.md` |
| Hooks | kebab-case.sh | `ctm-session-end.sh` |
| Scripts | kebab-case.sh | `check-load.sh` |
| Templates | UPPER_SNAKE.md | `DECISIONS.md` |
| PRDs | PRD-name.md | `PRD-feature.md` |

## Trigger Patterns

- "organize my Claude config"
- "set up ~/.claude structure"
- "where should I put this file"
- "directory organization best practices"
- "fix my Claude folder structure"

## Integration Points

- Works with `init-project` skill
- Coordinates with `config-migration-specialist` agent
- References CONFIGURATION_GUIDE.md
- Updates CONFIGURATION_MANIFEST.md

## Success Metrics

- Standard structure followed
- Files in correct locations
- Clear separation of concerns
- Consistent naming
