---
name: hubspot-api-specialist
description: HubSpot API v3/v4, CLI commands, SDK patterns, authentication, and rate limits
triggers:
  - HubSpot API
  - hubspot api
  - API v3
  - API v4
  - hs CLI
  - hubspot cli
  - rate limit
  - batch operation
  - associations v4
  - @hubspot/api-client
  - private app token
  - OAuth HubSpot
---

# HubSpot API Specialist

Deep technical expertise for HubSpot API integration.

## When to Invoke

- User asks about API endpoints or methods
- User needs SDK help (`@hubspot/api-client`)
- User asks about rate limits or pagination
- User needs authentication guidance
- User asks about CLI commands (`hs auth`, `hs project`)
- User wants to debug API errors

## Reference Files

| File | Content |
|------|---------|
| `references/api-v3-reference.md` | CRM v3 endpoints, CRUD, search |
| `references/api-v4-reference.md` | Associations v4, Automation v4 |
| `references/cli-reference.md` | All `hs` CLI commands |
| `references/sdk-patterns.md` | Node.js SDK patterns |

## Quick Reference

### Authentication Priority

1. **Private App** - Server-side, scripts, serverless
2. **OAuth** - Public apps, multi-tenant
3. **Developer API Key** - App management only

### API Version Rule

- **v4**: Associations, Automation (workflows)
- **v3**: Everything else (CRM objects, search, properties)

### Rate Limits

| Tier | Req/Second | Req/Day |
|------|------------|---------|
| Free | 100 | 250K |
| Pro | 150 | 500K |
| Enterprise | 200 | 1M |

### Batch Limits

- Max 100 records per batch request
- Max 10 concurrent batch requests recommended

## Related

- Agent: `~/.claude/agents/hubspot-api-specialist.md`
- General: `~/.claude/skills/hubspot-specialist/`
- CRM Cards: `~/.claude/skills/hubspot-crm-card-specialist/`
