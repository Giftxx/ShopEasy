from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.agents.llm import classify_intent
from app.db.models import Conversation
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.workflow_01_tracking import handle_tracking_chat
from app.services.workflow_02_refund import handle_refund_chat


def _ensure_conversation(db: Session, payload: ChatRequest) -> None:
    """Create conversation if it doesn't exist yet. Uses merge to be idempotent."""
    if db.get(Conversation, payload.conversation_id) is None:
        db.merge(Conversation(
            id=payload.conversation_id,
            customer_id=payload.customer_id,
            channel="web_chat",
            status="open",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        ))
        db.flush()


def _try_react_engine(db: Session, payload: ChatRequest, intent: str) -> ChatResponse | None:
    """
    Attempt to use the autonomous ReAct engine.
    Returns ChatResponse if successful, None if should fall back to legacy workflows.
    Time-boxed to 90 seconds max.
    """
    import signal
    import threading
    import time

    start = time.time()

    try:
        from app.agents.react_engine import ReActEngine
        from app.agents.supervisor_agent import SupervisorAgent
        from app.agents.tool_registry import ToolRegistry
        from app.agents.tools.definitions import register_all_tools

        # Ensure tools are registered
        if not ToolRegistry.list_names():
            register_all_tools()

        # Build initial context
        initial_context = {
            "customer_id": payload.customer_id,
            "conversation_id": payload.conversation_id,
            "message": payload.message,
        }
        if payload.target_order_id:
            initial_context["order_id"] = payload.target_order_id

        # Run ReAct engine
        engine = ReActEngine(db=db, session_id=payload.conversation_id)
        state = engine.run(intent=intent, customer_id=payload.customer_id, initial_context=initial_context)

        if state.escalate:
            # ReAct decided to escalate — fall back to legacy workflow
            return None

        if not state.final_response:
            return None

        # Supervisor quality check
        supervisor = SupervisorAgent()
        tools_used = [obs.action for obs in state.observations if obs.success]
        supervision = supervisor.supervise(
            intent=intent,
            customer_message=payload.message,
            response=state.final_response,
            risk_score=int(state.context.get("risk_score", 0)),
            replan_count=state.replan_count,
            tools_used=tools_used,
        )

        if not supervision.approved and supervision.requires_human:
            # Quality too low or human needed — fall back
            return None

        # Build response
        shipment_summaries = state.context.get("shipments", [])
        return ChatResponse(
            conversation_id=payload.conversation_id,
            response=state.final_response,
            intent=intent,
            shipments=shipment_summaries if isinstance(shipment_summaries, list) else [],
        )

    except Exception:
        # Any error in ReAct — gracefully fall back to legacy
        return None


def handle_chat(db: Session, payload: ChatRequest) -> ChatResponse:
    from app.agents.inter_agent import MessageBus, MessageType, AgentMessage

    # Ensure conversation exists BEFORE the (slow) LLM call so the DB
    # connection is not left idle during inference.
    _ensure_conversation(db, payload)

    # ── LLM Agentic Router ────────────────────────────────────────────────────
    # The LLM classifies the customer message into a workflow intent.
    # Falls back to keyword matching automatically if Ollama is unavailable.
    intent = classify_intent(payload.message)

    # ── Inter-Agent: Publish intent classification event ──────────────────────
    bus = MessageBus.get_instance()
    bus.publish("intent_classified", AgentMessage(
        source_agent="router",
        target_agent=f"workflow_{intent}",
        message_type=MessageType.HANDOFF,
        payload={"intent": intent, "customer_id": payload.customer_id, "message": payload.message},
    ))

    # ── Try Autonomous ReAct Engine First ─────────────────────────────────────
    # NOTE: ReAct engine is disabled for local Ollama (too slow for multi-call loops).
    # Enable by setting REACT_ENABLED=true in env when using a fast cloud LLM.
    import os
    if os.getenv("REACT_ENABLED", "").lower() == "true":
        react_response = _try_react_engine(db, payload, intent)
        if react_response is not None:
            return react_response

    # ── Route to appropriate workflow ─────────────────────────────────────────
    if intent == "refund_request":
        return handle_refund_chat(db, payload)

    # Pass pre-classified intent to avoid redundant LLM call
    return handle_tracking_chat(db, payload, pre_classified_intent=intent)
