from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.reservation import Reservation
from app.models.resource import Resource


def get(db: Session, reservation_id: int) -> Reservation | None:
    return db.get(Reservation, reservation_id)


def lock_resource(db: Session, resource_id: int) -> Resource | None:
    """Row-lock the resource so concurrent approvals for it are serialised
    (SELECT ... FOR UPDATE on PostgreSQL; a no-op on SQLite)."""
    return db.scalar(select(Resource).where(Resource.id == resource_id).with_for_update())


def find_conflict(
    db: Session, resource_id: int, start: datetime, end: datetime, exclude_id: int | None = None
) -> Reservation | None:
    """An APPROVED reservation overlapping [start, end) on the same resource."""
    stmt = select(Reservation).where(
        Reservation.resource_id == resource_id,
        Reservation.status == "approved",
        Reservation.start_time < end,
        Reservation.end_time > start,
    )
    if exclude_id is not None:
        stmt = stmt.where(Reservation.id != exclude_id)
    return db.scalars(stmt.limit(1)).first()


def search(
    db: Session,
    *,
    user_id: int | None = None,
    status: str | None = None,
    resource_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Reservation]:
    stmt = select(Reservation)
    if user_id is not None:
        stmt = stmt.where(Reservation.user_id == user_id)
    if status:
        stmt = stmt.where(Reservation.status == status)
    if resource_id is not None:
        stmt = stmt.where(Reservation.resource_id == resource_id)
    stmt = stmt.order_by(Reservation.start_time.desc()).offset(skip).limit(limit)
    return list(db.scalars(stmt))


def busy_slots(db: Session, resource_id: int, since: datetime) -> list[Reservation]:
    return list(
        db.scalars(
            select(Reservation)
            .where(
                Reservation.resource_id == resource_id,
                Reservation.status == "approved",
                Reservation.end_time > since,
            )
            .order_by(Reservation.start_time)
        )
    )
