from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.agents.state import TrackingWorkflowState
from app.agents.tools.proactive import (
    build_proactive_message,
    calculate_delay_risk,
    detect_proactive_event,
    is_stale_update,
    select_proactive_policy_titles,
)
from app.db.models import Approval, Case, ProactiveAlert
from app.repositories.proactive import ProactiveContext, get_proactive_context


def event_ingestion_node(state: TrackingWorkflowState, event_type: str) -> TrackingWorkflowState:
    state.detected_intent = detect_proactive_event(event_type)
    state.selected_workflow = "workflow_03_proactive_delay_alert"
    state.tool_logs.append({"node": "event_ingestion_node", "tool": "detect_proactive_event", "event_type": event_type})
    return state


def proactive_context_resolution_node(db: Session, state: TrackingWorkflowState, shipment_id: str) -> tuple[TrackingWorkflowState, ProactiveContext]:
    context = get_proactive_context(db, shipment_id)
    if context is None:
        raise HTTPException(status_code=404, detail="Shipment not found.")
    if context.shipment.order is None:
        raise HTTPException(status_code=404, detail="Shipment order not found.")

    state.customer_id = context.shipment.order.customer_id
    state.active_order_ids = [context.shipment.order_id]
    state.active_shipment_ids = [context.shipment.id]
    state.customer_name = context.shipment.order.customer.name if getattr(context.shipment.order, "customer", None) else None
    state.tool_logs.append({"node": "context_resolution_node", "tool": "get_proactive_context", "shipment_id": shipment_id})
    return state, context


def proactive_shipping_node(state: TrackingWorkflowState, context: ProactiveContext) -> tuple[TrackingWorkflowState, bool, int]:
    stale = is_stale_update(context.shipment.last_update)
    risk_score = calculate_delay_risk(context.shipment)
    state.tool_logs.append(
        {
            "node": "shipping_node",
            "tool": "evaluate_shipment_delay",
            "shipment_id": context.shipment.id,
            "stale_update": stale,
            "risk_score": risk_score,
        }
    )
    return state, stale, risk_score


def proactive_policy_rag_node(state: TrackingWorkflowState, context: ProactiveContext) -> TrackingWorkflowState:
    state.tool_logs.append(
        {
            "node": "policy_rag_node",
            "tool": "select_proactive_policy_titles",
            "policies": select_proactive_policy_titles(context.policies),
        }
    )
    return state


def proactive_alert_node(db: Session, state: TrackingWorkflowState, context: ProactiveContext, risk_score: int) -> tuple[TrackingWorkflowState, ProactiveAlert]:
    alert = db.get(ProactiveAlert, "ALT-1001")
    if alert is None:
        alert = ProactiveAlert(
            id="ALT-1001",
            order_id=context.shipment.order_id,
            shipment_id=context.shipment.id,
            alert_type="shipment_delay",
            risk_score=risk_score,
            status="open",
            recommended_action="Notify customer and monitor shipment",
            message_draft=build_proactive_message(context.shipment.order_id, context.shipment.id, risk_score),
            case_id=None,
            created_at=datetime.utcnow(),
            resolved_at=None,
        )
        db.add(alert)
        db.flush()
    state.response_text = alert.message_draft
    state.tool_logs.append({"node": "proactive_alert_node", "tool": "create_or_load_proactive_alert", "alert_id": alert.id})
    return state, alert


def proactive_supervisor_node(state: TrackingWorkflowState, risk_score: int) -> TrackingWorkflowState:
    requires_approval = risk_score >= 80
    if requires_approval:
        state.fallback_reason = "requires_human_approval"
    state.tool_logs.append({"node": "supervisor_node", "tool": "evaluate_proactive_escalation", "requires_approval": requires_approval})
    return state


def proactive_case_node(db: Session, state: TrackingWorkflowState, context: ProactiveContext, alert: ProactiveAlert) -> tuple[TrackingWorkflowState, Case]:
    case = db.get(Case, "CS-7001")
    if case is None:
        case = Case(
            id="CS-7001",
            customer_id=context.shipment.order.customer_id,
            order_id=context.shipment.order_id,
            case_type="shipping_delay",
            priority="high",
            status="open",
            ai_summary="Proactive delay alert opened for shipment with stale tracking update.",
            assigned_role="admin",
            created_by="ai",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(case)
        db.flush()
    alert.case_id = case.id
    db.flush()
    state.tool_logs.append({"node": "case_node", "tool": "create_or_load_proactive_case", "case_id": case.id})
    return state, case


def proactive_approval_node(db: Session, state: TrackingWorkflowState, case: Case, risk_score: int) -> TrackingWorkflowState:
    if risk_score < 80:
        state.tool_logs.append({"node": "approval_node", "tool": "skip_approval"})
        return state

    approval = db.get(Approval, "APR-7001")
    if approval is None:
        approval = Approval(
            id="APR-7001",
            case_id=case.id,
            approval_type="compensation",
            requested_action="Review proactive compensation for delayed shipment",
            amount=100.00,
            currency="THB",
            risk_level="high",
            status="pending",
            ai_reason="Shipment delay exceeded threshold and risk score requires manual review.",
            policy_citation={"workflow": "workflow_03_proactive_delay_alert"},
            created_at=datetime.utcnow(),
        )
        db.add(approval)
        db.flush()
    state.tool_logs.append({"node": "approval_node", "tool": "create_or_load_proactive_approval", "approval_id": approval.id})
    return state


def proactive_memory_write_node(state: TrackingWorkflowState, case: Case, alert: ProactiveAlert) -> TrackingWorkflowState:
    state.memory_summary = f"Proactive alert {alert.id} created and linked to case {case.id}."
    state.tool_logs.append({"node": "memory_write_node", "tool": "write_proactive_memory"})
    return state


def proactive_logging_node(state: TrackingWorkflowState) -> TrackingWorkflowState:
    state.tool_logs.append({"node": "logging_node", "tool": "record_proactive_trace_placeholder"})
    return state
