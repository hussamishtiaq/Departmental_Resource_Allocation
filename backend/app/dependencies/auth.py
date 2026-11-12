from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.permissions import Permission, RoleName, has_permission
from app.core.security import decode_access_token
from app.dependencies.database import get_db
from app.models.user import User
from app.repositories import user_repository as users

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    credentials_error = HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    subject = decode_access_token(token)
    if subject is None or not subject.isdigit():
        raise credentials_error
    user = users.get_by_id(db, int(subject))
    if user is None or not user.is_active:
        raise credentials_error
    return user


def require_permission(permission: Permission):
    def checker(user: User = Depends(get_current_user)) -> User:
        if not has_permission(user.role.name, permission):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not enough permissions")
        return user

    return checker


def require_roles(*roles: RoleName):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role.name not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not enough permissions")
        return user

    return checker
