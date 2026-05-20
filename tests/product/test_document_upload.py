import pytest
import os
import shutil
from fastapi.testclient import TestClient
from src.product.main import app
from src.product.db.models import Base, Case
from src.product.db.session import engine, SessionLocal

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    # Make sure tables are created
    Base.metadata.create_all(bind=engine)
    yield
    # Clean up tables
    Base.metadata.drop_all(bind=engine)
    # Clean up uploads directory if created
    if os.path.exists("data/uploads"):
        shutil.rmtree("data/uploads")

def test_document_upload_success():
    # 1. Seed a Case in DB
    db = SessionLocal()
    db_case = Case(
        case_number="CASE-2569-0001",
        fiscal_year_be=2569,
        work_month="มีนาคม",
        case_type="utility",
        expense_group="ค่าไฟฟ้า",
        department="กองคลัง",
        status="draft"
    )
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    case_id = db_case.id
    db.close()

    # 2. Upload document via POST /api/cases/{case_id}/documents
    file_content = b"Mock PDF invoice contents"
    files = {"file": ("invoice.pdf", file_content, "application/pdf")}
    data = {"document_type": "bill"}

    response = client.post(
        f"/api/cases/{case_id}/documents",
        files=files,
        data=data
    )

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["file_name"] == "invoice.pdf"
    assert res_data["file_type"] == "pdf"
    assert res_data["document_type"] == "bill"
    assert res_data["case_id"] == case_id

    # 3. Verify file is stored on disk
    expected_path = os.path.join("data", "uploads", str(case_id), "invoice.pdf")
    assert os.path.exists(expected_path)
    with open(expected_path, "rb") as f:
        assert f.read() == file_content

    # 4. Verify Case Details returns the uploaded document
    detail_res = client.get(f"/api/cases/{case_id}")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert len(detail_data["documents"]) == 1
    assert detail_data["documents"][0]["file_name"] == "invoice.pdf"
    assert detail_data["documents"][0]["document_type"] == "bill"

def test_document_upload_case_not_found():
    # Attempt upload on non-existent case
    file_content = b"Dummy data"
    files = {"file": ("test.txt", file_content, "text/plain")}
    data = {"document_type": "receipt"}

    response = client.post(
        "/api/cases/99999/documents",
        files=files,
        data=data
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Case not found"
