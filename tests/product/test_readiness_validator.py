import pytest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.product.db.models import Base, Case, BillHeader, SourceDocument, Dika, Memo, BudgetLine, FiscalYear, ExpenseLedger
from src.product.services.readiness_validator import ReadinessValidator

engine = create_engine("sqlite:///:memory:")
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_check_documents(db_session):
    case = Case(case_number="CASE-001")
    db_session.add(case)
    db_session.commit()

    assert ReadinessValidator.check_documents(case) == False

    doc = SourceDocument(case_id=case.id, file_name="test.pdf")
    db_session.add(doc)
    db_session.commit()

    assert ReadinessValidator.check_documents(case) == True

def test_check_ocr_status(db_session):
    case = Case(case_number="CASE-002")
    doc = SourceDocument(case_id=1, file_name="test.pdf", case=case)
    db_session.add_all([case, doc])
    db_session.commit()

    assert ReadinessValidator.check_ocr_status(case) == False

    bill = BillHeader(document_id=doc.id, status="pending")
    db_session.add(bill)
    db_session.commit()

    assert ReadinessValidator.check_ocr_status(case) == False

    bill.status = "extracted"
    db_session.commit()

    assert ReadinessValidator.check_ocr_status(case) == True

def test_check_memo_generated(db_session):
    case = Case(case_number="CASE-003")
    db_session.add(case)
    db_session.commit()

    assert ReadinessValidator.check_memo_generated(case) == False

    dika = Dika(case_id=case.id)
    memo = Memo(dika=dika, file_path="some/path.docx")
    db_session.add_all([dika, memo])
    db_session.commit()

    assert ReadinessValidator.check_memo_generated(case) == True

def test_check_dika_metadata(db_session):
    case = Case(case_number="CASE-004")
    db_session.add(case)
    db_session.commit()

    assert ReadinessValidator.check_dika_metadata(case) == False

    dika = Dika(case_id=case.id, dika_number="DK-01", dika_date=datetime.date.today(), payee_name="Vendor A")
    db_session.add(dika)
    db_session.commit()

    assert ReadinessValidator.check_dika_metadata(case) == True

def test_normalize_provider():
    assert ReadinessValidator.normalize_provider("บมจ. โทรคมนาคมแห่งชาติ") == "บริษัท โทรคมนาคมแห่งชาติ จำกัด (มหาชน)"
    assert ReadinessValidator.normalize_provider("กฟภ.") == "การไฟฟ้าส่วนภูมิภาค"
    assert ReadinessValidator.normalize_provider("การประปาส่วนภูมิภาคสาขาเชียงใหม่") == "การประปาส่วนภูมิภาค"
    assert ReadinessValidator.normalize_provider("Random Vendor") == "Random Vendor"

def test_check_duplicate_bill(db_session):
    # Base case setup
    case1 = Case(case_number="CASE-01")
    doc1 = SourceDocument(case=case1)
    bill1 = BillHeader(document=doc1, status="extracted", provider="กฟภ.", bill_date=datetime.date(2026, 1, 1), total_amount=1500.0)

    case2 = Case(case_number="CASE-02")
    doc2 = SourceDocument(case=case2)
    # This should be a duplicate of bill1 based on exact match of date/amount and normalized provider
    bill2 = BillHeader(document=doc2, status="extracted", provider="การไฟฟ้าส่วนภูมิภาค", bill_date=datetime.date(2026, 1, 1), total_amount=1500.0)

    db_session.add_all([case1, doc1, bill1, case2, doc2, bill2])
    db_session.commit()

    warnings = ReadinessValidator.check_duplicate_bill(case2, db_session)
    assert len(warnings) == 1
    assert "เลขแฟ้ม CASE-01" in warnings[0]

def test_validate_budget(db_session):
    fy = FiscalYear(year_be=2569, start_date=datetime.date(2025, 10, 1), end_date=datetime.date(2026, 9, 30))
    budget_line = BudgetLine(fiscal_year=fy, department="สำนักปลัด", expense_type="ค่าไฟฟ้า", initial_amount=5000.0)

    # Case asks for 2000.0
    case = Case(fiscal_year_be=2569, department="สำนักปลัด", expense_group="ค่าไฟฟ้า")
    doc = SourceDocument(case=case)
    bill = BillHeader(document=doc, status="extracted", total_amount=2000.0)

    db_session.add_all([fy, budget_line, case, doc, bill])
    db_session.commit()

    res = ReadinessValidator.validate_budget(case, db_session)
    assert res["budget_ok"] == True
    assert res["available_budget"] == 5000.0

    # Add an expense ledger to deduct 3500.0
    ledger = ExpenseLedger(budget_line_id=budget_line.id, case_id=999, amount_deducted=3500.0)
    db_session.add(ledger)
    db_session.commit()

    # Remaining budget is 1500.0, required is 2000.0
    res2 = ReadinessValidator.validate_budget(case, db_session)
    assert res2["budget_ok"] == False
    assert res2["available_budget"] == 1500.0

def test_evaluate_readiness_all_ok(db_session):
    fy = FiscalYear(year_be=2569, start_date=datetime.date(2025, 10, 1), end_date=datetime.date(2026, 9, 30))
    budget_line = BudgetLine(fiscal_year=fy, department="สำนักปลัด", expense_type="ค่าไฟฟ้า", initial_amount=5000.0)

    case = Case(case_number="CASE-FULL", fiscal_year_be=2569, department="สำนักปลัด", expense_group="ค่าไฟฟ้า")
    doc = SourceDocument(case=case, file_name="test.pdf")
    bill = BillHeader(document=doc, status="extracted", total_amount=100.0, provider="NT", bill_date=datetime.date.today())
    dika = Dika(case=case, dika_number="DK-FULL", dika_date=datetime.date.today(), payee_name="NT")
    memo = Memo(dika=dika, file_path="data/generated/memo.docx")

    db_session.add_all([fy, budget_line, case, doc, bill, dika, memo])
    db_session.commit()

    result = ReadinessValidator.evaluate_readiness(case, db_session)
    assert result["ready"] == True
    assert len(result["blockers"]) == 0
    assert result["budget_ok"] == True
