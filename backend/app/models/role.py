from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Role(Base):
    """A role in the authority hierarchy. A higher `level` means more authority."""

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    level: Mapped[int] = mapped_column(Integer)
    description: Mapped[str | None] = mapped_column(String(255))
