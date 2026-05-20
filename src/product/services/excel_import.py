import pandas as pd
from io import BytesIO
from typing import List, Dict, Any

class ExcelImportService:
    @staticmethod
    def parse_budget_lines(file_content: bytes) -> List[Dict[str, Any]]:
        """
        Parses an uploaded Excel file to extract budget line items.
        Assumes the municipal workbook structure contains columns:
        'หน่วยงาน' (Department), 'ฝ่าย/งาน' (Division), 'ประเภทรายจ่าย' (Expense Type), 'งบตั้งต้น' (Initial Amount)
        """
        try:
            # Read Excel file
            df = pd.read_excel(BytesIO(file_content))
            
            # Expected columns in the Thai municipal template
            expected_columns = ['หน่วยงาน', 'ฝ่าย/งาน', 'ประเภทรายจ่าย', 'งบตั้งต้น']
            
            # Clean column names (strip whitespace)
            df.columns = df.columns.str.strip()
            
            # Check if all expected columns are present
            missing_cols = [col for col in expected_columns if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns in Excel file: {', '.join(missing_cols)}")
                
            # Filter and clean data
            # Drop rows where 'ประเภทรายจ่าย' is NaN
            df = df.dropna(subset=['ประเภทรายจ่าย'])
            
            # Fill NaN in division with empty string or 'ทั่วไป'
            df['ฝ่าย/งาน'] = df['ฝ่าย/งาน'].fillna('-')
            df['หน่วยงาน'] = df['หน่วยงาน'].fillna('ไม่ระบุ')
            
            # Convert to dict
            records = df.to_dict('records')
            
            budget_lines = []
            for row in records:
                budget_lines.append({
                    "department": str(row['หน่วยงาน']).strip(),
                    "division": str(row['ฝ่าย/งาน']).strip(),
                    "expense_type": str(row['ประเภทรายจ่าย']).strip(),
                    "initial_amount": float(row['งบตั้งต้น']) if pd.notna(row['งบตั้งต้น']) else 0.0
                })
                
            return budget_lines
            
        except Exception as e:
            raise ValueError(f"Failed to parse Excel file: {str(e)}")
