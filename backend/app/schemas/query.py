from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class CitationSpan(BaseModel):
    source: str = Field(description="Ten file goc chua doan trich dan")
    line_start: int = Field(default=1, description="Dong bat dau trong van ban goc")
    line_end: int = Field(default=1, description="Dong ket thuc trong van ban goc")
    char_start: int = Field(default=0, description="Vi tri ky tu bat dau trong van ban goc")
    char_end: int = Field(default=0, description="Vi tri ky tu ket thuc trong van ban goc")
    content: str = Field(description="Noi dung phan doan trich dan")
    score: float = Field(default=0.0, description="Diem tuong quan relevance/reranking")


class ChatMessage(BaseModel):
    role: str
    content: str


class QueryRequest(BaseModel):
    query: str
    use_rag: bool = True
    use_hybrid: bool = True
    use_rerank: bool = True
    top_k: int = 4
    temperature: float = 0.3
    model: Optional[str] = None
    chat_history: List[ChatMessage] = []
    user_id: Optional[int] = 1
    user_role: Optional[str] = "EMPLOYEE"
    conversation_id: Optional[str] = None
    mask_pii: bool = True


class QueryResponse(BaseModel):
    answer: str
    citations: List[CitationSpan] = []
    retrieval_strategy: str = "hybrid_rrf"
    retrieval_time_ms: float = 0.0
    generation_time_ms: float = 0.0
    total_time_ms: float = 0.0
    conversation_id: Optional[str] = None
    message_id: Optional[int] = None
    pii_detected: List[str] = []
    security_status: str = "PASSED"


class FeedbackRequest(BaseModel):
    message_id: int
    rating: int  # 1 for Thumbs Up, -1 for Thumbs Down
    comment: Optional[str] = None
    user_id: Optional[int] = 1


class FeedbackResponse(BaseModel):
    status: str = "success"
    message: str = "Feedback recorded"

