import html
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.app.config import CHUNK_SIZE, CHUNK_OVERLAP, DOCUMENTS_DIR


class EnhancedDocumentService:
    def __init__(self, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
        )

    def read_file_raw(self, file_path: Path) -> str:
        """Doc noi dung tho cua file (ho tro MD, TXT, PDF)."""
        suffix = file_path.suffix.lower()
        if suffix in [".txt", ".md", ".json", ".csv"]:
            return file_path.read_text(encoding="utf-8", errors="replace")
        elif suffix == ".pdf":
            loader = PyPDFLoader(str(file_path))
            pages = loader.load()
            return "\n\n".join([p.page_content for p in pages])
        else:
            return file_path.read_text(encoding="utf-8", errors="replace")

    def load_and_split_with_spans(
        self,
        file_path: Path,
        department: Optional[str] = None,
        classification: Optional[str] = None,
    ) -> List[Document]:
        """
        Doc va cat nho tai lieu dong thoi xac dinh toa do chinh xac 100%:
        - char_start, char_end: vi tri ky tu trong file goc
        - line_start, line_end: vi tri dong trong file goc (1-indexed)
        - department, classification: phan quyen RBAC doanh nghiep
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File khong ton tai: {path}")

        # Tu dong suy luan neu khong chi dinh
        fname_lower = path.name.lower()
        if not department:
            if any(k in fname_lower for k in ["luat", "nghi_dinh", "phap"]):
                department = "LEGAL"
            elif any(k in fname_lower for k in ["nhan_su", "quy_che", "lao_dong"]):
                department = "HR"
            elif any(k in fname_lower for k in ["tai_chinh", "ke_toan", "chi_tieu"]):
                department = "FINANCE"
            else:
                department = "GENERAL"

        if not classification:
            if any(k in fname_lower for k in ["bo_luat", "luat_", "nghi_dinh"]):
                classification = "PUBLIC"
            elif any(k in fname_lower for k in ["mat", "confidential", "bi_mat"]):
                classification = "CONFIDENTIAL"
            else:
                classification = "INTERNAL"

        full_text = self.read_file_raw(path)
        raw_chunks = self.splitter.split_text(full_text)

        documents: List[Document] = []
        search_cursor = 0

        for idx, chunk_text in enumerate(raw_chunks):
            chunk_clean = chunk_text.strip()
            if not chunk_clean:
                continue

            # Tim toa do char_start va char_end trong van ban goc
            char_pos = full_text.find(chunk_clean[:40], search_cursor)
            if char_pos == -1:
                # Neu khong tim thay do cat tu, tim tu dau
                char_pos = full_text.find(chunk_clean[:40])

            if char_pos != -1:
                char_start = char_pos
                char_end = char_pos + len(chunk_clean)
                search_cursor = max(0, char_start + 1)
            else:
                char_start = 0
                char_end = len(chunk_clean)

            # Tinh toan dong bat dau va dong ket thuc chinh xac
            line_start = full_text[:char_start].count("\n") + 1
            line_end = full_text[:char_end].count("\n") + 1

            meta = {
                "source": path.name,
                "file_path": str(path),
                "chunk_index": idx,
                "char_start": char_start,
                "char_end": char_end,
                "line_start": line_start,
                "line_end": line_end,
                "department": department,
                "classification": classification,
            }

            documents.append(Document(page_content=chunk_clean, metadata=meta))

        return documents


    def generate_highlighted_document(
        self,
        file_name: str,
        char_start: Optional[int] = None,
        char_end: Optional[int] = None,
        line_start: Optional[int] = None,
        line_end: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Boi den (Highlight) truc tiep doan van ban duoc trich dan trong file mau.
        Tra ve HTML da danh so dong va boc the <mark> tai dung vi tri.
        """
        file_path = DOCUMENTS_DIR / file_name
        if not file_path.exists():
            raise FileNotFoundError(f"Khong tim thay file: {file_name}")

        full_text = self.read_file_raw(file_path)
        lines = full_text.splitlines()
        total_lines = len(lines)
        total_chars = len(full_text)

        # Xac dinh toa do char neu chi co line
        if (char_start is None or char_end is None) and line_start is not None:
            l_start = max(1, line_start)
            l_end = min(total_lines, line_end if line_end is not None else line_start)
            char_start = sum(len(lines[i]) + 1 for i in range(l_start - 1))
            char_end = sum(len(lines[i]) + 1 for i in range(l_end))

        # Canh chinh gioi han char
        c_start = max(0, char_start if char_start is not None else 0)
        c_end = min(total_chars, char_end if char_end is not None else total_chars)

        snippet = full_text[c_start:c_end]

        # Tao giao dien HTML boi den truc tiep co danh so dong (Code/Document Viewer)
        highlighted_lines = []
        current_offset = 0

        for line_num, line in enumerate(lines, 1):
            line_len = len(line) + 1  # tinh ca ky tu newline
            line_start_off = current_offset
            line_end_off = current_offset + line_len

            # Kiem tra dong nay co giao voi doan can boi den khong
            if line_end_off > c_start and line_start_off < c_end:
                # Tinh phan can highlight trong dong nay
                h_start = max(0, c_start - line_start_off)
                h_end = min(len(line), c_end - line_start_off)

                before = html.escape(line[:h_start])
                marked = html.escape(line[h_start:h_end])
                after = html.escape(line[h_end:])

                styled_line = f'{before}<mark class="doc-highlight-span" id="highlight-target">{marked}</mark>{after}'
                line_class = "line-highlighted"
            else:
                styled_line = html.escape(line)
                line_class = "line-normal"

            highlighted_lines.append(
                f'<div class="doc-line {line_class}"><span class="line-num">{line_num:>4}</span> <span class="line-text">{styled_line}</span></div>'
            )
            current_offset = line_end_off

        rendered_html = (
            f'<div class="document-viewer-container">'
            f'{"".join(highlighted_lines)}'
            f'</div>'
        )

        return {
            "file_name": file_name,
            "total_lines": total_lines,
            "total_chars": total_chars,
            "line_start": line_start or (full_text[:c_start].count("\n") + 1),
            "line_end": line_end or (full_text[:c_end].count("\n") + 1),
            "char_start": c_start,
            "char_end": c_end,
            "snippet": snippet,
            "highlighted_html": rendered_html,
        }
