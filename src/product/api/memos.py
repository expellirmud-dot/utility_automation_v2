"""
Memo and Dika API routes for PRODUCT-004.

POST /api/cases/{case_id}/dika          - save Dika + Memo metadata
POST /api/cases/{case_id}/memo/generate - generate Word .docx
GET  /api/cases/{case_id}/memo/download - download the generated file
"""

import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from src.product.db.session import get_db
from src.product.db.models import Case, Dika, Memo, SourceDocument, BillHeader
from src.product.services.word_generation import WordGenerationService

router = APIRouter(prefix="/api/cases", tags=["Memos"])


# ─────────────────────────────────────────────
# Pydantic schemas
# ─────────────────────────────────────────────

class DikaSaveRequest(BaseModel):
    dika_no: str
    dika_date: datetime.date
    payee_name: str
    memo_number: str
    memo_date: datetime.date


class DikaResponse(BaseModel):
    id: int
    dika_number: Optional[str]
    dika_date: Optional[datetime.date]
    payee_name: Optional[str] = None
    status: str
    created_at: datetime.datetime
    memo_number: Optional[str] = None
    memo_date: Optional[datetime.date] = None
    memo_file_path: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MemoGenerateResponse(BaseModel):
    memo_id: int
    file_path: str
    status: str
    download_url: str


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

@router.post("/{case_id}/dika", response_model=DikaResponse)
def save_dika(case_id: int, payload: DikaSaveRequest, db: Session = Depends(get_db)):
    """Save or update Dika and Memo metadata for a case."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Upsert Dika
    dika = db.query(Dika).filter(Dika.case_id == case_id).first()
    if not dika:
        dika = Dika(case_id=case_id)
        db.add(dika)

    dika.dika_number = payload.dika_no
    dika.dika_date = payload.dika_date
    dika.payee_name = payload.payee_name  # stored on Dika, not on Case
    dika.status = "draft"
    db.flush()  # get dika.id before memo insert

    # Upsert Memo
    memo = db.query(Memo).filter(Memo.dika_id == dika.id).first()
    if not memo:
        memo = Memo(dika_id=dika.id)
        db.add(memo)

    memo.memo_number = payload.memo_number
    memo.memo_date = payload.memo_date
    db.commit()
    db.refresh(dika)
    db.refresh(memo)

    return DikaResponse(
        id=dika.id,
        dika_number=dika.dika_number,
        dika_date=dika.dika_date,
        payee_name=dika.payee_name,
        status=dika.status,
        created_at=dika.created_at,
        memo_number=memo.memo_number,
        memo_date=memo.memo_date,
        memo_file_path=memo.file_path,
    )


@router.post("/{case_id}/memo/generate", response_model=MemoGenerateResponse)
def generate_memo(case_id: int, db: Session = Depends(get_db)):
    """Generate Word memo .docx from case data and saved Dika/Memo metadata."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    dika = db.query(Dika).filter(Dika.case_id == case_id).first()
    if not dika:
        raise HTTPException(status_code=400, detail="Dika data not saved. Call POST /dika first.")

    memo = db.query(Memo).filter(Memo.dika_id == dika.id).first()
    if not memo:
        raise HTTPException(status_code=400, detail="Memo metadata missing. Call POST /dika first.")

    # Get first extracted BillHeader for this case (if any)
    bill_header: Optional[BillHeader] = None
    for doc in case.documents:
        if doc.bill_header and doc.bill_header.status == "extracted":
            bill_header = doc.bill_header
            break

    # provider: prefer BillHeader.provider, fall back to Dika.payee_name
    provider = (
        (bill_header.provider if bill_header and bill_header.provider else None)
        or dika.payee_name
        or ""
    )
    bill_date = bill_header.bill_date if bill_header else None
    total_amount = bill_header.total_amount if bill_header else 0.0

    try:
        output_path = WordGenerationService.generate(
            case_id=case_id,
            memo_number=memo.memo_number or "",
            memo_date=memo.memo_date,
            expense_group=case.expense_group or "",
            work_month=case.work_month or "",
            fiscal_year_be=case.fiscal_year_be,
            provider=provider,
            bill_date=bill_date,
            total_amount=total_amount,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Persist file path on Memo record
    memo.file_path = str(output_path)
    case.status = "word_generated"
    db.commit()
    db.refresh(memo)

    return MemoGenerateResponse(
        memo_id=memo.id,
        file_path=str(output_path),
        status="generated",
        download_url=f"/api/cases/{case_id}/memo/download",
    )


@router.get("/{case_id}/memo/download")
def download_memo(case_id: int, db: Session = Depends(get_db)):
    """Download the generated Word memo .docx for this case."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    dika = db.query(Dika).filter(Dika.case_id == case_id).first()
    if not dika:
        raise HTTPException(status_code=404, detail="No Dika record found")

    memo = db.query(Memo).filter(Memo.dika_id == dika.id).first()
    if not memo or not memo.file_path:
        raise HTTPException(status_code=404, detail="No generated memo file found. Generate first.")

    file_path = Path(memo.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Generated file missing from disk.")

    filename = f"memo_case_{case_id}.docx"
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
