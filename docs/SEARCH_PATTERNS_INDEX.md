# Search Patterns Index

Quick reference for efficient file and content discovery in Claude Code.

---

## Tool Selection Matrix

| Need | Tool | Speed | When to Use |
|------|------|-------|-------------|
| Find files by name/pattern | **Glob** | ~0.1s | Know filename pattern |
| Find text in files | **Grep** | 0.2-2s | Know exact text |
| Find concepts/meaning | **RAG** | 2-5s | Semantic search |
| Read specific file | **Read** | varies | Know exact path |
| Explore codebase | **Task+Explore** | 10-30s | Open-ended research |

---

## Glob Patterns

### File Discovery
```bash
# All TypeScript files
Glob **/*.ts

# All test files
Glob **/*.test.{ts,js}
Glob **/*_test.py

# Config files
Glob **/{*.config.*,*.json,*.yaml,*.toml}

# Markdown in specific dir
Glob docs/**/*.md

# Recently modified (by mtime)
Glob **/*.md  # Returns sorted by mtime
```

### Project Structure
```bash
# Source files only
Glob src/**/*.{ts,tsx,js,jsx}

# Exclude node_modules (automatic)
Glob **/*.js  # node_modules excluded by default

# Agent definitions
Glob ~/.claude/agents/*.md

# Skill definitions
Glob ~/.claude/skills/*/SKILL.md
```

---

## Grep Patterns

### Code Definitions
```bash
# Python function
Grep "^def function_name\("

# Python class
Grep "^class ClassName"

# TypeScript/JS function
Grep "function\s+functionName\s*\("
Grep "const\s+functionName\s*="

# React component
Grep "export.*function\s+ComponentName"
Grep "const\s+ComponentName.*=.*=>"

# Go function
Grep "^func\s+FunctionName\("
```

### Imports & Dependencies
```bash
# Python imports
Grep "^from\s+module\s+import"
Grep "^import\s+module"

# JS/TS imports
Grep "^import.*from\s+['\"]package"
Grep "require\(['\"]package"

# Find all imports of a module
Grep "import.*moduleName" --type ts
```

### Configuration
```bash
# Environment variables
Grep "process\.env\." --type ts
Grep "os\.environ" --type py

# API keys/secrets (audit)
Grep -i "api.?key|secret|password|token"

# URLs
Grep "https?://[^\s\"']+"
```

### Error Handling
```bash
# Try/catch blocks
Grep "try\s*\{" --type ts
Grep "except\s+\w+:" --type py

# Error classes
Grep "class.*Error\s*extends"
Grep "raise\s+\w+Error"
```

### Comments & TODOs
```bash
# TODO comments
Grep "TODO:|FIXME:|HACK:|XXX:"

# JSDoc/docstrings
Grep "/\*\*" --type ts
Grep '"""' --type py
```

---

## RAG Search Patterns

### Project Context
```bash
# Architecture decisions
rag_search "architecture decision authentication"

# Requirements
rag_search "requirement user authentication"

# Meeting notes
rag_search "meeting decision API design"
```

### Technical Concepts
```bash
# How something works
rag_search "how does authentication work"

# Integration patterns
rag_search "HubSpot API integration pattern"

# Data flow
rag_search "data flow between services"
```

### Historical Context
```bash
# Past decisions
rag_search "why did we choose PostgreSQL"

# Previous implementations
rag_search "previous payment integration approach"

# Stakeholder requirements
rag_search "client requirement reporting"
```

### Filtered Searches
```bash
# By category
rag_search "authentication" category="decision"
rag_search "API design" category="requirement"

# By relevance
rag_search "security" min_relevance="high"

# By phase
rag_search "deployment" phase="implementation"
```

---

## Combined Strategies

### Progressive Narrowing (Fast → Deep)
```
1. Glob → Scope files
2. Grep → Filter by content
3. RAG → Understand meaning
4. Read → Full context
```

**Example: Find authentication implementation**
```bash
# Step 1: Find candidate files
Glob src/**/*auth*.{ts,js}

# Step 2: Filter by specific pattern
Grep "validateToken|verifyAuth" --type ts

# Step 3: Understand the flow
rag_search "authentication token validation flow"

# Step 4: Read the key file
Read src/auth/tokenValidator.ts
```

### Parallel Search (Breadth)
```bash
# Run multiple searches simultaneously
Glob src/**/*.ts           # Find all TS files
Grep "interface.*Props"    # Find React props
rag_search "component architecture"  # Understand patterns
```

### CTM-Aware Search
```bash
# Check task context first
ctm brief

# Then search with context
rag_search "query" scope="current-project"
```

---

## Performance Tips

| Pattern | Slow | Fast |
|---------|------|------|
| Find file | `Grep "filename"` | `Glob **/filename*` |
| Find in type | `Grep "pattern"` | `Grep "pattern" --type ts` |
| Broad search | Multiple Greps | Single RAG query |
| Deep search | RAG alone | Glob → Grep → RAG |

### When to Use Task+Explore Agent
- Open-ended research ("how does X work?")
- Multiple file analysis needed
- Don't know where to look
- Need comprehensive understanding

### When NOT to Use Task
- Know exact file path → Use Read
- Know exact text → Use Grep
- Know filename pattern → Use Glob
- Quick factoid lookup → Direct RAG

---

## Common Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| `Grep "." **/*` | `Glob **/*` then targeted Grep |
| RAG for exact text | Grep for exact text |
| Glob for content | Grep for content |
| Read entire codebase | Progressive narrowing |
| Multiple sequential searches | Parallel searches |

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────┐
│ SEARCH QUICK REFERENCE                                  │
├─────────────────────────────────────────────────────────┤
│ Find files:     Glob **/*.ext                          │
│ Find text:      Grep "pattern" --type ext              │
│ Find meaning:   rag_search "concept"                   │
│ Read file:      Read /path/to/file                     │
│ Explore:        Task subagent_type=Explore             │
├─────────────────────────────────────────────────────────┤
│ SPEED: Glob (0.1s) < Grep (0.5s) < RAG (3s) < Explore │
└─────────────────────────────────────────────────────────┘
```

---

*Last Updated: 2026-01-22*
*See also: SEARCH_COORDINATION.md, RAG_GUIDE.md*
