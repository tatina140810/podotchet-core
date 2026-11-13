from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.base import TimestampMixin


class Organization(Base, TimestampMixin):
    """Tenant. Every business row carries org_id and every query is scoped by it."""

    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    # free | pro | business — limits live in app.services.plans
    plan: Mapped[str] = mapped_column(String(16), nullable=False, default="free")
