# ShopEasy Mock Data Plan

This document limits seed data to what the workflows actually need.

## Source of Truth

```text
Seed design must follow dbs.db, which is the DBML schema file for the project.
Do not invent alternate table names if the table already exists in dbs.db.
```

## Seeding Principle

```text
Do not mock the whole platform first.
Mock only the records required to execute the current workflow end-to-end.
```

## Priority Order

### Phase A: Workflow 1 Seed

Required tables:

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

Purpose:

```text
Enable "where is my order?" conversations with enough detail to summarize split shipments.
```

Suggested records:

```text
users:
- U-001 customer_demo
- U-002 admin_demo

customers:
- CUST-001 Narisara

sellers:
- SELL-001 FashionHub
- SELL-002 GadgetMall

orders:
- SP-1024 customer CUST-001 seller SELL-001 status partially_shipped
- SP-2044 customer CUST-001 seller SELL-002 status shipped
- SP-8831 customer CUST-001 seller SELL-001 status delivered

order_items:
- ITEM-1001 shirt in SP-1024
- ITEM-1002 suit in SP-1024
- ITEM-1003 pants in SP-1024
- ITEM-2001 headphones in SP-2044

shipments:
- SHP-9001 order SP-1024 status delivered
- SHP-9002 order SP-1024 status in_transit delayed_flag=true
- SHP-9003 order SP-2044 status out_for_delivery

shipment_items:
- SHP-9001 -> ITEM-1001
- SHP-9001 -> ITEM-1002
- SHP-9002 -> ITEM-1003
- SHP-9003 -> ITEM-2001

conversations:
- CONV-001 customer CUST-001 channel chat

messages:
- MSG-001 customer asks where the order is

agent_traces:
- one sample successful track_shipment trace

tool_logs:
- one sample detect_intent log
- one sample get_shipments_by_order log
```

Field alignment from dbs.db:

```text
orders.order_status
orders.payment_status
shipments.shipment_status
shipments.last_update
shipments.delay_risk_score
conversations.latest_intent
messages.metadata
agent_traces.workflow_name
agent_traces.intent
tool_logs.input_payload
tool_logs.output_payload
```

### Phase B: Workflow 2 Seed

Add these tables:

```text
cases
refund_requests
attachments
policies
policy_chunks
approvals
```

Purpose:

```text
Enable refund and return flows with evidence review and policy grounding.
```

Suggested records:

```text
cases:
- CS-5521 type refund_review status open

refund_requests:
- RF-5521 order SP-1024 status pending_review reason damaged_item

attachments:
- ATT-001 category damaged_item
- ATT-002 category parcel_package
- ATT-003 category parcel_label

policies:
- POL-REFUND-001 Refund Policy
- POL-RETURN-001 Return Policy
- POL-COMP-001 Compensation Policy

policy_chunks:
- 2 to 4 chunks per policy are enough for MVP

approvals:
- APR-1001 linked to CS-5521 status pending
```

Field alignment from dbs.db:

```text
cases.case_type
cases.priority
cases.status
refund_requests.requested_resolution
refund_requests.eligibility_status
refund_requests.risk_score
refund_requests.ai_recommendation
attachments.owner_type
attachments.attachment_type
attachments.evidence_group
approvals.approval_type
approvals.risk_level
approvals.policy_citation
```

### Phase C: Workflow 3 Seed

Add these tables:

```text
shipment_events
proactive_alerts
```

Purpose:

```text
Enable system-generated delay detection and proactive outreach.
```

Suggested records:

```text
shipment_events:
- EVT-7001 shipment SHP-9002 type shipment_no_update_48h

proactive_alerts:
- ALT-1001 shipment SHP-9002 status open risk_score 87
```

Field alignment from dbs.db:

```text
shipment_events.event_type
shipment_events.event_message
shipment_events.event_time
shipment_events.raw_payload
proactive_alerts.alert_type
proactive_alerts.risk_score
proactive_alerts.recommended_action
proactive_alerts.message_draft
```

## Minimal Relationship Map

```text
customer
-> orders
-> order_items
-> shipments
-> shipment_items

customer
-> conversations
-> messages

order
-> refund_requests
-> cases
-> approvals

refund_request
-> attachments

policies
-> policy_chunks

shipment
-> shipment_events
-> proactive_alerts
```

## Suggested Seed Modules

When implementation starts, keep seed files grouped by workflow instead of one giant script.

```text
backend/app/db/seeds/
- base_reference_seed.py
- workflow_01_tracking_seed.py
- workflow_02_refund_seed.py
- workflow_03_proactive_seed.py
```

## Data Rules

```text
- Use stable IDs that are easy to read in traces and screenshots.
- Keep customer count very small at the start.
- Ensure at least one order is split into multiple shipments.
- Ensure at least one shipment is delayed but not delivered.
- Ensure policy data is short, searchable, and tagged by category.
- Seed logs and traces only as examples until real execution exists.
```

## Ready-to-Build Sequence

```text
1. Seed Workflow 1 tables only.
2. Build Workflow 1 graph and confirm response quality.
3. Extend seeds for Workflow 2.
4. Add policy chunks and approval records.
5. Extend seeds for Workflow 3 event-driven flow.
```
