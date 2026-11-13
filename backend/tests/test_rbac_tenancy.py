from tests.conftest import auth


def ids(resp):
    return {e["employee_id"] for e in resp.json()}


def test_employee_sees_self_and_reporting_tree(client, w):
    for u in (w.lead, w.sam, w.outsider):
        w.expense(u)
    assert ids(client.get("/api/expenses", headers=auth(w.lead))) == {w.lead.id, w.sam.id}
    assert ids(client.get("/api/expenses", headers=auth(w.sam))) == {w.sam.id}


def test_auditor_reads_everything_but_cannot_approve(client, w):
    e = w.expense(w.sam)
    w.expense(w.outsider)
    assert len(client.get("/api/expenses", headers=auth(w.auditor)).json()) == 2
    r = client.post(f"/api/approvals/{e.id}", json={"action": "approve"}, headers=auth(w.auditor))
    assert r.status_code == 403


def test_employee_cannot_open_approval_queue(client, w):
    assert client.get("/api/approvals", headers=auth(w.sam)).status_code == 403


def test_other_tenant_gets_404_not_403(client, w):
    e = w.expense(w.sam)
    h = auth(w.stranger)
    assert client.get(f"/api/expenses/{e.id}/history", headers=h).status_code == 404
    assert client.post(f"/api/approvals/{e.id}", json={"action": "approve"}, headers=h).status_code == 404
    assert client.delete(f"/api/expenses/{e.id}", headers=h).status_code == 404
    assert client.get("/api/expenses", headers=h).json() == []


def test_cannot_file_expense_into_foreign_category(client, w):
    body = {"category_id": w.other_cat.id, "amount": "10.00", "spent_on": "2026-01-05"}
    assert client.post("/api/expenses", json=body, headers=auth(w.sam)).status_code == 404


def test_peer_cannot_see_outside_tree(client, w):
    e = w.expense(w.outsider)
    assert client.delete(f"/api/expenses/{e.id}", headers=auth(w.sam)).status_code == 404


def test_admin_cannot_create_owner(client, w):
    body = {"email": "x@test.dev", "full_name": "X", "password": "password123", "role": "owner"}
    assert client.post("/api/users", json=body, headers=auth(w.admin)).status_code == 403


def test_cannot_attach_user_to_foreign_supervisor(client, w):
    body = {"email": "new@example.com", "full_name": "New", "password": "password123",
            "supervisor_id": w.stranger.id}
    assert client.post("/api/users", json=body, headers=auth(w.admin)).status_code == 404


def test_mass_assignment_is_ignored(client, w):
    body = {"category_id": w.cat.id, "amount": "5.00", "spent_on": "2026-01-05",
            "status": "approved", "employee_id": w.admin.id, "org_id": w.other.id}
    r = client.post("/api/expenses", json=body, headers=auth(w.sam)).json()
    assert r["status"] == "pending" and r["employee_id"] == w.sam.id
