"""
e-LAAS Assist API routes for PRODUCT-006.

GET  /api/cases/{case_id}/elaas-payload        - Build and return payload (read-only)
POST /api/cases/{case_id}/elaas-payload/save   - Persist ElaasPayload record
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.product.db.session import get_db
from src.product.db.models import Case, ElaasPayload
from src.product.services.elaas_payload_builder import ElaasPayloadBuilder
from src.product.services.workflow_lifecycle import WorkflowLifecycleService

router = APIRouter(prefix="/api/cases", tags=["e-LAAS"])


@router.get("/{case_id}/elaas-payload")
def get_elaas_payload(case_id: int, db: Session = Depends(get_db)):
    """Build and return the e-LAAS submission payload for this case (read-only, no save)."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    payload = ElaasPayloadBuilder.build(case, db)
    return payload


@router.post("/{case_id}/elaas-payload/save")
def save_elaas_payload(case_id: int, db: Session = Depends(get_db)):
    """Persist the prepared e-LAAS payload. Does NOT submit to e-LAAS."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    payload = ElaasPayloadBuilder.build(case, db)
    record = ElaasPayloadBuilder.save(case, payload, db)

    WorkflowLifecycleService.record_event(
        db,
        case,
        "elaas_payload_saved",
        "Saved e-LAAS submission payload data"
    )

    return {
        "elaas_payload_id": record.id,
        "status": record.status,
        "case_id": case_id,
        "message": "Payload saved. Operator must submit to e-LAAS manually.",
    }
