# Serverless Function Patterns

Common patterns for HubSpot serverless functions in Developer Projects.

## Basic Function Structure

### Developer Projects (app.functions/)

```javascript
// src/app/app.functions/my-function.js
const hubspot = require('@hubspot/api-client');

exports.main = async (context = {}) => {
  const { propertiesToSend, parameters } = context;

  // Access properties sent from UI
  const { hs_object_id, email } = propertiesToSend;

  // Access custom parameters
  const { customParam } = parameters;

  // Initialize client
  const client = new hubspot.Client({
    accessToken: process.env.PRIVATE_APP_ACCESS_TOKEN,
  });

  // Do work...

  // Return data to UI
  return {
    success: true,
    data: { /* ... */ },
  };
};
```

### CMS Serverless (functions/)

```javascript
// functions/my-function.js
exports.main = async (context, sendResponse) => {
  const { body, params, method, headers } = context;

  try {
    // Process request...
    const result = await processData(body);

    sendResponse({
      statusCode: 200,
      body: JSON.stringify(result),
      headers: {
        'Content-Type': 'application/json',
      },
    });
  } catch (error) {
    sendResponse({
      statusCode: 500,
      body: JSON.stringify({ error: error.message }),
    });
  }
};
```

**Key Difference:** Developer Projects return values directly; CMS uses `sendResponse()`.

---

## serverless.json Configuration

### Developer Projects

```json
{
  "runtime": "nodejs18.x",
  "version": "1.0",
  "endpoints": {
    "get-data": {
      "file": "get-data.js",
      "method": "GET"
    },
    "save-data": {
      "file": "save-data.js",
      "method": "POST"
    }
  },
  "secrets": ["PRIVATE_APP_ACCESS_TOKEN", "EXTERNAL_API_KEY"]
}
```

### CMS Serverless

```json
{
  "runtime": "nodejs18.x",
  "version": "1.0",
  "environment": {
    "PUBLIC_VAR": "value"
  },
  "secrets": ["SECRET_API_KEY"],
  "endpoints": {
    "form-handler": {
      "method": "POST",
      "file": "form-handler.js",
      "path": "/form-handler"
    }
  }
}
```

---

## Common Patterns

### 1. Fetch Associated Records

```javascript
const hubspot = require('@hubspot/api-client');

exports.main = async (context = {}) => {
  const { hs_object_id } = context.propertiesToSend;

  const client = new hubspot.Client({
    accessToken: process.env.PRIVATE_APP_ACCESS_TOKEN,
  });

  // Get contact with deal associations
  const contact = await client.crm.contacts.basicApi.getById(
    hs_object_id,
    ['email', 'firstname', 'lastname'],
    undefined,
    ['deals']
  );

  if (!contact.associations?.deals?.results?.length) {
    return { deals: [], count: 0 };
  }

  // Batch fetch associated deals
  const dealIds = contact.associations.deals.results.map(d => d.id);
  const deals = await client.crm.deals.batchApi.read({
    inputs: dealIds.map(id => ({ id })),
    properties: ['dealname', 'amount', 'dealstage', 'closedate'],
  });

  return {
    deals: deals.results,
    count: deals.results.length,
  };
};
```

### 2. Create/Update Records

```javascript
exports.main = async (context = {}) => {
  const { hs_object_id } = context.propertiesToSend;
  const { newValue, propertyName } = context.parameters;

  const client = new hubspot.Client({
    accessToken: process.env.PRIVATE_APP_ACCESS_TOKEN,
  });

  // Update contact property
  const updated = await client.crm.contacts.basicApi.update(
    hs_object_id,
    {
      properties: {
        [propertyName]: newValue,
      },
    }
  );

  return {
    success: true,
    updatedAt: updated.updatedAt,
  };
};
```

### 3. Search Records

```javascript
exports.main = async (context = {}) => {
  const { searchQuery, objectType } = context.parameters;

  const client = new hubspot.Client({
    accessToken: process.env.PRIVATE_APP_ACCESS_TOKEN,
  });

  const searchRequest = {
    filterGroups: [
      {
        filters: [
          {
            propertyName: 'email',
            operator: 'CONTAINS_TOKEN',
            value: searchQuery,
          },
        ],
      },
    ],
    properties: ['email', 'firstname', 'lastname', 'company'],
    limit: 10,
  };

  const results = await client.crm.contacts.searchApi.doSearch(searchRequest);

  return {
    results: results.results,
    total: results.total,
  };
};
```

### 4. External API Integration

```javascript
const axios = require('axios');

exports.main = async (context = {}) => {
  const { email } = context.propertiesToSend;

  try {
    // Call external API
    const response = await axios.get(
      `https://api.external-service.com/enrich`,
      {
        params: { email },
        headers: {
          'Authorization': `Bearer ${process.env.EXTERNAL_API_KEY}`,
        },
        timeout: 5000,
      }
    );

    return {
      success: true,
      enrichedData: response.data,
    };
  } catch (error) {
    console.error('External API error:', error.message);
    throw new Error('Failed to enrich data');
  }
};
```

### 5. Batch Operations

```javascript
exports.main = async (context = {}) => {
  const { contactIds } = context.parameters;

  const client = new hubspot.Client({
    accessToken: process.env.PRIVATE_APP_ACCESS_TOKEN,
  });

  // Batch read (max 100 per request)
  const batchSize = 100;
  const results = [];

  for (let i = 0; i < contactIds.length; i += batchSize) {
    const batch = contactIds.slice(i, i + batchSize);
    const response = await client.crm.contacts.batchApi.read({
      inputs: batch.map(id => ({ id })),
      properties: ['email', 'firstname', 'lastname'],
    });
    results.push(...response.results);
  }

  return { contacts: results };
};
```

### 6. Create Association

```javascript
exports.main = async (context = {}) => {
  const { hs_object_id } = context.propertiesToSend;
  const { dealId } = context.parameters;

  const client = new hubspot.Client({
    accessToken: process.env.PRIVATE_APP_ACCESS_TOKEN,
  });

  // Associate contact with deal
  await client.crm.associations.v4.basicApi.create(
    'contacts',
    hs_object_id,
    'deals',
    dealId,
    [{ associationCategory: 'HUBSPOT_DEFINED', associationTypeId: 4 }]
  );

  return { success: true };
};
```

---

## Error Handling Pattern

```javascript
exports.main = async (context = {}) => {
  const { hs_object_id } = context.propertiesToSend;

  const client = new hubspot.Client({
    accessToken: process.env.PRIVATE_APP_ACCESS_TOKEN,
  });

  try {
    const contact = await client.crm.contacts.basicApi.getById(
      hs_object_id,
      ['email']
    );
    return { success: true, contact };
  } catch (error) {
    // Log for debugging (visible in hs logs functions)
    console.error('Error fetching contact:', {
      message: error.message,
      status: error.statusCode,
      body: error.body,
    });

    // Return user-friendly error
    if (error.statusCode === 404) {
      throw new Error('Contact not found');
    }
    if (error.statusCode === 403) {
      throw new Error('Permission denied - check app scopes');
    }
    throw new Error('Failed to fetch contact data');
  }
};
```

---

## Environment & Secrets

### Adding Secrets

```bash
# Add secret
hs secrets add PRIVATE_APP_ACCESS_TOKEN

# List secrets
hs secrets list

# Remove secret
hs secrets delete EXTERNAL_API_KEY
```

### Accessing in Code

```javascript
// Secrets are available as environment variables
const token = process.env.PRIVATE_APP_ACCESS_TOKEN;
const apiKey = process.env.EXTERNAL_API_KEY;
```

### package.json Dependencies

```json
{
  "name": "my-app-functions",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "@hubspot/api-client": "^12.0.0",
    "axios": "^1.6.0"
  }
}
```

---

## Debugging

### View Logs

```bash
# Tail logs in real-time
hs logs functions --tail

# View recent logs
hs logs functions --latest
```

### Local Testing

```javascript
// test-function.js (local testing)
require('dotenv').config();

const myFunction = require('./src/app/app.functions/my-function');

async function test() {
  const result = await myFunction.main({
    propertiesToSend: {
      hs_object_id: '123',
      email: 'test@example.com',
    },
    parameters: {},
  });
  console.log('Result:', result);
}

test().catch(console.error);
```

---

## Rate Limits

| Operation | Limit |
|-----------|-------|
| Function execution | 10s timeout |
| API calls per function | Follow HubSpot API limits |
| Batch operations | 100 records max |
| Daily executions | Based on portal tier |

**Best Practice:** Batch API calls and cache results when possible.
