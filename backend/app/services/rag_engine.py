import time
from typing import List, Dict, Any, Generator, Tuple, Optional
from langchain_core.documents import Document
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from backend.app.config import OLLAMA_BASE_URL, OLLAMA_DEFAULT_MODEL
from backend.app.services.hybrid_retriever import HybridRetrieverService
from backend.app.services.reranker_service import RerankerService
from backend.app.schemas.query import CitationSpan


class AdvancedRAGEngine:
    def __init__(
        self,
        retriever_service: HybridRetrieverService,
        reranker_service: Optional[RerankerService] = None,
        model_name: str = OLLAMA_DEFAULT_MODEL,
        base_url: str = OLLAMA_BASE_URL,
        temperature: float = 0.3,
        top_k: int = 4,
    ):
        self.retriever = retriever_service
        self.reranker = reranker_service or RerankerService()
        self.model_name = model_name
        self.base_url = base_url
        self.temperature = temperature
        self.top_k = top_k
        self._init_llm()

    def _init_llm(self):
        self.llm = ChatOllama(
            base_url=self.base_url,
            model=self.model_name,
            temperature=self.temperature,
        )

    def retrieve_and_rank(
        self, query: str, use_hybrid: bool = True, use_rerank: bool = True, user_role: str = "EMPLOYEE"
    ) -> List[Tuple[Document, float]]:
        """Truy xuat da tang: Dense + BM25 ket hop Re-ranking va phan quyen RBAC."""
        if use_hybrid:
            candidates = self.retriever.hybrid_search_rrf(query, top_k=self.top_k * 3, user_role=user_role)
        else:
            candidates = self.retriever.dense_search(query, k=self.top_k * 2, user_role=user_role)

        if use_rerank and candidates:
            final_ranked = self.reranker.rerank(query, candidates, top_k=self.top_k)
        else:
            final_ranked = candidates[: self.top_k]

        return final_ranked


    def format_context(self, ranked_docs: List[Tuple[Document, float]]) -> str:
        """Dinh dang ngu canh ro rang kem so hieu tham chieu."""
        if not ranked_docs:
            return "Khong tim thay tai lieu lien quan trong he thong."

        parts = []
        for idx, (doc, score) in enumerate(ranked_docs, 1):
            source = doc.metadata.get("source", "Tai lieu")
            line_s = doc.metadata.get("line_start", 1)
            line_e = doc.metadata.get("line_end", 1)
            parts.append(
                f"[Tai lieu tham chieu #{idx} | Nguon: {source} (Dong {line_s}-{line_e}) | Diem: {score:.3f}]\n"
                f"{doc.page_content.strip()}"
            )
        return "\n\n---\n\n".join(parts)

    def extract_citation_spans(
        self, ranked_docs: List[Tuple[Document, float]]
    ) -> List[CitationSpan]:
        """Trich xuat danh sach toa do trich dan chinh xac 100% vao schema."""
        spans = []
        for doc, score in ranked_docs:
            meta = doc.metadata
            span = CitationSpan(
                source=meta.get("source", "Tai lieu"),
                line_start=meta.get("line_start", 1),
                line_end=meta.get("line_end", 1),
                char_start=meta.get("char_start", 0),
                char_end=meta.get("char_end", len(doc.page_content)),
                content=doc.page_content.strip(),
                score=score,
            )
            spans.append(span)
        return spans

    def generate_response(
        self,
        query: str,
        chat_history: List[Dict[str, str]] = None,
        use_rag: bool = True,
        use_hybrid: bool = True,
        use_rerank: bool = True,
        user_role: str = "EMPLOYEE",
    ) -> Tuple[str, List[CitationSpan], Dict[str, float]]:
        """Sinh cau tra loi non-streaming cho REST API co ho tro phan quyen RBAC."""
        t_start = time.time()

        citations: List[CitationSpan] = []
        context_str = ""

        if use_rag:
            ranked_docs = self.retrieve_and_rank(
                query, use_hybrid=use_hybrid, use_rerank=use_rerank, user_role=user_role
            )
            citations = self.extract_citation_spans(ranked_docs)
            context_str = self.format_context(ranked_docs)

        t_retrieval = time.time()

        system_prompt = (
            "Ban la he thong Tro ly Tra cuu Tri thuc Chuyen nghiep (Enterprise RAG Assistant).\n"
            "Nhiem vu cua ban: Tra loi cau hoi dua tren NGU CANH TAI LIEU duoc cung cap duoi day.\n"
            "Quy tac quan trong:\n"
            "1. Chi su dung thong tin co trong ngu canh. Khong tu y suy doan hay them that thong tin ngoai le.\n"
            "2. Trinh bay ro rang, chinh xac, co trich dan ten tai lieu va dieu khoan cu the.\n"
            "3. Neu ngu canh khong chua thong tin de tra loi, hay noi ro rang la tai lieu khong de cap.\n\n"
            f"--- NGU CANH TAI LIEU ---\n{context_str}\n--- HET NGU CANH ---"
        )

        messages = [SystemMessage(content=system_prompt)]
        if chat_history:
            for msg in chat_history[-4:]:
                if msg.get("role") == "user":
                    messages.append(HumanMessage(content=msg.get("content", "")))
                elif msg.get("role") == "assistant":
                    messages.append(AIMessage(content=msg.get("content", "")))

        messages.append(HumanMessage(content=query))

        response = self.llm.invoke(messages)
        t_end = time.time()

        metrics = {
            "retrieval_ms": round((t_retrieval - t_start) * 1000, 2),
            "generation_ms": round((t_end - t_retrieval) * 1000, 2),
            "total_ms": round((t_end - t_start) * 1000, 2),
        }

        return response.content, citations, metrics

    def generate_response_stream(
        self,
        query: str,
        chat_history: List[Dict[str, str]] = None,
        use_rag: bool = True,
        use_hybrid: bool = True,
        use_rerank: bool = True,
        user_role: str = "EMPLOYEE",
    ) -> Tuple[Generator[str, None, None], List[CitationSpan]]:
        """Sinh cau tra loi streaming theo thoi gian thuc co ho tro RBAC."""
        citations: List[CitationSpan] = []
        context_str = ""

        if use_rag:
            ranked_docs = self.retrieve_and_rank(
                query, use_hybrid=use_hybrid, use_rerank=use_rerank, user_role=user_role
            )
            citations = self.extract_citation_spans(ranked_docs)
            context_str = self.format_context(ranked_docs)


        system_prompt = (
            "Ban la he thong Tro ly Tra cuu Tri thuc Chuyen nghiep (Enterprise RAG Assistant).\n"
            "Nhiem vu cua ban: Tra loi cau hoi dua tren NGU CANH TAI LIEU duoc cung cap.\n"
            "Quy tac:\n"
            "1. Chi dua tren thong tin trong ngu canh duoc cung cap.\n"
            "2. Trinh bay ngan gon, chinh xac, ro rang.\n"
            "3. Neu khong co thong tin, hay thong bao trung thuc.\n\n"
            f"--- NGU CANH TAI LIEU ---\n{context_str}\n--- HET NGU CANH ---"
        )

        messages = [SystemMessage(content=system_prompt)]
        if chat_history:
            for msg in chat_history[-4:]:
                if msg.get("role") == "user":
                    messages.append(HumanMessage(content=msg.get("content", "")))
                elif msg.get("role") == "assistant":
                    messages.append(AIMessage(content=msg.get("content", "")))

        messages.append(HumanMessage(content=query))

        def stream_generator():
            for chunk in self.llm.stream(messages):
                yield chunk.content

        return stream_generator(), citations
