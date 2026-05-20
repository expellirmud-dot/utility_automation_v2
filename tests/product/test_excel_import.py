import io

import pandas as pd
import pytest

from src.product.services.excel_import import ExcelImportService


def _excel_bytes(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()


def test_excel_import_parse_budget_lines():
    df = pd.DataFrame({
        "หน่วยงาน": ["สำนักปลัด", "กองคลัง"],
        "ฝ่าย/งาน": ["งานธุรการ", "งานการเงิน"],
        "ประเภทรายจ่าย": ["ค่าไฟฟ้า", "ค่าโทรศัพท์"],
        "หมวดงบประมาณ": ["ค่าสาธารณูปโภค", "ค่าสาธารณูปโภค"],
        "งบตั้งต้น": [120000.0, 95000.0],
    })

    budget_lines = ExcelImportService.parse_budget_lines(_excel_bytes(df))

    assert len(budget_lines) == 2
    assert budget_lines[0]["department"] == "สำนักปลัด"
    assert budget_lines[0]["expense_type"] == "ค่าไฟฟ้า"
    assert budget_lines[0]["appropriation_category"] == "ค่าสาธารณูปโภค"
    assert budget_lines[0]["initial_amount"] == 120000.0


def test_excel_import_missing_columns():
    df = pd.DataFrame({
        "หน่วยงาน": ["สำนักปลัด"],
        "ประเภทรายจ่าย": ["ค่าไฟฟ้า"],
        "งบตั้งต้น": [120000.0],
    })

    with pytest.raises(ValueError, match="Missing required columns"):
        ExcelImportService.parse_budget_lines(_excel_bytes(df))
