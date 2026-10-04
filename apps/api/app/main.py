import logging
import threading
import time
from collections import Counter
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from app.core.config import settings
from app.core.database import SessionLocal
from app.modules.accounts import models as account_models  # noqa: F401
from app.modules.accounts.router import router as accounts_router
from app.modules.cards import models as card_models  # noqa: F401
from app.modules.cards.router import router as cards_router
from app.modules.customers.router import router as customers_router
from app.modules.identity import models as identity_models  # noqa: F401
from app.modules.identity.router import router as identity_router
from app.modules.members.router import router as members_router
from app.modules.payments.router import router as payments_router
from app.modules.phase5_8 import models as phase5_8_models  # noqa: F401
from app.modules.phase5_8.router import router as phase5_8_router
from app.modules.phase9_11 import models as phase9_11_models  # noqa: F401
from app.modules.phase9_11.router import router as phase9_11_router
from app.modules.workspace import models as workspace_models  # noqa: F401
from app.modules.workspace.router import router as workspace_router

app = FastAPI(
    title="FinSphere X API",
    version="0.1.0",
    description="FinSphere X banking and financial operations API",
)
logger = logging.getLogger("finsphere.api")
metrics_lock = threading.Lock()
request_counts: Counter[tuple[str, int]] = Counter()
request_durations: Counter[str] = Counter()


@app.middleware("http")
async def request_observability(request, call_next):
    request_id = uuid4().hex
    start = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        elapsed = time.perf_counter() - start
        with metrics_lock:
            request_counts[(request.method, status_code)] += 1
            request_durations[request.method] += elapsed
        route = getattr(request.scope.get("route"), "path", "unmatched")
        logger.info("http_request", extra={"request_id": request_id, "method": request.method, "route": route, "status_code": status_code, "duration_seconds": round(elapsed, 6)})
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_web_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-API-Key"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "finsphere-api"}


@app.get("/ready")
def ready():
    from sqlalchemy import text

    with SessionLocal() as db:
        db.execute(text("SELECT 1"))
    return {"status": "ready", "database": "ok"}


@app.get("/metrics", include_in_schema=False, response_class=PlainTextResponse)
def metrics():
    lines = ["# HELP finspherex_http_requests_total Total HTTP requests.", "# TYPE finspherex_http_requests_total counter"]
    with metrics_lock:
        counts = dict(request_counts)
        durations = dict(request_durations)
    for (method, status), count in sorted(counts.items()):
        lines.append(f'finspherex_http_requests_total{{method="{method}",status="{status}"}} {count}')
    lines.extend(["# HELP finspherex_http_request_duration_seconds_sum Request duration sum by method.", "# TYPE finspherex_http_request_duration_seconds_sum counter"])
    for method, duration in sorted(durations.items()):
        lines.append(f'finspherex_http_request_duration_seconds_sum{{method="{method}"}} {duration:.6f}')
    return "\n".join(lines) + "\n"


for route in (identity_router, customers_router, accounts_router, payments_router, cards_router, phase5_8_router, phase9_11_router, members_router, workspace_router):
    app.include_router(route, prefix="/api/v1")
