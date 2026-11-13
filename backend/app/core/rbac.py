"""Role-based access control.

Roles are plain strings in the DB (no native enum), so adding a role needs no
migration. What each role may do is declared once, here, as a permission matrix;
routers ask `can(user, Perm.X)` instead of comparing role names inline.
"""
from enum import Enum

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User


class Role(str, Enum):
    owner = "owner"        # business owner: everything, including billing plan
    admin = "admin"        # runs the books: approves, manages people
    auditor = "auditor"    # read-only access to all data in the organization
    employee = "employee"  # spends money and reports it


class Perm(str, Enum):
    submit_expense = "submit_expense"
    review_expense = "review_expense"
    view_all = "view_all"
    view_reports = "view_reports"
    manage_users = "manage_users"
    manage_categories = "manage_categories"
    change_plan = "change_plan"


MATRIX: dict[Role, frozenset[Perm]] = {
    Role.owner: frozenset(Perm),
    Role.admin: frozenset(Perm) - {Perm.change_plan},
    Role.auditor: frozenset({Perm.view_all, Perm.view_reports}),
    Role.employee: frozenset({Perm.submit_expense}),
}


def can(user: User, perm: Perm) -> bool:
    try:
        return perm in MATRIX[Role(user.role)]
    except ValueError:  # unknown role string -> no permissions
        return False


def visible_user_ids(db: Session, me: User) -> list[int] | None:
    """Whose financial records `me` may see.

    None means "everyone in my organization" (caller adds no extra filter).
    Employees see themselves plus their reporting tree, walked breadth-first
    over supervisor_id so the depth of the hierarchy does not matter.
    """
    if can(me, Perm.view_all):
        return None
    seen: set[int] = {me.id}
    frontier = [me.id]
    while frontier:
        rows = db.scalars(
            select(User.id).where(User.org_id == me.org_id, User.supervisor_id.in_(frontier))
        ).all()
        frontier = [uid for uid in rows if uid not in seen]
        seen.update(frontier)
    return sorted(seen)
