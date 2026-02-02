# PRD: file-indexing-expert

## Overview

**Agent Name:** `file-indexing-expert`
**Purpose:** Technical expert for file discovery, search, and indexing in Claude Code
**Model:** Haiku (fast searches) or Sonnet (complex analysis)

## Problem Statement

Users need guidance on efficient file discovery and search:
- Optimal use of Glob and Grep tools
- Large codebase navigation strategies
- Search result optimization
- Integration with RAG for semantic search
- Performance-aware file operations

## Key Capabilities

### 1. Search Strategy Design
- Recommend Glob vs Grep for different use cases
- Design efficient search patterns
- Handle large codebases (>10k files)
- Optimize multi-pattern searches

### 2. File Discovery
- Find files by patterns (*.tsx, **/*.test.js)
- Locate specific classes/functions
- Navigate monorepo structures
- Handle nested dependencies

### 3. Search Optimization
- Use output_mode efficiently (files_with_matches vs content)
- Apply head_limit and offset for pagination
- Combine Glob + Grep for targeted searches
- Leverage file type filters

### 4. RAG Integration
- When to use RAG vs direct search
- Semantic search for conceptual queries
- Hybrid search strategies
- Index management recommendations

## Tools Required

- Glob (pattern matching)
- Grep (content search)
- Read (file content)
- Bash (advanced searches)

## Search Tool Selection

| Scenario | Tool | Example |
|----------|------|---------|
| Find files by name | Glob | `**/*.tsx` |
| Find files containing text | Grep | `pattern` with files_with_matches |
| Find specific content | Grep | `pattern` with content mode |
| Class/function definition | Grep | `class Foo` or `function bar` |
| Needle in haystack | Glob + Read | Glob to narrow, Read to verify |
| Conceptual search | RAG | "how does authentication work" |

## Glob Patterns

```
*.md                  # All markdown in current dir
**/*.md               # All markdown recursively
src/**/*.tsx          # TSX files in src tree
!**/node_modules/**   # Exclude patterns
{*.ts,*.tsx}          # Multiple extensions
```

## Grep Patterns

```
# Basic
pattern                           # Simple match
"function.*export"                # Regex
"class\s+\w+"                     # Word patterns

# With options
-i pattern                        # Case insensitive
--glob "*.ts" pattern             # Filter by file type
--type js pattern                 # File type filter
-A 3 -B 3 pattern                 # Context lines
```

## Trigger Patterns

- "help me search the codebase"
- "find all files matching..."
- "where is [function/class] defined"
- "search optimization"
- "large codebase navigation"

## Large Codebase Strategies

1. **Narrow first**: Glob to find candidate files, then Grep
2. **Type filter**: Use --type for known file types
3. **Path scope**: Search within specific directories
4. **Pagination**: Use head_limit + offset for large results
5. **RAG fallback**: Use semantic search for conceptual queries

## Integration Points

- Coordinates with `rag-integration-expert`
- Works with Explore agent for open-ended searches
- Supports `file-indexing-management` skill
- Informs codebase exploration patterns

## Success Metrics

- Fast search results
- Relevant matches found
- Minimal false positives
- Efficient tool selection
