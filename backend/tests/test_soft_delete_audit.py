from sqlalchemy import select

from app.models import Expense, RecordChangeLog
from tests.conftest import auth


def test_delete_is_soft_and_hidden_everywhere(client, w, db):
    e = w.expense(w.sam, amount="40.00")
    assert client.delete(f"/api/expenses/{e.id}", headers=auth(w.sam)).status_code == 204

    assert client.get("/api/expenses", headers=auth(w.admin)).json() == []
    assert client.get("/api/dashboard", headers=auth(w.admin)).json()["pending_count"] == 0
    db.expire_all()
    assert db.scalar(select(Expense).where(Expense.id == e.id)) is None
    row = db.scalar(select(Expense).where(Expense.id == e.id).execution_options(include_deleted=True))
    assert row is not None and row.deleted_by == w.sam.id


def test_delete_keeps_full_snapshot(client, w, db):
    e = w.expense(w.sam, amount="40.00")
    client.delete(f"/api/expenses/{e.id}", headers=auth(w.sam))
    log = db.scalar(select(RecordChangeLog).where(RecordChangeLog.action == "delete"))
    assert log.diff["amount"] == "40.00" and log.diff["employee_id"] == w.sam.id


def test_update_logs_only_changed_fields(client, w):
    e = w.expense(w.sam, amount="40.00")
    client.patch(f"/api/expenses/{e.id}", json={"amount": "45.50", "description": "Taxi"}, headers=auth(w.sam))
    client.post(f"/api/approvals/{e.id}", json={"action": "approve"}, headers=auth(w.admin))
    hist = client.get(f"/api/expenses/{e.id}/history", headers=auth(w.sam)).json()
    assert [h["action"] for h in hist] == ["update", "status"]
    assert hist[0]["diff"] == {"amount": {"old": "40.00", "new": "45.50"}}
    assert hist[1]["diff"]["status"] == {"old": "pending", "new": "approved"}


def test_noop_edit_writes_nothing(client, w):
    e = w.expense(w.sam)
    client.patch(f"/api/expenses/{e.id}", json={"description": "Taxi"}, headers=auth(w.sam))
    assert client.get(f"/api/expenses/{e.id}/history", headers=auth(w.sam)).json() == []
