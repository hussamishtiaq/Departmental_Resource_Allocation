from fastapi import APIRouter, Depends, Query
from fastapi import status as http
from sqlalchemy.orm import Session

from app.core.permissions import Permission
from app.dependencies.auth import get_current_user, require_permission
from app.dependencies.database import get_db
from app.models.user import User
from app.repositories import reservation_repository as repo
from app.schemas.reservation import (
    BusySlot,
    ReservationAssign,
    ReservationCreate,
    ReservationRead,
    ReservationStatus,
    ReviewNote,
)
from app.services import reservation_service as svc

router = APIRouter(prefix="/reservations", tags=["reservations"])

create_perm = require_permission(Permission.RESERVATIONS_CREATE)
review_perm = require_permission(Permission.RESERVATIONS_REVIEW)
assign_perm = require_permission(Permission.RESERVATIONS_ASSIGN)


@router.get("", response_model=list[ReservationRead])
def list_reservations(
    status: ReservationStatus | None = None,
    resource_id: int | None = None,
    mine: bool = Query(False, description="Staff: only show my own"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Staff see every reservation; everyone else sees only their own."""
    return svc.list_reservations(
        db, user, status_=status.value if status else None,
        resource_id=resource_id, mine=mine, skip=skip, limit=limit,
    )


@router.post("", response_model=ReservationRead, status_code=http.HTTP_201_CREATED)
def request_reservation(
    data: ReservationCreate, db: Session = Depends(get_db), user: User = Depends(create_perm)
):
    """Request a resource for yourself. Starts as `pending` until staff approve."""
    return svc.create_request(db, user, data)


@router.post("/assign", response_model=ReservationRead, status_code=http.HTTP_201_CREATED)
def assign_resource(
    data: ReservationAssign, db: Session = Depends(get_db), actor: User = Depends(assign_perm)
):
    """Allocate a resource to a user directly (approved immediately)."""
    return svc.assign(db, actor, data)


@router.get("/schedule/{resource_id}", response_model=list[BusySlot])
def resource_schedule(
    resource_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    """Upcoming approved bookings of a resource (times only)."""
    from datetime import datetime, timezone
    return repo.busy_slots(db, resource_id, datetime.now(timezone.utc))


@router.get("/{reservation_id}", response_model=ReservationRead)
def get_reservation(
    reservation_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return svc.get_reservation(db, user, reservation_id)


@router.post("/{reservation_id}/approve", response_model=ReservationRead)
def approve(
    reservation_id: int, body: ReviewNote | None = None,
    db: Session = Depends(get_db), actor: User = Depends(review_perm),
):
    return svc.approve(db, actor, reservation_id, body.note if body else None)


@router.post("/{reservation_id}/reject", response_model=ReservationRead)
def reject(
    reservation_id: int, body: ReviewNote | None = None,
    db: Session = Depends(get_db), actor: User = Depends(review_perm),
):
    return svc.reject(db, actor, reservation_id, body.note if body else None)


@router.post("/{reservation_id}/cancel", response_model=ReservationRead)
def cancel(
    reservation_id: int, body: ReviewNote | None = None,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    """Owners cancel their own pending/approved bookings; staff can cancel any they review."""
    return svc.cancel(db, user, reservation_id, body.note if body else None)
