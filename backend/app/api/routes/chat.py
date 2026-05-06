from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat import handle_chat


router = APIRouter()


@router.post("", response_model=ChatResponse)
def create_chat_response(payload: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    return handle_chat(db, payload)
