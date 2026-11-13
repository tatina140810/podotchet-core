from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.base import utcnow


class RecordChangeLog(Base):
    """Append-only audit trail for financial records.

    update -> diff of changed fields only: {"amount": {"old": "30.00", "new": "45.00"}}
    status -> same diff shape, written by the approval state machine
    delete -> full snapshot of the row at the moment it was soft-deleted
    """

    __tablename__ = "record_change_log"
    __table_args__ = (Index("ix_change_log_entity", "org_id", "entity_type", "entity_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(String(16), nullable=False)
    changed_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    diff: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
