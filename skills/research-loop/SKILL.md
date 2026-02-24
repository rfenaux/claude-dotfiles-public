---
name: research-loop
description: Self-directed research loop that cascades through RAG, web search, and user clarification to answer knowledge-gap questions with confidence scoring.
async:
  mode: never
  require_sync:
    - MCP tool access (rag_search, WebSearch)
    - User clarification prompts
    - Confidence scoring
context: fork
---

# /research - Self-Directed Research Loop

Autonomous research that cascades through local knowledge (RAG) -> web search -> user clarification until confidence threshold is met.

## Why This Is a Skill (Not an Agent)

This MUST run in the main session because it needs MCP tools:
- `rag_search` / `rag_tree_search` — RAG MCP server
- `WebSearch` — Built-in web search
- `WebFetch` — Follow-up URL fetching

Sub-agents cannot access MCP tools. This skill runs inline.

## Triggers

Invoke when:
- User says `/research`, "research X", "investigate X"
- User asks "how does X work?" with no obvious local answer
- RAG search returns insufficient results (confidence < 0.5)
- User says "find out about", "look into", "what do we know about"

## Commands

| Command | Action |
|---------|--------|
| `/research <topic>` | Start research loop on topic |
| `/research --rag-only <topic>` | Skip web search, RAG only |
| `/research --web-only <topic>` | Skip RAG, web search only |

## Configuration

Config file: `~/.claude/config/research-loop.json`

| Setting | Default | Description |
|---------|---------|-------------|
| `max_iterations` | 3 | Max research cycles |
| `confidence_threshold` | 0.8 | Stop when confidence >= this |
| `web_search_variants` | 3 | Number of web query variants |
| `auto_trigger` | false | Auto-invoke on knowledge gaps (future) |

## Workflow: State Machine

```
START -> RAG_SEARCH -> [confidence check]
                          |
                    >= 0.8 -> DONE (output findings)
                    < 0.8  -> EXPAND_QUERY -> WEB_SEARCH -> SYNTHESIZE
                                                              |
                                                    >= 0.8 -> DONE
                                                    < 0.8 and iterations < max -> USER_CLARIFY -> RAG_SEARCH (loop)
                                                    < 0.8 and iterations >= max -> DONE (with gaps noted)
```

### Phase 1: RAG_SEARCH

Search local knowledge using the 4-tier RAG cascade:

```
1. rag_search(query, project_path="~/.claude/lessons")     # Domain knowledge
2. rag_search(query, project_path="~/.claude")              # Config/agents
3. rag_search(query, project_path="<current_project>")      # Project-specific
4. rag_search(query, project_path="~/.claude/observations") # Session memory
```

For each tier:
- Use `rag_search` with `top_k=3`
- Collect results, deduplicate by source_file
- Track coverage: which aspects of the question are answered?

**Confidence scoring** (same formula as rag-search-agent):
- Coverage (0.4): What fraction of the question's sub-topics are addressed?
- Quality (0.3): How many sources were read fully vs. chunks only?
- Consensus (0.2): Do sources agree?
- Authority (0.1): Are sources primary (decision docs, specs) or secondary (summaries)?

If confidence >= threshold -> DONE. Output findings.

### Phase 2: EXPAND_QUERY

When RAG results are insufficient, expand the query:

1. Load `~/.claude/scripts/query_expander.py` (if available from F8)
2. Generate 2-3 query variants:
   - Synonym expansion: "HubSpot auth" -> "HubSpot OAuth authentication"
   - Reformulation: "how does X work" -> "X implementation mechanism"
   - Specificity: Add domain context from CTM if available
3. If query_expander.py not available, do manual expansion:
   - Remove question words, add domain terms
   - Try broader and narrower variants

### Phase 3: WEB_SEARCH

Search the web using expanded queries:

```
For each variant (max 3):
    WebSearch(query=variant)
    Collect top 3 results per query
    For most promising results:
        WebFetch(url=result_url, prompt="Extract information about [topic]")
```

Guidelines:
- Prefer official documentation, API docs, blog posts from vendors
- Skip forums/Q&A unless they're the only source
- Note the date of each source
- Cross-reference web findings with RAG results

### Phase 4: SYNTHESIZE

Combine RAG + web findings:

1. Merge evidence from both sources
2. Note where they agree (increases confidence)
3. Note where they conflict (decreases confidence)
4. Recalculate confidence score
5. If confidence >= threshold -> DONE
6. If confidence < threshold and iterations < max -> identify specific gap

### Phase 5: USER_CLARIFY (if needed)

When gaps remain after RAG + web:

1. Identify the specific unanswered question
2. Ask user: "I found [summary] but couldn't determine [specific gap]. Can you clarify?"
3. User response provides new context -> loop back to RAG_SEARCH with enriched query

Maximum 1 clarification per research loop. If still insufficient after clarification, output with gaps noted.

## Output Format

```markdown
## Research: [Topic]

### Findings (Confidence: X.XX)

[Synthesized answer with inline citations]

Key points:
- Point 1 [RAG: file.md, Section X]
- Point 2 [Web: https://..., accessed YYYY-MM-DD]
- Point 3 [RAG: file2.md + Web: url, corroborated]

### Sources

| # | Type | Source | Relevance |
|---|------|--------|-----------|
| 1 | RAG | `path/to/file.md` | high |
| 2 | Web | [Title](url) | medium |
| 3 | RAG | `path/to/file2.md` | high |

### Confidence Breakdown

- **Coverage**: X.XX (N/M sub-topics addressed)
- **Quality**: X.XX (N sources read fully)
- **Consensus**: X.XX (N/M sources agree)
- **Authority**: X.XX (N/M primary sources)

### Gaps

- [OPEN: Specific unanswered question 1]
- [OPEN: Specific unanswered question 2]

### Research Needed: true/false
```

**Research Needed** is `true` if confidence < threshold AND max iterations reached (indicates deeper investigation required).

## Iteration Limits

| Constraint | Value | Reason |
|------------|-------|--------|
| Max iterations | 3 | Prevent runaway loops |
| Max web searches | 9 | 3 variants × 3 iterations |
| Max web fetches | 6 | 2 deep reads per iteration |
| Max clarifications | 1 | Don't annoy user |

## Integration with Other Systems

| System | Integration |
|--------|-------------|
| **RAG** | Primary search source (4-tier cascade) |
| **CTM** | Add research context to active task decisions |
| **query_expander** (F8) | Generate query variants |
| **rag-search-agent** | If confidence < threshold, agent flags "Research Needed: true" |
| **Lessons** | Research findings can become lessons if significant |

## Examples

### Example 1: Full Loop
```
User: /research "How does HubSpot handle OAuth2 refresh tokens?"

Phase 1 (RAG): Found partial - HubSpot API auth basics, no refresh token specifics
Confidence: 0.45 (coverage low)

Phase 2 (Expand): "HubSpot OAuth2 refresh token rotation", "HubSpot API token expiry renewal"

Phase 3 (Web): Found HubSpot developer docs on token refresh, blog post on best practices
Confidence: 0.85 (above threshold)

Output: Synthesized answer with RAG + web sources cited
```

### Example 2: RAG Sufficient
```
User: /research "What did we decide about the database for Project X?"

Phase 1 (RAG): Found DECISIONS.md entry, 2 session summaries
Confidence: 0.92

Output: Direct answer with citations, no web search needed
```

### Example 3: Clarification Needed
```
User: /research "authentication approach"

Phase 1 (RAG): Multiple auth-related docs, unclear which system
Confidence: 0.35

Phase 2+3 (Web): Too broad to search effectively
Confidence: 0.40

Phase 5 (Clarify): "I found docs about HubSpot OAuth, JWT tokens, and SSO.
Which authentication system are you asking about?"

User: "HubSpot OAuth"

Phase 1 (retry): Focused RAG search -> high-quality results
Confidence: 0.88

Output: Focused answer about HubSpot OAuth
```
