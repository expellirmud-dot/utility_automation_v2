import hashlib
import re
from io import BytesIO
from typing import Any

import pandas as pd


HEADER_ALIASES = {
    "department": ("หน่วยงาน", "ส่วนราชการ", "สำนัก/กอง", "กอง/สำนัก"),
    "division": ("ฝ่าย/งาน", "งาน", "ฝ่าย", "ส่วนงาน"),
    "expense_type": ("ประเภทรายจ่าย", "กลุ่มค่าใช้จ่าย", "รายการ", "รายการงบประมาณ", "ค่าใช้จ่าย"),
    "appropriation_category": ("หมวดงบประมาณ", "หมวดรายจ่าย", "ประเภทงบ", "หมวด"),
    "initial_amount": ("งบตั้งต้น", "จำนวนเงิน", "งบประมาณตั้งไว้", "ยอดงบประมาณ", "เงินงบประมาณ"),
}

REQUIRED_FIELDS = ("department", "division", "expense_type", "appropriation_category", "initial_amount")


class BudgetImportService:
    @staticmethod
    def source_hash(file_content: bytes) -> str:
        return hashlib.sha256(file_content).hexdigest()

    @staticmethod
    def normalize_text(value: Any) -> str:
        if value is None or pd.isna(value):
            return ""
        return re.sub(r"\s+", " ", str(value)).strip()

    @staticmethod
    def normalize_key_part(value: Any) -> str:
        return BudgetImportService.normalize_text(value).casefold()

    @staticmethod
    def budget_key(
        fiscal_year_be: int,
        department: str,
        division: str,
        expense_type: str,
        appropriation_category: str,
    ) -> tuple:
        return (
            fiscal_year_be,
            BudgetImportService.normalize_key_part(department),
            BudgetImportService.normalize_key_part(division),
            BudgetImportService.normalize_key_part(expense_type),
            BudgetImportService.normalize_key_part(appropriation_category),
        )

    @staticmethod
    def list_sheet_names(file_content: bytes) -> list[str]:
        try:
            excel = pd.ExcelFile(BytesIO(file_content))
        except Exception as exc:
            raise ValueError(f"ไม่สามารถอ่านไฟล์ Excel ได้: {exc}")
        return list(excel.sheet_names)

    @staticmethod
    def _resolve_headers(columns: list[Any]) -> tuple[dict[str, str], list[str]]:
        normalized_columns = {BudgetImportService.normalize_text(col): col for col in columns}
        resolved: dict[str, str] = {}
        missing: list[str] = []

        for field, aliases in HEADER_ALIASES.items():
            matched = next((alias for alias in aliases if alias in normalized_columns), None)
            if matched:
                resolved[field] = normalized_columns[matched]
            else:
                missing.append(field)

        return resolved, missing

    @staticmethod
    def _parse_amount(value: Any) -> tuple[float | None, str | None]:
        if value is None or pd.isna(value):
            return None, "missing amount"
        if isinstance(value, (int, float)):
            amount = float(value)
        else:
            text = BudgetImportService.normalize_text(value)
            text = text.replace(",", "").replace("บาท", "").replace("฿", "").strip()
            try:
                amount = float(text)
            except ValueError:
                return None, f"invalid amount: {value}"
        if amount < 0:
            return None, "negative amount"
        return amount, None

    @staticmethod
    def preview_budget_lines(file_content: bytes, fiscal_year_be: int, sheet_name: str | None) -> dict:
        sheet_names = BudgetImportService.list_sheet_names(file_content)
        if not sheet_names:
            raise ValueError("ไม่พบ worksheet ในไฟล์ Excel")
        if not sheet_name:
            if len(sheet_names) == 1:
                sheet_name = sheet_names[0]
            else:
                return {
                    "valid": False,
                    "source_hash": BudgetImportService.source_hash(file_content),
                    "sheet_names": sheet_names,
                    "selected_sheet": None,
                    "rows": [],
                    "errors": ["กรุณาเลือก worksheet 1 รายการก่อน preview"],
                    "summary": {"row_count": 0, "total_initial_amount": 0.0},
                }
        if sheet_name not in sheet_names:
            raise ValueError(f"ไม่พบ worksheet: {sheet_name}")

        df = pd.read_excel(BytesIO(file_content), sheet_name=sheet_name)
        df.columns = [BudgetImportService.normalize_text(col) for col in df.columns]
        headers, missing = BudgetImportService._resolve_headers(df.columns.tolist())

        errors: list[str] = []
        if missing:
            errors.append("Missing required columns: " + ", ".join(missing))
            return {
                "valid": False,
                "source_hash": BudgetImportService.source_hash(file_content),
                "sheet_names": sheet_names,
                "selected_sheet": sheet_name,
                "rows": [],
                "errors": errors,
                "summary": {"row_count": 0, "total_initial_amount": 0.0},
            }

        rows: list[dict[str, Any]] = []
        seen_keys: dict[tuple, int] = {}
        total_amount = 0.0

        for idx, raw in df.iterrows():
            row_number = int(idx) + 2
            values = {
                "department": BudgetImportService.normalize_text(raw[headers["department"]]),
                "division": BudgetImportService.normalize_text(raw[headers["division"]]),
                "expense_type": BudgetImportService.normalize_text(raw[headers["expense_type"]]),
                "appropriation_category": BudgetImportService.normalize_text(raw[headers["appropriation_category"]]),
            }
            amount, amount_error = BudgetImportService._parse_amount(raw[headers["initial_amount"]])
            if not any(values.values()) and amount is None:
                continue

            row_errors: list[str] = []
            for required in ("department", "division", "expense_type", "appropriation_category"):
                if not values[required]:
                    row_errors.append(f"{required} is required")
            if amount_error:
                row_errors.append(amount_error)

            key = BudgetImportService.budget_key(
                fiscal_year_be,
                values["department"],
                values["division"],
                values["expense_type"],
                values["appropriation_category"],
            )
            if key in seen_keys:
                row_errors.append(f"duplicate row key also found at row {seen_keys[key]}")
            else:
                seen_keys[key] = row_number

            initial_amount = amount if amount is not None else 0.0
            total_amount += initial_amount
            rows.append({
                "row_number": row_number,
                **values,
                "initial_amount": initial_amount,
                "errors": row_errors,
                "valid": not row_errors,
            })
            errors.extend(f"row {row_number}: {error}" for error in row_errors)

        return {
            "valid": not errors and bool(rows),
            "source_hash": BudgetImportService.source_hash(file_content),
            "sheet_names": sheet_names,
            "selected_sheet": sheet_name,
            "rows": rows,
            "errors": errors or ([] if rows else ["ไม่พบรายการงบประมาณใน worksheet ที่เลือก"]),
            "summary": {"row_count": len(rows), "total_initial_amount": total_amount},
        }
