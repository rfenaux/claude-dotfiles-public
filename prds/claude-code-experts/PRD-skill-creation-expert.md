# PRD: skill-creation-expert

## Overview

**Agent Name:** `skill-creation-expert`
**Purpose:** Technical expert for creating custom Claude Code skills
**Model:** Sonnet (code generation + reasoning)

## Problem Statement

Users need guidance on creating effective custom skills that:
- Follow proper folder structure (skill-name/SKILL.md)
- Define clear slash command triggers
- Include reference materials when needed
- Differentiate from agents appropriately

## Key Capabilities

### 1. Skill Design
- Analyze requirements and design skill specifications
- Define /command syntax and parameters
- Plan reference file organization
- Distinguish skill vs agent use cases

### 2. Skill File Generation
- Create skill folders with proper structure
- Generate SKILL.md with proper frontmatter
- Organize reference materials in references/
- Support parameterized commands ($ARGUMENTS)

### 3. Skill Validation
- Audit existing skills for issues
- Verify folder structure
- Check SKILL.md syntax
- Test command invocation

### 4. Skills vs Agents Advisory
**Use Skills when:**
- User-invocable via /command
- Reusable workflow templates
- Interactive prompts needed
- Simple, focused tasks

**Use Agents when:**
- Autonomous task execution
- Complex multi-step workflows
- Background processing needed
- CDP delegation required

## Tools Required

- Read (analyze existing skills)
- Write (create new skills)
- Edit (update skills)
- Glob (find skill files)
- Bash (create folders)

## Skill Folder Structure

```
~/.claude/skills/
└── skill-name/
    ├── SKILL.md           # Main skill definition
    └── references/        # Optional reference materials
        ├── templates.md
        ├── examples.md
        └── api-docs.md
```

## SKILL.md Structure

```markdown
---
name: skill-name
description: Description shown in /commands menu
trigger: /skill-name
parameters:
  - name: arg1
    description: First argument
    required: true
---

# Skill Title

## Purpose
What this skill does.

## Usage
/skill-name <arg1>

## Instructions
Detailed skill prompt...

## References
- See references/templates.md for templates
- See references/examples.md for examples
```

## Trigger Patterns

- "create a new skill"
- "help me build a /command"
- "skill creation best practices"
- "fix my skill file"
- "should this be a skill or agent?"

## Integration Points

- Skills in ~/.claude/skills/ (global) or .claude/skills/ (project)
- Updates SKILLS_INDEX.md after creation
- Invoked via Skill tool
- Can reference external docs

## Success Metrics

- Valid folder structure
- Working /command invocation
- Clear parameter documentation
- Appropriate references/
