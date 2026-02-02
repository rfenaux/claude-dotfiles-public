# UI Extension Components Reference

Complete reference for `@hubspot/ui-extensions` components (v0.13.0+).

## Layout Components

### Flex
```jsx
<Flex direction="column" align="center" justify="between" gap="medium" wrap="wrap">
  {children}
</Flex>
```

| Prop | Values |
|------|--------|
| `direction` | `row`, `column` |
| `align` | `start`, `center`, `end`, `stretch` |
| `justify` | `start`, `center`, `end`, `between`, `around` |
| `gap` | `flush`, `extra-small`, `small`, `medium`, `large`, `extra-large` |
| `wrap` | `wrap`, `nowrap` |

### Box
```jsx
<Box padding="medium">
  {children}
</Box>
```

### Tile
```jsx
<Tile>
  <Flex direction="column" gap="small">
    <Text format={{ fontWeight: 'bold' }}>Title</Text>
    <Text>Content</Text>
  </Flex>
</Tile>
```

### Divider
```jsx
<Divider />
```

---

## Text & Display

### Text
```jsx
<Text format={{ fontWeight: 'bold', italic: true }}>
  Formatted text
</Text>

<Text variant="microcopy">Small text</Text>
```

| Prop | Values |
|------|--------|
| `variant` | `default`, `microcopy` |
| `format.fontWeight` | `regular`, `medium`, `demibold`, `bold` |
| `format.italic` | `true`, `false` |

### Heading
```jsx
<Heading>Section Title</Heading>
```

### Link
```jsx
<Link href="https://example.com" external={true}>
  External Link
</Link>
```

### Tag
```jsx
<Tag variant="success">Active</Tag>
<Tag variant="warning">Pending</Tag>
<Tag variant="error">Failed</Tag>
```

| `variant` | Color |
|-----------|-------|
| `default` | Gray |
| `success` | Green |
| `warning` | Yellow |
| `error` | Red |

---

## Data Display

### Statistics
```jsx
<Statistics>
  <StatisticsItem label="Deals" number={42}>
    <Text>Total open deals</Text>
  </StatisticsItem>
  <StatisticsItem label="Value" number={150000}>
    <Text>Pipeline value</Text>
  </StatisticsItem>
</Statistics>
```

### Table
```jsx
<Table bordered={true}>
  <TableHead>
    <TableRow>
      <TableHeader>Name</TableHeader>
      <TableHeader>Value</TableHeader>
    </TableRow>
  </TableHead>
  <TableBody>
    <TableRow>
      <TableCell>Deal 1</TableCell>
      <TableCell>$10,000</TableCell>
    </TableRow>
  </TableBody>
</Table>
```

### DescriptionList
```jsx
<DescriptionList direction="row">
  <DescriptionListItem label="Status">
    <Text>Active</Text>
  </DescriptionListItem>
  <DescriptionListItem label="Owner">
    <Text>John Doe</Text>
  </DescriptionListItem>
</DescriptionList>
```

### ProgressBar
```jsx
<ProgressBar
  value={75}
  maxValue={100}
  variant="success"
  showPercentage={true}
/>
```

---

## Form Components

### Button
```jsx
<Button
  onClick={handleClick}
  variant="primary"
  size="medium"
  disabled={false}
  type="button"
>
  Click Me
</Button>
```

| `variant` | Style |
|-----------|-------|
| `primary` | Blue filled |
| `secondary` | White/outlined |
| `destructive` | Red |

### ButtonRow
```jsx
<ButtonRow>
  <Button variant="primary">Save</Button>
  <Button variant="secondary">Cancel</Button>
</ButtonRow>
```

### Input
```jsx
<Input
  name="email"
  label="Email Address"
  placeholder="Enter email"
  value={email}
  onChange={(value) => setEmail(value)}
  required={true}
  error={emailError}
/>
```

### TextArea
```jsx
<TextArea
  name="notes"
  label="Notes"
  value={notes}
  onChange={(value) => setNotes(value)}
  rows={4}
/>
```

### Select
```jsx
<Select
  name="priority"
  label="Priority"
  value={priority}
  onChange={(value) => setPriority(value)}
  options={[
    { label: 'High', value: 'high' },
    { label: 'Medium', value: 'medium' },
    { label: 'Low', value: 'low' },
  ]}
/>
```

### Checkbox / Toggle
```jsx
<Checkbox
  name="agree"
  checked={agreed}
  onChange={(checked) => setAgreed(checked)}
>
  I agree to the terms
</Checkbox>

<Toggle
  name="notifications"
  checked={enabled}
  onChange={(checked) => setEnabled(checked)}
  label="Enable notifications"
/>
```

### DateInput
```jsx
<DateInput
  name="deadline"
  label="Deadline"
  value={deadline}
  onChange={(value) => setDeadline(value)}
  format="YYYY-MM-DD"
/>
```

### Form
```jsx
<Form onSubmit={handleSubmit}>
  <Input name="name" label="Name" required />
  <Input name="email" label="Email" type="email" />
  <Button type="submit">Submit</Button>
</Form>
```

---

## Feedback Components

### Alert
```jsx
<Alert title="Error" variant="error">
  Something went wrong. Please try again.
</Alert>

<Alert title="Success" variant="success">
  Record updated successfully.
</Alert>
```

| `variant` | Style |
|-----------|-------|
| `info` | Blue |
| `success` | Green |
| `warning` | Yellow |
| `error` | Red |

### LoadingSpinner
```jsx
<LoadingSpinner label="Loading data..." />
```

### EmptyState
```jsx
<EmptyState
  title="No deals found"
  message="This contact has no associated deals."
>
  <Button onClick={createDeal}>Create Deal</Button>
</EmptyState>
```

---

## Media

### Image
```jsx
<Image
  src="https://example.com/image.png"
  alt="Description"
  width={200}
  height={150}
/>
```

### Icon
```jsx
<Icon name="success" />
<Icon name="warning" />
<Icon name="error" />
```

---

## hubspot Object Methods

### Call Serverless Function
```jsx
const result = await hubspot.serverless('function-name', {
  propertiesToSend: ['hs_object_id', 'email', 'firstname'],
  parameters: { customData: 'value' },
});
```

### Get Context
```jsx
hubspot.extend(({ context }) => {
  const { user, portal } = context;
  console.log('Portal ID:', portal.id);
  console.log('User email:', user.email);
  return <MyCard />;
});
```

### Refresh CRM
```jsx
// After updating a record, refresh the CRM UI
hubspot.actions.refreshObjectProperties();
```

### Open Panel/Modal
```jsx
hubspot.actions.openIframe({
  uri: '/panel-content',
  height: 500,
  width: 400,
  title: 'Details',
});
```

---

## Complete Example

```jsx
import React, { useState, useEffect } from 'react';
import {
  Alert,
  Button,
  ButtonRow,
  Divider,
  Flex,
  LoadingSpinner,
  Statistics,
  StatisticsItem,
  Text,
  Tile,
  hubspot,
} from '@hubspot/ui-extensions';

hubspot.extend(({ context }) => <MyCard context={context} />);

const MyCard = ({ context }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await hubspot.serverless('get-data', {
        propertiesToSend: ['hs_object_id'],
      });
      setData(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) {
    return (
      <Flex direction="column" align="center" gap="medium">
        <LoadingSpinner />
        <Text>Loading...</Text>
      </Flex>
    );
  }

  if (error) {
    return (
      <Alert title="Error" variant="error">
        {error}
      </Alert>
    );
  }

  return (
    <Flex direction="column" gap="large">
      <Tile>
        <Text format={{ fontWeight: 'bold' }}>Summary</Text>
        <Divider />
        <Statistics>
          <StatisticsItem label="Deals" number={data.dealCount} />
          <StatisticsItem label="Value" number={data.totalValue} />
        </Statistics>
      </Tile>

      <ButtonRow>
        <Button onClick={fetchData} variant="secondary">
          Refresh
        </Button>
        <Button variant="primary">
          View Details
        </Button>
      </ButtonRow>
    </Flex>
  );
};
```
