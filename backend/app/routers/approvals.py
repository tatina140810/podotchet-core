from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_in_org, require
from app.core.rbac import Perm
from app.db import get_db
from app.models import Expense, User
from app.routers.expenses import ExpenseOut
from app.services.approval import Action, Status, apply

router = APIRouter(prefix="/api/approvals", tags=["approvals"])


class ReviewIn(BaseModel):
    action: Literal["approve", "reject"]
    comment: str | None = Field(default=None, max_length=1000)


@router.get("", response_model=list[ExpenseOut])
def queue(me: User = Depends(require(Perm.review_expense)), db: Session = Depends(get_db)) -> list[ExpenseOut]:
    q = (
        select(Expense)
        .where(Expense.org_id == me.org_id, Expense.status == Status.pending.value)
        .order_by(Expense.created_at)
    )
    return [ExpenseOut.of(e) for e in db.scalars(q).unique()]


@router.post("/{expense_id}", response_model=ExpenseOut)
def review(
    expense_id: int,
    body: ReviewIn,
    me: User = Depends(require(Perm.review_expense)),
    db: Session = Depends(get_db),
) -> ExpenseOut:
    e = get_in_org(db, Expense, expense_id, me)
    apply(db, e, Action(body.action), me, body.comment)
    db.commit()
    return ExpenseOut.of(e)
