from datetime import date, datetime, time
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

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
    created_by: int | None
    created_at: datetime
    updated_at: datetime