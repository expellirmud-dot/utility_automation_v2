from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import os
import datetime

from src.product.db.session import get_db
from src.product.db.models import Case, SourceDocument, BillHeader
from src.product.services.workflow_lifecycle import WorkflowLifecycleService
from src.workflows.unified_bill_pipeline import UnifiedBillPipeline

router = APIRouter(prefix="/api/cases", tags=["Documents"])

@router.post("/{case_id}/documents")
async def upload_document(
    case_id: int,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    db: Session = Depends(get_db)
):
    # 1. Verify case exists
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # 2. Save file to disk under data/uploads/{case_id}
    upload_dir = os.path.join("data", "uploads", str(case_id))
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Extract file type (extension)
    _, ext = os.path.splitext(file.filename)
    file_type = ext.lower().replace(".", "")

    # 3. Create SourceDocument record
    db_doc = SourceDocument(
        case_id=case_id,
        file_name=file.filename,
        file_path=file_path,
        file_type=file_type,
        document_type=document_type
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)

    WorkflowLifecycleService.record_event(
        db,
        case,
        "document_uploaded",
        f"Uploaded document {file.filename} ({document_type})"
    )

    return {
        "id": db_doc.id,
        "case_id": db_doc.case_id,
        "file_name": db_doc.file_name,
        "file_path": db_doc.file_path,
        "file_type": db_doc.file_type,
        "document_type": db_doc.document_type,
        "created_at": db_doc.created_at
    }

@router.post("/{case_id}/documents/{document_id}/process")
def process_document(
    case_id: int,
    document_id: int,
    db: Session = Depends(get_db)
):
    # 1. Verify case and document exist
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    doc = db.query(SourceDocument).filter(SourceDocument.id == document_id, SourceDocument.case_id == case_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # 2. Run the extraction pipeline
    try:
        bill = UnifiedBillPipeline.run(doc.file_path)
    except Exception as e:
        # Save a failed bill header
        bill_hdr = db.query(BillHeader).filter(BillHeader.document_id == document_id).first()
        if not bill_hdr:
            bill_hdr = BillHeader(document_id=document_id)
            db.add(bill_hdr)
        bill_hdr.provider = None
        bill_hdr.bill_date = None
        bill_hdr.total_amount = 0.0
        bill_hdr.status = "failed"
        db.commit()
        db.refresh(bill_hdr)
        raise HTTPException(status_code=500, detail=f"OCR/Extraction failed: {str(e)}")

    # 3. Parse date
    parsed_date = None
    if bill.bill_date:
        try:
            parsed_date = datetime.date.fromisoformat(bill.bill_date)
        except Exception:
            pass

    # 4. Save/Update BillHeader (persist all extracted fields)
    bill_hdr = db.query(BillHeader).filter(BillHeader.document_id == document_id).first()
    if not bill_hdr:
        bill_hdr = BillHeader(document_id=document_id)
        db.add(bill_hdr)

    bill_hdr.provider = bill.vendor_name
    bill_hdr.bill_date = parsed_date
    bill_hdr.total_amount = bill.total if bill.total is not None else 0.0
    # Persist new fields if the pipeline exposes them (graceful fallback)
    if hasattr(bill, "invoice_no") and bill.invoice_no:
        bill_hdr.invoice_no = bill.invoice_no
    if hasattr(bill, "vat_amount") and bill.vat_amount is not None:
        bill_hdr.vat_amount = bill.vat_amount
    if hasattr(bill, "withholding_tax") and bill.withholding_tax is not None:
        bill_hdr.withholding_tax = bill.withholding_tax
    bill_hdr.status = "extracted"

    db.commit()
    db.refresh(bill_hdr)

    WorkflowLifecycleService.record_event(
        db,
        case,
        "ocr_success",
        f"Extracted bill data successfully from {doc.file_name}"
    )

    return {
        "id": bill_hdr.id,
        "document_id": bill_hdr.document_id,
        "provider": bill_hdr.provider,
        "invoice_no": bill_hdr.invoice_no,
        "bill_date": bill_hdr.bill_date,
        "total_amount": bill_hdr.total_amount,
        "vat_amount": bill_hdr.vat_amount,
        "withholding_tax": bill_hdr.withholding_tax,
        "status": bill_hdr.status,
        "created_at": bill_hdr.created_at
    }


class BillHeaderUpdate(BaseModel):
    provider: Optional[str] = None
    invoice_no: Optional[str] = None
    bill_date: Optional[str] = None  # ISO date string YYYY-MM-DD
    total_amount: Optional[float] = None
    vat_amount: Optional[float] = None
    withholding_tax: Optional[float] = None


@router.patch("/{case_id}/documents/{document_id}/bill")
def update_bill_header(
    case_id: int,
    document_id: int,
    payload: BillHeaderUpdate,
    db: Session = Depends(get_db)
):
    """Allow operator to manually correct extracted BillHeader values."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    doc = db.query(SourceDocument).filter(SourceDocument.id == document_id, SourceDocument.case_id == case_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    bill_hdr = db.query(BillHeader).filter(BillHeader.document_id == document_id).first()
    if not bill_hdr:
        raise HTTPException(status_code=404, detail="No BillHeader found — run OCR first")

    # Apply only fields that were provided
    if payload.provider is not None:
        bill_hdr.provider = payload.provider
    if payload.invoice_no is not None:
        bill_hdr.invoice_no = payload.invoice_no
    if payload.bill_date is not None:
        try:
            bill_hdr.bill_date = datetime.date.fromisoformat(payload.bill_date)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid bill_date format, expected YYYY-MM-DD")
    if payload.total_amount is not None:
        bill_hdr.total_amount = payload.total_amount
    if payload.vat_amount is not None:
        bill_hdr.vat_amount = payload.vat_amount
    if payload.withholding_tax is not None:
        bill_hdr.withholding_tax = payload.withholding_tax

    db.commit()
    db.refresh(bill_hdr)

    WorkflowLifecycleService.record_event(
        db,
        case,
        "ocr_corrected",
        f"Operator manually corrected bill data for document {doc.file_name}"
    )

    return {
        "id": bill_hdr.id,
        "document_id": bill_hdr.document_id,
        "provider": bill_hdr.provider,
        "invoice_no": bill_hdr.invoice_no,
        "bill_date": bill_hdr.bill_date,
        "total_amount": bill_hdr.total_amount,
        "vat_amount": bill_hdr.vat_amount,
        "withholding_tax": bill_hdr.withholding_tax,
        "status": bill_hdr.status,
        "created_at": bill_hdr.created_at
    }
