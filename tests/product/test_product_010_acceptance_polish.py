import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.product.db.models import (
    Base,
    BillHeader,
    BudgetLine,
    Case,
    Dika,
    ExpenseLedger,
    FiscalYear,
    Memo,
    SourceDocument,
)
from src.product.services.elaas_payload_builder import ElaasPayloadBuilder
from src.product.services.readiness_validator import ReadinessValidator
from src.product.services.workflow_lifecycle import WorkflowLifecycleService


engine = create_engine("sqlite:///:memory:")
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def _budget(db, *, amount=5000.0, expense_type="ค่าไฟฟ้า"):
    fy = db.query(FiscalYear).filter(FiscalYear.year_be == 2569).first()
    if not fy:
        fy = FiscalYear(
            year_be=2569,
            start_date=datetime.date(2025, 10, 1),
            end_date=datetime.date(2026, 9, 30),
        )
    line = BudgetLine(
        fiscal_year=fy,
        department="สำนักปลัด",
        expense_type=expense_type,
        initial_amount=amount,
    )
    db.add_all([fy, line])
    db.commit()
    return line


def _ready_case(db, *, provider="PEA", expense_group="ค่าไฟฟ้า", amount=1200.0, budget_amount=5000.0):
    budget_line = _budget(db, amount=budget_amount, expense_type=expense_group)
    case = Case(
        case_number=f"PRODUCT-010-{provider}",
        fiscal_year_be=2569,
        work_month="พฤษภาคม",
        case_type="utility",
        expense_group=expense_group,
        department="สำนักปลัด",
        budget_line_id=budget_line.id,
        total_amount=amount,
    )
    doc = SourceDocument(case=case, file_name="bill.pdf", file_path="bill.pdf", document_type="bill")
    bill = BillHeader(
        document=doc,
        provider=provider,
        bill_date=datetime.date(2026, 5, 1),
        total_amount=amount,
        status="extracted",
    )
    dika = Dika(
        case=case,
        dika_number=f"ฎ-{provider}",
        dika_date=datetime.date(2026, 5, 2),
        payee_name=f"ผู้รับเงิน {provider}",
    )
    memo = Memo(
        dika=dika,
        memo_number=f"MEMO-{provider}",
        memo_date=datetime.date(2026, 5, 3),
        file_path=f"data/generated/{provider}.docx",
    )
    db.add_all([case, doc, bill, dika, memo])
    db.commit()
    db.refresh(case)
    return case, budget_line


@pytest.mark.parametrize(
    ("raw_provider", "expected"),
    [
        ("PEA", "การไฟฟ้าส่วนภูมิภาค"),
        ("MEA", "การไฟฟ้านครหลวง"),
        ("NT", "บริษัท โทรคมนาคมแห่งชาติ จำกัด (มหาชน)"),
        ("AIS", "บริษัท แอดวานซ์ อินโฟร์ เซอร์วิส จำกัด (มหาชน)"),
        ("water bill", "การประปาส่วนภูมิภาค"),
    ],
)
def test_product_010_provider_alias_acceptance(raw_provider, expected):
    assert ReadinessValidator.normalize_provider(raw_provider) == expected


def test_product_010_duplicate_warning(db):
    case1, _ = _ready_case(db, provider="PEA")
    case2, _ = _ready_case(db, provider="การไฟฟ้าส่วนภูมิภาค")
    case2.documents[0].bill_header.bill_date = case1.documents[0].bill_header.bill_date
    case2.documents[0].bill_header.total_amount = case1.documents[0].bill_header.total_amount
    db.commit()

    warnings = ReadinessValidator.check_duplicate_bill(case2, db)

    assert warnings == [f"อาจเป็นบิลซ้ำซ้อนกับเลขแฟ้ม {case1.case_number}"]


def test_product_010_insufficient_budget_blocks_readiness_and_payload(db):
    case, budget_line = _ready_case(db, provider="MEA", budget_amount=1000.0, amount=1200.0)
    db.add(ExpenseLedger(budget_line_id=budget_line.id, case_id=999, amount_deducted=100.0))
    db.commit()

    readiness = ReadinessValidator.evaluate_readiness(case, db)
    payload = ElaasPayloadBuilder.build(case, db)

    assert readiness["ready"] is False
    assert readiness["budget_ok"] is False
    assert readiness["available_budget"] == 900.0
    assert any("งบประมาณคงเหลือไม่เพียงพอ" in blocker for blocker in readiness["blockers"])
    assert payload["readiness_passed"] is False


def test_product_010_ocr_failure_blocks_readiness(db):
    case, _ = _ready_case(db, provider="NT")
    case.documents[0].bill_header.status = "failed"
    db.commit()

    readiness = ReadinessValidator.evaluate_readiness(case, db)

    assert readiness["ready"] is False
    assert readiness["summary"]["ocr_status"] is False
    assert "OCR" in readiness["blockers"][0]


def test_product_010_missing_memo_blocks_readiness(db):
    case, _ = _ready_case(db, provider="AIS")
    case.dika.memo.file_path = ""
    db.commit()

    readiness = ReadinessValidator.evaluate_readiness(case, db)

    assert readiness["ready"] is False
    assert readiness["summary"]["memo_status"] is False
    assert any("บันทึกข้อความ" in blocker for blocker in readiness["blockers"])


def test_product_010_ambiguous_budget_and_manual_override(db):
    _budget(db, amount=5000.0, expense_type="ค่าน้ำประปา")
    override = _budget(db, amount=7000.0, expense_type="ค่าน้ำประปา")
    case = Case(
        case_number="PRODUCT-010-BUDGET",
        fiscal_year_be=2569,
        work_month="พฤษภาคม",
        case_type="utility",
        expense_group="ค่าน้ำประปา",
        department="สำนักปลัด",
        total_amount=800.0,
    )
    doc = SourceDocument(case=case, file_name="water.pdf", file_path="water.pdf", document_type="bill")
    bill = BillHeader(document=doc, provider="water", total_amount=800.0, status="extracted")
    db.add_all([case, doc, bill])
    db.commit()

    ambiguous = ReadinessValidator.validate_budget(case, db)
    case.budget_line_id = override.id
    db.commit()
    manual = ReadinessValidator.validate_budget(case, db)

    assert ambiguous["budget_ok"] is False
    assert "มากกว่า 1 รายการ" in ambiguous["reason"]
    assert manual["budget_ok"] is True
    assert manual["available_budget"] == 7000.0


def test_product_010_elaas_payload_and_submitted_to_completed(db):
    case, _ = _ready_case(db, provider="PEA")

    payload = ElaasPayloadBuilder.build(case, db)
    record = ElaasPayloadBuilder.save(case, payload, db)
    WorkflowLifecycleService.record_event(db, case, "elaas_payload_saved", "payload saved")
    submitted = WorkflowLifecycleService.mark_submitted(db, case)
    completed = WorkflowLifecycleService.mark_completed(db, case)

    assert payload["readiness_passed"] is True
    assert payload["provider"] == "การไฟฟ้าส่วนภูมิภาค"
    assert payload["bill_amount"] == 1200.0
    assert record.status == "prepared"
    assert submitted.to_status == "submitted_manual"
    assert completed.to_status == "completed"
    assert case.status == "completed"
