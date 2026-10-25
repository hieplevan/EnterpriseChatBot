from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.db.session import get_db
from backend.app.db.models import AuditLog, Feedback, Message, User, DocumentRecord
from backend.app.schemas.query import FeedbackRequest, FeedbackResponse

router = APIRouter(prefix="/api/audit", tags=["Audit & Observability"])


@router.get("/metrics")
def get_audit_metrics(db: Session = Depends(get_db)):
    """Tra ve cac chi so quan tri RAG Observability tong the."""
    total_queries = db.query(AuditLog).filter(AuditLog.action == "QUERY").count()
    
    # Latency trung binh
    avg_latency = db.query(func.avg(AuditLog.latency_ms)).filter(AuditLog.action == "QUERY").scalar() or 0.0
    
    # So luong vi pham PII
    pii_violations = db.query(AuditLog).filter(
        AuditLog.pii_detected != None,
        AuditLog.pii_detected != ""
    ).count()

    # Thong ke danh gia nguoi dung
    positive_feedback = db.query(Feedback).filter(Feedback.rating > 0).count()
    negative_feedback = db.query(Feedback).filter(Feedback.rating < 0).count()

    # Tong so tai lieu da lap chi muc
    total_docs = db.query(DocumentRecord).count()

    return {
        "total_queries": total_queries,
        "avg_latency_ms": round(float(avg_latency), 2),
        "pii_violations_prevented": pii_violations,
        "positive_feedbacks": positive_feedback,
        "negative_feedbacks": negative_feedback,
        "total_documents": total_docs,
    }


@router.get("/logs")
def get_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    action: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Truy van nhat ky kiem toan he thong (Audit Trail)."""
    q = db.query(AuditLog)
    if action:
        q = q.filter(AuditLog.action == action)
    if role:
        q = q.filter(AuditLog.role == role)

    logs = q.order_by(AuditLog.created_at.desc()).limit(limit).all()

    return [
        {
            "id": log.id,
            "username": log.username or "anonymous",
            "role": log.role or "EMPLOYEE",
            "action": log.action,
            "query_text": log.query_text,
            "pii_detected": log.pii_detected,
            "latency_ms": round(log.latency_ms, 2) if log.latency_ms else 0.0,
            "faithfulness_score": log.faithfulness_score,
            "created_at": log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else "",
        }
        for log in logs
    ]


@router.post("/feedback", response_model=FeedbackResponse)
def submit_feedback(req: FeedbackRequest, db: Session = Depends(get_db)):
    """Ghi nhan danh gia chat luong phan hoi (Thumbs Up / Thumbs Down) tu nguoi dung."""
    fb = Feedback(
        message_id=req.message_id,
        user_id=req.user_id,
        rating=req.rating,
        comment=req.comment,
    )
    db.add(fb)
    db.commit()
    return FeedbackResponse(status="success", message="Cam on ban da gui danh gia chat luong.")


@router.get("/users")
def list_enterprise_users(db: Session = Depends(get_db)):
    """Lay danh sach cac tai khoan doanh nghiep da cau hinh san trong he thong."""
    users = db.query(User).filter(User.is_active == True).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "full_name": u.full_name,
            "role": u.role,
            "department": u.department,
        }
        for u in users
    ]
