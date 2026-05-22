import re
import pandas as pd
from io import BytesIO
from typing import List, Dict, Any, Optional


class RemainedBudgetParser:
    SHEET_NAME = "reportRemainBudgetXlsx"
    HEADER_ROW = 7  # Row 8 (0-indexed)
    DATA_START_ROW = HEADER_ROW + 1

    # Column Mapping
    COL_WORK = 1
    COL_APPROPRIATION_CATEGORY = 2
    COL_EXPENSE_TYPE = 3
    COL_PROJECT = 4
    COL_BUDGET_CODE = 5
    COL_APPROVED_AMOUNT = 8
    COL_TRANSFER_IN = 9
    COL_TRANSFER_OUT = 10
    COL_OBLIGATED_AMOUNT = 11
    COL_DISBURSED_AMOUNT = 12
    COL_REMAINING_AMOUNT = 14

    @staticmethod
    def _parse_amount(value: Any) -> Optional[float]:
        if value is None or pd.isna(value):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        
        try:
            text = str(value).replace(",", "").replace("บาท", "").replace("฿", "").strip()
            return float(text)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _determine_withholding_tax(expense_type: str, appropriation_category: str) -> Optional[bool]:
        if expense_type == "ค่าไฟฟ้า":
            return False
        if appropriation_category == "ค่าสาธารณูปโภค":
            return True
        return None

    @classmethod
    def _extract_metadata(cls, df_raw: pd.DataFrame) -> Dict[str, Any]:
        metadata = {
            "printed_month": "",
            "fiscal_year_be": None,
            "municipality": ""
        }
        try:
            # Row 2, Col 2 (index 1, 1): "วันที่พิมพ์ : 22/05/2569 17:54"
            row1_col1 = str(df_raw.iloc[1, 1] or "").strip()
            date_match = re.search(r"(\d{2})/(\d{2})/(\d{4})", row1_col1)
            if date_match:
                month_num = date_match.group(2)
                months = {
                    "01": "มกราคม", "02": "กุมภาพันธ์", "03": "มีนาคม", "04": "เมษายน",
                    "05": "พฤษภาคม", "06": "มิถุนายน", "07": "กรกฎาคม", "08": "สิงหาคม",
                    "09": "กันยายน", "10": "ตุลาคม", "11": "พฤศจิกายน", "12": "ธันวาคม"
                }
                metadata["printed_month"] = months.get(month_num, "")

            # Row 4, Col 2 (index 3, 1): "ปีงบประมาณ ... 2569"
            row3_col1 = str(df_raw.iloc[3, 1] or "").strip()
            year_match = re.search(r"(\d{4})", row3_col1)
            if year_match:
                metadata["fiscal_year_be"] = int(year_match.group(1))

            # Row 5, Col 2 (index 4, 1): "เทศบาลตำบลด่านทับตะโก"
            metadata["municipality"] = str(df_raw.iloc[4, 1] or "").strip()
        except Exception:
            pass
        return metadata

    @classmethod
    def parse_preview(cls, file_content: bytes, source_file_name: str = "B_RemainedBudget.xlsx") -> List[Dict[str, Any]]:
        try:
            df_raw = pd.read_excel(
                BytesIO(file_content), 
                sheet_name=cls.SHEET_NAME, 
                header=None
            )
        except Exception as e:
            raise ValueError(f"Failed to read sheet {cls.SHEET_NAME}: {e}")

        metadata = cls._extract_metadata(df_raw)
        
        results = []
        for idx in range(cls.DATA_START_ROW, len(df_raw)):
            row = df_raw.iloc[idx]
            source_row = idx + 1
            
            def get_val(col_idx):
                val = row[col_idx]
                return None if pd.isna(val) else val

            work_val = get_val(cls.COL_WORK)
            work = str(work_val or "").strip()
            if not work or work.startswith("รวม"):
                continue
                
            app_cat = str(get_val(cls.COL_APPROPRIATION_CATEGORY) or "").strip()
            exp_type = str(get_val(cls.COL_EXPENSE_TYPE) or "").strip()
            
            # Strict correction: department, plan, and budget as "รอข้อมูลจริง"
            dept = "รอข้อมูลจริง"
            plan = "รอข้อมูลจริง"
            budget = "รอข้อมูลจริง"
            
            budget_code_val = get_val(cls.COL_BUDGET_CODE)
            if budget_code_val is None or pd.isna(budget_code_val):
                budget_code = ""
            else:
                budget_code = str(budget_code_val).strip()
                if budget_code.endswith(".0"):
                    budget_code = budget_code[:-2]

            row_data = {
                "source_row": source_row,
                "fiscal_year_be": metadata["fiscal_year_be"],
                "printed_month": metadata["printed_month"],
                "municipality": metadata["municipality"],
                "department": dept,
                "plan": plan,
                "work": work,
                "budget": budget,
                "appropriation_category": app_cat,
                "expense_type": exp_type,
                "project": str(get_val(cls.COL_PROJECT) or "").strip(),
                "budget_code": budget_code,
                "approved_amount": cls._parse_amount(get_val(cls.COL_APPROVED_AMOUNT)),
                "transfer_in": cls._parse_amount(get_val(cls.COL_TRANSFER_IN)),
                "transfer_out": cls._parse_amount(get_val(cls.COL_TRANSFER_OUT)),
                "obligated_amount": cls._parse_amount(get_val(cls.COL_OBLIGATED_AMOUNT)),
                "disbursed_amount": cls._parse_amount(get_val(cls.COL_DISBURSED_AMOUNT)),
                "remaining_amount": cls._parse_amount(get_val(cls.COL_REMAINING_AMOUNT)),
                "withholding_tax": cls._determine_withholding_tax(exp_type, app_cat),
                "data_status": str(get_val(13) or "").strip(), # Preserving index 13 for status
                "source_file": source_file_name,
                "source_sheet": cls.SHEET_NAME,
            }
            results.append(row_data)
            
        return results

