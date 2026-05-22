import pytest
import pandas as pd
from io import BytesIO
from src.product.services.remained_budget_parser import RemainedBudgetParser

def create_mock_excel(rows_data, sheet_name="reportRemainBudgetXlsx"):
    # Column indices (0-14):
    # 1:work, 2:app_cat, 3:exp_type, 4:project, 5:budget_code, 8:approved, 9:trans_in, 10:trans_out, 11:oblg, 12:disb, 14:rem
    full_rows = []
    for rd in rows_data:
        row = [None] * 15
        row[1] = rd.get("work")
        row[2] = rd.get("appropriation_category")
        row[3] = rd.get("expense_type")
        row[4] = rd.get("project")
        row[5] = rd.get("budget_code")
        row[8] = rd.get("approved_amount")
        row[9] = rd.get("transfer_in")
        row[10] = rd.get("transfer_out")
        row[11] = rd.get("obligated_amount")
        row[12] = rd.get("disbursed_amount")
        row[14] = rd.get("remaining_amount")
        full_rows.append(row)
    
    df_data = pd.DataFrame(full_rows)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_data.to_excel(writer, sheet_name=sheet_name, index=False, header=False, startrow=8)
        ws = writer.book[sheet_name]
        ws.cell(row=2, column=2, value="วันที่พิมพ์ : 22/05/2569 17:54")
        ws.cell(row=4, column=2, value="ปีงบประมาณ 2569")
        ws.cell(row=5, column=2, value="เทศบาลตำบลด่านทับตะโก")
    return output.getvalue()

def test_remained_budget_parser_success():
    data = [
        {
            "work": "ค่าไฟฟ้า กพ.",
            "appropriation_category": "ค่าสาธารณูปโภค",
            "expense_type": "ค่าไฟฟ้า",
            "project": "โครงการไฟฟ้า",
            "budget_code": "12345",
            "approved_amount": "1,000.00 บาท",
            "transfer_in": 100,
            "transfer_out": 50,
            "obligated_amount": 200,
            "disbursed_amount": 100,
            "remaining_amount": 750,
        },
        {
            "work": "รวมค่าไฟฟ้า", # Should be skipped
            "appropriation_category": "ค่าสาธารณูปโภค",
            "expense_type": "ค่าไฟฟ้า",
            "project": "โครงการไฟฟ้า",
            "budget_code": "12345",
            "approved_amount": 1000,
            "transfer_in": 0,
            "transfer_out": 0,
            "obligated_amount": 0,
            "disbursed_amount": 0,
            "remaining_amount": 0,
        },
        {
            "work": "ค่าประปา มีค.",
            "appropriation_category": "ค่าสาธารณูปโภค",
            "expense_type": "ค่าประปา",
            "project": "โครงการประปา",
            "budget_code": "67890.0",
            "approved_amount": 2000.0,
            "transfer_in": 0,
            "transfer_out": 0,
            "obligated_amount": 500,
            "disbursed_amount": 300,
            "remaining_amount": "1,200.00 ฿",
        },
        {
            "work": "ค่าซ่อมแซม",
            "appropriation_category": "ค่าใช้สอย",
            "expense_type": "ซ่อมบำรุง",
            "project": "โครงการซ่อม",
            "budget_code": "ABC-123",
            "approved_amount": 5000,
            "transfer_in": 0,
            "transfer_out": 0,
            "obligated_amount": 0,
            "disbursed_amount": 0,
            "remaining_amount": 5000,
        }
    ]
    
    excel_content = create_mock_excel(data)
    results = RemainedBudgetParser.parse_preview(excel_content)
    
    assert len(results) == 3
    
    # Row 1: ค่าไฟฟ้า
    row1 = results[0]
    assert row1["work"] == "ค่าไฟฟ้า กพ."
    assert row1["department"] == "รอข้อมูลจริง"
    assert row1["plan"] == "รอข้อมูลจริง"
    assert row1["budget"] == "รอข้อมูลจริง"
    assert row1["withholding_tax"] is False
    assert row1["approved_amount"] == 1000.0
    assert row1["fiscal_year_be"] == 2569
    assert row1["printed_month"] == "พฤษภาคม"
    assert row1["municipality"] == "เทศบาลตำบลด่านทับตะโก"
    
    # Row 2: ค่าประปา
    row2 = results[1]
    assert row2["work"] == "ค่าประปา มีค."
    assert row2["withholding_tax"] is True
    assert row2["budget_code"] == "67890"
    assert row2["remaining_amount"] == 1200.0
    
    # Row 3: Non-utility
    row3 = results[2]
    assert row3["work"] == "ค่าซ่อมแซม"
    assert row3["withholding_tax"] is None
    assert row3["budget_code"] == "ABC-123"

def test_remained_budget_parser_withholding_tax_logic():
    cases = [
        ("ค่าไฟฟ้า", "ค่าสาธารณูปโภค", False),
        ("ค่าประปา", "ค่าสาธารณูปโภค", True),
        ("ค่าซ่อมแซม", "ค่าใช้สอย", None),
        ("", "ค่าสาธารณูปโภค", True),
    ]
    for et, ac, expected in cases:
        assert RemainedBudgetParser._determine_withholding_tax(et, ac) == expected

def test_remained_budget_parser_invalid_sheet():
    data = [{"work": "test"}]
    excel_content = create_mock_excel(data, sheet_name="WrongSheet")
    with pytest.raises(ValueError, match="Failed to read sheet reportRemainBudgetXlsx"):
        RemainedBudgetParser.parse_preview(excel_content)
