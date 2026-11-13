from typing import Callable, TypeVar

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.rbac import Perm, can
from app.core.security import decode_token
from app.db import Base, get_db
from app.models import User

_bearer = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)
M = TypeVar("M", bound=Base)


def current_user(token: str | None = Depends(_bearer), db: Session = Depends(get_db)) -> User:
    payload = decode_token(token) if token else None
    if not payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    user = db.get(User, int(payload.get("sub", 0)))
    if not user or not user.is_active or user.org_id != payload.get("org_id"):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    return user


def require(perm: Perm) -> Callable[[User], User]:
    def _dep(user: User = Depends(current_user)) -> User:
        if not can(user, perm):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not allowed for your role")
        return user

    return _dep


def get_in_org(db: Session, model: type[M], obj_id: int, me: User) -> M:
    """Load a row by id *within the caller's tenant*.

    A row from another organization answers 404, not 403, so ids cannot be used
    to probe which records exist elsewhere (IDOR protection).
    """
    obj = db.get(model, obj_id)
    if obj is None or getattr(obj, "org_id", None) != me.org_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    return obj
