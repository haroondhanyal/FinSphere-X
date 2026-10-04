import hashlib
import hmac
import json
import secrets
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import func
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.database import get_db
from app.core.security import current_user, require_roles
from app.modules.accounts.models import Account, FinancialTransaction
from app.modules.customers.router import customer_for
from app.modules.identity.models import AuditLog, Customer, User
from app.modules.phase9_11.models import (
    BankingConsent,
    DeveloperApiClient,
    InvestmentProduct,
    PortfolioPosition,
    RemittanceRequest,
    WebhookDelivery,
    WebhookEndpoint,
)
from app.modules.phase9_11.ai import generate_file_text, generate_text, provider_enabled

router = APIRouter(tags=["Investments, AI and developer platform"])
STAFF = ("operations", "admin")
FX = {
    ("PKR", "USD"): Decimal("0.00357"),
    ("USD", "PKR"): Decimal("280.00"),
    ("PKR", "EUR"): Decimal("0.00330"),
    ("EUR", "PKR"): Decimal("303.00"),
    ("PKR", "AED"): Decimal("0.01311"),
    ("AED", "PKR"): Decimal("76.28"),
    ("USD", "EUR"): Decimal("0.9230"),
    ("EUR", "USD"): Decimal("1.0834"),
}
COUNTRY_CURRENCY = {"US": "USD", "GB": "GBP", "AE": "AED", "EU": "EUR", "SA": "SAR"}


class PositionInput(BaseModel):
    product_code: str = Field(min_length=2, max_length=60)
    amount: Decimal = Field(gt=0, le=Decimal("100000000"))


class RemittanceInput(BaseModel):
    source_account_id: int = Field(gt=0)
    amount: Decimal = Field(gt=0, le=Decimal("100000000"))
    destination_country: str = Field(pattern="^[A-Z]{2}$")


class RemittanceDecision(BaseModel):
    decision: str = Field(pattern="^(approved|rejected|more_information_required)$")


class ConsentInput(BaseModel):
    provider_name: str = Field(min_length=2, max_length=120)
    scopes: list[str] = Field(min_length=1, max_length=8)
    duration_days: int = Field(default=90, ge=1, le=365)


class ApiClientInput(BaseModel):
    name: str = Field(min_length=2, max_length=120)


class WebhookInput(BaseModel):
    url: HttpUrl
    event_types: list[str] = Field(min_length=1, max_length=12)


class CopilotInput(BaseModel):
    source_text: str = Field(min_length=3, max_length=12000)
    consent: bool


class DocumentInput(BaseModel):
    document_text: str = Field(min_length=3, max_length=12000)
    document_type: str = Field(min_length=2, max_length=60)
    consent: bool


class CopilotConsent(BaseModel):
    consent: bool


def own_position_query(db: Session, user: User):
    customer = customer_for(db, user)
    return db.query(PortfolioPosition).filter_by(customer_id=customer.id)


def require_developer_key(
    api_key: str = Header(default="", alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> DeveloperApiClient:
    if not api_key.startswith("fsx_test_") or len(api_key) > 128:
        raise HTTPException(401, "A valid sandbox API key is required", headers={"WWW-Authenticate": "ApiKey"})
    prefix = api_key[:16]
    digest = hashlib.sha256(api_key.encode()).hexdigest()
    candidates = db.query(DeveloperApiClient).filter_by(key_prefix=prefix, active=True).all()
    for candidate in candidates:
        if candidate.secret_hash and hmac.compare_digest(candidate.secret_hash, digest):
            return candidate
    raise HTTPException(401, "A valid sandbox API key is required", headers={"WWW-Authenticate": "ApiKey"})


@router.get("/developer/v1/me")
def developer_key_identity(client: DeveloperApiClient = Depends(require_developer_key)):
    return {"client_id": client.id, "name": client.name, "environment": "sandbox", "permissions": ["accounts:read", "transactions:read"]}


@router.get("/developer/v1/accounts")
def developer_key_accounts(
    db: Session = Depends(get_db),
    client: DeveloperApiClient = Depends(require_developer_key),
):
    customer = db.query(Customer).filter_by(user_id=client.owner_user_id).first()
    if not customer:
        return []
    rows = db.query(Account).filter_by(customer_id=customer.id).order_by(Account.id).all()
    return [{"id": row.id, "account_number_masked": f"••••{row.account_number[-4:]}", "currency": row.currency, "balance": str(row.balance), "status": row.status} for row in rows]


@router.get("/developer/v1/transactions")
def developer_key_transactions(
    db: Session = Depends(get_db),
    client: DeveloperApiClient = Depends(require_developer_key),
):
    customer = db.query(Customer).filter_by(user_id=client.owner_user_id).first()
    if not customer:
        return []
    rows = db.query(FinancialTransaction).filter_by(customer_id=customer.id).order_by(FinancialTransaction.created_at.desc()).limit(100).all()
    return [{"id": row.id, "type": row.transaction_type, "amount": str(row.amount), "currency": row.currency, "status": row.status, "created_at": row.created_at} for row in rows]


@router.get("/investments/products")
def investment_products(db: Session = Depends(get_db), _user: User = Depends(current_user)):
    rows = db.query(InvestmentProduct).filter_by(active=True).order_by(InvestmentProduct.name).all()
    return [{"code": row.code, "name": row.name, "description": row.description, "annual_yield": str(row.annual_yield), "minimum_amount": str(row.minimum_amount), "currency": row.currency, "disclosure": "Simulated product; returns are illustrative and not guaranteed."} for row in rows]


@router.post("/investments/positions", status_code=201)
def create_position(body: PositionInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    customer = customer_for(db, user)
    product = db.query(InvestmentProduct).filter_by(code=body.product_code, active=True).first()
    if not product:
        raise HTTPException(404, "Investment product not found")
    if body.amount < product.minimum_amount:
        raise HTTPException(422, "Amount is below this product's minimum")
    row = PortfolioPosition(customer_id=customer.id, product_code=product.code, principal=body.amount, currency=product.currency)
    db.add(row)
    db.add(AuditLog(user_id=user.id, action="investment.position_simulated", resource="portfolio_position", detail=product.code))
    db.commit()
    db.refresh(row)
    return {"id": row.id, "product_code": row.product_code, "principal": str(row.principal), "currency": row.currency, "status": row.status, "disclosure": "Position recorded for simulation only; no investment was purchased."}


@router.get("/investments/portfolio")
def portfolio(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = own_position_query(db, user).order_by(PortfolioPosition.created_at.desc()).all()
    products = {item.code: item for item in db.query(InvestmentProduct).all()}
    result = []
    for row in rows:
        product = products.get(row.product_code)
        value = row.principal
        if product:
            value += (row.principal * product.annual_yield / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        result.append({"id": row.id, "product_code": row.product_code, "product_name": product.name if product else row.product_code, "principal": str(row.principal), "illustrative_value": str(value), "currency": row.currency, "status": row.status})
    return {"positions": result, "disclosure": "Illustrative one-year projection only; no market prices, accruals, or investment execution."}


@router.get("/treasury/liquidity")
def liquidity(db: Session = Depends(get_db), _user: User = Depends(require_roles(*STAFF))):
    rows = db.query(Account.currency, func.coalesce(func.sum(Account.balance), 0)).filter_by(status="active").group_by(Account.currency).all()
    return {"balances": [{"currency": currency, "total": str(amount)} for currency, amount in rows], "source": "Local demo account balances", "as_of": datetime.now(UTC)}


@router.get("/fx/quote")
def fx_quote(
    source_currency: str = Query(pattern="^[A-Z]{3}$"),
    destination_currency: str = Query(pattern="^[A-Z]{3}$"),
    amount: Decimal = Query(gt=0),
    _user: User = Depends(current_user),
):
    if source_currency == destination_currency:
        rate = Decimal("1")
    else:
        rate = FX.get((source_currency, destination_currency))
        if rate is None:
            raise HTTPException(422, "Currency pair is unavailable in the demo quote table")
    destination_amount = (amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return {"source_currency": source_currency, "destination_currency": destination_currency, "source_amount": str(amount), "rate": str(rate), "destination_amount": str(destination_amount), "expires_at": datetime.now(UTC) + timedelta(minutes=5), "disclosure": "Static demonstration rate; not a tradable or guaranteed quote."}


@router.post("/remittances", status_code=201)
def create_remittance(body: RemittanceInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    customer = customer_for(db, user)
    account = db.query(Account).filter_by(id=body.source_account_id, customer_id=customer.id).first()
    if not account:
        raise HTTPException(404, "Source account not found")
    destination_currency = COUNTRY_CURRENCY.get(body.destination_country)
    if not destination_currency:
        raise HTTPException(422, "Destination country is not enabled in the demo")
    rate = FX.get((account.currency, destination_currency))
    if not rate:
        raise HTTPException(422, "Currency pair is unavailable in the demo quote table")
    if body.amount > account.balance:
        raise HTTPException(422, "Insufficient source balance")
    row = RemittanceRequest(customer_id=customer.id, source_account_id=account.id, destination_country=body.destination_country, source_amount=body.amount, source_currency=account.currency, destination_currency=destination_currency, destination_amount=(body.amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), quoted_rate=rate)
    db.add(row)
    db.add(AuditLog(user_id=user.id, action="remittance.requested", resource="remittance_request", detail=f"{body.destination_country}:{body.amount}"))
    db.commit()
    db.refresh(row)
    return {"id": row.id, "source_amount": str(row.source_amount), "source_currency": row.source_currency, "destination_amount": str(row.destination_amount), "destination_currency": row.destination_currency, "quoted_rate": str(row.quoted_rate), "status": row.status, "disclosure": "Request for operations review only. No funds are debited or sent."}


@router.get("/remittances")
def list_remittances(db: Session = Depends(get_db), user: User = Depends(current_user)):
    query = db.query(RemittanceRequest)
    if user.role not in STAFF:
        customer = customer_for(db, user)
        query = query.filter_by(customer_id=customer.id)
    rows = query.order_by(RemittanceRequest.created_at.desc()).all()
    return [{"id": row.id, "destination_country": row.destination_country, "source_amount": str(row.source_amount), "source_currency": row.source_currency, "destination_amount": str(row.destination_amount), "destination_currency": row.destination_currency, "status": row.status, "created_at": row.created_at} for row in rows]


@router.patch("/remittances/{remittance_id}")
def review_remittance(remittance_id: int, body: RemittanceDecision, db: Session = Depends(get_db), user: User = Depends(require_roles(*STAFF))):
    row = db.get(RemittanceRequest, remittance_id)
    if not row:
        raise HTTPException(404, "Remittance request not found")
    if row.status != "pending_review":
        raise HTTPException(409, "Remittance has already been reviewed")
    row.status = body.decision
    db.add(AuditLog(user_id=user.id, action="remittance.reviewed", resource="remittance_request", resource_id=str(row.id), detail=body.decision))
    db.commit()
    return {"id": row.id, "status": row.status, "disclosure": "Review status only; no funds were transferred."}


@router.post("/copilot/transactions/{transaction_id}/explanation")
def explain_transaction(transaction_id: int, body: CopilotConsent, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if not body.consent:
        raise HTTPException(422, "Confirm consent before requesting AI assistance")
    row = db.get(FinancialTransaction, transaction_id)
    if not row:
        raise HTTPException(404, "Transaction not found")
    if user.role not in STAFF:
        customer = customer_for(db, user)
        if row.customer_id != customer.id:
            raise HTTPException(404, "Transaction not found")
    facts = {
        "transaction_type": row.transaction_type,
        "amount": str(row.amount),
        "currency": row.currency,
        "status": row.status,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }
    summary = generate_text(
        "Explain the supplied transaction facts in plain language. Use only those facts, "
        "say when information is missing, and do not give financial advice or recommend "
        "an action. Keep the answer under 100 words.",
        json.dumps(facts),
        max_output_tokens=180,
    )
    ai_used = summary is not None
    if summary is None:
        summary = f"{row.transaction_type.title()} for {row.amount} {row.currency}, status {row.status}."
    return {"summary": summary, "sources": [{"type": "transaction", "id": row.id}], "human_review_required": True, "ai_used": ai_used, "provider": "openai" if ai_used else "local_fallback", "disclosure": "AI-generated explanation from transaction metadata; verify against the source. No financial advice or automated decision is provided." if ai_used else "Local template explanation; configure OPENAI_API_KEY to enable AI-generated assistance."}


@router.get("/copilot/status")
def copilot_status(_user: User = Depends(current_user)):
    return {
        "ai_enabled": provider_enabled(),
        "provider": "openai" if provider_enabled() else "local_fallback",
        "model": settings.openai_model if provider_enabled() else None,
        "disclosure": "When enabled, submitted source text and limited transaction facts are sent to the configured OpenAI API. Do not submit information without authorization.",
    }


@router.post("/copilot/summarize")
def summarize_text(body: CopilotInput, _user: User = Depends(current_user)):
    if not body.consent:
        raise HTTPException(422, "Confirm consent before submitting source text")
    summary = generate_text(
        "Summarize the supplied source in 3 concise bullet points. Use only information in "
        "the source, preserve uncertainty, and do not infer financial advice or decisions.",
        body.source_text,
        max_output_tokens=300,
    )
    if summary is not None:
        return {"summary": summary, "source_length": len(body.source_text), "human_review_required": True, "ai_used": True, "provider": "openai", "disclosure": "AI-generated summary; check it against the original source."}
    sentences = [part.strip() for part in body.source_text.replace("\n", " ").split(".") if part.strip()]
    return {"summary": ". ".join(sentences[:3])[:900], "source_length": len(body.source_text), "human_review_required": True, "ai_used": False, "provider": "local_fallback", "disclosure": "Extractive local summary; configure OPENAI_API_KEY to enable AI-generated assistance. Verify against the source before acting."}


@router.post("/copilot/documents/extract")
def extract_document(body: DocumentInput, _user: User = Depends(current_user)):
    import re

    if not body.consent:
        raise HTTPException(422, "Confirm consent before submitting document text")
    extracted = generate_text(
        "Extract only explicitly present dates and monetary amounts from the supplied "
        "document text. Return one JSON object with string arrays named amount_candidates "
        "and date_candidates. Do not infer missing values. The document type is "
        + body.document_type
        + ".",
        body.document_text,
        max_output_tokens=350,
    )
    if extracted is not None:
        try:
            candidates = json.loads(extracted)
            amounts = candidates.get("amount_candidates", [])
            dates = candidates.get("date_candidates", [])
            if not isinstance(amounts, list) or not isinstance(dates, list):
                raise ValueError("Expected candidate arrays")
        except (json.JSONDecodeError, AttributeError, ValueError) as exc:
            raise HTTPException(status_code=503, detail="AI provider returned an invalid extraction. Please retry.") from exc
        return {"document_type": body.document_type, "amount_candidates": [str(value)[:100] for value in amounts[:20]], "date_candidates": [str(value)[:40] for value in dates[:20]], "source_excerpt": body.document_text[:400], "human_review_required": True, "ai_used": True, "provider": "openai", "disclosure": "AI extraction from supplied text; verify every field against the original document."}

    amounts = re.findall(r"(?<!\w)(?:PKR|USD|EUR|GBP|AED|SAR)?\s?\d[\d,]*(?:\.\d{1,2})?", body.document_text)
    dates = re.findall(r"\b\d{4}-\d{2}-\d{2}\b", body.document_text)
    return {"document_type": body.document_type, "amount_candidates": amounts[:20], "date_candidates": dates[:20], "source_excerpt": body.document_text[:400], "human_review_required": True, "ai_used": False, "provider": "local_fallback", "disclosure": "Pattern extraction only; configure OPENAI_API_KEY to enable AI assistance. Verify candidates against the original document."}


@router.post("/copilot/documents/extract-upload")
async def extract_document_upload(
    document_type: str = Form(min_length=2, max_length=60),
    consent: bool = Form(),
    file: UploadFile = File(...),
    _user: User = Depends(current_user),
):
    if not consent:
        raise HTTPException(422, "Confirm consent before uploading a document")
    if not provider_enabled():
        raise HTTPException(503, "Configure OPENAI_API_KEY to extract uploaded documents")
    mime_type = file.content_type or ""
    if mime_type not in {"application/pdf", "image/png", "image/jpeg", "image/webp"}:
        raise HTTPException(415, "Upload a PDF, PNG, JPEG, or WebP document")
    contents = await file.read(6 * 1024 * 1024 + 1)
    if not contents or len(contents) > 6 * 1024 * 1024:
        raise HTTPException(413, "Document must be between 1 byte and 6 MB")
    valid_signature = (
        (mime_type == "application/pdf" and contents.startswith(b"%PDF-"))
        or (mime_type == "image/png" and contents.startswith(b"\x89PNG\r\n\x1a\n"))
        or (mime_type == "image/jpeg" and contents.startswith(b"\xff\xd8\xff"))
        or (mime_type == "image/webp" and contents.startswith(b"RIFF") and contents[8:12] == b"WEBP")
    )
    if not valid_signature:
        raise HTTPException(415, "The uploaded document content does not match its file type")
    filename = (file.filename or "document").replace("\n", " ").replace("\r", " ")[:120]
    output = await run_in_threadpool(
        generate_file_text,
        document_type,
        filename,
        mime_type,
        contents,
        max_output_tokens=400,
    )
    try:
        candidates = json.loads(output or "")
        amounts = candidates["amount_candidates"]
        dates = candidates["date_candidates"]
        if not isinstance(amounts, list) or not isinstance(dates, list):
            raise ValueError("Expected candidate arrays")
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=503, detail="AI provider returned an invalid extraction. Please retry.") from exc
    return {
        "document_type": document_type,
        "filename": filename,
        "amount_candidates": [str(value)[:100] for value in amounts[:20]],
        "date_candidates": [str(value)[:40] for value in dates[:20]],
        "human_review_required": True,
        "ai_used": True,
        "provider": "openai",
        "disclosure": "AI extracted candidates from the uploaded file. Verify every field against the original document.",
    }


@router.post("/copilot/forecast")
def forecast(body: CopilotConsent, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if not body.consent:
        raise HTTPException(422, "Confirm consent before requesting transaction analysis")
    customer = customer_for(db, user)
    rows = db.query(FinancialTransaction).filter_by(customer_id=customer.id).order_by(FinancialTransaction.created_at.desc()).limit(30).all()
    total_outflow = sum((row.amount for row in rows if row.status == "posted"), Decimal("0"))
    period_count = max(1, min(3, len(rows)))
    average = (total_outflow / period_count).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    forecast_note = generate_text(
        "Explain these historical transaction aggregates and their simple average in at "
        "plain language. Do not change or calculate the supplied values, imply certainty, "
        "or provide financial advice. State that a small local history is not predictive.",
        json.dumps({"observed_transactions": len(rows), "recent_posted_total": str(total_outflow), "illustrative_next_period": str(average), "currency": rows[0].currency if rows else None}),
        max_output_tokens=180,
    )
    return {"observed_transactions": len(rows), "recent_posted_total": str(total_outflow), "illustrative_next_period": str(average), "source_transaction_ids": [row.id for row in rows], "human_review_required": True, "ai_used": forecast_note is not None, "provider": "openai" if forecast_note else "local_fallback", "explanation": forecast_note, "disclosure": "AI explains a simple historical average; the arithmetic is computed by the application. This is not predictive financial advice." if forecast_note else "Simple historical average over local demo transactions; not an AI forecast or financial advice. Configure OPENAI_API_KEY for AI-generated context."}


@router.get("/open-banking/providers")
def sandbox_providers(_user: User = Depends(current_user)):
    return [{"id": "demo-bank-a", "name": "Demo Bank A", "status": "sandbox_only"}, {"id": "demo-bank-b", "name": "Demo Bank B", "status": "sandbox_only"}]


@router.post("/open-banking/consents", status_code=201)
def create_consent(body: ConsentInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    allowed = {"accounts:read", "balances:read", "transactions:read"}
    if not set(body.scopes) <= allowed:
        raise HTTPException(422, "Consent contains unsupported scopes")
    row = BankingConsent(user_id=user.id, provider_name=body.provider_name, scopes=json.dumps(sorted(set(body.scopes))), expires_at=datetime.now(UTC) + timedelta(days=body.duration_days))
    db.add(row)
    db.add(AuditLog(user_id=user.id, action="open_banking.consent_created", resource="banking_consent", detail=body.provider_name))
    db.commit()
    db.refresh(row)
    return {"id": row.id, "provider_name": row.provider_name, "scopes": json.loads(row.scopes), "status": row.status, "expires_at": row.expires_at, "disclosure": "Consent is recorded in a local sandbox; no external provider is contacted."}


@router.get("/open-banking/consents")
def list_consents(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.query(BankingConsent).filter_by(user_id=user.id).order_by(BankingConsent.created_at.desc()).all()
    return [{"id": row.id, "provider_name": row.provider_name, "scopes": json.loads(row.scopes), "status": row.status, "expires_at": row.expires_at} for row in rows]


@router.post("/open-banking/consents/{consent_id}/revoke")
def revoke_consent(consent_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    row = db.query(BankingConsent).filter_by(id=consent_id, user_id=user.id).first()
    if not row:
        raise HTTPException(404, "Consent not found")
    if row.status != "active":
        raise HTTPException(409, "Consent is already inactive")
    row.status = "revoked"
    row.revoked_at = datetime.now(UTC)
    db.add(AuditLog(user_id=user.id, action="open_banking.consent_revoked", resource="banking_consent", resource_id=str(row.id)))
    db.commit()
    return {"id": row.id, "status": row.status}


@router.post("/developer/clients", status_code=201)
def create_api_client(body: ApiClientInput, db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    secret = "fsx_test_" + secrets.token_urlsafe(32)
    digest = hashlib.sha256(secret.encode()).hexdigest()
    row = DeveloperApiClient(owner_user_id=user.id, name=body.name, key_prefix=secret[:16], secret_hash=digest)
    db.add(row)
    db.add(AuditLog(user_id=user.id, action="developer.api_client_created", resource="developer_api_client", detail=body.name))
    db.commit()
    db.refresh(row)
    return {"id": row.id, "name": row.name, "key_prefix": row.key_prefix, "api_key": secret, "active": row.active, "warning": "Copy this test key now; it cannot be retrieved again. Sandbox only."}


@router.get("/developer/clients")
def list_api_clients(db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    rows = db.query(DeveloperApiClient).filter_by(owner_user_id=user.id).order_by(DeveloperApiClient.created_at.desc()).all()
    return [{"id": row.id, "name": row.name, "key_prefix": row.key_prefix, "active": row.active, "created_at": row.created_at} for row in rows]


@router.post("/developer/clients/{client_id}/revoke")
def revoke_api_client(client_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    row = db.query(DeveloperApiClient).filter_by(id=client_id, owner_user_id=user.id).first()
    if not row:
        raise HTTPException(404, "API client not found")
    row.active = False
    row.revoked_at = datetime.now(UTC)
    db.add(AuditLog(user_id=user.id, action="developer.api_client_revoked", resource="developer_api_client", resource_id=str(row.id)))
    db.commit()
    return {"id": row.id, "active": row.active}


@router.post("/developer/webhooks", status_code=201)
def create_webhook(body: WebhookInput, db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    url = str(body.url)
    if not url.startswith("https://") and not url.startswith("http://localhost"):
        raise HTTPException(422, "Webhook URLs must use HTTPS (localhost is allowed for development)")
    secret = secrets.token_urlsafe(32)
    row = WebhookEndpoint(owner_user_id=user.id, url=url, event_types=json.dumps(sorted(set(body.event_types))), secret_hash=hashlib.sha256(secret.encode()).hexdigest())
    db.add(row)
    db.add(AuditLog(user_id=user.id, action="developer.webhook_created", resource="webhook_endpoint", detail=url))
    db.commit()
    db.refresh(row)
    return {"id": row.id, "url": row.url, "event_types": json.loads(row.event_types), "secret": secret, "status": "active", "warning": "Signing secret is shown once. Deliveries are sandbox records only."}


@router.get("/developer/webhooks")
def list_webhooks(db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    rows = db.query(WebhookEndpoint).filter_by(owner_user_id=user.id).order_by(WebhookEndpoint.created_at.desc()).all()
    return [{"id": row.id, "url": row.url, "event_types": json.loads(row.event_types), "active": row.active} for row in rows]


@router.post("/developer/webhooks/{endpoint_id}/test-delivery", status_code=201)
def test_webhook_delivery(endpoint_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    endpoint = db.query(WebhookEndpoint).filter_by(id=endpoint_id, owner_user_id=user.id, active=True).first()
    if not endpoint:
        raise HTTPException(404, "Active webhook endpoint not found")
    event_type = json.loads(endpoint.event_types)[0]
    row = WebhookDelivery(endpoint_id=endpoint.id, event_type=event_type, payload=json.dumps({"id": f"evt_{secrets.token_hex(8)}", "type": event_type, "created_at": datetime.now(UTC).isoformat()}))
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "event_type": row.event_type, "status": row.status, "disclosure": "Recorded locally; the target URL was not called."}


@router.get("/developer/webhooks/deliveries")
def list_webhook_deliveries(db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    rows = db.query(WebhookDelivery).join(WebhookEndpoint, WebhookDelivery.endpoint_id == WebhookEndpoint.id).filter(WebhookEndpoint.owner_user_id == user.id).order_by(WebhookDelivery.created_at.desc()).all()
    return [{"id": row.id, "endpoint_id": row.endpoint_id, "event_type": row.event_type, "payload": json.loads(row.payload), "status": row.status, "attempt_count": row.attempt_count} for row in rows]
