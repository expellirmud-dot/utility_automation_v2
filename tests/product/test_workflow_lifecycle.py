import pytest
from fastapi.testclient import TestClient

from src.product.db.models import Base, Case, CaseTimelineEvent
from src.product.db.session import SessionLocal, engine
from src.product.main import app
from src.product.services.workflow_lifecycle import WorkflowLifecycleService


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


def _case(db, status="intake"):
    case = Case(
        case_number=f"WF-{status}",
        fiscal_year_be=2569,
        work_month="พฤษภาคม",
        case_type="utility",
        expense_group="ค่าไฟฟ้า",
        department="สำนักปลัด",
        status=status,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def test_automatic_lifecycle_events_advance_forward_only(db):
    case = _case(db)

    WorkflowLifecycleService.record_event(db, case, "document_uploaded", "uploaded bill.pdf")
    WorkflowLifecycleService.record_event(db, case, "ocr_success", "ocr completed")
    WorkflowLifecycleService.record_event(db, case, "dika_saved", "dika metadata saved")
    WorkflowLifecycleService.record_event(db, case, "memo_generated", "memo generated")
    WorkflowLifecycleService.record_event(db, case, "elaas_payload_saved", "payload saved")

    db.refresh(case)
    events = (
        db.query(CaseTimelineEvent)
        .filter(CaseTimelineEvent.case_id == case.id)
        .order_by(CaseTimelineEvent.id.asc())
        .all()
    )

    assert case.status == "elaas_prepared"
    assert [event.event_type for event in events] == [
        "document_uploaded",
        "ocr_success",
        "dika_saved",
        "memo_generated",
        "elaas_payload_saved",
    ]
    assert events[0].from_status == "intake"
    assert events[0].to_status == "documents_uploaded"


def test_stale_automatic_event_does_not_rewind_status(db):
    case = _case(db, status="memo_generated")

    event = WorkflowLifecycleService.record_event(db, case, "document_uploaded", "late upload")

    db.refresh(case)
    assert case.status == "memo_generated"
    assert event.from_status == "memo_generated"
    assert event.to_status == "memo_generated"


def test_manual_submitted_and_completed_require_valid_sequence(db):
    case = _case(db)

    submitted_too_early = client.post(f"/api/cases/{case.id}/status/submitted")
    assert submitted_too_early.status_code == 400

    WorkflowLifecycleService.record_event(db, case, "elaas_payload_saved", "payload saved")

    submitted = client.post(f"/api/cases/{case.id}/status/submitted")
    assert submitted.status_code == 200
    assert submitted.json()["status"] == "submitted_manual"

    completed = client.post(f"/api/cases/{case.id}/status/completed")
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"

    db.refresh(case)
    assert case.status == "completed"


def test_timeline_endpoint_returns_events_in_created_order(db):
    case = _case(db)
    WorkflowLifecycleService.record_event(db, case, "document_uploaded", "uploaded")
    WorkflowLifecycleService.record_event(db, case, "ocr_success", "ocr")

    response = client.get(f"/api/cases/{case.id}/timeline")

    assert response.status_code == 200
    assert [event["event_type"] for event in response.json()] == [
        "document_uploaded",
        "ocr_success",
    ]


def test_manual_status_unknown_case_returns_404():
    response = client.post("/api/cases/999999/status/submitted")
    assert response.status_code == 404
