from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.product.db.session import get_db
from src.product.db.models import Case
from src.product.services.readiness_validator import ReadinessValidator

router = APIRouter(prefix="/api/cases", tags=["validation"])

@router.get("/{case_id}/readiness")
def get_case_readiness(case_id: int, db: Session = Depends(get_db)):
    """Evaluate if a case is ready for final submission."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    return ReadinessValidator.evaluate_readiness(case, db)
