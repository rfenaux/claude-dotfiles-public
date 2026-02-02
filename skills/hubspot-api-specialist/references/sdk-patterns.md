# HubSpot SDK Patterns

Node.js SDK patterns for `@hubspot/api-client` v12+.

## Installation

```bash
npm install @hubspot/api-client
```

---

## Client Initialization

### Private App Token

```javascript
const hubspot = require('@hubspot/api-client');

const client = new hubspot.Client({
  accessToken: process.env.PRIVATE_APP_ACCESS_TOKEN,
});
```

### OAuth Token

```javascript
const client = new hubspot.Client({
  accessToken: userAccessToken,
});
```

### Developer API Key

```javascript
const client = new hubspot.Client({
  developerApiKey: process.env.DEVELOPER_API_KEY,
});
```

---

## CRUD Patterns

### Create Record

```javascript
async function createContact(properties) {
  const response = await client.crm.contacts.basicApi.create({
    properties: {
      email: properties.email,
      firstname: properties.firstname,
      lastname: properties.lastname,
    },
  });
  return response;
}
```

### Read Record

```javascript
async function getContact(contactId, properties = ['email', 'firstname']) {
  const response = await client.crm.contacts.basicApi.getById(
    contactId,
    properties,
    undefined,  // propertiesWithHistory
    ['deals']   // associations
  );
  return response;
}
```

### Update Record

```javascript
async function updateContact(contactId, properties) {
  const response = await client.crm.contacts.basicApi.update(
    contactId,
    { properties }
  );
  return response;
}
```

### Delete (Archive) Record

```javascript
async function archiveContact(contactId) {
  await client.crm.contacts.basicApi.archive(contactId);
}
```

---

## Batch Patterns

### Batch Create

```javascript
async function batchCreateContacts(contacts) {
  const response = await client.crm.contacts.batchApi.create({
    inputs: contacts.map(c => ({
      properties: c,
    })),
  });
  return response.results;
}
```

### Batch Read

```javascript
async function batchReadContacts(ids, properties) {
  const response = await client.crm.contacts.batchApi.read({
    inputs: ids.map(id => ({ id })),
    properties,
  });
  return response.results;
}
```

### Batch Update

```javascript
async function batchUpdateContacts(updates) {
  const response = await client.crm.contacts.batchApi.update({
    inputs: updates.map(u => ({
      id: u.id,
      properties: u.properties,
    })),
  });
  return response.results;
}
```

### Batch Upsert (Create or Update)

```javascript
async function batchUpsertContacts(records, idProperty = 'email') {
  const response = await client.crm.contacts.batchApi.upsert({
    inputs: records.map(r => ({
      idProperty,
      id: r[idProperty],
      properties: r,
    })),
  });
  return response.results;
}
```

### Chunked Batch (>100 records)

```javascript
async function batchReadAllContacts(ids, properties) {
  const BATCH_SIZE = 100;
  const results = [];

  for (let i = 0; i < ids.length; i += BATCH_SIZE) {
    const batch = ids.slice(i, i + BATCH_SIZE);
    const response = await client.crm.contacts.batchApi.read({
      inputs: batch.map(id => ({ id })),
      properties,
    });
    results.push(...response.results);

    // Rate limit buffer
    if (i + BATCH_SIZE < ids.length) {
      await sleep(100);
    }
  }

  return results;
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
```

---

## Search Patterns

### Basic Search

```javascript
async function searchContacts(email) {
  const response = await client.crm.contacts.searchApi.doSearch({
    filterGroups: [
      {
        filters: [
          {
            propertyName: 'email',
            operator: 'CONTAINS_TOKEN',
            value: email,
          },
        ],
      },
    ],
    properties: ['email', 'firstname', 'lastname'],
    limit: 100,
  });
  return response.results;
}
```

### Multi-Filter Search

```javascript
async function searchCustomers(domain, lifecyclestage) {
  const response = await client.crm.contacts.searchApi.doSearch({
    filterGroups: [
      {
        filters: [
          {
            propertyName: 'email',
            operator: 'CONTAINS_TOKEN',
            value: `@${domain}`,
          },
          {
            propertyName: 'lifecyclestage',
            operator: 'EQ',
            value: lifecyclestage,
          },
        ],
      },
    ],
    sorts: [
      {
        propertyName: 'createdate',
        direction: 'DESCENDING',
      },
    ],
    properties: ['email', 'firstname', 'lastname', 'company'],
    limit: 100,
  });
  return response.results;
}
```

### Paginated Search

```javascript
async function searchAllContacts(filters, properties) {
  const allResults = [];
  let after = 0;

  do {
    const response = await client.crm.contacts.searchApi.doSearch({
      filterGroups: [{ filters }],
      properties,
      limit: 100,
      after,
    });

    allResults.push(...response.results);
    after = response.paging?.next?.after;
  } while (after && allResults.length < 10000);

  return allResults;
}
```

---

## Association Patterns (v4)

### Get Association Labels

```javascript
async function getAssociationLabels(fromType, toType) {
  const response = await client.crm.associations.v4.schema.definitionsApi.getAll(
    fromType,
    toType
  );
  return response.results;
}
```

### Create Association

```javascript
async function associateContactToCompany(contactId, companyId, typeId = 1) {
  await client.crm.associations.v4.basicApi.create(
    'contacts',
    contactId,
    'companies',
    companyId,
    [
      {
        associationCategory: 'HUBSPOT_DEFINED',
        associationTypeId: typeId,
      },
    ]
  );
}
```

### Batch Create Associations

```javascript
async function batchAssociateContactsToDeals(associations) {
  await client.crm.associations.v4.batchApi.create(
    'contacts',
    'deals',
    {
      inputs: associations.map(a => ({
        _from: { id: a.contactId },
        to: { id: a.dealId },
        types: [
          {
            associationCategory: 'HUBSPOT_DEFINED',
            associationTypeId: 4,
          },
        ],
      })),
    }
  );
}
```

### Get Associations for Record

```javascript
async function getContactDeals(contactId) {
  const response = await client.crm.associations.v4.basicApi.getPage(
    'contacts',
    contactId,
    'deals',
    undefined,
    500
  );
  return response.results;
}
```

---

## Pagination Pattern

### Get All Records

```javascript
async function getAllContacts(properties = ['email', 'firstname']) {
  const allContacts = [];
  let after = undefined;

  do {
    const response = await client.crm.contacts.basicApi.getPage(
      100,
      after,
      properties
    );

    allContacts.push(...response.results);
    after = response.paging?.next?.after;
  } while (after);

  return allContacts;
}
```

---

## Error Handling

### Standard Error Handler

```javascript
async function safeApiCall(fn) {
  try {
    return await fn();
  } catch (error) {
    if (error.code === 404) {
      return null; // Record not found
    }
    if (error.code === 429) {
      // Rate limited - wait and retry
      const retryAfter = error.headers?.['retry-after'] || 1;
      await sleep(retryAfter * 1000);
      return safeApiCall(fn);
    }
    if (error.body?.category === 'VALIDATION_ERROR') {
      console.error('Validation errors:', error.body.errors);
      throw new Error('Invalid data: ' + error.body.errors.map(e => e.message).join(', '));
    }
    throw error;
  }
}

// Usage
const contact = await safeApiCall(() =>
  client.crm.contacts.basicApi.getById(id, ['email'])
);
```

### Retry with Exponential Backoff

```javascript
async function withRetry(fn, maxRetries = 3) {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      if (error.code === 429 || error.code >= 500) {
        const delay = Math.pow(2, attempt) * 1000;
        console.log(`Retry ${attempt + 1}/${maxRetries} in ${delay}ms`);
        await sleep(delay);
        continue;
      }
      throw error;
    }
  }
  throw new Error('Max retries exceeded');
}
```

---

## OAuth Token Refresh

```javascript
async function refreshAccessToken(refreshToken) {
  const response = await client.oauth.tokensApi.create(
    'refresh_token',
    undefined,
    undefined,
    process.env.CLIENT_ID,
    process.env.CLIENT_SECRET,
    refreshToken
  );

  return {
    accessToken: response.accessToken,
    refreshToken: response.refreshToken,
    expiresIn: response.expiresIn,
  };
}
```

---

## Webhook Verification

```javascript
const crypto = require('crypto');

function verifyHubSpotSignature(body, signature, secret) {
  const hash = crypto
    .createHmac('sha256', secret)
    .update(body)
    .digest('base64');

  return hash === signature;
}

// Express middleware
function hubspotWebhookAuth(req, res, next) {
  const signature = req.headers['x-hubspot-signature-v3'];
  const timestamp = req.headers['x-hubspot-request-timestamp'];

  // Check timestamp (within 5 minutes)
  const now = Date.now();
  if (Math.abs(now - parseInt(timestamp)) > 300000) {
    return res.status(401).json({ error: 'Request too old' });
  }

  // Verify signature
  const signatureInput = `${req.method}${req.originalUrl}${req.rawBody}${timestamp}`;
  if (!verifyHubSpotSignature(signatureInput, signature, process.env.WEBHOOK_SECRET)) {
    return res.status(401).json({ error: 'Invalid signature' });
  }

  next();
}
```

---

## Complete Example: Sync System

```javascript
const hubspot = require('@hubspot/api-client');

class HubSpotSync {
  constructor(accessToken) {
    this.client = new hubspot.Client({ accessToken });
  }

  async syncContacts(externalContacts) {
    const results = { created: 0, updated: 0, errors: [] };
    const BATCH_SIZE = 100;

    for (let i = 0; i < externalContacts.length; i += BATCH_SIZE) {
      const batch = externalContacts.slice(i, i + BATCH_SIZE);

      try {
        const response = await this.client.crm.contacts.batchApi.upsert({
          inputs: batch.map(c => ({
            idProperty: 'email',
            id: c.email,
            properties: {
              email: c.email,
              firstname: c.firstName,
              lastname: c.lastName,
              company: c.company,
            },
          })),
        });

        response.results.forEach(r => {
          if (r.new) {
            results.created++;
          } else {
            results.updated++;
          }
        });
      } catch (error) {
        results.errors.push({
          batch: i,
          error: error.message,
        });
      }

      // Rate limit buffer
      await this.sleep(100);
    }

    return results;
  }

  async getContactsModifiedSince(since) {
    const allContacts = [];
    let after = 0;

    const filters = [
      {
        propertyName: 'lastmodifieddate',
        operator: 'GTE',
        value: since.toISOString(),
      },
    ];

    do {
      const response = await this.client.crm.contacts.searchApi.doSearch({
        filterGroups: [{ filters }],
        properties: ['email', 'firstname', 'lastname', 'lastmodifieddate'],
        sorts: [{ propertyName: 'lastmodifieddate', direction: 'ASCENDING' }],
        limit: 100,
        after,
      });

      allContacts.push(...response.results);
      after = response.paging?.next?.after;
    } while (after && allContacts.length < 10000);

    return allContacts;
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

module.exports = HubSpotSync;
```
