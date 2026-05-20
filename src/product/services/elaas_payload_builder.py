"""
e-LAAS Payload Builder Service for PRODUCT-006.

Assembles a deterministic, copy-ready JSON payload from existing
Case / BillHeader / Dika / Memo / BudgetLine data.

No browser automation. No credentials. Operator-assisted only.
"""

import datetime
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from src.product.db.models import (
    Case, BillHeader, SourceDocument, Dika, Memo, BudgetLine,
    FiscalYear, ExpenseLedger, ElaasPayload,
)
from src.product.services.word_generation import bahttext, thai_date_format
from src.product.services.readiness_validator import ReadinessValidator


# ---------------------------------------------------------------------------
# Static attachment checklist
# ---------------------------------------------------------------------------

ATTACHMENT_CHECKLIST = [
    {"id": 1, "label": "ใบแจ้งหนี้ / บิลค่าใช้จ่าย",              "required": True,  "doc_type": "bill"},
    {"id": 2, "label": "ใบเสร็จรับเงิน (ถ้ามี)",                   "required": False, "doc_type": "receipt"},
    {"id": 3, "label": "บันทึกข้อความขออนุมัติเบิกจ่าย (Word)",    "required": True,  "doc_type": "memo_generated"},
    {"id": 4, "label": "สำเนาสัญญาหรือใบสั่งซื้อ (ถ้าบังคับ)",    "required": False, "doc_type": "contract"},
    {"id": 5, "label": "ฎีกาเบิกเงิน",                             "required": True,  "doc_type": "dika"},
]


class ElaasPayloadBuilder:
    """Stateless service that builds the e-LAAS submission payload."""

    @staticmethod
    def _get_best_bill_header(case: Case) -> Optional[BillHeader]:
        """Return the extracted BillHeader with the highest amount, or None."""
        extracted = [
            doc.bill_header
            for doc in case.documents
            if doc.bill_header and doc.bill_header.status == "extracted"
        ]
        if not extracted:
            return None
        return max(extracted, key=lambda h: h.total_amount)

    @staticmethod
    def _get_available_budget(case: Case, db: Session) -> Optional[float]:
        """Return available budget for the case's budget line, or None if not found."""
        if case.budget_line_id:
            budget_line = db.query(BudgetLine).filter(BudgetLine.id == case.budget_line_id).first()
        else:
            query = db.query(BudgetLine).join(FiscalYear).filter(
                FiscalYear.year_be == case.fiscal_year_be,
                BudgetLine.department == case.department,
                BudgetLine.expense_type == case.expense_group,
            )
            if case.division:
                query = query.filter(BudgetLine.division == case.division)
            matches = query.order_by(BudgetLine.id.asc()).all()
            budget_line = matches[0] if len(matches) == 1 else None
        if not budget_line:
            return None
        deducted = db.query(func.sum(ExpenseLedger.amount_deducted)).filter(
            ExpenseLedger.budget_line_id == budget_line.id,
            ExpenseLedger.case_id != case.id,
        ).scalar() or 0.0
        return budget_line.initial_amount - deducted

    @staticmethod
    def _build_attachment_status(case: Case) -> list:
        """Build checklist with present/absent status per item."""
        doc_types_present = {doc.document_type for doc in case.documents}
        has_memo = bool(case.dika and case.dika.memo and case.dika.memo.file_path)
        has_dika = bool(case.dika and case.dika.dika_number)

        result = []
        for item in ATTACHMENT_CHECKLIST:
            if item["doc_type"] == "memo_generated":
                present = has_memo
            elif item["doc_type"] == "dika":
                present = has_dika
            else:
                present = item["doc_type"] in doc_types_present
            result.append({**item, "present": present})
        return result

    @staticmethod
    def build(case: Case, db: Session) -> dict:
        """
        Build the complete e-LAAS submission payload dict.

        Field source priority:
          payee_name   : Dika.payee_name > BillHeader.provider (normalized)
          provider     : BillHeader.provider (normalized) > Dika.payee_name
          amount       : max(extracted BillHeader.total_amount) > Case.total_amount
          dates        : respective model fields, "" if missing
        """
        dika: Optional[Dika] = case.dika
        memo: Optional[Memo] = dika.memo if dika else None
        bill_header = ElaasPayloadBuilder._get_best_bill_header(case)

        # Amounts
        if bill_header:
            bill_amount = bill_header.total_amount
            bill_date = bill_header.bill_date
            raw_provider = bill_header.provider or ""
        else:
            bill_amount = case.total_amount or 0.0
            bill_date = None
            raw_provider = ""

        normalized_provider = ReadinessValidator.normalize_provider(raw_provider) if raw_provider else ""

        # Payee priority: Dika > normalized provider
        payee_name = ""
        if dika and dika.payee_name:
            payee_name = dika.payee_name
        elif normalized_provider:
            payee_name = normalized_provider

        # Budget
        available_budget = ElaasPayloadBuilder._get_available_budget(case, db)

        payload = {
            # หมวดหน่วยงาน
            "case_number":         case.case_number,
            "department":          case.department or "",
            "division":            case.division or "",
            "fiscal_year_be":      case.fiscal_year_be,
            "expense_group":       case.expense_group or "",
            "work_month":          case.work_month or "",

            # หมวดผู้รับเงิน
            "payee_name":          payee_name,

            # หมวดบิล
            "provider":            normalized_provider,
            "bill_date":           bill_date.isoformat() if bill_date else "",
            "bill_date_thai":      thai_date_format(bill_date),
            "bill_amount":         bill_amount,
            "bill_amount_thai":    bahttext(bill_amount),

            # หมวดฎีกา
            "dika_number":         dika.dika_number if dika else "",
            "dika_date":           dika.dika_date.isoformat() if (dika and dika.dika_date) else "",
            "dika_date_thai":      thai_date_format(dika.dika_date if dika else None),

            # หมวดบันทึกข้อความ
            "memo_number":         memo.memo_number if memo else "",
            "memo_date":           memo.memo_date.isoformat() if (memo and memo.memo_date) else "",
            "memo_date_thai":      thai_date_format(memo.memo_date if memo else None),
            "memo_file_path":      memo.file_path if memo else "",

            # งบประมาณ (info-only)
            "budget_available":    available_budget,

            # สถานะความพร้อม
            "readiness_passed":    all([
                bool(case.documents),
                bill_header is not None,
                dika is not None and bool(dika.dika_number),
                memo is not None and bool(memo.file_path),
            ]),

            # รายการเอกสารแนบ
            "attachment_checklist": ElaasPayloadBuilder._build_attachment_status(case),
        }

        return payload

    @staticmethod
    def save(case: Case, payload: dict, db: Session) -> ElaasPayload:
        """Persist the prepared payload as an ElaasPayload record (status=prepared)."""
        existing = db.query(ElaasPayload).filter(ElaasPayload.case_id == case.id).first()
        if existing:
            existing.payload_data = payload
            existing.status = "prepared"
            db.commit()
            db.refresh(existing)
            return existing

        record = ElaasPayload(
            case_id=case.id,
            payload_data=payload,
            status="prepared",
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
