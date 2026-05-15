from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.state import TrackingWorkflowState
from app.agents.tools.proactive import (
    build_carrier_notification,
    build_proactive_message,
    calculate_delay_risk,
    detect_proactive_event,
    is_stale_update,
    select_proactive_policy_titles,
)
from app.db.models import Approval, Case, ProactiveAlert, ShipmentEvent
from app.repositories.proactive import ProactiveContext, get_proactive_context


def _new_prefixed_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:8].upper()}"


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


def proactive_policy_rag_node(state: TrackingWorkflowState, context: ProactiveContext, db: Session) -> TrackingWorkflowState:
    from app.services.policy_rag import search_policy_hybrid

    # Search for delay / shipping policy chunks (hybrid: vector + keyword)
    query = "shipment delay compensation proactive notification"
    results = search_policy_hybrid(db, query=query, limit=3)

    state.policy_chunks = [r["chunk_text"] for r in results]
    state.policy_titles = [r["policy_title"] for r in results] or select_proactive_policy_titles(context.policies)

    state.tool_logs.append(
        {
            "node": "policy_rag_node",
            "tool": "search_policy_chunks",
            "query": query,
            "results_count": len(results),
        }
    )
    return state


def proactive_alert_node(db: Session, state: TrackingWorkflowState, context: ProactiveContext, risk_score: int) -> tuple[TrackingWorkflowState, ProactiveAlert]:
    fresh_message = build_proactive_message(context.shipment.order_id, context.shipment.id, risk_score)
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
            message_draft=fresh_message,
            case_id=None,
            created_at=datetime.utcnow(),
            resolved_at=None,
        )
        db.add(alert)
    else:
        alert.message_draft = fresh_message
        alert.risk_score = risk_score
    db.flush()
    state.response_text = alert.message_draft
    state.tool_logs.append({"node": "proactive_alert_node", "tool": "create_or_load_proactive_alert", "alert_id": alert.id})
    return state, alert


def proactive_supervisor_node(state: TrackingWorkflowState, risk_score: int) -> TrackingWorkflowState:
    """Full supervisor evaluation for proactive alerts."""
    from app.agents.inter_agent import MessageBus
    from app.agents.supervisor_agent import SupervisorAgent

    supervisor = SupervisorAgent()
    result = supervisor.supervise(
        intent="proactive_delay_alert",
        customer_message="system_event",
        response=state.response_text or "pending",
        risk_score=risk_score,
        tools_used=[log.get("tool", "") for log in state.tool_logs],
    )

    requires_approval = result.requires_human or risk_score >= 80

    if requires_approval:
        state.fallback_reason = "requires_human_approval"
        bus = MessageBus.get_instance()
        bus.escalate(
            source="proactive_workflow",
            context={"customer_id": state.customer_id, "shipment_ids": state.active_shipment_ids,
                      "quality_score": result.quality_score},
            reason=result.reason or f"High risk delay (score={risk_score})",
            risk_score=risk_score,
        )

    state.tool_logs.append({
        "node": "supervisor_node",
        "tool": "full_supervisor_evaluation",
        "requires_approval": requires_approval,
        "quality_score": result.quality_score,
        "issues": result.issues,
    })
    return state


def proactive_case_node(db: Session, state: TrackingWorkflowState, context: ProactiveContext, alert: ProactiveAlert) -> tuple[TrackingWorkflowState, Case]:
    existing_case = db.scalar(
        select(Case)
        .where(
            Case.order_id == context.shipment.order_id,
            Case.case_type == "shipping_delay",
            Case.status.notin_(["closed", "resolved"]),
        )
        .order_by(Case.created_at.desc())
    )
    if existing_case is not None:
        case = existing_case
        if alert.case_id is None:
            alert.case_id = case.id
            db.flush()
        state.tool_logs.append({"node": "case_node", "tool": "load_existing_proactive_case", "case_id": case.id})
        return state, case

    ai_summary = (
        f"Proactive delay alert for shipment {context.shipment.id} on order {context.shipment.order_id}. "
        f"Risk score: {alert.risk_score}/100. Stale tracking update detected."
    )
    case = Case(
        id=_new_prefixed_id("CS"),
        customer_id=context.shipment.order.customer_id,
        order_id=context.shipment.order_id,
        case_type="shipping_delay",
        priority="high",
        status="open",
        ai_summary=ai_summary,
        assigned_role="admin",
        created_by="ai",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(case)
    db.flush()
    alert.case_id = case.id
    db.flush()
    state.tool_logs.append({"node": "case_node", "tool": "create_proactive_case", "case_id": case.id})
    return state, case


def proactive_approval_node(db: Session, state: TrackingWorkflowState, case: Case, risk_score: int) -> TrackingWorkflowState:
    if risk_score < 80:
        state.tool_logs.append({"node": "approval_node", "tool": "skip_approval"})
        return state

    existing_approval = db.scalar(
        select(Approval)
        .where(
            Approval.case_id == case.id,
            Approval.approval_type == "compensation",
            Approval.status == "pending",
        )
        .order_by(Approval.created_at.desc())
    )
    if existing_approval is not None:
        state.tool_logs.append({"node": "approval_node", "tool": "load_existing_proactive_approval", "approval_id": existing_approval.id})
        return state

    approval = Approval(
        id=_new_prefixed_id("APR"),
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
    state.tool_logs.append({"node": "approval_node", "tool": "create_proactive_approval", "approval_id": approval.id})
    return state


def proactive_memory_write_node(db: Session, state: TrackingWorkflowState, case: Case, alert: ProactiveAlert) -> TrackingWorkflowState:
    """Persist memory after proactive alert across all 3 layers."""
    import logging

    from app.agents.memory.episodic import EpisodicMemory
    from app.agents.memory.long_term import LongTermMemory

    logger = logging.getLogger(__name__)
    customer_id = state.customer_id

    # Long-term: record delay pattern
    if customer_id and customer_id != "SYSTEM":
        try:
            ltm = LongTermMemory(db=db, customer_id=customer_id)
            ltm.save(
                memory_type="pattern",
                key="last_delay_alert",
                value={"alert_id": alert.id, "case_id": case.id, "risk_score": alert.risk_score},
                source_agent="proactive_workflow",
            )
        except Exception as e:
            logger.debug("Long-term write error: %s", e)

    # Episodic: record escalation event
    if customer_id and customer_id != "SYSTEM":
        try:
            em = EpisodicMemory(db=db, customer_id=customer_id)
            em.store(
                event_type="escalation",
                summary=f"Proactive delay alert {alert.id} for case {case.id}, risk={alert.risk_score}",
                metadata={"alert_id": alert.id, "case_id": case.id, "risk_score": alert.risk_score},
            )
        except Exception as e:
            logger.debug("Episodic write error: %s", e)

    state.memory_summary = f"Proactive alert {alert.id} created and linked to case {case.id}."
    state.tool_logs.append({"node": "memory_write_node", "tool": "persist_3layer_proactive_memory"})
    return state


def proactive_carrier_notify_node(
    db: Session, state: TrackingWorkflowState, context: ProactiveContext, alert: ProactiveAlert
) -> TrackingWorkflowState:
    """Simulate notifying the carrier about a stale shipment. Writes a ShipmentEvent record."""
    shipment = context.shipment

    # ── DEDUPE: at most one carrier_contacted event per shipment per UTC day ──
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    existing = db.execute(
        select(ShipmentEvent)
        .where(ShipmentEvent.shipment_id == shipment.id)
        .where(ShipmentEvent.event_type == "carrier_contacted")
        .where(ShipmentEvent.event_time >= today_start)
        .order_by(ShipmentEvent.event_time.desc())
        .limit(1)
    ).scalar_one_or_none()

    if existing is not None:
        state.tool_logs.append({
            "node": "carrier_notify_node",
            "tool": "notify_carrier",
            "shipment_id": shipment.id,
            "skipped": "already_notified_today",
            "existing_event_id": existing.id,
        })
        return state

    message = build_carrier_notification(
        shipment_id=shipment.id,
        tracking_no=shipment.tracking_no,
        carrier=shipment.carrier,
        order_id=shipment.order_id,
    )
    event = ShipmentEvent(
        id=_new_prefixed_id("EVT"),
        shipment_id=shipment.id,
        event_type="carrier_contacted",
        event_message=message,
        location="system",
        event_time=datetime.utcnow(),
        raw_payload={
            "source": "workflow_03_proactive_delay_alert",
            "alert_id": alert.id,
            "carrier": shipment.carrier,
            "tracking_no": shipment.tracking_no,
            "method": "simulated_api_call",
        },
        created_at=datetime.utcnow(),
    )
    db.add(event)
    db.flush()
    state.tool_logs.append({
        "node": "carrier_notify_node",
        "tool": "notify_carrier",
        "shipment_id": shipment.id,
        "carrier": shipment.carrier or "unknown",
        "tracking_no": shipment.tracking_no or "unknown",
        "event_id": event.id,
        "message_preview": message[:120],
    })
    return state


def _legacy_proactive_carrier_notify_node_DEPRECATED(
    db: Session, state: TrackingWorkflowState, context: ProactiveContext, alert: ProactiveAlert
) -> TrackingWorkflowState:
    """Simulate notifying the carrier about a stale shipment. Writes a ShipmentEvent record."""
    shipment = context.shipment
    message = build_carrier_notification(
        shipment_id=shipment.id,
        tracking_no=shipment.tracking_no,
        carrier=shipment.carrier,
        order_id=shipment.order_id,
    )
    event = ShipmentEvent(
        id=_new_prefixed_id("EVT"),
        shipment_id=shipment.id,
        event_type="carrier_contacted",
        event_message=message,
        location="system",
        event_time=datetime.utcnow(),
        raw_payload={
            "source": "workflow_03_proactive_delay_alert",
            "alert_id": alert.id,
            "carrier": shipment.carrier,
            "tracking_no": shipment.tracking_no,
            "method": "simulated_api_call",
        },
        created_at=datetime.utcnow(),
    )
    db.add(event)
    db.flush()
    state.tool_logs.append({
        "node": "carrier_notify_node",
        "tool": "notify_carrier",
        "shipment_id": shipment.id,
        "carrier": shipment.carrier or "unknown",
        "tracking_no": shipment.tracking_no or "unknown",
        "event_id": event.id,
        "message_preview": message[:120],
    })
    return state


def proactive_logging_node(state: TrackingWorkflowState) -> TrackingWorkflowState:
    state.tool_logs.append({"node": "logging_node", "tool": "finalize_proactive_workflow"})
    return state
