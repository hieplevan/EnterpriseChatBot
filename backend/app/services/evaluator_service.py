import re
from typing import List, Dict, Any
from backend.app.schemas.query import CitationSpan


class RAGEvaluatorService:
    """
    Dich vu danh gia dinh luong chat luong he thong RAG:
    - Faithfulness / Groundedness: Do trung thuc (khong ao giac)
    - Context Relevance: Do chinh xac cua tai lieu duoc tim kiem
    - Answer Relevance: Do bao phu va dung trong tam cau hoi
    """

    def __init__(self):
        pass

    def evaluate_groundedness(self, answer: str, citations: List[CitationSpan]) -> float:
        """
        Do luong muc do cau tra loi duoc can cu tren tai lieu goc.
        Kiem tra ty le n-gram / tu khoa quan trong trong cau tra loi co mat trong context.
        """
        if not citations or not answer:
            return 0.0

        context_text = " ".join([c.content.lower() for c in citations])
        answer_words = re.findall(r"\w+", answer.lower())
        meaningful_words = [w for w in answer_words if len(w) > 2]

        if not meaningful_words:
            return 1.0

        supported_count = sum(1 for w in meaningful_words if w in context_text)
        groundedness_score = round(supported_count / len(meaningful_words), 4)
        return min(1.0, max(0.0, groundedness_score))

    def evaluate_context_relevance(self, query: str, citations: List[CitationSpan]) -> float:
        """
        Do luong muc do cac doan tai lieu tim duoc thuc su lien quan den cau hoi.
        """
        if not citations or not query:
            return 0.0

        query_words = set(re.findall(r"\w+", query.lower()))
        if not query_words:
            return 1.0

        doc_relevance_scores = []
        for cit in citations:
            doc_words = set(re.findall(r"\w+", cit.content.lower()))
            overlap = query_words.intersection(doc_words)
            doc_relevance_scores.append(len(overlap) / len(query_words))

        avg_relevance = sum(doc_relevance_scores) / len(doc_relevance_scores)
        return round(min(1.0, max(0.0, avg_relevance)), 4)

    def evaluate_pipeline(
        self, query: str, answer: str, citations: List[CitationSpan]
    ) -> Dict[str, Any]:
        """
        Tong hop chi so RAG Triad Metrics cho mot phien hoi dap.
        """
        groundedness = self.evaluate_groundedness(answer, citations)
        context_relevance = self.evaluate_context_relevance(query, citations)

        # Answer relevance uoc tinh
        q_tokens = set(re.findall(r"\w+", query.lower()))
        a_tokens = set(re.findall(r"\w+", answer.lower()))
        ans_relevance = round(min(1.0, len(q_tokens.intersection(a_tokens)) / max(1, len(q_tokens))), 4)

        overall_score = round((groundedness * 0.45) + (context_relevance * 0.35) + (ans_relevance * 0.20), 4)

        return {
            "groundedness_faithfulness": round(groundedness * 100, 1),
            "context_relevance": round(context_relevance * 100, 1),
            "answer_relevance": round(ans_relevance * 100, 1),
            "rag_overall_quality": round(overall_score * 100, 1),
            "passed_guardrail": groundedness >= 0.65,
        }
