# ShopEasy LangGraph Nodes

This document defines the initial node contract for the MVP workflows.

## Schema Alignment

```text
These node contracts are aligned to the DBML schema in dbs.db.
Use the exact table names from dbs.db when implementing ORM models and tool queries.
```

## Shared State Shape

The graph state can start with these top-level sections:

```text
session:
- trace_id
- conversation_id
- customer_id
- message_id
- workflow_name

input:
- raw_message
- detected_intent
- event_payload

context:
- customer
- active_order_ids
- active_shipment_ids
- case_id
- refund_request_id

retrieval:
- memory_summary
- orders
- shipments
- shipment_items
- policies
- attachments

decision:
- selected_workflow
- eligibility_result
- risk_score
- requires_human_approval
- fallback_reason

output:
- customer_response
- internal_note

observability:
- tool_calls
- node_results
- warnings
```

## Node Catalog

### `router_node`

- Purpose: classify the incoming message or event into an intent or workflow family.
- Input state: `input.raw_message`, `input.event_payload`
- Output state: `input.detected_intent`, `decision.selected_workflow`
- Tools used: `detect_intent()`

### `memory_retrieval_node`

- Purpose: fetch recent conversation memory and customer-specific context that helps disambiguate the request.
- Input state: `session.conversation_id`, `session.customer_id`
- Output state: `retrieval.memory_summary`
- Tools used: `get_conversation_memory()`

### `context_resolution_node`

- Purpose: map the request to the most relevant customer, order, shipment, case, or refund request.
- Input state: `session.customer_id`, `input.raw_message`, `retrieval.memory_summary`
- Output state: `context.customer`, `context.active_order_ids`, `context.active_shipment_ids`, `context.case_id`
- Tools used: `resolve_customer_context()`

### `planner_node`

- Purpose: convert the intent into an execution plan and determine which downstream nodes are required.
- Input state: `input.detected_intent`, `context`, `retrieval.memory_summary`
- Output state: `decision.selected_workflow`, `observability.node_results`
- Tools used: `build_execution_plan()`

### `order_node`

- Purpose: load order-level business records needed by the workflow.
- Input state: `context.active_order_ids`, `session.customer_id`
- Output state: `retrieval.orders`
- Tools used: `get_customer_open_orders()`, `get_order()`

### `shipping_node`

- Purpose: load shipment records, tracking statuses, and item mappings.
- Input state: `context.active_order_ids`, `context.active_shipment_ids`
- Output state: `retrieval.shipments`, `retrieval.shipment_items`
- Tools used: `get_shipments_by_order()`, `get_shipment()`, `get_items_by_shipment()`

### `policy_rag_node`

- Purpose: retrieve policy chunks relevant to the decision being made.
- Input state: `input.raw_message`, `decision.selected_workflow`, `retrieval.orders`
- Output state: `retrieval.policies`
- Tools used: `search_policy()`

### `refund_node`

- Purpose: evaluate whether the order or item is eligible for refund or return.
- Input state: `retrieval.orders`, `retrieval.policies`, `context.case_id`
- Output state: `decision.eligibility_result`, `context.refund_request_id`
- Tools used: `check_refund_eligibility()`, `create_refund_request()`

### `evidence_node`

- Purpose: inspect uploaded files and determine whether the evidence set is sufficient.
- Input state: `context.refund_request_id`, `context.case_id`
- Output state: `retrieval.attachments`, `decision.eligibility_result`
- Tools used: `review_evidence_attachments()`

### `risk_node`

- Purpose: score operational or fraud risk for shipment delay and refund decisions.
- Input state: `retrieval.orders`, `retrieval.shipments`, `retrieval.attachments`, `retrieval.policies`
- Output state: `decision.risk_score`, `decision.requires_human_approval`
- Tools used: `calculate_risk_score()`, `calculate_delay_risk()`

### `supervisor_node`

- Purpose: apply escalation rules and decide whether to hand off to a human approval step.
- Input state: `decision.eligibility_result`, `decision.risk_score`
- Output state: `decision.requires_human_approval`
- Tools used: `apply_supervisor_rules()`

### `approval_node`

- Purpose: create approval records for high-risk or policy-sensitive actions.
- Input state: `decision.requires_human_approval`, `decision.eligibility_result`, `decision.risk_score`
- Output state: `context.case_id`, `observability.node_results`
- Tools used: `request_approval()`

### `proactive_alert_node`

- Purpose: create alert records and proactive case actions for shipment delays.
- Input state: `retrieval.shipments`, `decision.risk_score`, `retrieval.policies`
- Output state: `observability.node_results`, `context.case_id`
- Tools used: `create_proactive_alert()`, `create_case()`

### `support_response_node`

- Purpose: produce the customer-facing or internal response for the current workflow.
- Input state: `decision`, `retrieval`, `context`
- Output state: `output.customer_response`, `output.internal_note`
- Tools used: `send_customer_message()`, `send_customer_notification()`

### `memory_write_node`

- Purpose: save a concise summary of what happened so later turns can reuse it.
- Input state: `output.customer_response`, `decision`, `context`
- Output state: `retrieval.memory_summary`
- Tools used: `write_memory_summary()`

### `logging_node`

- Purpose: persist workflow trace data and per-tool execution logs.
- Input state: `session`, `decision`, `observability`, `output`
- Output state: `observability.node_results`
- Tools used: `log_tool_call()`, `log_agent_trace()`

### `fallback_node`

- Purpose: safely recover when intent, context, or required data cannot be resolved.
- Input state: `input`, `context`, `decision`
- Output state: `output.customer_response`, `decision.fallback_reason`
- Tools used: `send_customer_message()`

### `event_ingestion_node`

- Purpose: normalize background events into the same graph state used by chat-driven workflows.
- Input state: `input.event_payload`
- Output state: `session.customer_id`, `context.active_shipment_ids`, `decision.selected_workflow`
- Tools used: `ingest_event()`

## MVP Node Sets by Workflow

### Workflow 1: Track Shipment

```text
router_node
memory_retrieval_node
context_resolution_node
planner_node
order_node
shipping_node
support_response_node
memory_write_node
logging_node
```

### Workflow 2: Refund / Return

```text
router_node
memory_retrieval_node
context_resolution_node
planner_node
order_node
policy_rag_node
refund_node
evidence_node
risk_node
supervisor_node
approval_node
support_response_node
memory_write_node
logging_node
```

### Workflow 3: Proactive Delay Alert

```text
event_ingestion_node
shipping_node
risk_node
policy_rag_node
proactive_alert_node
supervisor_node
approval_node
support_response_node
memory_write_node
logging_node
```

## Implementation Notes

```text
- Build Workflow 1 first and keep the state minimal.
- Do not seed all database tables before a workflow needs them.
- Treat each node as a thin orchestration layer over reusable tools.
- Keep observability fields in state from day one so traces are not bolted on later.
```
