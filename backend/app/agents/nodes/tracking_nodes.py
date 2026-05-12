from __future__ import annotations

from datetime import datetime
from functools import partial

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.agents.state import GraphState
from app.agents.tools.tracking import (
    build_memory_summary,
    build_shipment_summaries,
    build_tracking_response,
    detect_tracking_intent,
)
from app.db.models import Conversation
from app.repositories.tracking import get_tracking_context


def _add_tool_call(state: GraphState, node: str, tool: str, result: dict | None = None) -> None:
    if "tool_calls" not in state:
        state["tool_calls"] = []
    log = {"node": node, "tool": tool}
    if result:
        log.update(result)
    state["tool_calls"].append(log)


def router_node(state: GraphState) -> GraphState:
    """Use the LLM to classify the customer's intent (falls back to keywords)."""
    # Skip LLM call if intent was already pre-classified
    existing = state.get("detected_intent")
    if existing:
        _add_tool_call(state, "router_node", "classify_intent_cached", {"intent": existing})
        return state
    from app.agents.llm import classify_intent
    raw_message = state.get("raw_message", "")
    intent = classify_intent(raw_message)
    state["detected_intent"] = intent
    _add_tool_call(state, "router_node", "classify_intent_llm", {"intent": intent})
    return state


def context_resolution_node(db: Session, state: GraphState) -> GraphState:
    """Fetch the full business context for the tracking workflow."""
    customer_id = state.get("customer_id")
    conversation_id = state.get("conversation_id")

    if not customer_id or not conversation_id:
        raise ValueError("customer_id and conversation_id must be in state")

    # Auto-create conversation if it doesn't exist (merge is idempotent)
    if db.get(Conversation, conversation_id) is None:
        db.merge(Conversation(
            id=conversation_id,
            customer_id=customer_id,
            channel="web_chat",
            status="open",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        ))
        db.flush()

    context = get_tracking_context(db=db, customer_id=customer_id, conversation_id=conversation_id)
    if context is None:
        raise HTTPException(status_code=404, detail="Customer or conversation not found.")

    state["customer"] = context.customer.to_dict()
    state["active_orders"] = [order.to_dict(include_relationships=True) for order in context.active_orders]

    enriched_shipments = []
    for shipment in context.active_shipments:
        s = shipment.to_dict(include_relationships=True)
        # Enrich seller_name from ORM object (nested relations not in to_dict)
        try:
            s["seller_name"] = shipment.order.seller.name
        except AttributeError:
            s["seller_name"] = "Unknown seller"
        # Enrich item_names from ORM object
        try:
            s["item_names"] = [
                si.order_item.product_name
                for si in shipment.shipment_items
                if si.order_item and si.order_item.product_name
            ] or ["สินค้า"]
        except AttributeError:
            s["item_names"] = ["สินค้า"]
        enriched_shipments.append(s)

    state["active_shipments"] = enriched_shipments
    state["active_order_ids"] = [order.id for order in context.active_orders]
    state["active_shipment_ids"] = [shipment.id for shipment in context.active_shipments]
    
    _add_tool_call(state, "context_resolution_node", "get_tracking_context")
    return state


def memory_retrieval_node(db: Session, state: GraphState) -> GraphState:
    """Build a summary from all 3 memory layers: short-term, long-term, episodic."""
    import logging

    from app.agents.memory.episodic import EpisodicMemory
    from app.agents.memory.long_term import LongTermMemory
    from app.agents.memory.short_term import ShortTermMemory

    logger = logging.getLogger(__name__)
    customer = state.get("customer", {})
    customer_id = state.get("customer_id", "")
    conversation_id = state.get("conversation_id", "")
    orders = state.get("active_orders", [])
    shipments = state.get("active_shipments", [])

    parts: list[str] = []

    # Layer 1: Short-term (Redis) — current session context
    try:
        stm = ShortTermMemory(session_id=conversation_id)
        prev = stm.get_all()
        if prev:
            parts.append("Session context: " + ", ".join(f"{k}={v}" for k, v in list(prev.items())[:5]))
        # Save current turn context
        stm.save("last_intent", state.get("detected_intent", "unknown"))
        stm.save("active_orders", [o.get("id") for o in orders] if orders else [])
    except Exception as e:
        logger.debug("Short-term memory error: %s", e)

    # Layer 2: Long-term (PostgreSQL) — persistent customer patterns
    if customer_id:
        try:
            ltm = LongTermMemory(db=db, customer_id=customer_id)
            summary = ltm.build_summary()
            if summary and "ไม่มี" not in summary:
                parts.append(summary)
        except Exception as e:
            logger.debug("Long-term memory error: %s", e)

    # Layer 3: Episodic (PostgreSQL) — significant past events
    if customer_id:
        try:
            em = EpisodicMemory(db=db, customer_id=customer_id)
            episodes = em.recall(limit=5)
            if episodes:
                ep_lines = [f"  - [{ep['type']}] {ep['summary']}" for ep in episodes]
                parts.append("Episodic history:\n" + "\n".join(ep_lines))
        except Exception as e:
            logger.debug("Episodic memory error: %s", e)

    # Layer 0: Business context summary (always available)
    if customer:
        context = {"customer": customer, "active_orders": orders, "active_shipments": shipments}
        parts.append(build_memory_summary(context))

    state["memory_summary"] = "\n".join(parts) if parts else None
    _add_tool_call(state, "memory_retrieval_node", "build_3layer_memory", {"layers": len(parts)})

    return state


def planner_node(db: Session, state: GraphState) -> GraphState:
    """Create an execution plan for the tracking workflow and persist it."""
    import logging

    from app.agents.planner import Planner
    from app.db.models.memory import ExecutionPlanRecord

    logger = logging.getLogger(__name__)
    intent = state.get("detected_intent", "track_shipment")
    customer_id = state.get("customer_id", "")

    state["selected_workflow"] = "workflow_01_track_shipment"

    try:
        planner = Planner()
        plan = planner.create_plan(
            intent=intent,
            context={"customer_id": customer_id, "active_orders": state.get("active_order_ids", [])},
            available_tools=["get_shipment_status", "build_tracking_response", "search_policy"],
        )
        state["execution_plan"] = plan.to_dict()

        # Persist plan to database
        record = ExecutionPlanRecord(
            trace_id=state.get("trace_id"),
            intent=intent,
            plan_json=plan.to_dict(),
            risk_level=plan.risk_level,
            replan_count=plan.replan_count,
        )
        db.add(record)
        db.flush()

        _add_tool_call(state, "planner_node", "create_execution_plan", {
            "plan_id": plan.plan_id, "steps": len(plan.steps), "risk_level": plan.risk_level
        })
    except Exception as e:
        logger.debug("Planner error (using default): %s", e)
        _add_tool_call(state, "planner_node", "select_workflow_fallback")
    return state


def shipping_node(state: GraphState) -> GraphState:
    """Summarize shipment information."""
    shipments = state.get("active_shipments", [])

    if shipments:
        # build_shipment_summaries uses _get_attr which handles dicts natively
        context = {"active_shipments": shipments}
        shipment_summaries = build_shipment_summaries(context)
        state["shipments"] = [s.model_dump() for s in shipment_summaries]

    _add_tool_call(state, "shipping_node", "build_shipment_summaries")
    return state


def support_response_node(state: GraphState) -> GraphState:
    """Generate the final response using GPT with real shipment context."""
    from app.agents.llm import TRACKING_SYSTEM_PROMPT, call_llm

    shipment_summaries = state.get("shipments", [])
    raw_message = state.get("raw_message", "")

    if shipment_summaries:
        # Build structured context for GPT from real DB data
        customer = state.get("customer", {})
        lines: list[str] = []
        if isinstance(customer, dict) and customer.get("name"):
            lines.append(f"ชื่อลูกค้า: {customer['name']}")
        for i, s in enumerate(shipment_summaries, 1):
            status = s.get("shipment_status") or s.get("status", "ไม่ทราบสถานะ")
            items = ", ".join(s.get("item_names", ["สินค้า"]))
            lines.append(
                f"พัสดุ {i}: ออเดอร์ {s.get('order_id', '?')} "
                f"จากร้าน {s.get('seller_name', '?')}, "
                f"สินค้า: {items}, สถานะ: {status}, "
                f"หมายเหตุ: {s.get('note', '')}"
            )
        context_str = "\n".join(lines)

        llm_response = call_llm(TRACKING_SYSTEM_PROMPT, context_str, raw_message)
        if llm_response:
            state["customer_response"] = llm_response
        else:
            state["customer_response"] = build_tracking_response(shipment_summaries)
    else:
        state["customer_response"] = "ขออภัยค่ะ ไม่พบข้อมูลการจัดส่งสำหรับออเดอร์ของคุณในขณะนี้"

    _add_tool_call(state, "support_response_node", "call_llm_tracking_response")
    return state


def fallback_node(state: GraphState) -> GraphState:
    """Use GPT to handle general inquiries that aren't tracking or refund."""
    from app.agents.llm import GENERAL_SYSTEM_PROMPT, call_llm

    raw_message = state.get("raw_message", "")
    state["fallback_reason"] = state.get("fallback_reason", "general_inquiry")

    context_str = (
        "แพลตฟอร์ม: ShopEasy อีคอมเมิร์ซไทย\n"
        "ลูกค้าถามคำถามทั่วไปที่ระบบตรวจไม่พบ intent ชัดเจน"
    )
    llm_response = call_llm(GENERAL_SYSTEM_PROMPT, context_str, raw_message)
    if llm_response:
        state["customer_response"] = llm_response
    else:
        state["customer_response"] = (
            "ขออภัยค่ะ สามารถช่วยเรื่องการติดตามพัสดุหรือการคืนเงินได้เลยค่ะ "
            "กรุณาระบุเลขออเดอร์หรืออธิบายปัญหาเพิ่มเติมได้ค่ะ"
        )

    _add_tool_call(state, "fallback_node", "call_llm_general_response")
    return state


def memory_write_node(db: Session, state: GraphState) -> GraphState:
    """Persist memory after each interaction across all 3 layers."""
    import logging

    from app.agents.memory.long_term import LongTermMemory
    from app.agents.memory.short_term import ShortTermMemory

    logger = logging.getLogger(__name__)
    customer_id = state.get("customer_id", "")
    conversation_id = state.get("conversation_id", "")
    intent = state.get("detected_intent", "unknown")

    # Layer 1: Short-term — save response for session continuity
    try:
        stm = ShortTermMemory(session_id=conversation_id)
        stm.save("last_response", (state.get("customer_response") or "")[:500])
        stm.save("last_workflow", state.get("selected_workflow", ""))
    except Exception as e:
        logger.debug("Short-term memory write error: %s", e)

    # Layer 2: Long-term — record interaction pattern
    if customer_id:
        try:
            ltm = LongTermMemory(db=db, customer_id=customer_id)
            ltm.save(
                memory_type="behavior",
                key=f"last_intent",
                value={"intent": intent, "workflow": state.get("selected_workflow", "")},
                source_agent="tracking_workflow",
            )
            # Track interaction frequency
            count = ltm.get("interaction_count")
            ltm.save(
                memory_type="pattern",
                key="interaction_count",
                value={"count": (count.get("count", 0) if isinstance(count, dict) else 0) + 1},
                source_agent="tracking_workflow",
            )
        except Exception as e:
            logger.debug("Long-term memory write error: %s", e)

    _add_tool_call(state, "memory_write_node", "persist_3layer_memory")
    return state
