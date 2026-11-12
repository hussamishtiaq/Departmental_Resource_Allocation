from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.permissions import Permission, can_assign_role
from app.dependencies.auth import require_permission
from app.dependencies.database import get_db
from app.models.user import User
from app.repositories import user_repository as repo
from app.schemas.user import UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserRead])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(Permission.USERS_READ)),
):
    return repo.list_users(db)


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(Permission.USERS_READ)),
):
    user = repo.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return user


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(require_permission(Permission.USERS_MANAGE)),
):
    """Change a role or (de)activate an account, following the role hierarchy:
    you can only manage users below you and only hand out roles below yours
    (the HOD can assign any role)."""
    user = repo.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    changes = data.model_dump(exclude_unset=True)
    if user.id == current.id and changes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot change your own account")

    if "role" in changes:
        role = repo.get_role_by_name(db, changes["role"])
        if role is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown role")
        if not can_assign_role(current.role.name, user.role.name, role.name):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You cannot assign that role")
        user.role_id = role.id
        user.role = role
    if "is_active" in changes:
        if changes["is_active"] is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "is_active cannot be null")
        # deactivating needs authority over the target, same as changing its role
        if not can_assign_role(current.role.name, user.role.name, user.role.name):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You cannot manage this user")
        user.is_active = changes["is_active"]
    db.commit()
    db.refresh(user)
    return user
