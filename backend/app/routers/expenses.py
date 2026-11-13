"""Expenses: submit, list, edit, soft-delete, history."""
from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import current_user, get_in_org, require
from app.core.rbac import Perm, can, visible_user_ids
from app.db import get_db
from app.models import Category, Expense, Organization, RecordChangeLog, User
from app.services import audit, plans
from app.services.approval import OWNER_EDITABLE, Action, Status, apply
from app.services.soft_delete import soft_delete

router = APIRouter(prefix="/api/expenses", tags=["expenses"])


class ExpenseIn(BaseModel):
    category_id: int
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    spent_on: date
    description: str = Field(default="", max_length=2000)


class ExpensePatch(BaseModel):
    category_id: int | None = None
    amount: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    spent_on: date | None = None
    description: str | None = Field(default=None, max_length=2000)


class ExpenseOut(BaseModel):
    id: int
    employee_id: int
    employee_name: str
    category_id: int
    category_name: str
    amount: Decimal
    currency: str
    spent_on: date
    description: str
    status: str
    review_comment: str | None
    created_at: datetime

    @classmethod
    def of(cls, e: Expense) -> "ExpenseOut":
        return cls(
            id=e.id, employee_id=e.employee_id, employee_name=e.employee.full_name,
            category_id=e.category_id, category_name=e.category.name, amount=e.amount,
            currency=e.currency, spent_on=e.spent_on, description=e.description,
            status=e.status, review_comment=e.review_comment, created_at=e.created_at,
        )


class ChangeOut(BaseModel):
    action: str
    changed_by: str
    changed_at: datetime
    diff: dict


def _visible_expense(db: Session, expense_id: int, me: User) -> Expense:
    e = get_in_org(db, Expense, expense_id, me)
    allowed = visible_user_ids(db, me)
    if allowed is not None and e.employee_id not in allowed:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    return e


def _check_category(db: Session, category_id: int, me: User) -> None:
    get_in_org(db, Category, category_id, me)


@router.get("", response_model=list[ExpenseOut])
def list_expenses(
    mine: bool = False,
    status_: Status | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, le=500),
    offset: int = 0,
    me: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> list[ExpenseOut]:
    q = select(Expense).where(Expense.org_id == me.org_id)
    if mine:
        q = q.where(Expense.employee_id == me.id)
    else:
        allowed = visible_user_ids(db, me)
        if allowed is not None:
            q = q.where(Expense.employee_id.in_(allowed))
    if status_:
        q = q.where(Expense.status == status_.value)
    q = q.order_by(Expense.spent_on.desc(), Expense.id.desc()).limit(limit).offset(offset)
    return [ExpenseOut.of(e) for e in db.scalars(q).unique()]


@router.post("", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
def create_expense(
    body: ExpenseIn, me: User = Depends(require(Perm.submit_expense)), db: Session = Depends(get_db)
) -> ExpenseOut:
    org = db.get(Organization, me.org_id)
    plans.ensure_can_add_expense(db, org)
    _check_category(db, body.category_id, me)
    e = Expense(org_id=me.org_id, employee_id=me.id, currency=org.currency, **body.model_dump())
    db.add(e)
    db.commit()
    db.refresh(e)
    return ExpenseOut.of(e)


@router.patch("/{expense_id}", response_model=ExpenseOut)
def update_expense(
    expense_id: int, body: ExpensePatch, me: User = Depends(current_user), db: Session = Depends(get_db)
) -> ExpenseOut:
    e = _visible_expense(db, expense_id, me)
    is_owner = e.employee_id == me.id
    if not (is_owner and Status(e.status) in OWNER_EDITABLE) and not can(me, Perm.review_expense):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only your own pending or rejected expenses can be edited")
    changes = body.model_dump(exclude_unset=True)
    if "category_id" in changes:
        _check_category(db, changes["category_id"], me)
    before = audit.snapshot(e)
    for k, v in changes.items():
        setattr(e, k, v)
    audit.log_update(db, e, before, me)
    # Editing a rejected expense sends it back for review.
    if is_owner and e.status == Status.rejected.value:
        apply(db, e, Action.resubmit, me)
    db.commit()
    return ExpenseOut.of(e)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int, me: User = Depends(current_user), db: Session = Depends(get_db)) -> None:
    e = _visible_expense(db, expense_id, me)
    is_owner = e.employee_id == me.id
    if not (is_owner and Status(e.status) in OWNER_EDITABLE) and not can(me, Perm.review_expense):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only your own pending or rejected expenses can be deleted")
    audit.log_delete(db, e, me)
    soft_delete(e, me)
    db.commit()


@router.get("/{expense_id}/history", response_model=list[ChangeOut])
def expense_history(expense_id: int, me: User = Depends(current_user), db: Session = Depends(get_db)) -> list[ChangeOut]:
    _visible_expense(db, expense_id, me)
    rows = db.execute(
        select(RecordChangeLog, User.full_name)
        .join(User, User.id == RecordChangeLog.changed_by)
        .where(
            RecordChangeLog.org_id == me.org_id,
            RecordChangeLog.entity_type == Expense.__tablename__,
            RecordChangeLog.entity_id == expense_id,
        )
        .order_by(RecordChangeLog.changed_at)
    ).all()
    return [ChangeOut(action=r.action, changed_by=name, changed_at=r.changed_at, diff=r.diff) for r, name in rows]
