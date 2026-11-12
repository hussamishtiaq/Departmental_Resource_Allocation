from enum import Enum


class StrEnum(str, Enum):
    """enum.StrEnum backport (the project venv runs Python 3.10)."""

    def __str__(self) -> str:
        return str(self.value)
