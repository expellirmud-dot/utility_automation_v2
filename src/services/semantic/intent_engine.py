from typing import Tuple

class IntentDetectionEngine:
    VALID_INTENTS = ["PAYMENT_REQUEST", "APPROVAL", "BUDGET_CHECK", "AUDIT", "REFUND"]

    def detect(self, extracted_data: dict) -> Tuple[str, float]:
        # 1. Rule-based first (keyword + structure)
        # Combine all string values from the extracted data for keyword matching
        text_content = str(extracted_data).lower()
        
        # Keywords
        payment_keywords = ["เบิกจ่าย", "ใบเสร็จ", "ขอเบิก", "invoice", "payment", "ฎีกาเบิกเงิน"]
        approval_keywords = ["อนุมัติ", "เห็นชอบ", "สั่งการ", "approval"]
        budget_keywords = ["ตรวจสอบงบประมาณ", "ยอดคงเหลือ", "budget"]
        audit_keywords = ["ตรวจสอบ", "audit", "ผู้ตรวจสอบ"]
        refund_keywords = ["คืนเงิน", "refund"]

        # Structural hints
        has_net = "net" in text_content or "financials" in extracted_data
        
        if any(kw in text_content for kw in payment_keywords) and has_net:
            return "PAYMENT_REQUEST", 0.95
        elif any(kw in text_content for kw in approval_keywords):
            return "APPROVAL", 0.90
        elif any(kw in text_content for kw in budget_keywords):
            return "BUDGET_CHECK", 0.85
        elif any(kw in text_content for kw in refund_keywords):
            return "REFUND", 0.85
        elif any(kw in text_content for kw in audit_keywords):
            return "AUDIT", 0.80

        # ML fallback could be integrated here (e.g., embedding similarity)
        # Using a dummy fallback for the sake of architecture
        
        return "UNKNOWN", 0.0
