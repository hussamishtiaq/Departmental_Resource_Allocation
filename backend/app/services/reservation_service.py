from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.permissions import Permission, RoleName, has_permission
from app.models.reservation import Reservation
from app.models.resource import Resource
from app.models.user import User
from app.repositories import reservation_repository as repo
from app.repositories import user_repository as users
from app.schemas.reservation import ReservationAssign, ReservationCreate
from app.services.resource_service import can_manage_kind

MAX_DURATION = timedelta(days=30)

def _utc(dt: datetime) -> datetime:
    return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

def _now() -> datetime:
    return datetime.now(timezone.utc)

def _is_reviewer(user: User) -> bool:
    return has_permission(user, Permission.RESERVATIONS_REVIEW)

def _get_or_404(db: Session, reservation_id: int) -> Reservation:
    reservation = repo.get(db, reservation_id)
    if reservation is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reservation not found")
    return reservation

def get_reservation(db: Session, user: User, reservation_id: int) -> Reservation:
    reservation = _get_or_404(db, reservation_id)
    if not _is_reviewer(user) and reservation.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reservation not found")
    return reservation

def _validate_window(start: datetime, end: datetime) -> tuple[datetime, datetime]:
    start, end = _utc(start), _utc(end)
    if end <= start:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "End time must be after start time")
    if start < _now():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Start time is in the past")
    if (end - start) < timedelta(minutes=15):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "A booking can last at least 15 minutes")
    if (end - start) > MAX_DURATION:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "A booking can last at most 30 days")
    return start, end

def _ensure_bookable(resource: Resource) -> None:
    if resource.status != "available":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Resource is not available for booking (status: {resource.status})")

def _ensure_free(db: Session, resource_id: int, start: datetime, end: datetime, exclude_id: int | None = None) -> None:
    if repo.find_conflict(db, resource_id, start, end, exclude_id):
        raise HTTPException(status.HTTP_409_CONFLICT, "Resource is already booked for part of that time")

def _ensure_can_manage_kind(db: Session, actor: User, resource_id: int) -> None:
    resource = repo.get_resource(db, resource_id)
    if resource is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Resource not found")
    if not can_manage_kind(actor, resource.kind):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Cannot manage this kind of resource")

def _lock_resource(db: Session, resource_id: int) -> Resource:
    resource = repo.lock_resource(db, resource_id)
    if resource is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Resource not found")
    return resource

def create_request(db: Session, user: User, data: ReservationCreate) -> Reservation:
    """A pending request. It is refused up-front if the slot is already taken."""
    start, end = _validate_window(data.start_time, data.end_time)
    resource = _lock_resource(db, data.resource_id)
    _ensure_bookable(resource)
    _ensure_free(db, data.resource_id, start, end)
    reservation = Reservation(
        resource_id=data.resource_id, user_id=user.id,
        start_time=start, end_time=end,
        purpose=data.purpose, status="pending", created_by_id=user.id,
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    return reservation

def assign_to_user(db: Session, actor: User, data: ReservationAssign) -> Reservation:
    """Staff allocate a resource straight to a user (approved immediately)."""
    target = users.get_by_id(db, data.user_id)
    if target is None or not target.is_active:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "User not found or inactive")
    _ensure_can_manage_kind(db, actor, data.resource_id)
    start, end = _validate_window(data.start_time, data.end_time)
    resource = _lock_resource(db, data.resource_id)
    _ensure_bookable(resource)
    _ensure_free(db, data.resource_id, start, end)
    reservation = Reservation(
        resource_id=data.resource_id, user_id=data.user_id,
        start_time=start, end_time=end,
        purpose=data.purpose, status="approved", created_by_id=actor.id,
        reviewed_by_id=actor.id, reviewed_at=_now(),
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    return reservation

def approve(db: Session, actor: User, reservation_id: int, note: str | None = None) -> Reservation:
    reservation = _get_or_404(db, reservation_id)
    resource = _lock_resource(db, reservation.resource_id)  # serialize per resource
    if reservation.status != "pending":
        raise HTTPException(status.HTTP_409_CONFLICT, f"Request is already {reservation.status}")
    _ensure_bookable(resource)
    _ensure_can_manage_kind(db, actor, reservation.resource_id)
    _ensure_free(db, reservation.resource_id, reservation.start_time, reservation.end_time, reservation.id)
    reservation.status = "approved"
    reservation.reviewed_by_id = actor.id
    reservation.reviewed_at = _now()
    reservation.review_note = note
    db.commit()
    db.refresh(reservation)
    return reservation

def reject(db: Session, actor: User, reservation_id: int, note: str | None = None) -> Reservation:
    reservation = _get_or_404(db, reservation_id)
    if reservation.status != "pending":
        raise HTTPException(status.HTTP_409_CONFLICT, f"Request is already {reservation.status}")
    _ensure_can_manage_kind(db, actor, reservation.resource_id)
    reservation.status = "rejected"
    reservation.reviewed_by_id = actor.id
    reservation.reviewed_at = _now()
    reservation.review_note = note
    db.commit()
    db.refresh(reservation)
    return reservation

def cancel(db: Session, actor: User, reservation_id: int, note: str | None = None) -> Reservation:
    reservation = get_reservation(db, actor, reservation_id)
    if not _is_reviewer(actor):
        _ensure_can_manage_kind(db, actor, reservation.resource_id)
    if reservation.status not in ("pending", "approved"):
        raise HTTPException(status.HTTP_409_CONFLICT, f"Request is already {reservation.status}")
    if _utc(reservation.end_time) <= _now():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "That booking is already over")
    if not _is_reviewer(actor):
        _ensure_can_manage_kind(db, actor, reservation.resource_id)
    reservation.status = "cancelled"
    reservation.reviewed_by_id = actor.id
    reservation.reviewed_at = _now()
    reservation.review_note = note
    db.commit()
    db.refresh(reservation)
    return reservation

def list_reservations(db: Session, user: User, *, status: str | None = None, resource_id: int | None = None, skip: int = 0, limit: int = 100):
    if _is_reviewer(user):
        return repo.search(db, status=status, resource_id=resource_id, skip=skip, limit=limit)
    return repo.search(db, user_id=user.id, status=status, resource_id=resource_id, skip=skip, limit=limit)