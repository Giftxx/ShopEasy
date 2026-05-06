# 🛍️ ShopEasy - Agentic Marketplace Operations Platform

> An AI-powered post-purchase support and operations platform for marketplace businesses combining LangGraph multi-agent workflows, PostgreSQL business data, Qdrant policy-grounded RAG, MinIO evidence storage, Redis background processing, and human-in-the-loop approvals.

---

## 📊 Project Status

| Milestone | Status |
|-----------|--------|
| UI Design (Blueprint) | ✅ Complete |
| Role & Access Control | ✅ Complete |
| Database Schema (DBML) | ✅ Complete |
| Tech Stack Selection | ✅ Complete |
| MinIO Integration | ✅ Complete |
| Qdrant Selection | ✅ Complete |
| FastAPI Stack | ✅ Complete |

**Phase**: Transitioning from Design → Implementation

---

## 🏗️ Architecture & Tech Stack

### Core Components

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **UI/Frontend** | Next.js + Tailwind + shadcn/ui | 3 Portals: Customer, Admin, AI Control |
| **Backend API** | FastAPI | REST endpoints & event processing |
| **AI Workflow** | LangGraph | Multi-agent orchestration engine |
| **Database** | PostgreSQL | Business data persistence |
| **ORM** | SQLAlchemy 2.x | Python ORM & schema mapping |
| **Migrations** | Alembic | Schema versioning & management |
| **Vector DB** | Qdrant | Policy embeddings & semantic search |
| **File Storage** | MinIO | Images, videos, evidence documents |
| **Cache/Queue** | Redis | Session cache & background jobs |
| **Infrastructure** | Docker Compose | Local multi-service development |
| **Deployment** | Vercel / Render / Railway / VPS | Production hosting options |

---

## 📈 Roadmap: 8-Phase Implementation

### Phase 1: Project Setup + Docker
**Goal**: Single-command deployment
```bash
docker compose up --build
```
**Deliverables**:
- Next.js frontend scaffold
- FastAPI backend scaffold
- docker-compose.yml with all services
- .env.example configuration
- Service health checks

**Success Criteria**:
- ✓ Frontend: localhost:3000
- ✓ FastAPI Swagger: localhost:8000/docs
- ✓ MinIO Console: localhost:9001
- ✓ Qdrant Health: localhost:6333/health
- ✓ PostgreSQL & Redis running

**Timeline**: Day 1

---

### Phase 2: Database + Migration + Seed Data
**Goal**: PostgreSQL schema with mock data

**Core Tables** (28 tables):
```
users, customers, sellers, orders, order_items,
shipments, shipment_items, shipment_events,
conversations, messages, attachments,
cases, approvals, refund_requests, evidence_reviews,
policies, policy_chunks,
agent_traces, tool_logs, proactive_alerts,
agents, agent_configs,
evaluations, evaluation_cases,
audit_logs, integrations, system_settings
```

**Mock Data Seed**:
```
Users:
  - customer_demo, admin_demo, ai_system_admin

Customers:
  - นารีศรา, Nicha, Beam

Sellers:
  - FashionHub, GadgetMall, BeautyMall

Orders (Sample):
  - SP-1024: Multiple items, in-progress shipment
  - SP-2044: Delayed shipment
  - SP-8831: Delivered
  - SP-7711: Cancelled
  - SP-9900: Refund requested

Policies:
  - Shipping, Refund, Return, Compensation, Seller SLA
```

**Success Criteria**:
- ✓ Alembic migrations run successfully
- ✓ All tables created in PostgreSQL
- ✓ Mock data queries return results
- ✓ Frontend/Backend can fetch data

**Timeline**: Day 2-3

---

### Phase 3: Backend API - Core Endpoints
**Goal**: API ready for UI integration

**Auth Routes**:
```
POST   /auth/mock-login        → Simulate login for 3 roles
GET    /auth/me                → Current user profile
```

**Customer Routes**:
```
GET    /customer/orders                          → List orders
GET    /customer/orders/{order_id}               → Order detail
GET    /customer/shipments                       → Track shipments
GET    /customer/refund-requests                 → Refund history
GET    /customer/notifications                   → Alerts
GET    /customer/conversations/{id}/messages     → Chat history
POST   /customer/messages                        → Send message
```

**Admin Routes**:
```
GET    /admin/dashboard                  → KPI metrics
GET    /admin/cases                      → Case queue
GET    /admin/cases/{case_id}            → Case details
GET    /admin/approvals                  → Approval queue
POST   /admin/approvals/{id}/approve     → Approve decision
POST   /admin/approvals/{id}/reject      → Reject decision
GET    /admin/refund-requests            → Refund queue
GET    /admin/proactive-alerts           → Delay alerts
```

**AI Control Routes**:
```
GET    /ai/agent-traces                  → Workflow executions
GET    /ai/agent-traces/{trace_id}       → Trace details
GET    /ai/tool-logs                     → Tool call logs
GET    /ai/policies                      → Policy documents
GET    /ai/evaluations                   → Model evaluations
GET    /ai/agents                        → Agent configurations
```

**Success Criteria**:
- ✓ All routes in Swagger UI
- ✓ CRUD operations working
- ✓ Status transitions working (approve/reject)
- ✓ Data persistence to database

**Timeline**: Day 4

---

### Phase 4: MinIO File Upload
**Goal**: Evidence document storage & retrieval

**Flow**:
```
1. Customer selects files
2. Frontend requests presigned upload URL
3. Backend generates object key
4. Frontend uploads to MinIO
5. Backend saves metadata to attachments table
6. Admin downloads via presigned download URL
```

**API Endpoints**:
```
POST   /attachments/presign-upload           → Get upload URL
POST   /attachments/confirm-upload           → Register upload
GET    /attachments                          → List files
GET    /attachments/{id}/presign-download    → Get download URL
DELETE /attachments/{id}                     → Remove file
```

**Object Key Format**:
```
refund_request/RF-5521/damaged_item/01_front-crack.jpg
refund_request/RF-5521/parcel_package/02_box-damaged.jpg
refund_request/RF-5521/parcel_label/03_shipping-label.jpg
refund_request/RF-5521/unboxing_video/04_unboxing.mp4
```

**Evidence Categories**:
- damaged_item, missing_item, wrong_item
- parcel_package, parcel_label, receipt
- unboxing_video, customer_note, admin_note
- policy_document, other

**Success Criteria**:
- ✓ Files upload to MinIO
- ✓ Metadata saved to database
- ✓ Admin can download via presigned URL
- ✓ Files organized by evidence_group

**Timeline**: Day 5

---

### Phase 5: Qdrant RAG - Policy Search
**Goal**: AI can search policies semantically

**Ingestion Pipeline**:
```
Read policies.content from PostgreSQL
→ Split into chunks
→ Generate embeddings
→ Upsert to Qdrant
→ Save embedding_id in policy_chunks
```

**Qdrant Payload Structure**:
```json
{
  "policy_id": "POL-001",
  "title": "Refund Policy",
  "category": "refund",
  "version": "v1.0",
  "status": "active",
  "section": "3.2",
  "language": "th"
}
```

**Policies to Index**:
- Shipping Policy
- Refund Policy
- Return Policy
- Compensation Policy
- Seller SLA Policy
- Address Change Policy
- Fraud Review Policy
- FAQ

**Search Example**:
```
Query: "ของมาชำรุด ขอคืนเงินได้ไหม"
Filters: category in ["refund", "return"], status="active"
Result: Relevant policy chunks with metadata
```

**API Endpoints**:
```
POST   /ai/rag/ingest-policies      → Index all policies
POST   /ai/rag/search               → Semantic search
GET    /ai/policies                 → List policies
GET    /ai/policy-chunks            → View chunks
```

**Success Criteria**:
- ✓ Policies ingested to Qdrant
- ✓ Search returns relevant chunks
- ✓ LangGraph agents can use results
- ✓ AI Control UI shows search results

**Timeline**: Day 6

---

### Phase 6: LangGraph Agent Workflows
**Goal**: 3 core AI workflows operational

#### Workflow 1: Order Tracking
**Trigger**: Customer asks "ของฉันอยู่ไหนแล้ว"

**Flow**:
```
router_node
→ context_resolution_node (identify customer)
→ order_node (fetch open orders)
→ shipping_node (get shipment status)
→ support_response_node (compose reply)
→ logging_node (record trace)
```

**Example Response**:
```
ตอนนี้ออเดอร์ SP-1024 มี 2 พัสดุค่ะ
1. เสื้อและสูท: ส่งสำเร็จแล้ว
2. กางเกง: อยู่ระหว่างขนส่ง (ไม่อัปเดต 48+ ชม.)
ระบบกำลังติดตามให้ค่ะ
```

---

#### Workflow 2: Refund Request
**Trigger**: Customer asks "สินค้าเสียหาย ขอคืนเงินได้ไหม"

**Flow**:
```
router_node
→ context_resolution_node
→ order_node (validate order)
→ policy_rag_node (search refund policy)
→ refund_node (check eligibility)
→ risk_node (calculate risk score)
→ supervisor_node (review decision)
→ approval_node or support_response_node
→ logging_node
```

**Decision Factors**:
- Order eligibility (time, status)
- Policy compliance
- Evidence attachments
- Risk score
- Amount threshold

---

#### Workflow 3: Proactive Delay Alert
**Trigger**: System detects shipment_no_update_48h

**Flow**:
```
event_ingestion_node
→ shipping_node (fetch shipment)
→ risk_node (calculate delay risk)
→ policy_rag_node (find SLA policy)
→ proactive_alert_node (create alert)
→ supervisor_node (review)
→ approval_node (if compensation needed)
→ logging_node
```

**Actions**:
- Create proactive_alert record
- Create case if high risk
- Create approval if compensation needed
- Send customer notification

---

**Nodes to Implement**:
```
router_node, context_resolution_node, order_node,
shipping_node, policy_rag_node, refund_node,
risk_node, supervisor_node, approval_node,
proactive_alert_node, support_response_node,
logging_node, fallback_node
```

**Tools to Implement**:
```
get_customer_open_orders()
get_order()
get_shipments_by_order()
get_items_by_shipment()
search_policy()
create_case()
create_refund_request()
request_approval()
create_proactive_alert()
send_customer_message()
log_tool_call()
```

**Success Criteria**:
- ✓ POST /chat returns LangGraph response
- ✓ agent_traces table populated
- ✓ tool_logs recorded for each action
- ✓ Admin sees created cases/approvals
- ✓ AI Control shows execution trace

**Timeline**: Day 7-9

---

### Phase 7: Frontend UI - 3 Portals
**Goal**: Complete user interfaces for all roles

#### Portal 1: Customer (`/customer`)
**Routes**:
- `/customer/chat` → Chat with AI
- `/customer/orders` → Order list
- `/customer/shipments` → Shipment tracking
- `/customer/refund-return` → Request refund/return
- `/customer/notifications` → Alerts & updates
- `/customer/help` → FAQ & contact

**Features**:
- Real-time chat interface
- Order status timeline
- Shipment tracking map
- Evidence upload gallery
- Notification center

---

#### Portal 2: Admin (`/admin`)
**Routes**:
- `/admin/dashboard` → KPI metrics
- `/admin/cases` → Case queue
- `/admin/approvals` → Approval workflow
- `/admin/refund-return` → Caseworker workspace
- `/admin/operations` → System controls
- `/admin/proactive-alerts` → Delay alerts

**Features**:
- Performance dashboard
- Case assignment & tracking
- Approval workflow with bulk actions
- Evidence gallery
- Alert management
- Operations control center

---

#### Portal 3: AI Control (`/ai-control`)
**Routes** (MVP: first 5):
- `/ai-control/agent-trace` → Workflow executions
- `/ai-control/tool-logs` → Tool call logs
- `/ai-control/policies-rag` → RAG search interface
- `/ai-control/multi-agent` → Agent workspace
- `/ai-control/evaluation` → Model evaluation

**Additional Routes** (Placeholder):
- `/ai-control/analytics` → Performance metrics
- `/ai-control/settings` → Configuration
- `/ai-control/prompt-config` → Prompt management
- `/ai-control/model-settings` → Model parameters
- `/ai-control/observability` → System health
- `/ai-control/audit-logs` → Audit trail
- `/ai-control/integrations` → External services

**Features**:
- Agent execution visualization
- Tool call debugging
- Policy search testing
- Multi-agent workspace
- Model performance tracking

**Timeline**: Day 10-13

---

### Phase 8: Deployment + Documentation
**Goal**: Production-ready system with documentation

**Deployment Options**:

*Option A: Cloud-Native (Recommended for MVP)*
```
Frontend      → Vercel
Backend       → Render / Railway / Fly.io
PostgreSQL    → Supabase / Neon
Qdrant        → Qdrant Cloud or self-hosted VPS
MinIO         → Railway volume / S3-compatible service
Redis         → Upstash / Redis Cloud
```

*Option B: Self-Hosted*
```
Docker Compose on VPS
- DigitalOcean
- Hetzner
- AWS Lightsail
- Vultr
```

**Documentation**:
- Project overview & vision
- Architecture diagram
- Tech stack rationale
- Feature list
- Database ERD
- LangGraph workflow diagrams
- RAG pipeline explanation
- MinIO upload flow
- Role-based access control matrix
- Local setup guide
- API documentation
- Demo scenarios
- Screenshots
- Future improvements roadmap

**Demo Scenarios** (Video):

*Scenario 1: Order Tracking*
```
Customer asks "ของฉันอยู่ไหน?"
→ AI identifies order & shipment
→ Returns status with tracking info
→ Trace & logs appear in AI Control
```

*Scenario 2: Refund Request*
```
Customer uploads evidence + requests refund
→ AI searches policy + calculates risk
→ Creates case + approval in system
→ Admin reviews & approves in dashboard
```

*Scenario 3: Proactive Alert*
```
System detects 48h+ no shipment update
→ Proactive alert generated
→ Case created automatically
→ Compensation approval queued
→ Dashboard shows in real-time
```

**Timeline**: Day 14

---

## 📁 Project Structure

```
agentic-marketplace-ops/
│
├── frontend/                          # Next.js App
│   ├── app/
│   │   ├── customer/                 # Customer portal
│   │   ├── admin/                    # Admin portal
│   │   └── ai-control/               # AI Control portal
│   ├── components/                   # Shared components
│   ├── lib/                          # Utilities
│   ├── styles/                       # Tailwind + CSS
│   └── package.json
│
├── backend/                          # FastAPI App
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/              # API endpoints
│   │   │   └── deps.py              # Dependencies
│   │   ├── core/
│   │   │   ├── config.py            # Settings
│   │   │   └── security.py          # Auth/JWT
│   │   ├── db/
│   │   │   ├── base.py              # Base model
│   │   │   ├── session.py           # DB session
│   │   │   └── models/              # SQLAlchemy models
│   │   ├── schemas/                 # Pydantic schemas
│   │   ├── services/                # Business logic
│   │   ├── agents/                  # LangGraph workflows
│   │   │   ├── graph.py             # Main graph definition
│   │   │   ├── state.py             # Agent state schema
│   │   │   ├── nodes/               # Node implementations
│   │   │   └── tools/               # Tool definitions
│   │   ├── rag/                     # Qdrant integration
│   │   ├── storage/                 # MinIO integration
│   │   ├── workers/                 # Background tasks
│   │   └── main.py                  # FastAPI app
│   │
│   ├── alembic/                     # Database migrations
│   ├── alembic.ini
│   ├── requirements.txt
│   └── Dockerfile
│
├── docker-compose.yml               # Multi-service orchestration
├── .env.example                     # Environment template
├── .gitignore
└── README.md
```

---

## 🚀 14-Day Implementation Timeline

| Day | Focus | Deliverable |
|-----|-------|-------------|
| **1** | Repo + Docker | All services running |
| **2-3** | Database schema + seed | PostgreSQL with mock data |
| **4** | Backend CRUD APIs | FastAPI endpoints operational |
| **5** | MinIO integration | File upload/download working |
| **6** | Qdrant RAG | Policy search functional |
| **7-9** | LangGraph workflows | 3 agent workflows complete |
| **10-13** | Frontend UI | 3 portals complete |
| **14** | Deploy + docs | Live system + documentation |

---

## ⚠️ Out of Scope (MVP)

Keep scope contained by NOT implementing:

```
- LINE OA integration (mock instead)
- Real payment API (mock instead)
- Carrier API integration (mock instead)
- Production authentication (mock login)
- Kubernetes orchestration
- Multi-tenant support
- Advanced fraud detection models
- Image recognition pipeline
- Complex evaluation dashboards
- Advanced prompt versioning
```

*These can be added post-MVP*

---

## 🎯 MVP - Minimum Viable Features

Stripped down, the MVP needs only:

1. **Customer Chat** - Basic AI conversation
2. **Order/Shipment Lookup** - Query orders & track status
3. **Refund Request + Evidence** - Upload + submit refund
4. **Admin Cases/Approvals** - Review & approve decisions
5. **Agent Trace Viewer** - See what AI did
6. **Tool Logs** - Debug tool execution
7. **Policy RAG** - Search policy documents
8. **Proactive Alerts** - Detect shipping delays

**This alone is a strong Agentic AI portfolio project!**

---

## 🔄 Implementation Roadmap (Executable Steps)

```
1. ✓ Create repo structure
2. ✓ Docker Compose setup
3. ✓ PostgreSQL models + Alembic migration
4. ✓ Seed mock data
5. ✓ FastAPI CRUD APIs
6. ✓ MinIO file upload integration
7. ✓ Qdrant RAG setup
8. ✓ LangGraph workflows (3 core scenarios)
9. ✓ Frontend UI (3 portals)
10. ✓ Deploy + README + demo video
```

---

## 📝 Project Vision

**ShopEasy** transforms marketplace post-purchase operations through intelligent AI:

- 🤖 **Automated Support**: LangGraph agents handle common customer inquiries
- 🔍 **Policy-Aware Decisions**: Qdrant RAG ensures decisions follow company policy
- 📋 **Evidence Management**: MinIO stores customer proof for refund/return claims
- 👥 **Human-in-the-Loop**: Approvals let humans review high-risk decisions
- 📊 **Full Observability**: Traces, logs, and metrics for every AI action
- ⚡ **Async Processing**: Redis queues background tasks at scale

This is a complete, production-grade demonstration of modern Agentic AI architecture.

---

## 📚 Key Technologies Deep Dive

### LangGraph for Workflow Orchestration
- Multi-step decision trees
- Conditional routing based on state
- Tool integration & error handling
- Trace recording for observability

### Qdrant for Policy-Grounded RAG
- Semantic search over policy documents
- Metadata filtering (category, version, status)
- Fast similarity matching for AI decisions
- Embedding versioning & updates

### MinIO for Evidence Storage
- S3-compatible object storage
- Presigned URLs for browser uploads
- Metadata tagging for organization
- Integration with PostgreSQL references

### SQLAlchemy + Alembic
- Type-safe ORM models
- Automatic migration generation
- Schema versioning & rollback support
- Seed data scripts

---

**Ready to build? Start with Phase 1! 🚀**
#   S h o p E a s y  
 