from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import os

from src.product.db.session import get_db
from src.product.db.models import Case, SourceDocument

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
