import re
from typing import List, Dict, Any, Tuple
from rank_bm25 import BM25Okapi
from langchain_core.documents import Document

try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings

from backend.app.config import VECTOR_DB_DIR, OLLAMA_BASE_URL, OLLAMA_EMBED_MODEL


class HybridRetrieverService:
    def __init__(
        self,
        base_url: str = OLLAMA_BASE_URL,
        embed_model: str = OLLAMA_EMBED_MODEL,
        collection_name: str = "advanced_rag_collection",
        rrf_k: int = 60,
    ):
        self.base_url = base_url
        self.embed_model = embed_model
        self.collection_name = collection_name
        self.rrf_k = rrf_k
        self.persist_directory = str(VECTOR_DB_DIR)

        # 1. Khoi tao Vector Store (Dense Retriever)
        self.embeddings = OllamaEmbeddings(
            base_url=self.base_url,
            model=self.embed_model,
        )
        self.vector_store = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory,
        )

        # 2. Khoi tao BM25 (Sparse Keyword Retriever)
        self.bm25_corpus: List[Document] = []
        self.bm25_index: BM25Okapi = None
        self._sync_bm25_from_chroma()

    def _tokenize(self, text: str) -> List[str]:
        """Tach tu co ban ho tro ca tieng Viet va ky hieu ky thuat."""
        clean = re.sub(r"[^\w\s_]", " ", text.lower())
        tokens = [t for t in clean.split() if len(t) > 1]
        return tokens or [text.lower()]

    def _sync_bm25_from_chroma(self):
        """Dong bo toan bo du lieu tu ChromaDB sang BM25 Index."""
        try:
            collection = self.vector_store._collection
            count = collection.count()
            if count == 0:
                self.bm25_corpus = []
                self.bm25_index = None
                return

            data = collection.get(include=["documents", "metadatas"])
            docs = []
            for text, meta in zip(data.get("documents", []), data.get("metadatas", [])):
                docs.append(Document(page_content=text, metadata=meta or {}))

            self.bm25_corpus = docs
            tokenized_corpus = [self._tokenize(doc.page_content) for doc in docs]
            self.bm25_index = BM25Okapi(tokenized_corpus)
        except Exception:
            self.bm25_corpus = []
            self.bm25_index = None

    def add_documents(self, documents: List[Document]) -> int:
        """Them tai lieu vao ca Vector DB va BM25 Index."""
        if not documents:
            return 0
        self.vector_store.add_documents(documents)
        self._sync_bm25_from_chroma()
        return len(documents)

    ROLE_PERMISSIONS = {
        "ADMIN": {
            "classifications": ["PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"],
            "departments": None,
        },
        "LEGAL": {
            "classifications": ["PUBLIC", "INTERNAL", "CONFIDENTIAL"],
            "departments": ["LEGAL", "GENERAL", "ALL"],
        },
        "HR": {
            "classifications": ["PUBLIC", "INTERNAL", "CONFIDENTIAL"],
            "departments": ["HR", "GENERAL", "ALL"],
        },
        "FINANCE": {
            "classifications": ["PUBLIC", "INTERNAL", "CONFIDENTIAL"],
            "departments": ["FINANCE", "GENERAL", "ALL"],
        },
        "EMPLOYEE": {
            "classifications": ["PUBLIC", "INTERNAL"],
            "departments": ["GENERAL", "ALL"],
        },
    }

    def is_accessible(self, doc: Document, user_role: str = "EMPLOYEE") -> bool:
        """Kiem tra xem User Role hien tai co quyen truy xuat chunk tai lieu nay hay khong."""
        perm = self.ROLE_PERMISSIONS.get(user_role.upper(), self.ROLE_PERMISSIONS["EMPLOYEE"])
        meta = doc.metadata or {}
        doc_class = str(meta.get("classification", "INTERNAL")).upper()
        doc_dept = str(meta.get("department", "GENERAL")).upper()

        # Tai lieu PUBLIC (Luat phap quoc gia, nghi dinh, thong tin cong khai) cho phep tat ca moi nguoi truy cap
        if doc_class == "PUBLIC":
            return True

        if doc_class not in perm["classifications"]:
            return False

        if perm["departments"] is not None:
            if doc_dept not in perm["departments"] and doc_dept != "ALL":
                return False

        return True


    def dense_search(self, query: str, k: int = 10, user_role: str = "EMPLOYEE") -> List[Tuple[Document, float]]:
        """Truy xuat theo vector ngu nghia (Dense) co ap dung bo loc phan quyen RBAC."""
        try:
            results = self.vector_store.similarity_search_with_score(query, k=k * 2)
            filtered = [(doc, score) for doc, score in results if self.is_accessible(doc, user_role)]
            return filtered[:k]
        except Exception:
            return []

    def sparse_search(self, query: str, k: int = 10, user_role: str = "EMPLOYEE") -> List[Tuple[Document, float]]:
        """Truy xuat theo tu khoa chinh xac (BM25) co ap dung bo loc phan quyen RBAC."""
        if not self.bm25_index or not self.bm25_corpus:
            return []

        tokens = self._tokenize(query)
        scores = self.bm25_index.get_scores(tokens)

        # Sap xep theo diem so cao nhat
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        results = []
        for idx in ranked_indices:
            if scores[idx] > 0:
                doc = self.bm25_corpus[idx]
                if self.is_accessible(doc, user_role):
                    results.append((doc, float(scores[idx])))
            if len(results) >= k:
                break
        return results

    def hybrid_search_rrf(
        self, query: str, top_k: int = 4, candidate_k: int = 15, user_role: str = "EMPLOYEE"
    ) -> List[Tuple[Document, float]]:
        """
        Thuat toan Reciprocal Rank Fusion (RRF) hop nhat Dense va Sparse Search co phan quyen RBAC.
        Diem so = 1 / (60 + Rank_Dense) + 1 / (60 + Rank_BM25)
        """
        dense_results = self.dense_search(query, k=candidate_k, user_role=user_role)
        sparse_results = self.sparse_search(query, k=candidate_k, user_role=user_role)

        rrf_scores: Dict[str, float] = {}
        doc_map: Dict[str, Document] = {}

        # 1. Tinh diem Dense Rank
        for rank, (doc, _) in enumerate(dense_results, 1):
            key = f"{doc.metadata.get('source', '')}_{doc.metadata.get('chunk_index', rank)}_{doc.page_content[:30]}"
            doc_map[key] = doc
            rrf_scores[key] = rrf_scores.get(key, 0.0) + (1.0 / (self.rrf_k + rank))

        # 2. Tinh diem Sparse (BM25) Rank
        for rank, (doc, _) in enumerate(sparse_results, 1):
            key = f"{doc.metadata.get('source', '')}_{doc.metadata.get('chunk_index', rank)}_{doc.page_content[:30]}"
            doc_map[key] = doc
            rrf_scores[key] = rrf_scores.get(key, 0.0) + (1.0 / (self.rrf_k + rank))

        # 3. Sap xep theo diem RRF cao nhat
        sorted_keys = sorted(rrf_scores.keys(), key=lambda k: rrf_scores[k], reverse=True)[:top_k]

        final_ranked = [(doc_map[k], rrf_scores[k]) for k in sorted_keys]
        return final_ranked


    def get_indexed_documents_info(self) -> Dict[str, Any]:
        """Lay thong ke danh sach file va so chunks kem metadata phan quyen."""
        try:
            collection = self.vector_store._collection
            count = collection.count()
            if count == 0:
                return {"total_chunks": 0, "files": []}

            data = collection.get(include=["metadatas"])
            files_map: Dict[str, Dict[str, Any]] = {}
            for meta in data.get("metadatas", []):
                meta = meta or {}
                source = meta.get("source", "Unknown")
                if source not in files_map:
                    files_map[source] = {
                        "name": source,
                        "chunks": 0,
                        "department": meta.get("department", "GENERAL"),
                        "classification": meta.get("classification", "INTERNAL"),
                    }
                files_map[source]["chunks"] += 1

            files_list = list(files_map.values())
            return {"total_chunks": count, "files": files_list}
        except Exception:
            return {"total_chunks": 0, "files": []}


    def delete_document_by_source(self, source_name: str) -> bool:
        """Xoa mot file khoi Vector DB va cap nhat BM25."""
        try:
            collection = self.vector_store._collection
            collection.delete(where={"source": source_name})
            self._sync_bm25_from_chroma()
            return True
        except Exception:
            return False

    def clear_database(self) -> bool:
        """Xoa trang toan bo co so du lieu."""
        try:
            import shutil
            if VECTOR_DB_DIR.exists():
                shutil.rmtree(VECTOR_DB_DIR)
            VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)
            self.vector_store = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=str(VECTOR_DB_DIR),
            )
            self.bm25_corpus = []
            self.bm25_index = None
            return True
        except Exception:
            return False
