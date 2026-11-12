from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Resource(Base):
    """A room, laboratory or piece of equipment owned by the department.

    Hierarchy: rooms/laboratories sit directly under the department
    (parent_id is NULL); equipment may be placed inside a room/laboratory
    (parent_id) or left unassigned (shared equipment)."""

    __tablename__ = "resources"

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(20), index=True)  # room|laboratory|equipment
    name: Mapped[str] = mapped_column(String(150), index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(150))
    capacity: Mapped[int | None] = mapped_column(Integer)  # rooms / labs
    serial_number: Mapped[str | None] = mapped_column(String(100))  # equipment
    # available | maintenance | damaged | retired  (reserved / borrowed are
    # derived from bookings and loans by the later modules)
    status: Mapped[str] = mapped_column(String(20), default="available", index=True)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("resources.id", ondelete="RESTRICT"), index=True
    )
    created_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    parent: Mapped["Resource | None"] = relationship(
        back_populates="children", remote_side="Resource.id"
    )
    children: Mapped[list["Resource"]] = relationship(
        back_populates="parent", order_by="Resource.name"
    )
