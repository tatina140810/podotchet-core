"""Writes app.models.RecordChangeLog entries for financial records."""
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Session

from app.models import RecordChangeLog, User

_IGNORED = {"updated_at"}


def _json_safe(v: Any) -> Any:
    if isinstance(v, Decimal):
        return str(v)  # keep money exact
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    return v


def snapshot(obj) -> dict:
    mapper = sa_inspect(obj).mapper
    return {a.key: _json_safe(getattr(obj, a.key)) for a in mapper.column_attrs if a.key not in _IGNORED}


def diff(before: dict, after: dict) -> dict:
    return {
        k: {"old": before.get(k), "new": after.get(k)}
        for k in before.keys() | after.keys()
        if before.get(k) != after.get(k)
    }


def _write(db: Session, obj, action: str, payload: dict, user: User) -> None:
    db.add(RecordChangeLog(
        org_id=obj.org_id,
        entity_type=obj.__tablename__,
        entity_id=obj.id,
        action=action,
        changed_by=user.id,
        diff=payload,
    ))


def log_update(db: Session, obj, before: dict, user: User, action: str = "update") -> None:
    """`before` is snapshot(obj) taken prior to mutation. No-op edits are not logged."""
    changes = diff(before, snapshot(obj))
    if changes:
        _write(db, obj, action, changes, user)


def log_delete(db: Session, obj, user: User) -> None:
    _write(db, obj, "delete", snapshot(obj), user)
