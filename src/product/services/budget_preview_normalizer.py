import hashlib
from typing import List, Dict, Any, Optional

class BudgetPreviewNormalizer:
    """
    Normalizes the raw dictionary output from RemainedBudgetParser into 
    a canonical BudgetPreviewBatch structure, enforcing placeholder 
    separation, derivation rules, and evidence tracking.
    """

    @classmethod
    def normalize_batch(cls, raw_rows: List[Dict[str, Any]], source_file: str, source_identifier: str = "") -> Dict[str, Any]:
        """
        Takes raw parsed rows and returns a BudgetPreviewBatch.
        """
        if not raw_rows:
            return {
                "preview_kind": "remained_budget_xlsx",
                "source": {
                    "file_name": source_file,
                    "source_identifier": source_identifier,
                },
                "metadata": {},
                "rows": [],
                "summary": {"total_rows": 0}
            }

        # Extract metadata from the first row as it's duplicated across parser output
        first_row = raw_rows[0]
        metadata = {
            "fiscal_year_be": first_row.get("fiscal_year_be"),
            "printed_month": first_row.get("printed_month"),
            "municipality": first_row.get("municipality")
        }

        normalized_rows = []
        for index, row in enumerate(raw_rows):
            normalized_rows.append(cls._normalize_row(row, source_identifier, index))

        return {
            "preview_kind": "remained_budget_xlsx",
            "source": {
                "file_name": source_file,
                "source_identifier": source_identifier,
            },
            "metadata": metadata,
            "rows": normalized_rows,
            "summary": {
                "total_rows": len(normalized_rows)
            }
        }

    @classmethod
    def _normalize_row(cls, row: Dict[str, Any], source_identifier: str, index: int) -> Dict[str, Any]:
        source_row = row.get("source_row", index + 1)
        
        # Deterministic preview_row_id
        # Using source_identifier and source_row to create a stable hash
        hash_input = f"{source_identifier}_{source_row}".encode('utf-8')
        preview_row_id = f"prev_{hashlib.sha256(hash_input).hexdigest()[:12]}"
        
        # Source hash based on provided identifier or file
        source_hash = hashlib.sha256(source_identifier.encode('utf-8')).hexdigest()[:12] if source_identifier else "unknown"

        # Safe extraction for amounts to ensure JSON-safe primitives
        def _safe_float(val: Any) -> Optional[float]:
            if val is None:
                return None
            # Check for pandas NaN (which is a float but not equal to itself)
            if isinstance(val, float) and val != val:
                return None
            return float(val)

        extracted = {
            "work": row.get("work", ""),
            "appropriation_category": row.get("appropriation_category", ""),
            "expense_type": row.get("expense_type", ""),
            "project": row.get("project", ""),
            "budget_code": row.get("budget_code", ""),
            "approved_amount": _safe_float(row.get("approved_amount")),
            "transfer_in": _safe_float(row.get("transfer_in")),
            "transfer_out": _safe_float(row.get("transfer_out")),
            "obligated_amount": _safe_float(row.get("obligated_amount")),
            "disbursed_amount": _safe_float(row.get("disbursed_amount")),
            "remaining_amount": _safe_float(row.get("remaining_amount"))
        }

        placeholders = {
            "department": "รอข้อมูลจริง",
            "plan": "รอข้อมูลจริง",
            "budget": "รอข้อมูลจริง"
        }

        # Derived Withholding Tax
        expense_type = extracted.get("expense_type", "")
        appropriation_category = extracted.get("appropriation_category", "")
        
        withholding_tax = {
            "applies": None,
            "rule_id": "NON_UTILITY_UNKNOWN",
            "display_label": "รอตรวจสอบ"
        }
        
        if expense_type == "ค่าไฟฟ้า":
            withholding_tax = {
                "applies": False,
                "rule_id": "UTILITY_ELECTRICITY_NO_WHT",
                "display_label": "ไม่หักภาษี ณ ที่จ่าย"
            }
        elif appropriation_category == "ค่าสาธารณูปโภค" and expense_type != "ค่าไฟฟ้า":
            withholding_tax = {
                "applies": True,
                "rule_id": "UTILITY_DEFAULT_WHT",
                "display_label": "หักภาษี ณ ที่จ่าย"
            }

        derived = {
            "withholding_tax": withholding_tax,
            "mapping_readiness": {
                "plan_work_mapping_status": "missing_reference",
                "budget_expense_mapping_status": "missing_reference",
                "db_import_status": "blocked_pending_confirmed_mapping",
                "elaas_assist_status": "preview_only"
            },
            "db_import_safe": False
        }

        evidence = {
            "source_file": row.get("source_file", ""),
            "source_sheet": row.get("source_sheet", ""),
            "source_hash": source_hash,
            "source_row": source_row,
            "column_evidence": {
                "work": {"column_index": 1, "raw_value": row.get("work", ""), "normalized_value": extracted["work"]},
                "appropriation_category": {"column_index": 2, "raw_value": row.get("appropriation_category", ""), "normalized_value": extracted["appropriation_category"]},
                "expense_type": {"column_index": 3, "raw_value": row.get("expense_type", ""), "normalized_value": extracted["expense_type"]},
                "approved_amount": {"column_index": 8, "raw_value": row.get("approved_amount"), "normalized_value": extracted["approved_amount"]},
                "remaining_amount": {"column_index": 14, "raw_value": row.get("remaining_amount"), "normalized_value": extracted["remaining_amount"]}
            }
        }

        return {
            "preview_row_id": preview_row_id,
            "source_row": source_row,
            "extracted": extracted,
            "placeholders": placeholders,
            "derived": derived,
            "evidence": evidence
        }
