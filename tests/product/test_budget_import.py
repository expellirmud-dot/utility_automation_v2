import datetime
import io

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.product.db.models import Base, BudgetLine, FiscalYear
from src.product.db.session import SessionLocal, engine
from src.product.main import app
from src.product.services.budget_import import BudgetImportService


client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _seed_fiscal_year(db):
    fy = FiscalYear(
        year_be=2569,
        start_date=datetime.date(2025, 10, 1),
        end_date=datetime.date(2026, 9, 30),
        is_active=True,
    )
    db.add(fy)
    db.commit()
    db.refresh(fy)
    return fy


def _excel_bytes(df: pd.DataFrame, sheet_name: str = "งบประมาณ") -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return output.getvalue()


def _budget_df(**overrides):
    data = {
        "หน่วยงาน": ["สำนักปลัด", "กองคลัง"],
        "ฝ่าย/งาน": ["งานธุรการ", "งานการเงิน"],
        "ประเภทรายจ่าย": ["ค่าไฟฟ้า", "ค่าโทรศัพท์"],
        "หมวดงบประมาณ": ["ค่าสาธารณูปโภค", "ค่าสาธารณูปโภค"],
        "งบตั้งต้น": [120000.0, 95000.0],
    }
    data.update(overrides)
    return pd.DataFrame(data)


def test_preview_parses_canonical_thai_headers_without_db_mutation(db):
    _seed_fiscal_year(db)
    content = _excel_bytes(_budget_df())

    response = client.post(
        "/api/budget/import/preview",
        data={"fiscal_year_be": "2569", "sheet_name": "งบประมาณ"},
        files={"file": ("budget.xlsx", content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["valid"] is True
    assert payload["summary"]["row_count"] == 2
    assert payload["rows"][0]["appropriation_category"] == "ค่าสาธารณูปโภค"
    assert db.query(BudgetLine).count() == 0


def test_preview_requires_single_selected_sheet_when_workbook_has_multiple_sheets(db):
    _seed_fiscal_year(db)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        _budget_df().to_excel(writer, index=False, sheet_name="SheetA")
        _budget_df().to_excel(writer, index=False, sheet_name="SheetB")

    response = client.post(
        "/api/budget/import/preview",
        data={"fiscal_year_be": "2569"},
        files={"file": ("budget.xlsx", output.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["valid"] is False
    assert payload["sheet_names"] == ["SheetA", "SheetB"]
    assert "เลือก worksheet" in payload["errors"][0]


def test_preview_rejects_duplicate_rows_inside_same_file(db):
    _seed_fiscal_year(db)
    df = _budget_df(
        **{
            "หน่วยงาน": ["สำนักปลัด", "สำนักปลัด"],
            "ฝ่าย/งาน": ["งานธุรการ", "งานธุรการ"],
            "ประเภทรายจ่าย": ["ค่าไฟฟ้า", "ค่าไฟฟ้า"],
            "หมวดงบประมาณ": ["ค่าสาธารณูปโภค", "ค่าสาธารณูปโภค"],
            "งบตั้งต้น": [120000.0, 130000.0],
        }
    )

    preview = BudgetImportService.preview_budget_lines(_excel_bytes(df), 2569, "งบประมาณ")

    assert preview["valid"] is False
    assert any("duplicate row key" in error for error in preview["errors"])


def test_preview_rejects_invalid_amount(db):
    preview = BudgetImportService.preview_budget_lines(
        _excel_bytes(_budget_df(**{"งบตั้งต้น": ["not-a-number", 95000.0]})),
        2569,
        "งบประมาณ",
    )

    assert preview["valid"] is False
    assert any("invalid amount" in error for error in preview["errors"])


def test_commit_creates_then_deterministically_updates_existing_budget_lines(db):
    _seed_fiscal_year(db)
    content = _excel_bytes(_budget_df())
    source_hash = BudgetImportService.source_hash(content)

    first = client.post(
        "/api/budget/import/commit",
        data={"fiscal_year_be": "2569", "sheet_name": "งบประมาณ", "source_hash": source_hash},
        files={"file": ("budget.xlsx", content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert first.status_code == 200
    assert first.json()["created"] == 2
    assert first.json()["updated"] == 0

    updated_content = _excel_bytes(_budget_df(**{"งบตั้งต้น": [111000.0, 99000.0]}))
    updated_hash = BudgetImportService.source_hash(updated_content)
    second = client.post(
        "/api/budget/import/commit",
        data={"fiscal_year_be": "2569", "sheet_name": "งบประมาณ", "source_hash": updated_hash},
        files={"file": ("budget.xlsx", updated_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )

    assert second.status_code == 200
    assert second.json()["created"] == 0
    assert second.json()["updated"] == 2
    assert db.query(BudgetLine).count() == 2
    assert db.query(BudgetLine).filter(BudgetLine.department == "สำนักปลัด").one().initial_amount == 111000.0


def test_commit_requires_matching_preview_hash(db):
    _seed_fiscal_year(db)
    response = client.post(
        "/api/budget/import/commit",
        data={"fiscal_year_be": "2569", "sheet_name": "งบประมาณ", "source_hash": "bad-hash"},
        files={"file": ("budget.xlsx", _excel_bytes(_budget_df()), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )

    assert response.status_code == 400
    assert "source hash" in response.json()["detail"]
