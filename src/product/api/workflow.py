import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from src.product.db.models import Case, CaseNote, CaseTimelineEvent
from src.product.db.session import get_db
from src.product.services.workflow_lifecycle import WorkflowLifecycleService

router = APIRouter(prefix="/api/cases", tags=["workflow"])


class TimelineEventResponse(BaseModel):
    id: int
    case_id: int
    event_type: str
    from_status: str | None
    to_status: str | None
    detail: str | None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class NoteCreate(BaseModel):
    note_text: str


class CaseNoteResponse(BaseModel):
    id: int
    case_id: int
    note_text: str
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class StatusResponse(BaseModel):
    case_id: int
    status: str
    event: TimelineEventResponse


def _get_case_or_404(case_id: int, db: Session) -> Case:
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.get("/{case_id}/timeline", response_model=list[TimelineEventResponse])
def get_timeline(case_id: int, db: Session = Depends(get_db)):
    _get_case_or_404(case_id, db)
    return (
        db.query(CaseTimelineEvent)
        .filter(CaseTimelineEvent.case_id == case_id)
        .order_by(CaseTimelineEvent.created_at.asc(), CaseTimelineEvent.id.asc())
        .all()
    )


@router.get("/{case_id}/notes", response_model=list[CaseNoteResponse])
def get_notes(case_id: int, db: Session = Depends(get_db)):
    _get_case_or_404(case_id, db)
    return (
        db.query(CaseNote)
        .filter(CaseNote.case_id == case_id)
        .order_by(CaseNote.created_at.asc(), CaseNote.id.asc())
        .all()
    )


@router.post("/{case_id}/notes", response_model=CaseNoteResponse)
def create_note(case_id: int, payload: NoteCreate, db: Session = Depends(get_db)):
    case = _get_case_or_404(case_id, db)
    note_text = payload.note_text.strip()
    if not note_text:
        raise HTTPException(status_code=400, detail="Note text is required")
    return WorkflowLifecycleService.add_note(db, case, note_text)


@router.post("/{case_id}/status/submitted", response_model=StatusResponse)
def mark_submitted(case_id: int, db: Session = Depends(get_db)):
    case = _get_case_or_404(case_id, db)
    try:
        event = WorkflowLifecycleService.mark_submitted(db, case)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"case_id": case.id, "status": case.status, "event": event}


@router.post("/{case_id}/status/completed", response_model=StatusResponse)
def mark_completed(case_id: int, db: Session = Depends(get_db)):
    case = _get_case_or_404(case_id, db)
    try:
        event = WorkflowLifecycleService.mark_completed(db, case)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"case_id": case.id, "status": case.status, "event": event}
