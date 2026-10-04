from decimal import Decimal

from app.core.security import create_access_token, hash_password
from app.modules.accounts.models import Account
from app.modules.identity.models import Customer, User
from app.modules.phase9_11.models import InvestmentProduct

PASSWORD = "Extended-Phase-Test-2026!"


def register(client, email):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD, "full_name": "Phase Tester"},
    )
    assert response.status_code == 201, response.text
    login = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_investment_position_is_owned_and_does_not_debit_account(client):
    http, sessions = client
    headers = register(http, "investor@example.org")
    with sessions() as db:
        db.add(InvestmentProduct(code="test-fund", name="Test fund", description="Fixture", annual_yield=Decimal("5"), minimum_amount=Decimal("100")))
        user = db.query(User).filter_by(email="investor@example.org").one()
        customer = db.query(Customer).filter_by(user_id=user.id).one()
        account = db.query(Account).filter_by(customer_id=customer.id).one()
        account.balance = Decimal("500.0000")
        account_id = account.id
        db.commit()

    created = http.post("/api/v1/investments/positions", headers=headers, json={"product_code": "test-fund", "amount": "250"})
    assert created.status_code == 201, created.text
    assert "no investment was purchased" in created.json()["disclosure"]
    portfolio = http.get("/api/v1/investments/portfolio", headers=headers)
    assert len(portfolio.json()["positions"]) == 1
    with sessions() as db:
        assert db.get(Account, account_id).balance == Decimal("500.0000")


def test_fx_remittance_consent_and_revocation_are_recorded(client):
    http, sessions = client
    owner_headers = register(http, "consent-owner@example.org")
    other_headers = register(http, "consent-other@example.org")
    with sessions() as db:
        owner = db.query(User).filter_by(email="consent-owner@example.org").one()
        customer = db.query(Customer).filter_by(user_id=owner.id).one()
        account = db.query(Account).filter_by(customer_id=customer.id).one()
        account.balance = Decimal("1000.0000")
        account_id = account.id
        db.commit()

    quote = http.get("/api/v1/fx/quote?source_currency=PKR&destination_currency=USD&amount=100", headers=owner_headers)
    assert quote.status_code == 200 and quote.json()["destination_amount"] == "0.36"
    request = http.post("/api/v1/remittances", headers=owner_headers, json={"source_account_id": account_id, "amount": "100", "destination_country": "US"})
    assert request.status_code == 201, request.text
    with sessions() as db:
        assert db.get(Account, account_id).balance == Decimal("1000.0000")

    consent = http.post("/api/v1/open-banking/consents", headers=owner_headers, json={"provider_name": "Demo Bank A", "scopes": ["accounts:read", "balances:read"], "duration_days": 30})
    assert consent.status_code == 201, consent.text
    consent_id = consent.json()["id"]
    assert http.post(f"/api/v1/open-banking/consents/{consent_id}/revoke", headers=other_headers).status_code == 404
    assert http.post(f"/api/v1/open-banking/consents/{consent_id}/revoke", headers=owner_headers).json()["status"] == "revoked"


def test_developer_credentials_are_one_time_and_webhook_delivery_is_sandbox_only(client):
    http, sessions = client
    with sessions() as db:
        admin = User(email="developer-admin@example.org", password_hash=hash_password(PASSWORD), role="admin")
        db.add(admin)
        db.commit()
        admin_id = admin.id
    headers = {"Authorization": f"Bearer {create_access_token(admin_id, 'admin')}"}

    key = http.post("/api/v1/developer/clients", headers=headers, json={"name": "Local sandbox"})
    assert key.status_code == 201, key.text
    assert key.json()["api_key"].startswith("fsx_test_")
    sandbox_headers = {"X-API-Key": key.json()["api_key"]}
    identity = http.get("/api/v1/developer/v1/me", headers=sandbox_headers)
    assert identity.status_code == 200
    assert identity.json()["permissions"] == ["accounts:read", "transactions:read"]
    assert http.get("/api/v1/developer/v1/accounts", headers=sandbox_headers).status_code == 200
    assert http.get("/api/v1/developer/v1/me", headers={"X-API-Key": "fsx_test_invalid"}).status_code == 401
    listed = http.get("/api/v1/developer/clients", headers=headers).json()[0]
    assert "api_key" not in listed and "secret_hash" not in listed
    assert http.post(f"/api/v1/developer/clients/{listed['id']}/revoke", headers=headers).json()["active"] is False
    assert http.get("/api/v1/developer/v1/me", headers=sandbox_headers).status_code == 401

    endpoint = http.post("/api/v1/developer/webhooks", headers=headers, json={"url": "https://hooks.example.test/events", "event_types": ["transaction.posted"]})
    assert endpoint.status_code == 201, endpoint.text
    delivery = http.post(f"/api/v1/developer/webhooks/{endpoint.json()['id']}/test-delivery", headers=headers)
    assert delivery.status_code == 201 and delivery.json()["status"] == "queued_demo"
    assert http.get("/api/v1/developer/webhooks/deliveries", headers=headers).json()[0]["status"] == "queued_demo"
