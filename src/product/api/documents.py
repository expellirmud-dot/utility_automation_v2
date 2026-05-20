from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import os
import datetime

from src.product.db.session import get_db
from src.product.db.models import Case, SourceDocument, BillHeader
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

    # 4. Save/Update BillHeader
    bill_hdr = db.query(BillHeader).filter(BillHeader.document_id == document_id).first()
    if not bill_hdr:
        bill_hdr = BillHeader(document_id=document_id)
        db.add(bill_hdr)

    bill_hdr.provider = bill.vendor_name
    bill_hdr.bill_date = parsed_date
    bill_hdr.total_amount = bill.total if bill.total is not None else 0.0
    bill_hdr.status = "extracted"

    db.commit()
    db.refresh(bill_hdr)

    return {
        "id": bill_hdr.id,
        "document_id": bill_hdr.document_id,
        "provider": bill_hdr.provider,
        "bill_date": bill_hdr.bill_date,
        "total_amount": bill_hdr.total_amount,
        "status": bill_hdr.status,
        "created_at": bill_hdr.created_at
    }
