---
name: process-doc
description: Process input documents into structured summaries with sequential memory management. Extracts numbers, requirements, decisions, and open questions, then indexes to RAG.
async:
  mode: never
  require_sync:
    - document processing
    - structured extraction
---

# /process-doc - Document Processing Skill

Process input documents one at a time with structured extraction and memory-efficient handling. Inspired by sequential processing protocols that prevent context bloat during multi-doc intake.

## Trigger

Invoke when:
- User says "/process-doc [path]" or "process this document"
- User drops multiple files for analysis
- Starting discovery phase with client documents
- Processing meeting transcripts, briefs, requirements docs

## Arguments

```
/process-doc <file_path>              # Process single document
/process-doc <file1> <file2> ...      # Process multiple (sequential)
/process-doc <directory>              # Process all docs in directory
```

## Behavior

### Single Document Flow

1. **Read** the document (use appropriate tool: Read for text, Python for binary)
2. **Extract** structured data into the template below
3. **Write** summary to project context or summaries directory
4. **Index** to RAG if project has `.rag/`
5. **Report** what was extracted, what's unclear, what needs follow-up

### Multiple Document Flow

Process sequentially to manage context:
1. List all documents with sizes
2. Ask user for priority order (if > 3 docs)
3. For each document:
   - Read it
   - Extract into structured summary
   - Write summary to disk
   - Index to RAG
   - Release from active context before reading next
4. After all processed: cross-reference summaries for contradictions/relationships
5. Report overall findings

### Output Location

Write summaries to (in order of preference):
1. `<project>/.claude/context/sources/source-<filename>.md` (if project has `.claude/context/`)
2. `<project>/docs/summaries/source-<filename>.md` (if `docs/summaries/` exists)
3. `<project>/source-<filename>.md` (fallback)

## Extraction Template

```markdown
# Source Summary: [Original Document Name]
**Processed:** [YYYY-MM-DD]
**Source:** [file path]
**Type:** [brief / requirements / research / proposal / transcript / report]
**Confidence:** [high / medium / low] - [reason]

## Key Numbers & Metrics
<!-- Every number, amount, percentage, date, count. Exact values, no rounding. -->
- [metric]: [exact value] (section/page ref)

## Requirements & Constraints
<!-- IF/THEN/BUT/EXCEPT format for conditional logic -->
- REQ: [requirement]
  - CONDITION: [when this applies]
  - CONSTRAINT: [limitation]
  - PRIORITY: [must-have / should-have / nice-to-have]

## Decisions Referenced
- DEC: [what was decided] | WHY: [rationale] | BY: [who]
- ALTERNATIVES: [what was rejected and why]

## Open Items
- [OPEN]: [unresolved question] - needs input from [whom]
- [ASSUMED]: [interpretation made] - verify with [whom]
- [MISSING]: [info referenced but not provided]

## Cross-References
- SUPPORTS: [other known document/decision]
- CONTRADICTS: [conflict with other source]
- DEPENDS ON: [upstream dependency]

## Key Quotes
<!-- 2-5 verbatim quotes that capture stakeholder language or priorities -->
- "[exact quote]" - [speaker], [context]
```

## Integration

- **RAG**: Auto-indexes summaries to project RAG if `.rag/` exists
- **Decision tracker**: Flags extracted decisions for DECISIONS.md recording
- **OPEN/ASSUMED marking**: Uses structured ambiguity markers (see decision-auto-capture rule)
- **Binary files**: Uses Python for XLSX/DOCX/PPTX per binary file reference

## Example

```
User: /process-doc ~/Downloads/client-brief.pdf

Claude: Processing client-brief.pdf...

Source Summary: Client Brief - Acme Corp
Written to: .claude/context/sources/source-client-brief.md
Indexed to RAG.

**Extracted:**
- 12 metrics (revenue figures, headcount, timeline dates)
- 4 requirements (2 must-have, 2 should-have)
- 2 decisions (CRM platform choice, integration approach)
- 3 key quotes

**Needs attention:**
- [OPEN]: Budget range mentioned but no exact figure - ask client
- [ASSUMED]: "Q3" interpreted as Q3 2026 - verify timeline
- [MISSING]: Technical stack details referenced but not included

Process another document?
```
