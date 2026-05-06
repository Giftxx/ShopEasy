# ShopEasy Workflow Plan

This document defines the MVP AI workflows that should be implemented before full backend development and before broad mock data seeding.

## Source of Truth

```text
Database schema source:
- dbs.db

Important:
- dbs.db is a DBML/dbdiagram schema file
- it is not a SQLite runtime database
- workflow and seed planning should align to the table names and fields defined there
```

## Design Order

```text
1. Choose MVP workflow
2. Define LangGraph nodes
3. Draw graph flow
4. Map tools per node
5. Mock only the data needed by the workflow
6. Implement backend and LangGraph
```

## Workflow 1: Track Shipment

### Goal

Handle customer messages such as:

```text
ของฉันอยู่ไหนแล้ว
```

The AI should:

```text
- detect intent = track_shipment
- identify relevant customer context
- fetch open orders and active shipments
- summarize multi-shipment status clearly
- save memory and trace logs
```

### Input

```text
customer_message
conversation_id
customer_id
```

### Expected Output

```text
natural-language shipment summary
follow-up prompt if multiple active shipments exist
trace + tool logs
memory summary
```

### Nodes

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

### Graph Flow

```text
Customer message
-> router_node
-> memory_retrieval_node
-> context_resolution_node
-> planner_node
-> order_node
-> shipping_node
-> support_response_node
-> memory_write_node
-> logging_node
```

### Tools

```text
detect_intent()
get_conversation_memory()
resolve_customer_context()
get_customer_open_orders()
get_shipments_by_order()
get_items_by_shipment()
send_customer_message()
write_memory_summary()
log_tool_call()
log_agent_trace()
```

### Tables Used

```text
customers
orders
order_items
shipments
shipment_items
conversations
messages
agent_traces
tool_logs
```

### Required Mock Scenario

```text
Customer:
- CUST-001 Narisara

Orders:
- SP-1024 from FashionHub
- SP-2044 from GadgetMall

Items:
- shirt
- suit
- pants
- headphones

Shipments:
- SHP-9001 delivered
- SHP-9002 in_transit / delayed
- SHP-9003 out_for_delivery
```

### Example Response

```text
ตอนนี้คุณมี 2 พัสดุที่ยังไม่ถึงค่ะ

1. ออเดอร์ SP-1024: กางเกง จากร้าน FashionHub
สถานะ: อยู่ระหว่างขนส่ง และยังไม่มีอัปเดตล่าสุด

2. ออเดอร์ SP-2044: หูฟัง จากร้าน GadgetMall
สถานะ: กำลังนำส่งวันนี้

ต้องการให้ฉันติดตามรายการไหนเป็นพิเศษไหมคะ?
```

## Workflow 2: Refund / Return

### Goal

Handle refund or return requests such as:

```text
สินค้าเสียหาย ขอคืนเงิน
```

### Input

```text
customer_message
conversation_id
customer_id
optional attachment references
```

### Expected Output

```text
refund eligibility summary
case creation or escalation result
approval request if required
trace + tool logs
```

### Nodes

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

### Graph Flow

```text
Customer message
-> router_node
-> memory_retrieval_node
-> context_resolution_node
-> planner_node
-> order_node
-> policy_rag_node
-> refund_node
-> evidence_node
-> risk_node
-> supervisor_node
-> approval_node (conditional)
-> support_response_node
-> memory_write_node
-> logging_node
```

### Tools

```text
detect_intent()
get_conversation_memory()
resolve_customer_context()
get_order()
search_policy()
check_refund_eligibility()
review_evidence_attachments()
calculate_risk_score()
create_case()
create_refund_request()
request_approval()
send_customer_message()
write_memory_summary()
log_tool_call()
log_agent_trace()
```

### Tables Used

```text
customers
orders
order_items
refund_requests
cases
attachments
policies
policy_chunks
approvals
agent_traces
tool_logs
messages
conversations
```

### Required Mock Scenario

```text
refund_request RF-5521
case CS-5521
attachments:
- damaged_item image
- parcel_package image
- parcel_label image
policies:
- Refund Policy
- Return Policy
- Compensation Policy
```

### Example Response

```text
ได้รับคำขอคืนเงินสำหรับออเดอร์ SP-1024 แล้วค่ะ
ระบบตรวจพบว่าคุณแนบรูปหลักฐานสินค้าเสียหายแล้ว และได้เปิดเคส CS-5521 เพื่อส่งให้เจ้าหน้าที่ตรวจสอบค่ะ
```

## Workflow 3: Proactive Delay Alert

### Goal

Handle system-generated shipment delay events before the customer asks.

### Input

```text
event_type = shipment_no_update_48h
shipment_id
customer_id
```

### Expected Output

```text
delay risk evaluation
proactive alert record
case or approval if needed
customer notification
trace + tool logs
```

### Nodes

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

### Graph Flow

```text
System event
-> event_ingestion_node
-> shipping_node
-> risk_node
-> policy_rag_node
-> proactive_alert_node
-> supervisor_node
-> approval_node (conditional)
-> support_response_node
-> memory_write_node
-> logging_node
```

### Tools

```text
ingest_event()
get_shipment()
calculate_delay_risk()
search_policy()
create_proactive_alert()
create_case()
request_approval()
send_customer_notification()
write_memory_summary()
log_tool_call()
log_agent_trace()
```

### Tables Used

```text
shipments
shipment_events
orders
customers
policies
policy_chunks
proactive_alerts
cases
approvals
agent_traces
tool_logs
messages
conversations
```

### Required Mock Scenario

```text
shipment SHP-9002
last_update older than 48 hours
delay_risk_score = 87
compensation policy available
proactive_alert ALT-1001
case CS-7001
```

## Delivery Sequence

```text
First:
- finalize Workflow 1 graph
- mock only Workflow 1 data
- build backend/LangGraph path for Workflow 1

Second:
- add Workflow 2 with refund-specific tables and tools

Third:
- add Workflow 3 for proactive event handling
```
