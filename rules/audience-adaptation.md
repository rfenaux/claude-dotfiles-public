# Audience Adaptation

When `[AUDIENCE: X]` appears in context from the audience-detector hook, adapt output accordingly.

## Profile Behaviors

| Profile | Depth | Jargon | Format | Visuals |
|---------|-------|--------|--------|---------|
| Executive | 1-2 paragraphs | Minimal (0.2) | Business impact first, bullet decisions, ROI | Charts, traffic-light tables |
| Technical | Full detail | Full (1.0) | Code snippets, file paths, trade-offs | Code blocks, architecture diagrams |
| Operational | Structured steps | Moderate (0.5) | Numbered steps, checklists, tips | Flowcharts, annotated screenshots |
| Non-Technical | Simple, clear | None (0.0) | Analogies, short sentences, examples | Simple diagrams, before/after |
| Mixed (default) | Balanced | Moderate (0.6) | Summary then detail, layered headings | Mix of tables and diagrams |

## Manual Override

User can force a profile mid-conversation:
- "for executives" / "for the board" -> Executive
- "explain technically" / "for developers" -> Technical
- "step by step" / "as a runbook" -> Operational
- "in simple terms" / "ELI5" -> Non-Technical

## Config

Profile definitions: `~/.claude/config/audience-profiles.json`
