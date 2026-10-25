from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.chat import router as chat_router
from backend.app.api.documents import router as documents_router
from backend.app.api.evaluation import router as eval_router
from backend.app.api.conversations import router as conversations_router
from backend.app.api.audit import router as audit_router
from backend.app.db.init_db import init_database

app = FastAPI(
    title="Enterprise RAG Engine API",
    description="Enterprise-Grade RAG Backend with RBAC Security, Database Persistence, Audit Trail, Guardrails PII Masking, and Exact Grounding Spans",
    version="2.1.0",
)

# Khoi tao database va seed du lieu khi khoi dong
init_database()

# Cau hinh CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dang ky cac routers
app.include_router(chat_router)
app.include_router(documents_router)
app.include_router(conversations_router)
app.include_router(audit_router)
app.include_router(eval_router)


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "Enterprise RAG Engine",
        "version": "2.1.0",
        "features": [
            "Hybrid Search (BM25 + Dense ChromaDB)",
            "Reciprocal Rank Fusion (RRF)",
            "Cross-Encoder Re-Ranking",
            "Exact Document Span Grounding & Highlighting",
            "Role-Based Access Control (RBAC)",
            "Enterprise Database Persistence (SQLite/PostgreSQL)",
            "Guardrails (PII Masking & Prompt Injection Defense)",
            "Observability & Audit Trail Logging",
            "RAG Triad Quantitative Evaluation",
        ],
    }



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
