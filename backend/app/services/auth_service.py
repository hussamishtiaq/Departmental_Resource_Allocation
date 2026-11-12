from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.permissions import ROLE_DEFINITIONS, DEFAULT_REGISTRATION_ROLE
from app.core.security import create_access_token, hash_password, verify_password
from app.models.role import Role
from app.models.user import User
from app.repositories import user_repository as users

# Hash checked when the email is unknown, so login timing doesn't reveal accounts.
_DUMMY_HASH = hash_password("dummy-password")


def seed_roles(db: Session) -> None:
    existing = {r.name: r for r in db.query(Role).all()}
    for name, level, description in ROLE_DEFINITIONS:
        role = existing.get(name)
        if role is None:
            db.add(Role(name=str(name), level=level, description=description))
        else:
            role.level, role.description = level, description
    db.commit()


def register_user(db: Session, full_name: str, email: str, password: str) -> User:
    if users.get_by_email(db, email):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    role = users.get_role_by_name(db, DEFAULT_REGISTRATION_ROLE)
    if role is None:  # roles not seeded yet (e.g. fresh database)
        seed_roles(db)
        role = users.get_role_by_name(db, DEFAULT_REGISTRATION_ROLE)
    user = User(
        full_name=full_name.strip(),
        email=email.lower(),
        hashed_password=hash_password(password),
        role_id=role.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    user = users.get_by_email(db, email)
    ok = verify_password(password, user.hashed_password if user else _DUMMY_HASH)
    if user is None or not ok:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is disabled")
    return user


def issue_token(user: User) -> str:
    return create_access_token(user.id)
