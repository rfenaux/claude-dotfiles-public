# HubSpot Automation API v4 - Complete Technical Documentation

## Table of Contents
1. [Overview](#1-overview)
2. [Prerequisites & Authentication](#2-prerequisites--authentication)
3. [Workflows v4 API](#3-workflows-v4-api)
4. [Workflow Types: CONTACT_FLOW vs PLATFORM_FLOW](#4-workflow-types-contact_flow-vs-platform_flow)
5. [Workflow Triggers & Enrollment Criteria](#5-workflow-triggers--enrollment-criteria)
6. [Native Action Types](#6-native-action-types)
7. [Branching & Multi-Step Workflows](#7-branching--multi-step-workflows)
8. [Custom Workflow Actions](#8-custom-workflow-actions)
9. [Custom Code Actions](#9-custom-code-actions)
10. [Functions (Serverless)](#10-functions-serverless)
11. [Asynchronous Execution & Callbacks](#11-asynchronous-execution--callbacks)
12. [API Reference](#12-api-reference)
13. [Complete Examples](#13-complete-examples)
14. [Best Practices](#14-best-practices)
15. [API Rate Limits](#15-api-rate-limits)
16. [Troubleshooting](#16-troubleshooting)

---

## 1. Overview

The HubSpot Automation API v4 enables you to programmatically create, manage, and extend workflows. It supports three main capabilities:

- **Workflows v4 API**: Create, fetch, update, and delete complete workflows
- **Custom Workflow Actions**: Build reusable actions that integrate external services
- **Custom Code Actions**: Write JavaScript (Node.js) or Python code directly within workflows

**Required Scope:** `automation`

**Tier Requirement:** Professional or Enterprise (any Hub)

---

## 2. Prerequisites & Authentication

### 2.1 Required Setup

1. **Create a Developer Account** at developers.hubspot.com
2. **Create a HubSpot App** (app logo becomes the action icon)
3. **Configure Authentication**:
   - **Marketplace Apps**: Use OAuth tokens
   - **Single-Account Apps**: Use static auth tokens (private app access tokens)

### 2.2 Sensitive Data Scopes

For workflows accessing sensitive data properties:

| Scope | Purpose |
|-------|---------|
| `crm.objects.contacts.sensitive.read` | Read contact workflows with sensitive data |
| `crm.objects.contacts.sensitive.write` | Create/delete contact workflows with sensitive data |
| `crm.objects.companies.sensitive.read/write` | Company workflows |
| `crm.objects.deals.sensitive.read/write` | Deal workflows |
| `crm.objects.custom.sensitive.read/write` | Custom object workflows |

---

## 3. Workflows v4 API

### 3.1 Workflow Structure

A complete workflow specification includes:

```json
{
  "id": "585051946",
  "isEnabled": true,
  "flowType": "WORKFLOW",
  "revisionId": "7",
  "name": "My Workflow Name",
  "type": "CONTACT_FLOW",
  "objectTypeId": "0-1",
  "startActionId": "1",
  "nextAvailableActionId": "4",
  "actions": [...],
  "enrollmentCriteria": {...},
  "timeWindows": [],
  "blockedDates": [],
  "suppressionListIds": [],
  "canEnrollFromSalesforce": false
}
```

### 3.2 API Endpoints

| Operation | Method | Endpoint |
|-----------|--------|----------|
| Fetch all workflows | GET | `/automation/v4/flows` |
| Fetch workflow by ID | GET | `/automation/v4/flows/{flowId}` |
| Fetch workflows in bulk | POST | `/automation/v4/flows/batch/read` |
| Create workflow | POST | `/automation/v4/flows` |
| Update workflow | PUT | `/automation/v4/flows/{flowId}` |
| Delete workflow | DELETE | `/automation/v4/flows/{flowId}` |

### 3.3 Bulk Fetch Request

```json
{
  "inputs": [
    { "flowId": "619727002", "type": "FLOW_ID" },
    { "flowId": "617969780", "type": "FLOW_ID" }
  ]
}
```

---

## 4. Workflow Types: CONTACT_FLOW vs PLATFORM_FLOW

### 4.1 Type Definitions

| Type | Description | Usage |
|------|-------------|-------|
| `CONTACT_FLOW` | Contact-based workflows | Use for workflows that enroll contacts |
| `PLATFORM_FLOW` | All other workflow types | Use for deals, companies, tickets, custom objects |

### 4.2 Object Type IDs Reference

| Object | Object Type ID |
|--------|---------------|
| Contacts | `0-1` |
| Companies | `0-2` |
| Deals | `0-3` |
| Tickets | `0-5` |
| Line Items | `0-8` |
| Custom Objects | Use custom object ID |

### 4.3 CONTACT_FLOW Schema (Complete)

```json
{
  "type": "CONTACT_FLOW",
  "objectTypeId": "0-1",
  "canEnrollFromSalesforce": false,
  "isEnabled": true,
  "flowType": "WORKFLOW",
  "name": "Workflow Name",
  "description": "Workflow description",
  "uuid": "<optional-uuid>",
  "startActionId": "1",
  "actions": [],
  "timeWindows": [],
  "blockedDates": [],
  "customProperties": {},
  "dataSources": [],
  "suppressionListIds": [],
  "enrollmentCriteria": {},
  "enrollmentSchedule": {},
  "goalFilterBranch": {},
  "eventAnchor": {},
  "unEnrollmentSetting": {}
}
```

#### CONTACT_FLOW Required Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | enum | Yes | Must be `"CONTACT_FLOW"` |
| `objectTypeId` | string | Yes | CRM object type ID (e.g., `"0-1"` for contacts) |
| `canEnrollFromSalesforce` | boolean | Yes | Whether Salesforce can trigger enrollment |
| `isEnabled` | boolean | Yes | Workflow active status |
| `flowType` | enum | Yes | Must be `"WORKFLOW"` |
| `actions` | array | Yes | List of workflow actions |
| `timeWindows` | array | Yes | Execution time windows (can be empty `[]`) |
| `blockedDates` | array | Yes | Dates when workflow won't execute (can be empty `[]`) |
| `customProperties` | object | Yes | Custom metadata (can be empty `{}`) |
| `dataSources` | array | Yes | Data source configurations (can be empty `[]`) |
| `suppressionListIds` | integer[] | Yes | Lists to suppress from enrollment (can be empty `[]`) |

### 4.4 PLATFORM_FLOW Schema (Complete)

```json
{
  "type": "PLATFORM_FLOW",
  "objectTypeId": "0-3",
  "isEnabled": true,
  "flowType": "WORKFLOW",
  "name": "Workflow Name",
  "description": "Workflow description",
  "uuid": "<optional-uuid>",
  "startActionId": "1",
  "actions": [],
  "customProperties": {},
  "dataSources": [],
  "enrollmentCriteria": {}
}
```

#### PLATFORM_FLOW Required Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | enum | Yes | Must be `"PLATFORM_FLOW"` |
| `objectTypeId` | string | Yes | CRM object type ID |
| `isEnabled` | boolean | Yes | Workflow active status |
| `flowType` | enum | Yes | Must be `"WORKFLOW"` |
| `actions` | array | Yes | List of workflow actions |
| `customProperties` | object | Yes | Custom metadata (can be empty `{}`) |
| `dataSources` | array | Yes | Data source configurations (can be empty `[]`) |

---

## 5. Workflow Triggers & Enrollment Criteria

The `enrollmentCriteria` property defines how objects enter a workflow.

### 5.1 Enrollment Types

| Type | Description |
|------|-------------|
| `EVENT_BASED` | Enrolls objects when specific events occur |
| `LIST_BASED` | Enrolls objects when filter criteria are met |

### 5.2 Event-Based Enrollment

Triggered by user actions like form submissions, email opens, etc.

```json
{
  "enrollmentCriteria": {
    "type": "EVENT_BASED",
    "shouldReEnroll": true,
    "eventFilterBranches": [
      {
        "filterBranches": [],
        "filters": [],
        "eventTypeId": "4-1639801",
        "operator": "HAS_COMPLETED",
        "filterBranchType": "UNIFIED_EVENTS",
        "filterBranchOperator": "AND"
      }
    ],
    "listMembershipFilterBranches": []
  }
}
```

### 5.3 Event Type IDs Reference

| Event | Event Type ID |
|-------|---------------|
| Form submission | `4-1639801` |
| Form view | `4-1639797` |
| Form interaction | `4-1639799` |
| Email open | `4-666440` |
| Email click | `4-666288` |
| Email reply | `4-665538` |
| Email delivery | `4-665536` |
| Ad interaction | `4-1553675` |
| Marketing event registration | `4-68559` |
| Marketing event cancellation | `4-69072` |
| Call start | `4-1733817` |
| Call end | `4-1741072` |
| SMS shortlink click | `4-1722276` |
| CTA view | `4-1555804` |
| CTA click | `4-1555805` |
| Media play on webpage | `4-675783` |

### 5.4 Filter-Based (LIST_BASED) Enrollment

Enrolls objects based on property values:

```json
{
  "enrollmentCriteria": {
    "type": "LIST_BASED",
    "shouldReEnroll": false,
    "unEnrollObjectsNotMeetingCriteria": false,
    "listFilterBranch": {
      "filterBranchOperator": "OR",
      "filterBranchType": "OR",
      "filterBranches": [
        {
          "filterBranchType": "AND",
          "filterBranchOperator": "AND",
          "filterBranches": [],
          "filters": [
            {
              "property": "city",
              "operation": {
                "operator": "IS_EQUAL_TO",
                "includeObjectsWithNoValueSet": false,
                "values": ["Dublin"],
                "operationType": "MULTISTRING"
              },
              "filterType": "PROPERTY"
            }
          ]
        }
      ],
      "filters": []
    },
    "reEnrollmentTriggersFilterBranches": []
  }
}
```

### 5.5 Filter Types

| Filter Type | Description |
|-------------|-------------|
| `PROPERTY` | Filter by property value |
| `ASSOCIATION` | Filter by association |
| `PAGE_VIEW` | Filter by page view |
| `CTA` | Filter by CTA interaction |
| `EVENT` | Generic event filter |
| `FORM_SUBMISSION` | Filter by form submission |
| `FORM_SUBMISSION_ON_PAGE` | Filter by form on specific page |
| `INTEGRATION_EVENT` | Filter by integration event |
| `EMAIL_SUBSCRIPTION` | Filter by email subscription |
| `COMMUNICATION_SUBSCRIPTION` | Filter by communication preferences |
| `CAMPAIGN_INFLUENCED` | Filter by campaign influence |
| `SURVEY_MONKEY` | Filter by SurveyMonkey |
| `WEBINAR` | Filter by webinar |
| `EMAIL_EVENT` | Filter by email event |
| `PRIVACY` | Filter by privacy settings |
| `ADS_SEARCH` | Filter by ads search |
| `ADS_TIME` | Filter by ads time |
| `IN_LIST` | Filter by list membership |
| `NUM_ASSOCIATIONS` | Filter by number of associations |
| `UNIFIED_EVENTS` | Filter by unified events |
| `PROPERTY_ASSOCIATION` | Filter by property association |
| `CONSTANT` | Constant value filter |

### 5.6 Re-enrollment Settings

Set `shouldReEnroll: true` to allow objects to be enrolled multiple times.

---

## 6. Native Action Types

### 6.1 Action Structure

Every action contains:

```json
{
  "type": "SINGLE_CONNECTION",
  "actionId": "1",
  "actionTypeVersion": 0,
  "actionTypeId": "0-X",
  "connection": {
    "edgeType": "STANDARD",
    "nextActionId": "2"
  },
  "fields": { ... }
}
```

### 6.2 Action Type IDs Reference

| Action | Type ID | Description |
|--------|---------|-------------|
| Delay (time-based) | `0-1` | Delay for set time, day of week, or time of day |
| Delay (date-based) | `0-35` | Delay until specific date or date property |
| Create task | `0-3` | Create a new task |
| Send marketing email | `0-4` | Send automated email to enrolled contact |
| Set property | `0-5` | Set property on enrolled object |
| Send email notification | `0-8` | Internal email to user/team |
| Send in-app notification | `0-9` | In-app notification to user/team |
| Create record | `0-14` | Create contact, company, deal, ticket, or lead |
| Add to list | `0-63809083` | Add contact to static list |
| Remove from list | `0-63863438` | Remove contact from static list |

### 6.3 Action Types in the `actions` Array

| Action Type | Description |
|-------------|-------------|
| `STATIC_BRANCH` | Branching based on specific property values |
| `LIST_BRANCH` | Branching based on filter criteria |
| `AB_TEST_BRANCH` | A/B testing branch |
| `CUSTOM_CODE` | Custom code action |
| `WEBHOOK` | Webhook action |
| `SINGLE_CONNECTION` | Standard single-connection action |

### 6.4 Delay Actions

**Delay until specific date:**
```json
{
  "type": "SINGLE_CONNECTION",
  "actionId": "5",
  "actionTypeVersion": 0,
  "actionTypeId": "0-35",
  "connection": { "edgeType": "STANDARD", "nextActionId": "7" },
  "fields": {
    "date": {
      "type": "STATIC_VALUE",
      "staticValue": "1719446400000"
    },
    "delta": "0",
    "time_unit": "DAYS",
    "time_of_day": { "hour": 12, "minute": 0 }
  }
}
```

**Delay until date property:**
```json
{
  "fields": {
    "date": {
      "type": "OBJECT_PROPERTY",
      "propertyName": "closedate"
    },
    "delta": "0",
    "time_unit": "DAYS"
  }
}
```

**Delay for set time (6 hours = 360 minutes):**
```json
{
  "fields": {
    "delta": "360",
    "time_unit": "MINUTES"
  }
}
```

### 6.5 Set Property Action

```json
{
  "actionId": "2",
  "actionTypeVersion": 0,
  "actionTypeId": "0-5",
  "connection": { "edgeType": "STANDARD", "nextActionId": "4" },
  "fields": {
    "property_name": "hs_lead_status",
    "association": {
      "associationCategory": "HUBSPOT_DEFINED",
      "associationTypeId": 1
    },
    "value": { "staticValue": "IN_PROGRESS" }
  }
}
```

### 6.6 Create Task Action

```json
{
  "type": "SINGLE_CONNECTION",
  "actionId": "1",
  "actionTypeVersion": 0,
  "actionTypeId": "0-3",
  "fields": {
    "task_type": "TODO",
    "subject": "Check in with lead",
    "body": "<p>Remember to sync up with new lead!</p>",
    "associations": [
      {
        "target": { "associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 10 },
        "value": { "type": "ENROLLED_OBJECT" }
      }
    ],
    "use_explicit_associations": "true",
    "priority": "NONE"
  }
}
```

### 6.7 Create Record Action (Deal)

```json
{
  "type": "SINGLE_CONNECTION",
  "actionId": "2",
  "actionTypeVersion": 0,
  "actionTypeId": "0-14",
  "connection": { "edgeType": "STANDARD", "nextActionId": "3" },
  "fields": {
    "object_type_id": "0-3",
    "properties": [
      {
        "targetProperty": "dealstage",
        "value": { "type": "STATIC_VALUE", "staticValue": "appointmentscheduled" }
      },
      {
        "targetProperty": "dealname",
        "value": { "type": "STATIC_VALUE", "staticValue": "New deal" }
      },
      {
        "targetProperty": "amount",
        "value": { "type": "STATIC_VALUE", "staticValue": "1000" }
      }
    ],
    "associations": [
      {
        "target": { "associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 3 },
        "value": { "type": "ENROLLED_OBJECT" }
      }
    ],
    "use_explicit_associations": "true"
  }
}
```

### 6.8 Send Marketing Email

```json
{
  "type": "SINGLE_CONNECTION",
  "actionId": "4",
  "actionTypeVersion": 0,
  "actionTypeId": "0-4",
  "fields": { "content_id": "113782603056" }
}
```

### 6.9 List Actions

**Add to list:**
```json
{
  "actionId": "3",
  "actionTypeVersion": 0,
  "actionTypeId": "0-63809083",
  "fields": { "listId": "123" },
  "type": "SINGLE_CONNECTION"
}
```

**Remove from list:**
```json
{
  "actionId": "3",
  "actionTypeVersion": 0,
  "actionTypeId": "0-63863438",
  "fields": { "listId": "123" },
  "type": "SINGLE_CONNECTION"
}
```

---

## 7. Branching & Multi-Step Workflows

Branching actions segment enrolled objects into different paths based on conditions.

### 7.1 Branching Action Structure

Branching actions differ from standard actions:
- No `fields` property
- No single `connection` property
- Must define `defaultBranch` and `defaultBranchName`

### 7.2 Connection Edge Types

| Edge Type | Description |
|-----------|-------------|
| `STANDARD` | Proceed to next sequential action |
| `GOTO` | Jump to action in different branch |

### 7.3 Static Branch Actions

Branch based on specific property values:

```json
{
  "actionId": "1",
  "type": "STATIC_BRANCH",
  "inputValue": {
    "propertyName": "hs_lead_status"
  },
  "staticBranches": [
    {
      "branchValue": "NEW",
      "connection": { "edgeType": "STANDARD", "nextActionId": "2" }
    },
    {
      "branchValue": "IN_PROGRESS",
      "connection": { "edgeType": "STANDARD", "nextActionId": "3" }
    },
    {
      "branchValue": "QUALIFIED",
      "connection": { "edgeType": "STANDARD", "nextActionId": "4" }
    }
  ],
  "defaultBranchName": "Other Status",
  "defaultBranch": { "edgeType": "STANDARD", "nextActionId": "5" }
}
```

### 7.4 List Branch Actions

Segment based on filter criteria (property values, list membership):

```json
{
  "actionId": "6",
  "type": "LIST_BRANCH",
  "listBranches": [
    {
      "filterBranch": {
        "filterBranches": [],
        "filters": [
          {
            "property": "lifecyclestage",
            "operation": {
              "operator": "IS_EQUAL_TO",
              "values": ["lead"]
            },
            "filterType": "PROPERTY"
          }
        ],
        "filterBranchType": "AND"
      },
      "branchName": "Leads Branch",
      "connection": { "edgeType": "STANDARD", "nextActionId": "7" }
    },
    {
      "filterBranch": {
        "filters": [
          {
            "property": "lifecyclestage",
            "operation": {
              "operator": "IS_EQUAL_TO",
              "values": ["customer"]
            },
            "filterType": "PROPERTY"
          }
        ]
      },
      "branchName": "Customers Branch",
      "connection": { "edgeType": "GOTO", "nextActionId": "4" }
    }
  ],
  "defaultBranchName": "Fall-through branch",
  "defaultBranch": { "edgeType": "STANDARD", "nextActionId": "8" }
}
```

---

## 8. Custom Workflow Actions

Custom workflow actions integrate external services with HubSpot workflows.

### 8.1 Action Definition Structure

```json
{
  "actionUrl": "https://your-api.com/webhook",
  "objectTypes": ["CONTACT", "DEAL"],
  "published": true,
  "inputFields": [...],
  "inputFieldDependencies": [...],
  "outputFields": [...],
  "objectRequestOptions": { "properties": ["email", "firstname"] },
  "labels": {...},
  "executionRules": [...],
  "functions": [...]
}
```

### 8.2 Input Fields

**Static text input:**
```json
{
  "typeDefinition": {
    "name": "widgetName",
    "type": "string",
    "fieldType": "text"
  },
  "supportedValueTypes": ["STATIC_VALUE"],
  "isRequired": true
}
```

**Dropdown with static options:**
```json
{
  "typeDefinition": {
    "name": "priority",
    "type": "enumeration",
    "fieldType": "select",
    "options": [
      { "value": "high", "label": "High" },
      { "value": "medium", "label": "Medium" },
      { "value": "low", "label": "Low" }
    ]
  },
  "supportedValueTypes": ["STATIC_VALUE"]
}
```

**External options (dynamic):**
```json
{
  "typeDefinition": {
    "name": "productId",
    "type": "enumeration",
    "fieldType": "select",
    "optionsUrl": "https://your-api.com/products"
  },
  "supportedValueTypes": ["STATIC_VALUE"]
}
```

**Object property input:**
```json
{
  "typeDefinition": {
    "name": "contactEmail",
    "type": "string",
    "fieldType": "text"
  },
  "supportedValueTypes": ["OBJECT_PROPERTY"]
}
```

**HubSpot owner field:**
```json
{
  "typeDefinition": {
    "name": "assignedOwner",
    "type": "enumeration",
    "referencedObjectType": "OWNER"
  },
  "supportedValueTypes": ["STATIC_VALUE"]
}
```

### 8.3 Input Field Dependencies

**Simple dependency (grays out until parent is filled):**
```json
{
  "dependencyType": "SINGLE_FIELD",
  "controllingFieldName": "category",
  "dependentFieldNames": ["subcategory", "options"]
}
```

**Conditional dependency (hides until specific value):**
```json
{
  "dependencyType": "CONDITIONAL_SINGLE_FIELD",
  "controllingFieldName": "notificationType",
  "controllingFieldValue": "email",
  "dependentFieldNames": ["emailTemplate", "sendTime"]
}
```

### 8.4 Output Fields

```json
{
  "outputFields": [
    {
      "typeDefinition": {
        "name": "recordId",
        "type": "string",
        "fieldType": "text"
      }
    }
  ]
}
```

### 8.5 Labels (Localization)

```json
{
  "labels": {
    "en": {
      "actionName": "Create External Record",
      "actionDescription": "Creates a record in the external system",
      "actionCardContent": "Create {{recordType}} for {{contactEmail}}",
      "appDisplayName": "My Integration",
      "inputFieldLabels": {
        "recordType": "Record Type",
        "contactEmail": "Contact Email"
      },
      "outputFieldLabels": {
        "recordId": "Created Record ID"
      },
      "inputFieldDescriptions": {
        "recordType": "Select the type of record to create"
      },
      "executionRules": {
        "duplicateError": "Record already exists: {{recordId}}",
        "validationError": "Invalid data provided"
      }
    }
  }
}
```

**Supported Languages:** `en`, `fr`, `de`, `ja`, `es`, `pt-br`, `nl`, `pl`, `sv`, `it`, `da_dk`, `fi`, `no`, `zh-tw`

### 8.6 Execution Flow

**Request sent to actionUrl:**
```json
{
  "callbackId": "ap-102670506-56776413549-7-0",
  "origin": {
    "portalId": 102670506,
    "actionDefinitionId": 10646377,
    "actionDefinitionVersion": 1
  },
  "context": {
    "source": "WORKFLOWS",
    "workflowId": 192814114
  },
  "object": {
    "objectId": 904,
    "properties": { "email": "user@example.com" },
    "objectType": "CONTACT"
  },
  "inputFields": {
    "recordType": "customer",
    "priority": "high"
  }
}
```

**Expected response:**
```json
{
  "outputFields": {
    "recordId": "ext-12345",
    "status": "created",
    "hs_execution_state": "SUCCESS"
  }
}
```

### 8.7 Execution States

| State | Behavior |
|-------|----------|
| `SUCCESS` | Action completed; workflow proceeds |
| `FAIL_CONTINUE` | Action failed; workflow proceeds anyway |
| `BLOCK` | Workflow pauses until callback completion |
| `ASYNC` | Asynchronous execution |

### 8.8 HTTP Status Code Handling

| Status | Behavior |
|--------|----------|
| 2xx | Success |
| 4xx | Failure (except 429) |
| 429 | Rate limited; respects `Retry-After` header |
| 5xx | Retries with exponential backoff for up to 3 days |

---

## 9. Custom Code Actions

Write JavaScript or Python code directly in workflows. Requires **Operations Hub Professional or Enterprise**.

### 9.1 Supported Languages & Libraries

**Node.js Libraries:**
- `@hubspot/api-client`: ^10
- `axios`: ^1.2.0
- `lodash`: ^4.17.20
- `mongoose`: ^6.8.0
- `mysql`: ^2.18.1
- `redis`: ^4.5.1
- `googleapis`: ^67.0.0
- `aws-sdk`: ^2.744.0
- `bluebird`: ^3.7.2
- `random-number-csprng`: ^1.0.2

**Python Libraries:**
- `requests`: 2.28.2
- `@hubspot/api-client`: ^8
- `google-api-python-client`: 2.74.0
- `mysql-connector-python`: 8.0.32
- `redis`: 4.4.2
- `nltk`: 3.8.1

### 9.2 Event Object Structure

```json
{
  "origin": {
    "portalId": 1,
    "actionDefinitionId": 2
  },
  "object": {
    "objectType": "CONTACT",
    "objectId": 4
  },
  "inputFields": {
    "email": "user@example.com",
    "customField": "value"
  },
  "callbackId": "ap-123-456-7-8"
}
```

### 9.3 Node.js Code Structure

```javascript
const hubspot = require('@hubspot/api-client');

exports.main = async (event, callback) => {
  // Access secrets via environment variables
  const hubspotClient = new hubspot.Client({
    accessToken: process.env.SECRET_NAME
  });

  // Access input fields
  const email = event.inputFields['email'];

  let phone;
  try {
    const response = await hubspotClient.crm.contacts.basicApi.getById(
      event.object.objectId,
      ["phone"]
    );
    phone = response.properties.phone;
  } catch (err) {
    console.error(err);
    throw err; // Triggers retry on rate limiting
  }

  // Return output fields
  callback({
    outputFields: {
      email: email,
      phone: phone,
      processedAt: new Date().toISOString()
    }
  });
};
```

### 9.4 Python Code Structure

```python
import os
from hubspot import HubSpot
from hubspot.crm.contacts import ApiException

def main(event):
  # Access secrets via environment variables
  hubspot = HubSpot(access_token=os.getenv('SECRET_NAME'))

  # Access input fields
  email = event.get('inputFields').get('email')

  phone = ''
  try:
    response = hubspot.crm.contacts.basic_api.get_by_id(
      event.get('object').get('objectId'),
      properties=["phone"]
    )
    phone = response.properties.get('phone')
  except ApiException as e:
    print(e)
    raise  # Triggers retry on rate limiting

  # Return output fields
  return {
    "outputFields": {
      "email": email,
      "phone": phone
    }
  }
```

### 9.5 Limitations

- **Execution timeout:** 20 seconds max
- **Memory limit:** 128 MB
- **String output limit:** 65,000 characters
- **Properties per action:** 50 max

### 9.6 Programmatic Custom Code Deployment (CRITICAL)

**You CAN deploy custom code workflows programmatically using the v4 API.** This is the recommended approach for automated deployments.

#### Step 1: Create Empty Workflow Shell

```javascript
const createPayload = {
  name: "[MY-PREFIX] Workflow Name",
  flowType: "WORKFLOW",
  type: "PLATFORM_FLOW",  // or "CONTACT_FLOW" for contacts
  objectTypeId: "0-3",    // Deal = 0-3, Quote = 0-14, Contact = 0-1
  isEnabled: false,
  enrollmentCriteria: { type: "MANUAL" },
  startActionId: null,
  actions: []
};

const result = await apiRequest("POST", "/automation/v4/flows", createPayload);
const flowId = result.data.id;
```

#### Step 2: Add Custom Code via PUT

**CRITICAL REQUIREMENTS:**
1. **`revisionId` is REQUIRED** - get it from GET response
2. **`secretNames` must be `[]`** if secrets don't exist yet (causes 500 error otherwise!)
3. Use minimal payload with only required fields

```javascript
// First, GET the workflow to retrieve revisionId
const current = await apiRequest("GET", `/automation/v4/flows/${flowId}`);

// Build minimal update payload
const updatePayload = {
  id: current.data.id,
  revisionId: current.data.revisionId,  // REQUIRED!
  name: current.data.name,
  isEnabled: false,
  objectTypeId: current.data.objectTypeId,
  flowType: current.data.flowType,
  type: current.data.type,
  enrollmentCriteria: current.data.enrollmentCriteria,
  startActionId: "1",
  nextAvailableActionId: "2",
  actions: [
    {
      actionId: "1",
      type: "CUSTOM_CODE",
      runtime: "NODE20X",
      sourceCode: `exports.main = async (event, callback) => {
  const hubspotClient = new (require('@hubspot/api-client').Client)({
    accessToken: process.env.HUBSPOT_TOKEN
  });

  const objectId = event.inputFields['hs_object_id'];

  // Your logic here...

  callback({
    outputFields: {
      status: 'success',
      message: 'Processed successfully'
    }
  });
};`,
      secretNames: [],  // MUST be empty if secret doesn't exist!
      inputFields: [],
      outputFields: [
        { name: "status", type: "STRING" },
        { name: "message", type: "STRING" }
      ]
    }
  ]
};

const updateResult = await apiRequest("PUT", `/automation/v4/flows/${flowId}`, updatePayload);
```

#### Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `500 internal error` | `secretNames` contains non-existent secret | Use `secretNames: []` |
| `revisionId required` | Missing revisionId in PUT | GET workflow first, use its revisionId |
| `400 bad request` | Invalid payload structure | Use minimal payload structure above |

#### Complete Deployment Script Example

```javascript
const https = require("https");
const fs = require("fs");

function apiRequest(method, path, body = null) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: "api.hubapi.com",
      path: path,
      method: method,
      headers: {
        "Authorization": "Bearer " + process.env.HUBSPOT_ACCESS_TOKEN,
        "Content-Type": "application/json"
      }
    };
    const req = https.request(options, (res) => {
      let data = "";
      res.on("data", chunk => data += chunk);
      res.on("end", () => {
        try { resolve({ status: res.statusCode, data: JSON.parse(data) }); }
        catch { resolve({ status: res.statusCode, data: data }); }
      });
    });
    req.on("error", reject);
    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

async function deployCustomCode(flowId, sourceCode) {
  // Get current workflow
  const current = await apiRequest("GET", `/automation/v4/flows/${flowId}`);

  if (current.status !== 200) {
    throw new Error(`Failed to get workflow: ${current.status}`);
  }

  // Update with custom code
  const updatePayload = {
    id: current.data.id,
    revisionId: current.data.revisionId,
    name: current.data.name,
    isEnabled: false,
    objectTypeId: current.data.objectTypeId,
    flowType: current.data.flowType,
    type: current.data.type,
    enrollmentCriteria: current.data.enrollmentCriteria,
    startActionId: "1",
    nextAvailableActionId: "2",
    actions: [{
      actionId: "1",
      type: "CUSTOM_CODE",
      runtime: "NODE20X",
      sourceCode: sourceCode,
      secretNames: [],
      inputFields: [],
      outputFields: [
        { name: "status", type: "STRING" },
        { name: "message", type: "STRING" }
      ]
    }]
  };

  const result = await apiRequest("PUT", `/automation/v4/flows/${flowId}`, updatePayload);

  if (result.status !== 200) {
    throw new Error(`Failed to update workflow: ${JSON.stringify(result.data)}`);
  }

  return result.data;
}

// Usage
const code = fs.readFileSync("my-workflow-code.js", "utf8");
await deployCustomCode("1234567890", code);
```

#### Post-Deployment Steps

After deploying custom code via API:

1. **Add Secrets:** Settings → Integrations → Private Apps → Your App → Secrets
   - Add `HUBSPOT_TOKEN` with your Private App access token

2. **Configure Triggers:** Open workflow in HubSpot UI → Set enrollment triggers

3. **Enable Workflow:** Either via UI or API:
   ```javascript
   await apiRequest("PUT", `/automation/v4/flows/${flowId}`, {
     ...currentWorkflow,
     isEnabled: true
   });
   ```

---

## 10. Functions (Serverless)

Functions are AWS Lambda-backed code snippets that transform payloads.

### 10.1 Function Types

| Type | Purpose |
|------|---------|
| `PRE_ACTION_EXECUTION` | Transform payload before sending to `actionUrl` |
| `PRE_FETCH_OPTIONS` | Transform payload before fetching external options |
| `POST_FETCH_OPTIONS` | Transform external options response |

### 10.2 Function Structure

```json
{
  "functionType": "PRE_ACTION_EXECUTION",
  "functionSource": "exports.main = (event, callback) => { ... }",
  "id": "optionalFieldId"
}
```

**Note:** `functionSource` must be a string with escaped characters.

### 10.3 PRE_ACTION_EXECUTION

Transform the execution payload:

```javascript
exports.main = (event, callback) => {
  callback({
    webhookUrl: "https://custom-api.com/endpoint",
    body: JSON.stringify({
      contactId: event.object.objectId,
      widgetName: event.inputFields.widgetName
    }),
    httpHeaders: { "X-Custom-Header": "value" },
    contentType: "application/json",
    accept: "application/json",
    httpMethod: "POST"
  });
};
```

### 10.4 POST_FETCH_OPTIONS

Transform external API response to HubSpot format:

```javascript
exports.main = (event, callback) => {
  const data = JSON.parse(event.responseBody);
  callback({
    options: data.items.map(item => ({
      label: item.name,
      description: item.description,
      value: item.id.toString()
    })),
    searchable: true,
    after: data.nextCursor
  });
};
```

---

## 11. Asynchronous Execution & Callbacks

### 11.1 Blocking Execution

Pause workflow until external process completes:

```json
{
  "outputFields": {
    "hs_execution_state": "BLOCK",
    "hs_expiration_duration": "P1WT1H"
  }
}
```

| Field | Description |
|-------|-------------|
| `hs_execution_state` | Must be `BLOCK` |
| `hs_expiration_duration` | ISO 8601 duration (default: 1 week) |

**Duration examples:**
- `P1D` = 1 day
- `P1W` = 1 week
- `PT1H` = 1 hour
- `P1WT1H` = 1 week and 1 hour

### 11.2 Completing Blocked Executions

**Single callback:**
```
POST /automation/v4/actions/callbacks/{callbackId}/complete
```

```json
{
  "outputFields": {
    "hs_execution_state": "SUCCESS",
    "customOutput": "value"
  }
}
```

**Batch callbacks:**
```
POST /automation/v4/actions/callbacks/complete
```

```json
{
  "inputs": [
    {
      "callbackId": "ap-123-456-7-8",
      "outputFields": { "hs_execution_state": "SUCCESS" }
    },
    {
      "callbackId": "ap-123-456-7-9",
      "outputFields": { "hs_execution_state": "FAIL_CONTINUE" }
    }
  ]
}
```

---

## 12. API Reference

### 12.1 Workflows v4 API

| Operation | Method | Endpoint |
|-----------|--------|----------|
| Fetch all workflows | GET | `/automation/v4/flows` |
| Fetch workflow by ID | GET | `/automation/v4/flows/{flowId}` |
| Fetch workflows in bulk | POST | `/automation/v4/flows/batch/read` |
| Create workflow | POST | `/automation/v4/flows` |
| Update workflow | PUT | `/automation/v4/flows/{flowId}` |
| Delete workflow | DELETE | `/automation/v4/flows/{flowId}` |

### 12.2 Update Workflow Requirements

**Required Fields for Update (PUT):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `flowId` | string | Yes (path) | The workflow ID to update |
| `type` | enum | Yes | `CONTACT_FLOW` or `PLATFORM_FLOW` |
| `revisionId` | string | Yes | Current revision ID (prevents concurrent modifications) |
| `isEnabled` | boolean | Yes | Workflow active status |
| `actions` | array | Yes | Updated actions array |

**Important:** The `revisionId` must match the current workflow revision. Retrieve it via `GET /automation/v4/flows/{flowId}` before updating.

### 12.3 Custom Action Definitions API

| Operation | Method | Endpoint |
|-----------|--------|----------|
| Retrieve all definitions | GET | `/automation/v4/actions/{appId}` |
| Retrieve definition | GET | `/automation/v4/actions/{appId}/{definitionId}` |
| Create definition | POST | `/automation/v4/actions/{appId}` |
| Update definition | PATCH | `/automation/v4/actions/{appId}/{definitionId}` |
| Delete definition | DELETE | `/automation/v4/actions/{appId}/{definitionId}` |

### 12.4 Functions API

| Operation | Method | Endpoint |
|-----------|--------|----------|
| Retrieve functions for definition | GET | `/automation/v4/actions/{appId}/{definitionId}/functions` |
| Retrieve functions by type | GET | `/automation/v4/actions/{appId}/{definitionId}/functions/{functionType}` |

### 12.5 Callbacks API

| Operation | Method | Endpoint |
|-----------|--------|----------|
| Complete single callback | POST | `/automation/v4/actions/callbacks/{callbackId}/complete` |
| Complete batch callbacks | POST | `/automation/v4/actions/callbacks/complete` |

---

## 13. Complete Examples

### 13.1 Create Contact Workflow with Form Trigger and Branching

```json
{
  "type": "CONTACT_FLOW",
  "objectTypeId": "0-1",
  "isEnabled": false,
  "canEnrollFromSalesforce": false,
  "flowType": "WORKFLOW",
  "name": "Lead Nurturing Workflow",
  "description": "Nurtures leads based on form submissions",
  "startActionId": "1",
  "nextAvailableActionId": "5",
  "actions": [
    {
      "actionId": "1",
      "type": "STATIC_BRANCH",
      "inputValue": { "propertyName": "hs_lead_status" },
      "staticBranches": [
        {
          "branchValue": "NEW",
          "connection": { "edgeType": "STANDARD", "nextActionId": "2" }
        },
        {
          "branchValue": "QUALIFIED",
          "connection": { "edgeType": "STANDARD", "nextActionId": "3" }
        }
      ],
      "defaultBranchName": "Default Path",
      "defaultBranch": { "edgeType": "STANDARD", "nextActionId": "4" }
    },
    {
      "type": "SINGLE_CONNECTION",
      "actionId": "2",
      "actionTypeVersion": 0,
      "actionTypeId": "0-4",
      "connection": { "edgeType": "STANDARD", "nextActionId": "4" },
      "fields": { "content_id": "welcome_email_id" }
    },
    {
      "type": "SINGLE_CONNECTION",
      "actionId": "3",
      "actionTypeVersion": 0,
      "actionTypeId": "0-3",
      "fields": {
        "task_type": "CALL",
        "subject": "Follow up with qualified lead",
        "priority": "HIGH"
      }
    },
    {
      "type": "SINGLE_CONNECTION",
      "actionId": "4",
      "actionTypeVersion": 0,
      "actionTypeId": "0-5",
      "fields": {
        "property_name": "lifecyclestage",
        "value": { "staticValue": "lead" }
      }
    }
  ],
  "enrollmentCriteria": {
    "type": "EVENT_BASED",
    "shouldReEnroll": false,
    "eventFilterBranches": [
      {
        "eventTypeId": "4-1639801",
        "operator": "HAS_COMPLETED",
        "filterBranchType": "UNIFIED_EVENTS",
        "filterBranchOperator": "AND",
        "filterBranches": [],
        "filters": [
          {
            "property": "hs_form_id",
            "operation": {
              "operator": "IS_ANY_OF",
              "values": ["form-uuid-here"],
              "operationType": "ENUMERATION"
            },
            "filterType": "PROPERTY"
          }
        ]
      }
    ],
    "listMembershipFilterBranches": []
  },
  "timeWindows": [],
  "blockedDates": [],
  "customProperties": {},
  "dataSources": [],
  "suppressionListIds": []
}
```

### 13.2 Create Deal Workflow (PLATFORM_FLOW)

```json
{
  "type": "PLATFORM_FLOW",
  "objectTypeId": "0-3",
  "isEnabled": false,
  "flowType": "WORKFLOW",
  "name": "Deal Stage Automation",
  "startActionId": "1",
  "nextAvailableActionId": "3",
  "actions": [
    {
      "type": "SINGLE_CONNECTION",
      "actionId": "1",
      "actionTypeVersion": 0,
      "actionTypeId": "0-1",
      "connection": { "edgeType": "STANDARD", "nextActionId": "2" },
      "fields": { "delta": "1440", "time_unit": "MINUTES" }
    },
    {
      "type": "SINGLE_CONNECTION",
      "actionId": "2",
      "actionTypeVersion": 0,
      "actionTypeId": "0-9",
      "fields": {
        "user_ids": ["owner_id"],
        "delivery_method": "APP",
        "subject": "Deal follow-up reminder",
        "body": "Time to follow up on this deal!"
      }
    }
  ],
  "enrollmentCriteria": {
    "type": "LIST_BASED",
    "shouldReEnroll": false,
    "unEnrollObjectsNotMeetingCriteria": false,
    "listFilterBranch": {
      "filterBranchOperator": "OR",
      "filterBranchType": "OR",
      "filterBranches": [
        {
          "filterBranchType": "AND",
          "filterBranchOperator": "AND",
          "filters": [
            {
              "filterType": "PROPERTY",
              "property": "dealstage",
              "operation": {
                "operator": "IS_EQUAL_TO",
                "values": ["qualifiedtobuy"],
                "operationType": "ENUMERATION"
              }
            }
          ]
        }
      ],
      "filters": []
    }
  },
  "customProperties": {},
  "dataSources": []
}
```

### 13.3 Update Workflow Example

```json
// PUT /automation/v4/flows/585051946
{
  "type": "CONTACT_FLOW",
  "revisionId": "7",
  "isEnabled": true,
  "name": "Updated Lead Nurturing Workflow",
  "actions": [
    // ... updated actions array
  ],
  "enrollmentCriteria": {
    // ... updated enrollment criteria
  },
  "timeWindows": [],
  "blockedDates": [],
  "customProperties": {},
  "suppressionListIds": [],
  "canEnrollFromSalesforce": false
}
```

---

## Quick Reference Card

### Workflow Types
- `CONTACT_FLOW` - Contact workflows (objectTypeId: `0-1`)
- `PLATFORM_FLOW` - Deal, Company, Ticket, Custom Object workflows

### Object Type IDs
| Object | ID |
|--------|-----|
| Contacts | `0-1` |
| Companies | `0-2` |
| Deals | `0-3` |
| Tickets | `0-5` |
| Products | `0-7` |
| Line Items | `0-8` |
| Quotes | `0-14` |
| Custom Objects | `2-XXXXXXX` (use custom object ID) |

### Key Action Type IDs
| Action | ID |
|--------|-----|
| Delay (time) | `0-1` |
| Delay (date) | `0-35` |
| Create task | `0-3` |
| Send email | `0-4` |
| Set property | `0-5` |
| Email notification | `0-8` |
| In-app notification | `0-9` |
| Create record | `0-14` |
| Add to list | `0-63809083` |
| Remove from list | `0-63863438` |

### Event Type IDs
| Event | ID |
|-------|-----|
| Form submission | `4-1639801` |
| Email open | `4-666440` |
| Email click | `4-666288` |
| Call start | `4-1733817` |

### Enrollment Types
- `EVENT_BASED` - Trigger on events
- `LIST_BASED` - Filter criteria

### Execution States
- `SUCCESS` - Complete
- `FAIL_CONTINUE` - Failed but continue
- `BLOCK` - Wait for callback
- `ASYNC` - Asynchronous

### Custom Code Limits
- **Timeout:** 20 seconds
- **Memory:** 128 MB
- **Output:** 65,000 characters
- **Properties:** 50 max per action

### Runtime Versions
- `NODE20X` - Node.js 20.x (recommended)
- `NODE18X` - Node.js 18.x (legacy)
- `PYTHON311` - Python 3.11

### Custom Code Field Types
| Type | Description |
|------|-------------|
| `STRING` | Text values |
| `NUMBER` | Numeric values |
| `BOOLEAN` | true/false |
| `DATE` | Date values |
| `DATETIME` | Date and time values |
| `ENUMERATION` | Single select values |

---

## 14. Best Practices

### Two-Step Workflow Creation (Recommended)

Creating workflows with custom code is more reliable using two steps:

```javascript
// Step 1: Create empty workflow
const emptyWorkflow = {
  name: 'My Integration Workflow',
  flowType: 'WORKFLOW',
  type: 'PLATFORM_FLOW',
  objectTypeId: '0-2',
  isEnabled: false,
  enrollmentCriteria: { type: 'MANUAL' },
  startActionId: null,
  actions: []
};

const createResult = await apiRequest('POST', '/automation/v4/flows', emptyWorkflow);
const flowId = createResult.data.id;

// Step 2: Add custom code via PUT
const workflowWithCode = {
  ...createResult.data,
  startActionId: '1',
  actions: [{
    actionId: '1',
    type: 'CUSTOM_CODE',
    runtime: 'NODE20X',
    sourceCode: 'exports.main = async (event, callback) => { ... };',
    inputFields: [],
    outputFields: [{ name: 'result', type: 'STRING' }],
    secretNames: [],
    connection: null
  }]
};

await apiRequest('PUT', `/automation/v4/flows/${flowId}`, workflowWithCode);
```

### Partial Updates with PATCH

Use PATCH to update only specific parts (e.g., just the custom code):

```javascript
// Get current workflow
const workflow = await apiRequest('GET', `/automation/v4/flows/${flowId}`);

// Update only the sourceCode
workflow.data.actions[0].sourceCode = newSourceCode;

// PATCH only the actions array
await apiRequest('PATCH', `/automation/v4/flows/${flowId}`, {
  actions: workflow.data.actions
});
```

### Action Chaining

Chain multiple actions using the `connection` property:

```json
{
  "actionId": "1",
  "type": "CUSTOM_CODE",
  "connection": { "nextActionId": "2" },
  "..."
},
{
  "actionId": "2",
  "type": "CUSTOM_CODE",
  "connection": { "nextActionId": "3" },
  "..."
},
{
  "actionId": "3",
  "type": "CUSTOM_CODE",
  "connection": null
}
```

### Secrets Management

Declare secrets in the action, then access via `process.env`:

```json
{
  "actionId": "1",
  "type": "CUSTOM_CODE",
  "secretNames": ["API_KEY", "CLIENT_SECRET"],
  "sourceCode": "const apiKey = process.env.API_KEY;"
}
```

**Note:** Secrets must be created in HubSpot first:
Settings → Integrations → Private Apps → [App] → Secrets tab

---

## 15. API Rate Limits

| Limit Type | Value |
|------------|-------|
| Requests per second | 10 |
| Requests per day | 500,000 |
| Burst limit | 100 requests |

### Retry Logic for Rate Limits

```javascript
async function apiRequestWithRetry(method, path, body, retries = 3) {
  for (let i = 0; i < retries; i++) {
    const result = await apiRequest(method, path, body);
    if (result.status === 429) {
      const delay = Math.pow(2, i) * 1000;
      console.log(`Rate limited, waiting ${delay}ms...`);
      await new Promise(r => setTimeout(r, delay));
      continue;
    }
    return result;
  }
  throw new Error('Max retries exceeded');
}
```

---

## 16. Troubleshooting

### Common Errors

#### "type must be one of PLATFORM_FLOW, CONTACT_FLOW"

**Cause:** Wrong flow type for object
**Solution:** Use `PLATFORM_FLOW` for Companies, Deals, Tickets, Custom Objects. Use `CONTACT_FLOW` only for Contacts.

```javascript
// Wrong
{ type: 'CONTACT_FLOW', objectTypeId: '0-2' }  // Companies

// Correct
{ type: 'PLATFORM_FLOW', objectTypeId: '0-2' }  // Companies
```

#### "Invalid objectTypeId"

**Cause:** Object type doesn't exist or wrong format
**Solution:**
- Standard objects: `0-X` (e.g., `0-1`, `0-2`, `0-3`)
- Custom objects: `2-XXXXXXX` (e.g., `2-46766501`)

#### "Cannot create workflow with actions"

**Cause:** Some action configurations are invalid on creation
**Solution:** Create empty workflow first, then add actions via PUT (two-step pattern)

#### "Secret not found"

**Cause:** Secret declared in `secretNames` but not created in HubSpot
**Solution:** Create secrets in HubSpot before deploying:
1. Settings → Integrations → Private Apps
2. Select your app
3. Add secrets under "Secrets" tab

#### Custom code execution timeout

**Cause:** Code takes longer than 20 seconds
**Solution:**
- Optimize API calls (use `Promise.all` for parallel requests)
- Use shorter timeouts
- Break into multiple chained actions

```javascript
// Use Promise.all for parallel requests
const [result1, result2] = await Promise.all([
  axios.get('/endpoint1'),
  axios.get('/endpoint2')
]);
```

### Debug Tips

1. **Check workflow history:** HubSpot → Automation → Workflows → [Workflow] → History
2. **Use console.log:** Logs appear in workflow execution history
3. **Test API calls externally first:**
   ```bash
   curl -X GET 'https://api.hubapi.com/automation/v4/flows' \
     -H 'Authorization: Bearer YOUR_TOKEN'
   ```
4. **Validate JSON before sending:** `console.log(JSON.stringify(payload, null, 2))`

---

*Documentation based on HubSpot Developer Documentation - Automation API v4*
*Enhanced with practical implementation patterns from real integration projects*
