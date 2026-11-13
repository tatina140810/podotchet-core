from tests.conftest import auth


def test_free_plan_blocks_export_with_402(client, w, db):
    w.acme.plan = "free"
    db.commit()
    r = client.get("/api/reports/expenses.csv?from=2026-01-01&to=2026-12-31", headers=auth(w.admin))
    assert r.status_code == 402 and r.json()["detail"]["code"] == "export_locked"


def test_pro_plan_exports_csv(client, w):
    w.expense(w.sam, status="approved")
    r = client.get("/api/reports/expenses.csv?from=2000-01-01&to=2100-01-01", headers=auth(w.admin))
    assert r.status_code == 200 and r.text.count("\n") == 2


def test_free_plan_user_limit(client, w, db):
    w.acme.plan = "free"  # 3 users max; World already has 6
    db.commit()
    body = {"email": "new@test.dev", "full_name": "New", "password": "password123"}
    r = client.post("/api/users", json=body, headers=auth(w.admin))
    assert r.status_code == 402 and r.json()["detail"]["code"] == "user_limit"


def test_report_counts_only_approved(client, w):
    w.expense(w.sam, status="approved", amount="10.00")
    w.expense(w.sam, status="pending", amount="99.00")
    r = client.get("/api/reports?from=2000-01-01&to=2100-01-01", headers=auth(w.auditor)).json()
    assert r["total"] == "10.00"
