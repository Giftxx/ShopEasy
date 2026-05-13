# ShopEasy — Tech Stack & Architecture

> รายละเอียดเครื่องมือ, Framework, LLM และเทคโนโลยีทั้งหมดที่ใช้ในระบบ

---

## ภาพรวมสถาปัตยกรรม

```
┌──────────────────────────────────────────────────────────────────┐
│                        Frontend                                  │
│         React 19 + TypeScript 6 + Vite 8                        │
│                    Port 5173                                     │
├──────────────────────────────────────────────────────────────────┤
│                        Backend                                   │
│            FastAPI + Python 3.11 + LangGraph                    │
│                    Port 8000                                     │
├────────────┬────────────┬────────────┬───────────────────────────┤
│ PostgreSQL │   Redis    │   MinIO    │         Qdrant            │
│   16       │   7        │   latest   │         latest            │
│ Port 5433  │ Port 6379  │ Port 9000  │       Port 6333           │
│ ฐานข้อมูล   │ Cache/     │ ไฟล์       │      Vector DB            │
│ หลัก       │ Memory     │ หลักฐาน    │      สำหรับ RAG           │
├────────────┴────────────┴────────────┴───────────────────────────┤
│                     LLM Provider                                 │
│       OpenAI (gpt-3.5-turbo) ─ primary                          │
│       Ollama (qwen2.5:1.5b)  ─ fallback/local                  │
│       Ollama (bge-m3)         ─ embedding                       │
└──────────────────────────────────────────────────────────────────┘
```

---

## 1. Frontend

| เทคโนโลยี | เวอร์ชัน | ทำหน้าที่ |
|-----------|---------|----------|
| **React** | 19.2.5 | UI Framework หลัก |
| **TypeScript** | 6.0.2 | Type-safe JavaScript |
| **Vite** | 8.0.10 | Build tool & Dev server |
| **React Router DOM** | 7.14.2 | SPA Routing (3 portals) |
| **ESLint** | 10.2.1 | Code linting |

### Build Configuration
- **Target:** ES2023
- **Module:** ESNext + Bundler resolution
- **JSX:** react-jsx
- **Dev Server:** Hot reload ด้วย Vite, poll mode สำหรับ Docker

---

## 2. Backend

| เทคโนโลยี | เวอร์ชัน | ทำหน้าที่ |
|-----------|---------|----------|
| **Python** | 3.11 | ภาษาหลักฝั่ง Backend |
| **FastAPI** | ≥0.115 | Web Framework + API |
| **Uvicorn** | ≥0.30 | ASGI Server |
| **SQLAlchemy** | ≥2.0 | ORM + Database |
| **Pydantic** | ≥2.8 | Data Validation / Schemas |
| **Alembic** | ≥1.13 | Database Migration |
| **psycopg** | ≥3.2 | PostgreSQL Driver (async) |

### Security
| เทคโนโลยี | ทำหน้าที่ |
|-----------|----------|
| **python-jose** (≥3.3) | JWT Token สร้าง/ตรวจสอบ (HS256) |
| **passlib + bcrypt** | Password Hashing |
| **google-auth** (≥2.30) | Google OAuth Login |
| Token Expiry | 24 ชั่วโมง |

---

## 3. AI / LLM

### LLM Models

| Model | Provider | ใช้ทำอะไร | Config |
|-------|----------|----------|--------|
| **gpt-3.5-turbo** | OpenAI API | Primary LLM (ถ้ามี API Key) | temp=0.7, max_tokens=400, timeout=90s |
| **qwen2.5:1.5b** | Ollama (local) | Fallback LLM | temp=0.7, max_tokens=400, timeout=90s |
| **bge-m3** | Ollama (local) | Embedding สำหรับ RAG | 1024 dimensions |

### LLM Client Logic
```
ถ้ามี OPENAI_API_KEY ที่ขึ้นต้นด้วย "sk-"
    → ใช้ OpenAI API (gpt-3.5-turbo)
ถ้าไม่มี
    → ใช้ Ollama local (qwen2.5:1.5b)
```

### System Prompts (3 ตัว)
| Prompt | ใช้กับ | จำกัดคำ |
|--------|------|--------|
| `TRACKING_SYSTEM_PROMPT` | ติดตามพัสดุ (WF01) | 150 คำ |
| `REFUND_SYSTEM_PROMPT` | คืนเงิน (WF02) | 150 คำ |
| `GENERAL_SYSTEM_PROMPT` | คำถามทั่วไป (Fallback) | 150 คำ |

---

## 4. AI Agent Framework

### LangGraph (Workflow Orchestration)

| เทคโนโลยี | เวอร์ชัน | ทำหน้าที่ |
|-----------|---------|----------|
| **LangGraph** | ≥0.1.0 | StateGraph สำหรับ workflow orchestration |
| **LangChain Core** | ≥0.2.0 | Foundation ของ LangGraph |
| **OpenAI SDK** | ≥1.0.0 | LLM Client (ใช้กับทั้ง OpenAI และ Ollama) |

### Workflow Graph (8 Nodes)

```
[Router] → [Context] → [Memory] ─┬─ tracking → [Plan] → [Ship] → [Respond]
                                  └─ fallback → [Fallback]
                                                     ↓
                                              [Write Memory] → END
```

| Node | ทำหน้าที่ |
|------|----------|
| `router_node` | จำแนก intent ด้วย keyword + LLM |
| `context_resolution_node` | โหลดข้อมูลลูกค้า ออเดอร์ พัสดุ คำขอคืนเงิน |
| `memory_retrieval_node` | โหลด memory 3 ชั้น |
| `planner_node` | วางแผนการดึงข้อมูล + ประเมินความเสี่ยง |
| `shipping_node` | สรุปข้อมูลพัสดุ |
| `support_response_node` | สร้างคำตอบด้วย LLM + RAG |
| `fallback_node` | ตอบคำถามทั่วไป + RAG + ข้อมูลลูกค้าครบ |
| `memory_write_node` | บันทึก memory ทั้ง 3 ชั้น |

### ReAct Engine (Autonomous Mode)

| Parameter | ค่า |
|-----------|-----|
| Max Iterations | 4 |
| Time Budget | 30 วินาที |
| Pattern | THOUGHT → ACTION → OBSERVE → REFLECT → loop/Finish |
| เปิดใช้งานเมื่อ | `REACT_ENABLED=true` (สำหรับ Cloud LLM ที่เร็ว) |

### Advanced Agent Components

| Component | ทำหน้าที่ |
|-----------|----------|
| **Supervisor Agent** | ตรวจสอบคุณภาพคำตอบ (threshold: 0.6) + ประเมินความเสี่ยง (≥70 = human review) |
| **Circuit Breaker** | ป้องกัน cascading failure (5 failures → trip, 60s timeout) |
| **Planner** | สร้าง execution plan เป็น JSON, fallback เป็น template ถ้า LLM ไม่พร้อม |
| **Tool Registry** | ลงทะเบียน tools ทั้งหมดให้ ReAct engine เรียกใช้ |
| **Inter-Agent MessageBus** | Pub/Sub ระหว่าง agents (REQUEST, RESPONSE, EVENT, HANDOFF, ESCALATION) |

---

## 5. Memory System (3 ชั้น)

| ชั้น | Storage | TTL | เก็บอะไร |
|-----|---------|-----|---------|
| **Short-term** | Redis (Hash) | 24 ชั่วโมง | Session context: last intent, active orders |
| **Episodic** | PostgreSQL | ถาวร | เหตุการณ์สำคัญ: fraud, escalation, disputes |
| **Long-term** | PostgreSQL | ถาวร | รูปแบบพฤติกรรม: ความถี่, preferences |

---

## 6. RAG System (Retrieval-Augmented Generation)

| Component | Detail |
|-----------|--------|
| **Vector Database** | Qdrant (port 6333) |
| **Embedding Model** | bge-m3 (1024 dimensions) |
| **Distance Metric** | Cosine Similarity |
| **Chunk Size** | 500 characters |
| **Chunk Overlap** | 80 characters |
| **Search Strategy** | Hybrid — Vector search ก่อน, fallback เป็น Keyword (ILIKE) |
| **Collection** | `policy_chunks` |

### นโยบายที่ index อยู่ (26 chunks)

| ID | ชื่อ | หมวด | Chunks |
|----|------|------|--------|
| POL-001 | Refund Policy | refund | 6 |
| POL-002 | Return Policy | return | 5 |
| POL-003 | Compensation Policy | compensation | 5 |
| POL-004 | Shipping Policy | shipping | 6 |
| POL-005 | Seller SLA Policy | seller | 4 |

---

## 7. Database (PostgreSQL 16)

### Connection Pool Config
| Parameter | ค่า |
|-----------|-----|
| pool_size | 20 |
| max_overflow | 40 |
| pool_recycle | 1800 วินาที |
| pool_pre_ping | true |

### ตาราง (แบ่งตามกลุ่ม)

**กลุ่ม Business:** users, customers, sellers, orders, order_items  
**กลุ่ม Shipping:** shipments, shipment_items, shipment_events  
**กลุ่ม Support:** conversations, messages, cases, refund_requests, approvals, proactive_alerts  
**กลุ่ม AI:** agent_traces, tool_logs, execution_plans  
**กลุ่ม Memory:** customer_long_term_memory, customer_episodic_memory  
**กลุ่ม RAG:** policies, policy_chunks  
**กลุ่ม Files:** attachments  

### Migration: Alembic (5 versions)
```
488c75bf3411 — Init schema (ตารางทั้งหมด)
4b5bb6c546ab — Admin notes fields
59617f241933 — Memory tables + Shopify columns
c1e2f3a4b5d6 — Hashed password
d9f1a2b3c4e5 — Policy file + chunk metadata
```

---

## 8. Infrastructure (Docker Compose)

| Service | Image | Port | Volume | Healthcheck |
|---------|-------|------|--------|-------------|
| **db** | postgres:16-alpine | 5433:5432 | postgres_data | pg_isready |
| **redis** | redis:7-alpine | 6379:6379 | redis_data | redis-cli ping |
| **minio** | minio/minio:latest | 9000, 9001 | minio_data | curl /minio/health/live |
| **qdrant** | qdrant/qdrant:latest | 6333:6333 | qdrant_data | curl /collections |
| **backend** | python:3.11-slim (custom) | 8000:8000 | ./backend:/app | — |
| **frontend** | node (custom) | 5173:5173 | ./frontend:/app | — |
| **create-buckets** | minio/mc | — | — | — |

---

## 9. API Structure

```
/api/v1/
├── /auth
│   ├── POST /login          — Email + Password login
│   └── POST /google         — Google OAuth login
├── /chat
│   └── POST /               — ส่งข้อความ → AI ตอบ
├── /data
│   ├── /customers/{id}      — ข้อมูลลูกค้า + ออเดอร์
│   ├── /orders              — รายการออเดอร์
│   ├── /shipments           — สถานะพัสดุ
│   ├── /conversations       — ประวัติสนทนา + messages
│   ├── /refund-requests     — คำขอคืนเงิน
│   └── /proactive-alerts    — การแจ้งเตือนเชิงรุก
├── /admin
│   ├── /dashboard           — สรุปภาพรวม
│   ├── /approvals           — อนุมัติ/ปฏิเสธ
│   └── /cases               — จัดการเคส
├── /attachments
│   ├── POST /presign        — สร้าง presigned URL
│   └── POST /confirm        — ยืนยันอัปโหลด
├── /workflows
│   └── POST /run            — รัน workflow จาก AI Portal
├── /observability
│   ├── /traces              — Agent traces
│   ├── /tool-logs           — Tool call logs
│   └── /metrics             — Performance metrics
└── /health                  — Health check
```

---

## 10. Workflow สรุป

| Workflow | Trigger | AI Nodes | Human-in-Loop |
|----------|---------|----------|---------------|
| **WF01 — Tracking** | ลูกค้าถามสถานะพัสดุ | 7 nodes | ไม่มี |
| **WF02 — Refund** | ลูกค้าขอคืนเงิน | dedicated workflow | Risk ≥ 70 → Admin approve |
| **WF03 — Proactive** | ระบบตรวจพบพัสดุล่าช้า (48h+) | 11 nodes | Risk ≥ 70 → Admin approve |

---

## 11. Intent Classification

```
ลูกค้าพิมพ์ข้อความ
        ↓
[Keyword Rules — เร็ว, ทำงานเสมอ]
   ├── detect_refund_intent()  → "refund_request"
   ├── detect_tracking_intent() → "track_shipment"
   └── ไม่ match                → ใช้ LLM (ถ้าเปิด CLASSIFY_WITH_LLM=true)
        ↓
[LLM Classification — ถ้าเปิดใช้]
   Intent Router Prompt + ตัวอย่างไทย/อังกฤษ 9 ตัวอย่าง
        ↓
   "track_shipment" | "refund_request" | "general_inquiry"
```

---

## 12. Development Tools

| Tool | ใช้ทำอะไร |
|------|----------|
| **Docker Compose** | จัดการ services ทั้งหมด |
| **Alembic** | Database migration |
| **pytest + httpx** | Backend testing |
| **ESLint** | Frontend linting |
| **Vite** | Frontend dev server + HMR |
| **Git + GitHub** | Version control |

---

*ShopEasy Tech Stack Documentation — 13 พฤษภาคม 2026*
