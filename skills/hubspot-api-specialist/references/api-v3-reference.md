# HubSpot API v3 Reference

Complete reference for CRM API v3 endpoints.

## Base URL

```
https://api.hubapi.com
```

## Authentication Header

```
Authorization: Bearer {access_token}
```

---

## CRM Objects

### Standard Objects

| Object | Endpoint Base |
|--------|---------------|
| Contacts | `/crm/v3/objects/contacts` |
| Companies | `/crm/v3/objects/companies` |
| Deals | `/crm/v3/objects/deals` |
| Tickets | `/crm/v3/objects/tickets` |
| Products | `/crm/v3/objects/products` |
| Line Items | `/crm/v3/objects/line_items` |
| Quotes | `/crm/v3/objects/quotes` |
| Calls | `/crm/v3/objects/calls` |
| Emails | `/crm/v3/objects/emails` |
| Meetings | `/crm/v3/objects/meetings` |
| Notes | `/crm/v3/objects/notes` |
| Tasks | `/crm/v3/objects/tasks` |

### Custom Objects

```
/crm/v3/objects/{objectType}
```

Where `{objectType}` is the custom object's `objectTypeId` or `fullyQualifiedName`.

---

## CRUD Operations

### Create

```http
POST /crm/v3/objects/{objectType}
Content-Type: application/json

{
  "properties": {
    "email": "test@example.com",
    "firstname": "John",
    "lastname": "Doe"
  },
  "associations": [
    {
      "to": { "id": 123 },
      "types": [
        {
          "associationCategory": "HUBSPOT_DEFINED",
          "associationTypeId": 1
        }
      ]
    }
  ]
}
```

### Read (Single)

```http
GET /crm/v3/objects/{objectType}/{objectId}?properties=email,firstname&associations=deals
```

**Query Parameters:**
- `properties` - Comma-separated property names
- `propertiesWithHistory` - Include property history
- `associations` - Comma-separated object types

### Read (List)

```http
GET /crm/v3/objects/{objectType}?limit=100&after=cursor&properties=email
```

**Query Parameters:**
- `limit` - Max 100
- `after` - Pagination cursor
- `properties` - Properties to return

### Update

```http
PATCH /crm/v3/objects/{objectType}/{objectId}
Content-Type: application/json

{
  "properties": {
    "firstname": "Jane"
  }
}
```

### Delete (Archive)

```http
DELETE /crm/v3/objects/{objectType}/{objectId}
```

---

## Batch Operations

### Batch Create

```http
POST /crm/v3/objects/{objectType}/batch/create
Content-Type: application/json

{
  "inputs": [
    {
      "properties": {
        "email": "contact1@example.com",
        "firstname": "John"
      }
    },
    {
      "properties": {
        "email": "contact2@example.com",
        "firstname": "Jane"
      }
    }
  ]
}
```

### Batch Read

```http
POST /crm/v3/objects/{objectType}/batch/read
Content-Type: application/json

{
  "inputs": [
    { "id": "123" },
    { "id": "456" }
  ],
  "properties": ["email", "firstname"]
}
```

### Batch Update

```http
POST /crm/v3/objects/{objectType}/batch/update
Content-Type: application/json

{
  "inputs": [
    {
      "id": "123",
      "properties": {
        "firstname": "John Updated"
      }
    }
  ]
}
```

### Batch Upsert

```http
POST /crm/v3/objects/{objectType}/batch/upsert
Content-Type: application/json

{
  "inputs": [
    {
      "idProperty": "email",
      "id": "test@example.com",
      "properties": {
        "email": "test@example.com",
        "firstname": "John"
      }
    }
  ]
}
```

### Batch Archive

```http
POST /crm/v3/objects/{objectType}/batch/archive
Content-Type: application/json

{
  "inputs": [
    { "id": "123" },
    { "id": "456" }
  ]
}
```

---

## Search API

```http
POST /crm/v3/objects/{objectType}/search
Content-Type: application/json

{
  "filterGroups": [
    {
      "filters": [
        {
          "propertyName": "email",
          "operator": "CONTAINS_TOKEN",
          "value": "@company.com"
        }
      ]
    }
  ],
  "sorts": [
    {
      "propertyName": "createdate",
      "direction": "DESCENDING"
    }
  ],
  "properties": ["email", "firstname", "lastname"],
  "limit": 100,
  "after": 0
}
```

### Search Operators

| Operator | Description | Example Value |
|----------|-------------|---------------|
| `EQ` | Equals | `"value"` |
| `NEQ` | Not equals | `"value"` |
| `LT` | Less than | `"100"` |
| `LTE` | Less than or equal | `"100"` |
| `GT` | Greater than | `"100"` |
| `GTE` | Greater than or equal | `"100"` |
| `CONTAINS_TOKEN` | Contains word | `"john"` |
| `NOT_CONTAINS_TOKEN` | Doesn't contain | `"spam"` |
| `HAS_PROPERTY` | Has any value | `null` |
| `NOT_HAS_PROPERTY` | Is empty | `null` |
| `IN` | In list | `["a", "b", "c"]` |
| `NOT_IN` | Not in list | `["a", "b"]` |
| `BETWEEN` | Between range | `["2024-01-01", "2024-12-31"]` |

### Search Limits

- Max 10,000 results total
- Max 4 requests/second
- Max 3 filterGroups
- Max 6 filters per filterGroup

---

## Properties API

### List Properties

```http
GET /crm/v3/properties/{objectType}
```

### Get Property

```http
GET /crm/v3/properties/{objectType}/{propertyName}
```

### Create Property

```http
POST /crm/v3/properties/{objectType}
Content-Type: application/json

{
  "name": "my_custom_property",
  "label": "My Custom Property",
  "type": "string",
  "fieldType": "text",
  "groupName": "contactinformation",
  "description": "A custom property"
}
```

**Property Types:**
- `string`, `number`, `date`, `datetime`, `enumeration`, `bool`

**Field Types:**
- `text`, `textarea`, `number`, `date`, `file`, `checkbox`, `select`, `radio`, `booleancheckbox`, `calculation_equation`

### Update Property

```http
PATCH /crm/v3/properties/{objectType}/{propertyName}
Content-Type: application/json

{
  "label": "Updated Label"
}
```

---

## Pipelines API

### List Pipelines

```http
GET /crm/v3/pipelines/{objectType}
```

### Get Pipeline

```http
GET /crm/v3/pipelines/{objectType}/{pipelineId}
```

### Create Pipeline

```http
POST /crm/v3/pipelines/{objectType}
Content-Type: application/json

{
  "label": "My Pipeline",
  "displayOrder": 0,
  "stages": [
    {
      "label": "Stage 1",
      "displayOrder": 0,
      "metadata": {
        "probability": "0.2"
      }
    },
    {
      "label": "Stage 2",
      "displayOrder": 1,
      "metadata": {
        "probability": "0.5"
      }
    }
  ]
}
```

---

## Owners API

### List Owners

```http
GET /crm/v3/owners?limit=100&after=cursor
```

### Get Owner

```http
GET /crm/v3/owners/{ownerId}
```

---

## Response Format

### Success Response

```json
{
  "id": "123",
  "properties": {
    "email": "test@example.com",
    "firstname": "John",
    "hs_object_id": "123",
    "createdate": "2024-01-15T10:30:00.000Z"
  },
  "createdAt": "2024-01-15T10:30:00.000Z",
  "updatedAt": "2024-01-15T10:30:00.000Z",
  "archived": false
}
```

### Paginated Response

```json
{
  "results": [...],
  "paging": {
    "next": {
      "after": "cursor_string",
      "link": "https://api.hubapi.com/..."
    }
  }
}
```

### Error Response

```json
{
  "status": "error",
  "message": "Property values were not valid",
  "correlationId": "abc-123-def",
  "category": "VALIDATION_ERROR",
  "errors": [
    {
      "message": "Property 'email' is not valid",
      "context": {
        "propertyName": "email"
      }
    }
  ]
}
```

---

## Scopes Required

| Object | Read Scope | Write Scope |
|--------|------------|-------------|
| Contacts | `crm.objects.contacts.read` | `crm.objects.contacts.write` |
| Companies | `crm.objects.companies.read` | `crm.objects.companies.write` |
| Deals | `crm.objects.deals.read` | `crm.objects.deals.write` |
| Tickets | `crm.objects.tickets.read` | `crm.objects.tickets.write` |
| Products | `e-commerce` | `e-commerce` |
| Line Items | `crm.objects.line_items.read` | `crm.objects.line_items.write` |
| Quotes | `crm.objects.quotes.read` | `crm.objects.quotes.write` |
| Custom Objects | `crm.objects.custom.read` | `crm.objects.custom.write` |
| Properties | `crm.schemas.{object}.read` | `crm.schemas.{object}.write` |
