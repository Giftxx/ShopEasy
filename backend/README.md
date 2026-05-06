# ShopEasy Backend Skeleton

This backend scaffold is aligned to the DBML schema stored in the project root `dbs.db`.

## Focus

Current implementation focus:

```text
Workflow 1: Track Shipment
```

Included so far:

```text
- FastAPI app entrypoint
- Health route
- Chat route with Workflow 1 mock response
- SQLAlchemy base/session setup
- Workflow 1 models aligned to dbs.db
- LangGraph-aligned state and graph placeholder
- Workflow 1 seed structure
```

Infrastructure and project hygiene:

```text
- Dockerfile
- docker-compose.yml (backend + postgres)
- Alembic skeleton
- pytest smoke tests
- root/backend gitignore
```

## Run

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Run from:

```text
backend/
```

## Local PostgreSQL

This project can now point to a local PostgreSQL dev database through:

```text
backend/.env
```

Current local dev target:

```text
postgresql+psycopg://LLM-project-shopeasy:LLm-260346@127.0.0.1:5433/shopeasy
```

There is also a template file:

```text
backend/.env.example
```

Bootstrap the local PostgreSQL database with one command:

```powershell
python -m app.db.bootstrap_dev
```

Or on Windows:

```powershell
.\scripts\bootstrap_postgres_dev.ps1
```

Important note for Windows dev:

```text
- Port 5432 on the host may already be used by a local PostgreSQL installation.
- The Docker PostgreSQL used by this project is exposed on host port 5433.
- Use 127.0.0.1:5433 for local Python tools and pgAdmin.
```

Recommended pgAdmin connection:

```text
Name: ShopEasy Docker DB
Host: 127.0.0.1
Port: 5433
Database: shopeasy
Username: shopeasy_dev
Password: shopeasy123
```

You can also use the primary container role:

```text
Username: LLM-project-shopeasy
Password: LLm-260346
```

Quick data check from Windows:

```powershell
.\scripts\inspect_postgres_dev.ps1
```

What bootstrap does:

```text
1. Create the PostgreSQL database if it does not exist yet
2. Run Alembic upgrade head
3. Seed all MVP workflow data into PostgreSQL
```

Create local tables from the current SQLAlchemy models:

```bash
python -m app.db.init_db
```

Install dev/test dependencies:

```bash
pip install -r requirements-dev.txt
```

Seed Workflow 1 demo data:

```bash
python -m app.db.seeds.run_workflow_01_seed
```

Seed Workflow 2 demo data:

```bash
python -m app.db.seeds.run_workflow_02_seed
```

Seed both Workflow 1 and Workflow 2:

```bash
python -m app.db.seeds.run_all_seeds
```

Seed Workflow 3 only:

```bash
python -m app.db.seeds.run_workflow_03_seed
```

Trigger proactive delay event:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/events/proactive-delay" ^
  -H "Content-Type: application/json" ^
  -d "{\"shipment_id\":\"SHP-9002\",\"event_type\":\"shipment_no_update_48h\"}"
```

Admin read routes:

```text
GET /api/v1/admin/cases
GET /api/v1/admin/cases/{case_id}
POST /api/v1/admin/cases/{case_id}/close
GET /api/v1/admin/approvals
POST /api/v1/admin/approvals/{approval_id}/approve
POST /api/v1/admin/approvals/{approval_id}/reject
GET /api/v1/admin/refund-requests
GET /api/v1/admin/proactive-alerts
POST /api/v1/admin/proactive-alerts/{alert_id}/resolve
```

Business data read routes:

```text
GET /api/v1/data/customers/{customer_id}/orders
GET /api/v1/data/orders/{order_id}
GET /api/v1/data/customers/{customer_id}/shipments
GET /api/v1/data/shipments/{shipment_id}
GET /api/v1/data/customers/{customer_id}/conversations
GET /api/v1/data/conversations/{conversation_id}
GET /api/v1/data/conversations/{conversation_id}/messages
```

Each chat execution now also writes:

```text
- agent_traces
- tool_logs
- customer/ai messages in conversations
```

## Docker

From the repo root:

```bash
docker compose up --build
```

## Alembic

From `backend/`:

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

Recommended migration workflow:

```text
1. Update SQLAlchemy models first
2. Run: alembic revision --autogenerate -m "describe change"
3. Review the generated migration file carefully
4. Run: alembic upgrade head
```

Notes:

```text
- Do not create a new Alembic revision if models did not change.
- If autogenerate produces an empty migration, delete that migration file instead of keeping noisy history.
- The current initial migration is:
  488c75bf3411_init_schema.py
```

Windows + .venv example:

```powershell
.\.venv\Scripts\Activate.ps1
cd backend
alembic revision --autogenerate -m "add new field"
alembic upgrade head
```

## Tests

From `backend/`:

```bash
pytest
```

Example API call after seeding:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/chat" ^
  -H "Content-Type: application/json" ^
  -d "{\"customer_id\":\"CUST-001\",\"conversation_id\":\"CONV-001\",\"message\":\"ของฉันอยู่ไหนแล้ว\"}"
```
