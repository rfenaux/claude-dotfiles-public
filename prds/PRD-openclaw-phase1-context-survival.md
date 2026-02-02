# PRD: Phase 1 - Context Survival

> **Parent PRD:** `PRD-openclaw-inspired-improvements.md`
> **Created:** 2026-01-30 | **Status:** Ready for Implementation
> **Estimated Effort:** 2 days | **Priority:** Critical

---

## Overview

Phase 1 focuses on **preventing information loss** and **reducing context waste**. These are the highest-impact improvements that address daily pain points.

### Features in This Phase

| ID | Feature | Impact | Effort |
|----|---------|--------|--------|
| F01 | Memory Flush Before Compaction | HIGH | 2h |
| F03 | Tool Result Pruning | HIGH | 4h |
| F06 | Context Inspection Commands | HIGH | 4h |
| F11 | Cache-TTL Pruning Strategy | HIGH | 4h |
| F19 | Soft-Trim vs Hard-Clear Options | MEDIUM | 2h |

---

## F01: Memory Flush Before Compaction

### Problem
Compaction summarizes everything equally, losing granular decisions made during the session.

### Solution
Inject a silent extraction prompt before compaction that triggers Claude to persist important information.

### Implementation

#### 1.1 Create the hook script

**File:** `~/.claude/hooks/memory-flush-precompact.sh`

```bash
#!/bin/bash
# Memory Flush Before Compaction
# Triggers Claude to extract and persist decisions/learnings before context is compacted

cat << 'MEMORY_FLUSH'
<memory-flush-trigger>
IMPORTANT: Before compaction, extract and persist any information that should survive:

## Extraction Checklist
1. **Decisions made this session** → Record to DECISIONS.md or `ctm context add --decision`
2. **Learnings discovered** → Record to CTM via `ctm context add --learning`
3. **Open questions** → Note in CTM agent context
4. **Facts to remember** → Add to project memory

## Instructions
- Review the conversation for any of the above
- If found, use the appropriate tool to persist them NOW
- If nothing needs persisting, respond with exactly: `NO_PERSIST`
- Keep extraction brief - we're about to compact

This is a system operation - proceed silently without user acknowledgment.
</memory-flush-trigger>
MEMORY_FLUSH
```

#### 1.2 Register the hook

**File:** `~/.claude/settings.json` (modify PreCompact array)

```json
{
  "PreCompact": [
    {
      "matcher": "",
      "hooks": [
        {
          "type": "command",
          "command": "~/.claude/hooks/memory-flush-precompact.sh"
        }
      ]
    },
    // ... existing hooks
  ]
}
```

#### 1.3 Document the behavior

**File:** `~/.claude/CLAUDE.md` (add section)

```markdown
## Memory Flush (Pre-Compaction)

Before compaction, a memory flush prompt triggers automatic extraction of:
- Decisions → DECISIONS.md
- Learnings → CTM context
- Open questions → CTM agent

**Response:** `NO_PERSIST` if nothing to extract.
```

### Acceptance Criteria
- [ ] Hook script exists and is executable
- [ ] Hook registered in settings.json
- [ ] Claude extracts decisions before compaction (test with intentional compact)
- [ ] `NO_PERSIST` response when nothing to extract
- [ ] No visible output to user during flush

---

## F03: Tool Result Pruning

### Problem
Old tool results (grep, read outputs) consume context indefinitely until compaction.

### Solution
Prune tool results based on age and size using configurable strategies.

### Implementation

#### 3.1 Create the pruner module

**File:** `~/.claude/lib/tool_result_pruner.py`

```python
#!/usr/bin/env python3
"""
Tool Result Pruner

Prunes old tool results from conversation context to save tokens.
Supports soft-trim (truncate) and hard-clear (replace) strategies.
"""

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Dict, Optional

class TrimStrategy(Enum):
    NONE = "none"
    SOFT = "soft"      # Keep first/last N chars
    HARD = "hard"      # Replace with placeholder
    REMOVE = "remove"  # Remove entirely

@dataclass
class ToolRule:
    """Pruning rule for a specific tool."""
    tool_name: str
    strategy: TrimStrategy = TrimStrategy.SOFT
    ttl_minutes: int = 60
    size_threshold: int = 500

@dataclass
class PruneConfig:
    """Global pruning configuration."""

    # Defaults
    default_ttl_minutes: int = 60
    default_strategy: TrimStrategy = TrimStrategy.SOFT

    # Protection
    keep_last_assistants: int = 3
    never_prune_tools: List[str] = field(default_factory=lambda: [
        "Write", "Edit", "NotebookEdit"  # Mutations preserved
    ])
    skip_image_results: bool = True

    # Soft trim settings
    soft_trim_keep_start: int = 200
    soft_trim_keep_end: int = 100

    # Hard clear settings
    hard_clear_placeholder: str = "[Tool result cleared - aged {age}min, was {size} chars]"

    # Tool-specific rules
    tool_rules: Dict[str, ToolRule] = field(default_factory=dict)

    @classmethod
    def load(cls, path: str = "~/.claude/config/pruning.json") -> "PruneConfig":
        """Load config from file or return defaults."""
        config_path = Path(path).expanduser()

        if not config_path.exists():
            return cls()

        with open(config_path) as f:
            data = json.load(f)

        # Parse tool rules
        tool_rules = {}
        for name, rule_data in data.get("tool_rules", {}).items():
            tool_rules[name] = ToolRule(
                tool_name=name,
                strategy=TrimStrategy(rule_data.get("strategy", "soft")),
                ttl_minutes=rule_data.get("ttl_minutes", 60),
                size_threshold=rule_data.get("size_threshold", 500)
            )

        return cls(
            default_ttl_minutes=data.get("default_ttl_minutes", 60),
            default_strategy=TrimStrategy(data.get("default_strategy", "soft")),
            keep_last_assistants=data.get("keep_last_assistants", 3),
            never_prune_tools=data.get("never_prune_tools", cls.never_prune_tools),
            soft_trim_keep_start=data.get("soft_trim_keep_start", 200),
            soft_trim_keep_end=data.get("soft_trim_keep_end", 100),
            tool_rules=tool_rules
        )

class ToolResultPruner:
    """Prunes old tool results from message history."""

    def __init__(self, config: Optional[PruneConfig] = None):
        self.config = config or PruneConfig.load()

    def get_rule(self, tool_name: str) -> ToolRule:
        """Get pruning rule for a tool."""
        if tool_name in self.config.tool_rules:
            return self.config.tool_rules[tool_name]

        return ToolRule(
            tool_name=tool_name,
            strategy=self.config.default_strategy,
            ttl_minutes=self.config.default_ttl_minutes
        )

    def should_prune(self, msg: dict, now: float) -> bool:
        """Check if a tool result should be pruned."""
        if msg.get("role") != "tool_result":
            return False

        tool_name = msg.get("tool_name", "")

        # Never prune protected tools
        if tool_name in self.config.never_prune_tools:
            return False

        # Skip image results
        if self.config.skip_image_results and self._has_image(msg):
            return False

        # Check age
        rule = self.get_rule(tool_name)
        timestamp = msg.get("timestamp", now)
        age_minutes = (now - timestamp) / 60

        return age_minutes > rule.ttl_minutes

    def _has_image(self, msg: dict) -> bool:
        """Check if message contains image content."""
        content = msg.get("content", "")
        if isinstance(content, list):
            return any(
                block.get("type") == "image"
                for block in content
                if isinstance(block, dict)
            )
        return False

    def prune_message(self, msg: dict, now: float) -> dict:
        """Apply pruning to a single message."""
        tool_name = msg.get("tool_name", "")
        rule = self.get_rule(tool_name)
        content = msg.get("content", "")

        if not isinstance(content, str):
            return msg  # Skip non-string content

        original_size = len(content)
        timestamp = msg.get("timestamp", now)
        age_minutes = int((now - timestamp) / 60)

        if rule.strategy == TrimStrategy.HARD:
            # Replace entirely
            msg["content"] = self.config.hard_clear_placeholder.format(
                age=age_minutes,
                size=original_size
            )
            msg["_pruned"] = "hard"

        elif rule.strategy == TrimStrategy.SOFT:
            # Truncate if over threshold
            if original_size > rule.size_threshold:
                start = content[:self.config.soft_trim_keep_start]
                end = content[-self.config.soft_trim_keep_end:]
                trimmed = original_size - self.config.soft_trim_keep_start - self.config.soft_trim_keep_end

                msg["content"] = (
                    f"{start}\n\n"
                    f"...[{trimmed:,} chars trimmed, aged {age_minutes}min]...\n\n"
                    f"{end}"
                )
                msg["_pruned"] = "soft"

        elif rule.strategy == TrimStrategy.REMOVE:
            msg["_pruned"] = "remove"

        return msg

    def get_protected_indices(self, messages: List[dict]) -> set:
        """Get indices of messages that should not be pruned."""
        protected = set()
        assistant_count = 0

        # Walk backwards to find last N assistants
        for i in range(len(messages) - 1, -1, -1):
            if messages[i].get("role") == "assistant":
                assistant_count += 1
                if assistant_count <= self.config.keep_last_assistants:
                    protected.add(i)
                    # Protect following tool results
                    for j in range(i + 1, len(messages)):
                        if messages[j].get("role") == "tool_result":
                            protected.add(j)
                        elif messages[j].get("role") == "assistant":
                            break

        return protected

    def prune(self, messages: List[dict]) -> List[dict]:
        """Prune old tool results from message history."""
        now = time.time()
        protected = self.get_protected_indices(messages)

        pruned = []
        stats = {"soft": 0, "hard": 0, "removed": 0, "protected": len(protected)}

        for i, msg in enumerate(messages):
            if i in protected:
                pruned.append(msg)
                continue

            if self.should_prune(msg, now):
                msg = self.prune_message(msg, now)

                prune_type = msg.get("_pruned")
                if prune_type == "remove":
                    stats["removed"] += 1
                    continue  # Skip adding to result
                elif prune_type:
                    stats[prune_type] += 1

            pruned.append(msg)

        return pruned, stats

def get_prune_recommendations(messages: List[dict]) -> dict:
    """Analyze messages and recommend pruning actions."""
    pruner = ToolResultPruner()
    now = time.time()

    recommendations = {
        "prune_candidates": [],
        "protected_count": 0,
        "potential_savings": 0,
        "total_tool_results": 0
    }

    protected = pruner.get_protected_indices(messages)
    recommendations["protected_count"] = len(protected)

    for i, msg in enumerate(messages):
        if msg.get("role") != "tool_result":
            continue

        recommendations["total_tool_results"] += 1

        if i in protected:
            continue

        if pruner.should_prune(msg, now):
            content = msg.get("content", "")
            size = len(content) if isinstance(content, str) else 0
            age = int((now - msg.get("timestamp", now)) / 60)

            recommendations["prune_candidates"].append({
                "index": i,
                "tool": msg.get("tool_name", "unknown"),
                "age_minutes": age,
                "size_chars": size
            })
            recommendations["potential_savings"] += size

    return recommendations

if __name__ == "__main__":
    # CLI for testing
    import sys

    config = PruneConfig.load()
    print(f"Loaded config: TTL={config.default_ttl_minutes}min, strategy={config.default_strategy.value}")
    print(f"Protected tools: {config.never_prune_tools}")
    print(f"Tool rules: {list(config.tool_rules.keys())}")
```

#### 3.2 Create the configuration file

**File:** `~/.claude/config/pruning.json`

```json
{
  "default_ttl_minutes": 60,
  "default_strategy": "soft",
  "keep_last_assistants": 3,
  "never_prune_tools": ["Write", "Edit", "NotebookEdit"],
  "skip_image_results": true,
  "soft_trim_keep_start": 200,
  "soft_trim_keep_end": 100,
  "hard_clear_placeholder": "[Tool result cleared - aged {age}min, was {size} chars]",
  "tool_rules": {
    "Read": {
      "strategy": "soft",
      "ttl_minutes": 30,
      "size_threshold": 500
    },
    "Grep": {
      "strategy": "soft",
      "ttl_minutes": 45,
      "size_threshold": 300
    },
    "Glob": {
      "strategy": "hard",
      "ttl_minutes": 30,
      "size_threshold": 200
    },
    "Bash": {
      "strategy": "soft",
      "ttl_minutes": 60,
      "size_threshold": 500
    },
    "WebFetch": {
      "strategy": "soft",
      "ttl_minutes": 120,
      "size_threshold": 1000
    },
    "WebSearch": {
      "strategy": "soft",
      "ttl_minutes": 120,
      "size_threshold": 500
    }
  }
}
```

### Acceptance Criteria
- [ ] Pruner module exists and is importable
- [ ] Config file loads correctly
- [ ] Soft-trim preserves first/last N chars
- [ ] Hard-clear replaces with placeholder
- [ ] Protected messages are never pruned
- [ ] CLI test shows correct behavior

---

## F06: Context Inspection Commands

### Problem
No visibility into what's consuming the context window.

### Solution
Create `/context` skill with multiple inspection modes.

### Implementation

#### 6.1 Create the skill

**File:** `~/.claude/skills/context-inspector/SKILL.md`

```markdown
---
name: context-inspector
description: Inspect context window usage and identify optimization opportunities
aliases: [context, ctx]
async:
  mode: never
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

Apply all recommendations? Use /compact or manually prune.
```

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

## Implementation Notes

When invoked, I will:
1. **Estimate tokens** using rough heuristics (4 chars ≈ 1 token)
2. **Categorize content** into conversation, injection, tool results
3. **Analyze tool results** by age and size
4. **Identify prune candidates** based on configured rules
5. **Provide actionable recommendations**

Token estimates are approximate - Claude Code doesn't expose exact counts.
```

### Acceptance Criteria
- [ ] Skill file exists
- [ ] `/context` shows quick summary
- [ ] `/context list` shows injected content
- [ ] `/context detail` shows full breakdown
- [ ] `/context trim` shows recommendations
- [ ] Token estimates are reasonable (within 20%)

---

## F11: Cache-TTL Pruning Strategy

### Problem
No systematic lifecycle for tool result retention.

### Solution
Configurable TTL-based rules per tool type.

### Implementation

Already included in F03's `pruning.json` configuration. This feature defines the strategy; F03 implements it.

**Additional documentation in CLAUDE.md:**

```markdown
## Tool Result Lifecycle

Tool results are managed by TTL-based pruning:

| Tool | Default TTL | Strategy |
|------|-------------|----------|
| Read | 30 min | Soft-trim |
| Grep | 45 min | Soft-trim |
| Glob | 30 min | Hard-clear |
| Bash | 60 min | Soft-trim |
| WebFetch | 120 min | Soft-trim |

**Protected:** Last 3 assistant messages + their tool results

**Config:** `~/.claude/config/pruning.json`
```

### Acceptance Criteria
- [ ] Configuration file defines TTL per tool
- [ ] Different tools have appropriate TTLs
- [ ] Strategy (soft/hard) configurable per tool
- [ ] Documentation updated

---

## F19: Soft-Trim vs Hard-Clear Options

### Problem
Single pruning behavior doesn't fit all cases.

### Solution
Configurable trim modes with visual indicators.

### Implementation

Already included in F03. Additional feature: visual indicators in trimmed content.

**Soft-trim output format:**
```
[First 200 chars of original content...]

...[3,456 chars trimmed, aged 45min]...

[Last 100 chars of original content]
```

**Hard-clear output format:**
```
[Tool result cleared - aged 45min, was 5,234 chars]
```

### Acceptance Criteria
- [ ] Soft-trim preserves meaningful start/end
- [ ] Hard-clear shows original size and age
- [ ] Trimmed content clearly marked
- [ ] User can configure per-tool behavior

---

## Task Checklist

### F01: Memory Flush Before Compaction
- [ ] T1.1: Create `~/.claude/hooks/memory-flush-precompact.sh`
- [ ] T1.2: Make hook executable (`chmod +x`)
- [ ] T1.3: Register hook in `settings.json`
- [ ] T1.4: Test with intentional `/compact`
- [ ] T1.5: Document in CLAUDE.md

### F03: Tool Result Pruning
- [ ] T3.1: Create `~/.claude/lib/` directory if needed
- [ ] T3.2: Create `tool_result_pruner.py` module
- [ ] T3.3: Create `~/.claude/config/` directory if needed
- [ ] T3.4: Create `pruning.json` config
- [ ] T3.5: Test pruner with sample data
- [ ] T3.6: Document pruning behavior

### F06: Context Inspection Commands
- [ ] T6.1: Create `~/.claude/skills/context-inspector/` directory
- [ ] T6.2: Create `SKILL.md`
- [ ] T6.3: Test `/context` command
- [ ] T6.4: Test `/context list` command
- [ ] T6.5: Test `/context detail` command
- [ ] T6.6: Test `/context trim` command

### F11 & F19: Pruning Configuration
- [ ] T11.1: Verify `pruning.json` has all tool rules
- [ ] T11.2: Test TTL-based pruning
- [ ] T11.3: Test soft-trim behavior
- [ ] T11.4: Test hard-clear behavior
- [ ] T11.5: Update CLAUDE.md with lifecycle docs

### Integration Testing
- [ ] T-INT.1: Run full session with all Phase 1 features
- [ ] T-INT.2: Verify no breaking changes
- [ ] T-INT.3: Measure context savings
- [ ] T-INT.4: Test edge cases (empty results, binary content)

---

## Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Decisions extracted pre-compact | 100% | Manual audit of 5 sessions |
| Context savings from pruning | 30-40% | `/context` before/after |
| `/context` accuracy | Within 20% | Compare to actual usage |
| No breaking changes | 0 regressions | Existing workflow tests |

---

## Rollback Plan

1. Remove memory flush hook from `settings.json`
2. Delete `~/.claude/lib/tool_result_pruner.py`
3. Delete `~/.claude/config/pruning.json`
4. Delete `~/.claude/skills/context-inspector/`
5. Revert CLAUDE.md changes

All changes are additive and can be removed independently.
