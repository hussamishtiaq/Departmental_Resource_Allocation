from datetime import datetime

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from app.utils.enums import StrEnum


class ReservationStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ReservationCreate(BaseModel):
    resource_id: int
    start_time: AwareDatetime
    end_time: AwareDatetime
    purpose: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def check_window(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class ReservationAssign(ReservationCreate):
    """Staff allocate a resource straight to a user (approved immediately)."""
    user_id: int


class ReviewNote(BaseModel):
    note: str | None = Field(default=None, max_length=500)


class ReservationResource(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    kind: str
    name: str
    code: str


class ReservationUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    email: str


class ReservationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    resource: ReservationResource
    user: ReservationUser
    start_time: datetime
    end_time: datetime
    purpose: str | None = None
    status: str
    created_by_id: int | None = None
    reviewed_by: ReservationUser | None = None
    reviewed_at: datetime | None = None
    review_note: str | None = None
    created_at: datetime


class BusySlot(BaseModel):
    """Approved booking shown on a resource's schedule (no personal details)."""
    model_config = ConfigDict(from_attributes=True)
    start_time: datetime
    end_time: datetime
