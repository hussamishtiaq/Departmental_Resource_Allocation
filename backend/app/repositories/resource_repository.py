from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.resource import Resource


def get(db: Session, resource_id: int) -> Resource | None:
    return db.scalar(
        select(Resource)
        .options(selectinload(Resource.children), selectinload(Resource.parent))
        .where(Resource.id == resource_id)
        .execution_options(populate_existing=True)
    )


def search(
    db: Session,
    *,
    q: str | None = None,
    kind: str | None = None,
    status: str | None = None,
    parent_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Resource]:
    stmt = select(Resource).options(
        selectinload(Resource.children), selectinload(Resource.parent)
    )
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(
                Resource.name.ilike(like),
                Resource.code.ilike(like),
                Resource.serial_number.ilike(like),
            )
        )
    if kind:
        stmt = stmt.where(Resource.kind == kind)
    if status:
        stmt = stmt.where(Resource.status == status)
    if parent_id is not None:
        stmt = stmt.where(Resource.parent_id == parent_id)
    stmt = stmt.order_by(Resource.kind, Resource.name).offset(skip).limit(limit)
    return list(db.scalars(stmt))


def code_exists(db: Session, code: str, exclude_id: int | None = None) -> bool:
    stmt = select(Resource.id).where(Resource.code == code)
    if exclude_id is not None:
        stmt = stmt.where(Resource.id != exclude_id)
    return db.scalar(stmt) is not None
