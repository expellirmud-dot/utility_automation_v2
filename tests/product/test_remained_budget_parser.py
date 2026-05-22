import pytest
import pandas as pd
from io import BytesIO
from src.product.services.remained_budget_parser import RemainedBudgetParser

def create_mock_excel(rows_data, sheet_name="reportRemainBudgetXlsx"):
    # The real file has 15 columns (0 to 14)
    # Col indices: 0:NaN, 1:work, 2:app_cat, 3:exp_type, 4:dept, 5:budget_code, 6:project, 7:NaN, 8:approved, 9:trans_in, 10:trans_out, 11:oblg, 12:disb, 13:status, 14:rem
    
    full_rows = []
    for rd in rows_data:
        row = [None] * 15
        row[1] = rd.get("work")
        row[2] = rd.get("appropriation_category")
        row[3] = rd.get("expense_type")
        row[4] = rd.get("department")
        row[5] = rd.get("budget_code")
        row[6] = rd.get("project")
        row[8] = rd.get("approved_amount")
        row[9] = rd.get("transfer_in")
        row[10] = rd.get("transfer_out")
        row[11] = rd.get("obligated_amount")
        row[12] = rd.get("disbursed_amount")
        row[13] = rd.get("data_status")
        row[14] = rd.get("remaining_amount")
        full_rows.append(row)
    
    df_data = pd.DataFrame(full_rows)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Header at row 8 (index 7).
        # We write the data starting at row 9 (index 8).
        # We don't need a real header for index-based parsing, but the parser reads from index 8.
        df_data.to_excel(writer, sheet_name=sheet_name, index=False, header=False, startrow=8)
        
        # We need to ensure rows 0-7 exist so the parser doesn't crash when reading metadata
        # Pandas to_excel with startrow=8 will leave 0-7 as empty if the sheet is new.
        # But let's be explicit about metadata for the parser to find.
        ws = writer.book[sheet_name]
        ws.cell(row=2, column=2, value="วันที่พิมพ์ : 22/05/2567 17:54") # Row 2, Col 2 (index 1, 1)
        ws.cell(row=4, column=2, value="ปีงบประมาณ 2567") # Row 4, Col 2 (index 3, 1)
        ws.cell(row=5, column=2, value="เทศบาล A") # Row 5, Col 2 (index 4, 1)
        
    return output.getvalue()

def test_remained_budget_parser_success():
    data = [
        {
            "work": "ปรับปรุงถนน",
            "appropriation_category": "ค่าสาธารณูปโภค",
            "expense_type": "ค่าไฟฟ้า",
            "department": "กองช่าง",
            "budget_code": "12345",
            "approved_amount": 1000.0,
            "transfer_in": 100.0,
            "transfer_out": 50.0,
            "obligated_amount": 200.0,
            "disbursed_amount": 100.0,
            "remaining_amount": 750.0,
            "data_status": "ปกติ",
        },
        {
            "work": "รวม", # Should be skipped
            "appropriation_category": "ค่าสาธารณูปโภค",
            "expense_type": "ค่าไฟฟ้า",
            "department": "กองช่าง",
            "budget_code": "12345",
            "approved_amount": 1000.0,
            "transfer_in": 100.0,
            "transfer_out": 50.0,
            "obligated_amount": 200.0,
            "disbursed_amount": 100.0,
            "remaining_amount": 750.0,
            "data_status": "ปกติ",
        },
        {
            "work": "ติดตั้งไฟ",
            "appropriation_category": "ค่าสาธารณูปโภค",
            "expense_type": "ค่าประปา",
            "department": None, # Should become "รอข้อมูลจริง"
            "budget_code": "67890.0", # Test float to string
            "approved_amount": 2000.0,
            "transfer_in": 0,
            "transfer_out": 0,
            "obligated_amount": 500,
            "disbursed_amount": 300,
            "remaining_amount": 1200,
            "data_status": "ปกติ",
        }
    ]
    
    excel_content = create_mock_excel(data)
    results = RemainedBudgetParser.parse_preview(excel_content)
    
    assert len(results) == 2
    
    # Row 1
    row1 = results[0]
    assert row1["source_row"] == 9
    assert row1["department"] == "กองช่าง"
    assert row1["withholding_tax"] is False # ค่าไฟฟ้า -> False
    assert row1["budget_code"] == "12345"
    assert row1["approved_amount"] == 1000.0
    
    # Row 2 (The 3rd data row in excel)
    row2 = results[1]
    assert row2["source_row"] == 11
    assert row2["department"] == "รอข้อมูลจริง"
    assert row2["withholding_tax"] is True # ค่าสาธารณูปโภค and NOT ค่าไฟฟ้า -> True
    assert row2["budget_code"] == "67890"
    assert row2["approved_amount"] == 2000.0


def test_remained_budget_parser_withholding_tax_logic():
    cases = [
        ("ค่าไฟฟ้า", "ค่าสาธารณูปโภค", False),
        ("ค่าประปา", "ค่าสาธารณูปโภค", True),
        ("ค่าซ่อมแซม", "ค่าใช้สอย", None),
    ]
    
    for et, ac, expected in cases:
        assert RemainedBudgetParser._determine_withholding_tax(et, ac) == expected

def test_remained_budget_parser_invalid_sheet():
    # Create excel with different sheet name
    data = [{"work": "test"}]
    excel_content = create_mock_excel(data, sheet_name="WrongSheet")
    
    with pytest.raises(ValueError, match="Failed to read sheet reportRemainBudgetXlsx"):
        RemainedBudgetParser.parse_preview(excel_content)
