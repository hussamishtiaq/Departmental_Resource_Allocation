from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.permissions import Permission
from app.dependencies.auth import require_permission
from app.dependencies.database import get_db
from app.models.user import User
from app.repositories import resource_repository as repo
from app.schemas.resource import (
    ResourceCreate,
    ResourceKind,
    ResourceRead,
    ResourceStatus,
    ResourceUpdate,
)
from app.services import resource_service as svc

router = APIRouter(prefix="/resources", tags=["resources"])

read_res = require_permission(Permission.RESOURCES_READ)
manage_res = require_permission(Permission.RESOURCES_MANAGE)


@router.get("", response_model=list[ResourceRead])
def list_resources(
    q: str | None = Query(None, description="Search name, code or serial number"),
    kind: ResourceKind | None = None,
    status_: ResourceStatus | None = Query(None, alias="status"),
    parent_id: int | None = Query(None, description="Only items inside this room/lab"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(read_res),
):
    return repo.search(
        db,
        q=q,
        kind=kind.value if kind else None,
        status=status_.value if status_ else None,
        parent_id=parent_id,
        skip=skip,
        limit=limit,
    )


@router.get("/{resource_id}", response_model=ResourceRead)
def get_resource(
    resource_id: int, db: Session = Depends(get_db), _: User = Depends(read_res)
):
    return svc.get_resource(db, resource_id)


@router.post("", response_model=ResourceRead, status_code=status.HTTP_201_CREATED)
def create_resource(
    data: ResourceCreate,
    db: Session = Depends(get_db),
    user: User = Depends(manage_res),
):
    return svc.create_resource(db, user, data)


@router.patch("/{resource_id}", response_model=ResourceRead)
def update_resource(
    resource_id: int,
    data: ResourceUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(manage_res),
):
    return svc.update_resource(db, user, resource_id, data)


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resource(
    resource_id: int, db: Session = Depends(get_db), user: User = Depends(manage_res)
):
    svc.delete_resource(db, user, resource_id)
