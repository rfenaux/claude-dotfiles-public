# CRM Card API Endpoints

API reference for programmatically managing CRM cards.

## Card Management API

Base URL: `https://api.hubapi.com`

### List Cards

```bash
GET /crm/v3/extensions/cards/{appId}
Authorization: Bearer {developer_api_key}
```

### Create Card

```bash
POST /crm/v3/extensions/cards/{appId}
Authorization: Bearer {developer_api_key}
Content-Type: application/json
```

**Request Body:**

```json
{
  "title": "Contact Insights",
  "fetch": {
    "targetUrl": "https://your-app.com/api/card-data",
    "objectTypes": [
      {
        "name": "contacts",
        "propertiesToSend": ["email", "hs_object_id", "firstname", "lastname"]
      },
      {
        "name": "companies",
        "propertiesToSend": ["name", "hs_object_id", "domain"]
      }
    ]
  },
  "display": {
    "properties": [
      {
        "name": "deal_count",
        "label": "Deal Count",
        "dataType": "NUMERIC"
      },
      {
        "name": "total_value",
        "label": "Total Value",
        "dataType": "CURRENCY",
        "currencyCode": "USD"
      },
      {
        "name": "status",
        "label": "Status",
        "dataType": "STATUS",
        "options": [
          { "type": "DEFAULT", "name": "Pending", "label": "Pending" },
          { "type": "SUCCESS", "name": "Active", "label": "Active" },
          { "type": "WARNING", "name": "At Risk", "label": "At Risk" },
          { "type": "DANGER", "name": "Churned", "label": "Churned" }
        ]
      }
    ]
  },
  "actions": {
    "baseUrls": ["https://your-app.com"],
    "primary": [
      {
        "type": "IFRAME",
        "width": 800,
        "height": 600,
        "uri": "/details/{hs_object_id}",
        "label": "View Details"
      }
    ],
    "secondary": [
      {
        "type": "ACTION_HOOK",
        "httpMethod": "POST",
        "uri": "/api/sync",
        "label": "Sync Data"
      }
    ]
  }
}
```

### Update Card

```bash
PATCH /crm/v3/extensions/cards/{appId}/{cardId}
Authorization: Bearer {developer_api_key}
Content-Type: application/json
```

### Delete Card

```bash
DELETE /crm/v3/extensions/cards/{appId}/{cardId}
Authorization: Bearer {developer_api_key}
```

---

## Data Types Reference

| dataType | Description | Additional Properties |
|----------|-------------|----------------------|
| `STRING` | Plain text | - |
| `NUMERIC` | Number | - |
| `CURRENCY` | Money value | `currencyCode` (USD, EUR, etc.) |
| `DATE` | Date value | - |
| `DATETIME` | Date + time | - |
| `EMAIL` | Email link | - |
| `PHONE` | Phone link | - |
| `LINK` | URL link | - |
| `STATUS` | Status badge | `options` array |
| `BOOLEAN` | Yes/No | - |

---

## Action Types

### IFRAME
Opens content in a modal/panel.

```json
{
  "type": "IFRAME",
  "uri": "/panel/{hs_object_id}",
  "label": "Open Panel",
  "width": 800,
  "height": 600
}
```

### ACTION_HOOK
Calls a webhook endpoint.

```json
{
  "type": "ACTION_HOOK",
  "httpMethod": "POST",
  "uri": "/api/action",
  "label": "Trigger Action",
  "confirmation": {
    "title": "Confirm Action",
    "body": "Are you sure you want to proceed?"
  }
}
```

### CONFIRMATION_ACTION_HOOK
Action with required confirmation.

```json
{
  "type": "CONFIRMATION_ACTION_HOOK",
  "httpMethod": "POST",
  "uri": "/api/delete",
  "label": "Delete",
  "confirmation": {
    "title": "Delete Record?",
    "body": "This action cannot be undone."
  }
}
```

---

## Fetch Response Format

When HubSpot calls your `fetch.targetUrl`, respond with:

```json
{
  "results": [
    {
      "objectId": 123,
      "title": "John Doe",
      "properties": [
        { "name": "deal_count", "value": "5" },
        { "name": "total_value", "value": "75000" },
        { "name": "status", "value": "Active" }
      ],
      "actions": [
        {
          "type": "IFRAME",
          "uri": "/details/123",
          "label": "View"
        }
      ]
    }
  ]
}
```

---

## Node.js SDK Examples

### Create Card

```javascript
const hubspot = require('@hubspot/api-client');

const client = new hubspot.Client({
  developerApiKey: process.env.DEVELOPER_API_KEY,
});

async function createCard(appId) {
  const cardDefinition = {
    title: 'Contact Insights',
    fetch: {
      targetUrl: 'https://my-app.com/api/card-data',
      objectTypes: [
        {
          name: 'contacts',
          propertiesToSend: ['email', 'hs_object_id'],
        },
      ],
    },
    display: {
      properties: [
        {
          name: 'score',
          label: 'Engagement Score',
          dataType: 'NUMERIC',
        },
      ],
    },
  };

  const result = await client.crm.extensions.cards.cardsApi.create(
    appId,
    cardDefinition
  );

  console.log('Card created:', result.id);
  return result;
}
```

### List Cards

```javascript
async function listCards(appId) {
  const cards = await client.crm.extensions.cards.cardsApi.getAll(appId);
  return cards.results;
}
```

### Update Card

```javascript
async function updateCard(appId, cardId, updates) {
  const result = await client.crm.extensions.cards.cardsApi.update(
    appId,
    cardId,
    updates
  );
  return result;
}
```

### Delete Card

```javascript
async function deleteCard(appId, cardId) {
  await client.crm.extensions.cards.cardsApi.archive(appId, cardId);
}
```

---

## CLI Commands

```bash
# Create project with card
hs project create --platform-version 2025.2

# Deploy to HubSpot
hs project deploy

# Watch for changes (dev mode)
hs project dev

# View function logs
hs logs functions --tail

# Add secrets
hs secrets add PRIVATE_APP_ACCESS_TOKEN

# Upload CMS serverless
hs upload <local> <remote>
```

---

## Object Types for Cards

| Object | API Name | Scopes Required |
|--------|----------|-----------------|
| Contacts | `contacts` | `crm.objects.contacts.read` |
| Companies | `companies` | `crm.objects.companies.read` |
| Deals | `deals` | `crm.objects.deals.read` |
| Tickets | `tickets` | `crm.objects.tickets.read` |
| Custom Objects | `{objectType}` | `crm.objects.custom.read` |

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| Card CRUD operations | 100/day per app |
| Fetch endpoint calls | 10s timeout |
| Card data refresh | Every page load |

---

## Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| 401 | Unauthorized | Check API key |
| 403 | Forbidden | Check app scopes |
| 404 | Not found | Verify app ID / card ID |
| 429 | Rate limited | Implement backoff |
| 500 | Server error | Check fetch URL response |
