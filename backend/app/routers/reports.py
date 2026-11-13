"""Reports and dashboard. Only approved expenses count as spent; pending is shown separately."""
import csv
import io
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.core.deps import current_user, require
from app.core.rbac import Perm, visible_user_ids
from app.db import get_db
from app.models import Category, Expense, Organization, User
from app.services import plans
from app.services.approval import Status

router = APIRouter(prefix="/api", tags=["reports"])


class Row(BaseModel):
    key: str
    total: Decimal
    count: int


class Dashboard(BaseModel):
    currency: str
    approved_this_month: Decimal
    pending_total: Decimal
    pending_count: int
    rejected_count: int
    by_category: list[Row]


class Report(BaseModel):
    currency: str
    date_from: date
    date_to: date
    total: Decimal
    by_category: list[Row]
    by_employee: list[Row]
    by_month: list[Row]


def _scoped(q: Select, db: Session, me: User) -> Select:
    q = q.where(Expense.org_id == me.org_id)
    allowed = visible_user_ids(db, me)
    return q if allowed is None else q.where(Expense.employee_id.in_(allowed))


def _grouped(db: Session, me: User, label, start: date, end: date) -> list[Row]:
    q = (
        select(label.label("key"), func.sum(Expense.amount), func.count(Expense.id))
        .select_from(Expense)
        .join(Category, Category.id == Expense.category_id)
        .join(User, User.id == Expense.employee_id)
        .where(Expense.status == Status.approved.value, Expense.spent_on.between(start, end))
        .group_by(label)
        .order_by(func.sum(Expense.amount).desc())
    )
    return [Row(key=str(k), total=t or 0, count=c) for k, t, c in db.execute(_scoped(q, db, me))]


def _month_label(db: Session):
    if db.get_bind().dialect.name == "sqlite":
        return func.strftime("%Y-%m", Expense.spent_on)
    return func.to_char(Expense.spent_on, "YYYY-MM")


@router.get("/dashboard", response_model=Dashboard)
def dashboard(me: User = Depends(current_user), db: Session = Depends(get_db)) -> Dashboard:
    org = db.get(Organization, me.org_id)
    today = date.today()
    month_start = today.replace(day=1)

    def agg(status_: Status, since: date | None = None):
        q = select(func.coalesce(func.sum(Expense.amount), 0), func.count(Expense.id)).where(
            Expense.status == status_.value
        )
        if since:
            q = q.where(Expense.spent_on >= since)
        return db.execute(_scoped(q, db, me)).one()

    approved, _ = agg(Status.approved, month_start)
    pending, pending_n = agg(Status.pending)
    _, rejected_n = agg(Status.rejected)
    return Dashboard(
        currency=org.currency,
        approved_this_month=approved,
        pending_total=pending,
        pending_count=pending_n,
        rejected_count=rejected_n,
        by_category=_grouped(db, me, Category.name, month_start, today)[:6],
    )


@router.get("/reports", response_model=Report)
def report(
    date_from: date = Query(alias="from"),
    date_to: date = Query(alias="to"),
    me: User = Depends(require(Perm.view_reports)),
    db: Session = Depends(get_db),
) -> Report:
    by_category = _grouped(db, me, Category.name, date_from, date_to)
    return Report(
        currency=db.get(Organization, me.org_id).currency,
        date_from=date_from,
        date_to=date_to,
        total=sum((r.total for r in by_category), Decimal(0)),
        by_category=by_category,
        by_employee=_grouped(db, me, User.full_name, date_from, date_to),
        by_month=sorted(_grouped(db, me, _month_label(db), date_from, date_to), key=lambda r: r.key),
    )


@router.get("/reports/expenses.csv")
def export_csv(
    date_from: date = Query(alias="from"),
    date_to: date = Query(alias="to"),
    me: User = Depends(require(Perm.view_reports)),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    plans.ensure_can_export(db.get(Organization, me.org_id))
    q = _scoped(select(Expense).where(Expense.spent_on.between(date_from, date_to)), db, me)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id", "date", "employee", "category", "amount", "currency", "status", "description"])
    for e in db.scalars(q.order_by(Expense.spent_on)).unique():
        w.writerow([e.id, e.spent_on, e.employee.full_name, e.category.name, e.amount, e.currency, e.status, e.description])
    headers = {"Content-Disposition": f'attachment; filename="expenses_{date_from}_{date_to}.csv"'}
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv", headers=headers)
