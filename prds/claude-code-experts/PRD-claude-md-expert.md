# PRD: claude-md-expert

## Overview

**Agent Name:** `claude-md-expert`
**Purpose:** Technical expert for CLAUDE.md file creation, optimization, and best practices
**Model:** Sonnet (balanced reasoning + speed)

## Problem Statement

Users need guidance on creating and maintaining effective CLAUDE.md memory files that:
- Provide optimal context without exceeding instruction limits (~150-200 instructions)
- Follow the WHAT/WHY/HOW structure
- Avoid anti-patterns (auto-generation, style guides, task-specific content)
- Support hierarchical placement (global, project, nested)

## Key Capabilities

### 1. CLAUDE.md Analysis
- Audit existing CLAUDE.md files for effectiveness
- Identify anti-patterns (too long, style guides, auto-generated)
- Count instructions and warn about limits
- Check for stale code snippets

### 2. CLAUDE.md Generation
- Create new CLAUDE.md from project analysis
- Follow WHAT (architecture), WHY (rationale), HOW (workflows) structure
- Generate minimal, high-leverage content (<300 lines ideal, <60 lines optimal)
- Support monorepo configurations

### 3. Optimization Recommendations
- Suggest moving content to agent_docs/ for progressive disclosure
- Recommend hooks/commands instead of inline instructions
- Identify content that should use linters instead
- Prioritize instructions by impact

### 4. Hierarchy Management
- Advise on global (~/.claude/CLAUDE.md) vs project placement
- Support nested directory configurations
- Handle parent directory inheritance

## Tools Required

- Read (analyze existing files)
- Write (create new CLAUDE.md)
- Edit (optimize existing files)
- Glob (find CLAUDE.md files in hierarchy)
- Grep (search for patterns/anti-patterns)

## Trigger Patterns

- "help me write a CLAUDE.md"
- "optimize my CLAUDE.md"
- "audit my memory file"
- "CLAUDE.md best practices"
- "create project instructions"

## Example Interactions

```
User: "My CLAUDE.md is 500 lines, help me optimize it"
Agent: Analyzes file, identifies style guides (move to linter),
       task-specific content (move to commands/),
       and creates optimized <100 line version
```

## Integration Points

- Works with `init-project` skill for new projects
- Complements `memory-init` skill
- References `~/.claude/CONFIGURATION_GUIDE.md` for patterns

## Success Metrics

- CLAUDE.md files under 200 instructions
- No auto-generated content
- Clear WHAT/WHY/HOW sections
- Progressive disclosure to agent_docs/

## Sources

- [Anthropic Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)
- [HumanLayer CLAUDE.md Guide](https://www.humanlayer.dev/blog/writing-a-good-claude-md)
- [Claude Code Settings Docs](https://code.claude.com/docs/en/settings)
