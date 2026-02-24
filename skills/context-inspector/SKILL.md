---
name: context-inspector
description: Inspect context window usage and identify optimization opportunities
aliases: [context, ctx]
async:
  mode: never
context: fork
---

# /context - Context Inspector

Inspect what's consuming your context window and get optimization recommendations.

## Commands

| Command | Description |
|---------|-------------|
| `/context` | Quick summary (fullness + top consumers) |
| `/context list` | All injected content with estimated sizes |
| `/context detail` | Full breakdown by category + age analysis |
| `/context trim` | Recommendations for reducing context |
| `/context history` | Message history statistics |

---

## Quick Summary (`/context`)

When invoked without arguments, provide a quick overview:

```
═══ Context Usage ═══
Usage: 67% (134K / 200K tokens)

Top Consumers:
1. Tool Results     45K (34%)  ⚠ 12 results > 30min old
2. Conversation     38K (28%)
3. CLAUDE.md        22K (16%)
4. Skills           15K (11%)
5. System           14K (11%)

Quick Actions:
• Prune old tool results → save ~15K
• /compact → save ~40K
```

---

## List Command (`/context list`)

Show all injected content with sizes:

```
═══ Injected Content ═══

Config Files:
├── CLAUDE.md                    ~8,200 tokens
├── RAG_GUIDE.md                 ~2,100 tokens
├── CTM_GUIDE.md                 ~4,900 tokens
└── Subtotal                     ~15,200 tokens

Skills (26 active):
├── solution-architect           ~1,200 tokens
├── hubspot-specialist             ~890 tokens
├── ctm                            ~650 tokens
└── ... (23 more)                ~3,400 tokens
└── Subtotal                      ~6,140 tokens

Tool Schemas:
├── Core tools (Read, Write...)  ~2,100 tokens
├── MCP tools (RAG, Fathom...)   ~1,400 tokens
└── Subtotal                      ~3,500 tokens

System:
├── Base prompts                  ~1,800 tokens
├── Hook outputs                    ~300 tokens
└── Subtotal                      ~2,100 tokens

═══════════════════════════════════
Total Injected: ~26,940 tokens (13%)
```

---

## Detail Command (`/context detail`)

Deep breakdown with actionable insights:

```
═══ Context Detail ═══

CONVERSATION HISTORY
├── User messages:        12 msgs  (~4,500 tokens)
├── Assistant messages:   11 msgs  (~28,500 tokens)
├── Tool calls:          34 calls  (~2,300 tokens)
└── Tool results:        34 results (~45,700 tokens)
    └── ⚠ Tool results are 57% of history!

TOOL RESULTS BY AGE
├── < 10 min:    8 results  (12,300 tokens) [protected]
├── 10-30 min:  12 results  (18,200 tokens)
├── 30-60 min:   8 results  (10,500 tokens) ← prune candidates
└── > 60 min:    6 results  ( 4,700 tokens) ← prune candidates

TOOL RESULTS BY TYPE
├── Read:       15 results  (25,400 tokens)
├── Grep:        8 results  ( 8,900 tokens)
├── Bash:        6 results  ( 6,200 tokens)
├── WebFetch:    3 results  ( 4,100 tokens)
└── Other:       2 results  ( 1,100 tokens)

LARGE ITEMS (>2K tokens each)
├── Read of ~/.claude/CTM_GUIDE.md     4,892 tokens [32min ago]
├── Read of ~/.claude/CLAUDE.md        8,234 tokens [45min ago]
├── Grep results at msg #23            3,456 tokens [28min ago]
└── WebFetch of docs.openclaw.ai       2,890 tokens [15min ago]

RECOMMENDATIONS
1. Prune 14 tool results > 30min → save ~15,200 tokens
2. Consider /compact → save ~40,000 tokens
3. Large Read at msg #23 could be soft-trimmed → save ~3,000 tokens
```

---

## Trim Command (`/context trim`)

Specific pruning recommendations:

```
═══ Trim Recommendations ═══

SAFE TO PRUNE (14 items, ~15,200 tokens):
These tool results are old and not referenced recently.

1. [45min] Read ~/.claude/CLAUDE.md (8,234 tokens)
   → Soft-trim to 300 tokens

2. [38min] Grep for "memory" (3,456 tokens)
   → Hard-clear (results outdated)

3. [32min] Read ~/.claude/CTM_GUIDE.md (4,892 tokens)
   → Soft-trim to 300 tokens

... (11 more)

PROTECTED (8 items):
These are recent or part of active context.

Note: Automatic pruning is configured in ~/.claude/config/pruning.json
```

---

## History Command (`/context history`)

Message-level statistics:

```
═══ Message History ═══

Total Messages: 57
├── User:       12 (avg 375 tokens)
├── Assistant:  11 (avg 2,590 tokens)
├── Tool Call:  34 (avg 68 tokens)
└── Tool Result: 34 (avg 1,344 tokens)

Conversation Flow:
Turn  1: U(120) → A(450) → T×2(2,100)
Turn  2: U(85) → A(890) → T×4(5,600)
Turn  3: U(200) → A(1,200) → T×1(890)
...
Turn 12: U(380) → A(2,100) → T×6(8,900)

Largest Turns:
• Turn 7: 15,600 tokens (bulk file reads)
• Turn 2: 6,575 tokens (initial exploration)
• Turn 11: 5,200 tokens (grep searches)
```

---

## Implementation Notes

When invoked, I will:

1. **Estimate tokens** using the heuristic: ~4 characters ≈ 1 token
2. **Categorize content** into: conversation, injection, tool results
3. **Analyze tool results** by age (using timestamps) and size
4. **Identify prune candidates** based on rules in `~/.claude/config/pruning.json`
5. **Provide actionable recommendations** prioritized by savings

### Token Estimation Formula

```
tokens ≈ characters / 4
```

This is approximate - actual tokenization varies. For more accuracy:
- Code: ~3.5 chars/token
- English prose: ~4 chars/token
- JSON/structured: ~3 chars/token

### Age Calculation

Tool results should include timestamps. If missing, I estimate based on:
- Position in conversation (earlier = older)
- Surrounding message timestamps

### Pruning Config Reference

The `/context trim` command reads from `~/.claude/config/pruning.json`:

```json
{
  "default_ttl_minutes": 60,
  "default_strategy": "soft",
  "tool_rules": {
    "Read": {"ttl_minutes": 30, "strategy": "soft"},
    "Grep": {"ttl_minutes": 45, "strategy": "soft"},
    "Glob": {"ttl_minutes": 30, "strategy": "hard"}
  }
}
```

---

## Related Features

- **Memory Flush** — Extracts decisions before compaction
- **Tool Result Pruning** — Automatic pruning based on TTL
- **CTM Checkpoints** — Saves task state before compaction

---

*Part of OpenClaw-inspired improvements (Phase 1, F06)*
