from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import current_user
from app.core.rbac import MATRIX, Role
from app.core.security import create_access_token, verify_password
from app.db import get_db
from app.models import Organization, User
from app.services.plans import limits

router = APIRouter(prefix="/api/auth", tags=["auth"])


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    permissions: list[str]
    org_id: int
    org_name: str
    org_currency: str
    plan: str
    plan_limits: dict


@router.post("/login", response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> TokenOut:
    user = db.scalar(select(User).where(func.lower(User.email) == form.username.strip().lower()))
    # Same message for unknown email and wrong password: no account enumeration.
    if not user or not user.is_active or not verify_password(form.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    return TokenOut(access_token=create_access_token(user.id, user.org_id))


@router.get("/me", response_model=MeOut)
def me(user: User = Depends(current_user), db: Session = Depends(get_db)) -> MeOut:
    org = db.get(Organization, user.org_id)
    return MeOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        permissions=sorted(p.value for p in MATRIX.get(Role(user.role), frozenset())),
        org_id=org.id,
        org_name=org.name,
        org_currency=org.currency,
        plan=org.plan,
        plan_limits=limits(org),
    )
