# ShopEasy — Agentic AI Operations Platform
## Complete Project Reference Document

> **Version 3.0 — Unified Reference**  
> รวม Project Blueprint + Agentic Architecture ฉบับสมบูรณ์  
> อัปเดตล่าสุด: 7 พฤษภาคม 2026

**Concept:** AI-powered post-purchase support platform สำหรับ marketplace ที่ผสาน LangGraph multi-agent workflows, PostgreSQL, MinIO, Redis และ Human-in-the-Loop approvals  
**Core Capabilities:** ReAct Loop · Dynamic Planning · Self-Correction · 3-Layer Memory · Inter-Agent Protocol · Full Observability

---

## สารบัญ

1. [วิสัยทัศน์และภาพรวม](#1-วิสัยทัศน์และภาพรวม)
2. [Architecture และ Tech Stack](#2-architecture-และ-tech-stack)
3. [Database Schema](#3-database-schema)
4. [API Routes ทั้งหมด](#4-api-routes-ทั้งหมด)
5. [LangGraph — 3 Core Workflows](#5-langgraph--3-core-workflows)
6. [Agentic AI Architecture](#6-agentic-ai-architecture)
   - 6.1 ReAct Loop Engine
   - 6.2 Planning Layer
   - 6.3 Memory System 3 ชั้น
   - 6.4 Error Recovery System
   - 6.5 Supervisor Agent
   - 6.6 Inter-Agent Communication Protocol
7. [Full Observability System](#7-full-observability-system)
8. [Frontend — 3 Portals](#8-frontend--3-portals)
9. [MinIO File Storage](#9-minio-file-storage)
10. [Infrastructure & Deployment](#10-infrastructure--deployment)
11. [Project Structure](#11-project-structure)
12. [Implementation Roadmap](#12-implementation-roadmap)
13. [Agentic AI Checklist](#13-agentic-ai-checklist)

---

# 1. วิสัยทัศน์และภาพรวม

**ShopEasy** เปลี่ยน marketplace post-purchase operations ให้ชาญฉลาดด้วย AI โดยไม่ใช่แค่ chatbot แต่เป็นระบบ **Agentic AI Operations Platform** ที่สามารถ:

- วางแผนและตัดสินใจเองแบบ dynamic
- เรียกใช้ tool ต่าง ๆ และสังเกตผลลัพธ์
- แก้ไขข้อผิดพลาดและ replan ได้เอง
- จำ context, พฤติกรรมลูกค้า และเหตุการณ์สำคัญในอดีต
- ส่งต่อให้ human เมื่อความเสี่ยงสูง
- บันทึก trace ทุกขั้นตอนเพื่อ audit และปรับปรุง

### Use Cases หลัก

| Use Case | ผู้ใช้ | Workflow |
|----------|--------|----------|
| ตรวจสอบ order / shipment | Customer | Workflow 01 — Order Tracking |
| ขอคืนเงิน / คืนสินค้า | Customer | Workflow 02 — Refund Request |
| แจ้งเตือน shipment ล่าช้า | ระบบ (Event-driven) | Workflow 03 — Proactive Delay Alert |
| อนุมัติ / ปฏิเสธ approval | Admin | Human-in-the-Loop |
| ดู trace และ debug | AI Engineer | AI Control Portal |

### ความแตกต่าง Scripted Multi-Agent vs Truly Agentic

| ด้าน | Scripted (แบบเดิม) | Truly Agentic (ปัจจุบัน) |
|------|-------------------|--------------------------|
| Workflow | ลำดับ hardcode A → B → C | Agent ตัดสินใจ path เองตามสถานการณ์ |
| เมื่อ tool fail | หยุดหรือ error | Retry → Fallback → Replan → Escalate |
| Memory | จำได้เฉพาะ session | Short-term + Long-term + Episodic |
| Planning | ไม่มีแผนก่อนทำ | สร้าง ExecutionPlan ก่อน execute |
| Inter-agent | shared state เท่านั้น | Message passing + Event + Agent spawning |
| Self-correction | ไม่มี | Reflect, revise, re-run และปรับแผนได้ |
| Observability | log พื้นฐาน | Trace ทุก node, tool call, plan step, decision |

---

# 2. Architecture และ Tech Stack

### ภาพรวม System Architecture

```
Customer Portal  Admin Portal  AI Control Portal
       │               │                │
       └───────────────┴────────────────┘
                        │
                   FastAPI Backend
                  /api/v1/...
                        │
          ┌─────────────┼────────────────┐
          │             │                │
     LangGraph     PostgreSQL         MinIO
   (3 Workflows)  (Business Data)  (Evidence Files)
          │             │
        Redis         Alembic
    (Cache/Queue)   (Migrations)
```

### Tech Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Frontend** | React + Vite + TypeScript | 18 / 5 | 3 Portals: Customer, Admin, AI Control |
| **Styling** | CSS Custom Properties | — | Design system ที่ไม่ใช้ framework |
| **Backend API** | FastAPI | ≥0.115 | REST endpoints & event processing |
| **AI Workflow** | LangGraph | ≥0.1 | Multi-agent orchestration engine |
| **LLM Framework** | LangChain Core | ≥0.2 | Tool binding & chain utilities |
| **Database** | PostgreSQL | 16 | Business data persistence |
| **ORM** | SQLAlchemy | 2.x | Python ORM & schema mapping |
| **Migrations** | Alembic | ≥1.13 | Schema versioning & management |
| **File Storage** | MinIO | ≥7.2 | Images, videos, evidence documents |
| **Cache** | Redis | 7 | Session cache & background jobs |
| **Infrastructure** | Docker Compose | — | Local multi-service development |
| **ASGI Server** | Uvicorn | ≥0.30 | Production-ready async server |

> **หมายเหตุ MVP:** Qdrant (Vector DB สำหรับ Policy RAG) ยังไม่ได้ implement ใน codebase ปัจจุบัน Policy search ทำงานผ่าน keyword matching กับ PostgreSQL โดยตรง

### Docker Services

| Service | Container | Port | Image |
|---------|-----------|------|-------|
| PostgreSQL | shopeasy-postgres | 5433:5432 | postgres:16-alpine |
| Backend API | shopeasy-backend | 8000:8000 | ./backend/Dockerfile |
| Frontend | shopeasy-frontend | 5173:5173 | ./frontend/Dockerfile |
| Redis | shopeasy-redis | 6379:6379 | redis:7-alpine |
| MinIO | shopeasy-minio | 9000:9000, 9001:9001 | minio/minio:latest |

```bash
# เริ่มระบบทั้งหมด
docker compose up --build

# Health check endpoints
GET http://localhost:8000/            → Backend root
GET http://localhost:8000/api/v1/health  → API health
GET http://localhost:9001             → MinIO Console
```

---

# 3. Database Schema

### ตาราง Core (28 ตาราง)

```
users, customers, sellers
orders, order_items
shipments, shipment_items, shipment_events
conversations, messages
attachments
cases, approvals, refund_requests, evidence_reviews
policies, policy_chunks
agent_traces, tool_logs, proactive_alerts
agents, agent_configs
evaluations, evaluation_cases
audit_logs, integrations, system_settings
```

### Entity Relationships หลัก

```
User (1) ──── (0..1) Customer
Customer (1) ──── (N) Order
Customer (1) ──── (N) Conversation
Order (1) ──── (N) OrderItem
Order (1) ──── (N) Shipment
Shipment (1) ──── (N) ShipmentItem
Shipment (1) ──── (N) ShipmentEvent
Order (1) ──── (0..1) Case
Case (1) ──── (N) Approval
Case (1) ──── (N) RefundRequest
Case (1) ──── (N) Attachment
Conversation (1) ──── (N) Message
Conversation (1) ──── (N) AgentTrace
AgentTrace (1) ──── (N) ToolLog
```

### GraphState — Agent State Schema

`GraphState` ใน `app/agents/state.py` ประกอบด้วย 6 sub-state:

```python
class GraphState(
    SessionState,       # trace_id, conversation_id, customer_id, workflow_name
    InputState,         # raw_message, detected_intent, event_payload
    ContextState,       # customer, active_orders, active_shipments, ids
    RetrievalState,     # memory_summary, orders, shipments, policies, attachments
    DecisionState,      # selected_workflow, eligibility, risk_score, requires_human
    OutputState,        # customer_response, internal_note
    ObservabilityState, # tool_calls, node_results, warnings
):
    pass
```

### Mock Data Seeds

```
Users:   customer_demo, admin_demo, ai_system_admin
Customers: นารีศรา, Nicha, Beam
Sellers:   FashionHub, GadgetMall, BeautyMall
Orders:    SP-1024 (in-progress), SP-2044 (delayed), SP-8831 (delivered)
           SP-7711 (cancelled), SP-9900 (refund requested)
```

### Alembic Migrations

```bash
# สร้าง migration ใหม่
alembic revision --autogenerate -m "description"

# Run migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

# 4. API Routes ทั้งหมด

Base URL: `http://localhost:8000/api/v1`

### Auth Routes (`/auth`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/mock-login` | Login สำหรับ 3 roles (customer / admin / ai_control) |
| GET | `/auth/me` | Current user profile |

```json
// POST /auth/mock-login
{ "role": "customer" }  // → returns user + access_token

// Roles: "customer", "admin", "ai_control"
// Mock tokens: mock_token_for_{role}_{user_id}
```

### Chat Routes (`/chat`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/chat` | ส่งข้อความและรับ AI response |

```json
// POST /chat
{
  "conversation_id": "conv-uuid",
  "customer_id": "cust-uuid",
  "message": "ของฉันอยู่ไหนแล้ว",
  "target_order_id": null
}

// Intent routing logic ใน chat.py:
// 1. ถ้า message มี keyword refund → handle_refund_chat()
// 2. ถ้า intent = track_shipment → handle_tracking_chat()
// 3. default → handle_tracking_chat()
```

### Customer Data Routes (`/data`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/data/customers/{id}` | Customer profile |
| GET | `/data/orders` | รายการ orders |
| GET | `/data/orders/{order_id}` | Order detail |
| GET | `/data/shipments` | ติดตาม shipments |
| GET | `/data/refund-requests` | ประวัติ refund |
| GET | `/data/conversations` | รายการ conversations |
| GET | `/data/conversations/{id}/messages` | Chat history |
| GET | `/data/proactive-alerts` | การแจ้งเตือน |

### Admin Routes (`/admin`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/admin/cases` | Case queue |
| GET | `/admin/cases/{case_id}` | Case detail |
| GET | `/admin/approvals` | Approval queue |
| POST | `/admin/approvals/{id}/approve` | Approve decision |
| POST | `/admin/approvals/{id}/reject` | Reject decision |
| GET | `/admin/refund-requests` | Refund queue |
| POST | `/admin/cases/{id}/close` | Close case |
| GET | `/admin/proactive-alerts` | Delay alerts |
| POST | `/admin/proactive-alerts/{id}/resolve` | Resolve alert |

### Attachments Routes (`/attachments`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/attachments/presign-upload` | Generate presigned upload URL |
| POST | `/attachments/confirm-upload` | Register upload metadata |
| GET | `/attachments` | List attachments |
| GET | `/attachments/{id}/presign-download` | Get download URL |
| DELETE | `/attachments/{id}` | Remove file |

### AI Control Routes (`/ai`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/ai/agent-traces` | Workflow executions (filter: workflow, status, intent, case_id) |
| GET | `/ai/agent-traces/{trace_id}` | Trace detail |
| GET | `/ai/tool-logs` | Tool call logs |

### Events Routes (`/events`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/events/proactive-delay` | Trigger proactive delay workflow |

```json
// POST /events/proactive-delay
{
  "shipment_id": "SHP-001",
  "event_type": "shipment_no_update_48h"
}
```

### Health Route (`/health`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service health check |

---

# 5. LangGraph — 3 Core Workflows

## 5.1 Workflow 01 — Order Tracking

**Trigger:** Customer ส่งข้อความถามสถานะ order / shipment  
**Implementation:** `app/agents/graph.py` + `app/services/workflow_01_tracking.py`

### Graph Flow (LangGraph StateGraph)

```
START
  │
  ▼
router_node            → detect_tracking_intent() → set detected_intent
  │
  ├─ [intent = track_shipment] ──→ get_context
  └─ [other intent] ──────────→ fallback ──→ END
  │
  ▼
get_context            → get_tracking_context(db, customer_id, conversation_id)
                         → loads: customer, active_orders, active_shipments
  │
  ▼
get_memory             → build_memory_summary() → set memory_summary
  │
  ▼
plan                   → select_workflow = "workflow_01_track_shipment"
  │
  ▼
get_shipping           → build_shipment_summaries() → set shipments[]
  │
  ▼
respond                → build_tracking_response() → set customer_response
  │
  ▼
END
```

### Nodes และ Tools

| Node | Tool | Output |
|------|------|--------|
| `router_node` | `detect_tracking_intent()` | `detected_intent` |
| `context_resolution_node` | `get_tracking_context()` | customer, orders, shipments |
| `memory_retrieval_node` | `build_memory_summary()` | `memory_summary` |
| `planner_node` | `select_workflow()` | `selected_workflow` |
| `shipping_node` | `build_shipment_summaries()` | `shipments[]` |
| `support_response_node` | `build_tracking_response()` | `customer_response` |
| `fallback_node` | — | `fallback_reason` |

### ตัวอย่าง Response

```
ตอนนี้ออเดอร์ SP-1024 มี 2 พัสดุค่ะ
1. เสื้อและสูท (FashionHub): ส่งสำเร็จแล้ว ✓
2. กางเกง (FashionHub): อยู่ระหว่างขนส่ง — ไม่อัปเดต 48+ ชม.
ระบบกำลังติดตามให้ค่ะ
```

---

## 5.2 Workflow 02 — Refund Request

**Trigger:** Customer ส่งข้อความที่มี keyword refund/คืนเงิน/สินค้าเสียหาย  
**Implementation:** `app/agents/nodes/refund_nodes.py` + `app/services/workflow_02_refund.py`

### Node Pipeline (Sequential — ไม่ใช้ StateGraph)

```
refund_router_node            → detect_refund_intent()
  │
  ▼
refund_context_resolution_node → get_refund_context(db, customer_id, conversation_id, order_id)
  │
  ▼
refund_memory_retrieval_node  → build memory summary
  │
  ▼
refund_planner_node           → selected_workflow = "workflow_02_refund_return"
  │
  ▼
refund_order_node             → validate & load order
  │
  ▼
policy_rag_node               → select_relevant_policy_titles(policies)
  │
  ▼
refund_node                   → create RefundRequest(id=RF-xxx, status="pending")
  │
  ▼
evidence_node                 → evaluate_evidence(attachments)
  │
  ▼
risk_node                     → calculate_refund_risk(order_amount, evidence)
                                → risk_score < 70: "Approve review queue"
                                → risk_score ≥ 70: "Escalate for approval"
  │
  ▼
supervisor_node               → risk_score ≥ 70 → fallback_reason = "requires_human_approval"
  │
  ▼
ensure_case_node              → create Case(id=CS-xxx, type="refund_request")
  │
  ▼
approval_node                 → if risk_score ≥ 70: create Approval(id=APR-xxx, status="pending")
  │
  ▼
refund_support_response_node  → build customer response
  │
  ▼
refund_memory_write_node      → update memory
  │
  ▼
refund_logging_node           → log tool calls
  │
  ▼
persist_workflow_observability → save AgentTrace + ToolLogs → db.commit()
```

### Decision Logic

| Condition | Action |
|-----------|--------|
| `risk_score < 70` | Auto-approve to review queue |
| `risk_score ≥ 70` | Create Approval → Human review required |
| ไม่มี evidence | Risk score สูงขึ้น |
| `order_amount` สูง | Risk score สูงขึ้น |

### Risk Score Formula (`calculate_refund_risk`)

```python
# tools/refund.py
base_score = 40
if order_amount > 5000: base_score += 30
if not evidence or not evidence.get("has_evidence"): base_score += 20
if evidence.get("low_quality"): base_score += 10
# return 0-100
```

---

## 5.3 Workflow 03 — Proactive Delay Alert

**Trigger:** System event เมื่อ shipment ไม่มี update ≥ 48 ชั่วโมง  
**Implementation:** `app/agents/nodes/proactive_nodes.py` + `app/services/workflow_03_proactive.py`

### Node Pipeline

```
event_ingestion_node          → detect_proactive_event(event_type)
  │
  ▼
proactive_context_resolution_node → get_proactive_context(db, shipment_id)
  │
  ▼
proactive_shipping_node       → is_stale_update() + calculate_delay_risk(shipment)
                                → returns stale: bool, risk_score: int
  │
  ▼
proactive_policy_rag_node     → select_proactive_policy_titles(policies)
  │
  ▼
proactive_alert_node          → create ProactiveAlert(id=ALT-xxx, status="open")
                                → build_proactive_message(order_id, shipment_id, risk_score)
  │
  ▼
proactive_supervisor_node     → risk_score ≥ 80 → requires_human_approval
  │
  ▼
proactive_case_node           → create/load Case(id=CS-xxx)
  │
  ▼
proactive_approval_node       → if risk_score ≥ 80: create Approval
  │
  ▼
proactive_memory_write_node   → update state memory
  │
  ▼
proactive_logging_node        → log
  │
  ▼
persist_workflow_observability → save trace → db.commit()
```

### Risk Threshold

| Risk Score | Action |
|-----------|--------|
| < 80 | Auto-alert, no approval needed |
| ≥ 80 | Create Approval for compensation review |

---

## 5.4 Observability — ทุก Workflow

ทุก workflow สิ้นสุดด้วยการ persist ผ่าน `persist_workflow_observability()` ใน `app/services/observability.py`:

```python
persist_workflow_observability(db, state, workflow_name, case_id=case.id)
# สร้าง: AgentTrace + ToolLog (ทุก tool_log ใน state)
# อัปเดต: Conversation.latest_intent
# บันทึก: Message (customer) + Message (agent response)
```

---

# 6. Agentic AI Architecture

## 6.1 ReAct Loop Engine — หัวใจของ Agentic AI

**ReAct** = **Reasoning + Acting** — pattern ที่ทำให้ agent ไม่ทำงานแบบ linear แต่คิดก่อนทำ ลงมือทำ สังเกตผล และคิดใหม่ได้

### ReAct Cycle

```
THOUGHT  → Agent วิเคราะห์สถานการณ์และเลือก action ถัดไป
ACTION   → Agent เรียก tool หรือ sub-agent จริง
OBSERVE  → Agent รับผลลัพธ์จาก action
REFLECT  → Agent ประเมินว่าผลลัพธ์พอหรือยัง ถ้ายังไม่พอ → loop ซ้ำ
```

```
[Thought] → [Action] → [Observe] → [Reflect]
               ↑                        │
               └────────────────────────┘
                    (ถ้ายังไม่ครบ)
                           │ (Goal achieved)
                           ▼
                        [Finish]
```

### ReAct Implementation

```python
# agents/react_engine.py

class ReActEngine:
    MAX_ITERATIONS = 8

    async def run(self, state: AgentState) -> AgentState:
        iteration = 0
        while iteration < self.MAX_ITERATIONS:
            # THOUGHT — วิเคราะห์และเลือก action
            thought = await self.llm.think(state, prompt="What should I do next?")
            if thought.action == "FINISH":
                state.final_response = thought.answer
                break

            # ACTION — execute tool
            result = await self.tool_executor.run(
                tool=thought.action, params=thought.params
            )

            # OBSERVE — save observation to state
            state.observations.append({
                "iteration": iteration,
                "thought": thought.reasoning,
                "action": thought.action,
                "params": thought.params,
                "result": result,
            })

            # REFLECT — ประเมินว่าพอหรือยัง
            reflection = await self.llm.reflect(state)
            if reflection.goal_achieved:
                state.react_done = True
                break

            iteration += 1
        return state
```

### ตัวอย่าง ReAct ใน Refund Request

| Iteration | Thought | Action | Observe |
|-----------|---------|--------|---------|
| #1 | ต้องโหลดข้อมูลลูกค้าก่อน | `get_customer_profile()` | `customer_id = C001` |
| #2 | ต้องดู order ที่เกี่ยวข้อง | `get_order_detail("ORD-999")` | status = delivered |
| #3 | ต้องเช็ค policy | `search_policy("damaged item refund")` | 7-day return window |
| #4 | คำนวณ risk score | `calculate_risk_score("C001")` | risk = low, score = 0.2 |
| #5 | ข้อมูลครบ สามารถ approve ได้ | `create_refund_request()` | refund_id = REF-441 |
| Finish | ตอบลูกค้า | `send_response()` | Response sent |

---

## 6.2 Planning Layer — คิดก่อนทำ

Planning Layer ทำให้ agent สร้าง **execution plan** ก่อน execute เพื่อให้ workflow มีความชัดเจน ตรวจสอบได้ และปรับเปลี่ยนได้เมื่อสถานการณ์เปลี่ยน

### Planning Architecture

```
1. รับ Intent จาก Router Agent
2. Planner Agent วิเคราะห์และสร้าง step-by-step plan
3. Plan Validator ตรวจว่า plan feasible และ safe
4. Executor ทำตาม plan ทีละ step
5. Progress Tracker ติดตามสถานะของแต่ละ step
6. Replanner ปรับ plan ถ้า step fail หรือข้อมูลเปลี่ยน
```

### Plan Data Structure

```python
# models/plan.py

@dataclass
class ExecutionPlan:
    plan_id: str
    intent: str
    steps: List["PlanStep"]
    estimated_time: int      # seconds
    risk_level: str          # low | medium | high
    requires_approval: bool
    created_at: datetime

@dataclass
class PlanStep:
    step_id: int
    description: str
    agent: str               # agent ที่รับผิดชอบ
    tool: str                # tool ที่จะ call
    params: dict
    depends_on: List[int]    # step ที่ต้องเสร็จก่อน
    fallback: Optional[str]
    status: str              # pending | running | done | failed
    error: Optional[str] = None
```

### ตัวอย่าง Plan — Refund Workflow

| Step | Description | Agent | Tool | Depends On |
|------|-------------|-------|------|------------|
| 1 | โหลดข้อมูลลูกค้า | CustomerContextAgent | `get_customer_profile` | — |
| 2 | โหลดรายละเอียด order | OrderAgent | `get_order_detail` | Step 1 |
| 3 | ค้น policy ที่เกี่ยวข้อง | PolicyRAGAgent | `search_policy` | Step 2 |
| 4 | คำนวณ risk score | RiskAgent | `calculate_risk_score` | Step 2 |
| 5 | ตัดสินใจ approve / reject | SupervisorAgent | `evaluate_decision` | Step 3, 4 |
| 6 | ส่ง human approval ถ้า risk สูง | ApprovalAgent | `request_human_approval` | Step 5 |
| 7 | สร้าง refund request | RefundAgent | `create_refund_request` | Step 5 หรือ 6 |
| 8 | ตอบลูกค้าและบันทึก trace | ResponseAgent + TraceAgent | `send_response`, `log_trace` | Step 7 |

### Dynamic Replanning

```python
# planner/replanner.py

async def replan_if_needed(state: AgentState, failed_step: PlanStep):
    context = {
        "original_intent": state.intent,
        "completed_steps": state.plan.completed_steps(),
        "failed_step": failed_step,
        "failure_reason": failed_step.error,
        "available_tools": TOOL_REGISTRY.list(),
    }
    new_plan = await planner_llm.generate(context, prompt=REPLAN_PROMPT)
    if plan_validator.is_safe(new_plan):
        state.plan = new_plan
        state.replan_count += 1
        return state
    return escalate_to_human(state)
```

### สถานการณ์ที่ต้อง Replan

| สถานการณ์ | ตัวอย่าง | Action |
|-----------|---------|--------|
| Tool timeout | `get_order_detail` ไม่ตอบ | retry → fallback cache → replan |
| Policy ไม่เจอ | search แล้วไม่มี result | broaden query → escalate |
| Risk score สูง | ลูกค้ามี dispute history | เพิ่ม approval step |
| ข้อมูลขัดแย้งกัน | shipment = delivered แต่ customer ไม่ได้รับ | spawn investigation agent |
| Plan ช้าเกิน | หลาย tool fail ต่อเนื่อง | stop loop → human |

---

## 6.3 Memory System 3 ชั้น

Memory ทำให้ agent ไม่ใช่ระบบที่ "ลืมทุกอย่างหลังจบ request"

### Memory Types

| Memory Type | ข้อมูลที่เก็บ | Scope | Storage | TTL |
|-------------|--------------|-------|---------|-----|
| **Short-term** | session context, observations, tool results | 1 conversation | Redis | 24 ชั่วโมง |
| **Long-term** | customer behavior, decision history, preferences | per customer | PostgreSQL | Permanent |
| **Episodic** | fraud attempt, escalation, dispute, policy exception | per customer | PostgreSQL + Qdrant | Permanent |

### Short-term Memory (Redis)

```python
# memory/short_term.py

class ShortTermMemory:
    def __init__(self, session_id: str):
        self.key = f"session:{session_id}"
        self.ttl = 86400  # 24 hours

    async def save(self, key: str, value: Any):
        data = await redis.hgetall(self.key) or {}
        data[key] = json.dumps(value)
        await redis.hmset(self.key, data)
        await redis.expire(self.key, self.ttl)

    async def get(self, key: str) -> Any:
        val = await redis.hget(self.key, key)
        return json.loads(val) if val else None
```

**เก็บ:** intent ล่าสุด, order ที่กำลังถาม, tool results, observations, partial decision

### Long-term Memory (PostgreSQL)

```sql
-- Schema: customer_long_term_memory
CREATE TABLE customer_long_term_memory (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id  UUID NOT NULL REFERENCES customers(id),
    memory_type  VARCHAR(50),  -- behavior | preference | pattern
    key          VARCHAR(100),
    value        JSONB,
    confidence   FLOAT DEFAULT 1.0,
    source       VARCHAR(50),  -- agent ที่บันทึก
    updated_at   TIMESTAMPTZ DEFAULT NOW()
);
```

```json
// ตัวอย่างข้อมูล
{"memory_type": "behavior", "key": "refund_rate", "value": 0.12, "source": "RefundAgent"}
{"memory_type": "preference", "key": "preferred_lang", "value": "th", "source": "ResponseAgent"}
```

### Episodic Memory (PostgreSQL + Qdrant)

เก็บ "เหตุการณ์สำคัญ" ที่นำมาใช้ตัดสินใจในอนาคต: fraud attempt, refund abuse, escalation, delivery dispute, high-value complaint, policy exception

```python
# memory/episodic.py

class EpisodicMemory:
    async def store_episode(self, customer_id: str, event: dict):
        # 1. บันทึกใน PostgreSQL
        episode = await db.episodes.insert({...})

        # 2. Embed และบันทึกใน Qdrant สำหรับ semantic search
        embedding = await embedder.embed(str(event))
        await qdrant.upsert("episodes", points=[{
            "id": str(episode.id),
            "vector": embedding,
            "payload": {"customer_id": customer_id, **event}
        }])

    async def recall_similar(self, customer_id: str, current_context: str):
        embedding = await embedder.embed(current_context)
        return await qdrant.search(
            "episodes",
            query_vector=embedding,
            filter={"customer_id": customer_id},
            limit=5
        )
```

---

## 6.4 Error Recovery System — Self-Healing Agent

### Recovery Levels

| Level | เงื่อนไข | Action | Max Attempts |
|-------|---------|--------|--------------|
| **Level 1: Retry** | Tool timeout หรือ transient error | Exponential backoff | 3 ครั้ง |
| **Level 2: Fallback** | Retry ครบแล้วยัง fail | Alternative tool หรือ cache | 1 ครั้ง |
| **Level 3: Escalate** | Fallback fail หรือ risk สูง | Supervisor / Human | — |

### Error Recovery Implementation

```python
# tools/error_recovery.py

class ErrorRecoverySystem:
    FALLBACK_MAP = {
        "get_shipment_status":  "get_shipment_from_cache",
        "search_policy":        "use_policy_cache",
        "calculate_risk_score": "use_default_risk_medium",
        "get_order_detail":     "get_order_from_replica",
        "analyze_evidence_image": "manual_review_required",
    }

    async def execute_with_recovery(self, tool: str, params: dict) -> ToolResult:
        # Level 1: Retry with exponential backoff
        for attempt in range(1, 4):
            try:
                result = await tool_registry.run(tool, params)
                return ToolResult(success=True, data=result)
            except TransientError:
                await asyncio.sleep(2 ** attempt)  # 2s, 4s, 8s
            except FatalError:
                break

        # Level 2: Fallback
        fallback_tool = self.FALLBACK_MAP.get(tool)
        if fallback_tool:
            try:
                result = await tool_registry.run(fallback_tool, params)
                return ToolResult(success=True, data=result, used_fallback=True)
            except Exception:
                pass

        # Level 3: Escalate
        return ToolResult(success=False, escalate=True, reason=f"{tool} failed all recovery")
```

### Circuit Breaker Pattern

```python
# tools/circuit_breaker.py

class CircuitBreaker:
    # States: CLOSED (normal) → OPEN (blocking) → HALF_OPEN (testing)
    def __init__(self, tool_name: str, threshold: int = 5, timeout: int = 60):
        self.threshold = threshold  # ครั้งที่ fail ก่อน OPEN
        self.timeout = timeout      # วินาทีก่อน HALF_OPEN
        self.state = "CLOSED"
        self.fail_count = 0
```

---

## 6.5 Supervisor Agent — ผู้ควบคุม Agents ทั้งหมด

Supervisor Agent คือ meta-agent ที่ monitor agent อื่น ตรวจคุณภาพ ตัดสินใจ re-route และ escalate

### Supervisor Responsibilities

| หน้าที่ | Trigger | Action |
|--------|---------|--------|
| Monitor Progress | ทุก step ที่เสร็จ | ตรวจว่า agents ทำงานตามแผน |
| Detect Anomaly | timeout หรือ loop > 3 ครั้ง | หา agent ที่ stuck |
| Re-route | agent fail หรือ poor quality | เปลี่ยน agent / tool |
| Spawn Sub-agent | task ซับซ้อน | สร้าง agent ชั่วคราว |
| Quality Control | ก่อน ResponseAgent ส่ง | ตรวจ response quality |
| Escalate to Human | high risk หรือ ambiguous | ส่ง team ops |

### Supervisor Decision Rules

| Rule | Condition | Action |
|------|-----------|--------|
| High Risk | `risk_score > 0.7` | Require human approval |
| Too Many Replans | `replan_count >= 2` | Escalate |
| High Refund Amount | `refund_amount > 5000 THB` | Human approval |
| Fraud History | `has_fraud_history = true` | Escalate to fraud ops |
| Low Quality | `quality_score < 0.6` | Re-run weak agent |
| Conflicting Evidence | policy ขัดแย้งกับ order status | Resolve หรือ escalate |

### Implementation ใน Workflow

```python
# ปัจจุบัน: supervisor_node ใน refund_nodes.py
def supervisor_node(state, refund_request):
    requires_approval = refund_request.risk_score >= 70
    if requires_approval:
        state.fallback_reason = "requires_human_approval"
    return state

# เป้าหมาย: SupervisorAgent class
class SupervisorAgent:
    async def supervise(self, state: AgentState) -> AgentState:
        quality = await self.evaluate_quality(state)
        if quality.score < 0.6:
            state = await self.re_run_agent(state, quality.weak_agent)
        if self.requires_human(state):
            state.approval_required = True
        state.supervisor_approved = quality.score >= 0.6
        return state
```

---

## 6.6 Inter-Agent Communication Protocol

### Message Protocol

```python
# models/agent_message.py

@dataclass
class AgentMessage:
    message_id: str
    from_agent: str
    to_agent: str
    message_type: str       # request | response | event | error
    payload: dict
    priority: int = 5       # 1 = highest, 10 = lowest
    correlation_id: str = ""
    trace_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
```

### Agent Communication Flow

| Sender | Receiver | Message Type | เมื่อไหร่ |
|--------|----------|--------------|----------|
| RouterAgent | Supervisor | `request: assign_workflow` | รับ intent ใหม่ |
| Supervisor | CustomerContextAgent | `request: load_customer` | เริ่ม workflow |
| CustomerContextAgent | Supervisor | `response: customer_loaded` | โหลดเสร็จ |
| Supervisor | RiskAgent | `request: calculate_risk` | ก่อนตัดสินใจ refund |
| Supervisor | ApprovalAgent | `event: escalate_human` | risk > 0.7 |
| TraceAgent | All | `event: log_action` | ทุก action |

---

# 7. Full Observability System

## 7.1 Trace Schema (PostgreSQL)

```sql
CREATE TABLE agent_traces (
    id                   VARCHAR(100) PRIMARY KEY,
    conversation_id      VARCHAR(36) REFERENCES conversations(id),
    case_id              VARCHAR(50),
    workflow_name        VARCHAR(100),
    intent               VARCHAR(100),
    confidence           NUMERIC(5,4),
    status               VARCHAR(50),   -- completed | fallback | error
    requires_human_approval BOOLEAN DEFAULT FALSE,
    final_response       TEXT,
    state_snapshot       JSONB,         -- full state dump
    started_at           TIMESTAMP,
    ended_at             TIMESTAMP
);

CREATE TABLE tool_logs (
    id             VARCHAR(100) PRIMARY KEY,
    trace_id       VARCHAR(100) REFERENCES agent_traces(id),
    agent_name     VARCHAR(100),        -- node ที่เรียก
    tool_name      VARCHAR(100),        -- tool ที่ถูกเรียก
    input_payload  JSONB,
    output_payload JSONB,
    status         VARCHAR(50),         -- success | error
    latency_ms     INTEGER DEFAULT 0,
    error_message  TEXT,
    created_at     TIMESTAMP
);
```

## 7.2 Observability Flow

```python
# services/observability.py — persist_workflow_observability()

def persist_workflow_observability(db, state, workflow_name, *, case_id=None):
    trace = AgentTrace(
        id=trace_id,
        workflow_name=workflow_name,
        intent=state.detected_intent,
        status="completed" if not state.fallback_reason else "fallback",
        requires_human_approval=(state.fallback_reason == "requires_human_approval"),
        state_snapshot=state.model_dump(),
        ...
    )
    db.add(trace)

    for tool_entry in state.tool_logs:
        db.add(ToolLog(
            trace_id=trace_id,
            agent_name=tool_entry.get("node"),
            tool_name=tool_entry.get("tool"),
            ...
        ))

    # อัปเดต Conversation.latest_intent
    # บันทึก Message (customer + agent)
```

## 7.3 Metrics ที่ควร Track

| Metric | คำอธิบาย | Target |
|--------|---------|--------|
| `react_iterations_avg` | ReAct loop เฉลี่ยต่อ request | < 4 iterations |
| `replan_rate` | % request ที่ต้อง replan | < 10% |
| `tool_failure_rate` | % tool call ที่ fail | < 2% |
| `fallback_rate` | % ที่ต้องใช้ fallback tool | < 5% |
| `human_escalation_rate` | % ที่ escalate to human | < 15% |
| `memory_hit_rate` | % ที่ long-term memory มีประโยชน์ | > 60% |
| `response_time_p95` | 95th percentile response time | < 8 วินาที |
| `supervisor_intervention_rate` | % ที่ Supervisor ต้อง intervene | < 20% |

## 7.4 ตัวอย่าง Trace Event

```json
{
  "id": "TRACE-ABC123456789",
  "workflow_name": "workflow_02_refund_return",
  "intent": "refund_request",
  "confidence": 0.95,
  "status": "fallback",
  "requires_human_approval": true,
  "state_snapshot": {
    "customer_id": "cust-001",
    "risk_score": 75,
    "fallback_reason": "requires_human_approval"
  },
  "tool_logs": [
    {"node": "router_node", "tool": "detect_refund_intent"},
    {"node": "risk_node", "tool": "calculate_refund_risk", "risk_score": 75},
    {"node": "supervisor_node", "tool": "determine_human_review", "requires_approval": true}
  ]
}
```

---

# 8. Frontend — 3 Portals

## ภาพรวม

| Portal | Path | Role | ไฟล์หลัก |
|--------|------|------|---------|
| Customer | `/customer` | customer | `CustomerPortal.tsx` |
| Admin | `/admin` | admin | `AdminPortal.tsx` |
| AI Control | `/ai-control` | ai-engineer | `AiControlPortal.tsx` |

Auth ใช้ Mock Login (`POST /auth/mock-login`) → เก็บ session ใน `localStorage` → `readSession()` ใน `lib/session.ts`

```tsx
// App.tsx — ProtectedRoute
function ProtectedRoute({ allow, children }: { allow: Role[]; children: ReactNode }) {
  const session = readSession()
  if (!session || !allow.includes(session.role)) {
    return <Navigate to="/" replace />
  }
  return children
}
```

## 8.1 Customer Portal (`/customer`)

### Navigation Tabs

| Tab Key | Label | Icon | Feature |
|---------|-------|------|---------|
| `home` | หน้าหลัก | ⌂ | Overview |
| `assistant` | แชตกับ AI | ✦ | Real-time chat + history |
| `orders` | คำสั่งซื้อของฉัน | ▣ | Order list + status |
| `shipments` | การจัดส่งของฉัน | ◎ | Shipment tracking |
| `refund` | คืนเงิน / คืนสินค้า | ◌ | Refund request + evidence upload |
| `alerts` | การแจ้งเตือน | ◔ | Proactive alerts |
| `help` | ศูนย์ช่วยเหลือ | ? | FAQ |

### Key Features

- **AI Chat** — ส่งข้อความ → POST `/chat` → รับ response + shipment cards
- **Evidence Upload** — presign upload URL → PUT to MinIO → confirm metadata
- **Shipment Status** — labels: กำลังนำส่ง / อยู่ระหว่างขนส่ง / สำเร็จ / ล่าช้า
- **Order Status** — labels: กำลังจัดเตรียม / สำเร็จ / ยกเลิกแล้ว

## 8.2 Admin Portal (`/admin`)

### Features

- **Case Queue** — รายการ cases ทั้งหมด พร้อม priority และ status
- **Case Detail** — ดู approvals, refund requests, attachments ใน case เดียว
- **Approval Workflow** — Approve / Reject พร้อม review note
- **Proactive Alerts** — ดูและ resolve delay alerts
- **Refund Queue** — จัดการ refund requests

## 8.3 AI Control Portal (`/ai-control`)

### Features (MVP)

- **Agent Traces** — รายการ workflow executions พร้อม filter (workflow, status, intent)
- **Trace Detail** — ดู state snapshot, tool_logs, business context
- **Tool Logs** — Debug tool call ทุกครั้ง
- **Policy RAG** — Test semantic search (Placeholder — Qdrant ยังไม่ implement)

### API Client (`lib/api.ts`)

```typescript
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api/v1'

// ฟังก์ชันหลัก
api.chat(payload)                    // POST /chat
api.getAgentTraces(filters)          // GET /ai/agent-traces
api.getAgentTraceDetail(traceId)     // GET /ai/agent-traces/{id}
api.approveApproval(id, note)        // POST /admin/approvals/{id}/approve
api.rejectApproval(id, note)         // POST /admin/approvals/{id}/reject
api.presignUpload(req)               // POST /attachments/presign-upload
api.confirmUpload(req)               // POST /attachments/confirm-upload
api.triggerProactiveDelay(payload)   // POST /events/proactive-delay
```

---

# 9. MinIO File Storage

## Upload Flow

```
1. Customer เลือกไฟล์ใน frontend
2. POST /attachments/presign-upload → backend generate object_key + presigned URL
3. Frontend PUT file ไปที่ MinIO URL โดยตรง (ไม่ผ่าน backend)
4. POST /attachments/confirm-upload → backend save metadata ลง PostgreSQL
5. Admin GET /attachments/{id}/presign-download → presigned download URL (TTL 24h)
```

## Object Key Format

```
refund_request/{refund_id}/{evidence_group}/{sequence}_{filename}

ตัวอย่าง:
refund_request/RF-5521/damaged_item/01_front-crack.jpg
refund_request/RF-5521/parcel_package/02_box-damaged.jpg
refund_request/RF-5521/unboxing_video/04_unboxing.mp4
```

## Evidence Categories

| Category | ใช้สำหรับ |
|----------|---------|
| `damaged_item` | สินค้าเสียหาย |
| `missing_item` | สินค้าขาดหาย |
| `wrong_item` | ส่งสินค้าผิด |
| `parcel_package` | กล่องพัสดุเสียหาย |
| `parcel_label` | ป้ายจัดส่ง |
| `receipt` | ใบเสร็จ |
| `unboxing_video` | วิดีโอแกะกล่อง |
| `customer_note` | หมายเหตุลูกค้า |
| `admin_note` | หมายเหตุ admin |
| `policy_document` | เอกสาร policy |
| `other` | อื่น ๆ |

## MinIO Service (`storage/minio.py`)

```python
minio_client = Minio(
    settings.minio_endpoint,          # minio:9000 (docker) / localhost:9000 (local)
    access_key=settings.minio_access_key,
    secret_key=settings.minio_secret_key,
    secure=settings.minio_use_ssl,    # False สำหรับ local
)

generate_presigned_upload_url(object_name, expiration_hours=1)
generate_presigned_download_url(object_name, expiration_hours=24)
remove_object(object_name)
```

---

# 10. Infrastructure & Deployment

## Local Development (Docker Compose)

```bash
# เริ่มทุก service
docker compose up --build

# Environment variables (docker-compose.yml)
DATABASE_URL=postgresql+psycopg://LLM-project-shopeasy:LLm-260346@db:5432/shopeasy
REDIS_HOST=redis
REDIS_PORT=6379
MINIO_ENDPOINT=minio:9000
MINIO_BUCKET_NAME=evidence

# Ports
PostgreSQL: localhost:5433  (mapped from 5432)
Backend:    localhost:8000
Frontend:   localhost:5173
MinIO API:  localhost:9000
MinIO UI:   localhost:9001
Redis:      localhost:6379
```

## Database Setup

```bash
# Run migrations
alembic upgrade head

# Seed data
python -m app.db.seeds.run_all_seeds      # ทั้งหมด
python -m app.db.seeds.run_workflow_01_seed  # Tracking seed
python -m app.db.seeds.run_workflow_02_seed  # Refund seed
python -m app.db.seeds.run_workflow_03_seed  # Proactive seed
```

## Production Deployment Options

| Option | Service | Suitable For |
|--------|---------|-------------|
| **Cloud-Native** | Vercel (FE) + Render/Railway (BE) + Supabase (DB) + Upstash (Redis) + MinIO (Railway) | MVP / Demo |
| **Self-Hosted** | Docker Compose บน VPS (DigitalOcean / Hetzner / Vultr) | Production |

---

# 11. Project Structure

```
ShopEasy/
│
├── docker-compose.yml                    # Multi-service orchestration
├── DocProject.MD                         # Project blueprint (ต้นฉบับ)
├── ShopEasy_Agentic_Architecture_Detailed.md  # Agentic design doc (ต้นฉบับ)
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt                  # fastapi, uvicorn, sqlalchemy, langgraph, minio...
│   ├── alembic.ini
│   │
│   ├── alembic/
│   │   └── versions/
│   │       ├── 488c75bf3411_init_schema.py
│   │       └── 4b5bb6c546ab_add_admin_notes_fields.py
│   │
│   └── app/
│       ├── main.py                       # FastAPI app + CORS + router
│       │
│       ├── api/
│       │   ├── router.py                 # api_router รวม routes ทั้งหมด
│       │   ├── deps.py                   # get_db() dependency
│       │   └── routes/
│       │       ├── auth.py               # /auth — mock-login, me
│       │       ├── chat.py               # /chat — POST
│       │       ├── customer.py           # /data — orders, shipments, etc.
│       │       ├── admin.py              # /admin — cases, approvals
│       │       ├── attachments.py        # /attachments — MinIO upload
│       │       ├── observability.py      # /ai — traces, tool-logs
│       │       ├── proactive.py          # /events — proactive-delay
│       │       └── health.py             # /health
│       │
│       ├── agents/
│       │   ├── state.py                  # GraphState, TrackingWorkflowState
│       │   ├── graph.py                  # create_tracking_workflow() — LangGraph
│       │   ├── nodes/
│       │   │   ├── tracking_nodes.py     # Workflow 01 nodes
│       │   │   ├── refund_nodes.py       # Workflow 02 nodes
│       │   │   └── proactive_nodes.py    # Workflow 03 nodes
│       │   └── tools/
│       │       ├── tracking.py           # detect intent, build summaries
│       │       ├── refund.py             # refund intent, risk, evidence
│       │       └── proactive.py          # delay risk, proactive message
│       │
│       ├── services/
│       │   ├── chat.py                   # handle_chat() — intent routing
│       │   ├── workflow_01_tracking.py   # handle_tracking_chat()
│       │   ├── workflow_02_refund.py     # handle_refund_chat()
│       │   ├── workflow_03_proactive.py  # handle_proactive_event()
│       │   ├── observability.py          # persist_workflow_observability()
│       │   └── admin_actions.py          # approve/reject/close
│       │
│       ├── db/
│       │   ├── base.py                   # Base, TimestampMixin
│       │   ├── session.py                # SessionLocal, get_db
│       │   ├── init_db.py
│       │   ├── bootstrap_dev.py
│       │   ├── models/
│       │   │   ├── customer.py           # User, Customer, Seller
│       │   │   ├── order.py              # Order, OrderItem, Shipment, ShipmentItem, ShipmentEvent
│       │   │   ├── refund.py             # Case, Approval, RefundRequest, Attachment, ProactiveAlert
│       │   │   └── conversation.py       # Conversation, Message, AgentTrace, ToolLog
│       │   └── seeds/
│       │       ├── run_all_seeds.py
│       │       ├── workflow_01_tracking_seed.py
│       │       ├── workflow_02_refund_seed.py
│       │       └── workflow_03_proactive_seed.py
│       │
│       ├── repositories/
│       │   ├── tracking.py               # get_tracking_context()
│       │   ├── refund.py                 # get_refund_context()
│       │   ├── proactive.py              # get_proactive_context()
│       │   ├── admin.py                  # list_cases, list_approvals
│       │   ├── observability.py          # list_agent_traces, get_agent_trace
│       │   └── business.py               # get_user_by_username
│       │
│       ├── schemas/
│       │   ├── chat.py                   # ChatRequest, ChatResponse, ShipmentSummary
│       │   ├── admin.py                  # CaseSummary, ApprovalResponse, etc.
│       │   ├── observability.py          # AgentTraceSummary, ToolLogResponse
│       │   ├── proactive.py              # ProactiveEventRequest/Response
│       │   ├── auth.py                   # MockLoginRequest/Response
│       │   └── business.py               # UserResponse
│       │
│       └── storage/
│           └── minio.py                  # MinIO client + presigned URLs
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   ├── index.html
│   │
│   └── src/
│       ├── App.tsx                       # Routes + ProtectedRoute
│       ├── main.tsx
│       ├── styles.css
│       │
│       ├── lib/
│       │   ├── api.ts                    # API client ทั้งหมด
│       │   └── session.ts                # localStorage session
│       │
│       ├── types/
│       │   └── api.ts                    # TypeScript types
│       │
│       ├── components/
│       │   ├── PortalShell.tsx
│       │   ├── Sidebar.tsx
│       │   ├── StatCard.tsx
│       │   └── Surface.tsx
│       │
│       └── pages/
│           ├── LoginPage.tsx
│           ├── customer/
│           │   └── CustomerPortal.tsx    # All customer tabs
│           ├── admin/
│           │   └── AdminPortal.tsx       # All admin tabs
│           └── ai/
│               └── AiControlPortal.tsx   # Traces + tool logs
│
└── docs/
    └── planning/
        ├── workflow.md
        ├── langgraph_nodes.md
        ├── db_schema_alignment.md
        └── mock_data_plan.md
```

---

# 12. Implementation Roadmap

## สถานะปัจจุบัน (7 พฤษภาคม 2026)

| Component | สถานะ | หมายเหตุ |
|-----------|-------|---------|
| Docker Compose + Services | ✅ Complete | db, backend, frontend, redis, minio |
| PostgreSQL Schema + Alembic | ✅ Complete | 2 migrations, all tables |
| Seed Data (3 workflows) | ✅ Complete | Mock data สำหรับทุก workflow |
| FastAPI Backend Structure | ✅ Complete | 8 route groups |
| Auth (Mock) | ✅ Complete | 3 roles: customer, admin, ai_control |
| MinIO Integration | ✅ Complete | presign upload + download |
| Workflow 01 — Tracking | ✅ Complete | LangGraph StateGraph |
| Workflow 02 — Refund | ✅ Complete | Sequential node pipeline |
| Workflow 03 — Proactive | ✅ Complete | Event-driven pipeline |
| Observability (Trace + ToolLog) | ✅ Complete | persist per workflow |
| Admin Actions (Approve/Reject) | ✅ Complete | |
| Frontend — 3 Portals | ✅ Complete | Customer, Admin, AI Control |
| Qdrant Policy RAG | 🔲 Not Started | Placeholder ใน codebase |
| ReAct Loop Engine | 🔲 Planned | Design documented |
| Planning Layer | 🔲 Planned | Design documented |
| 3-Layer Memory | 🔲 Planned | Redis partial (structure defined) |
| Error Recovery + Circuit Breaker | 🔲 Planned | Design documented |
| Supervisor Agent (Full) | 🔲 Planned | supervisor_node มีแล้ว (basic) |

## Sprint Plan (Agentic Upgrades)

| Sprint | ระยะเวลา | สิ่งที่ทำ | Deliverable |
|--------|---------|---------|-------------|
| **Sprint 1** | 1–2 สัปดาห์ | Memory System (Short-term + Long-term) | Redis session memory, `customer_long_term_memory` table |
| **Sprint 2** | 2–3 สัปดาห์ | ReAct Loop Engine | `ReActEngine` class, observation logging ใน LangGraph |
| **Sprint 3** | 2 สัปดาห์ | Planning Layer + Supervisor Agent (Full) | `ExecutionPlan` model, Supervisor node ใน LangGraph |
| **Sprint 4** | 1–2 สัปดาห์ | Error Recovery + Episodic Memory + Qdrant | `CircuitBreaker`, episode table, Policy RAG |

## Priority Order

1. **ReAct Loop** — impact สูงสุด เปลี่ยน core architecture ให้ agentic จริง
2. **Error Recovery** — ทำให้ระบบ stable ก่อน scale
3. **Memory System** — ทำให้ agent จำและเรียนรู้จาก customer pattern
4. **Planning Layer** — เพิ่ม transparency และ control
5. **Supervisor Agent (Full)** — meta-layer สำหรับ production reliability
6. **Qdrant Policy RAG** — Policy-grounded decisions

## Minimal Implementation Checklist

### Phase 1: Core Agentic Execution (ReAct)
- [ ] Create `AgentState` v2 พร้อม `observations` field
- [ ] Implement `ReActEngine` class
- [ ] Add tool executor wrapper
- [ ] Add trace logging ต่อ iteration
- [ ] Integrate ReAct into LangGraph node

### Phase 2: Memory System
- [ ] Implement `ShortTermMemory` (Redis)
- [ ] Create `customer_long_term_memory` migration
- [ ] Implement `LongTermMemory` service
- [ ] Add `memory_init_node` ใน graph
- [ ] Add `memory_update_node` ใน graph

### Phase 3: Planning Layer
- [ ] Create `ExecutionPlan` + `PlanStep` dataclass
- [ ] Implement `PlannerAgent`
- [ ] Implement `PlanValidator`
- [ ] Add replanner logic
- [ ] Add plan status tracking ใน trace

### Phase 4: Error Recovery & Production Safety
- [ ] Implement `ErrorRecoverySystem`
- [ ] Implement `CircuitBreaker`
- [ ] Define fallback map ต่อ tool
- [ ] Upgrade Supervisor quality gate
- [ ] Add observability metrics (Grafana-ready)

### Phase 5: Policy RAG (Qdrant)
- [ ] Setup Qdrant service ใน docker-compose
- [ ] Ingestion pipeline (PostgreSQL → chunks → embeddings → Qdrant)
- [ ] `search_policy()` tool ที่ใช้ vector search
- [ ] Policy RAG UI ใน AI Control Portal

---

# 13. Agentic AI Checklist

| Agentic Capability | Component | สถานะ | ส่งผลต่อ |
|-------------------|-----------|-------|---------|
| Dynamic reasoning ไม่ hardcode flow | ReAct Loop Engine | 🔲 Planned | Core intelligence |
| Plan before execute | Planning Layer + Validator | 🔲 Planned | Predictability |
| Self-correction on failure | Error Recovery + Circuit Breaker | 🔲 Planned | Reliability |
| Short-term memory | Redis Session Memory | 🔲 Planned | Context awareness |
| Long-term memory | PostgreSQL Customer Memory | 🔲 Planned | Personalization |
| Episodic memory | PostgreSQL + Qdrant Episodes | 🔲 Planned | Risk & fraud detection |
| Inter-agent communication | AgentMessage Protocol | 🔲 Planned | Debuggability |
| Meta-agent supervision | Supervisor Agent (Full) | 🟡 Partial | Quality & safety |
| Dynamic agent spawning | Supervisor `spawn()` | 🔲 Planned | Scalability |
| Tool calling | Tool Registry (tracking/refund/proactive) | ✅ Done | Execution power |
| Human-in-the-loop | Approval Agent + Admin Portal | ✅ Done | Safety & control |
| Policy-grounded decisions | Policy RAG (Qdrant) | 🔲 Planned | Accuracy & compliance |
| Full observability | AgentTrace + ToolLog + AI Control Portal | ✅ Done | Monitoring |
| Workflow orchestration | LangGraph (3 workflows) | ✅ Done | Multi-step execution |
| Evidence management | MinIO + Attachments | ✅ Done | Refund evidence |
| Event-driven processing | Proactive delay workflow | ✅ Done | Proactive support |

---

## Out of Scope (MVP)

```
- LINE OA integration (mock instead)
- Real payment API (mock instead)
- Carrier API integration (mock instead)
- Production JWT authentication (mock login)
- Kubernetes orchestration
- Multi-tenant support
- Advanced fraud detection models
- Image recognition pipeline
- Complex evaluation dashboards
- Advanced prompt versioning
```

---

> **ShopEasy** ไม่ใช่แค่ chatbot แต่เป็นระบบ **AI Operations Platform** ที่สามารถคิด วางแผน ใช้เครื่องมือ จำข้อมูล แก้ปัญหา และตรวจคุณภาพตัวเองได้ พร้อมรองรับ Human-in-the-Loop สำหรับ high-risk decisions และ Full Observability สำหรับทุก action ที่เกิดขึ้น
