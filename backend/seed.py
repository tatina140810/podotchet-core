"""Demo data: Acme Trading LLC (USD). Idempotent — safe to run on every start.

All people, companies and numbers here are fictional.
"""
import random
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select

import app.services.soft_delete  # noqa: F401
from app.core.security import hash_password
from app.db import SessionLocal
from app.models import Category, Expense, Organization, User

DEMO_PASSWORD = "demo1234"
CATEGORIES = ["Travel", "Meals", "Office supplies", "Fuel", "Software", "Client entertainment"]
PEOPLE = [
    # email, name, role, supervisor email
    ("owner@acme.test", "Olivia Carter", "owner", None),
    ("admin@acme.test", "Daniel Brooks", "admin", None),
    ("auditor@acme.test", "Grace Kim", "auditor", None),
    ("lead@acme.test", "Marcus Lee", "employee", None),
    ("sam@acme.test", "Sam Rivera", "employee", "lead@acme.test"),
    ("nina@acme.test", "Nina Patel", "employee", "lead@acme.test"),
]
NOTES = {
    "Travel": ["Flight to Chicago trade show", "Hotel, 2 nights", "Airport taxi"],
    "Meals": ["Team lunch", "Dinner with supplier", "Coffee for workshop"],
    "Office supplies": ["Printer paper and toner", "Whiteboard markers", "Desk organizer"],
    "Fuel": ["Fuel for delivery van", "Fuel, client visit"],
    "Software": ["Design tool subscription", "Cloud storage, annual"],
    "Client entertainment": ["Conference tickets for client", "Client dinner"],
}


def main() -> None:
    db = SessionLocal()
    if db.scalar(select(Organization).where(Organization.name == "Acme Trading LLC")):
        print("seed: demo data already present")
        return
    org = Organization(name="Acme Trading LLC", currency="USD", plan="pro")
    db.add(org)
    db.flush()
    cats = [Category(org_id=org.id, name=n) for n in CATEGORIES]
    db.add_all(cats)
    users: dict[str, User] = {}
    pw = hash_password(DEMO_PASSWORD)
    for email, name, role, sup in PEOPLE:
        u = User(org_id=org.id, email=email, full_name=name, role=role, password_hash=pw,
                 supervisor_id=users[sup].id if sup else None)
        db.add(u)
        db.flush()
        users[email] = u

    rng = random.Random(42)
    spenders = [users[e] for e in ("lead@acme.test", "sam@acme.test", "nina@acme.test")]
    reviewer = users["admin@acme.test"]
    today = date.today()
    for i in range(60):
        cat = rng.choice(cats)
        age = rng.randint(0, 120)
        status = "pending" if age < 7 else rng.choices(["approved", "rejected"], [9, 1])[0]
        db.add(Expense(
            org_id=org.id,
            employee_id=rng.choice(spenders).id,
            category_id=cat.id,
            amount=Decimal(rng.randint(1200, 48000)) / 100,
            currency="USD",
            spent_on=today - timedelta(days=age),
            description=rng.choice(NOTES[cat.name]),
            status=status,
            reviewed_by=None if status == "pending" else reviewer.id,
            review_comment="Receipt is missing, please attach it" if status == "rejected" else None,
        ))
    db.commit()
    print(f"seed: created Acme Trading LLC, {len(users)} users, 60 expenses (password: {DEMO_PASSWORD})")


if __name__ == "__main__":
    main()
