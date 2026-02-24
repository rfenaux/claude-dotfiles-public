# PRD: Proactive Memory System

**Version:** 1.0
**Date:** 2026-02-02
**Author:** Raphael + Claude
**Inspired By:** [memU](https://github.com/NevaMind-AI/memU) framework

---

## 1. Executive Summary

The Proactive Memory System enhances Claude Code with intelligent context surfacing capabilities inspired by the memU framework. Instead of waiting for users to query for context, the system proactively retrieves and presents relevant information based on:

1. **Current task context** (CTM)
2. **Document topic clustering** (RAG)
3. **Learned interaction patterns** (behavioral)

This reduces cognitive load, improves session continuity, and optimizes token usage by surfacing the right context at the right time.

---

## 2. Problem Statement

### Current Pain Points

1. **Manual Context Retrieval**: Users must explicitly query RAG or read files to get context
2. **Cold Start Sessions**: Each session starts without awareness of relevant historical context
3. **Flat Document Organization**: RAG indexes lack semantic grouping beyond basic categories
4. **No Pattern Learning**: System doesn't learn from repeated user behaviors

### User Impact

- Time spent re-discovering information already in the knowledge base
- Missed connections between current tasks and relevant past decisions
- Suboptimal task prioritization without behavioral insights

---

## 3. Solution Overview

### Three Integrated Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    PROACTIVE MEMORY SYSTEM                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │ PROACTIVE RAG    │  │ TOPIC CLUSTERING │  │ INTENT         │ │
│  │ SURFACING        │  │                  │  │ PREDICTION     │ │
│  ├──────────────────┤  ├──────────────────┤  ├────────────────┤ │
│  │ SessionStart     │  │ Post-Index       │  │ PostToolUse    │ │
│  │ CTM → Query      │  │ DBSCAN + TF-IDF  │  │ Pattern Track  │ │
│  │ RAG Cascade      │  │ Cluster Storage  │  │ Prediction API │ │
│  │ Summary Output   │  │ Filtered Search  │  │ Briefing Inject│ │
│  └──────────────────┘  └──────────────────┘  └────────────────┘ │
│                                                                  │
│  Phase 1 (MVP)          Phase 2              Phase 3            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Detailed Design

### 4.1 Proactive RAG Surfacing (Phase 1)

#### Purpose
Automatically surface relevant documents at session start based on CTM task context.

#### Trigger
`SessionStart` hook

#### Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Extract CTM Context                                          │
│    ├─ Active task title (weight: 3x)                            │
│    ├─ Task tags (weight: 2x)                                    │
│    ├─ Recent decisions (weight: 1.5x)                           │
│    └─ Project directory (weight: 1x)                            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Build Composite Query                                        │
│    query = f"{title} {title} {title} {tags} {tags} {decisions}" │
│    (repeated terms = higher weight in embedding)                │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. RAG Cascade Search                                           │
│    a. ~/.claude/lessons (domain knowledge) → top 2              │
│    b. ~/.claude (config/agents/skills) → top 2                  │
│    c. $PROJECT/.rag (project-specific) → top 2                  │
│    Stop when 3+ relevant results found                          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. Generate Summaries                                           │
│    - Filter: relevance >= medium                                │
│    - Deduplicate by source_file                                 │
│    - Format: title + one-sentence summary                       │
│    - Max output: 400 tokens                                     │
└─────────────────────────────────────────────────────────────────┘
```

#### Output Format

```markdown
### Proactive Context

**Relevant to: [task title]**

From Lessons:
- **HubSpot API Rate Limits**: Use exponential backoff with 10-second base...
- **OAuth Token Refresh**: Store refresh tokens securely, never in logs...

From Config:
- **hubspot-api-specialist agent**: Routes to domain-specific sub-agents...

From Project:
- **DECISIONS.md A-012**: Using PostgreSQL for audit trail storage...
```

#### Configuration

```json
// ~/.claude/config/proactive-rag.json
{
  "enabled": true,
  "max_results": 5,
  "max_tokens": 400,
  "cascade_order": ["lessons", "config", "project"],
  "min_relevance": "medium",
  "weights": {
    "task_title": 3,
    "task_tags": 2,
    "decisions": 1.5,
    "project": 1
  }
}
```

#### Files

| File | Purpose |
|------|---------|
| `~/.claude/hooks/proactive-rag-surfacer.sh` | Main hook |
| `~/.claude/lib/proactive_rag.py` | Python logic |
| `~/.claude/config/proactive-rag.json` | Configuration |

---

### 4.2 Topic Clustering (Phase 2)

#### Purpose
Automatically group indexed documents by semantic similarity for better organization and filtered search.

#### Trigger
Post `rag_index` completion

#### Algorithm

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Load Document Embeddings                                     │
│    - Get all summary vectors from catalog table                 │
│    - Minimum 5 documents required for clustering                │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. DBSCAN Clustering                                            │
│    - eps: median pairwise distance * 0.8                        │
│    - min_samples: 2                                             │
│    - No preset cluster count (density-based)                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Generate Cluster Labels                                      │
│    - Extract text from all docs in cluster                      │
│    - TF-IDF to find top 3 distinguishing terms                  │
│    - Label format: "term1-term2-term3"                          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. Store Clusters                                               │
│    - project/.rag/topic-clusters.json                           │
│    - Update catalog table with cluster_id                       │
└─────────────────────────────────────────────────────────────────┘
```

#### Data Models

```python
@dataclass
class TopicCluster:
    id: str                    # "cluster_001"
    label: str                 # "hubspot-api-auth"
    centroid: List[float]      # Average embedding vector
    document_count: int
    top_keywords: List[str]    # ["hubspot", "api", "authentication"]
    created_at: str            # ISO timestamp

# Storage: project/.rag/topic-clusters.json
{
  "version": "1.0",
  "generated_at": "2026-02-02T10:00:00Z",
  "clusters": [
    {
      "id": "cluster_001",
      "label": "hubspot-api-auth",
      "document_count": 8,
      "top_keywords": ["hubspot", "api", "authentication"],
      "documents": ["doc1.md", "doc2.md", ...]
    }
  ]
}
```

#### Schema Extension

```python
# vectordb.py catalog table additions
pa.field("cluster_id", pa.string()),      # "cluster_001" or null
pa.field("topic_keywords", pa.string()),  # JSON: ["hubspot", "api"]
```

#### Enhanced rag_search

```python
@mcp.tool()
def rag_search(
    query: str,
    project_path: str,
    top_k: int = 5,
    category: str = None,        # existing
    cluster_id: str = None,      # NEW: filter by cluster
    topics: List[str] = None,    # NEW: filter by topic keywords
    min_relevance: str = None,   # existing
) -> dict:
    """
    Search with optional cluster/topic filtering.

    cluster_id: Only return results from specified cluster
    topics: Only return results containing ALL specified topics
    """
```

#### Files

| File | Purpose |
|------|---------|
| `~/.claude/mcp-servers/rag-server/src/rag_server/topic_clusters.py` | Clustering logic |
| `chunk_classifier.py` | Extended with topic extraction |
| `vectordb.py` | Schema + clustering trigger |
| `server.py` | Extended rag_search |

---

### 4.3 Intent Prediction (Phase 3)

#### Purpose
Learn from interaction patterns to predict what the user needs before they ask.

#### Trigger
`PostToolUse` hook (for tracking)
`SessionStart` (for predictions)

#### Pattern Detection

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Track Tool Sequences                                         │
│    - Log: [timestamp, tool_name, context_keywords]              │
│    - Store in /tmp/claude-tools-{session}.log                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Detect Patterns (background)                                 │
│    - Analyze sequences of 2-3 tools                             │
│    - Match against existing patterns                            │
│    - If match: increment frequency                              │
│    - If new + frequency >= 3: create pattern                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Prediction (on session start)                                │
│    - Load patterns matching current CTM context                 │
│    - Filter by confidence >= 0.5                                │
│    - Return top 3 predictions                                   │
└─────────────────────────────────────────────────────────────────┘
```

#### Data Model

```python
@dataclass
class InteractionPattern:
    id: str                    # "pat_001"
    trigger: str               # "ctm spawn" or "hubspot implementation"
    predicted_action: str      # "search for similar HubSpot projects"
    frequency: int             # Times observed (min 3 to create)
    confidence: float          # 0.0 - 1.0 (formula below)
    project: str               # Project path or "global"
    last_seen: str             # ISO timestamp
    context_keywords: List[str] # ["hubspot", "implementation", "api"]
    tool_sequence: List[str]   # ["Read", "Grep", "rag_search"]

# Confidence calculation
confidence = min(0.95, frequency / (frequency + 5) * recency_factor)
recency_factor = exp(-days_since_last_seen / 30)

# Storage: ~/.claude/intent-patterns.json
{
  "version": "1.0",
  "patterns": [...],
  "stats": {
    "total_patterns": 15,
    "global_patterns": 5,
    "project_patterns": 10
  }
}
```

#### Briefing Integration

```python
# In briefing.py
def _generate_predicted_actions_section(self) -> Optional[BriefingSection]:
    """Surface predicted next actions based on learned patterns."""
    predictions = get_predictions(
        project=str(self.project_path),
        ctm_context=self._get_ctm_keywords(),
        top_k=3
    )

    if not predictions:
        return None

    lines = ["Based on your patterns:"]
    for p in predictions:
        if p.confidence >= 0.7:
            lines.append(f"  → {p.predicted_action} (likely)")
        elif p.confidence >= 0.5:
            lines.append(f"  ? {p.predicted_action} (possible)")

    return BriefingSection(
        title="Predicted Actions",
        content="\n".join(lines),
        priority=8  # After recommendations
    )
```

#### Scheduler Integration

```python
# In scheduler.py calculate_priority()
pattern_boost = self._get_pattern_boost(agent)
if pattern_boost > 0:
    score += pattern_boost * 0.1  # Max 10% boost from patterns
```

#### Files

| File | Purpose |
|------|---------|
| `~/.claude/lib/intent_predictor.py` | Pattern logic |
| `~/.claude/hooks/pattern-tracker.sh` | PostToolUse hook |
| `~/.claude/intent-patterns.json` | Pattern storage |
| `briefing.py` | Extended with predictions |
| `scheduler.py` | Extended with pattern boost |

---

## 5. Token Budget

| Component | Max Tokens | Strategy |
|-----------|------------|----------|
| Proactive RAG summaries | 400 | 5 docs × ~80 tokens each |
| Predicted actions | 100 | 3 predictions × ~30 tokens |
| **Total injection** | **500** | Strict cap, hard limit |

---

## 6. Graceful Degradation

All components designed to fail silently:

| Failure | Behavior |
|---------|----------|
| RAG unavailable | No proactive surfacing, session continues |
| Ollama down | No embeddings, use keyword fallback |
| Pattern file corrupt | Return empty predictions |
| Clustering fails | Documents remain unclustered |
| Any Python exception | Log to file, exit 0 |

Logging: `~/.claude/logs/proactive-memory.log`

---

## 7. Implementation Phases

### Phase 1: Proactive RAG Surfacing (MVP)
- Duration: 2-3 hours
- Files: 4 new, 1 modified
- Risk: Low (additive, non-breaking)

### Phase 2: Topic Clustering
- Duration: 3-4 hours
- Files: 1 new, 3 modified
- Risk: Medium (schema changes)
- Prerequisite: Phase 1 complete

### Phase 3: Intent Prediction
- Duration: 4-5 hours
- Files: 3 new, 2 modified
- Risk: Medium (hook addition, CTM integration)
- Prerequisite: Phase 2 complete

---

## 8. Success Metrics

### Phase 1
- [ ] Hook executes without error on session start
- [ ] Relevant documents surfaced for 80%+ of sessions with active CTM tasks
- [ ] Output under 500 tokens

### Phase 2
- [ ] Clusters created for projects with 5+ documents
- [ ] Cluster labels are meaningful (human-readable)
- [ ] Filtered search returns subset of results

### Phase 3
- [ ] Patterns detected after 3+ repetitions
- [ ] Predictions appear in briefing with confidence scores
- [ ] Pattern boost affects task priority

---

## 9. Future Enhancements

1. **Proactive Mid-Session Surfacing**: PreToolUse hook suggests docs before certain tools
2. **Cross-Project Pattern Transfer**: Learn from one project, apply to similar
3. **Confidence Decay**: Prune patterns not seen in 30+ days
4. **Feedback Loop**: User can dismiss/confirm predictions to improve accuracy

---

## 10. References

- [memU Framework](https://github.com/NevaMind-AI/memU) - Inspiration
- [DBSCAN Algorithm](https://scikit-learn.org/stable/modules/clustering.html#dbscan) - Clustering
- [TF-IDF](https://scikit-learn.org/stable/modules/feature_extraction.html#tfidf-term-weighting) - Keyword extraction
- `~/.claude/hooks/lesson-surfacer.sh` - Pattern to follow
- `~/.claude/ctm/lib/briefing.py` - Integration point
