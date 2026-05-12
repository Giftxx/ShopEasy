"""
Tool definitions — registers all tools into ToolRegistry with Pydantic schemas.

This module wraps existing tool functions from tracking.py, refund.py, proactive.py
and makes them available for autonomous AI selection.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.agents.tool_registry import ToolDefinition, ToolRegistry


# ══════════════════════════════════════════════════════════════════════════════
# Pydantic Input/Output Schemas
# ══════════════════════════════════════════════════════════════════════════════

# --- Tracking ---

class GetOrderInput(BaseModel):
    customer_id: str = Field(..., description="Customer UUID")
    order_id: str | None = Field(None, description="Specific order ID if known")


class GetOrderOutput(BaseModel):
    order_id: str = ""
    order_status: str = ""
    order_total: float = 0.0
    item_count: int = 0
    items: list[dict] = Field(default_factory=list)


class GetShipmentInput(BaseModel):
    customer_id: str = Field(..., description="Customer UUID")
    shipment_id: str | None = Field(None, description="Specific shipment ID")


class GetShipmentOutput(BaseModel):
    shipments: list[dict] = Field(default_factory=list)
    shipment_count: int = 0


class TrackingResponseInput(BaseModel):
    customer_name: str = ""
    shipments: list[dict] = Field(default_factory=list)
    message: str = ""


class TrackingResponseOutput(BaseModel):
    response_text: str = ""


# --- Refund ---

class RefundRiskInput(BaseModel):
    order_total: float = 0.0
    evidence_result: dict = Field(default_factory=dict)


class RefundRiskOutput(BaseModel):
    risk_score: int = 0


class CreateRefundInput(BaseModel):
    customer_id: str
    order_id: str
    reason: str = ""


class CreateRefundOutput(BaseModel):
    refund_request_id: str = ""
    case_id: str = ""
    status: str = "pending"


class EvidenceInput(BaseModel):
    customer_id: str
    case_id: str = ""


class EvidenceOutput(BaseModel):
    attachment_count: int = 0
    evidence_groups: list[str] = Field(default_factory=list)
    sufficient: bool = False


class ApprovalRequestInput(BaseModel):
    case_id: str
    risk_score: int = 0
    reason: str = ""


class ApprovalRequestOutput(BaseModel):
    approval_id: str = ""
    status: str = "pending"


# --- Policy ---

class PolicySearchInput(BaseModel):
    query: str
    limit: int = 5


class PolicySearchOutput(BaseModel):
    policies: list[dict] = Field(default_factory=list)
    count: int = 0


# --- Proactive ---

class DelayRiskInput(BaseModel):
    shipment_id: str


class DelayRiskOutput(BaseModel):
    risk_score: int = 0
    is_stale: bool = False


class ProactiveAlertInput(BaseModel):
    shipment_id: str
    order_id: str
    risk_score: int = 0


class ProactiveAlertOutput(BaseModel):
    alert_id: str = ""
    message: str = ""


# --- Memory ---

class RecallMemoryInput(BaseModel):
    customer_id: str


class RecallMemoryOutput(BaseModel):
    memory_summary: str = ""
    memories: list[dict] = Field(default_factory=list)


# --- Fallback tools ---

class DefaultRiskOutput(BaseModel):
    risk_score: int = 50


class DefaultEvidenceOutput(BaseModel):
    attachment_count: int = 0
    evidence_groups: list[str] = Field(default_factory=list)
    sufficient: bool = False


class FallbackPolicyOutput(BaseModel):
    policies: list[dict] = Field(default_factory=list)
    count: int = 0


# ══════════════════════════════════════════════════════════════════════════════
# Handler Wrappers
# ══════════════════════════════════════════════════════════════════════════════

def handle_get_order_detail(customer_id: str, order_id: str | None = None, db=None) -> dict:
    """Load order details from DB."""
    from app.repositories.tracking import get_tracking_context

    context = get_tracking_context(db, customer_id, conversation_id="")
    if context is None:
        return {"order_id": "", "order_status": "not_found", "order_total": 0.0, "item_count": 0, "items": []}

    orders = context.get("active_orders", [])
    if order_id:
        order = next((o for o in orders if getattr(o, "id", None) == order_id), None)
        if order:
            return {
                "order_id": order.id,
                "order_status": order.order_status or "",
                "order_total": float(order.total_amount or 0),
                "item_count": len(order.order_items) if hasattr(order, "order_items") else 0,
                "items": [{"product_name": i.product_name, "quantity": i.quantity} for i in (order.order_items or [])],
            }
    elif orders:
        order = orders[0]
        return {
            "order_id": order.id,
            "order_status": order.order_status or "",
            "order_total": float(order.total_amount or 0),
            "item_count": len(order.order_items) if hasattr(order, "order_items") else 0,
            "items": [{"product_name": i.product_name, "quantity": i.quantity} for i in (order.order_items or [])],
        }
    return {"order_id": "", "order_status": "not_found", "order_total": 0.0, "item_count": 0, "items": []}


def handle_get_shipment_status(customer_id: str, shipment_id: str | None = None, db=None) -> dict:
    """Load shipment status from DB."""
    from app.repositories.tracking import get_tracking_context

    context = get_tracking_context(db, customer_id, conversation_id="")
    if context is None:
        return {"shipments": [], "shipment_count": 0}

    shipments = context.get("active_shipments", [])
    results = []
    for s in shipments:
        if shipment_id and getattr(s, "id", None) != shipment_id:
            continue
        results.append({
            "shipment_id": s.id,
            "status": s.shipment_status or "",
            "order_id": s.order_id or "",
            "delay_risk_score": getattr(s, "delay_risk_score", None),
        })

    return {"shipments": results, "shipment_count": len(results)}


def handle_build_tracking_response(customer_name: str = "", shipments: list[dict] | None = None, message: str = "", **kwargs) -> dict:
    """Build a tracking response message."""
    from app.agents.tools.tracking import build_shipment_summaries, build_status_note

    if not shipments:
        return {"response_text": f"สวัสดีค่ะ คุณ{customer_name} ตอนนี้ยังไม่มีข้อมูลพัสดุค่ะ"}

    lines = [f"สวัสดีค่ะ คุณ{customer_name} สรุปสถานะพัสดุ:"]
    for i, s in enumerate(shipments, 1):
        status = s.get("status", "unknown")
        note = build_status_note(status)
        lines.append(f"{i}. พัสดุ {s.get('shipment_id', '?')}: {note}")
    lines.append("มีอะไรให้ช่วยเพิ่มเติมไหมคะ?")
    return {"response_text": "\n".join(lines)}


def handle_calculate_refund_risk(order_total: float = 0.0, evidence_result: dict | None = None, **kwargs) -> dict:
    """Calculate refund risk score."""
    from app.agents.tools.refund import calculate_refund_risk

    score = calculate_refund_risk(order_total, evidence_result or {})
    return {"risk_score": score}


def handle_create_refund_request(customer_id: str, order_id: str, reason: str = "", db=None, **kwargs) -> dict:
    """Create a refund request with associated case."""
    from uuid import uuid4

    from app.db.models import Case, RefundRequest

    case_id = f"CS-{uuid4().hex[:8].upper()}"
    refund_id = f"RF-{uuid4().hex[:8].upper()}"

    case = Case(
        id=case_id,
        order_id=order_id,
        case_type="refund_request",
        status="open",
        priority="normal",
    )
    db.add(case)
    db.flush()

    refund = RefundRequest(
        id=refund_id,
        case_id=case_id,
        reason=reason or "customer_request",
        status="pending",
    )
    db.add(refund)
    db.flush()

    return {"refund_request_id": refund_id, "case_id": case_id, "status": "pending"}


def handle_evaluate_evidence(customer_id: str, case_id: str = "", db=None, **kwargs) -> dict:
    """Evaluate evidence attachments for a case."""
    from app.db.models import Attachment

    attachments = []
    if case_id and db:
        attachments = db.query(Attachment).filter(Attachment.case_id == case_id).all()

    from app.agents.tools.refund import evaluate_evidence

    result = evaluate_evidence(attachments)
    return dict(result)


def handle_request_human_approval(case_id: str, risk_score: int = 0, reason: str = "", db=None, **kwargs) -> dict:
    """Create an approval request for human review."""
    from uuid import uuid4

    from app.db.models import Approval

    approval_id = f"APR-{uuid4().hex[:8].upper()}"
    approval = Approval(
        id=approval_id,
        case_id=case_id,
        approval_type="refund",
        status="pending",
    )
    db.add(approval)
    db.flush()
    return {"approval_id": approval_id, "status": "pending"}


def handle_search_policy(query: str, limit: int = 5, db=None, **kwargs) -> dict:
    """Search policies — uses keyword matching (Qdrant upgrade later)."""
    from app.db.models import Policy

    if db is None:
        return {"policies": [], "count": 0}

    policies = db.query(Policy).limit(limit).all()
    results = [{"policy_id": p.id, "title": p.title, "category": getattr(p, "category", "")} for p in policies]
    return {"policies": results, "count": len(results)}


def handle_calculate_delay_risk(shipment_id: str, db=None, **kwargs) -> dict:
    """Calculate delay risk for a shipment."""
    from app.agents.tools.proactive import calculate_delay_risk, is_stale_update
    from app.db.models import Shipment

    if db is None:
        return {"risk_score": 50, "is_stale": True}

    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if shipment is None:
        return {"risk_score": 50, "is_stale": True}

    risk = calculate_delay_risk(shipment)
    stale = is_stale_update(getattr(shipment, "last_update_at", None))
    return {"risk_score": risk, "is_stale": stale}


def handle_create_proactive_alert(shipment_id: str, order_id: str, risk_score: int = 0, db=None, **kwargs) -> dict:
    """Create a proactive alert."""
    from uuid import uuid4

    from app.agents.tools.proactive import build_proactive_message
    from app.db.models import ProactiveAlert

    alert_id = f"ALT-{uuid4().hex[:8].upper()}"
    msg = build_proactive_message(order_id, shipment_id, risk_score)

    alert = ProactiveAlert(
        id=alert_id,
        order_id=order_id,
        shipment_id=shipment_id,
        alert_type="shipment_no_update_48h",
        delay_risk_score=risk_score,
        message=msg,
        status="open",
    )
    db.add(alert)
    db.flush()
    return {"alert_id": alert_id, "message": msg}


def handle_recall_customer_memory(customer_id: str, db=None, **kwargs) -> dict:
    """Recall long-term memory for a customer."""
    try:
        from app.agents.memory.long_term import LongTermMemory

        mem = LongTermMemory(db, customer_id)
        summary = mem.build_summary()
        memories = mem.get_all()
        return {"memory_summary": summary, "memories": memories}
    except Exception:
        return {"memory_summary": "ไม่มี memory ของลูกค้าคนนี้", "memories": []}


# --- Fallback Handlers ---

def handle_default_risk_medium(**kwargs) -> dict:
    return {"risk_score": 50}


def handle_default_evidence_insufficient(**kwargs) -> dict:
    return {"attachment_count": 0, "evidence_groups": [], "sufficient": False}


def handle_get_all_policies_fallback(db=None, **kwargs) -> dict:
    """Fallback: return all policies without search."""
    from app.db.models import Policy

    if db is None:
        return {"policies": [], "count": 0}
    policies = db.query(Policy).limit(10).all()
    results = [{"policy_id": p.id, "title": p.title} for p in policies]
    return {"policies": results, "count": len(results)}


def handle_get_order_from_db_direct(customer_id: str, **kwargs) -> dict:
    """Fallback: direct DB query for order."""
    return handle_get_order_detail(customer_id=customer_id, db=kwargs.get("db"))


def handle_get_shipment_from_db_direct(customer_id: str, **kwargs) -> dict:
    """Fallback: direct DB query for shipment."""
    return handle_get_shipment_status(customer_id=customer_id, db=kwargs.get("db"))


# ══════════════════════════════════════════════════════════════════════════════
# Registration
# ══════════════════════════════════════════════════════════════════════════════

def register_all_tools():
    """Register all tools into the ToolRegistry. Call once at startup."""

    # --- Tracking ---
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

    # --- Refund ---
    ToolRegistry.register(ToolDefinition(
        name="calculate_refund_risk",
        description="คำนวณ risk score สำหรับการคืนเงิน (0-100) โดยดูจาก order_total และ evidence",
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
        description="ประเมิน evidence ที่ลูกค้าแนบมา (รูป/วิดีโอ) ว่าเพียงพอหรือไม่",
        input_schema=EvidenceInput,
        output_schema=EvidenceOutput,
        handler=handle_evaluate_evidence,
        tags=["refund"],
        requires_db=True,
    ))

    ToolRegistry.register(ToolDefinition(
        name="request_human_approval",
        description="ส่งคำขออนุมัติให้ admin เมื่อ risk score สูง (≥70)",
        input_schema=ApprovalRequestInput,
        output_schema=ApprovalRequestOutput,
        handler=handle_request_human_approval,
        tags=["refund", "proactive"],
        requires_db=True,
    ))

    # --- Policy ---
    ToolRegistry.register(ToolDefinition(
        name="search_policy",
        description="ค้นหา policy ที่เกี่ยวข้องกับสถานการณ์",
        input_schema=PolicySearchInput,
        output_schema=PolicySearchOutput,
        handler=handle_search_policy,
        tags=["refund", "tracking", "proactive"],
        requires_db=True,
    ))

    # --- Proactive ---
    ToolRegistry.register(ToolDefinition(
        name="calculate_delay_risk",
        description="คำนวณความเสี่ยงของการล่าช้า shipment (0-100)",
        input_schema=DelayRiskInput,
        output_schema=DelayRiskOutput,
        handler=handle_calculate_delay_risk,
        tags=["proactive"],
        requires_db=True,
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

    # --- Memory ---
    ToolRegistry.register(ToolDefinition(
        name="recall_customer_memory",
        description="ดึง long-term memory ของลูกค้า (พฤติกรรม, ประวัติ, preferences)",
        input_schema=RecallMemoryInput,
        output_schema=RecallMemoryOutput,
        handler=handle_recall_customer_memory,
        tags=["tracking", "refund", "proactive"],
        requires_db=True,
    ))

    # --- Fallback Tools ---
    ToolRegistry.register(ToolDefinition(
        name="use_default_risk_medium",
        description="Fallback: ใช้ risk score = 50 (medium) เมื่อคำนวณจริงไม่ได้",
        input_schema=RefundRiskInput,
        output_schema=DefaultRiskOutput,
        handler=handle_default_risk_medium,
        tags=["fallback"],
    ))

    ToolRegistry.register(ToolDefinition(
        name="use_default_evidence_insufficient",
        description="Fallback: ถือว่า evidence ไม่เพียงพอ",
        input_schema=EvidenceInput,
        output_schema=DefaultEvidenceOutput,
        handler=handle_default_evidence_insufficient,
        tags=["fallback"],
    ))

    ToolRegistry.register(ToolDefinition(
        name="get_all_policies_fallback",
        description="Fallback: ดึง policy ทั้งหมดโดยไม่ search",
        input_schema=PolicySearchInput,
        output_schema=FallbackPolicyOutput,
        handler=handle_get_all_policies_fallback,
        tags=["fallback"],
        requires_db=True,
    ))

    ToolRegistry.register(ToolDefinition(
        name="get_order_from_db_direct",
        description="Fallback: ดึง order โดยตรงจาก DB",
        input_schema=GetOrderInput,
        output_schema=GetOrderOutput,
        handler=handle_get_order_from_db_direct,
        tags=["fallback"],
        requires_db=True,
    ))

    ToolRegistry.register(ToolDefinition(
        name="get_shipment_from_db_direct",
        description="Fallback: ดึง shipment โดยตรงจาก DB",
        input_schema=GetShipmentInput,
        output_schema=GetShipmentOutput,
        handler=handle_get_shipment_from_db_direct,
        tags=["fallback"],
        requires_db=True,
    ))
