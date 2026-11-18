from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.permissions import RoleName
from app.models.class_schedule import ClassSchedule
from app.models.reservation import Reservation
from app.models.resource import Resource
from app.models.user import User
from app.repositories import schedule_repository as repo
from app.schemas.class_schedule import ClassScheduleCreate, ClassScheduleUpdate

LOCAL_TZ = ZoneInfo("Asia/Karachi")
PLACEHOLDER_RESOURCE_KINDS = ("room", "laboratory")
UNAVAILABLE_RESOURCE_STATUSES = ("maintenance", "damaged", "retired")

def get_schedule(db: Session, schedule_id: int) -> ClassSchedule:
    schedule = repo.get(db, schedule_id)
    if schedule is None:
        raise HTTPException(404, "Class schedule not found")
    return schedule

def get_resource(db: Session, resource_id: int) -> Resource:
    resource = db.get(Resource, resource_id)
    if resource is None:
        raise HTTPException(404, "Resource not found")
    return resource

def get_faculty(db: Session, faculty_id: int) -> User:
    faculty = db.get(User, faculty_id)
    if faculty is None or not faculty.is_active:
        raise HTTPException(404, "Faculty member not found or inactive")
    if faculty.role_name != RoleName.FACULTY:
        raise HTTPException(400, "Selected user is not faculty")
    return faculty

def lock_resource_row(db: Session, resource_id: int) -> Resource:
    # PostgreSQL row lock serializes operations along this resource.
    resource = db.execute(
        select(Resource).where(Resource.id == resource_id).with_for_update()
    ).scalar_one_or_none()
    if resource is None:
        raise HTTPException(404, "Resource not found")
    return resource

def validate_resource(resource: Resource) -> None:
    if resource.kind not in PLACEHOLDER_RESOURCE_KINDS:
        raise HTTPException(400, "Only rooms and laboratories can be scheduled")
    if resource.status in UNAVAILABLE_RESOURCE_STATUSES:
        raise HTTPException(400, "Resource is not available")

def has_weekday(start: date, end: date, weekday: int) -> bool:
    first = start + timedelta(days=(weekday - start.weekday()) % 7)
    return first <= end

def check_reservation_conflicts(db: Session, *, resource_id: int, day_of_week: int,
                                start_date: date, end_date: date,
                                start_time: time, end_time: time) -> None:
    local_start = datetime.combine(start_date, start_time, tzinfo=LOCAL_TZ)
    local_end = datetime.combine(end_date, end_time, tzinfo=LOCAL_TZ)
    start = select(Reservation).where(
        Reservation.resource_id == resource_id,
        Reservation.status == "approved",
        Reservation.start_time < local_end,
        Reservation.end_time > local_start,
    )
    for booking in db.scalars(start).all():
        rs, re_ = booking.start_time, booking.end_time
        if rs is None or re_ is None:
            continue
        rs = rs.replace(tzinfo=LOCAL_TZ)
        re_ = re_.replace(tzinfo=LOCAL_TZ)
        rs, re_ = rs.astimezone(LOCAL_TZ), re_.astimezone(LOCAL_TZ)
        day = max(start_date, rs.date())
        last = min(end_date, re_.date())
        while day <= last:
            if day.weekday() == day_of_week:
                cs = datetime.combine(day, start_time, tzinfo=LOCAL_TZ)
                ce = datetime.combine(day, end_time, tzinfo=LOCAL_TZ)
                if cs < re_ and ce > rs:
                    raise HTTPException(409, "Approved reservation conflict on day")
            day += timedelta(days=1)

def validate_conflicts(db: Session, *, resource_id: int, faculty_id: int,
                       day_of_week: int, start_date: date, end_date: date,
                       start_time: time, end_time: time,
                       exclude_id: int | None = None) -> None:
    rooms = repo.find_resource_conflicts(
        db, resource_id=resource_id, day_of_week=day_of_week,
        start_date=start_date, end_date=end_date,
        start_time=start_time, end_time=end_time, exclude_id=exclude_id
    )
    rooms = [r for r in rooms if has_weekday(
        max(r.start_date, start_date), min(r.end_date, end_date), day_of_week
    )]
    if rooms:
        raise HTTPException(409, "Resource already has a class during this time")

    faculty = repo.find_faculty_conflicts(
        db, faculty_id=faculty_id, day_of_week=day_of_week,
        start_date=start_date, end_date=end_date,
        start_time=start_time, end_time=end_time
    )
    faculty = [f for f in faculty if has_weekday(
        max(f.start_date, start_date), min(f.end_date, end_date), day_of_week
    )]
    if faculty:
        raise HTTPException(409, "Faculty member already has a class during this time")

    check_reservation_conflicts(
        db, resource_id=resource_id, day_of_week=day_of_week,
        start_date=start_date, end_date=end_date,
        start_time=start_time, end_time=end_time
    )

def check_reservation_against_schedule(db: Session, *, resource_id: int,
                                       start_date: date, end_date: date,
                                       start_time: time, end_time: time) -> None:
    # Called by reservation approval before changing status to approved
    schedules = db.execute(
        select(ClassSchedule).where(
            ClassSchedule.resource_id == resource_id,
            ClassSchedule.is_active.is_(True),
        )
    ).scalars().all()
    for sched in schedules:
        if not (end_date < sched.start_date or start_date > sched.end_date):
            if sched.day_of_week == start_date.weekday():
                if not (end_time <= sched.start_time or start_time >= sched.end_time):
                    raise HTTPException(409, "Reservation conflicts with class on day")

def create_schedule(db: Session, actor: User, data: ClassScheduleCreate) -> ClassSchedule:
    resource = lock_resource_row(db, data.resource_id)
    validate_resource(resource)
    get_faculty(db, data.faculty_id)
    validate_conflicts(
        db, resource_id=data.resource_id, faculty_id=data.faculty_id,
        day_of_week=data.day_of_week, start_date=data.start_date,
        end_date=data.end_date, start_time=data.start_time, end_time=data.end_time
    )
    obj = ClassSchedule(**data.model_dump(), created_by=actor.id)
    db.add(obj)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Schedule already exists")
    db.refresh(obj)
    return repo.get(db)