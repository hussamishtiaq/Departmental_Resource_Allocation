from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.utils.enums import StrEnum


class ResourceKind(StrEnum):
    ROOM = "room"
    LABORATORY = "laboratory"
    EQUIPMENT = "equipment"


class ResourceStatus(StrEnum):
    AVAILABLE = "available"
    MAINTENANCE = "maintenance"
    DAMAGED = "damaged"
    RETIRED = "retired"


class ResourceBase(BaseModel):
    kind: ResourceKind
    name: str = Field(min_length=1, max_length=150)
    code: str = Field(min_length=1, max_length=50)
    description: str | None = None
    location: str | None = Field(default=None, max_length=150)
    capacity: int | None = Field(default=None, ge=1, le=10000)
    serial_number: str | None = Field(default=None, max_length=100)
    status: ResourceStatus = ResourceStatus.AVAILABLE
    parent_id: int | None = None


class ResourceCreate(ResourceBase):
    pass


class ResourceUpdate(BaseModel):
    """`kind` is fixed after creation."""
    name: str | None = Field(default=None, min_length=1, max_length=150)
    code: str | None = Field(default=None, min_length=1, max_length=50)
    description: str | None = None
    location: str | None = Field(default=None, max_length=150)
    capacity: int | None = Field(default=None, ge=1, le=10000)
    serial_number: str | None = Field(default=None, max_length=100)
    status: ResourceStatus | None = None
    parent_id: int | None = None


class ResourceSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    kind: str
    name: str
    code: str
    status: str


class ResourceRead(ResourceBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    kind: str
    status: str
    parent: ResourceSummary | None = None
    children: list[ResourceSummary] = []
