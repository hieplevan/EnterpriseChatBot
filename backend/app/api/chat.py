import json
import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.app.schemas.query import QueryRequest, QueryResponse
from backend.app.services.hybrid_retriever import HybridRetrieverService
from backend.app.services.reranker_service import RerankerService
from backend.app.services.rag_engine import AdvancedRAGEngine
from backend.app.services.guardrails_service import EnterpriseGuardrailsService
from backend.app.config import OLLAMA_BASE_URL, OLLAMA_DEFAULT_MODEL
from backend.app.db.session import get_db
from backend.app.db.models import Conversation, Message, AuditLog, User

router = APIRouter(prefix="/api/chat", tags=["Chat & RAG"])

# Singleton services
_retriever = None
_reranker = None
_guardrails = EnterpriseGuardrailsService()


def get_retriever():
    global _retriever
    if _retriever is None:
        _retriever = HybridRetrieverService()
    return _retriever


def get_reranker():
    global _reranker
    if _reranker is None:
        _reranker = RerankerService()
    return _reranker


@router.post("", response_model=QueryResponse)
def chat_query(
    request: QueryRequest,
    retriever: HybridRetrieverService = Depends(get_retriever),
    reranker: RerankerService = Depends(get_reranker),
    db: Session = Depends(get_db),
):
    """Xu ly cau hoi, kiem tra an toan guardrails, phan quyen RBAC va luu tru phien hoi thoai."""
    try:
        # 1. Kiem tra Prompt Injection
        is_safe, reason = _guardrails.check_prompt_safety(request.query)
        if not is_safe:
            # Ghi nhat ky canh bao bao mat
            audit = AuditLog(
                user_id=request.user_id,
                username=f"user_{request.user_id}",
                role=request.user_role,
                action="PROMPT_INJECTION_BLOCKED",
                query_text=request.query,
                pii_detected="INJECTION_ATTEMPT",
            )
            db.add(audit)
            db.commit()

            return QueryResponse(
                answer=f"[CANH BAO AN TOAN DOANH NGHIEP] {reason}",
                citations=[],
                retrieval_strategy="blocked",
                security_status="BLOCKED",
            )

        # 2. Phat hien va che PII neu duoc yeu cau
        processed_query = request.query
        pii_detected_types = []
        if request.mask_pii:
            processed_query, pii_detected_types = _guardrails.sanitize_and_mask_pii(request.query)

        # 3. Khoi tao RAG Engine va sinh cau tra loi theo Role
        engine = AdvancedRAGEngine(
            retriever_service=retriever,
            reranker_service=reranker,
            model_name=request.model or OLLAMA_DEFAULT_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=request.temperature,
            top_k=request.top_k,
        )

        history_dicts = [{"role": m.role, "content": m.content} for m in request.chat_history]

        answer, citations, metrics = engine.generate_response(
            query=processed_query,
            chat_history=history_dicts,
            use_rag=request.use_rag,
            use_hybrid=request.use_hybrid,
            use_rerank=request.use_rerank,
            user_role=request.user_role or "EMPLOYEE",
        )

        # 4. Luu tru hoi thoai vao CSDL Doanh nghiep (Persistence)
        conv_id = request.conversation_id
        if not conv_id:
            conv_id = str(uuid.uuid4())
            title_snippet = request.query[:40] + ("..." if len(request.query) > 40 else "")
            new_conv = Conversation(
                id=conv_id,
                user_id=request.user_id or 1,
                title=title_snippet,
            )
            db.add(new_conv)
            db.commit()

        # Luu message user
        user_msg = Message(
            conversation_id=conv_id,
            role="user",
            content=request.query,
        )
        db.add(user_msg)

        # Luu message assistant
        cits_dict = [c.model_dump() for c in citations]
        asst_msg = Message(
            conversation_id=conv_id,
            role="assistant",
            content=answer,
            citations_json=json.dumps(cits_dict, ensure_ascii=False),
            metrics_json=json.dumps(metrics),
        )
        db.add(asst_msg)
        db.commit()
        db.refresh(asst_msg)

        # 5. Ghi Nhat ky Kiem toan (Audit Log)
        audit_entry = AuditLog(
            user_id=request.user_id,
            username=f"user_{request.user_id}",
            role=request.user_role,
            action="QUERY",
            query_text=processed_query,
            pii_detected=",".join(pii_detected_types) if pii_detected_types else None,
            latency_ms=metrics.get("total_ms", 0.0),
        )
        db.add(audit_entry)
        db.commit()

        return QueryResponse(
            answer=answer,
            citations=citations,
            retrieval_strategy="hybrid_rrf_rerank" if request.use_rerank else "hybrid_rrf",
            retrieval_time_ms=metrics["retrieval_ms"],
            generation_time_ms=metrics["generation_ms"],
            total_time_ms=metrics["total_ms"],
            conversation_id=conv_id,
            message_id=asst_msg.id,
            pii_detected=pii_detected_types,
            security_status="PASSED",
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
def chat_stream(
    request: QueryRequest,
    retriever: HybridRetrieverService = Depends(get_retriever),
    reranker: RerankerService = Depends(get_reranker),
):
    """Streaming tra loi theo thoi gian thuc dang Server-Sent Events (SSE)."""
    try:
        # PII & Injection safety
        is_safe, reason = _guardrails.check_prompt_safety(request.query)
        if not is_safe:
            def err_stream():
                yield f"event: token\ndata: {json.dumps({'token': f'[CANH BAO AN TOAN] {reason}'})}\n\n"
                yield "event: done\ndata: {}\n\n"
            return StreamingResponse(err_stream(), media_type="text/event-stream")

        processed_query = request.query
        if request.mask_pii:
            processed_query, _ = _guardrails.sanitize_and_mask_pii(request.query)

        engine = AdvancedRAGEngine(
            retriever_service=retriever,
            reranker_service=reranker,
            model_name=request.model or OLLAMA_DEFAULT_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=request.temperature,
            top_k=request.top_k,
        )

        history_dicts = [{"role": m.role, "content": m.content} for m in request.chat_history]

        stream_gen, citations = engine.generate_response_stream(
            query=processed_query,
            chat_history=history_dicts,
            use_rag=request.use_rag,
            use_hybrid=request.use_hybrid,
            use_rerank=request.use_rerank,
            user_role=request.user_role or "EMPLOYEE",
        )

        def event_stream():
            # Gui truoc thong tin citations kem toa do
            cits_json = [c.model_dump() for c in citations]
            yield f"event: citations\ndata: {json.dumps(cits_json, ensure_ascii=False)}\n\n"

            # Stream tung token
            for chunk in stream_gen:
                if chunk:
                    data_payload = json.dumps({"token": chunk}, ensure_ascii=False)
                    yield f"event: token\ndata: {data_payload}\n\n"

            yield "event: done\ndata: {}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
