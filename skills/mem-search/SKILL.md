# /mem-search - Observation Memory Search

Search session observation summaries with progressive disclosure.

## Usage

```
/mem-search                    # Last 5 session summaries (compact table)
/mem-search recent             # Same as above
/mem-search "query"            # Semantic search across summaries
/mem-search detail             # Last 5 with full content
/mem-search detail "query"     # Search with full content
/mem-search stats              # Observation system statistics
```

## Behavior

### Default / Recent Mode

Display a compact table of the most recent session summaries:

```markdown
| Date | Session | Entries | Compression | Projects |
|------|---------|---------|-------------|----------|
| 2026-02-07 | 143022-1234 | 47 | ollama | ~/project-a |
| 2026-02-06 | 091500-5678 | 23 | rule-based | ~/project-b |
```

**Source:** Read files from `~/.claude/observations/summaries/` sorted by date descending. Parse YAML frontmatter for metadata.

### Search Mode

When a query string is provided:

1. **RAG search first**: `rag_search(query, project_path="~/.claude/observations")` if RAG is initialized
2. **Fallback**: Grep through `~/.claude/observations/summaries/*.md` for the query
3. Display matching summaries with relevance scores

### Detail Mode

Show full markdown content of each summary instead of just the table row.

### Stats Mode

Show observation system health:

```markdown
**Observation Memory Stats**
- Active session entries: {count from active-session.jsonl}
- Archived sessions: {count in archive/}
- Summary files: {count in summaries/}
- Total disk usage: {du -sh observations/}
- RAG indexed: {yes/no}
- Compression model: {from config}
- Retention: {days} days
```

## Implementation Steps

1. Check which mode was requested (recent/search/detail/stats)
2. For **recent/detail**:
   - `ls -t ~/.claude/observations/summaries/*.md | head -5`
   - Parse YAML frontmatter from each file
   - Display as table (recent) or full content (detail)
3. For **search**:
   - Try `rag_search` on observations project path
   - Fallback to grep through summaries
   - Display results with source file references
4. For **stats**:
   - Count files in each directory
   - Read config for settings
   - Check RAG init status
   - Display formatted stats block

## Dependencies

- `~/.claude/observations/` directory structure
- `~/.claude/config/observation-config.json` for settings
- Optional: RAG index on `~/.claude/observations` for semantic search
