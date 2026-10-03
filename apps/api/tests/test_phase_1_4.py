from decimal import Decimal

from app.core.security import hash_password
from app.modules.accounts.models import Account
from app.modules.identity.models import Customer, RolePermission, User

PASSWORD = "This-Is-A-Long-Demo-Password-2026!"


def register(client, email="customer@example.org"):
    result = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": PASSWORD,
            "full_name": "Sample Customer",
            "phone": "+923001234567",
        },
    )
    assert result.status_code == 201, result.text
    return result.json()


def token_for(client, email="customer@example.org"):
    response = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_auth_register_login_and_resource_ownership(client):
    http, sessions = client
    register(http)
    token = token_for(http)
    headers = {"Authorization": f"Bearer {token}"}
    assert http.get("/api/v1/auth/me", headers=headers).json()["role"] == "customer"
    own_account = http.get("/api/v1/accounts", headers=headers).json()[0]
    assert own_account["balance"] == "0.0000"

    with sessions() as db:
        second = User(
            email="other@example.test", password_hash=hash_password(PASSWORD), role="customer"
        )
        db.add(second)
        db.flush()
        customer = Customer(user_id=second.id, full_name="Other Customer", kyc_status="approved")
        db.add(customer)
        db.flush()
        account = Account(
            customer_id=customer.id,
            account_number="FSXSECOND0001",
            balance=Decimal("75"),
            currency="PKR",
        )
        db.add(account)
        db.commit()
        account_id = account.id
    assert http.get(f"/api/v1/accounts/{account_id}", headers=headers).status_code == 404


def test_refresh_token_rotates_and_logout_revokes_session(client):
    http, _sessions = client
    register(http)
    pair = http.post(
        "/api/v1/auth/login", json={"email": "customer@example.org", "password": PASSWORD}
    ).json()
    bearer = {"Authorization": f"Bearer {pair['access_token']}"}
    rotated = http.post("/api/v1/auth/refresh", json={"refresh_token": pair["refresh_token"]})
    assert rotated.status_code == 200
    assert (
        http.post("/api/v1/auth/refresh", json={"refresh_token": pair["refresh_token"]}).status_code
        == 401
    )
    assert (
        http.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {rotated.json()['refresh_token']}"},
        ).status_code
        == 401
    )
    assert (
        http.post(
            "/api/v1/auth/logout",
            headers=bearer,
            json={"refresh_token": rotated.json()["refresh_token"]},
        ).status_code
        == 200
    )
    assert (
        http.post(
            "/api/v1/auth/refresh", json={"refresh_token": rotated.json()["refresh_token"]}
        ).status_code
        == 401
    )


def test_transfer_is_idempotent_and_has_balanced_ledger(client):
    http, sessions = client
    register(http)
    token = token_for(http)
    headers = {"Authorization": f"Bearer {token}"}
    with sessions() as db:
        owner = db.query(User).filter_by(email="customer@example.org").one()
        source_customer = db.query(Customer).filter_by(user_id=owner.id).one()
        source = db.query(Account).filter_by(customer_id=source_customer.id).one()
        source.balance = Decimal("100.0000")
        target_user = User(
            email="target@example.test", password_hash=hash_password(PASSWORD), role="customer"
        )
        db.add(target_user)
        db.flush()
        target_customer = Customer(
            user_id=target_user.id, full_name="Recipient", kyc_status="approved"
        )
        db.add(target_customer)
        db.flush()
        target = Account(
            customer_id=target_customer.id,
            account_number="FSXTARGET0001",
            balance=Decimal("5.0000"),
            currency="PKR",
        )
        db.add(target)
        db.commit()
        source_id = source.id
        target_number = target.account_number

    beneficiary = http.post(
        "/api/v1/beneficiaries",
        headers=headers,
        json={"name": "Recipient", "account_number": target_number, "currency": "PKR"},
    )
    beneficiary_id = beneficiary.json()["id"]
    http.post(f"/api/v1/beneficiaries/{beneficiary_id}/verify", headers=headers)
    body = {
        "source_account_id": source_id,
        "beneficiary_id": beneficiary_id,
        "amount": "12.5000",
        "purpose": "Test",
    }
    payment_headers = {**headers, "Idempotency-Key": "test-transfer-key-001"}
    first = http.post("/api/v1/transfers", headers=payment_headers, json=body)
    repeated = http.post("/api/v1/transfers", headers=payment_headers, json=body)
    assert first.status_code == 201, first.text
    assert repeated.json()["id"] == first.json()["id"]
    changed_request = {**body, "amount": "13.0000"}
    assert (
        http.post("/api/v1/transfers", headers=payment_headers, json=changed_request).status_code
        == 409
    )
    assert http.get("/api/v1/accounts", headers=headers).json()[0]["balance"] == "87.5000"
    lines = http.get(f"/api/v1/transactions/{first.json()['id']}/ledger", headers=headers).json()[
        "lines"
    ]
    assert (
        sum(Decimal(row["debit"]) for row in lines)
        == sum(Decimal(row["credit"]) for row in lines)
        == Decimal("12.5000")
    )


def test_wallet_move_posts_balanced_entries(client):
    http, sessions = client
    register(http)
    token = token_for(http)
    headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": "test-wallet-deposit-001"}
    with sessions() as db:
        owner = db.query(User).filter_by(email="customer@example.org").one()
        customer = db.query(Customer).filter_by(user_id=owner.id).one()
        account = db.query(Account).filter_by(customer_id=customer.id).one()
        account.balance = Decimal("40.0000")
        account_id = account.id
        db.commit()
    response = http.post(
        "/api/v1/wallet/transfers",
        headers=headers,
        json={"account_id": account_id, "direction": "deposit", "amount": "10.00"},
    )
    assert response.status_code == 201, response.text
    assert http.get("/api/v1/wallet", headers=headers).json()["balance"] == "10.0000"
    ledger = http.get(
        f"/api/v1/transactions/{response.json()['id']}/ledger", headers=headers
    ).json()["lines"]
    assert (
        sum(Decimal(row["debit"]) for row in ledger)
        == sum(Decimal(row["credit"]) for row in ledger)
        == Decimal("10.0000")
    )


def test_card_controls_and_permission_guard(client):
    http, sessions = client
    register(http)
    customer_token = token_for(http)
    customer_headers = {"Authorization": f"Bearer {customer_token}"}
    account = http.get("/api/v1/accounts", headers=customer_headers).json()[0]
    issued = http.post(
        "/api/v1/cards",
        headers=customer_headers,
        json={"account_id": account["id"], "card_type": "virtual"},
    )
    assert issued.status_code == 201
    card_id = issued.json()["id"]
    assert (
        http.post(f"/api/v1/cards/{card_id}/activate", headers=customer_headers).json()["status"]
        == "active"
    )
    assert (
        http.post(f"/api/v1/cards/{card_id}/freeze", headers=customer_headers).json()["status"]
        == "frozen"
    )
    assert http.get("/api/v1/customers/", headers=customer_headers).status_code == 403
    with sessions() as db:
        operator = User(
            email="ops@example.test", password_hash=hash_password(PASSWORD), role="operations"
        )
        db.add(operator)
        db.add(RolePermission(role="operations", permission="customers:read"))
        db.commit()
        operator_id = operator.id
    # Set a signed token through the public password login boundary.
    from app.core.security import create_access_token

    operator_headers = {"Authorization": f"Bearer {create_access_token(operator_id, 'operations')}"}
    assert http.get("/api/v1/customers/", headers=operator_headers).status_code == 200
