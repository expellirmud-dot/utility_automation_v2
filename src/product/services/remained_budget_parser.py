import pandas as pd
from io import BytesIO
from typing import List, Dict, Any, Optional


class RemainedBudgetParser:
    SHEET_NAME = "reportRemainBudgetXlsx"
    HEADER_ROW = 7  # Row 8 (0-indexed)

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
    def parse_preview(cls, file_content: bytes, source_file_name: str = "B_RemainedBudget.xlsx") -> List[Dict[str, Any]]:
        try:
            # Read the entire sheet without headers first to extract metadata from top rows
            df_raw = pd.read_excel(
                BytesIO(file_content), 
                sheet_name=cls.SHEET_NAME, 
                header=None
            )
        except Exception as e:
            raise ValueError(f"Failed to read sheet {cls.SHEET_NAME}: {e}")

        # Metadata Extraction
        # Row 1: Printed Date (index 1)
        # Row 3: Fiscal Year (index 3)
        # Row 4: Municipality (index 4)
        
        printed_month = ""
        fiscal_year_be = None
        municipality = ""

        try:
            # Row 1, Col 1: "วันที่พิมพ์ : 22/05/2569 17:54"
            row1_col1 = str(df_raw.iloc[1, 1] or "").strip()
            # print(f"DEBUG: row1_col1 = {row1_col1}")
            if "/" in row1_col1:
                parts = row1_col1.split(":")
                date_part = parts[1].strip().split(" ")[0] if len(parts) > 1 else row1_col1.split("/")[0]
                # Try to extract just the date part: DD/MM/YYYY
                import re as re_meta
                date_match = re_meta.search(r"(\d{2})/(\d{2})/(\d{4})", row1_col1)
                if date_match:
                    month_num = date_match.group(2)
                    months = {
                        "01": "มกราคม", "02": "กุมภาพันธ์", "03": "มีนาคม", "04": "เมษายน",
                        "05": "พฤษภาคม", "06": "มิถุนายน", "07": "กรกฎาคม", "08": "สิงหาคม",
                        "09": "กันยายน", "10": "ตุลาคม", "11": "พฤศจิกายน", "12": "ธันวาคม"
                    }
                    printed_month = months.get(month_num, "")

            # Row 3, Col 1: "ปีงบประมาณ ... 2569"
            row3_col1 = str(df_raw.iloc[3, 1] or "").strip()
            # print(f"DEBUG: row3_col1 = {row3_col1}")
            year_match = re_meta.search(r"(\d{4})", row3_col1)
            if year_match:
                fiscal_year_be = int(year_match.group(1))

            # Row 4, Col 1: "เทศบาลตำบลด่านทับตะโก"
            municipality = str(df_raw.iloc[4, 1] or "").strip()
            # print(f"DEBUG: municipality = {municipality}")
        except Exception as e:
            # print(f"DEBUG: metadata error = {e}")
            pass

        results = []
        # Data starts at row 9 (index 8). Header is row 8 (index 7).
        # We iterate from index 8 onwards.
        for idx in range(8, len(df_raw)):
            row = df_raw.iloc[idx]
            source_row = idx + 1
            
            def get_val(col_idx):
                val = row[col_idx]
                return None if pd.isna(val) else val

            work_val = get_val(1)
            work = str(work_val or "").strip()
            if not work or work.startswith("รวม"):
                continue
                
            # Based on analysis of B_RemainedBudget.xlsx:
            # Col 1: work
            # Col 2: appropriation_category
            # Col 3: expense_type
            # Col 4: department
            # Col 5: budget_code
            # Col 8: approved_amount
            # Col 9: transfer_in
            # Col 10: transfer_out
            # Col 11: obligated_amount
            # Col 12: disbursed_amount
            # Col 14: remaining_amount
            
            app_cat = str(get_val(2) or "").strip()
            exp_type = str(get_val(3) or "").strip()
            
            dept_val = get_val(4)
            dept = str(dept_val or "").strip()
            if not dept:
                dept = "รอข้อมูลจริง"
            
            # Plan and Budget are not clearly distinct columns in this layout
            plan = "รอข้อมูลจริง"
            budget = "รอข้อมูลจริง"
            
            budget_code_val = get_val(5)
            if budget_code_val is None or pd.isna(budget_code_val):
                budget_code = ""
            else:
                budget_code = str(budget_code_val).strip()
                if budget_code.endswith(".0"):
                    budget_code = budget_code[:-2]

            row_data = {
                "source_row": source_row,
                "fiscal_year_be": fiscal_year_be,
                "printed_month": printed_month,
                "municipality": municipality,
                "department": dept,
                "plan": plan,
                "work": work,
                "budget": budget,
                "appropriation_category": app_cat,
                "expense_type": exp_type,
                "project": str(get_val(6) or "").strip(), # Attempt to use Col 6 for project
                "budget_code": budget_code,
                "approved_amount": cls._parse_amount(get_val(8)),
                "transfer_in": cls._parse_amount(get_val(9)),
                "transfer_out": cls._parse_amount(get_val(10)),
                "obligated_amount": cls._parse_amount(get_val(11)),
                "disbursed_amount": cls._parse_amount(get_val(12)),
                "remaining_amount": cls._parse_amount(get_val(14)),
                "withholding_tax": cls._determine_withholding_tax(exp_type, app_cat),
                "data_status": str(get_val(13) or "").strip(), # Attempt to use Col 13 for status
                "source_file": source_file_name,
                "source_sheet": cls.SHEET_NAME,
            }
            results.append(row_data)
            
        return results

