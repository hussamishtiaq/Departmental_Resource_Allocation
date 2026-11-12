from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.permissions import RoleName
from app.models.resource import Resource
from app.models.user import User
from app.repositories import resource_repository as repo
from app.schemas.resource import ResourceCreate, ResourceKind, ResourceUpdate

PLACEABLE_CONTAINERS = {ResourceKind.ROOM.value, ResourceKind.LABORATORY.value}


def get_resource(db: Session, resource_id: int) -> Resource:
    resource = repo.get(db, resource_id)
    if resource is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Resource not found")
    return resource


def ensure_can_manage_kind(user: User, kind: str) -> None:
    """HOD and department admin manage everything; lab staff only equipment."""
    if user.role.name == RoleName.LAB_STAFF and kind != ResourceKind.EQUIPMENT.value:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Laboratory staff can only manage equipment"
        )


def _validate_parent(db: Session, kind: str, parent_id: int | None, self_id: int | None = None) -> None:
    """Hierarchy rules: rooms/labs are top level; equipment may sit inside a room/lab."""
    if parent_id is None:
        return
    if kind != ResourceKind.EQUIPMENT.value:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Rooms and laboratories sit directly under the department"
        )
    parent = db.get(Resource, parent_id)
    if parent is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Parent room/laboratory not found")
    if parent.kind not in PLACEABLE_CONTAINERS:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Equipment can only be placed in a room or laboratory"
        )


def _validate_fields(kind: str, capacity: int | None, serial: str | None) -> None:
    if kind == ResourceKind.EQUIPMENT.value and capacity is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Capacity applies to rooms and laboratories only")
    if kind != ResourceKind.EQUIPMENT.value and serial:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Serial number applies to equipment only")


def create_resource(db: Session, user: User, data: ResourceCreate) -> Resource:
    kind = data.kind.value
    ensure_can_manage_kind(user, kind)
    code = data.code.strip().upper()
    if repo.code_exists(db, code):
        raise HTTPException(status.HTTP_409_CONFLICT, f"Resource code '{code}' already exists")
    _validate_parent(db, kind, data.parent_id)
    _validate_fields(kind, data.capacity, data.serial_number)

    fields = data.model_dump(exclude={"kind", "code", "status"})
    resource = Resource(
        **fields, kind=kind, code=code, status=data.status.value, created_by_id=user.id
    )
    db.add(resource)
    db.commit()
    db.expire_all()  # sessions don't expire on commit; reload parent/children
    return get_resource(db, resource.id)


def update_resource(db: Session, user: User, resource_id: int, data: ResourceUpdate) -> Resource:
    resource = get_resource(db, resource_id)
    ensure_can_manage_kind(user, resource.kind)
    changes = data.model_dump(exclude_unset=True)

    for required in ("name", "code", "status"):
        if required in changes and changes[required] is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"{required} cannot be null")
    if "code" in changes:
        changes["code"] = changes["code"].strip().upper()
        if repo.code_exists(db, changes["code"], exclude_id=resource.id):
            raise HTTPException(status.HTTP_409_CONFLICT, "Resource code already exists")
    if "status" in changes:
        changes["status"] = changes["status"].value
    if "parent_id" in changes:
        _validate_parent(db, resource.kind, changes["parent_id"])
    _validate_fields(
        resource.kind,
        changes.get("capacity", resource.capacity),
        changes.get("serial_number", resource.serial_number),
    )

    for key, value in changes.items():
        setattr(resource, key, value)
    db.commit()
    db.expire_all()  # sessions don't expire on commit; reload parent/children
    return get_resource(db, resource.id)


def delete_resource(db: Session, user: User, resource_id: int) -> None:
    resource = get_resource(db, resource_id)
    ensure_can_manage_kind(user, resource.kind)
    if resource.children:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Move or delete the equipment inside this room/laboratory first",
        )
    db.delete(resource)
    db.commit()
