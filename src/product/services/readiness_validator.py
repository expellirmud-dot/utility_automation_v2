from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from src.product.db.models import Case, BillHeader, SourceDocument, BudgetLine, FiscalYear, ExpenseLedger

class ReadinessValidator:

    @staticmethod
    def check_documents(case: Case) -> bool:
        """Check if case has at least one source document."""
        return len(case.documents) > 0

    @staticmethod
    def check_ocr_status(case: Case) -> bool:
        """Check if at least one document has a successfully extracted bill header."""
        for doc in case.documents:
            if doc.bill_header and doc.bill_header.status == 'extracted':
                return True
        return False

    @staticmethod
    def check_memo_generated(case: Case) -> bool:
        """Check if the Word memo document has been generated."""
        if case.dika and case.dika.memo and case.dika.memo.file_path:
            return True
        return False

    @staticmethod
    def check_dika_metadata(case: Case) -> bool:
        """Check if required Dika metadata exists."""
        if not case.dika:
            return False
        return bool(case.dika.dika_number and case.dika.dika_date and case.dika.payee_name)

    @staticmethod
    def normalize_provider(name: str) -> str:
        """Minimal deterministic alias mapping for providers."""
        if not name:
            return ""
        name_lower = name.lower()
        if "nt" in name_lower or "กสท" in name_lower or "โทรคมนาคม" in name_lower:
            return "บริษัท โทรคมนาคมแห่งชาติ จำกัด (มหาชน)"
        if "pea" in name_lower or "กฟภ" in name_lower or ("ไฟฟ้า" in name_lower and "ภูมิภาค" in name_lower):
            return "การไฟฟ้าส่วนภูมิภาค"
        if "pwa" in name_lower or "กปภ" in name_lower or ("ประปา" in name_lower and "ภูมิภาค" in name_lower):
            return "การประปาส่วนภูมิภาค"
        return name.strip()

    @staticmethod
    def check_duplicate_bill(case: Case, db: Session) -> list[str]:
        """Look for duplicate bills with the same provider, date, and amount across other cases."""
        warnings = []
        extracted_headers = [doc.bill_header for doc in case.documents if doc.bill_header and doc.bill_header.status == 'extracted']
        if not extracted_headers:
            return warnings

        # Pick the highest amount bill header for duplicate check
        target_header = max(extracted_headers, key=lambda x: x.total_amount)
        if not target_header.provider or not target_header.bill_date:
            return warnings

        norm_provider = ReadinessValidator.normalize_provider(target_header.provider)

        # Query all other extracted bills with same date and amount
        duplicates = db.query(BillHeader).join(BillHeader.document).filter(
            SourceDocument.case_id != case.id,
            BillHeader.status == 'extracted',
            BillHeader.bill_date == target_header.bill_date,
            BillHeader.total_amount == target_header.total_amount
        ).all()

        for dup in duplicates:
            if ReadinessValidator.normalize_provider(dup.provider) == norm_provider:
                warnings.append(f"อาจเป็นบิลซ้ำซ้อนกับเลขแฟ้ม {dup.document.case.case_number}")

        # Deduplicate warnings
        return list(dict.fromkeys(warnings))

    @staticmethod
    def validate_budget(case: Case, db: Session) -> dict:
        """Compare required amount against available budget line."""
        extracted_headers = [doc.bill_header for doc in case.documents if doc.bill_header and doc.bill_header.status == 'extracted']
        if extracted_headers:
            required_amount = max(header.total_amount for header in extracted_headers)
        else:
            required_amount = case.total_amount or 0.0

        if case.budget_line_id:
            budget_line = db.query(BudgetLine).filter(BudgetLine.id == case.budget_line_id).first()
        else:
            query = db.query(BudgetLine).join(FiscalYear).filter(
                FiscalYear.year_be == case.fiscal_year_be,
                BudgetLine.department == case.department,
                BudgetLine.expense_type == case.expense_group
            )

            if case.division:
                query = query.filter(BudgetLine.division == case.division)

            matches = query.order_by(BudgetLine.id.asc()).all()
            if len(matches) > 1:
                return {
                    "budget_ok": False,
                    "available_budget": 0.0,
                    "required_amount": required_amount,
                    "reason": "พบรายการงบประมาณมากกว่า 1 รายการ กรุณาเลือกงบประมาณด้วยตนเอง"
                }
            budget_line = matches[0] if matches else None

        if not budget_line:
            return {
                "budget_ok": False,
                "available_budget": 0.0,
                "required_amount": required_amount,
                "reason": "ไม่พบรายการงบประมาณที่ตรงกัน"
            }

        deducted = db.query(func.sum(ExpenseLedger.amount_deducted)).filter(
            ExpenseLedger.budget_line_id == budget_line.id,
            ExpenseLedger.case_id != case.id # Exclude current case if it already deducted
        ).scalar() or 0.0

        available_budget = budget_line.initial_amount - deducted
        budget_ok = available_budget >= required_amount
        reason = "" if budget_ok else "งบประมาณคงเหลือไม่เพียงพอ"

        return {
            "budget_ok": budget_ok,
            "available_budget": available_budget,
            "required_amount": required_amount,
            "reason": reason
        }

    @staticmethod
    def evaluate_readiness(case: Case, db: Session) -> dict:
        """Evaluate all readiness criteria and return structured result."""
        doc_ok = ReadinessValidator.check_documents(case)
        ocr_ok = ReadinessValidator.check_ocr_status(case)
        dika_ok = ReadinessValidator.check_dika_metadata(case)
        memo_ok = ReadinessValidator.check_memo_generated(case)

        budget_info = ReadinessValidator.validate_budget(case, db)
        budget_ok = budget_info["budget_ok"]

        blockers = []
        if not doc_ok:
            blockers.append("ไม่มีเอกสารอัปโหลด")
        if not ocr_ok:
            blockers.append("ยังไม่มีบิลที่ผ่านการวิเคราะห์ (OCR) สำเร็จ")
        if not dika_ok:
            blockers.append("ข้อมูลฎีกาไม่ครบถ้วน")
        if not memo_ok:
            blockers.append("ยังไม่ได้สร้างบันทึกข้อความ (Word)")
        if not budget_ok:
            blockers.append(f"ปัญหาด้านงบประมาณ: {budget_info['reason']}")

        warnings = ReadinessValidator.check_duplicate_bill(case, db)

        ready = (doc_ok and ocr_ok and dika_ok and memo_ok and budget_ok)

        return {
            "ready": ready,
            "budget_ok": budget_ok,
            "available_budget": budget_info["available_budget"],
            "required_amount": budget_info["required_amount"],
            "blockers": blockers,
            "warnings": warnings,
            "summary": {
                "document_status": doc_ok,
                "ocr_status": ocr_ok,
                "dika_status": dika_ok,
                "memo_status": memo_ok
            }
        }
