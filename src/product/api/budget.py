from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from src.product.db.models import BudgetLine, Case, ExpenseLedger, FiscalYear
from src.product.db.session import get_db
from src.product.services.budget_import import BudgetImportService

router = APIRouter(prefix="/api/budget", tags=["Budget"])


class BudgetLineResponse(BaseModel):
    id: int
    department: str
    division: str
    expense_type: str
    appropriation_category: str | None = ""
    initial_amount: float
    deducted_amount: float = 0.0
    available_amount: float = 0.0
    fiscal_year_be: int

    model_config = ConfigDict(from_attributes=True)


class BudgetSelectionRequest(BaseModel):
    budget_line_id: int


def _get_fiscal_year(fiscal_year_be: int, db: Session) -> FiscalYear:
    fy = db.query(FiscalYear).filter(FiscalYear.year_be == fiscal_year_be).first()
    if not fy:
        raise HTTPException(status_code=404, detail=f"Fiscal year {fiscal_year_be} not found")
    return fy


def _line_key(fiscal_year_be: int, line: BudgetLine) -> tuple:
    return BudgetImportService.budget_key(
        fiscal_year_be,
        line.department or "",
        line.division or "",
        line.expense_type or "",
        line.appropriation_category or "",
    )


def _existing_lines_by_key(fiscal_year_be: int, db: Session) -> dict[tuple, list[BudgetLine]]:
    lines = db.query(BudgetLine).join(FiscalYear).filter(FiscalYear.year_be == fiscal_year_be).all()
    result: dict[tuple, list[BudgetLine]] = {}
    for line in lines:
        result.setdefault(_line_key(fiscal_year_be, line), []).append(line)
    return result


def _deducted_amount(line_id: int, db: Session) -> float:
    return db.query(func.sum(ExpenseLedger.amount_deducted)).filter(
        ExpenseLedger.budget_line_id == line_id
    ).scalar() or 0.0


def _budget_response(line: BudgetLine, db: Session) -> BudgetLineResponse:
    deducted = _deducted_amount(line.id, db)
    return BudgetLineResponse(
        id=line.id,
        department=line.department,
        division=line.division,
        expense_type=line.expense_type,
        appropriation_category=line.appropriation_category or "",
        initial_amount=line.initial_amount,
        deducted_amount=deducted,
        available_amount=line.initial_amount - deducted,
        fiscal_year_be=line.fiscal_year.year_be,
    )


@router.post("/import/sheets")
async def list_import_sheets(file: UploadFile = File(...)):
    content = await file.read()
    try:
        sheet_names = BudgetImportService.list_sheet_names(content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "source_hash": BudgetImportService.source_hash(content),
        "sheet_names": sheet_names,
    }


@router.post("/import/preview")
async def preview_budget_import(
    fiscal_year_be: int = Form(...),
    sheet_name: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    _get_fiscal_year(fiscal_year_be, db)
    content = await file.read()
    try:
        preview = BudgetImportService.preview_budget_lines(content, fiscal_year_be, sheet_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    existing = _existing_lines_by_key(fiscal_year_be, db)
    for row in preview["rows"]:
        key = BudgetImportService.budget_key(
            fiscal_year_be,
            row["department"],
            row["division"],
            row["expense_type"],
            row["appropriation_category"],
        )
        matches = existing.get(key, [])
        row["import_action"] = "create" if not matches else "update"
        if len(matches) > 1:
            row["valid"] = False
            row["errors"].append("existing database contains duplicate budget key")
            preview["errors"].append(f"row {row['row_number']}: existing database contains duplicate budget key")

    preview["valid"] = preview["valid"] and not preview["errors"]
    return preview


@router.post("/import/commit")
async def commit_budget_import(
    fiscal_year_be: int = Form(...),
    source_hash: str = Form(...),
    sheet_name: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    fy = _get_fiscal_year(fiscal_year_be, db)
    content = await file.read()
    actual_hash = BudgetImportService.source_hash(content)
    if actual_hash != source_hash:
        raise HTTPException(status_code=400, detail="Uploaded file does not match preview source hash")

    try:
        preview = BudgetImportService.preview_budget_lines(content, fiscal_year_be, sheet_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not preview["valid"]:
        raise HTTPException(status_code=400, detail={"message": "Import preview is not valid", "errors": preview["errors"]})

    created = 0
    updated = 0
    existing = _existing_lines_by_key(fiscal_year_be, db)
    batch_id = actual_hash[:16]

    for row in preview["rows"]:
        key = BudgetImportService.budget_key(
            fiscal_year_be,
            row["department"],
            row["division"],
            row["expense_type"],
            row["appropriation_category"],
        )
        matches = existing.get(key, [])
        if len(matches) > 1:
            raise HTTPException(status_code=400, detail="Existing database contains duplicate budget key")
        if matches:
            line = matches[0]
            line.initial_amount = row["initial_amount"]
            line.source_import_batch_id = batch_id
            line.source_row_number = row["row_number"]
            updated += 1
        else:
            line = BudgetLine(
                fiscal_year_id=fy.id,
                department=row["department"],
                division=row["division"],
                expense_type=row["expense_type"],
                appropriation_category=row["appropriation_category"],
                initial_amount=row["initial_amount"],
                source_import_batch_id=batch_id,
                source_row_number=row["row_number"],
            )
            db.add(line)
            existing.setdefault(key, []).append(line)
            created += 1

    db.commit()
    return {
        "message": "Import committed",
        "source_hash": actual_hash,
        "selected_sheet": preview["selected_sheet"],
        "created": created,
        "updated": updated,
        "lines_processed": created + updated,
    }


@router.get("/", response_model=list[BudgetLineResponse])
def get_budgets(fiscal_year_be: int = None, db: Session = Depends(get_db)):
    query = db.query(BudgetLine).join(FiscalYear)
    if fiscal_year_be:
        query = query.filter(FiscalYear.year_be == fiscal_year_be)
    return [_budget_response(line, db) for line in query.order_by(BudgetLine.id.asc()).all()]


@router.get("/cases/{case_id}/match")
def get_case_budget_match(case_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if case.budget_line_id:
        line = db.query(BudgetLine).filter(BudgetLine.id == case.budget_line_id).first()
        if line:
            return {"status": "selected", "selected": _budget_response(line, db), "candidates": []}

    query = db.query(BudgetLine).join(FiscalYear).filter(
        FiscalYear.year_be == case.fiscal_year_be,
        BudgetLine.department == case.department,
        BudgetLine.expense_type == case.expense_group,
    )
    if case.division:
        query = query.filter(BudgetLine.division == case.division)
    candidates = [_budget_response(line, db) for line in query.order_by(BudgetLine.id.asc()).all()]
    if len(candidates) == 1:
        return {"status": "matched", "selected": candidates[0], "candidates": candidates}
    if len(candidates) > 1:
        return {"status": "ambiguous", "selected": None, "candidates": candidates}
    return {"status": "not_found", "selected": None, "candidates": []}


@router.post("/cases/{case_id}/selection")
def select_case_budget_line(case_id: int, payload: BudgetSelectionRequest, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    line = db.query(BudgetLine).join(FiscalYear).filter(
        BudgetLine.id == payload.budget_line_id,
        FiscalYear.year_be == case.fiscal_year_be,
    ).first()
    if not line:
        raise HTTPException(status_code=404, detail="Budget line not found for case fiscal year")
    case.budget_line_id = line.id
    db.commit()
    db.refresh(case)
    return {"case_id": case.id, "budget_line_id": line.id, "selected": _budget_response(line, db)}
