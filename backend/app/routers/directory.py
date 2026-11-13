"""Organization directory: categories and users."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import current_user, get_in_org, require
from app.core.rbac import Perm, Role
from app.core.security import hash_password
from app.db import get_db
from app.models import Category, Organization, User
from app.services import plans

router = APIRouter(prefix="/api", tags=["directory"])


class CategoryOut(BaseModel):
    id: int
    name: str


class CategoryIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    supervisor_id: int | None
    is_active: bool


class UserIn(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=8, max_length=128)
    role: Role = Role.employee
    supervisor_id: int | None = None


@router.get("/categories", response_model=list[CategoryOut])
def categories(me: User = Depends(current_user), db: Session = Depends(get_db)) -> list[CategoryOut]:
    rows = db.scalars(select(Category).where(Category.org_id == me.org_id).order_by(Category.name))
    return [CategoryOut(id=c.id, name=c.name) for c in rows]


@router.post("/categories", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def add_category(
    body: CategoryIn, me: User = Depends(require(Perm.manage_categories)), db: Session = Depends(get_db)
) -> CategoryOut:
    c = Category(org_id=me.org_id, name=body.name.strip())
    db.add(c)
    db.commit()
    return CategoryOut(id=c.id, name=c.name)


@router.get("/users", response_model=list[UserOut])
def users(me: User = Depends(require(Perm.view_all)), db: Session = Depends(get_db)) -> list[UserOut]:
    rows = db.scalars(select(User).where(User.org_id == me.org_id).order_by(User.full_name))
    return [UserOut.model_validate(u, from_attributes=True) for u in rows]


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def add_user(body: UserIn, me: User = Depends(require(Perm.manage_users)), db: Session = Depends(get_db)) -> UserOut:
    if body.role is Role.owner:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Owners cannot be created via the API")
    plans.ensure_can_add_user(db, db.get(Organization, me.org_id))
    if body.supervisor_id is not None:
        get_in_org(db, User, body.supervisor_id, me)
    if db.scalar(select(User.id).where(func.lower(User.email) == body.email.lower())):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    u = User(
        org_id=me.org_id,
        email=body.email.lower(),
        full_name=body.full_name,
        password_hash=hash_password(body.password),
        role=body.role.value,
        supervisor_id=body.supervisor_id,
    )
    db.add(u)
    db.commit()
    return UserOut.model_validate(u, from_attributes=True)
