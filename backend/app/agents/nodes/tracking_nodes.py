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
    """Determine the initial intent of the user."""
    raw_message = state.get("raw_message", "")
    intent = detect_tracking_intent(raw_message)
    state["detected_intent"] = intent
    _add_tool_call(state, "router_node", "detect_tracking_intent", {"intent": intent})
    return state


def context_resolution_node(db: Session, state: GraphState) -> GraphState:
    """Fetch the full business context for the tracking workflow."""
    customer_id = state.get("customer_id")
    conversation_id = state.get("conversation_id")

    if not customer_id or not conversation_id:
        raise ValueError("customer_id and conversation_id must be in state")

    # Auto-create conversation if it doesn't exist
    if db.get(Conversation, conversation_id) is None:
        db.add(Conversation(
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
    state["active_shipments"] = [shipment.to_dict(include_relationships=True) for shipment in context.active_shipments]
    state["active_order_ids"] = [order.id for order in context.active_orders]
    state["active_shipment_ids"] = [shipment.id for shipment in context.active_shipments]
    
    _add_tool_call(state, "context_resolution_node", "get_tracking_context")
    return state


def memory_retrieval_node(state: GraphState) -> GraphState:
    """Build a summary of the conversation memory."""
    customer = state.get("customer", {})
    orders = state.get("active_orders", [])
    shipments = state.get("active_shipments", [])

    if customer:
        # build_memory_summary uses _get_attr which handles dicts natively
        context = {
            "customer": customer,
            "active_orders": orders,
            "active_shipments": shipments,
        }
        state["memory_summary"] = build_memory_summary(context)
        _add_tool_call(state, "memory_retrieval_node", "build_memory_summary")

    return state


def planner_node(state: GraphState) -> GraphState:
    """Select the appropriate workflow based on the current state."""
    state["selected_workflow"] = "workflow_01_track_shipment"
    _add_tool_call(state, "planner_node", "select_workflow")
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
    """Generate the final response for the user."""
    shipment_summaries = state.get("shipments", [])

    if shipment_summaries:
        # build_tracking_response uses _get_attr which handles dicts natively
        response_text = build_tracking_response(shipment_summaries)
        state["customer_response"] = response_text
    else:
        state["customer_response"] = "ขออภัยค่ะ ไม่พบข้อมูลการจัดส่งสำหรับออเดอร์ของคุณในขณะนี้"

    _add_tool_call(state, "support_response_node", "build_tracking_response")
    return state


def fallback_node(state: GraphState) -> GraphState:
    """Provide a fallback response when the workflow cannot proceed."""
    state["fallback_reason"] = state.get("fallback_reason", "Unknown reason")
    state["customer_response"] = "ขออภัยค่ะ ตอนนี้ฉันยังระบุพัสดุที่ต้องการติดตามไม่ได้ ช่วยส่งเลขออเดอร์ให้ฉันได้ไหมคะ?"
    _add_tool_call(state, "fallback_node", "fallback_response")
    return state
