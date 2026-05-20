import pytest
from fastapi.testclient import TestClient

from src.product.db.models import Base, Case
from src.product.db.session import SessionLocal, engine
from src.product.main import app


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


def _case(db, case_number="NOTE-CASE-001"):
    case = Case(
        case_number=case_number,
        fiscal_year_be=2569,
        work_month="พฤษภาคม",
        case_type="utility",
        expense_group="ค่าไฟฟ้า",
        department="สำนักปลัด",
        status="intake",
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def test_notes_list_empty_for_new_case(db):
    case = _case(db)

    response = client.get(f"/api/cases/{case.id}/notes")

    assert response.status_code == 200
    assert response.json() == []


def test_create_notes_is_append_only_and_ordered(db):
    case = _case(db)

    first = client.post(
        f"/api/cases/{case.id}/notes",
        json={"note_text": "รอเอกสารจากกองคลัง"},
    )
    second = client.post(
        f"/api/cases/{case.id}/notes",
        json={"note_text": "โทรยืนยันยอดแล้ว"},
    )

    assert first.status_code == 200
    assert first.json()["note_text"] == "รอเอกสารจากกองคลัง"
    assert second.status_code == 200
    assert second.json()["note_text"] == "โทรยืนยันยอดแล้ว"

    response = client.get(f"/api/cases/{case.id}/notes")
    notes = response.json()
    assert [note["note_text"] for note in notes] == [
        "รอเอกสารจากกองคลัง",
        "โทรยืนยันยอดแล้ว",
    ]


def test_notes_are_scoped_to_case(db):
    first_case = _case(db, "NOTE-CASE-001")
    second_case = _case(db, "NOTE-CASE-002")

    client.post(f"/api/cases/{first_case.id}/notes", json={"note_text": "first"})
    client.post(f"/api/cases/{second_case.id}/notes", json={"note_text": "second"})

    first_notes = client.get(f"/api/cases/{first_case.id}/notes").json()
    second_notes = client.get(f"/api/cases/{second_case.id}/notes").json()

    assert [note["note_text"] for note in first_notes] == ["first"]
    assert [note["note_text"] for note in second_notes] == ["second"]


def test_create_note_rejects_empty_text(db):
    case = _case(db)
    response = client.post(f"/api/cases/{case.id}/notes", json={"note_text": "   "})
    assert response.status_code == 400


def test_notes_unknown_case_returns_404():
    response = client.get("/api/cases/999999/notes")
    assert response.status_code == 404
