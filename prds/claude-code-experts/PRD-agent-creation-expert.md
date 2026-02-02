# PRD: agent-creation-expert

## Overview

**Agent Name:** `agent-creation-expert`
**Purpose:** Technical expert for creating custom Claude Code agents
**Model:** Sonnet (code generation + reasoning)

## Problem Statement

Users need guidance on creating effective custom agents that:
- Follow proper YAML frontmatter structure
- Select appropriate tools and models
- Define clear triggers and use cases
- Integrate with CDP (Cognitive Delegation Protocol)
- Support async/sync execution patterns

## Key Capabilities

### 1. Agent Design
- Analyze requirements and design agent specifications
- Recommend model selection (haiku/sonnet/opus) based on task complexity
- Define tool selection patterns
- Create trigger phrases and descriptions

### 2. Agent File Generation
- Generate .md files with proper YAML frontmatter
- Follow established patterns from existing agents
- Include CDP configuration when needed
- Add self-improving flags where appropriate

### 3. Agent Validation
- Audit existing agents for issues
- Check frontmatter syntax
- Verify tool availability
- Test trigger matching

### 4. Best Practices Advisory
- Model selection guidelines:
  - Haiku: file lookups, simple queries, exploration
  - Sonnet: code implementation, reviews, documentation
  - Opus: complex architecture, multi-system integration
- Tool selection patterns
- Async vs sync decision framework
- CDP depth limits and context passing

## Tools Required

- Read (analyze existing agents)
- Write (create new agents)
- Edit (update agents)
- Glob (find agent files)
- Grep (search agent patterns)

## Agent File Structure

```yaml
---
name: agent-name
description: Clear, concise description for Task tool
model: sonnet  # haiku | sonnet | opus
async:
  mode: auto  # auto | always | never
  require_sync:
    - condition1
    - condition2
cdp:
  version: 1.0
  input_requirements:
    - requirement1
  output_includes:
    - output1
tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
---

# Agent Title

## Purpose
Clear statement of what this agent does.

## Capabilities
1. Capability one
2. Capability two

## Instructions
Detailed instructions for the agent...
```

## Trigger Patterns

- "create a new agent"
- "help me build an agent for..."
- "agent creation best practices"
- "fix my agent file"
- "agent YAML structure"

## Integration Points

- Discovers agents in ~/.claude/agents/
- Updates AGENTS_INDEX.md after creation
- Works with CDP protocol for delegation
- Coordinates with `agent-coordination-expert`

## Success Metrics

- Valid YAML frontmatter
- Appropriate model selection
- Clear trigger descriptions
- Functional tool configuration
