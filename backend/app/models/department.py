from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Department(Base):
    """The single university department this system manages.
    It is the root of the resource hierarchy:
    Department -> Rooms / Laboratories -> Equipment."""

    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    code: Mapped[str] = mapped_column(String(20))
    description: Mapped[str | None] = mapped_column(String(500))
