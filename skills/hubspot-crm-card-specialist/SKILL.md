---
name: hubspot-crm-card-specialist
description: CRM cards, UI Extensions, and serverless functions for HubSpot Developer Platform
triggers:
  - CRM card
  - custom card
  - UI extension
  - serverless function HubSpot
  - hs project
  - app.functions
  - crm.record.tab
  - crm.record.sidebar
---

# HubSpot CRM Card Specialist

Technical skill for creating CRM cards (UI Extensions) and serverless functions on the HubSpot Developer Platform (2025.2).

## When to Invoke

- User wants to create a CRM card or custom card
- User needs serverless functions for HubSpot (Developer Projects OR CMS)
- User asks about UI Extensions, `@hubspot/ui-extensions`
- User needs boilerplate for HubSpot app development
- User asks about `hs project create`, `hsproject.json`, `app.json`
- User wants to call HubSpot API from a serverless function

## Reference Files

Read these for detailed examples and API reference:

| File | Content |
|------|---------|
| `references/ui-components.md` | All @hubspot/ui-extensions components |
| `references/serverless-patterns.md` | Function patterns and examples |
| `references/api-endpoints.md` | CRM card API endpoints |

## Quick Reference

### Project Creation

```bash
hs project create \
  --platform-version 2025.2 \
  --name "my-app" \
  --project-base app \
  --distribution private \
  --auth static
```

### Key Files

| File | Purpose |
|------|---------|
| `hsproject.json` | Project config, platform version |
| `src/app/app.json` | App manifest, scopes, extensions |
| `src/app/extensions/*.json` | Card definitions |
| `src/app/extensions/*.jsx` | React components |
| `src/app/app.functions/*.js` | Serverless functions |
| `src/app/app.functions/serverless.json` | Function endpoints |

### Card Locations

| Location | Placement |
|----------|-----------|
| `crm.record.tab` | Middle column tab |
| `crm.record.sidebar` | Right sidebar |

### Calling Serverless from UI

```jsx
const result = await hubspot.serverless('function-name', {
  propertiesToSend: ['hs_object_id', 'email'],
  parameters: { key: 'value' },
});
```

## Related

- Agent: `~/.claude/agents/hubspot-crm-card-specialist.md`
- HubSpot Specialist: `~/.claude/skills/hubspot-specialist/`
