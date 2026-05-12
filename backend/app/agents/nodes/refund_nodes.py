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
    """Use the LLM to classify intent (falls back to keywords)."""
    from app.agents.llm import classify_intent
    state.detected_intent = classify_intent(state.raw_message)
    state.tool_logs.append({"node": "router_node", "tool": "classify_intent_llm"})
    return state


def refund_context_resolution_node(db: Session, state: TrackingWorkflowState) -> tuple[TrackingWorkflowState, RefundContext]:
    context = get_refund_context(db, state.customer_id, state.conversation_id, state.target_order_id)
    if context is None:
        raise HTTPException(status_code=404, detail="Customer, conversation, or order not found.")

    state.customer_name = context.customer.name
    state.active_order_ids = [context.order.id]
    state.tool_logs.append({"node": "context_resolution_node", "tool": "get_refund_context"})
    return state, context


def refund_memory_retrieval_node(db: Session, state: TrackingWorkflowState, context: RefundContext) -> TrackingWorkflowState:
    """Retrieve all 3 layers of memory for refund context."""
    import logging

    from app.agents.memory.episodic import EpisodicMemory
    from app.agents.memory.long_term import LongTermMemory
    from app.agents.memory.short_term import ShortTermMemory

    logger = logging.getLogger(__name__)
    parts: list[str] = [f"Customer {context.customer.name} requested refund support for order {context.order.id}."]

    # Short-term: previous session context
    try:
        stm = ShortTermMemory(session_id=state.conversation_id)
        prev = stm.get_all()
        if prev:
            parts.append("Session: " + ", ".join(f"{k}={v}" for k, v in list(prev.items())[:5]))
    except Exception as e:
        logger.debug("Short-term memory error: %s", e)

    # Long-term: customer patterns
    try:
        ltm = LongTermMemory(db=db, customer_id=state.customer_id)
        summary = ltm.build_summary()
        if summary and "ไม่มี" not in summary:
            parts.append(summary)
    except Exception as e:
        logger.debug("Long-term memory error: %s", e)

    # Episodic: past refund/fraud history
    try:
        em = EpisodicMemory(db=db, customer_id=state.customer_id)
        episodes = em.recall(event_types=["refund_abuse", "fraud", "dispute"], limit=5)
        if episodes:
            ep_lines = [f"  - [{ep['type']}] {ep['summary']}" for ep in episodes]
            parts.append("Risk history:\n" + "\n".join(ep_lines))
    except Exception as e:
        logger.debug("Episodic memory error: %s", e)

    state.memory_summary = "\n".join(parts)
    state.tool_logs.append({"node": "memory_retrieval_node", "tool": "build_3layer_refund_memory", "layers": len(parts)})
    return state


def refund_planner_node(db: Session, state: TrackingWorkflowState) -> TrackingWorkflowState:
    """Create an execution plan for the refund workflow."""
    import logging

    from app.agents.planner import Planner
    from app.db.models.memory import ExecutionPlanRecord

    logger = logging.getLogger(__name__)

    state.selected_workflow = "workflow_02_refund_return"

    try:
        planner = Planner()
        plan = planner.create_plan(
            intent="refund_request",
            context={"customer_id": state.customer_id, "order_id": state.target_order_id},
            available_tools=["get_order_detail", "search_policy", "calculate_refund_risk", "evaluate_evidence"],
        )

        record = ExecutionPlanRecord(
            trace_id=state.trace_id,
            intent="refund_request",
            plan_json=plan.to_dict(),
            risk_level=plan.risk_level,
            replan_count=plan.replan_count,
        )
        db.add(record)
        db.flush()

        state.tool_logs.append({
            "node": "planner_node", "tool": "create_execution_plan",
            "plan_id": plan.plan_id, "steps": len(plan.steps), "risk_level": plan.risk_level,
        })
    except Exception as e:
        logger.debug("Planner error (using default): %s", e)
        state.tool_logs.append({"node": "planner_node", "tool": "select_refund_workflow_fallback"})
    return state


def refund_order_node(state: TrackingWorkflowState, context: RefundContext) -> TrackingWorkflowState:
    state.active_order_ids = [context.order.id]
    state.tool_logs.append({"node": "order_node", "tool": "resolve_refund_order"})
    return state


def policy_rag_node(state: TrackingWorkflowState, context: RefundContext, db: Session) -> TrackingWorkflowState:
    from app.services.policy_rag import search_policy_hybrid

    # Search for policy chunks relevant to the customer's message (hybrid: vector + keyword)
    query = state.raw_message or "คืนเงิน สินค้าเสียหาย"
    results = search_policy_hybrid(db, query=query, limit=5)

    # Also include all policy titles from context for backwards compatibility
    title_log = select_relevant_policy_titles(context.policies)

    # Store retrieved chunk texts in state for use in response node
    state.policy_chunks = [r["chunk_text"] for r in results]
    state.policy_titles = [r["policy_title"] for r in results] or title_log

    state.tool_logs.append(
        {
            "node": "policy_rag_node",
            "tool": "search_policy_chunks",
            "query": query,
            "results_count": len(results),
            "chunk_previews": [r["chunk_text"][:60] for r in results],
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
    """Full supervisor evaluation: rule-based + LLM quality gate + escalation."""
    from app.agents.inter_agent import MessageBus
    from app.agents.supervisor_agent import SupervisorAgent

    # Run full supervisor evaluation
    supervisor = SupervisorAgent()
    result = supervisor.supervise(
        intent="refund_request",
        customer_message=state.raw_message or "",
        response=state.response_text or "pending",
        risk_score=refund_request.risk_score,
        tools_used=[log.get("tool", "") for log in state.tool_logs],
    )

    requires_approval = result.requires_human or refund_request.risk_score >= 70

    state.tool_logs.append({
        "node": "supervisor_node",
        "tool": "full_supervisor_evaluation",
        "requires_approval": requires_approval,
        "quality_score": result.quality_score,
        "issues": result.issues,
    })

    if requires_approval:
        state.fallback_reason = "requires_human_approval"
        # Escalate via inter-agent protocol
        bus = MessageBus.get_instance()
        bus.escalate(
            source="refund_workflow",
            context={"refund_id": refund_request.id, "customer_id": state.customer_id,
                      "quality_score": result.quality_score, "issues": result.issues},
            reason=result.reason or f"High risk refund (score={refund_request.risk_score})",
            risk_score=refund_request.risk_score,
        )
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
    from app.agents.llm import REFUND_SYSTEM_PROMPT, call_llm

    # Use chunks retrieved by policy_rag_node (real search results)
    policy_chunks = getattr(state, "policy_chunks", [])
    policy_titles = getattr(state, "policy_titles", [p.title for p in context.policies[:3] if p.title])
    requires_approval = state.fallback_reason == "requires_human_approval"

    context_lines = [
        f"ชื่อลูกค้า: {context.customer.name}",
        f"ออเดอร์: {context.order.id}, มูลค่า: {context.order.total_amount} {context.order.currency or 'THB'}",
        f"เคสที่เปิด: {case.id}",
        f"หลักฐานที่อัปโหลด: {evidence_result.get('attachment_count', 0)} ไฟล์, "
        f"เพียงพอ: {'ใช่' if evidence_result.get('sufficient') else 'ไม่เพียงพอ'}",
    ]
    if evidence_result.get("evidence_groups"):
        groups = ", ".join(str(g) for g in evidence_result["evidence_groups"])
        context_lines.append(f"กลุ่มหลักฐาน: {groups}")

    # Include actual policy chunk text so the LLM can cite real policies
    if policy_chunks:
        context_lines.append("\n[นโยบายที่เกี่ยวข้อง (ค้นพบจากระบบ)]")
        for i, chunk in enumerate(policy_chunks[:3], 1):
            context_lines.append(f"{i}. {chunk}")
    elif policy_titles:
        context_lines.append(f"นโยบายที่เกี่ยวข้อง: {', '.join(policy_titles)}")

    context_lines.append(
        f"สถานะ: {'ต้องรอการอนุมัติจากเจ้าหน้าที่' if requires_approval else 'อยู่ระหว่างการตรวจสอบโดย AI'}"
    )

    context_str = "\n".join(context_lines)
    raw_message = state.raw_message or "ขอคืนเงิน"

    llm_response = call_llm(REFUND_SYSTEM_PROMPT, context_str, raw_message)
    if llm_response:
        state.response_text = llm_response
    else:
        # Template fallback
        response = build_refund_response(
            order_id=context.order.id,
            case_id=case.id,
            has_evidence=bool(evidence_result.get("sufficient", False)),
        )
        if policy_titles:
            response += f" (อ้างอิงนโยบาย: {', '.join(policy_titles[:2])})"
        state.response_text = response

    state.tool_logs.append({"node": "support_response_node", "tool": "call_llm_refund_response"})
    return state


def refund_memory_write_node(db: Session, state: TrackingWorkflowState, case: Case, refund_request: RefundRequest) -> TrackingWorkflowState:
    """Persist memory across all 3 layers after refund workflow."""
    import logging

    from app.agents.memory.episodic import EpisodicMemory
    from app.agents.memory.long_term import LongTermMemory
    from app.agents.memory.short_term import ShortTermMemory

    logger = logging.getLogger(__name__)

    # Short-term: save session state
    try:
        stm = ShortTermMemory(session_id=state.conversation_id)
        stm.save("last_workflow", "workflow_02_refund_return")
        stm.save("last_case_id", case.id)
        stm.save("last_refund_id", refund_request.id)
    except Exception as e:
        logger.debug("Short-term write error: %s", e)

    # Long-term: record refund behavior
    if state.customer_id:
        try:
            ltm = LongTermMemory(db=db, customer_id=state.customer_id)
            ltm.save(
                memory_type="behavior",
                key="last_refund_request",
                value={"case_id": case.id, "order_id": state.active_order_ids[0] if state.active_order_ids else None,
                       "risk_score": refund_request.risk_score},
                source_agent="refund_workflow",
            )
            # Track refund frequency
            count = ltm.get("refund_count")
            ltm.save(
                memory_type="pattern",
                key="refund_count",
                value={"count": (count.get("count", 0) if isinstance(count, dict) else 0) + 1},
                source_agent="refund_workflow",
            )
        except Exception as e:
            logger.debug("Long-term write error: %s", e)

    # Episodic: record significant refund event
    if state.customer_id:
        try:
            em = EpisodicMemory(db=db, customer_id=state.customer_id)
            event_type = "refund_abuse" if refund_request.risk_score >= 70 else "dispute"
            em.store(
                event_type=event_type,
                summary=f"Refund case {case.id} for order {state.active_order_ids[0] if state.active_order_ids else '?'}, risk={refund_request.risk_score}",
                metadata={"case_id": case.id, "risk_score": refund_request.risk_score, "refund_id": refund_request.id},
            )
        except Exception as e:
            logger.debug("Episodic write error: %s", e)

    state.memory_summary = f"Refund case {case.id} opened for customer {state.customer_name}."
    state.tool_logs.append({"node": "memory_write_node", "tool": "persist_3layer_refund_memory"})
    return state


def refund_logging_node(state: TrackingWorkflowState) -> TrackingWorkflowState:
    state.tool_logs.append({"node": "logging_node", "tool": "finalize_refund_workflow"})
    return state
