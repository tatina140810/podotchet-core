"""Expense approval state machine.

    pending ──approve──▶ approved   (terminal: locked for everyone but reviewers)
       │
       └────reject────▶ rejected ──resubmit (owner edits)──▶ pending

Transitions are data, not if-chains, so the whole lifecycle is reviewable in
one place and tests can enumerate it.
"""
from enum import Enum

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Expense, User
from app.services import audit


class Status(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class Action(str, Enum):
    approve = "approve"
    reject = "reject"
    resubmit = "resubmit"


TRANSITIONS: dict[tuple[Status, Action], Status] = {
    (Status.pending, Action.approve): Status.approved,
    (Status.pending, Action.reject): Status.rejected,
    (Status.rejected, Action.resubmit): Status.pending,
}

# Statuses in which the expense owner may still edit or delete their own record.
OWNER_EDITABLE = {Status.pending, Status.rejected}


def apply(db: Session, expense: Expense, action: Action, actor: User, comment: str | None = None) -> Expense:
    target = TRANSITIONS.get((Status(expense.status), action))
    if target is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Cannot {action.value} an expense that is {expense.status}",
        )
    if action is Action.reject and not (comment or "").strip():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "A reason is required to reject")
    if action in (Action.approve, Action.reject) and expense.employee_id == actor.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You cannot review your own expense")

    before = audit.snapshot(expense)
    expense.status = target.value
    if action is Action.resubmit:
        expense.reviewed_by = None
        expense.review_comment = None
    else:
        expense.reviewed_by = actor.id
        expense.review_comment = comment
    audit.log_update(db, expense, before, actor, action="status")
    return expense
