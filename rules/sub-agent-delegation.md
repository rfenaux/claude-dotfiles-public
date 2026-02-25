# Sub-Agent Delegation

Agents explore and analyze. Main session edits.

## Read-Only Agent Pattern

| Agent Role | Allowed | Not Allowed |
|-----------|---------|-------------|
| Explore / research | Read, Grep, Glob, WebFetch | Edit, Write, Bash (destructive) |
| Bulk analysis | Read files, count patterns, categorize | Modify files, create files |
| Audit / review | Identify issues, report findings | Fix issues directly |

## Delegation Flow

```
1. Spawn agents with exploration scope
2. Agents return structured findings (file, issue, recommendation)
3. Main session reviews findings
4. Main session executes all edits centrally
```

## Why

Sub-agents choke on coordinated writes (observed: 2/13 files modified in 636-file audit).
Plan mode traps agents. Permission mismatches block edits. Context fragmentation causes wrong-file targeting.

## When Agents CAN Edit

- Single-file, self-contained changes (e.g., fix one config file)
- Explicitly instructed with specific file path + exact change
- No cross-file dependencies involved

## Output Contracts

Agent returns must use structured contracts (CDP v2.2) — not free-form prose:

| Task Type | Contract | Max Tokens |
|-----------|----------|------------|
| Document analysis | `DOCUMENT_ANALYSIS` | 1-2K |
| Research / exploration | `RESEARCH_OUTPUT` | 1-2K |
| Review / audit | `REVIEW_OUTPUT` | 1-2K |

Specify in HANDOFF.md: `Use: RESEARCH_OUTPUT contract`. Full specs in `CDP_PROTOCOL.md`.

## Recovery

If a sub-agent gets stuck mid-edit: abandon agent, bring findings to main session, execute edits there.
