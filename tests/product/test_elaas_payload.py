"""
Tests for PRODUCT-006: ElaasPayloadBuilder service and API endpoints.
"""

import pytest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.product.db.models import (
    Base, Case, BillHeader, SourceDocument, Dika, Memo,
    BudgetLine, FiscalYear, ExpenseLedger, ElaasPayload,
)
from src.product.services.elaas_payload_builder import ElaasPayloadBuilder

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


def _make_full_case(db):
    """Helper: create a fully-populated case with all related data."""
    fy = FiscalYear(
        year_be=2569,
        start_date=datetime.date(2025, 10, 1),
        end_date=datetime.date(2026, 9, 30),
    )
    budget_line = BudgetLine(
        fiscal_year=fy,
        department="สำนักปลัด",
        expense_type="ค่าไฟฟ้า",
        initial_amount=10000.0,
    )
    case = Case(
        case_number="CASE-2569-0001",
        fiscal_year_be=2569,
        work_month="พฤษภาคม",
        case_type="utility",
        expense_group="ค่าไฟฟ้า",
        department="สำนักปลัด",
    )
    doc = SourceDocument(case=case, file_name="bill.pdf", document_type="bill")
    bill = BillHeader(
        document=doc,
        status="extracted",
        provider="กฟภ.",
        bill_date=datetime.date(2026, 4, 30),
        total_amount=1250.50,
    )
    dika = Dika(
        case=case,
        dika_number="ฎ-001/2569",
        dika_date=datetime.date(2026, 5, 1),
        payee_name="การไฟฟ้าส่วนภูมิภาค",
    )
    memo = Memo(
        dika=dika,
        memo_number="กค 001/2569",
        memo_date=datetime.date(2026, 5, 10),
        file_path="data/generated/case_1_memo.docx",
    )
    db.add_all([fy, budget_line, case, doc, bill, dika, memo])
    db.commit()
    db.refresh(case)
    return case


def test_build_payload_full(db):
    case = _make_full_case(db)
    payload = ElaasPayloadBuilder.build(case, db)

    assert payload["case_number"] == "CASE-2569-0001"
    assert payload["department"] == "สำนักปลัด"
    assert payload["fiscal_year_be"] == 2569
    assert payload["expense_group"] == "ค่าไฟฟ้า"
    assert payload["work_month"] == "พฤษภาคม"
    assert payload["provider"] == "การไฟฟ้าส่วนภูมิภาค"
    assert payload["bill_amount"] == 1250.50
    assert payload["bill_amount_thai"] != ""
    assert "ถ้วน" not in payload["bill_amount_thai"]  # has satang
    assert payload["dika_number"] == "ฎ-001/2569"
    assert payload["memo_number"] == "กค 001/2569"
    assert payload["readiness_passed"] is True
    assert payload["bill_date"] == "2026-04-30"
    assert payload["budget_available"] == 10000.0


def test_build_payload_payee_priority(db):
    """Dika.payee_name must take priority over BillHeader.provider."""
    case = _make_full_case(db)
    payload = ElaasPayloadBuilder.build(case, db)
    # Dika has payee_name = "การไฟฟ้าส่วนภูมิภาค"
    assert payload["payee_name"] == "การไฟฟ้าส่วนภูมิภาค"


def test_build_payload_payee_fallback_to_provider(db):
    """When Dika.payee_name is empty, falls back to normalized provider."""
    case = Case(
        case_number="CASE-FB-001",
        fiscal_year_be=2569,
        work_month="มกราคม",
        expense_group="ค่าน้ำประปา",
        department="สำนักปลัด",
    )
    doc = SourceDocument(case=case, file_name="bill.pdf", document_type="bill")
    bill = BillHeader(
        document=doc,
        status="extracted",
        provider="กปภ.",
        bill_date=datetime.date(2026, 1, 31),
        total_amount=500.0,
    )
    dika = Dika(case=case, dika_number="ฎ-002/2569", dika_date=datetime.date(2026, 2, 1), payee_name="")
    db.add_all([case, doc, bill, dika])
    db.commit()
    db.refresh(case)
    payload = ElaasPayloadBuilder.build(case, db)
    assert payload["payee_name"] == "การประปาส่วนภูมิภาค"


def test_build_payload_missing_bill(db):
    """No extracted bill → falls back to Case.total_amount, no crash."""
    case = Case(
        case_number="CASE-NOBILL-001",
        fiscal_year_be=2569,
        work_month="มีนาคม",
        expense_group="ค่าโทรศัพท์",
        department="สำนักปลัด",
        total_amount=800.0,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    payload = ElaasPayloadBuilder.build(case, db)
    assert payload["bill_amount"] == 800.0
    assert payload["provider"] == ""
    assert payload["bill_date"] == ""
    assert payload["readiness_passed"] is False


def test_build_payload_missing_dika(db):
    """No Dika → dika fields blank, no crash."""
    case = Case(
        case_number="CASE-NODIKA-001",
        fiscal_year_be=2569,
        work_month="กุมภาพันธ์",
        expense_group="ค่าไฟฟ้า",
        department="กองช่าง",
    )
    doc = SourceDocument(case=case, file_name="bill.pdf", document_type="bill")
    bill = BillHeader(document=doc, status="extracted", provider="PEA", total_amount=2000.0)
    db.add_all([case, doc, bill])
    db.commit()
    db.refresh(case)
    payload = ElaasPayloadBuilder.build(case, db)
    assert payload["dika_number"] == ""
    assert payload["memo_number"] == ""
    assert payload["readiness_passed"] is False


def test_attachment_checklist_complete(db):
    """All required document types present → required items show present=True."""
    case = _make_full_case(db)
    payload = ElaasPayloadBuilder.build(case, db)
    checklist = {item["doc_type"]: item for item in payload["attachment_checklist"]}
    assert checklist["bill"]["present"] is True
    assert checklist["memo_generated"]["present"] is True
    assert checklist["dika"]["present"] is True


def test_attachment_checklist_partial(db):
    """Only bill doc → receipt and contract show present=False."""
    case = _make_full_case(db)
    payload = ElaasPayloadBuilder.build(case, db)
    checklist = {item["doc_type"]: item for item in payload["attachment_checklist"]}
    assert checklist["receipt"]["present"] is False
    assert checklist["contract"]["present"] is False


def test_save_payload(db):
    """POST /save persists ElaasPayload record with status=prepared."""
    case = _make_full_case(db)
    payload = ElaasPayloadBuilder.build(case, db)
    record = ElaasPayloadBuilder.save(case, payload, db)

    assert record.id is not None
    assert record.case_id == case.id
    assert record.status == "prepared"
    assert record.payload_data is not None
    assert record.payload_data["case_number"] == "CASE-2569-0001"


def test_save_payload_upsert(db):
    """Saving twice updates the existing record (upsert)."""
    case = _make_full_case(db)
    payload = ElaasPayloadBuilder.build(case, db)
    record1 = ElaasPayloadBuilder.save(case, payload, db)

    payload["memo_number"] = "กค 002/2569"
    record2 = ElaasPayloadBuilder.save(case, payload, db)

    assert record1.id == record2.id
    assert record2.payload_data["memo_number"] == "กค 002/2569"
    count = db.query(ElaasPayload).filter(ElaasPayload.case_id == case.id).count()
    assert count == 1
