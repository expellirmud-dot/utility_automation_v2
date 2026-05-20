import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from src.product.main import app
from src.product.db.models import Base, Case, SourceDocument, BillHeader
from src.product.db.session import engine, SessionLocal
from src.models.bill_data import BillData
import datetime
import io
import os

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_document_process_and_retrieval():
    # 1. Create a case
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
    case_id = create_res.json()["id"]

    # 2. Upload a dummy document
    dummy_file = io.BytesIO(b"dummy pdf content")
    upload_res = client.post(
        f"/api/cases/{case_id}/documents",
        files={"file": ("test_bill.pdf", dummy_file, "application/pdf")},
        data={"document_type": "bill"}
    )
    assert upload_res.status_code == 200
    doc_id = upload_res.json()["id"]

    # 3. Process the document with mocked UnifiedBillPipeline
    mock_bill_data = BillData(
        vendor_name="Electricity",
        bill_number="1234567890",
        bill_date="2026-03-15",
        total=3500.50,
        account_number="CA-998877",
        service_period="01/02/2569 - 28/02/2569",
        raw_text="Mocked MEA Bill Total: 3,500.50"
    )

    expected_path = os.path.join("data", "uploads", str(case_id), "test_bill.pdf")

    with patch("src.product.api.documents.UnifiedBillPipeline.run", return_value=mock_bill_data) as mock_run:
        process_res = client.post(f"/api/cases/{case_id}/documents/{doc_id}/process")
        assert process_res.status_code == 200
        data = process_res.json()
        assert data["provider"] == "Electricity"
        assert data["bill_date"] == "2026-03-15"
        assert data["total_amount"] == 3500.50
        assert data["status"] == "extracted"
        mock_run.assert_called_once_with(expected_path)

    # 4. Get case details and verify nested bill_header
    detail_res = client.get(f"/api/cases/{case_id}")
    assert detail_res.status_code == 200
    case_detail = detail_res.json()
    assert len(case_detail["documents"]) == 1
    doc_detail = case_detail["documents"][0]
    assert doc_detail["id"] == doc_id
    assert doc_detail["bill_header"] is not None
    assert doc_detail["bill_header"]["provider"] == "Electricity"
    assert doc_detail["bill_header"]["total_amount"] == 3500.50
    assert doc_detail["bill_header"]["status"] == "extracted"
