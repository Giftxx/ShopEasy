# ShopEasy — Project Overview & Roadmap
> เวอร์ชัน: พฤษภาคม 2026 | Branch: `final-shop`  
> ครอบคลุมทุกส่วน: Architecture · DB · AI Pipeline · Frontend · API · Roadmap

---

## สารบัญ

1. [ภาพรวมระบบ (High-Level)](#1-ภาพรวมระบบ)
2. [Tech Stack](#2-tech-stack)
3. [โครงสร้างโปรเจกต์](#3-โครงสร้างโปรเจกต์)
4. [Database Schema](#4-database-schema)
5. [Backend — Service Layer](#5-backend--service-layer)
6. [AI Pipeline (LangGraph)](#6-ai-pipeline-langgraph)
7. [Policy RAG System](#7-policy-rag-system)
8. [Frontend — 3 Portals](#8-frontend--3-portals)
9. [API Endpoints](#9-api-endpoints)
10. [Docker Services](#10-docker-services)
11. [Git Branches & Commit History](#11-git-branches--commit-history)
12. [สิ่งที่ทำงานแล้ว (Done ✅)](#12-สิ่งที่ทำงานแล้ว-done-)
13. [Roadmap — สิ่งที่ต้องทำต่อ (WOW Features)](#13-roadmap--สิ่งที่ต้องทำต่อ-wow-features)

---

## 1. ภาพรวมระบบ

ShopEasy คือแพลตฟอร์ม E-Commerce ที่มี **Agentic AI Customer Support** ฝังอยู่ในตัว ลูกค้าไม่ต้องรอ agent มนุษย์ — AI จัดการได้ทุก workflow อัตโนมัติ

```mermaid
graph TB
    C([👤 Customer]) -->|"ถามผ่าน Chat"| FE[React Frontend]
    FE -->|"POST /api/v1/chat"| API[FastAPI Backend]
    API -->|"classify intent"| LLM[Ollama / qwen2.5]
    LLM -->|"intent"| ROUTER{Intent Router}

    ROUTER -->|"track_shipment"| WF1[Workflow 01\nTracking LangGraph]
    ROUTER -->|"refund_request"| WF2[Workflow 02\nRefund Handler]
    ROUTER -->|"policy_question"| RAG[Policy RAG\nQdrant + PostgreSQL]
    ROUTER -->|"greeting"| GREET[Fast Path\nno LLM needed]
    ROUTER -->|"general_inquiry"| WF3[Fallback Node\nGeneral LLM]

    WF1 -->|"query"| PG[(PostgreSQL)]
    WF2 -->|"query"| PG
    RAG -->|"vector search"| QD[(Qdrant)]
    RAG -->|"keyword search"| PG

    WF1 -->|"response"| API
    WF2 -->|"response"| API
    RAG -->|"response"| API
    GREET -->|"response"| API
    WF3 -->|"response"| API

    API -->|"result"| FE
    FE -->|"แสดงผล"| C

    ADMIN([👨‍💼 Admin]) -->|"จัดการ"| FE
    AIENGINEER([🤖 AI Engineer]) -->|"ดู Trace / Metrics"| FE

    style ROUTER fill:#f4a261,color:#000
    style RAG fill:#2a9d8f,color:#fff
    style LLM fill:#e76f51,color:#fff
    style PG fill:#264653,color:#fff
    style QD fill:#457b9d,color:#fff
```

---

## 2. Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| **Frontend** | React 18 + TypeScript + Vite | SPA, Tailwind-like custom CSS |
| **Backend** | FastAPI + Python 3.11 | Async-ready, Pydantic v2 |
| **ORM** | SQLAlchemy 2.0 + Alembic | Type-safe models, migrations |
| **Database** | PostgreSQL 16 | Main data store |
| **Vector DB** | Qdrant | Policy RAG embeddings |
| **Object Storage** | MinIO | Policy PDF files |
| **Cache / Queue** | Redis | Session, rate limit |
| **AI Orchestration** | LangGraph | Stateful multi-node graph |
| **LLM** | Ollama (qwen2.5:1.5b) | Local CPU inference |
| **Embeddings** | Ollama (nomic-embed-text) | For Qdrant vector search |
| **Container** | Docker Compose | 6-service stack |
| **Auth** | JWT (python-jose) | Role-based: customer / admin / ai_engineer |

---

## 3. โครงสร้างโปรเจกต์

```
ShopEasy/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI entry point
│   │   ├── agents/                  # AI Agent layer
│   │   │   ├── graph.py             # LangGraph workflow definition
│   │   │   ├── llm.py               # LLM client + System Prompts
│   │   │   ├── state.py             # GraphState TypedDict
│   │   │   ├── nodes/
│   │   │   │   └── tracking_nodes.py  # All LangGraph nodes
│   │   │   ├── tools/
│   │   │   │   ├── tracking.py      # Tracking helper functions
│   │   │   │   ├── refund.py        # Refund + intent detection
│   │   │   │   └── proactive.py     # Proactive alert tools
│   │   │   └── memory/
│   │   │       ├── short_term.py    # Redis-based session memory
│   │   │       └── long_term.py     # DB-based customer memory
│   │   ├── api/
│   │   │   ├── router.py            # API route registration
│   │   │   └── routes/              # Endpoint handlers
│   │   ├── services/
│   │   │   ├── chat.py              # Main chat handler + intent router
│   │   │   ├── policy_rag.py        # RAG search (hybrid vector+keyword)
│   │   │   ├── workflow_01_tracking.py
│   │   │   └── workflow_02_refund.py
│   │   ├── db/
│   │   │   ├── models/              # SQLAlchemy models
│   │   │   └── seeds/               # Demo data
│   │   └── repositories/            # DB query layer
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── customer/CustomerPortal.tsx
│       │   ├── admin/AdminPortal.tsx
│       │   └── ai/AiControlPortal.tsx
│       └── components/
├── docker-compose.yml
└── docs/
```

---

## 4. Database Schema

```mermaid
erDiagram
    USERS {
        string id PK
        string name
        string email
        string role
        string hashed_password
    }
    CUSTOMERS {
        string id PK
        string user_id FK
        string name
        string tier
        string preferred_language
    }
    SELLERS {
        string id PK
        string name
    }
    ORDERS {
        string id PK
        string customer_id FK
        string seller_id FK
        string order_status
        float total_amount
        string currency
        date promised_delivery_date
    }
    ORDER_ITEMS {
        string id PK
        string order_id FK
        string product_name
        int quantity
        float unit_price
    }
    SHIPMENTS {
        string id PK
        string order_id FK
        string carrier
        string tracking_number
        string shipment_status
        string note
    }
    CONVERSATIONS {
        string id PK
        string customer_id FK
        string channel
        string status
        string latest_intent
    }
    MESSAGES {
        string id PK
        string conversation_id FK
        string role
        string content
    }
    REFUND_REQUESTS {
        string id PK
        string order_id FK
        string customer_id FK
        string status
        string reason
        float amount_requested
    }
    CASES {
        string id PK
        string customer_id FK
        string order_id FK
        string case_type
        string status
        string admin_notes
    }
    PROACTIVE_ALERTS {
        string id PK
        string customer_id FK
        string order_id FK
        string alert_type
        float risk_score
        string status
        string case_id FK
    }
    POLICIES {
        string id PK
        string title
        string status
        string file_url
    }
    POLICY_CHUNKS {
        string id PK
        string policy_id FK
        string heading
        text chunk_text
        int chunk_index
        string qdrant_point_id
    }
    WORKFLOW_TRACES {
        string id PK
        string conversation_id FK
        string detected_intent
        string selected_workflow
        string response_text
    }

    USERS ||--o| CUSTOMERS : "has profile"
    CUSTOMERS ||--o{ ORDERS : "places"
    SELLERS ||--o{ ORDERS : "receives"
    ORDERS ||--o{ ORDER_ITEMS : "contains"
    ORDERS ||--o{ SHIPMENTS : "has"
    CUSTOMERS ||--o{ CONVERSATIONS : "opens"
    CONVERSATIONS ||--o{ MESSAGES : "has"
    ORDERS ||--o| REFUND_REQUESTS : "may have"
    CUSTOMERS ||--o{ PROACTIVE_ALERTS : "receives"
    PROACTIVE_ALERTS ||--o| CASES : "linked to"
    POLICIES ||--o{ POLICY_CHUNKS : "split into"
```

---

## 5. Backend — Service Layer

```mermaid
flowchart LR
    REQ[HTTP Request] --> AUTH[JWT Auth Middleware]
    AUTH --> ROUTE[API Router]
    ROUTE --> CHAT[chat.py\nhandle_chat]
    ROUTE --> DATA[data routes\ncustomer data]
    ROUTE --> ADMIN[admin routes\napproval, cases]
    ROUTE --> POLICY[policy routes\nupload, list]

    CHAT --> INTENT{Intent}
    INTENT -->|greeting| FAST[Fast Response\nno LLM]
    INTENT -->|policy_question| RAG_SVC[policy_rag.py]
    INTENT -->|refund_request| REFUND[workflow_02_refund.py]
    INTENT -->|track_shipment\ngeneral_inquiry| GRAPH[workflow_01_tracking.py\n→ LangGraph]

    RAG_SVC --> QDRANT[(Qdrant)]
    RAG_SVC --> PGDB[(PostgreSQL)]
    REFUND --> PGDB
    GRAPH --> PGDB

    GRAPH --> OBS[observability.py\nWorkflow Trace]
    OBS --> PGDB
```

---

## 6. AI Pipeline (LangGraph)

LangGraph คือ state machine ที่ควบคุมการทำงานของ AI nodes แต่ละตัว:

```mermaid
stateDiagram-v2
    [*] --> router_node : รับ message

    router_node --> get_context : ทุก intent
    note right of router_node
        classify_intent()
        keyword-first → LLM fallback
    end note

    get_context --> get_memory : โหลด orders, shipments, refunds, alerts
    note right of get_context
        get_tracking_context()
        ALL_SHIPMENT_STATUSES
    end note

    get_memory --> tracking_branch : intent = track_shipment
    get_memory --> fallback_branch : intent = general_inquiry

    state tracking_branch {
        plan_node --> shipping_node
        shipping_node --> support_response_node
        note right of support_response_node
            STATUS_FILTERS (5 statuses)
            STATUS_LABEL (Thai names)
            RAG policy search
        end note
    }

    state fallback_branch {
        fallback_node : build full context\n+ RAG search\n+ call_llm(GENERAL_SYSTEM_PROMPT)
    }

    tracking_branch --> write_memory
    fallback_branch --> write_memory
    write_memory --> [*] : return customer_response
```

### Intent Classification

```mermaid
flowchart TD
    MSG[ข้อความลูกค้า] --> GREET_CHECK{Pure Greeting?}
    GREET_CHECK -->|YES| FAST_RESP[ตอบทันที\nไม่เรียก LLM]
    GREET_CHECK -->|NO| POLICY_KW{มีคำว่า\nนโยบาย/เงื่อนไข/\nกี่วัน/รับประกัน?}

    POLICY_KW -->|YES| POLICY_Q[policy_question]
    POLICY_KW -->|NO| REFUND_KW{มีคำว่า\nคืนเงิน/ขอคืน/\nยกเลิก?}
    REFUND_KW -->|YES| REFUND_Q[refund_request]
    REFUND_KW -->|NO| TRACK_KW{มีคำว่า\nออเดอร์/พัสดุ/\nSP-/KRY-?}
    TRACK_KW -->|YES| TRACK_Q[track_shipment]
    TRACK_KW -->|NO| LLM_CLS[LLM classify\nqwen2.5:1.5b]
    LLM_CLS --> FINAL[general_inquiry]

    POLICY_Q --> POLICY_RAG[_handle_policy_chat]
    REFUND_Q --> REFUND_WF[handle_refund_chat]
    TRACK_Q --> TRACKING_WF[LangGraph\nWorkflow 01]
    FINAL --> TRACKING_WF
```

---

## 7. Policy RAG System

```mermaid
flowchart TD
    UPLOAD[Admin อัปโหลด PDF] --> EXTRACT[pdf_extractor.py\nแยกข้อความ + chunks]
    EXTRACT --> EMBED[Ollama\nnomic-embed-text\nสร้าง vector]
    EMBED --> QDRANT[(Qdrant\npolicy_chunks collection)]
    EXTRACT --> PG_CHUNK[(PostgreSQL\npolicy_chunks table)]

    QUERY[ลูกค้าถาม\n"นโยบายคืนเงิน"] --> TOKENIZE[_tokenize_query()\nตัดคำ Thai + stopwords]
    TOKENIZE --> HYBRID{Hybrid Search}

    HYBRID -->|vector search| QDRANT
    HYBRID -->|keyword ILIKE| PG_CHUNK
    QDRANT --> MERGE[Deduplicate\nby policy_id + chunk_index]
    PG_CHUNK --> MERGE
    MERGE --> LLM_RAG[call_llm()\nqwen2.5 + context]
    LLM_RAG --> RESP[ตอบลูกค้า\nอ้างอิงนโยบายจริง]

    style QDRANT fill:#457b9d,color:#fff
    style PG_CHUNK fill:#264653,color:#fff
```

### Tokenizer Logic

ปัญหาภาษาไทย: ไม่มี word space → ต้องตัดคำเอง

```python
# ตัวอย่าง: "นโยบายการคืนเงินคือ"
_tokenize_query() →
  strip stopwords: ["นโยบาย", "คือ"]
  remaining: ["การคืนเงิน", "คืนเงิน"]
  search ILIKE: %การคืนเงิน%, %คืนเงิน%
```

---

## 8. Frontend — 3 Portals

```mermaid
graph LR
    LOGIN[LoginPage.tsx] -->|role=customer| CP[CustomerPortal.tsx]
    LOGIN -->|role=admin| AP[AdminPortal.tsx]
    LOGIN -->|role=ai_engineer| AIP[AiControlPortal.tsx]

    subgraph CP [Customer Portal]
        C1[💬 AI Chat]
        C2[📦 Orders]
        C3[🚚 Shipments]
        C4[💰 Refunds]
        C5[🔔 Alerts]
    end

    subgraph AP [Admin Portal]
        A1[📋 Cases]
        A2[👥 Customers]
        A3[💰 Refund Approval]
        A4[🔔 Proactive Alerts]
        A5[📄 Policies Upload]
        A6[📊 Observability]
    end

    subgraph AIP [AI Control Portal]
        AI1[🔬 RAG Testing]
        AI2[📈 Metrics]
        AI3[🔍 Workflow Traces]
        AI4[⚡ Agent Config]
    end
```

### Customer Portal — Chat Flow

```mermaid
sequenceDiagram
    actor Customer
    participant UI as React UI
    participant API as FastAPI
    participant LLM as Ollama LLM
    participant DB as PostgreSQL
    participant QD as Qdrant

    Customer->>UI: พิมพ์ข้อความ
    UI->>API: POST /api/v1/chat
    API->>API: _is_pure_greeting()?
    alt Greeting
        API-->>UI: "สวัสดีค่ะ มีอะไรให้ช่วย?"
    else Policy Question
        API->>DB: count active_policies
        API->>QD: vector search
        API->>DB: keyword search
        API->>LLM: call_llm(policy context)
        LLM-->>API: policy answer
        API-->>UI: response
    else Tracking / Refund
        API->>DB: get_tracking_context()
        API->>LLM: call_llm(shipment context)
        LLM-->>API: tracking answer
        API-->>UI: response
    end
    UI-->>Customer: แสดงคำตอบ
```

---

## 9. API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/login` | Login → JWT token |
| POST | `/api/v1/chat` | Main AI chat endpoint |
| GET | `/api/v1/data/customers/{id}/orders` | ออเดอร์ของลูกค้า |
| GET | `/api/v1/data/customers/{id}/shipments` | พัสดุของลูกค้า |
| GET | `/api/v1/data/customers/{id}/conversations` | ประวัติแชท |
| GET | `/api/v1/data/customers/{id}/refund-requests` | คำขอคืนเงิน |
| GET | `/api/v1/data/customers/{id}/proactive-alerts` | การแจ้งเตือน |
| GET | `/api/v1/data/shipments/{id}` | รายละเอียดพัสดุ |
| POST | `/api/v1/admin/policies` | อัปโหลด policy PDF |
| GET | `/api/v1/admin/policies` | รายการ policies |
| GET | `/api/v1/admin/cases` | รายการ cases |
| PATCH | `/api/v1/admin/refunds/{id}/approve` | อนุมัติคืนเงิน |
| GET | `/api/v1/observability/traces` | AI workflow traces |
| GET | `/api/v1/health` | Health check |

---

## 10. Docker Services

```mermaid
graph TB
    subgraph Docker Network
        FE[shopeasy-frontend\n:3000\nReact + Vite]
        BE[shopeasy-backend\n:8000\nFastAPI]
        PG[shopeasy-postgres\n:5432\nPostgreSQL ✅ healthy]
        QD[shopeasy-qdrant\n:6333\nQdrant ⚠️ unhealthy*]
        MN[shopeasy-minio\n:9000/:9001\nMinIO ✅ healthy]
        RD[shopeasy-redis\n:6379\nRedis ✅ healthy]
        OL[Ollama\n:11434\nhost.docker.internal]
    end

    FE -->|API calls| BE
    BE --> PG
    BE --> QD
    BE --> MN
    BE --> RD
    BE -->|LLM inference| OL
```

> ⚠️ **Qdrant unhealthy**: healthcheck config ใน docker-compose ผิด แต่ vector search ทำงานได้ปกติ (ทดสอบยืนยันแล้ว)

---

## 11. Git Branches & Commit History

| Branch | Status | Notes |
|--------|--------|-------|
| `main` | stable | Last commit: `efc7eea` |
| `final-shop` | **active** ← current | All new features here |

### Recent Changes (final-shop)
```
60390ee  feat: final-shop - intent routing, alert fixes, status filters, policy RAG
         ├── backend/app/agents/llm.py          — system prompts + ค่ะ-only rule
         ├── backend/app/services/chat.py        — greeting fast-path + intent router
         ├── backend/app/services/policy_rag.py  — Thai tokenizer + hybrid search
         ├── backend/app/agents/nodes/tracking_nodes.py — STATUS_FILTERS (5 statuses)
         ├── backend/app/repositories/tracking.py       — ALL_SHIPMENT_STATUSES
         └── frontend/src/pages/admin/AdminPortal.tsx   — Open Case button + alerts UI
```

### Uncommitted Changes (ยังไม่ได้ commit)
- `backend/app/agents/llm.py` — เพิ่ม `[CRITICAL] ใช้ "ค่ะ" เท่านั้น`
- `backend/app/services/chat.py` — `_is_pure_greeting()` fast path
- `frontend/src/pages/admin/AdminPortal.tsx` — remove Open badge

---

## 12. สิ่งที่ทำงานแล้ว (Done ✅)

| Feature | Status |
|---------|--------|
| Customer AI Chat (Tracking) | ✅ ทำงาน |
| Customer AI Chat (Refund) | ✅ ทำงาน |
| Customer AI Chat (Policy RAG) | ✅ ทำงาน |
| Greeting fast-path (ไม่เรียก LLM) | ✅ ทำงาน |
| ตอบ "ค่ะ" เท่านั้น | ✅ ทำงาน |
| Status filter (จัดเตรียม/จัดส่ง/สำเร็จ/ยกเลิก/ล่าช้า) | ✅ ทำงาน |
| Thai tokenizer สำหรับ RAG | ✅ ทำงาน |
| Policy hybrid search (vector + keyword) | ✅ ทำงาน |
| Admin Portal — Cases / Customers | ✅ ทำงาน |
| Admin Portal — Refund Approval | ✅ ทำงาน |
| Admin Portal — Proactive Alerts (Open Case / Resolve) | ✅ ทำงาน |
| Admin Portal — Policy Upload | ✅ ทำงาน |
| AI Engineer Portal — RAG Testing | ✅ ทำงาน |
| AI Engineer Portal — Workflow Traces | ✅ ทำงาน |
| JWT Auth (3 roles) | ✅ ทำงาน |
| Docker 6-service stack | ✅ ทำงาน |

---

## 13. Roadmap — สิ่งที่ต้องทำต่อ (WOW Features)

### Priority Matrix

```mermaid
quadrantChart
    title WOW Feature Priority (Impact vs Effort)
    x-axis Low Effort --> High Effort
    y-axis Low Impact --> High Impact
    quadrant-1 Do First
    quadrant-2 Plan Carefully
    quadrant-3 Fill-ins
    quadrant-4 Reconsider

    Real-time Chat (WebSocket): [0.35, 0.92]
    Multi-language Support (EN): [0.30, 0.75]
    Commit Uncommitted Changes: [0.05, 0.80]
    Fix Qdrant Healthcheck: [0.10, 0.55]
    Chat History Scroll (persist): [0.20, 0.70]
    Order Status Push Notification: [0.50, 0.85]
    Admin Dashboard Analytics: [0.55, 0.78]
    AI Confidence Score Display: [0.40, 0.65]
    Proactive Alert Auto-trigger: [0.60, 0.88]
    Shopify Integration (live sync): [0.85, 0.90]
    Mobile Responsive UI: [0.45, 0.72]
    Rate Limiting per User: [0.25, 0.60]
```

---

### Phase 1 — Quick Wins (ทำได้เลย)

#### 1.1 Commit uncommitted changes
```
git add .
git commit -m "fix: greeting fast-path, ค่ะ-only rule, remove Open badge"
git push origin final-shop
```

#### 1.2 Fix Qdrant healthcheck (docker-compose.yml)
```yaml
# เปลี่ยน healthcheck ให้ถูก
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:6333/healthz"]
  interval: 30s
  timeout: 10s
  retries: 3
```

#### 1.3 Chat History — persist & scroll back
- บันทึก messages ลง DB (`messages` table) สำหรับ policy + greeting workflows
- Frontend โหลด history เมื่อเปิด conversation เดิม

#### 1.4 Typing Indicator
- แสดง "AI กำลังพิมพ์..." ระหว่างรอ LLM (~30-90s บน Ollama)

---

### Phase 2 — WOW UI/UX (1-2 สัปดาห์)

#### 2.1 Real-time Chat (WebSocket)
```mermaid
sequenceDiagram
    participant FE as Frontend
    participant WS as WebSocket Server
    participant LLM as Ollama (streaming)

    FE->>WS: connect + send message
    WS->>LLM: stream=True
    loop token by token
        LLM-->>WS: token
        WS-->>FE: token
        FE-->>FE: append to chat bubble
    end
```
- ใช้ FastAPI `WebSocket` + `StreamingResponse`
- Ollama รองรับ streaming แล้ว
- ผลลัพธ์: ตัวอักษรพิมพ์ทีละตัวเหมือน ChatGPT

#### 2.2 AI Confidence Score
- แสดง `confidence` badge ข้างคำตอบ AI
- ถ้า score < 0.5 → แสดง "⚠️ ควรยืนยันกับเจ้าหน้าที่"
- คำนวณจาก: Qdrant similarity score + intent certainty

#### 2.3 Mobile Responsive
- ปัจจุบัน UI ออกแบบสำหรับ desktop เท่านั้น
- เพิ่ม responsive breakpoints (768px, 480px)
- Customer Portal ต้องใช้งานบนมือถือได้สะดวก

#### 2.4 Admin Dashboard Analytics
```mermaid
graph LR
    DB[(PostgreSQL)] --> STATS[Analytics API]
    STATS --> CHART1[📊 Total Cases by Status]
    STATS --> CHART2[📈 Chat Volume per Day]
    STATS --> CHART3[🎯 Intent Distribution]
    STATS --> CHART4[⏱️ Avg Response Time]
    STATS --> CHART5[💰 Refund Approval Rate]
```

---

### Phase 3 — Agentic WOW (2-4 สัปดาห์)

#### 3.1 Proactive Alert Auto-trigger
```mermaid
flowchart TD
    CRON[⏰ Cron Job\nทุก 15 นาที] --> SCAN[สแกน shipments\nที่ล่าช้า / risk score สูง]
    SCAN --> AI_EVAL[AI ประเมิน\nrisk score]
    AI_EVAL -->|score > 0.7| ALERT[สร้าง ProactiveAlert]
    ALERT --> NOTIFY_ADMIN[แจ้ง Admin Portal]
    ALERT --> NOTIFY_CUST[แจ้งลูกค้าใน Chat]
    ALERT --> DRAFT[สร้าง message_draft\nให้ Admin ส่ง]
```
- ปัจจุบัน: Alert สร้างจาก seed data เท่านั้น
- WOW: AI สแกนอัตโนมัติ + แจ้งเตือน real-time

#### 3.2 Multi-turn Memory (Long-term)
- ปัจจุบัน: จำได้แค่ใน session เดียว
- WOW: AI จำประวัติลูกค้าข้ามหลาย session
- เช่น: "ครั้งก่อนคุณถามเรื่อง SP-1024 ที่ล่าช้า ตอนนี้ได้รับแล้วนะคะ"

#### 3.3 Order Status Push Notification
```mermaid
flowchart LR
    DB[(Shipment Status\nChanged)] --> WEBHOOK[Webhook Handler]
    WEBHOOK --> REDIS[(Redis Pub/Sub)]
    REDIS --> WS[WebSocket Server]
    WS --> FE[Frontend\nCustomer Portal]
    FE --> TOAST[🔔 Toast Notification\n"พัสดุ SP-1024 จัดส่งแล้วค่ะ"]
```

#### 3.4 Shopify Live Sync
- Connect ไป Shopify API webhook
- sync orders/shipments แบบ real-time
- ปัจจุบันใช้ `shopify_order_id` column แต่ยังไม่ sync

---

### Phase 4 — Production Ready

#### 4.1 Rate Limiting
```python
# เพิ่มใน FastAPI middleware
@app.middleware("http")
async def rate_limit(request, call_next):
    # 30 requests/minute per user
```

#### 4.2 OpenAI API Upgrade
- ปัจจุบัน: Ollama qwen2.5:1.5b (CPU, ~30-90s/call)
- Production: GPT-4o-mini (~1-3s/call)
- Config ใน `.env`: `OPENAI_API_KEY=sk-...`
- Code รองรับแล้ว — ไม่ต้องแก้ code เลย

#### 4.3 Merge final-shop → main
```bash
git checkout main
git merge final-shop
git push origin main
```

#### 4.4 CI/CD Pipeline (GitHub Actions)
```yaml
on: push to main
jobs:
  test: pytest backend/tests/
  build: docker build + push to registry
  deploy: docker compose pull + up -d
```

---

## สรุป Roadmap Timeline

```mermaid
gantt
    title ShopEasy WOW Roadmap
    dateFormat  YYYY-MM-DD
    section Phase 1 - Quick Wins
    Commit uncommitted changes     :done, p1a, 2026-05-15, 1d
    Fix Qdrant healthcheck         :p1b, 2026-05-15, 1d
    Chat history persist           :p1c, 2026-05-16, 3d
    Typing indicator               :p1d, 2026-05-16, 2d

    section Phase 2 - WOW UI/UX
    WebSocket streaming chat       :p2a, 2026-05-19, 5d
    AI Confidence Score badge      :p2b, 2026-05-21, 3d
    Mobile responsive UI           :p2c, 2026-05-22, 5d
    Admin analytics dashboard      :p2d, 2026-05-24, 4d

    section Phase 3 - Agentic WOW
    Proactive alert auto-trigger   :p3a, 2026-05-28, 7d
    Multi-turn long-term memory    :p3b, 2026-06-01, 5d
    Push notification (WebSocket)  :p3c, 2026-06-03, 4d
    Shopify live sync              :p3d, 2026-06-08, 7d

    section Phase 4 - Production
    Rate limiting                  :p4a, 2026-06-10, 2d
    OpenAI API switch              :p4b, 2026-06-11, 1d
    Merge to main + CI/CD          :p4c, 2026-06-12, 3d
```

---

> **สถานะปัจจุบัน**: Branch `final-shop` | 3 files uncommitted | ทุก workflow ทดสอบผ่านแล้ว  
> **Next action**: Commit + push → แล้วเริ่ม Phase 1 Quick Wins
