from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.agents.tools.refund import detect_refund_intent
from app.agents.tools.tracking import detect_tracking_intent
from app.db.models import Conversation
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.workflow_01_tracking import handle_tracking_chat
from app.services.workflow_02_refund import handle_refund_chat


def _ensure_conversation(db: Session, payload: ChatRequest) -> None:
    """Auto-create conversation if it doesn't exist yet."""
    conversation = db.get(Conversation, payload.conversation_id)
    if conversation is None:
        db.add(Conversation(
            id=payload.conversation_id,
            customer_id=payload.customer_id,
            channel="web_chat",
            status="open",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        ))
        db.flush()


def handle_chat(db: Session, payload: ChatRequest) -> ChatResponse:
    _ensure_conversation(db, payload)

    refund_intent = detect_refund_intent(payload.message)
    if refund_intent == "refund_request":
        return handle_refund_chat(db, payload)

    tracking_intent = detect_tracking_intent(payload.message)
    if tracking_intent == "track_shipment":
        return handle_tracking_chat(db, payload)

    # general_inquiry fallback → tracking workflow (shows order context)
    return handle_tracking_chat(db, payload)
