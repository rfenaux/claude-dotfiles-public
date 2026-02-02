---
name: enhance
description: Prompt enhancement system - rewrites and improves user prompts before execution for better clarity, specificity, and edge case coverage.
async:
  mode: never
  require_sync:
    - prompt approval
    - interactive workflow
---

# /enhance - Prompt Enhancement Skill

Rewrites and enhances user prompts before execution for better results.

## Commands

| Command | Action |
|---------|--------|
| `/enhance` | Show current status (on/off) |
| `/enhance on` | Enable prompt enhancement |
| `/enhance off` | Disable prompt enhancement |
| `/enhance <prompt>` | Enhance a specific prompt |

## How It Works

When **enabled**, every user prompt goes through enhancement:

1. **Analyze** - Identify gaps, ambiguities, missing context
2. **Enhance** - Add specificity, success criteria, edge cases
3. **Present** - Show enhanced version in fenced block
4. **Wait** - User approves, modifies, or requests original

### Enhanced Prompt Format

```
**Enhanced Prompt:**
[enhanced version with improvements]

**Changes:**
- [what was added/clarified]
```

## User Responses

| Response | Action |
|----------|--------|
| `go` / `yes` / `y` / `ok` | Execute enhanced prompt |
| `original` / `orig` | Execute original prompt as-is |
| Any other text | Treat as modification, re-enhance |

## Enhancement Patterns

When enhancing, I:
- Add missing context from project/conversation
- Specify output format when ambiguous
- Include edge cases to consider
- Add success criteria when missing
- Reference relevant files/decisions if known
- Clarify scope (what's in/out)

## Excluded from Enhancement

These bypass enhancement to prevent loops:
- Single-word approvals (`go`, `yes`, `y`, `ok`, `original`)
- Skill invocations starting with `/`
- Direct commands (`ls`, `cd`, file paths)
- Follow-up questions from Claude
- Messages under 10 characters

## State Persistence

Enhancement state persists for the session. Default: **ON**

Toggle inline: `"enhance off"` or `"enhance on"` anywhere in a message.

## Examples

**User:** "fix the bug"

**Enhanced Prompt:**
```
Fix the bug in [specific file/function based on recent context].

Success criteria:
- Bug no longer reproduces
- Existing tests pass
- No regressions introduced

Approach:
1. Identify root cause
2. Implement minimal fix
3. Verify with test
```

**User:** "add validation"

**Enhanced Prompt:**
```
Add input validation to [identified endpoint/function].

Validate:
- Required fields present
- Type correctness
- Length/range constraints
- Sanitize for security (XSS, injection)

Return clear error messages with field names.
```
