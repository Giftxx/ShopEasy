from datetime import datetime

from sqlalchemy.orm import Session

from app.agents.llm import classify_intent
from app.db.models import Conversation
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.workflow_01_tracking import handle_tracking_chat
from app.services.workflow_02_refund import handle_refund_chat


def _handle_policy_chat(db: Session, payload: ChatRequest) -> ChatResponse:
    """
    Handle a policy question using ONLY the admin-uploaded policy knowledge base
    (RAG with vector + keyword fallback). Never falls back to general LLM
    knowledge and never reads customer order data.
    """
    import logging

    from sqlalchemy import func, select

    from app.agents.llm import call_llm
    from app.db.models import Policy, PolicyChunk
    from app.services.policy_rag import search_policy_hybrid

    logger = logging.getLogger(__name__)
    raw_message = payload.message

    # Quick sanity check — is there any policy/chunk uploaded at all?
    active_policies = db.scalar(
        select(func.count(Policy.id)).where(Policy.status == "active")
    ) or 0
    chunk_count = db.scalar(select(func.count(PolicyChunk.id))) or 0

    rag_results: list[dict] = []
    if active_policies > 0 and chunk_count > 0:
        try:
            rag_results = search_policy_hybrid(db, query=raw_message, limit=5)
        except Exception as exc:
            logger.warning("Policy RAG search failed: %s", exc)

    logger.info(
        "intent=policy_question | tool=search_policy_hybrid | "
        "active_policies=%d chunks=%d retrieved=%d | conversation=%s | q=%.80s",
        active_policies,
        chunk_count,
        len(rag_results),
        payload.conversation_id,
        raw_message,
    )

    if active_policies == 0 or chunk_count == 0:
        response_text = (
            "ขณะนี้ยังไม่มีเอกสารนโยบายในระบบค่ะ "
            "กรุณาให้ผู้ดูแลอัปโหลดนโยบายในหน้า Admin → Policies ก่อน "
            "แล้วลองสอบถามอีกครั้ง"
        )
    elif not rag_results:
        response_text = (
            "ไม่พบข้อมูลนี้ในนโยบายที่อัปโหลดไว้ "
            "กรุณาลองพิมพ์คำถามใหม่ด้วยคำสำคัญที่ตรงกับชื่อนโยบาย "
            "หรือติดต่อเจ้าหน้าที่เพื่อตรวจสอบเพิ่มเติมค่ะ"
        )
    else:
        # Deduplicate chunks by normalised text before building context.
        # Vector search + keyword fallback can return the same physical chunk twice.
        seen_texts: set[str] = set()
        deduped: list[dict] = []
        for r in rag_results:
            norm = (r.get("chunk_text") or "").strip()
            if norm and norm not in seen_texts:
                seen_texts.add(norm)
                deduped.append(r)

        policy_lines: list[str] = []
        sources: list[str] = []
        for r in deduped:
            title = r.get("policy_title") or ""
            heading = r.get("heading") or ""
            text = r.get("chunk_text") or ""
            if text:
                label = f"{title} — {heading}" if heading else title
                policy_lines.append(f"[{label}]\n{text}")
                if title and title not in sources:
                    sources.append(title)

        context_str = "นโยบายที่เกี่ยวข้อง:\n" + "\n\n---\n\n".join(policy_lines)

        POLICY_ONLY_SYSTEM_PROMPT = (
            "คุณคือผู้ช่วยตอบคำถามเกี่ยวกับนโยบายของ ShopEasy "
            "ตอบโดยใช้เฉพาะข้อมูลใน 'นโยบายที่เกี่ยวข้อง' ที่ระบบส่งให้เท่านั้น "
            "ห้ามใช้ความรู้ทั่วไป ห้ามเดา\n"
            "กฎการตอบ:\n"
            "- สรุปเป็นข้อๆ กระชับ ไม่เกิน 5 ข้อ\n"
            "- แต่ละข้อต้องมีเนื้อหาต่างกัน ห้ามซ้ำ\n"
            "- ห้ามนับเลขข้อที่เนื้อหาซ้ำหรือเหมือนข้ออื่น\n"
            "- ถ้าข้อมูลในนโยบายไม่ครอบคลุมคำถาม ให้ตอบว่า "
            "'ไม่พบข้อมูลนี้ในนโยบายที่อัปโหลดไว้ กรุณาติดต่อเจ้าหน้าที่'\n"
            "- ตอบเป็นภาษาเดียวกับคำถาม อ้างชื่อนโยบายท้ายคำตอบ"
        )

        llm_response = call_llm(POLICY_ONLY_SYSTEM_PROMPT, context_str, raw_message)
        response_text = llm_response or (
            "พบข้อมูลในนโยบาย แต่ขณะนี้ระบบประมวลผลคำตอบไม่ได้ "
            "กรุณาดูเอกสารโดยตรง: " + ", ".join(sources)
        )

    _ensure_conversation(db, payload)
    try:
        conv = db.get(Conversation, payload.conversation_id)
        if conv:
            conv.latest_intent = "policy_question"
            conv.updated_at = datetime.utcnow()
        db.commit()
    except Exception:
        db.rollback()

    return ChatResponse(
        workflow_name="workflow_policy_rag",
        intent="policy_question",
        response_text=response_text,
        active_shipments=[],
        state_snapshot={
            "rag_results_count": len(rag_results),
            "policy_titles": [r.get("policy_title") for r in rag_results if r.get("policy_title")],
        },
    )


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


_GREETING_TOKENS = {
    "สวัสดี", "หวัดดี", "ดีครับ", "ดีค่ะ", "เฮ้", "เฮ้โล",
    "hello", "hi", "hey",
}


def _is_pure_greeting(message: str) -> bool:
    """True if message is a greeting with no substantive question."""
    stripped = message.strip()
    if len(stripped) > 60:
        return False
    lower = stripped.lower()
    return any(lower.startswith(kw) or lower == kw for kw in _GREETING_TOKENS)


def handle_chat(db: Session, payload: ChatRequest) -> ChatResponse:
    from app.agents.inter_agent import MessageBus, MessageType, AgentMessage

    # Ensure conversation exists BEFORE the (slow) LLM call so the DB
    # connection is not left idle during inference.
    _ensure_conversation(db, payload)

    # ── Fast path: pure greeting → skip workflow entirely ─────────────────────
    if _is_pure_greeting(payload.message):
        try:
            conv = db.get(Conversation, payload.conversation_id)
            if conv:
                conv.updated_at = datetime.utcnow()
                conv.latest_intent = "general_inquiry"
                db.commit()
        except Exception:
            db.rollback()
        return ChatResponse(
            workflow_name="greeting",
            intent="general_inquiry",
            response_text="สวัสดีค่ะ มีอะไรให้ช่วยได้บ้างคะ?",
            active_shipments=[],
            state_snapshot={},
        )

    # ── LLM Agentic Router ────────────────────────────────────────────────────
    # The LLM classifies the customer message into a workflow intent.
    # Falls back to keyword matching automatically if Ollama is unavailable.
    intent = classify_intent(payload.message)

    # Validate intent value
    _VALID_INTENTS = {"track_shipment", "refund_request", "policy_question", "general_inquiry"}
    if intent not in _VALID_INTENTS:
        intent = "general_inquiry"

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
        response = handle_refund_chat(db, payload)
    elif intent == "policy_question":
        # Policy-only RAG answer — do NOT load customer order data, do NOT use
        # general LLM knowledge. If no policy chunks match, say so explicitly.
        response = _handle_policy_chat(db, payload)
    else:
        # Pass pre-classified intent to avoid redundant LLM call
        response = handle_tracking_chat(db, payload, pre_classified_intent=intent)

    # ── Update conversation metadata (messages saved by observability layer) ─
    try:
        conv = db.get(Conversation, payload.conversation_id)
        if conv:
            conv.updated_at = datetime.utcnow()
            conv.latest_intent = intent
            db.commit()
    except Exception:
        db.rollback()

    return response
