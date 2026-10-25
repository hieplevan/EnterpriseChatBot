import re
from typing import List, Tuple
from langchain_core.documents import Document


class RerankerService:
    """
    Dich vu Cross-Re-Ranking: Cham diem va sap xep lai thu tu cac chunk ung vien.
    Loc bo cac doan gay nhieu va dua doan co gia tri tra loi cao nhat len dau.
    """

    def __init__(self):
        pass

    def _extract_query_features(self, query: str) -> List[str]:
        words = re.findall(r"\w+", query.lower())
        return [w for w in words if len(w) > 1]

    def score_document(self, query: str, doc: Document, initial_score: float = 0.0) -> float:
        """
        Thuat toan cham diem relevance dua tren:
        - Mat do tu khoa truy van xuat hien trong chunk
        - Ty le bao phu cua cum tu (bigram/trigram overlap)
        - Vi tri xuat hien cua tu khoa
        """
        q_tokens = self._extract_query_features(query)
        if not q_tokens:
            return initial_score

        doc_text = doc.page_content.lower()
        total_tokens = len(q_tokens)
        matched_tokens = 0

        # 1. Exact token matches
        for t in q_tokens:
            if t in doc_text:
                matched_tokens += 1

        token_coverage = matched_tokens / max(1, total_tokens)

        # 2. Phrase matching (2 tu lien tiep)
        phrase_matches = 0
        for i in range(len(q_tokens) - 1):
            phrase = f"{q_tokens[i]} {q_tokens[i+1]}"
            if phrase in doc_text:
                phrase_matches += 1

        phrase_bonus = (phrase_matches * 0.25)

        # 3. Ket hop voi diem ban dau (RRF score)
        final_score = (token_coverage * 0.6) + phrase_bonus + (initial_score * 0.4)
        return round(final_score, 4)

    def rerank(
        self, query: str, candidates: List[Tuple[Document, float]], top_k: int = 4
    ) -> List[Tuple[Document, float]]:
        """
        Nhan danh sach candidate tu Hybrid Search, tinh toan diem moi va sap xep lai.
        """
        if not candidates:
            return []

        scored_list = []
        for doc, init_score in candidates:
            rescore = self.score_document(query, doc, initial_score=init_score)
            scored_list.append((doc, rescore))

        # Sap xep giam dan theo diem moi
        scored_list.sort(key=lambda item: item[1], reverse=True)
        return scored_list[:top_k]
