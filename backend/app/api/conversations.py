import uuid
import json
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.db.session import get_db
from backend.app.db.models import Conversation, Message, User

router = APIRouter(prefix="/api/conversations", tags=["Conversations Persistence"])


class CreateConversationRequest(BaseModel):
    user_id: int = 1
    title: Optional[str] = "Phien tra cuu moi"


@router.get("")
def list_conversations(user_id: int = 1, db: Session = Depends(get_db)):
    """Lay danh sach cac phien hoi thoai cua nguoi dung."""
    convs = (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )
    return [
        {
            "id": c.id,
            "title": c.title,
            "created_at": c.created_at.strftime("%Y-%m-%d %H:%M:%S") if c.created_at else "",
            "updated_at": c.updated_at.strftime("%Y-%m-%d %H:%M:%S") if c.updated_at else "",
            "message_count": len(c.messages),
        }
        for c in convs
    ]


@router.post("")
def create_conversation(req: CreateConversationRequest, db: Session = Depends(get_db)):
    """Tao mot phien hoi thoai moi."""
    conv_id = str(uuid.uuid4())
    conv = Conversation(
        id=conv_id,
        user_id=req.user_id,
        title=req.title or "Phien tra cuu moi",
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return {"id": conv.id, "title": conv.title}


@router.get("/{conv_id}/messages")
def get_conversation_messages(conv_id: str, db: Session = Depends(get_db)):
    """Lay lich su tin nhan cua phien hoi thoai kem toa do trich dan."""
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Khong tim thay phien hoi thoai")

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conv_id)
        .order_by(Message.created_at.asc())
        .all()
    )

    results = []
    for m in messages:
        cits = json.loads(m.citations_json) if m.citations_json else []
        metrics = json.loads(m.metrics_json) if m.metrics_json else {}
        results.append({
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "citations": cits,
            "metrics": metrics,
            "created_at": m.created_at.strftime("%Y-%m-%d %H:%M:%S") if m.created_at else "",
        })

    return {"conversation_id": conv_id, "title": conv.title, "messages": results}


@router.delete("/{conv_id}")
def delete_conversation(conv_id: str, db: Session = Depends(get_db)):
    """Xoa phien hoi thoai."""
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Khong tim thay phien hoi thoai")
    db.delete(conv)
    db.commit()
    return {"message": "Da xoa phien hoi thoai thanh cong"}
