from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import current_user, require_permission
from app.modules.identity.models import AuditLog, Customer, KycDocument, User

router = APIRouter(prefix="/customers", tags=["Customers and KYC"])
UPLOAD_DIR = Path(__file__).resolve().parents[3] / "uploads" / "kyc"
ALLOWED_TYPES = {"application/pdf", "image/jpeg", "image/png"}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024


class KycUpdate(BaseModel):
    nationality: str = Field(min_length=2, max_length=80)


class KycReview(BaseModel):
    decision: str = Field(pattern="^(approved|rejected|additional_information_required)$")


def customer_for(db: Session, user: User) -> Customer:
    customer = db.query(Customer).filter_by(user_id=user.id).first()
    if not customer:
        raise HTTPException(404, "Customer profile not found")
    return customer


@router.get("/me")
def get_profile(db: Session = Depends(get_db), user: User = Depends(current_user)):
    customer = customer_for(db, user)
    return {
        "id": customer.id,
        "full_name": customer.full_name,
        "email": user.email,
        "phone": customer.phone,
        "nationality": customer.nationality,
        "kyc_status": customer.kyc_status,
    }


@router.patch("/me/kyc")
def update_kyc(body: KycUpdate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    customer = customer_for(db, user)
    customer.nationality = body.nationality
    customer.kyc_status = "under_review"
    db.commit()
    return {"kyc_status": customer.kyc_status}


@router.post("/me/kyc/documents", status_code=201)
async def upload_kyc_document(
    document_type: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(415, "Upload a PDF, PNG, or JPEG document")
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "File exceeds the 5 MB limit")
    customer = customer_for(db, user)
    storage_name = f"{uuid4().hex}{Path(file.filename or 'document').suffix.lower()}"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    (UPLOAD_DIR / storage_name).write_bytes(content)
    record = KycDocument(
        customer_id=customer.id, document_type=document_type[:60], filename=storage_name
    )
    db.add(record)
    customer.kyc_status = "under_review"
    db.commit()
    db.refresh(record)
    return {"id": record.id, "document_type": record.document_type, "status": record.status}


@router.get("/me/kyc/documents")
def list_documents(db: Session = Depends(get_db), user: User = Depends(current_user)):
    customer = customer_for(db, user)
    return [
        {
            "id": d.id,
            "document_type": d.document_type,
            "status": d.status,
            "created_at": d.created_at,
        }
        for d in db.query(KycDocument).filter_by(customer_id=customer.id).all()
    ]


@router.get("/me/kyc/documents/{document_id}/download")
def download_document(
    document_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)
):
    customer = customer_for(db, user)
    record = db.query(KycDocument).filter_by(id=document_id, customer_id=customer.id).first()
    if not record:
        raise HTTPException(404, "Document not found")
    path = UPLOAD_DIR / record.filename
    if not path.is_file():
        raise HTTPException(404, "Document file not found")
    return FileResponse(path)


@router.get("/")
def list_customers(
    db: Session = Depends(get_db), _user: User = Depends(require_permission("customers:read"))
):
    return [
        {"id": c.id, "full_name": c.full_name, "kyc_status": c.kyc_status}
        for c in db.query(Customer).order_by(Customer.id).all()
    ]


@router.post("/{customer_id}/kyc/review")
def review_kyc(
    customer_id: int,
    body: KycReview,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("kyc:review")),
):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(404, "Customer not found")
    customer.kyc_status = body.decision
    db.add(
        AuditLog(
            user_id=user.id,
            action="kyc.reviewed",
            resource="customer",
            resource_id=str(customer.id),
            detail=body.decision,
        )
    )
    db.commit()
    return {"customer_id": customer.id, "kyc_status": customer.kyc_status}
