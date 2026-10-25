import requests
from typing import Dict, Any, List, Optional


class RAGBackendClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")

    def check_health(self) -> Dict[str, Any]:
        try:
            res = requests.get(f"{self.base_url}/health", timeout=3)
            return res.json() if res.status_code == 200 else {"status": "unhealthy"}
        except Exception:
            return {"status": "offline"}

    def get_users(self) -> List[Dict[str, Any]]:
        try:
            res = requests.get(f"{self.base_url}/api/audit/users", timeout=5)
            return res.json() if res.status_code == 200 else []
        except Exception:
            return []

    def get_conversations(self, user_id: int = 1) -> List[Dict[str, Any]]:
        try:
            res = requests.get(f"{self.base_url}/api/conversations", params={"user_id": user_id}, timeout=5)
            return res.json() if res.status_code == 200 else []
        except Exception:
            return []

    def create_conversation(self, user_id: int = 1, title: str = "Phien tra cuu moi") -> Dict[str, Any]:
        try:
            res = requests.post(
                f"{self.base_url}/api/conversations",
                json={"user_id": user_id, "title": title},
                timeout=5,
            )
            return res.json() if res.status_code == 200 else {}
        except Exception:
            return {}

    def get_conversation_messages(self, conv_id: str) -> Dict[str, Any]:
        try:
            res = requests.get(f"{self.base_url}/api/conversations/{conv_id}/messages", timeout=5)
            return res.json() if res.status_code == 200 else {"messages": []}
        except Exception:
            return {"messages": []}

    def delete_conversation(self, conv_id: str) -> bool:
        try:
            res = requests.delete(f"{self.base_url}/api/conversations/{conv_id}", timeout=5)
            return res.status_code == 200
        except Exception:
            return False

    def query(
        self,
        prompt: str,
        chat_history: List[Dict[str, str]] = None,
        use_rag: bool = True,
        use_hybrid: bool = True,
        use_rerank: bool = True,
        top_k: int = 4,
        temperature: float = 0.3,
        user_id: int = 1,
        user_role: str = "EMPLOYEE",
        conversation_id: Optional[str] = None,
        mask_pii: bool = True,
    ) -> Dict[str, Any]:
        payload = {
            "query": prompt,
            "use_rag": use_rag,
            "use_hybrid": use_hybrid,
            "use_rerank": use_rerank,
            "top_k": top_k,
            "temperature": temperature,
            "chat_history": chat_history or [],
            "user_id": user_id,
            "user_role": user_role,
            "conversation_id": conversation_id,
            "mask_pii": mask_pii,
        }
        res = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=90)
        res.raise_for_status()
        return res.json()

    def submit_feedback(self, message_id: int, rating: int, comment: Optional[str] = None, user_id: int = 1) -> Dict[str, Any]:
        try:
            payload = {
                "message_id": message_id,
                "rating": rating,
                "comment": comment,
                "user_id": user_id,
            }
            res = requests.post(f"{self.base_url}/api/audit/feedback", json=payload, timeout=5)
            return res.json() if res.status_code == 200 else {}
        except Exception:
            return {}

    def list_documents(self) -> Dict[str, Any]:
        res = requests.get(f"{self.base_url}/api/documents", timeout=10)
        res.raise_for_status()
        return res.json()

    def upload_document(
        self,
        file_bytes: bytes,
        filename: str,
        department: str = "GENERAL",
        classification: str = "INTERNAL",
        uploaded_by: str = "admin",
    ) -> Dict[str, Any]:
        files = {"file": (filename, file_bytes)}
        data = {
            "department": department,
            "classification": classification,
            "uploaded_by": uploaded_by,
        }
        res = requests.post(f"{self.base_url}/api/documents/upload", files=files, data=data, timeout=120)
        res.raise_for_status()
        return res.json()

    def get_document_highlight(
        self,
        file_name: str,
        char_start: Optional[int] = None,
        char_end: Optional[int] = None,
        line_start: Optional[int] = None,
        line_end: Optional[int] = None,
    ) -> Dict[str, Any]:
        params = {}
        if char_start is not None:
            params["char_start"] = char_start
        if char_end is not None:
            params["char_end"] = char_end
        if line_start is not None:
            params["line_start"] = line_start
        if line_end is not None:
            params["line_end"] = line_end

        res = requests.get(f"{self.base_url}/api/documents/{file_name}/highlight", params=params, timeout=10)
        res.raise_for_status()
        return res.json()

    def ingest_samples(self) -> Dict[str, Any]:
        res = requests.post(f"{self.base_url}/api/documents/ingest-samples", timeout=120)
        res.raise_for_status()
        return res.json()

    def delete_document(self, name: str) -> Dict[str, Any]:
        res = requests.delete(f"{self.base_url}/api/documents/{name}", timeout=10)
        res.raise_for_status()
        return res.json()

    def get_audit_metrics(self) -> Dict[str, Any]:
        try:
            res = requests.get(f"{self.base_url}/api/audit/metrics", timeout=5)
            return res.json() if res.status_code == 200 else {}
        except Exception:
            return {}

    def get_audit_logs(self, limit: int = 50, action: Optional[str] = None, role: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            params = {"limit": limit}
            if action:
                params["action"] = action
            if role:
                params["role"] = role
            res = requests.get(f"{self.base_url}/api/audit/logs", params=params, timeout=5)
            return res.json() if res.status_code == 200 else []
        except Exception:
            return []

    def run_benchmark(self) -> Dict[str, Any]:
        res = requests.post(f"{self.base_url}/api/eval/benchmark", timeout=180)
        res.raise_for_status()
        return res.json()
