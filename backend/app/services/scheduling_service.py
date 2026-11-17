from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.permissions import Permission
from app.dependencies.auth import require_permission
from app.dependencies.database import get_db
from app.models.user import User
from app.schemas.class_schedule import (
    ClassScheduleCreate, ClassScheduleRead, ClassScheduleUpdate
)
from app.services import scheduling_service as svc

router = APIRouter(prefix="/schedules", tags=["class schedules"])
read_permission = require_permission(Permission.RESOURCES_READ)
manage_permission = require_permission(Permission.SCHEDULES_MANAGE)


@router.get("", response_model=list[ClassScheduleRead])
def list_schedules(
    resource_id: int | None = Query(default=None, gt=0),
    faculty_id: int | None = Query(default=None, gt=0),
    day_of_week: int | None = Query(default=None, ge=0, le=6),
    start_date: date | None = None,
    end_date: date | None = None,
    active_only: bool = True,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(read_permission),
):
    if start_date and end_date and end_date < start_date:
        raise HTTPException(422, "end_date cannot be before start_date")
    return svc.list_schedules(
        db,
        resource_id=resource_id,
        faculty_id=faculty_id,
        day_of_week=day_of_week,
        start_date=start_date,
        end_date=end_date,
        active_only=active_only,
        skip=skip,
        limit=limit,
    )


@router.get("/{schedule_id}", response_model=ClassScheduleRead)
def get_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(read_permission),
):
    return svc.get_schedule(db, schedule_id)


@router.post("", response_model=ClassScheduleRead,
             status_code=status.HTTP_201_CREATED)
def create_schedule(
    data: ClassScheduleCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(manage_permission),
):
    return svc.create_schedule(db, actor, data)


@router.patch("/{schedule_id}", response_model=ClassScheduleRead)
def update_schedule(
    schedule_id: int,
    data: ClassScheduleUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(manage_permission),
):
    return svc.update_schedule(db, actor, schedule_id, data)


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(manage_permission),
):
    svc.cancel_schedule(db, schedule_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)