from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
import datetime

from src.product.db.session import get_db
from src.product.db.models import Case

router = APIRouter(prefix="/api/cases", tags=["Cases"])

class CaseCreate(BaseModel):
    fiscal_year_be: int
    work_month: str
    case_type: str
    expense_group: str
    department: str
    division: Optional[str] = None
    note: Optional[str] = None

class CaseResponse(BaseModel):
    id: int
    case_number: str
    fiscal_year_be: int
    work_month: str
    case_type: str
    expense_group: str
    department: str
    division: Optional[str]
    status: str
    total_amount: float
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class BillHeaderResponse(BaseModel):
    id: int
    provider: Optional[str]
    bill_date: Optional[datetime.date]
    total_amount: float
    status: str
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class SourceDocumentResponse(BaseModel):
    id: int
    file_name: str
    file_path: str
    file_type: str
    document_type: str
    created_at: datetime.datetime
    bill_header: Optional[BillHeaderResponse] = None

    model_config = ConfigDict(from_attributes=True)

class CaseDetailResponse(BaseModel):
    id: int
    case_number: str
    fiscal_year_be: int
    work_month: str
    case_type: str
    expense_group: str
    department: str
    division: Optional[str]
    status: str
    total_amount: float
    note: Optional[str]
    created_at: datetime.datetime
    documents: List[SourceDocumentResponse] = []

    model_config = ConfigDict(from_attributes=True)

@router.post("/", response_model=CaseResponse)
def create_case(case: CaseCreate, db: Session = Depends(get_db)):
    # Generate case number e.g. CASE-2569-03-001
    # Very simplistic generation for baseline
    count = db.query(Case).filter(Case.fiscal_year_be == case.fiscal_year_be).count()
    # Map thai month name to number for ID if possible, otherwise use a generic sequence
    seq = count + 1
    case_number = f"CASE-{case.fiscal_year_be}-{seq:04d}"
    
    db_case = Case(
        case_number=case_number,
        fiscal_year_be=case.fiscal_year_be,
        work_month=case.work_month,
        case_type=case.case_type,
        expense_group=case.expense_group,
        department=case.department,
        division=case.division,
        note=case.note,
        status="draft"
    )
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    return db_case

@router.get("/", response_model=List[CaseResponse])
def list_cases(db: Session = Depends(get_db)):
    cases = db.query(Case).order_by(Case.created_at.desc()).all()
    return cases

@router.get("/{case_id}", response_model=CaseDetailResponse)
def get_case(case_id: int, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case
