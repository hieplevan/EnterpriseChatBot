from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query, Depends
from sqlalchemy.orm import Session

from backend.app.schemas.document import (
    DocumentListResponse,
    DocumentInfo,
    DocumentHighlightResponse,
    DocumentUploadResponse,
)
from backend.app.services.document_service import EnhancedDocumentService
from backend.app.services.hybrid_retriever import HybridRetrieverService
from backend.app.config import DOCUMENTS_DIR
from backend.app.api.chat import get_retriever
from backend.app.db.session import get_db
from backend.app.db.models import DocumentRecord, AuditLog

router = APIRouter(prefix="/api/documents", tags=["Documents Management"])

_doc_service = EnhancedDocumentService()


@router.get("", response_model=DocumentListResponse)
def list_documents(
    retriever: HybridRetrieverService = Depends(get_retriever),
    db: Session = Depends(get_db),
):
    """Lay danh sach cac tai lieu da duoc lap chi muc trong he thong kem metadata phan quyen."""
    info = retriever.get_indexed_documents_info()
    doc_items = []
    
    # Lay metadata bo sung tu database neu co
    db_records = {r.filename: r for r in db.query(DocumentRecord).all()}

    for f in info.get("files", []):
        file_path = DOCUMENTS_DIR / f["name"]
        size = file_path.stat().st_size if file_path.exists() else 0
        total_lines = 0
        if file_path.exists():
            try:
                total_lines = len(file_path.read_text(encoding="utf-8", errors="replace").splitlines())
            except Exception:
                pass

        db_rec = db_records.get(f["name"])
        dept = db_rec.department if db_rec else f.get("department", "GENERAL")
        classification = db_rec.classification if db_rec else f.get("classification", "INTERNAL")
        uploaded_by = db_rec.uploaded_by if db_rec else "admin"

        doc_items.append(
            DocumentInfo(
                name=f["name"],
                size_bytes=size,
                chunks=f["chunks"],
                lines=total_lines,
                department=dept,
                classification=classification,
                uploaded_by=uploaded_by,
            )
        )

    return DocumentListResponse(
        total_documents=len(doc_items),
        total_chunks=info.get("total_chunks", 0),
        documents=doc_items,
    )


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    department: str = Form("GENERAL"),
    classification: str = Form("INTERNAL"),
    uploaded_by: str = Form("admin"),
    retriever: HybridRetrieverService = Depends(get_retriever),
    db: Session = Depends(get_db),
):
    """
    Tai len tai lieu moi (TXT, MD, PDF), tu dong trich xuat toa do bôi đen,
    gan nhan phan quyen RBAC, lap chi muc tuc thi vao Vector DB va BM25.
    """
    try:
        file_path = DOCUMENTS_DIR / file.filename
        
        # Luu file len dia
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        # Xoa du lieu cu cua file nay neu da ton tai truoc do trong index
        retriever.delete_document_by_source(file.filename)

        # Phan doan va trich xuat span toa do kem nhan quyen
        chunks = _doc_service.load_and_split_with_spans(
            file_path,
            department=department,
            classification=classification,
        )
        added_count = retriever.add_documents(chunks)

        # Luu / Cap nhat thong tin vao CSDL
        existing_rec = db.query(DocumentRecord).filter(DocumentRecord.filename == file.filename).first()
        if existing_rec:
            existing_rec.chunk_count = added_count
            existing_rec.department = department
            existing_rec.classification = classification
            existing_rec.size_bytes = len(content)
            existing_rec.uploaded_by = uploaded_by
        else:
            new_rec = DocumentRecord(
                filename=file.filename,
                file_type=file_path.suffix.lower().replace(".", ""),
                size_bytes=len(content),
                chunk_count=added_count,
                department=department,
                classification=classification,
                uploaded_by=uploaded_by,
            )
            db.add(new_rec)

        # Ghi nhat ky kiem toan (Audit Log)
        audit = AuditLog(
            username=uploaded_by,
            role="ADMIN",
            action="UPLOAD_DOCUMENT",
            query_text=f"Uploaded {file.filename} ({added_count} chunks, {classification}, {department})",
        )
        db.add(audit)
        db.commit()

        return DocumentUploadResponse(
            filename=file.filename,
            status="indexed_successfully",
            chunks_indexed=added_count,
            department=department,
            classification=classification,
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Loi khi tai len va lap chi muc: {str(e)}")


@router.get("/{name}/highlight", response_model=DocumentHighlightResponse)
def get_document_highlight(
    name: str,
    char_start: Optional[int] = Query(None, description="Vi tri ky tu bat dau"),
    char_end: Optional[int] = Query(None, description="Vi tri ky tu ket thuc"),
    line_start: Optional[int] = Query(None, description="Dong bat dau"),
    line_end: Optional[int] = Query(None, description="Dong ket thuc"),
):
    """
    Boi den (Highlight) truc tiep doan van ban duoc trich dan trong file mau.
    Tra ve HTML kem so dong de render len Document Viewer ben phia Frontend.
    """
    try:
        highlight_data = _doc_service.generate_highlighted_document(
            file_name=name,
            char_start=char_start,
            char_end=char_end,
            line_start=line_start,
            line_end=line_end,
        )
        return DocumentHighlightResponse(**highlight_data)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Khong tim thay tep: {name}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest-samples")
def ingest_all_samples(
    retriever: HybridRetrieverService = Depends(get_retriever),
    db: Session = Depends(get_db),
):
    """Nap toan bo cac tep mau trong data/documents vao Vector DB va BM25 kem phan quyen."""
    sample_files = [
        f for f in DOCUMENTS_DIR.glob("*")
        if f.is_file() and f.suffix.lower() in [".pdf", ".txt", ".md"]
    ]

    total_chunks = 0
    results = []

    for file_path in sample_files:
        try:
            chunks = _doc_service.load_and_split_with_spans(file_path)
            added = retriever.add_documents(chunks)
            total_chunks += added

            # Dong bo database
            dept = chunks[0].metadata.get("department", "GENERAL") if chunks else "GENERAL"
            classification = chunks[0].metadata.get("classification", "INTERNAL") if chunks else "INTERNAL"

            existing_rec = db.query(DocumentRecord).filter(DocumentRecord.filename == file_path.name).first()
            if existing_rec:
                existing_rec.chunk_count = added
                existing_rec.department = dept
                existing_rec.classification = classification
            else:
                db.add(DocumentRecord(
                    filename=file_path.name,
                    file_type=file_path.suffix.lower().replace(".", ""),
                    size_bytes=file_path.stat().st_size,
                    chunk_count=added,
                    department=dept,
                    classification=classification,
                    uploaded_by="system",
                ))

            results.append({"file": file_path.name, "chunks": added, "status": "success"})
        except Exception as e:
            results.append({"file": file_path.name, "chunks": 0, "status": f"error: {e}"})

    db.commit()

    return {
        "total_files": len(sample_files),
        "total_chunks_indexed": total_chunks,
        "details": results,
    }


@router.delete("/{name}")
def delete_document(
    name: str,
    retriever: HybridRetrieverService = Depends(get_retriever),
    db: Session = Depends(get_db),
):
    """Xoa mot tep khoi chi muc tri thuc va database."""
    success = retriever.delete_document_by_source(name)
    if not success:
        raise HTTPException(status_code=500, detail="Loi khi xoa tai lieu khoi chi muc.")

    # Xoa record database
    db.query(DocumentRecord).filter(DocumentRecord.filename == name).delete()
    
    # Ghi audit log
    db.add(AuditLog(
        username="admin",
        role="ADMIN",
        action="DELETE_DOCUMENT",
        query_text=f"Deleted document {name}",
    ))
    db.commit()

    # Xoa file dia neu co
    file_path = DOCUMENTS_DIR / name
    if file_path.exists():
        try:
            file_path.unlink()
        except Exception:
            pass

    return {"message": f"Da xoa thanh cong: {name}"}
