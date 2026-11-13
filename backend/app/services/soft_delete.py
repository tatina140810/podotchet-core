"""Global soft-delete filter.

One `do_orm_execute` listener on the Session class appends
`deleted_at IS NULL` to every ORM SELECT touching a SoftDeleteMixin model.
Reports, dashboards and list endpoints never need to remember the filter —
which is exactly the bug class this prevents.

Escape hatch: `.execution_options(include_deleted=True)` for the audit log
and recovery paths only.
"""
from datetime import datetime, timezone

from sqlalchemy import event
from sqlalchemy.orm import Session, with_loader_criteria

from app.models import SoftDeleteMixin, User


@event.listens_for(Session, "do_orm_execute")
def _hide_deleted(state) -> None:
    if not state.is_select or state.is_column_load or state.is_relationship_load:
        return
    if state.execution_options.get("include_deleted", False):
        return
    state.statement = state.statement.options(
        with_loader_criteria(
            SoftDeleteMixin,
            lambda cls: cls.deleted_at.is_(None),
            include_aliases=True,
            propagate_to_loaders=True,
        )
    )


def soft_delete(obj: SoftDeleteMixin, user: User) -> None:
    """Mark the row deleted. Does not commit: the caller owns the transaction."""
    obj.deleted_at = datetime.now(timezone.utc)
    obj.deleted_by = user.id
