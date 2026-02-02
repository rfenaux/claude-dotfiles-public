---
name: hubspot-specialist
description: Comprehensive HubSpot platform and API specialist with up-to-date knowledge of all Hubs (Marketing, Sales, Service, Content, Operations, Commerce), API v3/v4, Breeze AI, and 2024-2025 product releases. Use when advising on HubSpot implementations, integrations, API development, feature recommendations, pricing/tier guidance, or troubleshooting HubSpot-related issues.
context: fork
agent: Explore
async:
  mode: auto
  prefer_background:
    - API research
    - documentation lookup
  require_sync:
    - implementation guidance
    - architecture decisions
---

# HubSpot Specialist Skill

A comprehensive knowledge base for HubSpot platform features, API capabilities, and implementation best practices. Updated through December 2025.

## When to Use This Skill

- HubSpot implementation planning and architecture
- API integration development (v3 and v4)
- Feature recommendations based on tier and use case
- Pricing and tier selection guidance
- Troubleshooting HubSpot configurations
- Breeze AI implementation and agent configuration
- Migration planning from other CRMs
- Custom object and data model design
- Workflow and automation design
- Reporting and analytics architecture

---

## PART 1: PLATFORM OVERVIEW

### Hub Ecosystem (2025)

| Hub | Purpose | Key Features |
|-----|---------|--------------|
| **Marketing Hub** | Attract and convert leads | Email, forms, automation, ABM, attribution |
| **Sales Hub** | Close deals efficiently | Pipelines, sequences, quotes, forecasting |
| **Service Hub** | Delight customers | Help desk, tickets, knowledge base, portal |
| **Content Hub** | Create and manage content | Website builder, blog, SEO, personalization |
| **Operations Hub** | Connect and clean data | Data sync, automation, datasets |
| **Commerce Hub** | Manage revenue | Payments, invoices, subscriptions, CPQ |
| **Data Hub** (Beta) | Unified data platform | External data, AI insights, data quality |

### Pricing Tiers

| Tier | Target | Key Differentiators |
|------|--------|---------------------|
| **Free** | Solopreneurs | Basic features, HubSpot branding, 10 custom properties |
| **Starter** | Small teams (1-10) | No branding, basic automation, $15-45/seat/mo |
| **Professional** | Growing teams (10-100) | Advanced automation, ABM, AI, $500-900/mo base |
| **Enterprise** | Large orgs (100+) | Predictive AI, custom objects, sandbox, $1,200-4,500/mo |

---

## PART 2: API REFERENCE

### API v3 (Current Standard)

**Authentication Methods:**
1. **Private Apps** (Recommended): Scoped tokens for internal integrations
2. **OAuth 2.0**: For marketplace apps and third-party integrations
3. **API Keys**: DEPRECATED - Do not use for new integrations

**Core CRM Endpoints:**
```
/crm/v3/objects/contacts
/crm/v3/objects/companies
/crm/v3/objects/deals
/crm/v3/objects/tickets
/crm/v3/objects/products
/crm/v3/objects/line_items
/crm/v3/objects/quotes
/crm/v3/objects/{customObjectType}
```

**Key Capabilities:**
- **Batch Operations**: Up to 100 records per request
- **Search API**: Filter, sort, paginate (10 req/sec limit)
- **Associations API**: Link objects together
- **Properties API**: Manage custom properties
- **Pipelines API**: Manage deal/ticket stages
- **Workflows API**: Read workflow configurations
- **Webhooks**: Event-driven notifications (5-sec timeout, 10 retries over 24h)

**Rate Limits (v3):**
| Type | Limit |
|------|-------|
| Standard API | 100 req/10 sec |
| OAuth Marketplace Apps | 110 req/10 sec |
| Search API | 10 req/sec |
| Batch endpoints | 10 req/sec |

### API v4 (New Features)

**v4 Associations API:**
```
/crm/v4/associations/{fromObjectType}/{toObjectType}/batch/create
/crm/v4/associations/{fromObjectType}/{toObjectType}/batch/read
```

Key Improvements:
- **Association Labels**: Custom relationship types (e.g., "Decision Maker")
- **Batch Limits**: 1,000 read / 2,000 create (vs 100 in v3)
- **Primary Company**: Set/change primary company associations
- **Custom Objects**: Enhanced support

**v4 Automation API (Beta):**
```
/automation/v4/flows/batch/read
```

Key Improvements:
- Multi-object workflows (deals, tickets, not just contacts)
- Full action details (no more `UNSUPPORTED_ACTION`)
- Update existing workflows via API
- Migration endpoints (v3 workflowId → v4 flowId)

**Webhooks v4 Journal API (Beta):**
- Pull-based event model (vs push)
- Poll for changes on your schedule
- 3-day historical retrieval
- Granular subscriptions (per-portal, per-object, per-property)
- Snapshots endpoint for current state

**Date-Based Versioning (2025):**
- New format: `YYYY-MM` (e.g., `2025-09`)
- Beta for: CRM objects, properties, associations, account info
- v3 continues to be supported during rollout

### GraphQL API

**Endpoint:** `https://api.hubspot.com/collector/graphql`

**Rate Limits:**
- 500,000 points/min per account
- 30,000 points max per query
- 500 items per CRM query

**Use Cases:**
- Data-driven CMS pages
- Complex nested data retrieval
- Reducing multiple API calls
- Custom dashboards

### API Deprecation Schedule

| API | Sunset Date | Migration Path |
|-----|-------------|----------------|
| v2 Owners API | March 24, 2025 | → v3 Owners API |
| v1 Contact Lists API | April 30, 2026 | → v3 Lists API |
| Marketing Email API v1 | November 1, 2025 | → v3 |

---

## PART 3: BREEZE AI (2024-2025)

### Breeze Components

**1. Breeze Copilot** (All tiers with limits)
- Chat-based AI companion
- Content generation
- CRM data interaction
- Company research (Pro+)
- Ticket summarization (Pro+)

**2. Breeze Agents** (Professional+)
| Agent | Function |
|-------|----------|
| **Content Agent** | Generate blogs, landing pages, case studies |
| **Prospecting Agent** | Research accounts, personalize outreach |
| **Customer Agent** | 24/7 support, KB-powered responses (Enterprise) |
| **Social Media Agent** | Analyze trends, create posts |
| **Data Agent** | Enrich and clean data |

**3. Breeze Intelligence** (Professional+)
- 200M+ buyer/company profiles
- Buyer intent identification
- Form shortening for conversion

**4. Breeze Marketplace & Studio** (2025)
- Pre-built agent discovery
- No-code agent customization
- Custom assistant creation
- 33+ agents available (15 GA + 18 beta)

---

## PART 4: 2024-2025 MAJOR RELEASES

### INBOUND 2024 (September)
- Breeze AI platform launch
- 4 initial Breeze Agents
- 80+ AI features
- Centralized AI settings

### Spring 2024
- New Service Hub redesign
- Content Hub launch (formerly CMS Hub)
- 100+ product updates

### Spring 2025
- Sales Workspace
- Customer Success Workspace
- Help Desk Workspace
- Enhanced Breeze Agents
- Multi-account management

### INBOUND 2025 (September)
- Data Hub (Beta)
- Breeze Marketplace & Studio
- 18 new Breeze Agents
- AI-powered CPQ
- 200+ product updates

### Commerce Hub Evolution
- Native payments, invoicing, subscriptions
- QuickBooks Online integration
- Tax calculation
- Payment schedules
- AI-powered CPQ (2025)

---

## PART 5: FEATURE MATRIX BY HUB

### Marketing Hub

| Feature | Free | Starter | Pro | Enterprise |
|---------|------|---------|-----|------------|
| Email (branded) | Yes | No brand | Advanced | Advanced |
| Forms | Basic | Standard | Smart forms | Smart forms |
| Workflows | No | Simple | Advanced | Advanced |
| Lead scoring | No | No | 25 models | Predictive AI |
| ABM | No | No | Yes | Yes |
| Attribution | No | No | Contact only | Multi-touch |
| Custom objects | No | No | No | Yes |

### Sales Hub

| Feature | Free | Starter | Pro | Enterprise |
|---------|------|---------|-----|------------|
| Pipelines | 1 | Multiple | Multiple | Multiple |
| Sequences | No | Basic | Advanced | Advanced |
| Quotes | No | Yes | Yes | AI-assisted |
| Forecasting | No | No | Yes | Advanced |
| Conversation intel | No | No | No | Yes |
| Predictive scoring | No | No | No | Yes |

### Service Hub

| Feature | Free | Starter | Pro | Enterprise |
|---------|------|---------|-----|------------|
| Tickets | Basic | Standard | Advanced | AI-powered |
| Knowledge base | No | No | Yes | Yes |
| Customer portal | No | No | Yes | Yes |
| SLAs | No | No | Yes | Advanced |
| Customer Agent (AI) | No | No | No | Yes |

### Operations Hub

| Feature | Free | Starter | Pro | Enterprise |
|---------|------|---------|-----|------------|
| Data sync | Yes | Enhanced | Real-time | Real-time |
| Custom code | No | No | Yes | Yes |
| Data quality automation | No | No | Yes | Yes |
| Datasets | No | No | No | Yes |
| Snowflake Data Share | No | No | No | Yes |

---

## PART 6: IMPLEMENTATION PATTERNS

### Integration Architecture

**Sync Patterns:**
1. **Real-time**: Webhooks + immediate processing
2. **Near-real-time**: Polling every 1-5 minutes
3. **Batch**: Daily/hourly bulk syncs
4. **Event-driven**: Webhooks v4 Journal (enterprise scale)

**Error Handling:**
```javascript
// Recommended pattern
try {
  const response = await hubspotClient.crm.contacts.basicApi.create(contact);
} catch (error) {
  if (error.code === 429) {
    // Rate limited - respect Retry-After header
    await sleep(error.headers['retry-after'] * 1000);
    return retry(request);
  }
  if (error.code === 477) {
    // Portal migration - retry after specified time
    return scheduleRetry(error.context);
  }
  throw error;
}
```

**Batch Operations Best Practices:**
1. Use batch endpoints for 3+ records
2. Include `objectWriteTraceId` for debugging
3. Handle partial failures gracefully
4. Respect rate limits (10 req/sec for batch)

### Custom Object Design

**When to Use:**
- Industry-specific entities (Projects, Listings, Courses)
- Many-to-many relationships
- Complex data not fitting standard objects

**Limits:**
- Up to 10 unique value properties per custom object
- Enterprise tier required
- Association limits apply

**Best Practices:**
1. Map relationships before creation
2. Use association labels for clarity
3. Consider reporting implications
4. Plan for data migration

### Workflow Architecture

**Enrollment Types:**
- **Event-based**: Trigger on specific actions
- **List-based**: Trigger on list membership

**Performance Considerations:**
1. Use delays to prevent overwhelming integrations
2. Implement proper error handling in custom code
3. Monitor enrollment rate anomalies (AI feature)
4. Use branch logic efficiently

---

## PART 7: TROUBLESHOOTING

### Common API Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| 429 errors | Rate limiting | Implement exponential backoff |
| 477 errors | Portal migration | Retry after specified time |
| Association failures | Label mismatch | Verify label IDs exist |
| Search not returning | Indexing delay | Wait 30 sec after creates |
| Webhook timeouts | Slow processing | Respond in <5 seconds, queue work |

### Data Quality Issues

1. **Duplicate contacts**: Use Operations Hub deduplication
2. **Property formatting**: Implement data quality automation
3. **Sync conflicts**: Define SSOT, use conflict resolution rules
4. **Missing associations**: Audit and bulk-update via API

### Performance Optimization

1. **Reduce API calls**: Use batch endpoints and GraphQL
2. **Cache frequently accessed data**: Properties, owners, pipelines
3. **Use webhooks**: Instead of polling for changes
4. **Optimize queries**: Use indexed properties for search

---

## PART 8: QUICK REFERENCE

### SDKs Available
- Node.js (v9.0.0+ for v4 APIs)
- Python
- Ruby
- PHP

### Key Documentation URLs
- API Reference: developers.hubspot.com/docs/api
- Changelog: developers.hubspot.com/changelog
- Knowledge Base: knowledge.hubspot.com
- Community: community.hubspot.com

### Scopes Reference

| Scope | Access |
|-------|--------|
| `crm.objects.contacts.read/write` | Contact records |
| `crm.objects.deals.read/write` | Deal records |
| `crm.objects.custom.read/write` | Custom objects |
| `automation` | Workflow APIs |
| `marketing.campaigns.read/write` | Campaign management |
| `oauth` | OAuth flows |

### Contact Limits by Tier

| Tier | Marketing Contacts |
|------|-------------------|
| Free | 1,000 |
| Starter | 1,000 (included), up to 1M |
| Professional | 2,000 (included), up to 10M |
| Enterprise | 10,000 (included), up to 50M |

---

## Usage Guidelines

1. **Always verify tier availability** before recommending features
2. **Check deprecation dates** for API version recommendations
3. **Consider rate limits** in integration designs
4. **Recommend v4 APIs** for new integrations where available
5. **Suggest Breeze AI** features for Professional+ customers
6. **Validate custom object needs** (Enterprise only)

---

*Last Updated: December 2025*
*Sources: developers.hubspot.com, knowledge.hubspot.com, HubSpot product releases*
