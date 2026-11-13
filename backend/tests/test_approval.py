import pytest

from app.services.approval import TRANSITIONS, Action, Status
from tests.conftest import auth


def test_transition_table_is_closed():
    # approved is terminal: nothing leaves it.
    assert not [k for k in TRANSITIONS if k[0] is Status.approved]


def test_admin_approves_pending(client, w):
    e = w.expense(w.sam)
    r = client.post(f"/api/approvals/{e.id}", json={"action": "approve"}, headers=auth(w.admin))
    assert r.status_code == 200 and r.json()["status"] == "approved"


def test_reject_requires_reason(client, w):
    e = w.expense(w.sam)
    r = client.post(f"/api/approvals/{e.id}", json={"action": "reject"}, headers=auth(w.admin))
    assert r.status_code == 422


@pytest.mark.parametrize("start", ["approved", "rejected"])
def test_cannot_review_twice(client, w, start):
    e = w.expense(w.sam, status=start)
    r = client.post(f"/api/approvals/{e.id}", json={"action": "approve"}, headers=auth(w.admin))
    assert r.status_code == 409


def test_cannot_review_own_expense(client, w):
    e = w.expense(w.admin)
    r = client.post(f"/api/approvals/{e.id}", json={"action": "approve"}, headers=auth(w.admin))
    assert r.status_code == 403


def test_resubmit_is_not_a_reviewer_action(client, w):
    e = w.expense(w.sam, status="rejected")
    r = client.post(f"/api/approvals/{e.id}", json={"action": "resubmit"}, headers=auth(w.admin))
    assert r.status_code == 422


def test_editing_rejected_expense_sends_it_back(client, w):
    e = w.expense(w.sam, status="rejected")
    r = client.patch(f"/api/expenses/{e.id}", json={"amount": "30.00"}, headers=auth(w.sam))
    assert r.status_code == 200 and r.json()["status"] == "pending"


def test_owner_cannot_edit_approved(client, w):
    e = w.expense(w.sam, status="approved")
    r = client.patch(f"/api/expenses/{e.id}", json={"amount": "1.00"}, headers=auth(w.sam))
    assert r.status_code == 403
