# backend/app/api/routes/chat.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.chat_service import chat_service
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    response: str
    intent: str


@router.post("/message", response_model=ChatResponse)
def send_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """إرسال رسالة للـ AI Agent"""
    try:
        result = chat_service.process_message(
            patient_id=current_user.id,
            patient_name=current_user.full_name,
            message=request.message,
            session_id=request.session_id,
        )
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"حصل خطأ: {str(e)}")


@router.get("/history/{session_id}")
def get_chat_history(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """جلب تاريخ المحادثة"""
    from app.core.database import SessionLocal
    from app.models.chat import ChatMessage

    db = SessionLocal()
    try:
        messages = db.query(ChatMessage).filter(
            ChatMessage.patient_id == current_user.id,
            ChatMessage.session_id == session_id,
        ).order_by(ChatMessage.created_at).all()

        return [
            {
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at,
            }
            for msg in messages
        ]
    finally:
        db.close()