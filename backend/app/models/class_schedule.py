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
    # pydantic request and response schemas

    from datetime import date, datetime, time
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class ClassScheduleBase(BaseModel):
    resource_id: int = Field(gt=0)
    faculty_id: int = Field(gt=0)
    course_name: Annotated[str, Field(min_length=2, max_length=150)]
    class_name: Annotated[str, Field(min_length=1, max_length=100)]
    day_of_week: int = Field(ge=0, le=6)
    start_time: time
    end_time: time
    start_date: date
    end_date: date
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("course_name", "class_name")
    @classmethod
    def strip_names(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be empty")

        return value

    @model_validator(mode="after")
    def validate_schedule(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        if self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date")
        return self


class ClassScheduleCreate(ClassScheduleBase):
    pass


class ClassScheduleUpdate(BaseModel):
    resource_id: int | None = Field(default=None, gt=0)
    faculty_id: int | None = Field(default=None, gt=0)
    course_name: str | None = Field(default=None, min_length=2, max_length=150)
    class_name: str | None = Field(default=None, min_length=1, max_length=100)
    day_of_week: int | None = Field(default=None, ge=0, le=6)
    start_time: time | None = None
    end_time: time | None = None
    start_date: date | None = None
    end_date: date | None = None
    notes: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class ScheduleResourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    kind: str
    status: str


class ScheduleFacultyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: str


class ClassScheduleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    resource_id: int
    faculty_id: int
    resource: ScheduleResourceRead
    faculty: ScheduleFacultyRead
    course_name: str
    class_name: str
    day_of_week: int
    start_time: time
    end_time: time
    start_date: date
    end_date: date
    notes: str | None
    is_active: bool
    created_by_id: int | None
    created_at: datetime
    updated_at: datetime