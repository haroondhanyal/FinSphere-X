from decimal import Decimal

from app.core.security import create_access_token, hash_password
from app.modules.accounts.models import Account
from app.modules.identity.models import Customer, User


PASSWORD = "Workspace-Feature-Test-2026!"


def sign_in(client, email):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD, "full_name": "Workspace Tester"},
    )
    assert response.status_code == 201, response.text
    pair = client.post(
        "/api/v1/auth/login", json={"email": email, "password": PASSWORD}
    ).json()
    return {"Authorization": "Bearer " + pair["access_token"]}


def test_support_ticket_is_owned_and_staff_can_resolve(client):
    http, sessions = client
    owner = sign_in(http, "support-owner@example.test")
    other = sign_in(http, "support-other@example.test")
    created = http.post(
        "/api/v1/support/tickets",
        headers=owner,
        json={"subject": "Card payment question", "category": "cards", "body": "Please explain this card payment on my account."},
    )
    assert created.status_code == 201, created.text
    ticket_id = created.json()["id"]
    assert len(http.get("/api/v1/support/tickets", headers=owner).json()) == 1
    assert http.get("/api/v1/support/tickets", headers=other).json() == []
    with sessions() as db:
        operator = User(email="support-operator@example.test", password_hash=hash_password(PASSWORD), role="operations")
        db.add(operator)
        db.commit()
        operator_id = operator.id
    operator_headers = {"Authorization": "Bearer " + create_access_token(operator_id, "operations")}
    reviewed = http.patch(
        f"/api/v1/support/tickets/{ticket_id}",
        headers=operator_headers,
        json={"status": "resolved", "staff_response": "The card transaction is a seeded demo record."},
    )
    assert reviewed.status_code == 200 and reviewed.json()["status"] == "resolved"
    assert http.get("/api/v1/support/tickets", headers=owner).json()[0]["staff_response"]


def test_budget_goal_and_deposit_trackers_are_owned_and_do_not_move_money(client):
    http, sessions = client
    owner = sign_in(http, "planner@example.test")
    other = sign_in(http, "planner-other@example.test")
    with sessions() as db:
        user = db.query(User).filter_by(email="planner@example.test").one()
        customer = db.query(Customer).filter_by(user_id=user.id).one()
        account = db.query(Account).filter_by(customer_id=customer.id).first()
        assert account is not None
        account.balance = Decimal("20000.0000")
        account_id = account.id
        original_balance = account.balance
        db.commit()

    budget = http.post(
        "/api/v1/budgets",
        headers=owner,
        json={"month": "2026-10", "category": "payments", "limit_amount": "5000", "currency": "PKR"},
    )
    assert budget.status_code == 201, budget.text
    assert http.get("/api/v1/budgets", headers=other).json() == []

    goal = http.post(
        "/api/v1/goals",
        headers=owner,
        json={"name": "Emergency fund", "target_amount": "10000", "currency": "PKR"},
    )
    assert goal.status_code == 201, goal.text
    progress = http.post(
        f"/api/v1/goals/{goal.json()['id']}/contributions",
        headers=owner,
        json={"amount": "2500"},
    )
    assert progress.status_code == 200 and progress.json()["current_amount"] == "2500.0000"

    position = http.post(
        "/api/v1/deposits/positions",
        headers=owner,
        json={"source_account_id": account_id, "product_code": "term-3m", "amount": "5000"},
    )
    assert position.status_code == 201, position.text
    assert "maturity_date" in position.json()
    with sessions() as db:
        assert db.get(Account, account_id).balance == original_balance


def test_activity_feed_and_global_search_are_user_scoped(client):
    http, _sessions = client
    owner = sign_in(http, "search-owner@example.test")
    other = sign_in(http, "search-other@example.test")
    account = http.get("/api/v1/accounts", headers=owner).json()[0]
    search = http.get("/api/v1/search?q=" + account["account_number_masked"][-4:], headers=owner)
    assert search.status_code == 200
    assert any(row["type"] == "account" for row in search.json()["results"])
    own_activity = http.get("/api/v1/notifications", headers=owner)
    assert own_activity.status_code == 200 and own_activity.json()["read_tracking"] is False
    other_activity = http.get("/api/v1/notifications", headers=other).json()
    assert not any(row["id"] in {item["id"] for item in own_activity.json()["items"]} for row in other_activity["items"])
