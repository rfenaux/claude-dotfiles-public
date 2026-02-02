# HubSpot API v4 Reference

Reference for v4 APIs: Associations and Automation.

---

## Associations v4

### Why v4?

- Labeled associations (custom relationship types)
- Bulk operations
- Better performance
- Full association metadata

### Base URL

```
https://api.hubapi.com/crm/v4/associations
```

---

### Get Association Labels

Lists all association types between two object types.

```http
GET /crm/v4/associations/{fromObjectType}/{toObjectType}/labels
```

**Response:**
```json
{
  "results": [
    {
      "category": "HUBSPOT_DEFINED",
      "typeId": 1,
      "label": "Primary"
    },
    {
      "category": "USER_DEFINED",
      "typeId": 28,
      "label": "Billing contact"
    },
    {
      "category": "HUBSPOT_DEFINED",
      "typeId": 279,
      "label": null
    }
  ]
}
```

### Default Association Type IDs

| From → To | TypeId | Label | Inverse TypeId |
|-----------|--------|-------|----------------|
| Contact → Company | 1 | Primary | 2 |
| Contact → Company | 279 | Unlabeled | 280 |
| Contact → Deal | 4 | — | 3 |
| Contact → Ticket | 15 | — | 16 |
| Company → Deal | 6 | — | 5 |
| Company → Ticket | 25 | — | 26 |
| Deal → Line Item | 19 | — | 20 |
| Deal → Quote | 63 | — | 64 |
| Quote → Line Item | 67 | — | 68 |

---

### Create Custom Association Label

```http
POST /crm/v4/associations/{fromObjectType}/{toObjectType}/labels
Content-Type: application/json

{
  "name": "billing_contact",
  "label": "Billing Contact"
}
```

**Paired Labels (bidirectional):**
```json
{
  "name": "manager_employee",
  "label": "Manager",
  "inverseLabel": "Employee"
}
```

**Response:**
```json
{
  "results": [
    {
      "category": "USER_DEFINED",
      "typeId": 145,
      "label": "Employee"
    },
    {
      "category": "USER_DEFINED",
      "typeId": 144,
      "label": "Manager"
    }
  ]
}
```

**Limits:** Max 10 custom labels per object pairing.

---

### Associate Records (Single)

```http
PUT /crm/v4/objects/{objectType}/{objectId}/associations/{toObjectType}/{toObjectId}
Content-Type: application/json

[
  {
    "associationCategory": "HUBSPOT_DEFINED",
    "associationTypeId": 1
  }
]
```

**Response:**
```json
{
  "fromObjectTypeId": "0-1",
  "fromObjectId": 29851,
  "toObjectTypeId": "0-2",
  "toObjectId": 21678228008,
  "labels": ["Primary"]
}
```

---

### Associate Records (Batch)

```http
POST /crm/v4/associations/{fromObjectType}/{toObjectType}/batch/create
Content-Type: application/json

{
  "inputs": [
    {
      "from": { "id": "123" },
      "to": { "id": "456" },
      "types": [
        {
          "associationCategory": "HUBSPOT_DEFINED",
          "associationTypeId": 1
        }
      ]
    },
    {
      "from": { "id": "789" },
      "to": { "id": "012" },
      "types": [
        {
          "associationCategory": "USER_DEFINED",
          "associationTypeId": 28
        }
      ]
    }
  ]
}
```

---

### Get Associations for Record

```http
GET /crm/v4/objects/{objectType}/{objectId}/associations/{toObjectType}?limit=500
```

**Response:**
```json
{
  "results": [
    {
      "toObjectId": 456,
      "associationTypes": [
        {
          "category": "HUBSPOT_DEFINED",
          "typeId": 1,
          "label": "Primary"
        }
      ]
    }
  ],
  "paging": {
    "next": {
      "after": "cursor"
    }
  }
}
```

---

### Remove Association (Single)

```http
DELETE /crm/v4/objects/{objectType}/{objectId}/associations/{toObjectType}/{toObjectId}
```

### Remove Associations (Batch)

```http
POST /crm/v4/associations/{fromObjectType}/{toObjectType}/batch/archive
Content-Type: application/json

{
  "inputs": [
    {
      "from": { "id": "123" },
      "to": { "id": "456" }
    }
  ]
}
```

---

## Automation v4 (Workflows)

### Why v4?

- Programmatic workflow creation
- Full workflow structure (actions, branches, delays)
- Enrollment criteria management

### Base URL

```
https://api.hubapi.com/automation/v4
```

---

### Flow Types

| Type | Object | Use Case |
|------|--------|----------|
| `CONTACT_FLOW` | Contacts | Contact-based workflows |
| `PLATFORM_FLOW` | Any object | Deals, tickets, companies, custom objects |

---

### Create Workflow

```http
POST /automation/v4/flows
Content-Type: application/json

{
  "name": "New Contact Welcome",
  "type": "CONTACT_FLOW",
  "isEnabled": false,
  "enrollmentCriteria": {
    "listMembershipOperator": "ANY",
    "listIds": [123]
  },
  "actions": [
    {
      "type": "DELAY",
      "delayMillis": 86400000
    },
    {
      "type": "SINGLE_CONNECTION",
      "actionType": "SEND_EMAIL",
      "emailId": 456
    }
  ]
}
```

**Important:** Always create workflows with `isEnabled: false` first, then enable after testing.

---

### Enrollment Types

```json
{
  "enrollmentCriteria": {
    "type": "LIST_BASED",
    "listMembershipOperator": "ANY",
    "listIds": [123, 456]
  }
}
```

```json
{
  "enrollmentCriteria": {
    "type": "EVENT_BASED",
    "eventType": "FORM_SUBMISSION",
    "formId": "abc-123"
  }
}
```

```json
{
  "enrollmentCriteria": {
    "type": "MANUAL"
  }
}
```

---

### Action Types

#### Delay

```json
{
  "type": "DELAY",
  "delayMillis": 86400000
}
```

#### Send Email

```json
{
  "type": "SINGLE_CONNECTION",
  "actionType": "SEND_EMAIL",
  "emailId": 123
}
```

#### Set Property

```json
{
  "type": "SINGLE_CONNECTION",
  "actionType": "SET_PROPERTY",
  "propertyName": "lifecyclestage",
  "propertyValue": "lead"
}
```

#### Create Task

```json
{
  "type": "SINGLE_CONNECTION",
  "actionType": "CREATE_TASK",
  "taskProperties": {
    "subject": "Follow up",
    "notes": "Call to discuss requirements",
    "priority": "HIGH"
  }
}
```

#### Webhook

```json
{
  "type": "WEBHOOK",
  "httpMethod": "POST",
  "webhookUrl": "https://your-app.com/webhook",
  "propertiesToSend": ["email", "firstname"]
}
```

#### Custom Code

```json
{
  "type": "CUSTOM_CODE",
  "secretNames": ["API_KEY"],
  "code": "exports.main = async (event, callback) => { ... }"
}
```

---

### Branching

#### If/Then Branch

```json
{
  "type": "STATIC_BRANCH",
  "branches": [
    {
      "name": "Has email",
      "condition": {
        "filterGroups": [
          {
            "filters": [
              {
                "propertyName": "email",
                "operator": "HAS_PROPERTY"
              }
            ]
          }
        ]
      },
      "actions": [...]
    },
    {
      "name": "No email",
      "condition": null,
      "actions": [...]
    }
  ]
}
```

#### A/B Test Branch

```json
{
  "type": "AB_TEST_BRANCH",
  "splitPercentages": [50, 50],
  "branches": [
    {
      "name": "Version A",
      "actions": [...]
    },
    {
      "name": "Version B",
      "actions": [...]
    }
  ]
}
```

---

### List Workflows

```http
GET /automation/v4/flows?limit=100&after=cursor
```

### Get Workflow

```http
GET /automation/v4/flows/{flowId}
```

### Update Workflow

```http
PATCH /automation/v4/flows/{flowId}
Content-Type: application/json

{
  "name": "Updated Name",
  "isEnabled": true
}
```

### Delete Workflow

```http
DELETE /automation/v4/flows/{flowId}
```

---

### Enroll Contact Manually

```http
POST /automation/v4/flows/{flowId}/enrollments
Content-Type: application/json

{
  "inputs": [
    { "id": "123" },
    { "id": "456" }
  ]
}
```

---

## Scopes Required

| API | Scope |
|-----|-------|
| Associations v4 | `crm.objects.{object}.read`, `crm.objects.{object}.write` |
| Automation v4 | `automation` |
