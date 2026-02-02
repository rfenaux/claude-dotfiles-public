# HubSpot API Endpoints Reference

## CRM Object APIs (v3)

### Contacts
```
GET    /crm/v3/objects/contacts
POST   /crm/v3/objects/contacts
GET    /crm/v3/objects/contacts/{contactId}
PATCH  /crm/v3/objects/contacts/{contactId}
DELETE /crm/v3/objects/contacts/{contactId}
POST   /crm/v3/objects/contacts/batch/read
POST   /crm/v3/objects/contacts/batch/create
POST   /crm/v3/objects/contacts/batch/update
POST   /crm/v3/objects/contacts/batch/archive
POST   /crm/v3/objects/contacts/search
```

### Companies
```
GET    /crm/v3/objects/companies
POST   /crm/v3/objects/companies
GET    /crm/v3/objects/companies/{companyId}
PATCH  /crm/v3/objects/companies/{companyId}
DELETE /crm/v3/objects/companies/{companyId}
POST   /crm/v3/objects/companies/batch/read
POST   /crm/v3/objects/companies/batch/create
POST   /crm/v3/objects/companies/batch/update
POST   /crm/v3/objects/companies/batch/archive
POST   /crm/v3/objects/companies/search
```

### Deals
```
GET    /crm/v3/objects/deals
POST   /crm/v3/objects/deals
GET    /crm/v3/objects/deals/{dealId}
PATCH  /crm/v3/objects/deals/{dealId}
DELETE /crm/v3/objects/deals/{dealId}
POST   /crm/v3/objects/deals/batch/read
POST   /crm/v3/objects/deals/batch/create
POST   /crm/v3/objects/deals/batch/update
POST   /crm/v3/objects/deals/batch/archive
POST   /crm/v3/objects/deals/search
```

### Tickets
```
GET    /crm/v3/objects/tickets
POST   /crm/v3/objects/tickets
GET    /crm/v3/objects/tickets/{ticketId}
PATCH  /crm/v3/objects/tickets/{ticketId}
DELETE /crm/v3/objects/tickets/{ticketId}
POST   /crm/v3/objects/tickets/batch/read
POST   /crm/v3/objects/tickets/batch/create
POST   /crm/v3/objects/tickets/batch/update
POST   /crm/v3/objects/tickets/batch/archive
POST   /crm/v3/objects/tickets/search
```

### Products
```
GET    /crm/v3/objects/products
POST   /crm/v3/objects/products
GET    /crm/v3/objects/products/{productId}
PATCH  /crm/v3/objects/products/{productId}
DELETE /crm/v3/objects/products/{productId}
POST   /crm/v3/objects/products/batch/read
POST   /crm/v3/objects/products/batch/create
POST   /crm/v3/objects/products/batch/update
POST   /crm/v3/objects/products/batch/archive
POST   /crm/v3/objects/products/search
```

### Line Items
```
GET    /crm/v3/objects/line_items
POST   /crm/v3/objects/line_items
GET    /crm/v3/objects/line_items/{lineItemId}
PATCH  /crm/v3/objects/line_items/{lineItemId}
DELETE /crm/v3/objects/line_items/{lineItemId}
POST   /crm/v3/objects/line_items/batch/read
POST   /crm/v3/objects/line_items/batch/create
POST   /crm/v3/objects/line_items/batch/update
POST   /crm/v3/objects/line_items/batch/archive
```

### Quotes
```
GET    /crm/v3/objects/quotes
POST   /crm/v3/objects/quotes
GET    /crm/v3/objects/quotes/{quoteId}
PATCH  /crm/v3/objects/quotes/{quoteId}
DELETE /crm/v3/objects/quotes/{quoteId}
POST   /crm/v3/objects/quotes/batch/read
POST   /crm/v3/objects/quotes/batch/create
POST   /crm/v3/objects/quotes/batch/update
```

### Custom Objects
```
GET    /crm/v3/objects/{objectType}
POST   /crm/v3/objects/{objectType}
GET    /crm/v3/objects/{objectType}/{objectId}
PATCH  /crm/v3/objects/{objectType}/{objectId}
DELETE /crm/v3/objects/{objectType}/{objectId}
POST   /crm/v3/objects/{objectType}/batch/read
POST   /crm/v3/objects/{objectType}/batch/create
POST   /crm/v3/objects/{objectType}/batch/update
POST   /crm/v3/objects/{objectType}/batch/archive
POST   /crm/v3/objects/{objectType}/search
```

---

## Associations API

### v3 Associations
```
GET    /crm/v3/associations/{fromObjectType}/{toObjectType}/types
POST   /crm/v3/associations/{fromObjectType}/{toObjectType}/batch/create
POST   /crm/v3/associations/{fromObjectType}/{toObjectType}/batch/read
POST   /crm/v3/associations/{fromObjectType}/{toObjectType}/batch/archive
```

### v4 Associations (Enhanced)
```
POST   /crm/v4/associations/{fromObjectType}/{toObjectType}/batch/create
POST   /crm/v4/associations/{fromObjectType}/{toObjectType}/batch/read
GET    /crm/v4/associations/definitions
POST   /crm/v4/associations/definitions
DELETE /crm/v4/associations/definitions/{associationTypeId}
```

**v4 Improvements:**
- Association labels support
- Batch read: 1,000 IDs (vs 100 in v3)
- Batch create: 2,000 inputs
- Primary company management

---

## Properties API
```
GET    /crm/v3/properties/{objectType}
POST   /crm/v3/properties/{objectType}
GET    /crm/v3/properties/{objectType}/{propertyName}
PATCH  /crm/v3/properties/{objectType}/{propertyName}
DELETE /crm/v3/properties/{objectType}/{propertyName}
POST   /crm/v3/properties/{objectType}/batch/read
POST   /crm/v3/properties/{objectType}/batch/create
POST   /crm/v3/properties/{objectType}/batch/archive
GET    /crm/v3/properties/{objectType}/groups
POST   /crm/v3/properties/{objectType}/groups
```

---

## Pipelines API
```
GET    /crm/v3/pipelines/{objectType}
POST   /crm/v3/pipelines/{objectType}
GET    /crm/v3/pipelines/{objectType}/{pipelineId}
PATCH  /crm/v3/pipelines/{objectType}/{pipelineId}
DELETE /crm/v3/pipelines/{objectType}/{pipelineId}
GET    /crm/v3/pipelines/{objectType}/{pipelineId}/stages
POST   /crm/v3/pipelines/{objectType}/{pipelineId}/stages
```

---

## Owners API (v3)
```
GET    /crm/v3/owners
GET    /crm/v3/owners/{ownerId}
```

**Note:** v2 Owners API sunsets March 24, 2025

---

## Engagements API
```
GET    /crm/v3/objects/calls
POST   /crm/v3/objects/calls
GET    /crm/v3/objects/emails
POST   /crm/v3/objects/emails
GET    /crm/v3/objects/meetings
POST   /crm/v3/objects/meetings
GET    /crm/v3/objects/notes
POST   /crm/v3/objects/notes
GET    /crm/v3/objects/tasks
POST   /crm/v3/objects/tasks
```

---

## Lists API (v3)
```
GET    /crm/v3/lists
POST   /crm/v3/lists
GET    /crm/v3/lists/{listId}
PATCH  /crm/v3/lists/{listId}
DELETE /crm/v3/lists/{listId}
GET    /crm/v3/lists/{listId}/memberships
POST   /crm/v3/lists/{listId}/memberships/add
POST   /crm/v3/lists/{listId}/memberships/remove
POST   /crm/v3/lists/records/memberships/batch/read
```

**Note:** v1 Contact Lists API sunsets April 30, 2026

---

## Automation API

### v3 Workflows (Read-only, Legacy)
```
GET    /automation/v3/workflows
GET    /automation/v3/workflows/{workflowId}
```

### v4 Flows API (Full CRUD - Recommended)
```
GET    /automation/v4/flows                    # List all flows
POST   /automation/v4/flows                    # Create workflow
GET    /automation/v4/flows/{flowId}           # Get flow by ID
PUT    /automation/v4/flows/{flowId}           # Update flow
DELETE /automation/v4/flows/{flowId}           # Delete flow
POST   /automation/v4/flows/batch/read         # Batch read
GET    /automation/v4/flows/email-campaigns    # List email campaigns
POST   /automation/v4/workflow-id-mappings/batch/read  # v3 to v4 ID mapping
```

**Tier Requirement:** Professional or Enterprise (any Hub)

**Flow Types:**
- `CONTACT_FLOW`: Contact-based workflows
- `PLATFORM_FLOW`: Company, Deal, Ticket, Custom Object workflows

**Action Types:**
- `SINGLE_CONNECTION` - Standard actions (send email, update property, create record)
- `STATIC_BRANCH` - If/Then conditional branches
- `LIST_BRANCH` - Branch by list membership
- `AB_TEST_BRANCH` - A/B test split
- `CUSTOM_CODE` - Execute custom JavaScript/Python
- `WEBHOOK` - Call external webhook

**Enrollment Types:**
- `LIST_BASED` - Enroll based on filter criteria
- `EVENT_BASED` - Enroll on event trigger (form, page view, etc.)
- `MANUAL` - API/UI enrollment only

**See:** `automation-v4-api.md` for complete schema and examples

### v4 Custom Workflow Actions (App Developers)
```
GET    /automation/v4/actions/{appId}                     # List custom actions
POST   /automation/v4/actions/{appId}                     # Create custom action
GET    /automation/v4/actions/{appId}/{definitionId}      # Get action
PATCH  /automation/v4/actions/{appId}/{definitionId}      # Update action
DELETE /automation/v4/actions/{appId}/{definitionId}      # Delete action
PUT    /automation/v4/actions/{appId}/{definitionId}/functions/{functionType}
POST   /automation/v4/actions/callbacks/{callbackId}/complete  # Complete async action
```

**Function Types:** `PRE_ACTION_EXECUTION`, `POST_ACTION_EXECUTION`, `PRE_FETCH_OPTIONS`, `POST_FETCH_OPTIONS`

---

## Marketing APIs

### Marketing Emails
```
GET    /marketing/v3/emails
POST   /marketing/v3/emails
GET    /marketing/v3/emails/{emailId}
PATCH  /marketing/v3/emails/{emailId}
DELETE /marketing/v3/emails/{emailId}
POST   /marketing/v3/emails/{emailId}/send
```

### Forms
```
GET    /marketing/v3/forms
POST   /marketing/v3/forms
GET    /marketing/v3/forms/{formId}
PATCH  /marketing/v3/forms/{formId}
DELETE /marketing/v3/forms/{formId}
POST   /marketing/v3/forms/{formId}/submissions
```

### Campaigns
```
GET    /marketing/v3/campaigns
POST   /marketing/v3/campaigns
GET    /marketing/v3/campaigns/{campaignId}
PATCH  /marketing/v3/campaigns/{campaignId}
DELETE /marketing/v3/campaigns/{campaignId}
```

**Scope changes (July 2025):**
- Write operations: `marketing.campaigns.write`
- Read operations: `marketing.campaigns.read`

---

## Conversations API (Beta)
```
GET    /conversations/v3/conversations/threads
GET    /conversations/v3/conversations/threads/{threadId}
PATCH  /conversations/v3/conversations/threads/{threadId}
GET    /conversations/v3/conversations/threads/{threadId}/messages
POST   /conversations/v3/conversations/threads/{threadId}/messages
```

---

## Commerce API

### Payments (2025)
```
GET    /crm/v3/objects/payments
POST   /crm/v3/objects/payments
GET    /crm/v3/objects/payments/{paymentId}
PATCH  /crm/v3/objects/payments/{paymentId}
DELETE /crm/v3/objects/payments/{paymentId}
```

### Invoices
```
GET    /crm/v3/objects/invoices
POST   /crm/v3/objects/invoices
GET    /crm/v3/objects/invoices/{invoiceId}
PATCH  /crm/v3/objects/invoices/{invoiceId}
```

### Subscriptions
```
GET    /crm/v3/objects/subscriptions
POST   /crm/v3/objects/subscriptions
GET    /crm/v3/objects/subscriptions/{subscriptionId}
PATCH  /crm/v3/objects/subscriptions/{subscriptionId}
```

---

## Webhooks API

### v3 Webhooks
```
GET    /webhooks/v3/{appId}/settings
PUT    /webhooks/v3/{appId}/settings
GET    /webhooks/v3/{appId}/subscriptions
POST   /webhooks/v3/{appId}/subscriptions
DELETE /webhooks/v3/{appId}/subscriptions/{subscriptionId}
```

### v4 Webhooks Journal (Beta)
```
GET    /webhooks/v4/subscriptions
POST   /webhooks/v4/subscriptions
DELETE /webhooks/v4/subscriptions/{subscriptionId}
GET    /webhooks/v4/journal/{subscriptionId}
GET    /webhooks/v4/snapshots/{objectType}/{objectId}
```

**Rate Limit:** Snapshots - 10 req/sec per app

---

## Import/Export APIs
```
POST   /crm/v3/imports
GET    /crm/v3/imports/{importId}
POST   /crm/v3/exports
GET    /crm/v3/exports/{exportId}
GET    /crm/v3/exports/{exportId}/status
```

---

## Timeline Events API
```
GET    /crm/v3/timeline/events/{eventTemplateId}
POST   /crm/v3/timeline/events
POST   /crm/v3/timeline/events/batch/create
```

---

## Custom Events API
```
POST   /events/v3/send
POST   /events/v3/send/batch
```

**Rate Limit:** 1,250 req/sec (completion endpoint)

---

## GraphQL API
```
POST   https://api.hubspot.com/collector/graphql
```

**Rate Limits:**
- 500,000 points/min per account
- 30,000 points max per query
- 500 items per CRM query

---

## Account Info API
```
GET    /integrations/v1/me
GET    /account-info/v3/details
GET    /account-info/v3/api-usage/daily
```

---

## Data Model Limits API (2024)
```
GET    /crm/v3/schemas/limits
```

Check portal progress towards data limits.
