---
name: score
description: Check your Claude Code configuration score, tier, and breakdown
user_invocable: true
---

# /score - Configuration Score

Check your current configuration health score, tier ranking, and detailed breakdown.

## Instructions

When the user invokes `/score`, fetch the config score from the Command Center dashboard API and display a formatted summary.

1. Run: `curl -s http://localhost:8420/api/config-score`
2. Parse the JSON response
3. Display:
   - Total score / 300 with percentage
   - Current tier (Legendary/Expert/Advanced/Intermediate/Basic) and global percentile
   - Group breakdown (Core/Advanced/Standard) with scores
   - Any items with gaps (earned < max) as improvement opportunities

## Output Format

```
Configuration Score: 284/300 (95%) — Legendary (Top 0.1%)

Core (x3):     87/90  ████████████████████░ 97%
Advanced (x2): 94/100 ██████████████████░░░ 94%
Standard (x1): 97/110 █████████████████░░░░ 88%

Improvement opportunities:
  - Skills: 38/40+ (need 2 more for full points)
```

If the dashboard is unreachable, inform the user to check if the server is running (`launchctl start com.claude.rag-dashboard`).
