"""Tests build the schema through Alembic (not create_all), so migrations are tested too.

DATABASE_URL defaults to a throwaway SQLite file; point it at Postgres to run
the same suite against the production engine.
"""
import os
import tempfile

_tmp = tempfile.mkdtemp()
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_tmp}/test.db")
os.environ.setdefault("JWT_SECRET", "test-secret")

from datetime import date  # noqa: E402
from decimal import Decimal  # noqa: E402

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.security import create_access_token, hash_password  # noqa: E402
from app.db import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Category, Expense, Organization, User  # noqa: E402

_INI = os.path.join(os.path.dirname(__file__), "..", "alembic.ini")


@pytest.fixture(scope="session", autouse=True)
def _schema():
    cfg = Config(_INI)
    cfg.set_main_option("script_location", os.path.join(os.path.dirname(_INI), "alembic"))
    command.upgrade(cfg, "head")
    yield


@pytest.fixture(autouse=True)
def _clean():
    yield
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


@pytest.fixture
def db():
    s = SessionLocal()
    yield s
    s.close()


@pytest.fixture
def client():
    return TestClient(app)


class World:
    """Two tenants. Acme: owner, admin, auditor, lead -> sam, and an outsider employee."""

    def __init__(self, db):
        self.db = db
        self.acme = self._org("Acme Trading LLC", "pro")
        self.other = self._org("Globex Inc", "pro")
        self.cat = self._cat(self.acme)
        self.other_cat = self._cat(self.other)
        self.owner = self._user(self.acme, "owner")
        self.admin = self._user(self.acme, "admin")
        self.auditor = self._user(self.acme, "auditor")
        self.lead = self._user(self.acme, "employee")
        self.sam = self._user(self.acme, "employee", supervisor=self.lead)
        self.outsider = self._user(self.acme, "employee")
        self.stranger = self._user(self.other, "admin")
        db.commit()

    def _org(self, name, plan):
        o = Organization(name=name, currency="USD", plan=plan)
        self.db.add(o)
        self.db.flush()
        return o

    def _cat(self, org):
        c = Category(org_id=org.id, name="Travel")
        self.db.add(c)
        self.db.flush()
        return c

    def _user(self, org, role, supervisor=None):
        n = self.db.query(User).count()
        u = User(org_id=org.id, email=f"u{n}@test.dev", full_name=f"User {n}", role=role,
                 password_hash=hash_password("password123"),
                 supervisor_id=supervisor.id if supervisor else None)
        self.db.add(u)
        self.db.flush()
        return u

    def expense(self, owner, status="pending", amount="25.00"):
        e = Expense(org_id=owner.org_id, employee_id=owner.id,
                    category_id=self.cat.id if owner.org_id == self.acme.id else self.other_cat.id,
                    amount=Decimal(amount), currency="USD", spent_on=date.today(),
                    description="Taxi", status=status)
        self.db.add(e)
        self.db.commit()
        return e


@pytest.fixture
def w(db):
    return World(db)


def auth(user) -> dict:
    return {"Authorization": f"Bearer {create_access_token(user.id, user.org_id)}"}
