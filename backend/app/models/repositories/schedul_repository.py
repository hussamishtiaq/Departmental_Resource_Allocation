from datetime import date, time

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.class_schedule import ClassSchedule


def get(db: Session, schedule_id: int) -> ClassSchedule | None:
    stmt = (
        select(ClassSchedule)
        .options(
            joinedload(ClassSchedule.resource),
            joinedload(ClassSchedule.faculty)
        )
        .where(ClassSchedule.id == schedule_id)
    )
    return db.scalar(stmt)


def search(
    db: Session,
    *,
    resource_id=None,
    faculty_id=None,
    day_of_week=None,
    start_date: date | None = None,
    end_date: date | None = None,
    active_only: bool = True,
    skip: int = 0,
    limit: int = 100
) -> list[ClassSchedule]:

    stmt = select(ClassSchedule).options(
        joinedload(ClassSchedule.resource),
        joinedload(ClassSchedule.faculty)
    )

    if resource_id is not None:
        stmt = stmt.where(ClassSchedule.resource_id == resource_id)

    if faculty_id is not None:
        stmt = stmt.where(ClassSchedule.faculty_id == faculty_id)

    if day_of_week is not None:
        stmt = stmt.where(ClassSchedule.day_of_week == day_of_week)

    if start_date is not None:
        stmt = stmt.where(ClassSchedule.end_date >= start_date)

    if end_date is not None:
        stmt = stmt.where(ClassSchedule.start_date <= end_date)

    if active_only:
        stmt = stmt.where(ClassSchedule.is_active.is_(True))

    stmt = stmt.order_by(
        ClassSchedule.day_of_week,
        ClassSchedule.start_time
    ).offset(skip).limit(limit)

    return list(db.scalars(stmt).unique().all())


def find_resource_conflicts(
    db: Session,
    *,
    resource_id: int,
    day_of_week: int,
    start_date: date,
    end_date: date,
    start_time: time,
    end_time: time,
    exclude_id: int | None = None
) -> list[ClassSchedule]:

    stmt = select(ClassSchedule).where(
        ClassSchedule.resource_id == resource_id,
        ClassSchedule.day_of_week == day_of_week,
        ClassSchedule.is_active.is_(True),
        ClassSchedule.start_date <= end_date,
        ClassSchedule.end_date >= start_date,
        ClassSchedule.start_time < end_time,
        ClassSchedule.end_time > start_time,
    )

    if exclude_id is not None:
        stmt = stmt.where(ClassSchedule.id != exclude_id)

    return list(db.scalars(stmt).all())


def find_faculty_conflicts(
    db: Session,
    *,
    faculty_id: int,
    day_of_week: int,
    start_date: date,
    end_date: date,
    start_time: time,
    end_time: time,
    exclude_id: int | None = None
) -> list[ClassSchedule]:

    stmt = select(ClassSchedule).where(
        ClassSchedule.faculty_id == faculty_id,
        ClassSchedule.day_of_week == day_of_week,
        ClassSchedule.is_active.is_(True),
        ClassSchedule.start_date <= end_date,
        ClassSchedule.end_date >= start_date,
        ClassSchedule.start_time < end_time,
        ClassSchedule.end_time > start_time,
    )

    if exclude_id is not None:
        stmt = stmt.where(ClassSchedule.id != exclude_id)

    return list(db.scalars(stmt).all())