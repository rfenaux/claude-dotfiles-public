# Deviation Handling

When work diverges from plan, use `/deviate` to handle gracefully:

| Type | Trigger | Action |
|------|---------|--------|
| `bug` | "found bug", "breaks" | Ask: fix now or spawn task? |
| `architectural` | "need to rethink" | Pause, escalate to user |
| `scope_creep` | "also need", "while here" | Park via `/focus park` |
| `blocker` | "can't proceed" | Log blocker, suggest switch |

**Commands:** `/deviate` (auto-detect) | `/deviate bug --fix` | `/deviate scope`

**Config:** `~/.claude/config/deviation-rules.json`
