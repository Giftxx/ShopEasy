import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat import handle_chat

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=ChatResponse)
def create_chat_response(payload: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    try:
        return handle_chat(db, payload)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Chat processing failed for %s: %s", payload.customer_id, exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="ขออภัยค่ะ ระบบไม่สามารถประมวลผลข้อความได้ในขณะนี้ กรุณาลองใหม่อีกครั้ง",
        )
