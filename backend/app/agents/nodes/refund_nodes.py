from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.agents.state import TrackingWorkflowState
from app.agents.tools.refund import (
    build_refund_response,
    calculate_refund_risk,
    detect_refund_intent,
    evaluate_evidence,
    select_relevant_policy_titles,
)
from app.db.models import Attachment, Case, RefundRequest
from app.repositories.refund import RefundContext, get_refund_context


def _new_prefixed_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:8].upper()}"


def refund_router_node(state: TrackingWorkflowState) -> TrackingWorkflowState:
    state.detected_intent = detect_refund_intent(state.raw_message)
    state.tool_logs.append({"node": "router_node", "tool": "detect_refund_intent"})
    return state


def refund_context_resolution_node(db: Session, state: TrackingWorkflowState) -> tuple[TrackingWorkflowState, RefundContext]:
    context = get_refund_context(db, state.customer_id, state.conversation_id, state.target_order_id)
    if context is None:
        raise HTTPException(status_code=404, detail="Customer, conversation, or order not found.")

    state.customer_name = context.customer.name
    state.active_order_ids = [context.order.id]
    state.tool_logs.append({"node": "context_resolution_node", "tool": "get_refund_context"})
    return state, context


def refund_memory_retrieval_node(state: TrackingWorkflowState, context: RefundContext) -> TrackingWorkflowState:
    state.memory_summary = f"Customer {context.customer.name} requested refund support for order {context.order.id}."
    state.tool_logs.append({"node": "memory_retrieval_node", "tool": "refund_memory_summary"})
    return state


def refund_planner_node(state: TrackingWorkflowState) -> TrackingWorkflowState:
    state.selected_workflow = "workflow_02_refund_return"
    state.tool_logs.append({"node": "planner_node", "tool": "select_refund_workflow"})
    return state


def refund_order_node(state: TrackingWorkflowState, context: RefundContext) -> TrackingWorkflowState:
    state.active_order_ids = [context.order.id]
    state.tool_logs.append({"node": "order_node", "tool": "resolve_refund_order"})
    return state


def policy_rag_node(state: TrackingWorkflowState, context: RefundContext) -> TrackingWorkflowState:
    state.tool_logs.append(
        {
            "node": "policy_rag_node",
            "tool": "select_relevant_policy_titles",
            "policies": select_relevant_policy_titles(context.policies),
        }
    )
    return state


def refund_node(db: Session, state: TrackingWorkflowState, context: RefundContext) -> tuple[TrackingWorkflowState, RefundRequest]:
    if context.existing_refund_request is not None:
        refund_request = context.existing_refund_request
        state.tool_logs.append({"node": "refund_node", "tool": "load_existing_refund_request", "refund_request_id": refund_request.id})
        return state, refund_request

    refund_request = RefundRequest(
        id=_new_prefixed_id("RF"),
        order_id=context.order.id,
        customer_id=context.customer.id,
        case_id=None,
        reason=state.raw_message,
        requested_resolution="refund",
        eligibility_status="under_review",
        risk_score=0,
        ai_recommendation="Pending evidence and policy review.",
        status="pending",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(refund_request)
    db.flush()
    state.tool_logs.append({"node": "refund_node", "tool": "create_refund_request", "refund_request_id": refund_request.id})
    return state, refund_request


def evidence_node(state: TrackingWorkflowState, context: RefundContext) -> tuple[TrackingWorkflowState, dict[str, object]]:
    evidence_result = evaluate_evidence(context.attachments)
    state.tool_logs.append({"node": "evidence_node", "tool": "evaluate_evidence", "result": evidence_result})
    return state, evidence_result


def risk_node(
    db: Session,
    state: TrackingWorkflowState,
    context: RefundContext,
    refund_request: RefundRequest,
    evidence_result: dict[str, object],
) -> TrackingWorkflowState:
    risk_score = calculate_refund_risk(
        float(context.order.total_amount) if context.order.total_amount is not None else None,
        evidence_result,
    )
    refund_request.risk_score = risk_score
    refund_request.ai_recommendation = "Approve review queue" if risk_score < 70 else "Escalate for approval"
    refund_request.updated_at = datetime.utcnow()
    db.flush()
    state.tool_logs.append({"node": "risk_node", "tool": "calculate_refund_risk", "risk_score": risk_score})
    return state


def supervisor_node(state: TrackingWorkflowState, refund_request: RefundRequest) -> TrackingWorkflowState:
    requires_approval = refund_request.risk_score >= 70
    state.tool_logs.append({"node": "supervisor_node", "tool": "determine_human_review", "requires_approval": requires_approval})
    if requires_approval:
        state.fallback_reason = "requires_human_approval"
    return state


def approval_node(db: Session, state: TrackingWorkflowState, case: Case, refund_request: RefundRequest) -> TrackingWorkflowState:
    if refund_request.risk_score < 70:
        state.tool_logs.append({"node": "approval_node", "tool": "skip_approval"})
        return state

    from app.db.models import Approval

    approval = Approval(
        id=_new_prefixed_id("APR"),
        case_id=case.id,
        approval_type="refund",
        requested_action="Review refund recommendation",
        amount=refund_request.order.total_amount if hasattr(refund_request, "order") else None,
        currency="THB",
        risk_level="high",
        status="pending",
        ai_reason="High risk refund request requires manual approval.",
        policy_citation={"workflow": "workflow_02_refund_return"},
        created_at=datetime.utcnow(),
    )
    db.add(approval)
    db.flush()
    state.tool_logs.append({"node": "approval_node", "tool": "create_or_load_approval", "approval_id": approval.id})
    return state


def ensure_case_node(db: Session, state: TrackingWorkflowState, context: RefundContext, refund_request: RefundRequest) -> tuple[TrackingWorkflowState, Case]:
    if context.existing_case is not None:
        case = context.existing_case
        if refund_request.case_id is None:
            refund_request.case_id = case.id
            refund_request.updated_at = datetime.utcnow()
            db.flush()
        state.tool_logs.append({"node": "case_node", "tool": "load_existing_case", "case_id": case.id})
        return state, case

    policy_titles = [p.title for p in context.policies[:3] if p.title]
    ai_summary = (
        f"Customer {context.customer.name} requested refund for order {context.order.id}. "
        f"Amount: {context.order.total_amount} {context.order.currency}."
        + (f" Policies: {', '.join(policy_titles)}." if policy_titles else "")
    )

    case = Case(
        id=_new_prefixed_id("CS"),
        customer_id=context.customer.id,
        order_id=context.order.id,
        case_type="refund",
        priority="medium",
        status="open",
        ai_summary=ai_summary,
        assigned_role="admin",
        created_by="ai",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(case)
    db.flush()
    refund_request.case_id = case.id
    refund_request.updated_at = datetime.utcnow()
    db.flush()
    state.tool_logs.append({"node": "case_node", "tool": "create_case", "case_id": case.id})
    return state, case


def refund_support_response_node(
    state: TrackingWorkflowState,
    context: RefundContext,
    case: Case,
    evidence_result: dict[str, object],
) -> TrackingWorkflowState:
    response = build_refund_response(
        order_id=context.order.id,
        case_id=case.id,
        has_evidence=bool(evidence_result.get("sufficient", False)),
    )
    policy_titles = [p.title for p in context.policies[:2] if p.title]
    if policy_titles:
        response += f" (อ้างอิงนโยบาย: {', '.join(policy_titles)})"
    state.response_text = response
    state.tool_logs.append({"node": "support_response_node", "tool": "build_refund_response"})
    return state


def refund_memory_write_node(state: TrackingWorkflowState, case: Case) -> TrackingWorkflowState:
    state.memory_summary = f"Refund case {case.id} opened for customer {state.customer_name}."
    state.tool_logs.append({"node": "memory_write_node", "tool": "write_refund_memory"})
    return state


def refund_logging_node(state: TrackingWorkflowState) -> TrackingWorkflowState:
    state.tool_logs.append({"node": "logging_node", "tool": "finalize_refund_workflow"})
    return state
