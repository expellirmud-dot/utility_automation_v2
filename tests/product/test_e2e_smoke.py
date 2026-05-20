import pytest
from fastapi.testclient import TestClient
from src.product.main import app
from src.product.db.models import Base
from src.product.db.session import engine
import datetime
import io

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "municipal-finance-product-api"}

def test_fiscal_year_and_budget_import():
    from src.product.db.models import FiscalYear
    from src.product.db.session import SessionLocal
    
    # 1. Seed Fiscal Year
    db = SessionLocal()
    fy = FiscalYear(year_be=2569, start_date=datetime.date(2025, 10, 1), end_date=datetime.date(2026, 9, 30), is_active=True)
    db.add(fy)
    db.commit()
    db.close()
    
    # 2. Test Excel Import
    import pandas as pd
    df = pd.DataFrame({
        'หน่วยงาน': ['สำนักปลัด', 'กองคลัง'],
        'ฝ่าย/งาน': ['งานธุรการ', 'งานการเงิน'],
        'ประเภทรายจ่าย': ['ค่าไฟฟ้า', 'ค่าโทรศัพท์'],
        'หมวดงบประมาณ': ['ค่าสาธารณูปโภค', 'ค่าสาธารณูปโภค'],
        'งบตั้งต้น': [120000.0, 95000.0]
    })
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    
    file_bytes = output.getvalue()
    
    preview = client.post(
        "/api/budget/import/preview",
        data={"fiscal_year_be": "2569", "sheet_name": "Sheet1"},
        files={"file": ("budget.xlsx", file_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    )
    assert preview.status_code == 200
    assert preview.json()["valid"] is True

    response = client.post(
        "/api/budget/import/commit",
        data={
            "fiscal_year_be": "2569",
            "sheet_name": "Sheet1",
            "source_hash": preview.json()["source_hash"],
        },
        files={"file": ("budget.xlsx", file_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    )
    assert response.status_code == 200
    assert response.json()["lines_processed"] == 2
    
    # 3. Test Budget List
    list_res = client.get("/api/budget/")
    assert list_res.status_code == 200
    budgets = list_res.json()
    assert len(budgets) == 2
    assert budgets[0]["department"] == "สำนักปลัด"
    
def test_create_and_list_cases():
    # 1. Create case
    case_payload = {
        "fiscal_year_be": 2569,
        "work_month": "มีนาคม",
        "case_type": "utility",
        "expense_group": "ค่าไฟฟ้า",
        "department": "กองคลัง",
        "division": "งานการเงิน",
        "note": "ทดสอบ"
    }
    
    create_res = client.post("/api/cases/", json=case_payload)
    assert create_res.status_code == 200
    created_case = create_res.json()
    assert created_case["case_number"] == "CASE-2569-0001"
    assert created_case["work_month"] == "มีนาคม"
    assert created_case["status"] == "draft"
    
    # 2. List cases
    list_res = client.get("/api/cases/")
    assert list_res.status_code == 200
    cases = list_res.json()
    assert len(cases) >= 1
    assert any(c["case_number"] == "CASE-2569-0001" for c in cases)
