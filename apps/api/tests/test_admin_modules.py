from decimal import Decimal

from app.core.security import create_access_token, hash_password
from app.modules.identity.models import RolePermission, User
from app.modules.phase5_8.models import BusinessOrganization, MerchantDispute, MerchantSale


def test_admin_can_create_members_accounts_and_suspend_access(client):
    http, sessions = client
    with sessions() as db:
        admin = User(email="directory-admin@example.test", password_hash=hash_password("Long-Admin-Password-2026!"), role="admin")
        db.add(admin)
        db.add(RolePermission(role="admin", permission="roles:manage"))
        db.commit()
        admin_id = admin.id
    headers = {"Authorization": f"Bearer {create_access_token(admin_id, 'admin')}"}

    created = http.post("/api/v1/admin/members", headers=headers, json={
        "email": "new-member@example.com",
        "full_name": "New Member",
        "password": "Member-Temporary-Password-2026!",
        "role": "customer",
        "phone": "+923001234567",
        "country": "Pakistan",
        "currency": "PKR",
    })
    assert created.status_code == 201, created.text
    member = created.json()
    assert member["account_count"] == 1
    assert member["kyc_status"] == "pending"
    assert http.get("/api/v1/admin/members", headers=headers).json()[0]["email"] == "new-member@example.com"
    assert http.post("/api/v1/admin/members", headers=headers, json={
        "email": "new-member@example.com", "full_name": "Duplicate Member",
        "password": "Member-Temporary-Password-2026!", "role": "customer",
    }).status_code == 409

    suspended = http.patch(f"/api/v1/admin/members/{member['id']}/status", headers=headers, json={"is_active": False})
    assert suspended.status_code == 200
    assert suspended.json()["is_active"] is False
    restored = http.patch(f"/api/v1/admin/members/{member['id']}/status", headers=headers, json={"is_active": True})
    assert restored.status_code == 200


def test_dispute_review_stores_reasoned_decision(client):
    http, sessions = client
    with sessions() as db:
        admin = User(email="dispute-admin@example.test", password_hash=hash_password("Long-Admin-Password-2026!"), role="admin")
        merchant = User(email="dispute-merchant@example.test", password_hash=hash_password("Long-Merchant-Password-2026!"), role="merchant")
        db.add_all([admin, merchant])
        db.flush()
        organization = BusinessOrganization(user_id=merchant.id, legal_name="Merchant Co", status="active")
        db.add(organization)
        db.flush()
        sale = MerchantSale(organization_id=organization.id, reference="SALE-DISPUTE-1", description="Demo sale", amount=Decimal("1250"), currency="PKR")
        db.add(sale)
        db.flush()
        dispute = MerchantDispute(organization_id=organization.id, sale_id=sale.id, reason="Duplicate charge", evidence_reference="case-file-1")
        db.add(dispute)
        db.commit()
        admin_id = admin.id
        dispute_id = dispute.id
    headers = {"Authorization": f"Bearer {create_access_token(admin_id, 'admin')}"}

    queue = http.get("/api/v1/merchant/disputes", headers=headers)
    assert queue.status_code == 200
    assert queue.json()["items"][0]["sale_reference"] == "SALE-DISPUTE-1"
    assert http.patch(f"/api/v1/merchant/disputes/{dispute_id}", headers=headers, json={"decision":"resolved", "note":"no"}).status_code == 422
    decision = http.patch(f"/api/v1/merchant/disputes/{dispute_id}", headers=headers, json={"decision":"escalated", "note":"Merchant evidence needs secondary review"})
    assert decision.status_code == 200
    assert decision.json()["status"] == "escalated"
    assert http.get("/api/v1/merchant/disputes", headers=headers).json()["items"][0]["decision_note"] == "Merchant evidence needs secondary review"
