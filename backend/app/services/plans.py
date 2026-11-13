"""Freemium plans. Exceeding a limit answers HTTP 402 with a machine-readable code
so the frontend can show an upgrade prompt instead of a generic error."""
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Expense, Organization, User

PLANS: dict[str, dict] = {
    "free": {"max_users": 3, "max_expenses_per_month": 50, "can_export": False},
    "pro": {"max_users": 25, "max_expenses_per_month": None, "can_export": True},
    "business": {"max_users": None, "max_expenses_per_month": None, "can_export": True},
}


def limits(org: Organization) -> dict:
    return PLANS.get(org.plan, PLANS["free"])


def _deny(code: str, message: str) -> HTTPException:
    return HTTPException(status.HTTP_402_PAYMENT_REQUIRED, {"code": code, "message": message})


def ensure_can_add_user(db: Session, org: Organization) -> None:
    cap = limits(org)["max_users"]
    if cap is None:
        return
    count = db.scalar(select(func.count(User.id)).where(User.org_id == org.id, User.is_active.is_(True)))
    if count >= cap:
        raise _deny("user_limit", f"The {org.plan} plan allows up to {cap} active users")


def ensure_can_add_expense(db: Session, org: Organization, today: date | None = None) -> None:
    cap = limits(org)["max_expenses_per_month"]
    if cap is None:
        return
    today = today or date.today()
    month_start = today.replace(day=1)
    count = db.scalar(
        select(func.count(Expense.id)).where(Expense.org_id == org.id, Expense.created_at >= month_start)
    )
    if count >= cap:
        raise _deny("expense_limit", f"The {org.plan} plan allows {cap} expenses per month")


def ensure_can_export(org: Organization) -> None:
    if not limits(org)["can_export"]:
        raise _deny("export_locked", "CSV export is available on Pro and Business plans")
