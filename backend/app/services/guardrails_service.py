import re
from typing import Tuple, List, Dict, Any


class EnterpriseGuardrailsService:
    def __init__(self):
        # Regex mau PII pho bien tai Viet Nam
        self.cccd_pattern = re.compile(r"\b(?:\d{9}|\d{12})\b")
        self.phone_pattern = re.compile(r"(?:\+84|0)(?:3[2-9]|5[2689]|7[06-9]|8[1-9]|9[0-9])\d{7}\b")
        self.email_pattern = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")
        self.card_pattern = re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b")

        # Tu khoa tan cong Prompt Injection & Jailbreak
        self.injection_patterns = [
            re.compile(r"ignore\s+(?:all\s+)?(?:previous|prior)\s+instructions", re.IGNORECASE),
            re.compile(r"system\s+prompt\s+override", re.IGNORECASE),
            re.compile(r"you\s+are\s+now\s+in\s+developer\s+mode", re.IGNORECASE),
            re.compile(r"jailbreak|bypass\s+(?:filter|safety|policy)", re.IGNORECASE),
            re.compile(r"reveal\s+(?:all\s+)?system\s+instructions", re.IGNORECASE),
            re.compile(r"bo\s+qua\s+moi\s+chi\s+thi\s+truoc\s+do", re.IGNORECASE),
        ]

    def check_prompt_safety(self, text: str) -> Tuple[bool, str]:
        """Kiem tra xem query co chua hanh vi tan cong prompt injection hay khong."""
        for pattern in self.injection_patterns:
            if pattern.search(text):
                return False, "Phat hien hanh vi tan cong Prompt Injection hoac vi pham chinh sach an toan he thong."
        return True, ""

    def sanitize_and_mask_pii(self, text: str) -> Tuple[str, List[str]]:
        """
        Phat hien va che (masking) cac thong tin ca nhan nhay cam (PII)
        nhu CCCD/CMND, So dien thoai, Email, So the ngan hang.
        Tra ve (masked_text, danh_sach_loai_pii_da_phat_hien).
        """
        detected_types: List[str] = []
        masked_text = text

        # 1. PII: Email
        if self.email_pattern.search(masked_text):
            detected_types.append("EMAIL")
            masked_text = self.email_pattern.sub("[REDACTED_EMAIL]", masked_text)

        # 2. PII: Phone
        if self.phone_pattern.search(masked_text):
            detected_types.append("PHONE_NUMBER")
            masked_text = self.phone_pattern.sub("[REDACTED_PHONE]", masked_text)

        # 3. PII: Card
        if self.card_pattern.search(masked_text):
            detected_types.append("CREDIT_CARD")
            masked_text = self.card_pattern.sub("[REDACTED_CARD]", masked_text)

        # 4. PII: CCCD / CMND (chi che khi khong phai so hieu van ban/nam)
        if self.cccd_pattern.search(masked_text):
            detected_types.append("CITIZEN_ID_CCCD")
            masked_text = self.cccd_pattern.sub("[REDACTED_ID]", masked_text)

        return masked_text, detected_types
