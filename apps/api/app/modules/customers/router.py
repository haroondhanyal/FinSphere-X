from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import current_user, require_permission
from app.modules.identity.models import AuditLog, Customer, KycDocument, User

router = APIRouter(prefix="/customers", tags=["Customers and KYC"])
UPLOAD_DIR = Path(__file__).resolve().parents[3] / "uploads" / "kyc"
PROFILE_IMAGE_DIR = UPLOAD_DIR.parent / "profile"
ALLOWED_TYPES = {"application/pdf", "image/jpeg", "image/png"}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
PROFILE_IMAGE_TYPES = {
    "image/jpeg": (".jpg", b"\xff\xd8\xff"),
    "image/png": (".png", b"\x89PNG\r\n\x1a\n"),
    "image/webp": (".webp", b"RIFF"),
}
MAX_PROFILE_IMAGE_BYTES = 10 * 1024 * 1024


class KycUpdate(BaseModel):
    nationality: str = Field(min_length=2, max_length=80)


class ProfileUpdate(BaseModel):
    full_name: str = Field(min_length=2, max_length=160)
    phone: str = Field(default="", max_length=40)
    country: str = Field(default="", max_length=100)
    state: str = Field(default="", max_length=100)
    city: str = Field(default="", max_length=100)


class KycReview(BaseModel):
    decision: str = Field(pattern="^(approved|rejected|additional_information_required)$")
    reason: str = Field(default="", max_length=500)


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
        "country": customer.country,
        "state": customer.state,
        "city": customer.city,
        "has_profile_image": bool(customer.profile_image_filename),
        "nationality": customer.nationality,
        "kyc_status": customer.kyc_status,
    }


@router.patch("/me")
def update_profile(
    body: ProfileUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    customer = customer_for(db, user)
    full_name = body.full_name.strip()
    if len(full_name) < 2:
        raise HTTPException(422, "Full name must contain at least two characters")
    customer.full_name = full_name
    customer.phone = body.phone.strip()
    customer.country = body.country.strip()
    customer.state = body.state.strip()
    customer.city = body.city.strip()
    db.add(AuditLog(user_id=user.id, action="profile.updated", resource="customer", resource_id=str(customer.id)))
    db.commit()
    return {"message": "Profile updated"}


@router.post("/me/profile-image", status_code=201)
async def upload_profile_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    file_type = PROFILE_IMAGE_TYPES.get(file.content_type or "")
    if not file_type:
        raise HTTPException(415, "Upload a JPEG, PNG, or WebP image")
    content = await file.read(MAX_PROFILE_IMAGE_BYTES + 1)
    if len(content) > MAX_PROFILE_IMAGE_BYTES:
        raise HTTPException(413, "Profile image must be 10 MB or smaller")
    extension, signature = file_type
    if not content.startswith(signature) or (file.content_type == "image/webp" and content[8:12] != b"WEBP"):
        raise HTTPException(415, "The uploaded file is not a valid image")

    customer = customer_for(db, user)
    if customer.profile_image_filename:
        (PROFILE_IMAGE_DIR / customer.profile_image_filename).unlink(missing_ok=True)
    filename = f"{uuid4().hex}{extension}"
    PROFILE_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    (PROFILE_IMAGE_DIR / filename).write_bytes(content)
    customer.profile_image_filename = filename
    db.commit()
    return {"has_profile_image": True}


@router.get("/me/profile-image")
def get_profile_image(db: Session = Depends(get_db), user: User = Depends(current_user)):
    customer = customer_for(db, user)
    if not customer.profile_image_filename:
        raise HTTPException(404, "No profile image is set")
    path = PROFILE_IMAGE_DIR / customer.profile_image_filename
    if not path.is_file():
        raise HTTPException(404, "Profile image file not found")
    return FileResponse(path)


@router.delete("/me/profile-image")
def delete_profile_image(db: Session = Depends(get_db), user: User = Depends(current_user)):
    customer = customer_for(db, user)
    if customer.profile_image_filename:
        (PROFILE_IMAGE_DIR / customer.profile_image_filename).unlink(missing_ok=True)
        customer.profile_image_filename = None
        db.commit()
    return {"has_profile_image": False}


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


@router.get("/{customer_id}/kyc/review-details")
def get_kyc_review_details(
    customer_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission("kyc:review")),
):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(404, "Customer not found")
    documents = db.query(KycDocument).filter_by(customer_id=customer.id).order_by(KycDocument.created_at.desc()).all()
    return {
        "id": customer.id,
        "full_name": customer.full_name,
        "email": customer.user.email,
        "phone": customer.phone,
        "country": customer.country,
        "state": customer.state,
        "city": customer.city,
        "nationality": customer.nationality,
        "kyc_status": customer.kyc_status,
        "documents": [
            {"id": document.id, "document_type": document.document_type, "status": document.status, "created_at": document.created_at}
            for document in documents
        ],
    }


@router.get("/{customer_id}/kyc/documents/{document_id}/view")
def view_kyc_document(
    customer_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission("kyc:review")),
):
    document = db.query(KycDocument).filter_by(id=document_id, customer_id=customer_id).first()
    if not document:
        raise HTTPException(404, "KYC document not found")
    path = UPLOAD_DIR / document.filename
    if not path.is_file():
        raise HTTPException(404, "KYC document file not found")
    return FileResponse(
        path,
        filename=f"{document.document_type}{path.suffix}",
        content_disposition_type="inline",
    )


@router.get("/")
def list_customers(
    db: Session = Depends(get_db), _user: User = Depends(require_permission("customers:read"))
):
    customers = db.query(Customer).order_by(Customer.id).all()
    document_counts = dict(
        db.query(KycDocument.customer_id, func.count(KycDocument.id))
        .group_by(KycDocument.customer_id)
        .all()
    )
    return [
        {
            "id": c.id,
            "full_name": c.full_name,
            "email": c.user.email,
            "kyc_status": c.kyc_status,
            "document_count": document_counts.get(c.id, 0),
        }
        for c in customers
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
    reason = body.reason.strip()
    if body.decision != "approved" and len(reason) < 5:
        raise HTTPException(422, "A decision note of at least five characters is required")
    customer.kyc_status = body.decision
    db.add(
        AuditLog(
            user_id=user.id,
            action="kyc.reviewed",
            resource="customer",
            resource_id=str(customer.id),
            detail=f"{body.decision}: {reason}".rstrip(": "),
        )
    )
    db.commit()
    return {"customer_id": customer.id, "kyc_status": customer.kyc_status}
