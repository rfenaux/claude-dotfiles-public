# Search Coordination Guide

How RAG, Glob, Grep, and CTM work together for optimal information retrieval.

---

## The Search Stack (MANDATORY ORDER)

```
┌─────────────────────────────────────────────────────────────┐
│              COMPREHENSIVE SEARCH HIERARCHY                  │
├─────────────────────────────────────────────────────────────┤
│ 1. CTM (Task Context)                                       │
│    → "What am I working on?"                                │
│                                                             │
│ 2. RAG SEARCH - ALWAYS FIRST FOR CONCEPTS                   │
│    ├─ Lessons RAG (~/.claude/lessons)                       │
│    │  → Domain knowledge, past learnings, gotchas           │
│    ├─ Config RAG (~/.claude)                                │
│    │  → Agents, skills, guides, workflows                   │
│    └─ Project RAG (./project/.rag)                          │
│       → Decisions, requirements, meeting notes              │
│                                                             │
│ 3. Greptile (Code/PR Context)                               │
│    → PR comments, code patterns, team conventions           │
│                                                             │
│ 4. Context7 (Library Docs)                                  │
│    → Up-to-date library/framework documentation             │
│                                                             │
│ 5. Grep (Exact Text Match)                                  │
│    → Specific strings, function names, imports              │
│                                                             │
│ 6. Glob (File Discovery)                                    │
│    → File patterns, directory structure                     │
│                                                             │
│ 7. Read (Full Content)                                      │
│    → Complete file when you know exactly which one          │
│                                                             │
│ 8. WebSearch (External Info)                                │
│    → Current events, external documentation                 │
└─────────────────────────────────────────────────────────────┘
```

### RAG First Rule (ENFORCED)

**Before using Grep or Glob for any question containing "how", "why", "what", "where", or "which":**

1. Check Lessons RAG: `rag_search("query", project_path="~/.claude/lessons")`
2. Check Project RAG: `rag_search("query", project_path="./current-project")`
3. THEN use pattern matching for specific locations

A PreToolUse hook reminds about RAG when Grep/Glob is invoked.

---

## Decision Flow

```
┌─────────────────────────────────────────────────────────────┐
│ WHAT DO I NEED?                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  "What was decided about X?"  ───────→  RAG Search          │
│  "Where is the auth code?"    ───────→  Grep + Glob         │
│  "What's in config.ts?"       ───────→  Read directly       │
│  "Find all test files"        ───────→  Glob **/*.test.*    │
│  "How does feature Y work?"   ───────→  Task + Explore      │
│  "What's my current task?"    ───────→  CTM brief           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Workflow: Search-First Pattern

Before proposing solutions or making changes:

### Step 1: Check Task Context (CTM)
```bash
ctm brief
```
- What task am I working on?
- What decisions have been made?
- What's the current state?

### Step 2: Query Project Knowledge (RAG)
```bash
rag_search "relevant query" --project_path /path/to/project
```
- Requirements, constraints, past decisions
- Meeting notes, stakeholder preferences
- Technical context, integration details

### Step 3: Locate Specific Code (Grep/Glob)
```bash
# Find files first
Glob src/**/*auth*.ts

# Then search content
Grep "validateToken" --type ts
```

### Step 4: Read Full Context (Read)
```bash
Read /path/to/specific/file.ts
```

---

## RAG + CTM Integration

### Automatic Context Loading

When CTM has an active task, relevant lessons and context are auto-surfaced:

```
Session Start
    ↓
CTM identifies active task
    ↓
RAG queries lessons tagged with task keywords
    ↓
Relevant lessons appear in session context
```

### Cross-Reference Pattern

```
CTM Task: "HubSpot integration for Rescue"
    ↓
RAG searches:
  - "rescue hubspot integration" (project docs)
  - "hubspot api patterns" (lessons)
  - "quickbooks integration" (related context)
    ↓
Synthesized context for informed decisions
```

---

## When to Use Each Tool

### RAG Search (Semantic)

**Best for:**
- Questions about decisions, requirements, context
- "Why did we choose X?"
- "What are the constraints for Y?"
- Meeting notes, stakeholder preferences
- Historical context

**Query tips:**
- Use natural language
- Include domain terms
- Filter by category when specific

```bash
# Good RAG queries
rag_search "authentication decision OAuth vs JWT"
rag_search "client requirement reporting format"
rag_search "integration constraint real-time sync"
```

### Grep (Exact Match)

**Best for:**
- Finding specific strings, identifiers
- Code definitions (functions, classes)
- Import statements
- Error messages, log patterns

**Pattern tips:**
- Use regex for flexibility
- Filter by file type for speed
- Use context flags (-A/-B/-C) for surrounding lines

```bash
# Good Grep patterns
Grep "class AuthService" --type ts
Grep "def process_payment" --type py
Grep "TODO:|FIXME:" --glob "src/**"
```

### Glob (File Discovery)

**Best for:**
- Finding files by name pattern
- Discovering project structure
- Locating config files
- Listing test files

**Pattern tips:**
- Use ** for recursive
- Use {a,b} for alternatives
- Results sorted by mtime

```bash
# Good Glob patterns
Glob **/*.config.{js,ts,json}
Glob src/components/**/*.tsx
Glob **/test/**/*.spec.ts
```

### CTM (Task Context)

**Best for:**
- Session continuity
- Task switching
- Decision tracking
- Checkpoint/restore

**Commands:**
```bash
ctm brief          # Current task summary
ctm status         # All tasks overview
ctm switch <id>    # Change active task
ctm checkpoint     # Save state
```

---

## Coordination Patterns

### Pattern 1: Research Before Implementation

```
1. ctm brief                    # What's my task?
2. rag_search "task keywords"   # What do we know?
3. Glob src/**/*.ts             # What files exist?
4. Grep "related_pattern"       # Where's relevant code?
5. Read specific_file.ts        # Full context
6. Implement with full context
```

### Pattern 2: Debug Investigation

```
1. Grep "error message"         # Find occurrence
2. Read file_with_error.ts      # See context
3. rag_search "similar issues"  # Past solutions
4. Glob **/*test*.ts            # Find tests
5. Fix with informed approach
```

### Pattern 3: Cross-Project Learning

```
1. rag_search "pattern name" --project ~/.claude
2. rag_search "same pattern" --project ./current
3. Compare approaches
4. Apply lessons learned
```

### Pattern 4: Decision Archaeology

```
1. rag_search "feature decision"           # Find decision
2. Grep "DECISIONS.md" in project          # Check docs
3. rag_search "meeting <feature>"          # Meeting context
4. Reconstruct decision rationale
```

---

## Performance Optimization

### Fast Path (< 1s)
```
Glob → Read
```
Use when you know the file pattern.

### Medium Path (1-5s)
```
Grep → Read
```
Use when you know the content pattern.

### Semantic Path (2-10s)
```
RAG → Grep → Read
```
Use for conceptual questions.

### Deep Path (10-30s)
```
Task+Explore agent
```
Use for open-ended research.

---

## Anti-Patterns to Avoid

| Don't | Do Instead |
|-------|------------|
| RAG for exact text match | Grep for exact text |
| Grep for conceptual questions | RAG for concepts |
| Read entire codebase | Progressive narrowing |
| Skip CTM context | Check task first |
| Multiple sequential searches | Parallel when independent |
| Glob for content search | Grep for content |

---

## Quick Reference

```
┌─────────────────────────────────────────────────────────────┐
│ SEARCH QUICK DECISION                                       │
├─────────────────────────────────────────────────────────────┤
│ Know the file?        → Read it                             │
│ Know the filename?    → Glob then Read                      │
│ Know exact text?      → Grep then Read                      │
│ Asking "why/how"?     → RAG then investigate                │
│ Need full picture?    → Task + Explore agent                │
│ Switching context?    → CTM switch                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Integration with CLAUDE.md

The search workflow is documented in CLAUDE.md under "RAG Auto-Use Rule":

> **If `.rag/` exists in project → use `rag_search` FIRST for any question about the project.**

This ensures semantic search is the default for project questions, with Grep/Glob as targeted follow-up.

---

*See also: SEARCH_PATTERNS_INDEX.md, RAG_GUIDE.md, CTM_GUIDE.md*
*Last Updated: 2026-01-22*
