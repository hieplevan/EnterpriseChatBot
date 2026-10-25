from typing import List, Optional
from pydantic import BaseModel, Field


class DocumentInfo(BaseModel):
    name: str
    size_bytes: int
    chunks: int
    lines: int
    department: str = "GENERAL"
    classification: str = "INTERNAL"
    uploaded_by: str = "admin"


class DocumentListResponse(BaseModel):
    total_documents: int
    total_chunks: int
    documents: List[DocumentInfo]


class DocumentUploadResponse(BaseModel):
    filename: str
    status: str
    chunks_indexed: int
    department: str
    classification: str



class DocumentHighlightRequest(BaseModel):
    char_start: Optional[int] = None
    char_end: Optional[int] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None


class DocumentHighlightResponse(BaseModel):
    file_name: str
    total_lines: int
    total_chars: int
    line_start: int
    line_end: int
    char_start: int
    char_end: int
    snippet: str
    highlighted_html: str
