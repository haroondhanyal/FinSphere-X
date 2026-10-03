from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.modules.accounts import models as account_models  # noqa: F401
from app.modules.accounts.router import router as accounts_router
from app.modules.cards import models as card_models  # noqa: F401
from app.modules.cards.router import router as cards_router
from app.modules.customers.router import router as customers_router
from app.modules.identity import models as identity_models  # noqa: F401
from app.modules.identity.router import router as identity_router
from app.modules.payments.router import router as payments_router

app = FastAPI(
    title="FinSphere X API",
    version="0.1.0",
    description="FinSphere X banking and financial operations API",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "finsphere-api"}


for route in (identity_router, customers_router, accounts_router, payments_router, cards_router):
    app.include_router(route, prefix="/api/v1")
