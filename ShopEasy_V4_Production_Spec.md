# ShopEasy — V4 Production Specification
## Autonomous AI Tool Pipeline + Shopify-Ready Deployment

> **Version 4.0 — Production Release Spec**  
> สร้างขึ้นจาก V3 Reference ที่ implement ครบแล้ว  
> อัปเดต: 11 พฤษภาคม 2026  
>  
> **เป้าหมายหลัก:**  
> 1. AI เลือก tool และสร้าง pipeline เองโดยอัตโนมัติ (ไม่ต้อง hardcode workflow)  
> 2. Output ของ tool หนึ่งไหลเป็น input ของ tool ถัดไปอัตโนมัติ (Tool Chaining)  
> 3. ระบบพร้อม deploy บน Shopify/cloud ได้ 100%

---

## สารบัญ

1. [สิ่งที่มีแล้ว (V3 Complete)](#1-สิ่งที่มีแล้ว-v3-complete)
2. [V4 Feature ที่ต้องสร้าง](#2-v4-feature-ที่ต้องสร้าง)
3. [Autonomous Tool Selection Architecture](#3-autonomous-tool-selection-architecture)
4. [Tool Registry และ Tool Chaining](#4-tool-registry-และ-tool-chaining)
5. [ReAct Engine (Full Implementation)](#5-react-engine-full-implementation)
6. [Planning Layer (Full Implementation)](#6-planning-layer-full-implementation)
7. [3-Layer Memory System](#7-3-layer-memory-system)
8. [Error Recovery + Circuit Breaker](#8-error-recovery--circuit-breaker)
9. [Supervisor Agent (Full)](#9-supervisor-agent-full)
10. [Qdrant Policy RAG](#10-qdrant-policy-rag)
11. [Production Deployment — Shopify App](#11-production-deployment--shopify-app)
12. [Database Migrations V4](#12-database-migrations-v4)
13. [Implementation Prompts](#13-implementation-prompts)

---

# 1. สิ่งที่มีแล้ว (V3 Complete)

| Component | Status | รายละเอียด |
|-----------|--------|-----------|
| Docker Compose (5 services) | ✅ | db, backend, frontend, redis, minio |
| PostgreSQL Schema (28 tables) | ✅ | Alembic migrations |
| FastAPI Backend (8 route groups) | ✅ | auth, chat, data, admin, ai, events, attachments, health |
| LangGraph Workflow 01 — Tracking | ✅ | StateGraph, 7 nodes |
| LangGraph Workflow 02 — Refund | ✅ | Sequential pipeline, 13 nodes |
| LangGraph Workflow 03 — Proactive | ✅ | Event-driven, risk scoring |
| Human-in-the-Loop (Approval) | ✅ | Admin approve/reject, risk threshold 70 |
| MinIO Evidence Upload | ✅ | Presign upload + confirm |
| Observability (AgentTrace + ToolLog) | ✅ | persist_workflow_observability() |
| Frontend 3 Portals | ✅ | Customer, Admin, AI Control |
| Google OAuth Login | ✅ | GSI + backend token verification |
| Mock Auth (3 roles) | ✅ | customer, admin, ai_control |
| Proactive Alert Endpoint | ✅ | POST /events/proactive-delay |

**สิ่งที่ยังไม่มี (V4 จะสร้าง):**

| Component | Priority |
|-----------|---------|
| Autonomous Tool Selection (AI เลือก tool เอง) | 🔴 Critical |
| Tool Chaining (output → input อัตโนมัติ) | 🔴 Critical |
| ReAct Loop Engine | 🔴 Critical |
| Planning Layer + Dynamic Replanning | 🟠 High |
| 3-Layer Memory (Redis + PostgreSQL) | 🟠 High |
| Qdrant Policy RAG | 🟡 Medium |
| Error Recovery + Circuit Breaker | 🟡 Medium |
| Supervisor Agent (Full) | 🟡 Medium |
| Shopify App Bridge + Webhook | 🔴 Critical (Deploy) |
| Production Config (env, secrets, SSL) | 🔴 Critical (Deploy) |

---

# 2. V4 Feature ที่ต้องสร้าง

## 2.1 Autonomous Tool Pipeline

แทนที่ workflow แบบ hardcode (A→B→C เสมอ), V4 ให้ LLM ตัดสินใจว่าจะใช้ tool อะไร จะเรียงลำดับยังไง และ output ของ tool ก่อนหน้าจะถูกส่งต่อไปอัตโนมัติ

```
ก่อน V4 (Hardcode):
  refund_router → context_resolution → policy_rag → risk_calc → create_refund → respond

หลัง V4 (Autonomous):
  LLM ได้รับ: intent + customer context + available tools
  LLM ตัดสินใจ: [get_order_detail] → [search_policy] → [calculate_risk] → [create_refund]
  Output ของแต่ละ tool ไหลเข้า tool ถัดไปอัตโนมัติผ่าน ToolChain
```

## 2.2 Tool Chaining

```
Tool A output → schema mapping → Tool B input
                ↓
             ToolChain validates & transforms automatically
```

## 2.3 Shopify Deployment

- **Shopify App Bridge** สำหรับ embed ใน Shopify Admin
- **Shopify Webhook** รับ event จาก Shopify (order/fulfillment/refund)
- **Environment-based config** สำหรับทุก secret
- **Health checks + graceful shutdown** สำหรับ production container

---

# 3. Autonomous Tool Selection Architecture

## 3.1 ภาพรวม

```
Customer Message
      │
      ▼
  IntentRouter (LLM)
      │
      ▼
  ToolSelector (LLM + Tool Registry)
  - รับ: intent + customer context + TOOL_REGISTRY
  - ส่งออก: ToolExecutionPlan (ordered list of tool calls)
      │
      ▼
  ToolChainExecutor
  - Execute ทีละ tool
  - Map output → input ถัดไปอัตโนมัติ
  - Handle errors ด้วย ErrorRecovery
      │
      ▼
  SupervisorAgent
  - ตรวจ quality ของผล
  - Approve หรือ escalate
      │
      ▼
  ResponseGenerator
      │
      ▼
  Customer Response
```

## 3.2 Tool Selector Prompt

```python
TOOL_SELECTOR_SYSTEM_PROMPT = """
คุณคือ AI ที่ทำหน้าที่เลือก tool และออกแบบ pipeline สำหรับจัดการคำขอของลูกค้า

## TOOLS ที่ใช้ได้
{available_tools}

## CONTEXT
- Intent: {intent}
- Customer: {customer_summary}
- History: {memory_summary}

## หลักการเลือก tool
1. เลือกเฉพาะ tool ที่จำเป็น ไม่ต้องใช้ทุกอัน
2. เรียงลำดับที่สมเหตุสมผล (ต้องรู้ order ก่อนจะคำนวณ risk)
3. ระบุว่า output field ของ tool ก่อนหน้าจะไปใส่ input field ใดของ tool ถัดไป
4. ถ้าไม่แน่ใจ ให้ escalate ไม่ใช่เดา

## OUTPUT FORMAT (JSON เท่านั้น)
{
  "reasoning": "อธิบายว่าทำไมถึงเลือก tool เหล่านี้",
  "steps": [
    {
      "step": 1,
      "tool": "get_order_detail",
      "params": {"order_id": "{{context.order_id}}"},
      "output_mapping": {"order.total": "next.order_total", "order.status": "next.order_status"}
    },
    {
      "step": 2,
      "tool": "calculate_risk_score",
      "params": {"order_total": "{{step_1.order_total}}"},
      "output_mapping": {"risk_score": "next.risk_score"}
    }
  ],
  "requires_human": false,
  "estimated_steps": 3
}
"""
```

## 3.3 Implementation

### ไฟล์ที่ต้องสร้าง

```
backend/app/agents/
├── tool_selector.py         # LLM-based tool selection
├── tool_chain_executor.py   # Execute chain + output→input mapping
├── tool_registry.py         # Register all available tools
├── react_engine.py          # ReAct loop
├── planner.py               # Planning + replanning
├── supervisor_agent.py      # Full supervisor
└── memory/
    ├── short_term.py        # Redis-based session memory
    ├── long_term.py         # PostgreSQL customer memory
    └── episodic.py          # Event-based episodic memory
```

---

# 4. Tool Registry และ Tool Chaining

## 4.1 Tool Registry

ทุก tool ที่ AI สามารถเลือกได้ต้องลงทะเบียนใน `ToolRegistry` พร้อม schema ของ input/output

```python
# backend/app/agents/tool_registry.py

from dataclasses import dataclass, field
from typing import Any, Callable, Type
from pydantic import BaseModel


@dataclass
class ToolDefinition:
    name: str                        # ชื่อ tool (unique)
    description: str                 # อธิบายให้ LLM เข้าใจ
    input_schema: Type[BaseModel]    # Pydantic model สำหรับ input
    output_schema: Type[BaseModel]   # Pydantic model สำหรับ output
    handler: Callable                # ฟังก์ชันที่รันจริง
    tags: list[str] = field(default_factory=list)  # ["tracking", "refund", "proactive"]
    requires_db: bool = False        # ต้องการ DB session หรือไม่
    max_retries: int = 3
    timeout_seconds: int = 10


class ToolRegistry:
    _tools: dict[str, ToolDefinition] = {}

    @classmethod
    def register(cls, tool: ToolDefinition):
        cls._tools[tool.name] = tool

    @classmethod
    def get(cls, name: str) -> ToolDefinition:
        if name not in cls._tools:
            raise ValueError(f"Tool '{name}' not found in registry")
        return cls._tools[name]

    @classmethod
    def list_for_llm(cls, tags: list[str] | None = None) -> list[dict]:
        """ส่งคืน tool descriptions สำหรับ LLM prompt"""
        tools = cls._tools.values()
        if tags:
            tools = [t for t in tools if any(tag in t.tags for tag in tags)]
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_fields": list(t.input_schema.model_fields.keys()),
                "output_fields": list(t.output_schema.model_fields.keys()),
            }
            for t in tools
        ]
```

## 4.2 Tool Definitions (ทุก tool ที่มี)

```python
# backend/app/agents/tools/definitions.py

from app.agents.tool_registry import ToolRegistry, ToolDefinition

# --- Tracking Tools ---
ToolRegistry.register(ToolDefinition(
    name="get_order_detail",
    description="โหลดรายละเอียด order รวมถึง status, items, total amount",
    input_schema=GetOrderInput,
    output_schema=GetOrderOutput,
    handler=handle_get_order_detail,
    tags=["tracking", "refund"],
    requires_db=True,
))

ToolRegistry.register(ToolDefinition(
    name="get_shipment_status",
    description="โหลดสถานะการจัดส่งล่าสุดรวม events timeline",
    input_schema=GetShipmentInput,
    output_schema=GetShipmentOutput,
    handler=handle_get_shipment_status,
    tags=["tracking", "proactive"],
    requires_db=True,
))

ToolRegistry.register(ToolDefinition(
    name="build_tracking_response",
    description="สร้างข้อความตอบลูกค้าเกี่ยวกับสถานะ shipment",
    input_schema=TrackingResponseInput,
    output_schema=TrackingResponseOutput,
    handler=handle_build_tracking_response,
    tags=["tracking"],
))

# --- Refund Tools ---
ToolRegistry.register(ToolDefinition(
    name="calculate_refund_risk",
    description="คำนวณ risk score สำหรับการคืนเงิน (0-100)",
    input_schema=RefundRiskInput,
    output_schema=RefundRiskOutput,
    handler=handle_calculate_refund_risk,
    tags=["refund"],
))

ToolRegistry.register(ToolDefinition(
    name="create_refund_request",
    description="สร้าง RefundRequest และ Case ในฐานข้อมูล",
    input_schema=CreateRefundInput,
    output_schema=CreateRefundOutput,
    handler=handle_create_refund_request,
    tags=["refund"],
    requires_db=True,
))

ToolRegistry.register(ToolDefinition(
    name="evaluate_evidence",
    description="ประเมิน evidence ที่ลูกค้าแนบมา (รูป/วิดีโอ)",
    input_schema=EvidenceInput,
    output_schema=EvidenceOutput,
    handler=handle_evaluate_evidence,
    tags=["refund"],
    requires_db=True,
))

ToolRegistry.register(ToolDefinition(
    name="request_human_approval",
    description="ส่งคำขออนุมัติให้ admin เมื่อ risk score สูง",
    input_schema=ApprovalRequestInput,
    output_schema=ApprovalRequestOutput,
    handler=handle_request_human_approval,
    tags=["refund", "proactive"],
    requires_db=True,
))

# --- Policy Tools ---
ToolRegistry.register(ToolDefinition(
    name="search_policy",
    description="ค้นหา policy ที่เกี่ยวข้องกับสถานการณ์ (vector search)",
    input_schema=PolicySearchInput,
    output_schema=PolicySearchOutput,
    handler=handle_search_policy,
    tags=["refund", "tracking", "proactive"],
    requires_db=True,
))

# --- Proactive Tools ---
ToolRegistry.register(ToolDefinition(
    name="calculate_delay_risk",
    description="คำนวณความเสี่ยงของการล่าช้า shipment",
    input_schema=DelayRiskInput,
    output_schema=DelayRiskOutput,
    handler=handle_calculate_delay_risk,
    tags=["proactive"],
))

ToolRegistry.register(ToolDefinition(
    name="create_proactive_alert",
    description="สร้าง ProactiveAlert และ notification ให้ลูกค้า",
    input_schema=ProactiveAlertInput,
    output_schema=ProactiveAlertOutput,
    handler=handle_create_proactive_alert,
    tags=["proactive"],
    requires_db=True,
))

# --- Memory Tools ---
ToolRegistry.register(ToolDefinition(
    name="recall_customer_memory",
    description="ดึง long-term memory ของลูกค้า (พฤติกรรม, ประวัติ)",
    input_schema=RecallMemoryInput,
    output_schema=RecallMemoryOutput,
    handler=handle_recall_customer_memory,
    tags=["tracking", "refund", "proactive"],
    requires_db=True,
))
```

## 4.3 Tool Chain Executor

```python
# backend/app/agents/tool_chain_executor.py

import json
from typing import Any
from app.agents.tool_registry import ToolRegistry
from app.agents.error_recovery import ErrorRecoverySystem


class ToolChainExecutor:
    """Execute tool chain ตาม plan ที่ LLM สร้าง และ map output → input อัตโนมัติ"""

    def __init__(self, db=None):
        self.db = db
        self.recovery = ErrorRecoverySystem()
        self.step_results: dict[int, Any] = {}  # เก็บผลแต่ละ step

    async def execute(self, plan: list[dict], context: dict) -> dict:
        """
        plan: [{"step": 1, "tool": "...", "params": {...}, "output_mapping": {...}}, ...]
        context: initial context (customer_id, order_id, etc.)
        """
        accumulated_context = dict(context)

        for step_def in plan:
            step_num = step_def["step"]
            tool_name = step_def["tool"]
            raw_params = step_def.get("params", {})
            output_mapping = step_def.get("output_mapping", {})

            # Resolve params — แทนที่ {{placeholder}} ด้วยค่าจริง
            resolved_params = self._resolve_params(raw_params, accumulated_context)

            # Execute tool พร้อม error recovery
            tool_def = ToolRegistry.get(tool_name)
            kwargs = {}
            if tool_def.requires_db:
                kwargs["db"] = self.db

            result = await self.recovery.execute_with_recovery(
                tool_name=tool_name,
                params=resolved_params,
                handler=tool_def.handler,
                kwargs=kwargs,
            )

            if not result.success:
                if result.escalate:
                    return {"error": f"Tool {tool_name} failed", "escalate": True, "step": step_num}
                continue

            # เก็บผล step นี้
            self.step_results[step_num] = result.data

            # Map output → accumulated context สำหรับ step ถัดไป
            self._apply_output_mapping(result.data, output_mapping, accumulated_context, step_num)

        return {"results": self.step_results, "context": accumulated_context, "success": True}

    def _resolve_params(self, params: dict, context: dict) -> dict:
        """แทนที่ {{context.field}} และ {{step_N.field}} ด้วยค่าจริง"""
        resolved = {}
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
                path = value[2:-2].strip()
                resolved[key] = self._resolve_path(path, context)
            else:
                resolved[key] = value
        return resolved

    def _resolve_path(self, path: str, context: dict) -> Any:
        """Resolve 'step_1.order_total' หรือ 'context.customer_id'"""
        parts = path.split(".", 1)
        root = parts[0]
        remainder = parts[1] if len(parts) > 1 else None

        if root.startswith("step_"):
            step_num = int(root.replace("step_", ""))
            base = self.step_results.get(step_num, {})
        elif root == "context":
            base = context
        else:
            base = context.get(root)

        if remainder and isinstance(base, dict):
            return base.get(remainder)
        return base

    def _apply_output_mapping(self, output: Any, mapping: dict, context: dict, step_num: int):
        """เพิ่มผล output เข้า accumulated context ตาม mapping"""
        if not mapping or not isinstance(output, dict):
            return
        for output_field, target_key in mapping.items():
            value = output.get(output_field)
            if value is not None:
                # target_key เช่น "next.order_total" หรือ "context.risk_score"
                clean_key = target_key.replace("next.", "").replace("context.", "")
                context[clean_key] = value
                # เก็บด้วยชื่อ step เพื่อ reference ภายหลัง
                step_key = f"step_{step_num}.{output_field}"
                context[step_key] = value
```

---

# 5. ReAct Engine (Full Implementation)

## 5.1 Overview

ReAct Engine เป็นตัวขับ Autonomous Tool Pipeline โดยวน loop:  
**Thought → Action (Tool) → Observe → Reflect → (loop or Finish)**

## 5.2 Full Implementation

```python
# backend/app/agents/react_engine.py

from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import Any

from app.agents.tool_selector import ToolSelector
from app.agents.tool_chain_executor import ToolChainExecutor
from app.agents.tool_registry import ToolRegistry
from app.agents.memory.short_term import ShortTermMemory
from app.agents.error_recovery import ErrorRecoverySystem


@dataclass
class ReActObservation:
    iteration: int
    thought: str
    action: str          # tool name หรือ "FINISH" หรือ "ESCALATE"
    params: dict
    result: Any
    success: bool
    used_fallback: bool = False


@dataclass
class ReActState:
    intent: str
    customer_id: str
    context: dict = field(default_factory=dict)
    observations: list[ReActObservation] = field(default_factory=list)
    final_response: str = ""
    react_done: bool = False
    escalate: bool = False
    replan_count: int = 0
    total_tool_calls: int = 0


class ReActEngine:
    MAX_ITERATIONS = 8

    def __init__(self, db=None, session_id: str = ""):
        self.db = db
        self.session_id = session_id
        self.tool_selector = ToolSelector()
        self.executor = ToolChainExecutor(db=db)
        self.memory = ShortTermMemory(session_id) if session_id else None

    async def run(self, intent: str, customer_id: str, initial_context: dict) -> ReActState:
        state = ReActState(intent=intent, customer_id=customer_id, context=initial_context)

        # โหลด memory ก่อนถ้ามี
        if self.memory:
            cached = await self.memory.get("last_context")
            if cached:
                state.context.update(cached)

        for iteration in range(self.MAX_ITERATIONS):
            # THOUGHT — ให้ LLM คิดว่าควรทำอะไรต่อ
            thought_result = await self.tool_selector.think(
                intent=state.intent,
                context=state.context,
                observations=state.observations,
                available_tools=ToolRegistry.list_for_llm(),
            )

            action = thought_result.get("action", "FINISH")

            if action == "FINISH":
                state.final_response = thought_result.get("response", "")
                state.react_done = True
                break

            if action == "ESCALATE":
                state.escalate = True
                break

            # ACTION — execute tool
            tool_name = action
            params = thought_result.get("params", {})

            tool_def = ToolRegistry.get(tool_name)
            kwargs = {"db": self.db} if tool_def.requires_db else {}

            recovery = ErrorRecoverySystem()
            result = await recovery.execute_with_recovery(
                tool_name=tool_name,
                params=params,
                handler=tool_def.handler,
                kwargs=kwargs,
            )

            state.total_tool_calls += 1

            # OBSERVE — บันทึกผลลัพธ์
            obs = ReActObservation(
                iteration=iteration,
                thought=thought_result.get("reasoning", ""),
                action=tool_name,
                params=params,
                result=result.data if result.success else result.error,
                success=result.success,
                used_fallback=result.used_fallback,
            )
            state.observations.append(obs)

            # อัป context ด้วยผลที่ได้
            if result.success and isinstance(result.data, dict):
                state.context.update(result.data)

            # REFLECT — ตรวจว่าพอแล้วหรือยัง
            if result.escalate:
                state.escalate = True
                break

        # บันทึก memory
        if self.memory:
            await self.memory.save("last_context", state.context)

        return state
```

## 5.3 Tool Selector (LLM Think Function)

```python
# backend/app/agents/tool_selector.py

import json
from app.agents.llm import get_llm_client

THINK_PROMPT = """
คุณคือ AI Agent ที่กำลังจัดการคำขอของลูกค้า

## สถานการณ์ปัจจุบัน
- Intent: {intent}
- Context ที่มีอยู่: {context_summary}
- สิ่งที่ทำไปแล้ว: {observations_summary}

## Tools ที่ใช้ได้
{tools_json}

## ตัดสินใจ (เลือก 1 อย่าง)
1. เรียก tool → ระบุ tool name + params
2. FINISH → ถ้ามีข้อมูลพอที่จะตอบลูกค้าแล้ว
3. ESCALATE → ถ้าไม่สามารถจัดการได้หรือ risk สูงมาก

ตอบเป็น JSON:
{
  "reasoning": "...",
  "action": "tool_name หรือ FINISH หรือ ESCALATE",
  "params": {},
  "response": "ข้อความตอบลูกค้า (ถ้า action = FINISH)"
}
"""


class ToolSelector:
    def __init__(self):
        self.llm = get_llm_client()

    async def think(self, intent: str, context: dict, observations: list, available_tools: list) -> dict:
        obs_summary = "\n".join(
            f"- ใช้ {o.action}: {'สำเร็จ' if o.success else 'ล้มเหลว'}"
            for o in observations[-3:]  # แสดงแค่ 3 อันล่าสุด
        )
        context_summary = ", ".join(f"{k}={v}" for k, v in list(context.items())[:8])

        prompt = THINK_PROMPT.format(
            intent=intent,
            context_summary=context_summary,
            observations_summary=obs_summary or "ยังไม่ได้ทำอะไร",
            tools_json=json.dumps(available_tools, ensure_ascii=False, indent=2),
        )

        response = await self.llm.chat(prompt)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"action": "ESCALATE", "reasoning": "LLM ตอบ format ผิด"}
```

---

# 6. Planning Layer (Full Implementation)

## 6.1 Execution Plan

AI สร้าง plan ก่อน execute ทำให้ตรวจสอบได้ ปรับแผนได้ และ audit ง่าย

```python
# backend/app/agents/planner.py

from __future__ import annotations
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.agents.llm import get_llm_client

PLAN_PROMPT = """
สร้าง execution plan สำหรับ intent นี้

## Intent: {intent}
## Customer Context: {context_json}
## Tools ที่ใช้ได้: {tools_json}

สร้าง plan เป็น JSON:
{
  "plan_id": "PLAN-xxx",
  "reasoning": "เหตุผลที่เลือก steps เหล่านี้",
  "steps": [
    {
      "step": 1,
      "tool": "tool_name",
      "description": "อธิบายว่าทำอะไร",
      "params": {"key": "{{context.field}} หรือค่าตรง"},
      "output_mapping": {"output_field": "next.input_field"},
      "depends_on": [],
      "fallback_tool": "alternative_tool หรือ null"
    }
  ],
  "requires_human_approval": false,
  "risk_level": "low | medium | high",
  "estimated_steps": 3
}
"""

REPLAN_PROMPT = """
Plan เดิมล้มเหลวที่ step {failed_step}
เหตุผล: {failure_reason}

Steps ที่ทำสำเร็จแล้ว: {completed_steps}
Context ที่มีอยู่: {context_json}
Tools ที่ใช้ได้: {tools_json}

สร้าง plan ใหม่สำหรับ steps ที่เหลือ (JSON เหมือนเดิม แต่ไม่ต้องมี steps ที่เสร็จแล้ว)
"""


@dataclass
class PlanStep:
    step: int
    tool: str
    description: str
    params: dict
    output_mapping: dict = field(default_factory=dict)
    depends_on: list[int] = field(default_factory=list)
    fallback_tool: str | None = None
    status: str = "pending"   # pending | running | done | failed
    error: str | None = None


@dataclass
class ExecutionPlan:
    plan_id: str
    intent: str
    steps: list[PlanStep]
    reasoning: str
    requires_human_approval: bool = False
    risk_level: str = "low"
    created_at: datetime = field(default_factory=datetime.utcnow)
    replan_count: int = 0

    def completed_steps(self) -> list[int]:
        return [s.step for s in self.steps if s.status == "done"]

    def next_step(self) -> PlanStep | None:
        return next((s for s in self.steps if s.status == "pending"), None)


class Planner:
    def __init__(self):
        self.llm = get_llm_client()

    async def create_plan(self, intent: str, context: dict, available_tools: list) -> ExecutionPlan:
        prompt = PLAN_PROMPT.format(
            intent=intent,
            context_json=json.dumps(context, ensure_ascii=False, default=str),
            tools_json=json.dumps(available_tools, ensure_ascii=False, indent=2),
        )
        response = await self.llm.chat(prompt)
        data = json.loads(response)
        steps = [PlanStep(**s) for s in data["steps"]]
        return ExecutionPlan(
            plan_id=data.get("plan_id", f"PLAN-{uuid.uuid4().hex[:8].upper()}"),
            intent=intent,
            steps=steps,
            reasoning=data.get("reasoning", ""),
            requires_human_approval=data.get("requires_human_approval", False),
            risk_level=data.get("risk_level", "low"),
        )

    async def replan(self, plan: ExecutionPlan, failed_step: PlanStep, context: dict, available_tools: list) -> ExecutionPlan:
        prompt = REPLAN_PROMPT.format(
            failed_step=failed_step.step,
            failure_reason=failed_step.error,
            completed_steps=plan.completed_steps(),
            context_json=json.dumps(context, ensure_ascii=False, default=str),
            tools_json=json.dumps(available_tools, ensure_ascii=False, indent=2),
        )
        response = await self.llm.chat(prompt)
        data = json.loads(response)
        new_steps = [PlanStep(**s) for s in data["steps"]]
        plan.steps = [s for s in plan.steps if s.status == "done"] + new_steps
        plan.replan_count += 1
        return plan
```

---

# 7. 3-Layer Memory System

## 7.1 Short-term Memory (Redis)

```python
# backend/app/agents/memory/short_term.py

import json
from typing import Any
import redis.asyncio as aioredis
from app.core.config import get_settings


class ShortTermMemory:
    TTL = 86400  # 24 ชั่วโมง

    def __init__(self, session_id: str):
        settings = get_settings()
        self.redis = aioredis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            decode_responses=True,
        )
        self.key = f"session:{session_id}"

    async def save(self, field: str, value: Any):
        await self.redis.hset(self.key, field, json.dumps(value, default=str))
        await self.redis.expire(self.key, self.TTL)

    async def get(self, field: str) -> Any | None:
        val = await self.redis.hget(self.key, field)
        return json.loads(val) if val else None

    async def get_all(self) -> dict:
        data = await self.redis.hgetall(self.key)
        return {k: json.loads(v) for k, v in data.items()}

    async def clear(self):
        await self.redis.delete(self.key)
```

## 7.2 Long-term Memory (PostgreSQL)

### Migration ที่ต้องสร้าง

```python
# alembic/versions/e1f2a3b4c5d6_add_customer_memory.py

def upgrade():
    op.create_table(
        "customer_long_term_memory",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("memory_type", sa.String(50)),       # behavior | preference | pattern | risk
        sa.Column("key", sa.String(100)),
        sa.Column("value", postgresql.JSONB),
        sa.Column("confidence", sa.Float, default=1.0),
        sa.Column("source_agent", sa.String(50)),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), onupdate=sa.text("now()")),
    )
    op.create_index("ix_customer_memory_customer_id", "customer_long_term_memory", ["customer_id"])
    op.create_index("ix_customer_memory_key", "customer_long_term_memory", ["key"])
```

### Service

```python
# backend/app/agents/memory/long_term.py

from sqlalchemy.orm import Session
from app.db.models import CustomerLongTermMemory


class LongTermMemory:
    def __init__(self, db: Session, customer_id: str):
        self.db = db
        self.customer_id = customer_id

    def save(self, memory_type: str, key: str, value: dict, source_agent: str = "system"):
        existing = (
            self.db.query(CustomerLongTermMemory)
            .filter_by(customer_id=self.customer_id, key=key)
            .first()
        )
        if existing:
            existing.value = value
            existing.source_agent = source_agent
        else:
            self.db.add(CustomerLongTermMemory(
                customer_id=self.customer_id,
                memory_type=memory_type,
                key=key,
                value=value,
                source_agent=source_agent,
            ))
        self.db.flush()

    def get(self, key: str) -> dict | None:
        record = (
            self.db.query(CustomerLongTermMemory)
            .filter_by(customer_id=self.customer_id, key=key)
            .first()
        )
        return record.value if record else None

    def get_all(self) -> list[dict]:
        records = (
            self.db.query(CustomerLongTermMemory)
            .filter_by(customer_id=self.customer_id)
            .all()
        )
        return [{"key": r.key, "value": r.value, "type": r.memory_type} for r in records]

    def build_summary(self) -> str:
        all_mem = self.get_all()
        if not all_mem:
            return "ไม่มี memory ของลูกค้าคนนี้"
        lines = [f"- {m['key']}: {m['value']}" for m in all_mem[:10]]
        return "Long-term memory:\n" + "\n".join(lines)
```

## 7.3 Episodic Memory

```python
# backend/app/agents/memory/episodic.py
# เก็บ event สำคัญ เช่น fraud attempt, escalation, dispute

from sqlalchemy.orm import Session
from app.db.models import CustomerEpisodicMemory  # ต้อง migrate


class EpisodicMemory:
    def __init__(self, db: Session, customer_id: str):
        self.db = db
        self.customer_id = customer_id

    def store(self, event_type: str, summary: str, metadata: dict):
        self.db.add(CustomerEpisodicMemory(
            customer_id=self.customer_id,
            event_type=event_type,   # fraud | escalation | dispute | refund_abuse
            summary=summary,
            metadata=metadata,
        ))
        self.db.flush()

    def recall(self, event_types: list[str] | None = None) -> list[dict]:
        q = self.db.query(CustomerEpisodicMemory).filter_by(customer_id=self.customer_id)
        if event_types:
            q = q.filter(CustomerEpisodicMemory.event_type.in_(event_types))
        return [
            {"type": e.event_type, "summary": e.summary, "metadata": e.metadata, "created_at": str(e.created_at)}
            for e in q.order_by(CustomerEpisodicMemory.created_at.desc()).limit(10).all()
        ]
```

---

# 8. Error Recovery + Circuit Breaker

## 8.1 Error Recovery System

```python
# backend/app/agents/error_recovery.py

import asyncio
import inspect
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class ToolResult:
    success: bool
    data: Any = None
    error: str = ""
    used_fallback: bool = False
    escalate: bool = False


FALLBACK_MAP: dict[str, str] = {
    "get_shipment_status":     "get_shipment_from_db_direct",
    "search_policy":           "get_all_policies_fallback",
    "calculate_refund_risk":   "use_default_risk_medium",
    "get_order_detail":        "get_order_from_db_direct",
    "evaluate_evidence":       "use_default_evidence_insufficient",
}


class ErrorRecoverySystem:
    async def execute_with_recovery(
        self,
        tool_name: str,
        params: dict,
        handler: Callable,
        kwargs: dict | None = None,
    ) -> ToolResult:
        kwargs = kwargs or {}
        # Level 1: Retry with exponential backoff
        for attempt in range(1, 4):
            try:
                if inspect.iscoroutinefunction(handler):
                    result = await handler(**params, **kwargs)
                else:
                    result = handler(**params, **kwargs)
                return ToolResult(success=True, data=result if isinstance(result, dict) else {"result": result})
            except Exception as exc:
                if attempt == 3:
                    last_error = str(exc)
                else:
                    await asyncio.sleep(2 ** attempt)

        # Level 2: Fallback
        fallback_name = FALLBACK_MAP.get(tool_name)
        if fallback_name:
            try:
                from app.agents.tool_registry import ToolRegistry
                fallback_def = ToolRegistry.get(fallback_name)
                if inspect.iscoroutinefunction(fallback_def.handler):
                    result = await fallback_def.handler(**params, **kwargs)
                else:
                    result = fallback_def.handler(**params, **kwargs)
                return ToolResult(success=True, data=result, used_fallback=True)
            except Exception:
                pass

        # Level 3: Escalate
        return ToolResult(success=False, error=last_error, escalate=True)
```

## 8.2 Circuit Breaker

```python
# backend/app/agents/circuit_breaker.py

import time
from collections import defaultdict


class CircuitBreaker:
    """CLOSED → (threshold fails) → OPEN → (timeout) → HALF_OPEN → (success) → CLOSED"""

    _state: dict[str, str] = defaultdict(lambda: "CLOSED")
    _fail_count: dict[str, int] = defaultdict(int)
    _open_time: dict[str, float] = {}
    THRESHOLD = 5
    TIMEOUT = 60  # วินาที

    @classmethod
    def can_execute(cls, tool_name: str) -> bool:
        state = cls._state[tool_name]
        if state == "CLOSED":
            return True
        if state == "OPEN":
            if time.time() - cls._open_time.get(tool_name, 0) > cls.TIMEOUT:
                cls._state[tool_name] = "HALF_OPEN"
                return True
            return False
        return True  # HALF_OPEN — ลองอีกครั้ง

    @classmethod
    def record_success(cls, tool_name: str):
        cls._fail_count[tool_name] = 0
        cls._state[tool_name] = "CLOSED"

    @classmethod
    def record_failure(cls, tool_name: str):
        cls._fail_count[tool_name] += 1
        if cls._fail_count[tool_name] >= cls.THRESHOLD:
            cls._state[tool_name] = "OPEN"
            cls._open_time[tool_name] = time.time()
```

---

# 9. Supervisor Agent (Full)

```python
# backend/app/agents/supervisor_agent.py

from __future__ import annotations
from dataclasses import dataclass
from app.agents.tool_registry import ToolRegistry
from app.agents.llm import get_llm_client


QUALITY_PROMPT = """
ประเมินคุณภาพของ response นี้

Intent: {intent}
Customer Question: {customer_message}
Agent Response: {response}
Tools Used: {tools_used}

ประเมินเป็น JSON:
{
  "quality_score": 0.0-1.0,
  "issues": ["ปัญหาที่พบ"],
  "requires_human": true/false,
  "reason": "เหตุผล"
}
"""


@dataclass
class SupervisionResult:
    approved: bool
    quality_score: float
    requires_human: bool
    issues: list[str]
    reason: str


class SupervisorAgent:
    QUALITY_THRESHOLD = 0.6
    HIGH_RISK_SCORE = 70

    def __init__(self):
        self.llm = get_llm_client()

    async def supervise(
        self,
        intent: str,
        customer_message: str,
        response: str,
        risk_score: int,
        replan_count: int,
        tools_used: list[str],
    ) -> SupervisionResult:
        # Rule-based checks ก่อน (ไม่เสีย LLM token)
        if risk_score >= self.HIGH_RISK_SCORE:
            return SupervisionResult(
                approved=False, quality_score=0.5,
                requires_human=True, issues=["High risk score"],
                reason=f"Risk score {risk_score} ≥ {self.HIGH_RISK_SCORE}",
            )
        if replan_count >= 2:
            return SupervisionResult(
                approved=False, quality_score=0.4,
                requires_human=True, issues=["Too many replans"],
                reason="Replanned ≥ 2 ครั้ง — ส่ง human",
            )

        # LLM quality check
        prompt = QUALITY_PROMPT.format(
            intent=intent,
            customer_message=customer_message,
            response=response,
            tools_used=", ".join(tools_used),
        )
        result_text = await self.llm.chat(prompt)
        try:
            import json
            data = json.loads(result_text)
        except Exception:
            data = {"quality_score": 0.5, "issues": [], "requires_human": False, "reason": "parse error"}

        score = float(data.get("quality_score", 0.5))
        return SupervisionResult(
            approved=score >= self.QUALITY_THRESHOLD and not data.get("requires_human"),
            quality_score=score,
            requires_human=data.get("requires_human", False),
            issues=data.get("issues", []),
            reason=data.get("reason", ""),
        )
```

---

# 10. Qdrant Policy RAG

## 10.1 Setup Qdrant ใน Docker Compose

```yaml
# เพิ่มใน docker-compose.yml

  qdrant:
    image: qdrant/qdrant:latest
    container_name: shopeasy-qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  qdrant_data:
```

## 10.2 Policy Ingestion Pipeline

```python
# backend/app/services/policy_rag.py (อัปเดตจาก keyword search)

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import openai
import uuid

COLLECTION_NAME = "policies"
VECTOR_SIZE = 1536  # text-embedding-3-small


class PolicyRAGService:
    def __init__(self):
        self.qdrant = QdrantClient(host="qdrant", port=6333)
        self._ensure_collection()

    def _ensure_collection(self):
        existing = [c.name for c in self.qdrant.get_collections().collections]
        if COLLECTION_NAME not in existing:
            self.qdrant.create_collection(
                COLLECTION_NAME,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )

    def _embed(self, text: str) -> list[float]:
        response = openai.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )
        return response.data[0].embedding

    def ingest_policy(self, policy_id: str, title: str, content: str):
        chunks = self._chunk_text(content, chunk_size=500)
        points = []
        for i, chunk in enumerate(chunks):
            embedding = self._embed(chunk)
            points.append(PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={"policy_id": policy_id, "title": title, "chunk": chunk, "chunk_index": i},
            ))
        self.qdrant.upsert(COLLECTION_NAME, points=points)

    def search(self, query: str, limit: int = 5) -> list[dict]:
        embedding = self._embed(query)
        results = self.qdrant.search(
            COLLECTION_NAME,
            query_vector=embedding,
            limit=limit,
            with_payload=True,
        )
        return [
            {"policy_id": r.payload["policy_id"], "title": r.payload["title"],
             "chunk": r.payload["chunk"], "score": r.score}
            for r in results
        ]

    def _chunk_text(self, text: str, chunk_size: int = 500) -> list[str]:
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size):
            chunks.append(" ".join(words[i:i + chunk_size]))
        return chunks
```

## 10.3 requirements.txt เพิ่ม

```
qdrant-client>=1.9.0,<2.0.0
openai>=1.30.0,<2.0.0
```

---

# 11. Production Deployment — Shopify App

## 11.1 ภาพรวม Shopify Integration

ShopEasy ทำงานเป็น **Shopify App** ที่ embed ใน Shopify Admin ผ่าน App Bridge และรับ webhook จาก Shopify events

```
Shopify Store
    │
    ├── Webhook → POST /webhooks/shopify/{event}
    │               (orders/create, fulfillments/update, refunds/create)
    │
    └── App Bridge (iframe embed)
        └── Admin Portal ใน Shopify Admin
```

## 11.2 Webhook Handler

```python
# backend/app/api/routes/webhooks.py

import hashlib
import hmac
import json
from fastapi import APIRouter, Header, HTTPException, Request
from app.core.config import get_settings

router = APIRouter()


def verify_shopify_webhook(body: bytes, hmac_header: str) -> bool:
    settings = get_settings()
    secret = settings.shopify_webhook_secret.encode("utf-8")
    digest = hmac.new(secret, body, hashlib.sha256).digest()
    import base64
    computed = base64.b64encode(digest).decode("utf-8")
    return hmac.compare_digest(computed, hmac_header)


@router.post("/shopify/orders/create")
async def shopify_order_create(
    request: Request,
    x_shopify_hmac_sha256: str = Header(...),
):
    body = await request.body()
    if not verify_shopify_webhook(body, x_shopify_hmac_sha256):
        raise HTTPException(status_code=401, detail="Invalid HMAC")
    payload = json.loads(body)
    # Map Shopify order → ShopEasy Order และบันทึก DB
    return {"status": "received"}


@router.post("/shopify/fulfillments/update")
async def shopify_fulfillment_update(
    request: Request,
    x_shopify_hmac_sha256: str = Header(...),
):
    body = await request.body()
    if not verify_shopify_webhook(body, x_shopify_hmac_sha256):
        raise HTTPException(status_code=401, detail="Invalid HMAC")
    payload = json.loads(body)
    # อัปเดต Shipment status จาก Shopify fulfillment
    return {"status": "received"}


@router.post("/shopify/refunds/create")
async def shopify_refund_create(
    request: Request,
    x_shopify_hmac_sha256: str = Header(...),
):
    body = await request.body()
    if not verify_shopify_webhook(body, x_shopify_hmac_sha256):
        raise HTTPException(status_code=401, detail="Invalid HMAC")
    # ทริกเกอร์ Workflow 02 อัตโนมัติ
    return {"status": "received"}
```

## 11.3 Environment Config (Production)

```bash
# backend/.env.production

# Database
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@DB_HOST:5432/shopeasy

# Security
SECRET_KEY=<random 64 char hex>
ALLOWED_ORIGINS=https://your-shopify-app.myshopify.com,https://admin.shopify.com

# AI
OPENAI_API_KEY=sk-...

# Shopify
SHOPIFY_API_KEY=...
SHOPIFY_API_SECRET=...
SHOPIFY_WEBHOOK_SECRET=...
SHOPIFY_STORE_URL=https://your-store.myshopify.com

# Storage
MINIO_ENDPOINT=your-minio.domain.com
MINIO_ACCESS_KEY=...
MINIO_SECRET_KEY=...
MINIO_USE_SSL=true
MINIO_BUCKET_NAME=evidence

# Cache
REDIS_HOST=your-redis.host
REDIS_PORT=6379

# Vector DB
QDRANT_HOST=your-qdrant.host
QDRANT_PORT=6333

# Google OAuth
GOOGLE_CLIENT_ID=...
```

```typescript
// frontend/.env.production
VITE_API_BASE_URL=https://api.your-shopeasy-app.com/api/v1
VITE_GOOGLE_CLIENT_ID=...
```

## 11.4 docker-compose.production.yml

```yaml
version: "3.9"

services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: shopeasy
    volumes:
      - pg_data:/var/lib/postgresql/data
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql+psycopg://${DB_USER}:${DB_PASSWORD}@db:5432/shopeasy
      SECRET_KEY: ${SECRET_KEY}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      SHOPIFY_WEBHOOK_SECRET: ${SHOPIFY_WEBHOOK_SECRET}
      GOOGLE_CLIENT_ID: ${GOOGLE_CLIENT_ID}
      MINIO_ENDPOINT: ${MINIO_ENDPOINT}
      MINIO_ACCESS_KEY: ${MINIO_ACCESS_KEY}
      MINIO_SECRET_KEY: ${MINIO_SECRET_KEY}
      MINIO_USE_SSL: "true"
      REDIS_HOST: redis
      QDRANT_HOST: qdrant
    depends_on:
      db:
        condition: service_healthy
    restart: always
    ports:
      - "8000:8000"
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

  frontend:
    build:
      context: ./frontend
      args:
        VITE_API_BASE_URL: ${VITE_API_BASE_URL}
        VITE_GOOGLE_CLIENT_ID: ${VITE_GOOGLE_CLIENT_ID}
    ports:
      - "80:80"
    restart: always

  redis:
    image: redis:7-alpine
    restart: always
    volumes:
      - redis_data:/data

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ACCESS_KEY}
      MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY}
    volumes:
      - minio_data:/data
    restart: always

  qdrant:
    image: qdrant/qdrant:latest
    volumes:
      - qdrant_data:/qdrant/storage
    restart: always

volumes:
  pg_data:
  redis_data:
  minio_data:
  qdrant_data:
```

## 11.5 Nginx Config (Reverse Proxy)

```nginx
# nginx.conf
server {
    listen 80;
    server_name your-shopeasy-app.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name your-shopeasy-app.com;

    ssl_certificate /etc/letsencrypt/live/your-shopeasy-app.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-shopeasy-app.com/privkey.pem;

    # Frontend
    location / {
        proxy_pass http://frontend:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Backend API
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 120s;
    }

    # Webhooks (ต้อง whitelist Shopify IPs)
    location /webhooks/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
    }
}
```

---

# 12. Database Migrations V4

## 12.1 Migration List

```bash
# Migration 1: Customer Memory Tables
alembic revision --autogenerate -m "add_customer_memory_tables"

# Migration 2: Episodic Memory
alembic revision --autogenerate -m "add_episodic_memory_table"

# Migration 3: Shopify Integration Fields
alembic revision --autogenerate -m "add_shopify_fields_to_orders"

# Migration 4: Agent Execution Plans (for observability)
alembic revision --autogenerate -m "add_execution_plans_table"
```

## 12.2 Schema Additions

```sql
-- customer_long_term_memory
CREATE TABLE customer_long_term_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    memory_type VARCHAR(50) NOT NULL,
    key VARCHAR(100) NOT NULL,
    value JSONB,
    confidence FLOAT DEFAULT 1.0,
    source_agent VARCHAR(50),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- customer_episodic_memory
CREATE TABLE customer_episodic_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    summary TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- execution_plans (สำหรับ observability)
CREATE TABLE execution_plans (
    id VARCHAR(50) PRIMARY KEY,
    trace_id VARCHAR(100) REFERENCES agent_traces(id),
    intent VARCHAR(100),
    plan_json JSONB,
    risk_level VARCHAR(20),
    replan_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- orders เพิ่ม Shopify fields
ALTER TABLE orders
    ADD COLUMN IF NOT EXISTS shopify_order_id VARCHAR(50),
    ADD COLUMN IF NOT EXISTS shopify_store_url VARCHAR(200);

-- shipments เพิ่ม Shopify fields
ALTER TABLE shipments
    ADD COLUMN IF NOT EXISTS shopify_fulfillment_id VARCHAR(50);
```

## 12.3 New SQLAlchemy Models

```python
# backend/app/db/models/memory.py

from app.db.base import Base, TimestampMixin
import uuid
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


class CustomerLongTermMemory(Base):
    __tablename__ = "customer_long_term_memory"
    id = sa.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = sa.Column(UUID(as_uuid=True), sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    memory_type = sa.Column(sa.String(50))
    key = sa.Column(sa.String(100))
    value = sa.Column(JSONB)
    confidence = sa.Column(sa.Float, default=1.0)
    source_agent = sa.Column(sa.String(50))
    updated_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.text("now()"))


class CustomerEpisodicMemory(Base, TimestampMixin):
    __tablename__ = "customer_episodic_memory"
    id = sa.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = sa.Column(UUID(as_uuid=True), sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    event_type = sa.Column(sa.String(50), nullable=False)
    summary = sa.Column(sa.Text)
    metadata_ = sa.Column("metadata", JSONB)
```

---

# 13. Implementation Prompts

ส่วนนี้คือ prompt สำเร็จรูปสำหรับ implement แต่ละ feature โดย GitHub Copilot หรือ AI coding assistant

---

## PROMPT 1: Autonomous Tool Selection + Tool Chain

```
You are implementing the autonomous tool selection system for ShopEasy, a FastAPI + LangGraph AI operations platform.

## CODEBASE CONTEXT
- Backend: FastAPI, SQLAlchemy 2.x, LangGraph ≥0.1, Python 3.11
- Existing tools in: backend/app/agents/tools/ (tracking.py, refund.py, proactive.py)
- Existing nodes in: backend/app/agents/nodes/ (tracking_nodes.py, refund_nodes.py, proactive_nodes.py)
- LLM client: backend/app/agents/llm.py
- State: backend/app/agents/state.py (TrackingWorkflowState)

## TASK
Create the following files:

1. backend/app/agents/tool_registry.py
   - ToolDefinition dataclass (name, description, input_schema, output_schema, handler, tags, requires_db)
   - ToolRegistry class with register(), get(), list_for_llm() methods

2. backend/app/agents/tool_chain_executor.py
   - ToolChainExecutor class
   - execute(plan: list[dict], context: dict) method
   - _resolve_params() method: replace {{context.field}} and {{step_N.field}} placeholders
   - _apply_output_mapping() method: copy output fields to accumulated_context for next step

3. backend/app/agents/tool_selector.py
   - ToolSelector class with async think() method
   - Uses LLM to decide: which tool to call next, or FINISH, or ESCALATE
   - Returns JSON: {reasoning, action, params, response}

4. backend/app/agents/tools/definitions.py
   - Register all 10+ existing tools from tracking.py, refund.py, proactive.py into ToolRegistry
   - Create Pydantic input/output schemas for each tool

## KEY REQUIREMENTS
- Tool chaining: output of tool A must automatically become input of tool B via output_mapping
- No hardcoded workflow order — LLM decides the sequence
- {{context.field}} resolves from initial context dict
- {{step_N.field}} resolves from result of step N
- All handlers must remain sync (existing tools are sync functions)
- ToolChainExecutor must handle both sync and async handlers

## OUTPUT
Implement all 4 files. Do not modify existing tool files — only wrap them.
```

---

## PROMPT 2: ReAct Engine

```
You are implementing the ReAct (Reasoning + Acting) engine for ShopEasy.

## CODEBASE CONTEXT
- ToolRegistry and ToolChainExecutor already exist (see Prompt 1)
- LLM client: backend/app/agents/llm.py (has async chat() method)
- ErrorRecoverySystem will be created separately

## TASK
Create backend/app/agents/react_engine.py with:

### ReActObservation dataclass
Fields: iteration, thought, action, params, result, success, used_fallback

### ReActState dataclass  
Fields: intent, customer_id, context(dict), observations(list), final_response, react_done, escalate, replan_count, total_tool_calls

### ReActEngine class
- __init__(db=None, session_id="")
- async run(intent, customer_id, initial_context) → ReActState
- MAX_ITERATIONS = 8
- Loop: THOUGHT (call ToolSelector.think) → ACTION (execute tool) → OBSERVE (save result to state) → REFLECT (check if escalate needed)
- On each iteration: update state.context with tool results
- Stop conditions: action=="FINISH", action=="ESCALATE", max iterations reached
- After loop: save context to ShortTermMemory if session_id provided

## INTEGRATION
- After implementing ReActEngine, update backend/app/services/chat.py to use ReActEngine instead of direct workflow calls
- Keep existing workflow functions as fallback if LLM tool selector fails

## KEY REQUIREMENTS
- MAX_ITERATIONS = 8 hard limit
- Each iteration must log: thought, action, params, result, success
- state.context must accumulate results across iterations
- If ToolSelector returns invalid JSON, action = "ESCALATE"
```

---

## PROMPT 3: Planning Layer

```
You are implementing the Planning Layer for ShopEasy's agentic AI system.

## CODEBASE CONTEXT
- ReActEngine already exists
- ToolRegistry.list_for_llm() returns tool descriptions for LLM
- LLM client: backend/app/agents/llm.py

## TASK
Create backend/app/agents/planner.py with:

### PlanStep dataclass
Fields: step(int), tool(str), description(str), params(dict), output_mapping(dict), 
        depends_on(list[int]), fallback_tool(str|None), status(str), error(str|None)

### ExecutionPlan dataclass
Fields: plan_id(str), intent(str), steps(list[PlanStep]), reasoning(str),
        requires_human_approval(bool), risk_level(str), created_at, replan_count(int)
Methods: completed_steps() → list[int], next_step() → PlanStep|None

### Planner class
- async create_plan(intent, context, available_tools) → ExecutionPlan
  - Uses LLM with PLAN_PROMPT to generate structured plan
  - Parses JSON response into ExecutionPlan
- async replan(plan, failed_step, context, available_tools) → ExecutionPlan
  - Uses LLM with REPLAN_PROMPT
  - Keeps completed steps, replaces remaining steps

## PLAN_PROMPT must include:
- Intent
- Customer context (JSON)
- Available tools with input/output fields
- Expected JSON format with output_mapping for tool chaining

## REPLAN_PROMPT must include:
- Which step failed and why
- What was completed
- Current accumulated context
- Ask LLM to create new steps for remaining work only

## KEY REQUIREMENTS
- plan_id format: "PLAN-{8 hex chars uppercase}"
- If LLM returns invalid JSON, raise ValueError
- replan_count must be incremented on replan
- Plans with risk_level="high" or requires_human_approval=True must be flagged in trace
```

---

## PROMPT 4: 3-Layer Memory System

```
You are implementing the 3-layer memory system for ShopEasy.

## CODEBASE CONTEXT
- Redis is available at settings.redis_host:settings.redis_port
- PostgreSQL models are in backend/app/db/models/
- Settings: backend/app/core/config.py (get_settings())

## TASK

### 1. backend/app/agents/memory/short_term.py
- ShortTermMemory class
- __init__(session_id: str): creates redis connection key = "session:{session_id}"
- async save(field: str, value: Any): hset with TTL 86400
- async get(field: str) → Any|None: hget + json.loads
- async get_all() → dict
- async clear(): delete key
- Use redis.asyncio (aioredis)

### 2. Create Alembic migration
File: backend/alembic/versions/{hex}_add_customer_memory_tables.py
Tables to create:
  - customer_long_term_memory (id, customer_id FK, memory_type, key, value JSONB, confidence, source_agent, updated_at)
  - customer_episodic_memory (id, customer_id FK, event_type, summary, metadata JSONB, created_at)

### 3. backend/app/db/models/memory.py
SQLAlchemy models for both tables above

### 4. backend/app/agents/memory/long_term.py
- LongTermMemory(db, customer_id) class
- save(memory_type, key, value, source_agent): upsert by (customer_id, key)
- get(key) → dict|None
- get_all() → list[dict]
- build_summary() → str: human-readable summary of top 10 memories

### 5. backend/app/agents/memory/episodic.py
- EpisodicMemory(db, customer_id) class
- store(event_type, summary, metadata): insert row
- recall(event_types: list|None) → list[dict]: query recent episodes

## KEY REQUIREMENTS
- Short-term uses Redis HASH (hset/hget/hgetall/expire)
- Long-term does upsert: if (customer_id, key) exists → update value, else insert
- All Redis operations must be async (redis.asyncio)
- JSON serialization must handle datetime (use default=str)
- Add memory import to backend/app/db/models/__init__.py
```

---

## PROMPT 5: Error Recovery + Circuit Breaker

```
You are implementing the Error Recovery and Circuit Breaker patterns for ShopEasy.

## TASK

### 1. backend/app/agents/error_recovery.py

ToolResult dataclass: success(bool), data(Any), error(str), used_fallback(bool), escalate(bool)

FALLBACK_MAP dict: maps primary tool name → fallback tool name

ErrorRecoverySystem class with:
async execute_with_recovery(tool_name, params, handler, kwargs) → ToolResult
  Level 1: Retry 3 times with exponential backoff (2s, 4s, 8s) for any Exception
  Level 2: If retries exhausted, try FALLBACK_MAP[tool_name] if exists
  Level 3: If fallback fails or no fallback, return ToolResult(success=False, escalate=True)
  Must handle both sync and async handlers (use inspect.iscoroutinefunction)
  Must check CircuitBreaker.can_execute() before each attempt
  Must call CircuitBreaker.record_success/failure after each attempt

### 2. backend/app/agents/circuit_breaker.py

CircuitBreaker class (class-level state, not instance):
  States: CLOSED → OPEN → HALF_OPEN → CLOSED
  THRESHOLD = 5 failures before OPEN
  TIMEOUT = 60 seconds before HALF_OPEN
  can_execute(tool_name) → bool
  record_success(tool_name)
  record_failure(tool_name)
  Use defaultdict for _state, _fail_count, _open_time

## KEY REQUIREMENTS
- Exponential backoff: await asyncio.sleep(2 ** attempt) where attempt is 1,2,3
- Circuit breaker state is shared across all requests (class-level dict)
- HALF_OPEN state: allow 1 request through to test recovery
- If handler raises Exception (any), increment fail count and retry
- escalate=True means the calling agent should request human review
```

---

## PROMPT 6: Supervisor Agent (Full)

```
You are implementing the full SupervisorAgent for ShopEasy.

## CODEBASE CONTEXT
- LLM client: backend/app/agents/llm.py
- Existing basic supervisor logic in: backend/app/agents/nodes/refund_nodes.py (supervisor_node function)

## TASK
Create backend/app/agents/supervisor_agent.py

SupervisionResult dataclass:
  approved(bool), quality_score(float), requires_human(bool), issues(list[str]), reason(str)

SupervisorAgent class:
  QUALITY_THRESHOLD = 0.6
  HIGH_RISK_SCORE = 70

  async supervise(intent, customer_message, response, risk_score, replan_count, tools_used) → SupervisionResult:
    1. Rule-based check FIRST (no LLM needed):
       - risk_score >= HIGH_RISK_SCORE → requires_human=True
       - replan_count >= 2 → requires_human=True
       - response is empty → approved=False
    2. If no rule triggered: LLM quality check
       - Send QUALITY_PROMPT with intent, customer_message, response, tools_used
       - Parse JSON: {quality_score, issues, requires_human, reason}
    3. Return SupervisionResult

QUALITY_PROMPT template (Thai language, asking LLM to evaluate response quality):
- Was the response relevant to the intent?
- Did it use appropriate tools?
- Is the information complete?
- Should a human review this?

## INTEGRATION
After creating SupervisorAgent, update backend/app/services/chat.py:
- After getting response from ReActEngine or existing workflow, call supervisor.supervise()
- If not approved and requires_human: add to approval queue
- Log supervision result in AgentTrace.state_snapshot

## KEY REQUIREMENTS
- Rule-based checks must run BEFORE LLM to save tokens
- LLM quality prompt must be in Thai (for Thai customer context)
- approved = quality_score >= 0.6 AND requires_human == False
- Do NOT call LLM if rule-based check already determines requires_human=True
```

---

## PROMPT 7: Shopify Webhook Integration

```
You are implementing the Shopify webhook integration for ShopEasy.

## CODEBASE CONTEXT
- FastAPI backend, existing routes in backend/app/api/routes/
- Existing models: Order, Shipment in backend/app/db/models/
- Router registration: backend/app/api/router.py
- Settings: backend/app/core/config.py

## TASK

### 1. Add to backend/app/core/config.py Settings class:
  shopify_api_key: str = ""
  shopify_api_secret: str = ""
  shopify_webhook_secret: str = ""
  shopify_store_url: str = ""

### 2. Create backend/app/api/routes/webhooks.py
  
  verify_shopify_webhook(body: bytes, hmac_header: str) → bool:
    - Compute HMAC-SHA256 of body using shopify_webhook_secret
    - Base64 encode and compare with hmac_header using hmac.compare_digest
  
  POST /shopify/orders/create → shopify_order_create():
    - Verify HMAC first, 401 if invalid
    - Extract order data from Shopify payload
    - Create Order + OrderItems in DB if not exists (check shopify_order_id)
    - Return {"status": "received"}
  
  POST /shopify/fulfillments/update → shopify_fulfillment_update():
    - Verify HMAC
    - Find Shipment by shopify_fulfillment_id
    - Update shipment_status based on Shopify fulfillment_status
    - Create ShipmentEvent for status change
    - If status suggests delay: trigger proactive delay workflow
    - Return {"status": "received"}
  
  POST /shopify/refunds/create → shopify_refund_create():
    - Verify HMAC
    - Find Order by shopify_order_id
    - Trigger Workflow 02 (refund) automatically via handle_refund_chat()
    - Return {"status": "received"}

### 3. Register in backend/app/api/router.py:
  from app.api.routes.webhooks import router as webhooks_router
  api_router.include_router(webhooks_router, prefix="/webhooks", tags=["webhooks"])

### 4. Add DB columns (create Alembic migration):
  orders.shopify_order_id VARCHAR(50)
  shipments.shopify_fulfillment_id VARCHAR(50)

## SECURITY REQUIREMENTS
- ALWAYS verify HMAC before processing any webhook
- Use hmac.compare_digest (timing-safe comparison)
- Log all webhook receipts to audit_logs table
- Idempotency: check if order/fulfillment already processed before inserting
```

---

## PROMPT 8: Production Docker + Deployment Checklist

```
You are finalizing ShopEasy for production deployment.

## CODEBASE CONTEXT
- docker-compose.yml exists (local dev)
- backend/Dockerfile exists
- frontend/Dockerfile exists
- All services: postgres, backend, frontend, redis, minio

## TASK

### 1. Create docker-compose.production.yml
- Add qdrant service (qdrant/qdrant:latest, port 6333, volume)
- Backend: workers=4, no --reload
- Frontend: multi-stage build (node build → nginx serve)
- All secrets via environment variables (no hardcoded values)
- Health checks for all services
- restart: always for all services
- Volumes: pg_data, redis_data, minio_data, qdrant_data

### 2. Update frontend/Dockerfile for production
- Stage 1 (build): node:20-alpine, npm ci, npm run build with build args
- Stage 2 (serve): nginx:alpine, copy dist to /usr/share/nginx/html
- Add nginx.conf that handles SPA routing (try_files $uri /index.html)

### 3. Create nginx.conf
- HTTP → HTTPS redirect
- HTTPS with SSL (certbot/letsencrypt paths)
- Proxy /api/ → backend:8000
- Proxy /webhooks/ → backend:8000  
- Frontend static → frontend:80
- Timeout 120s for API routes

### 4. Create backend/app/core/health.py (enhanced health check)
- Check DB connectivity (query SELECT 1)
- Check Redis ping
- Check MinIO bucket exists
- Check Qdrant collection exists
- Return {"status": "healthy/degraded/unhealthy", "services": {...}}
- Update GET /health to use this

### 5. Create .env.example with ALL required variables documented

## PRODUCTION REQUIREMENTS
- No mock auth in production (return 403 if SECRET_KEY = default dev key)
- CORS must use ALLOWED_ORIGINS env var (not wildcard)
- All DB queries must use connection pooling (SQLAlchemy pool_size=10)
- Backend must support graceful shutdown (SIGTERM handler)
- Logs in JSON format for log aggregation
```

---

## สรุป Implementation Order

```
Sprint 1 (สัปดาห์ 1–2): Core Autonomous AI
  [x] PROMPT 1: Tool Registry + Tool Chain Executor
  [x] PROMPT 2: ReAct Engine
  [x] PROMPT 5: Error Recovery + Circuit Breaker

Sprint 2 (สัปดาห์ 3–4): Intelligence Layer
  [x] PROMPT 3: Planning Layer
  [x] PROMPT 4: 3-Layer Memory System
  [x] PROMPT 6: Supervisor Agent (Full)

Sprint 3 (สัปดาห์ 5): Shopify Integration
  [x] PROMPT 7: Shopify Webhook Integration
  [x] Policy RAG (Qdrant) — ใช้ schema จาก Section 10

Sprint 4 (สัปดาห์ 6): Production Hardening
  [x] PROMPT 8: Production Docker + Deployment
  [x] Run all DB migrations
  [x] Load test + monitoring setup
  [x] SSL certificate (Let's Encrypt)
  [x] Backup strategy (pg_dump schedule)
```

---

## Checklist ก่อน Deploy บน Shopify

```
Authentication & Security
  [ ] เปลี่ยน SECRET_KEY จาก default dev key
  [ ] GOOGLE_CLIENT_ID ตั้งค่าถูกต้อง
  [ ] ALLOWED_ORIGINS ตั้งเฉพาะ domain ที่อนุญาต
  [ ] SHOPIFY_WEBHOOK_SECRET ตั้งใน Shopify Partner Dashboard
  [ ] ทุก endpoint ที่ sensitive ต้องมี auth header check

Database
  [ ] Run alembic upgrade head บน production DB
  [ ] Seed data (ถ้าต้องการ demo)
  [ ] Backup ตั้ง schedule (daily pg_dump)
  [ ] Connection pool ตั้ง pool_size=10

AI / LLM
  [ ] OPENAI_API_KEY ตั้งค่า
  [ ] ทดสอบ ToolSelector กับ intent ทั้งหมด
  [ ] ทดสอบ ReAct loop ไม่ loop เกิน 8 ครั้ง
  [ ] Qdrant ingestion pipeline รัน policy_rag.ingest_all()

Storage
  [ ] MinIO bucket "evidence" สร้างแล้ว
  [ ] MinIO access ผ่าน SSL
  [ ] Qdrant collection "policies" สร้างแล้ว

Shopify
  [ ] App ลงทะเบียนใน Shopify Partner Dashboard
  [ ] Webhook endpoints ลงทะเบียนทั้ง 3 events
  [ ] App Bridge embed URL ตั้งค่าถูกต้อง
  [ ] ทดสอบ HMAC verification ด้วย test webhook

Monitoring
  [ ] /health endpoint return 200
  [ ] Logs ออก JSON format
  [ ] Error alerting ตั้งค่า (Sentry / Grafana)
  [ ] Uptime monitoring ตั้งค่า
```

---

> **ShopEasy V4** — ระบบ AI Operations Platform ที่ AI เลือก tool และสร้าง pipeline เองอัตโนมัติ  
> ไม่ต้อง hardcode workflow · Output ไหลเป็น Input อัตโนมัติ · พร้อม deploy บน Shopify
