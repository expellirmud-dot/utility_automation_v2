import pytest
from src.product.services.excel_import import ExcelImportService
import pandas as pd
import io

def test_excel_import_parse_budget_lines():
    # Create a mock Excel file in memory
    df = pd.DataFrame({
        'หน่วยงาน': ['สำนักปลัด', 'กองคลัง'],
        'ฝ่าย/งาน': ['งานธุรการ', 'งานการเงิน'],
        'ประเภทรายจ่าย': ['ค่าไฟฟ้า', 'ค่าโทรศัพท์'],
        'งบตั้งต้น': [120000.0, 95000.0]
    })
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    
    excel_bytes = output.getvalue()
    
    # Parse the bytes
    budget_lines = ExcelImportService.parse_budget_lines(excel_bytes)
    
    assert len(budget_lines) == 2
    assert budget_lines[0]['department'] == 'สำนักปลัด'
    assert budget_lines[0]['expense_type'] == 'ค่าไฟฟ้า'
    assert budget_lines[0]['initial_amount'] == 120000.0

def test_excel_import_missing_columns():
    df = pd.DataFrame({
        'หน่วยงาน': ['สำนักปลัด'],
        # 'ฝ่าย/งาน' missing
        'ประเภทรายจ่าย': ['ค่าไฟฟ้า'],
        'งบตั้งต้น': [120000.0]
    })
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    
    excel_bytes = output.getvalue()
    
    with pytest.raises(ValueError, match="Missing required columns"):
        ExcelImportService.parse_budget_lines(excel_bytes)
