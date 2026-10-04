import hashlib
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password, verify_password
from app.modules.accounts import models as account_models  # noqa: F401
from app.modules.accounts.models import (
    Account,
    Beneficiary,
    FinancialTransaction,
    JournalEntry,
    JournalLine,
    LedgerAccount,
    Wallet,
)
from app.modules.cards.models import Card
from app.modules.identity.models import AuthSession, Customer, KycDocument, RolePermission, User
from app.modules.phase5_8 import models as phase5_8_models  # noqa: F401
from app.modules.phase5_8.models import (
    BnplInstallment,
    BnplPlan,
    BusinessExpenseClaim,
    BusinessInvoice,
    BusinessOrganization,
    FeeRule,
    LoanApplication,
    LoanInstallment,
    LoanProduct,
    MerchantDispute,
    MerchantSale,
    MerchantSettlement,
    PayrollBatch,
    ReconciliationRun,
    RiskCase,
    ScreeningRun,
)
from app.modules.phase9_11 import models as phase9_11_models  # noqa: F401
from app.modules.phase9_11.models import (
    BankingConsent,
    DeveloperApiClient,
    InvestmentProduct,
    PortfolioPosition,
    RemittanceRequest,
    WebhookDelivery,
    WebhookEndpoint,
)

Base.metadata.create_all(bind=engine)


def _ensure(db, model, filters: dict, **values):
    row = db.query(model).filter_by(**filters).first()
    if row is None:
        row = model(**values)
        db.add(row)
        db.flush()
    return row


def _demo_pdf(name: str) -> bytes:
    lines = [
        "FinSphere X - SIMULATED DEMO ONLY",
        f"Fictional KYC sample for {name}",
        "This is not a real identity document.",
    ]
    commands = ["BT", "/F1 18 Tf", "55 760 Td"]
    for index, line in enumerate(lines):
        safe_line = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        if index:
            commands.append("0 -28 Td")
        commands.append(f"({safe_line}) Tj")
    commands.append("ET")
    stream = "\n".join(commands).encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    document = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, body in enumerate(objects, start=1):
        offsets.append(len(document))
        document.extend(f"{index} 0 obj\n".encode("ascii") + body + b"\nendobj\n")
    xref = len(document)
    document.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
    document.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        document.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    document.extend(
        f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii")
    )
    return bytes(document)


def seed_demo_workflows(db):
    from pathlib import Path

    def customer(email):
        user = db.query(User).filter_by(email=email).one()
        return user, user.customer, db.query(Account).filter_by(customer_id=user.customer.id).first()

    customers = [customer(f"customer{suffix}@finspherex.com") for suffix in ("", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12")]
    admin = db.query(User).filter_by(email="admin@finspherex.com").one()

    # Customers and cards: make each customer workspace useful after login.
    for index, (user, profile, account) in enumerate(customers, start=1):
        if index <= 8:
            _ensure(
                db,
                Card,
                {"customer_id": profile.id, "last4": f"{4100 + index}"},
                customer_id=profile.id,
                account_id=account.id,
                last4=f"{4100 + index}",
                card_type="debit",
                status="active" if index % 3 else "inactive",
                daily_limit=Decimal("100000.00"),
            )
        _ensure(
            db,
            Beneficiary,
            {"customer_id": profile.id, "account_number": f"DEMO{profile.id:08d}"},
            customer_id=profile.id,
            name=f"Demo beneficiary {index}",
            account_number=f"DEMO{profile.id:08d}",
            bank_name="FinSphere Demo Bank",
            currency="PKR",
            is_verified=True,
        )

    # Pending KYC cases include actual, clearly fictional preview documents.
    kyc_dir = Path(__file__).resolve().parents[1] / "uploads" / "kyc"
    kyc_dir.mkdir(parents=True, exist_ok=True)
    for email in ("customer8@finspherex.com", "customer10@finspherex.com"):
        _, profile, _ = customer(email)
        filename = f"demo-kyc-customer-{profile.id}.pdf"
        path = kyc_dir / filename
        if not path.exists():
            path.write_bytes(_demo_pdf(profile.full_name))
        document = _ensure(
            db,
            KycDocument,
            {"customer_id": profile.id, "filename": filename},
            customer_id=profile.id,
            document_type="Illustrative identity sample",
            filename=filename,
            status="pending_review",
        )
        if document.status == "pending_review":
            profile.kyc_status = "under_review"

    # Posted sample ledger activity for account history, statements and finance.
    cash = _ensure(db, LedgerAccount, {"code": "DEMO-CASH-PKR"}, code="DEMO-CASH-PKR", name="Demo settlement cash", currency="PKR")
    for index, (_, profile, account) in enumerate(customers[:8], start=1):
        reference = f"DEMO-TXN-{index:04d}"
        transaction = _ensure(
            db,
            FinancialTransaction,
            {"reference": reference},
            reference=reference,
            idempotency_key=f"demo-seed-{reference}",
            customer_id=profile.id,
            source_account_id=account.id,
            transaction_type="deposit",
            amount=Decimal("12500.00") + Decimal(index * 250),
            fee=Decimal("0.00"),
            currency="PKR",
            status="posted",
        )
        liability = _ensure(
            db,
            LedgerAccount,
            {"code": f"DEMO-CUSTOMER-{profile.id}"},
            code=f"DEMO-CUSTOMER-{profile.id}",
            name=f"Demo customer balance {index}",
            currency="PKR",
        )
        journal = _ensure(
            db,
            JournalEntry,
            {"transaction_id": transaction.id},
            transaction_id=transaction.id,
            reference=f"J-{reference}",
        )
        _ensure(
            db,
            JournalLine,
            {"journal_entry_id": journal.id, "ledger_account_id": cash.id},
            journal_entry_id=journal.id,
            ledger_account_id=cash.id,
            debit=transaction.amount,
            credit=Decimal("0"),
        )
        _ensure(
            db,
            JournalLine,
            {"journal_entry_id": journal.id, "ledger_account_id": liability.id},
            journal_entry_id=journal.id,
            ledger_account_id=liability.id,
            debit=Decimal("0"),
            credit=transaction.amount,
        )

    # Loan, BNPL, investment and remittance examples for customer products.
    for index, (_, profile, account) in enumerate(customers[:4], start=1):
        loan = _ensure(
            db,
            LoanApplication,
            {"purpose": f"DEMO: education support {index}"},
            customer_id=profile.id,
            product_code="personal",
            purpose=f"DEMO: education support {index}",
            requested_amount=Decimal("180000.00") + Decimal(index * 10000),
            currency="PKR",
            term_months=12,
            annual_rate=Decimal("18.00"),
            monthly_payment=Decimal("18000.00") + Decimal(index * 1000),
            illustrative_score=680 + index * 15,
            score_reasons="Illustrative seeded case; review all details before deciding.",
            status="submitted" if index <= 2 else "approved",
        )
        for installment_number in range(1, 4):
            _ensure(
                db,
                LoanInstallment,
                {"loan_id": loan.id, "installment_number": installment_number},
                loan_id=loan.id,
                installment_number=installment_number,
                due_at=datetime.now(UTC) + timedelta(days=30 * installment_number),
                amount=loan.monthly_payment,
                status="scheduled",
            )
        plan = _ensure(
            db,
            BnplPlan,
            {"customer_id": profile.id, "merchant_name": f"Demo Market {index}"},
            customer_id=profile.id,
            merchant_name=f"Demo Market {index}",
            purchase_amount=Decimal("40000.00"),
            currency="PKR",
            installment_count=4,
            installment_amount=Decimal("10000.00"),
            status="active",
        )
        for installment_number in range(1, 5):
            _ensure(
                db,
                BnplInstallment,
                {"plan_id": plan.id, "installment_number": installment_number},
                plan_id=plan.id,
                installment_number=installment_number,
                due_at=datetime.now(UTC) + timedelta(days=14 * installment_number),
                amount=Decimal("10000.00"),
                status="scheduled",
            )
        _ensure(
            db,
            PortfolioPosition,
            {"customer_id": profile.id, "product_code": "demo-balanced"},
            customer_id=profile.id,
            product_code="demo-balanced",
            principal=Decimal("25000.00") + Decimal(index * 5000),
            currency="PKR",
            status="simulated_active",
        )
        if index == 1:
            _ensure(
                db,
                RemittanceRequest,
                {"customer_id": profile.id, "destination_country": "AE", "source_amount": Decimal("25000.00")},
                customer_id=profile.id,
                source_account_id=account.id,
                destination_country="AE",
                source_amount=Decimal("25000.00"),
                source_currency="PKR",
                destination_amount=Decimal("327.50"),
                destination_currency="AED",
                quoted_rate=Decimal("0.0131"),
                status="pending_review",
            )
        consent = _ensure(
            db,
            BankingConsent,
            {"user_id": customers[index - 1][0].id, "provider_name": "Demo Open Banking Provider"},
            user_id=customers[index - 1][0].id,
            provider_name="Demo Open Banking Provider",
            scopes=json.dumps(["accounts:read", "transactions:read"]),
            status="active",
            expires_at=datetime.now(UTC) + timedelta(days=90),
        )
        consent.scopes = json.dumps(["accounts:read", "transactions:read"])

    # Organization workflows: one pending review item, plus active business data.
    organizations = db.query(BusinessOrganization).all()
    for organization in organizations:
        owner = db.get(User, organization.user_id)
        if not owner or not owner.email.endswith("@finspherex.com"):
            continue
        if organization.status != "active":
            continue
        if owner.role == "business":
            _ensure(
                db,
                BusinessInvoice,
                {"invoice_number": f"DEMO-INV-{organization.id:04d}"},
                organization_id=organization.id,
                invoice_number=f"DEMO-INV-{organization.id:04d}",
                customer_name="Demo Retail Client",
                amount=Decimal("85000.00"),
                currency="PKR",
                status="issued",
            )
            _ensure(
                db,
                PayrollBatch,
                {"organization_id": organization.id, "pay_period": "2026-10"},
                organization_id=organization.id,
                pay_period="2026-10",
                employee_count=8,
                total_amount=Decimal("640000.00"),
                currency="PKR",
                status="pending_approval",
            )
            _ensure(
                db,
                BusinessExpenseClaim,
                {"organization_id": organization.id, "description": "DEMO: office equipment"},
                organization_id=organization.id,
                claimant_name="Demo Employee",
                description="DEMO: office equipment",
                amount=Decimal("28500.00"),
                currency="PKR",
                evidence_reference="DEMO-RECEIPT-OFFICE-01",
                status="pending_approval",
            )
        elif owner.role == "merchant":
            sale = _ensure(
                db,
                MerchantSale,
                {"reference": f"DEMO-SALE-{organization.id:04d}"},
                organization_id=organization.id,
                reference=f"DEMO-SALE-{organization.id:04d}",
                description="DEMO: online order #1001",
                amount=Decimal("18500.00"),
                currency="PKR",
                status="captured_demo",
            )
            _ensure(
                db,
                MerchantDispute,
                {"sale_id": sale.id},
                organization_id=organization.id,
                sale_id=sale.id,
                reason="DEMO: customer says order was not received",
                evidence_reference="DEMO-DELIVERY-PROOF-1001",
                status="open",
            )
            settlement = _ensure(
                db,
                MerchantSettlement,
                {"reference": f"DEMO-SET-{organization.id:04d}"},
                organization_id=organization.id,
                reference=f"DEMO-SET-{organization.id:04d}",
                gross_amount=Decimal("18500.00"),
                fee_amount=Decimal("277.50"),
                net_amount=Decimal("18222.50"),
                currency="PKR",
                status="simulated",
            )
            if settlement.status == "pending_review":
                settlement.status = "simulated"

    risk_customer = customers[2][1]
    _ensure(
        db,
        RiskCase,
        {"summary": "DEMO: unusual transaction velocity"},
        customer_id=risk_customer.id,
        category="transaction_monitoring",
        summary="DEMO: unusual transaction velocity",
        score=72,
        status="open",
        notes="Synthetic review case; verify the linked sample activity.",
        evidence_reference="DEMO-EVIDENCE-VELOCITY-01",
    )
    _ensure(
        db,
        ScreeningRun,
        {"subject_name": "Demo Sample Company", "category": "sanctions"},
        created_by=admin.id,
        subject_name="Demo Sample Company",
        category="sanctions",
        score=12,
        result="possible_match",
        rationale="Synthetic sample result for review workflow demonstration.",
    )
    _ensure(
        db,
        ReconciliationRun,
        {"source": "DEMO: acquiring settlement file"},
        created_by=admin.id,
        source="DEMO: acquiring settlement file",
        ledger_total=Decimal("125000.00"),
        external_total=Decimal("124500.00"),
        status="variance",
        notes="Illustrative variance for the reconciliation review workflow.",
    )

    # Developer console has a masked test key and a queued test event.
    _ensure(
        db,
        DeveloperApiClient,
        {"key_prefix": "fsx_demo_"},
        owner_user_id=admin.id,
        name="FinSphere demo integration",
        key_prefix="fsx_demo_",
        secret_hash=hashlib.sha256(b"demo-only-placeholder-key-never-valid").hexdigest(),
        active=True,
    )
    endpoint = _ensure(
        db,
        WebhookEndpoint,
        {"owner_user_id": admin.id, "url": "https://example.test/finsphere-webhook"},
        owner_user_id=admin.id,
        url="https://example.test/finsphere-webhook",
        event_types="payment.posted,account.updated",
        secret_hash=hashlib.sha256(b"demo-only-webhook-secret-never-valid").hexdigest(),
        active=True,
    )
    _ensure(
        db,
        WebhookDelivery,
        {"endpoint_id": endpoint.id, "event_type": "payment.posted"},
        endpoint_id=endpoint.id,
        event_type="payment.posted",
        payload='{"demo":true,"reference":"DEMO-TXN-0001"}',
        status="queued_demo",
        attempt_count=0,
    )

roles = {
    "customer": ["accounts:read:self", "payments:create:self", "cards:manage:self"],
    "operations": ["customers:read", "payments:read", "kyc:review", "loan:review", "business:review", "finance:read", "risk:manage"],
    "admin": ["customers:read", "kyc:review", "roles:manage", "products:manage", "audit:read", "loan:review", "business:review", "finance:read", "risk:manage"],
    "business": ["business:manage"],
    "merchant": ["merchant:settlements:manage"],
}

with SessionLocal() as db:
    if not db.query(InvestmentProduct).filter_by(code="demo-income").first():
        db.add(InvestmentProduct(code="demo-income", name="Demo income portfolio", description="Illustrative fixed income position", annual_yield=Decimal("8.0"), minimum_amount=Decimal("1000")))
    if not db.query(InvestmentProduct).filter_by(code="demo-balanced").first():
        db.add(InvestmentProduct(code="demo-balanced", name="Demo balanced portfolio", description="Illustrative diversified portfolio", annual_yield=Decimal("6.5"), minimum_amount=Decimal("5000")))
    if not db.query(LoanProduct).filter_by(code="personal").first():
        db.add(LoanProduct(code="personal", name="Personal loan", description="Illustrative unsecured personal loan", annual_rate=Decimal("18.0"), minimum_amount=Decimal("10000"), maximum_amount=Decimal("5000000"), minimum_term_months=3, maximum_term_months=60))
    if not db.query(LoanProduct).filter_by(code="salary_advance").first():
        db.add(LoanProduct(code="salary_advance", name="Salary advance", description="Illustrative short-term salary advance", annual_rate=Decimal("12.0"), minimum_amount=Decimal("5000"), maximum_amount=Decimal("500000"), minimum_term_months=3, maximum_term_months=12))
    if not db.query(FeeRule).filter_by(code="merchant_settlement").first():
        db.add(FeeRule(code="merchant_settlement", description="Illustrative merchant settlement fee", percentage=Decimal("1.5")))
    for role, permissions in roles.items():
        for permission in permissions:
            if not db.query(RolePermission).filter_by(role=role, permission=permission).first():
                db.add(RolePermission(role=role, permission=permission))
    demo_password = "FinSphere-Demo-2026!"
    admin_demo_password = "admin12345678"
    for email, name, role in (
        ("customer@finspherex.com", "Amina Demo", "customer"),
        ("customer2@finspherex.com", "Bilal Demo", "customer"),
        ("customer3@finspherex.com", "Sara Demo", "customer"),
        ("customer4@finspherex.com", "Hamza Demo", "customer"),
        ("customer5@finspherex.com", "Noor Demo", "customer"),
        ("customer6@finspherex.com", "Zain Demo", "customer"),
        ("operations@finspherex.com", "Operations Demo", "operations"),
        ("operations2@finspherex.com", "Operations Two Demo", "operations"),
        ("operations3@finspherex.com", "Operations Three Demo", "operations"),
        ("admin@finspherex.com", "Admin Demo", "admin"),
        ("admin2@finspherex.com", "Admin Two Demo", "admin"),
        ("business@finspherex.com", "Business Demo", "business"),
        ("business2@finspherex.com", "Business Two Demo", "business"),
        ("merchant@finspherex.com", "Merchant Demo", "merchant"),
        ("merchant2@finspherex.com", "Merchant Two Demo", "merchant"),
        ("customer7@finspherex.com", "Hira Demo", "customer"),
        ("customer8@finspherex.com", "Omar Demo", "customer"),
        ("customer9@finspherex.com", "Mariam Demo", "customer"),
        ("customer10@finspherex.com", "Usman Demo", "customer"),
        ("customer11@finspherex.com", "Zoya Demo", "customer"),
        ("customer12@finspherex.com", "Ibrahim Demo", "customer"),
        ("operations4@finspherex.com", "Operations Four Demo", "operations"),
        ("admin3@finspherex.com", "Admin Three Demo", "admin"),
        ("business3@finspherex.com", "Business Three Demo", "business"),
        ("merchant3@finspherex.com", "Merchant Three Demo", "merchant"),
    ):
        user = db.query(User).filter_by(email=email).first()
        if user:
            if role == "admin" and verify_password(demo_password, user.password_hash):
                user.password_hash = hash_password(admin_demo_password)
                for session in db.query(AuthSession).filter_by(user_id=user.id).all():
                    if not session.revoked_at:
                        session.revoked_at = datetime.now(UTC)
            continue
        password = admin_demo_password if role == "admin" else demo_password
        user = User(email=email, password_hash=hash_password(password), role=role)
        db.add(user)
        db.flush()
        customer = Customer(user_id=user.id, full_name=name, kyc_status="approved")
        db.add(customer)
        db.flush()
        db.add(
            Account(
                customer_id=customer.id,
                account_number=f"FSX{customer.id:010d}",
                balance=Decimal("250000.00"),
                currency="PKR",
            )
        )
        db.add(
            Wallet(
                customer_id=customer.id,
                balance=Decimal("12500.00"),
                currency="PKR",
                level="verified",
            )
        )
        if role in ("business", "merchant"):
            org_status = "pending_review" if email == "business3@finspherex.com" else "active"
            db.add(BusinessOrganization(user_id=user.id, legal_name=f"{name} Company", status=org_status))
    db.commit()

    seed_demo_workflows(db)
    db.commit()

print("Seeded 25 demo users plus sample records for the product workflows.")
print("Admin password: admin12345678; other accounts: FinSphere-Demo-2026!")
