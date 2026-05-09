from typing import Callable

from fastapi import Depends, HTTPException, Request
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ROLES = {"student", "faculty", "admin", "technician"}


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def current_user(request: Request) -> dict:
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def require_role(*allowed_roles: str) -> Callable:
    allowed = set(allowed_roles)

    def dependency(user: dict = Depends(current_user)) -> dict:
        if user["role"] not in allowed:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user

    return dependency
