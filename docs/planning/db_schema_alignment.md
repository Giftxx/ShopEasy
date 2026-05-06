# ShopEasy DB Schema Alignment

This document maps the workflow plan to the existing schema in `dbs.db`.

## What `dbs.db` Actually Is

```text
dbs.db is a DBML/dbdiagram schema file.
It is not a SQLite database file.
```

## Confirmed Tables Needed by MVP

Workflow 1:

```text
users
customers
sellers
orders
order_items
shipments
shipment_items
conversations
messages
agent_traces
tool_logs
```

Workflow 2 adds:

```text
attachments
cases
approvals
refund_requests
policies
policy_chunks
```

Workflow 3 adds:

```text
shipment_events
proactive_alerts
```

## Important Field Matches

### Tracking flow

```text
orders.id
orders.customer_id
orders.seller_id
orders.order_status

shipments.id
shipments.order_id
shipments.tracking_no
shipments.shipment_status
shipments.eta
shipments.last_update
shipments.delay_risk_score

shipment_items.shipment_id
shipment_items.order_item_id
```

### Conversation flow

```text
conversations.id
conversations.customer_id
conversations.latest_intent

messages.conversation_id
messages.sender_type
messages.content
messages.metadata
```

### Refund flow

```text
cases.id
cases.order_id
cases.case_type
cases.priority
cases.status

refund_requests.id
refund_requests.order_id
refund_requests.customer_id
refund_requests.case_id
refund_requests.requested_resolution
refund_requests.eligibility_status
refund_requests.risk_score

attachments.refund_request_id
attachments.case_id
attachments.attachment_type
attachments.evidence_group
attachments.object_key
```

### Observability flow

```text
agent_traces.id
agent_traces.workflow_name
agent_traces.intent
agent_traces.status
agent_traces.requires_human_approval
agent_traces.final_response
agent_traces.state_snapshot

tool_logs.trace_id
tool_logs.agent_name
tool_logs.tool_name
tool_logs.input_payload
tool_logs.output_payload
tool_logs.status
tool_logs.error_message
```

## Build Implications

```text
- Do not redesign table names.
- ORM models should mirror dbs.db first.
- Seed scripts should use the exact IDs and relations planned in workflow docs.
- Workflow 1 can start immediately because the schema already supports split shipment tracking.
```

## Recommended Next Build Step

```text
1. Create backend skeleton
2. Convert dbs.db schema into SQLAlchemy models
3. Seed Workflow 1 records only
4. Implement Workflow 1 LangGraph path
```
