import datetime

import pytest
from fastapi.testclient import TestClient

from src.product.db.models import Base, BudgetLine, Case, ExpenseLedger, FiscalYear
from src.product.db.session import SessionLocal, engine
from src.product.main import app
from src.product.services.readiness_validator import ReadinessValidator


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


def _fy(db):
    fy = FiscalYear(
        year_be=2569,
        start_date=datetime.date(2025, 10, 1),
        end_date=datetime.date(2026, 9, 30),
    )
    db.add(fy)
    db.commit()
    db.refresh(fy)
    return fy


def _case(db):
    case = Case(
        case_number="BUDGET-MATCH-001",
        fiscal_year_be=2569,
        work_month="พฤษภาคม",
        case_type="utility",
        expense_group="ค่าไฟฟ้า",
        department="สำนักปลัด",
        division="งานธุรการ",
        total_amount=3000.0,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def _budget_line(db, fy, category="ค่าสาธารณูปโภค", amount=10000.0):
    line = BudgetLine(
        fiscal_year_id=fy.id,
        department="สำนักปลัด",
        division="งานธุรการ",
        expense_type="ค่าไฟฟ้า",
        appropriation_category=category,
        initial_amount=amount,
    )
    db.add(line)
    db.commit()
    db.refresh(line)
    return line


def test_case_budget_match_returns_single_match_with_real_available_balance(db):
    fy = _fy(db)
    case = _case(db)
    line = _budget_line(db, fy)
    db.add(ExpenseLedger(budget_line_id=line.id, case_id=999, amount_deducted=2500.0))
    db.commit()

    response = client.get(f"/api/budget/cases/{case.id}/match")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "matched"
    assert payload["selected"]["available_amount"] == 7500.0


def test_case_budget_match_returns_ambiguous_candidates(db):
    fy = _fy(db)
    case = _case(db)
    _budget_line(db, fy, category="ค่าสาธารณูปโภค")
    _budget_line(db, fy, category="เงินกันไว้เบิกเหลื่อมปี")

    response = client.get(f"/api/budget/cases/{case.id}/match")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ambiguous"
    assert len(payload["candidates"]) == 2


def test_manual_budget_selection_overrides_ambiguous_match(db):
    fy = _fy(db)
    case = _case(db)
    first = _budget_line(db, fy, category="ค่าสาธารณูปโภค")
    selected = _budget_line(db, fy, category="เงินกันไว้เบิกเหลื่อมปี")

    response = client.post(
        f"/api/budget/cases/{case.id}/selection",
        json={"budget_line_id": selected.id},
    )
    assert response.status_code == 200
    assert response.json()["budget_line_id"] == selected.id

    match = client.get(f"/api/budget/cases/{case.id}/match").json()
    assert match["status"] == "selected"
    assert match["selected"]["id"] == selected.id
    assert match["selected"]["id"] != first.id


def test_readiness_uses_selected_budget_line_when_auto_match_is_ambiguous(db):
    fy = _fy(db)
    case = _case(db)
    _budget_line(db, fy, category="ค่าสาธารณูปโภค", amount=1000.0)
    selected = _budget_line(db, fy, category="เงินกันไว้เบิกเหลื่อมปี", amount=5000.0)
    case.budget_line_id = selected.id
    db.commit()
    db.refresh(case)

    result = ReadinessValidator.validate_budget(case, db)

    assert result["budget_ok"] is True
    assert result["available_budget"] == 5000.0
