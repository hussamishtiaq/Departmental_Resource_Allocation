from datetime import date, datetime, time, timezone

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Time,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ClassSchedule(Base):
    _tablename_ = "class_schedules"

    _table_args_ = (
        Index(
            "ix_class_schedules_resource_weekday",
            "resource_id",
            "day_of_week",
        ),
        Index(
            "ix_class_schedules_dates",
            "start_date",
            "end_date",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    resource_id: Mapped[int] = mapped_column(
        ForeignKey("resources.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    faculty_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    course_name: Mapped[str] = mapped_column(String(150), nullable=False)
    class_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Monday=0 ... Sunday=6
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)

    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    notes: Mapped[str | None] = mapped_column(String(500))

    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
        index=True
    )

    created_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    resource = relationship("Resource", lazy="joined")

    faculty = relationship(
        "User",
        foreign_keys=[faculty_id],
        lazy="joined"
    )

    created_by = relationship(
        "User",
        foreign_keys=[created_by_id],
        lazy="joined"
    )