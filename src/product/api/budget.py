from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel, ConfigDict

from src.product.db.session import get_db
from src.product.db.models import BudgetLine, FiscalYear
from src.product.services.excel_import import ExcelImportService

router = APIRouter(prefix="/api/budget", tags=["Budget"])

class BudgetLineResponse(BaseModel):
    id: int
    department: str
    division: str
    expense_type: str
    initial_amount: float
    fiscal_year_be: int

    model_config = ConfigDict(from_attributes=True)

@router.post("/import")
async def import_budget(fiscal_year_be: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Verify fiscal year exists
    fy = db.query(FiscalYear).filter(FiscalYear.year_be == fiscal_year_be).first()
    if not fy:
        raise HTTPException(status_code=404, detail=f"Fiscal year {fiscal_year_be} not found")
        
    content = await file.read()
    try:
        budget_lines_data = ExcelImportService.parse_budget_lines(content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    inserted_count = 0
    for data in budget_lines_data:
        # Check if exists
        existing = db.query(BudgetLine).filter(
            BudgetLine.fiscal_year_id == fy.id,
            BudgetLine.department == data["department"],
            BudgetLine.division == data["division"],
            BudgetLine.expense_type == data["expense_type"]
        ).first()
        
        if existing:
            existing.initial_amount = data["initial_amount"]
        else:
            new_line = BudgetLine(
                fiscal_year_id=fy.id,
                department=data["department"],
                division=data["division"],
                expense_type=data["expense_type"],
                initial_amount=data["initial_amount"]
            )
            db.add(new_line)
        inserted_count += 1
        
    db.commit()
    return {"message": "Import successful", "lines_processed": inserted_count}

@router.get("/", response_model=List[BudgetLineResponse])
def get_budgets(fiscal_year_be: int = None, db: Session = Depends(get_db)):
    query = db.query(BudgetLine).join(FiscalYear)
    if fiscal_year_be:
        query = query.filter(FiscalYear.year_be == fiscal_year_be)
        
    lines = query.all()
    
    result = []
    for line in lines:
        result.append(BudgetLineResponse(
            id=line.id,
            department=line.department,
            division=line.division,
            expense_type=line.expense_type,
            initial_amount=line.initial_amount,
            fiscal_year_be=line.fiscal_year.year_be
        ))
        
    return result
